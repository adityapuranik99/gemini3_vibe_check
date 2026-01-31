"""Generate social media share cards using Fal.ai's Nano Banana Pro."""

import os
import logging
import asyncio
from typing import Optional, Dict, Any
import fal_client
from PIL import Image
import requests
from io import BytesIO
from pathlib import Path
import base64

from models import MomentAnalysis, MomentType

logger = logging.getLogger(__name__)

THEMES = {
    "stadium": {
        "prompt_style": "epic sports moment, stadium lights, dramatic atmosphere, crowd energy",
        "bg_color": "#1a1a2e"
    },
    "cyberpunk": {
        "prompt_style": "cyberpunk neon aesthetic, glowing edges, futuristic sports broadcast",
        "bg_color": "#0f0f23"
    },
    "minimal": {
        "prompt_style": "clean minimal design, bold typography, professional sports graphic",
        "bg_color": "#111111"
    },
    "hype": {
        "prompt_style": "explosive energy, fire effects, maximum hype sports moment",
        "bg_color": "#1a0a0a"
    }
}


class ShareCardGenerator:
    """
    Generate social media share cards for moments using Nano Banana Pro.

    Pipeline:
    1. Extract subject from keyframe using Bria RMBG (background removal)
    2. Generate stylized share card with Nano Banana Pro using the cutout
    """

    def __init__(
        self,
        fal_api_key: Optional[str] = None,
        output_dir: str = "./storage/share_cards",
    ):
        self.fal_api_key = fal_api_key or os.getenv("FAL_KEY")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        (self.output_dir / "images").mkdir(exist_ok=True)
        (self.output_dir / "cutouts").mkdir(exist_ok=True)

        logger.info(f"📸 Share card generator initialized (Nano Banana Pro)")

    async def generate_static_card(
        self,
        moment: MomentAnalysis,
        theme_name: str = "stadium",
        keyframe_path: Optional[str] = None
    ) -> str:
        """Generate a share card using background removal + Nano Banana Pro."""
        theme = THEMES.get(theme_name, THEMES["stadium"])

        logger.info(f"🎨 Generating share card for {moment.moment_id} with theme: {theme_name}")

        if not keyframe_path or not os.path.exists(keyframe_path):
            logger.warning("No keyframe provided, generating text-only card")
            return await self._generate_text_only_card(moment, theme_name)

        try:
            # Step 1: Remove background from keyframe to get subject cutout
            logger.info("✂️ Removing background from keyframe...")
            cutout_url = await self._remove_background(keyframe_path)

            # Step 2: Generate stylized share card with Nano Banana Pro
            logger.info("🎨 Generating share card with Nano Banana Pro...")
            card_image = await self._generate_with_nano_banana(
                moment=moment,
                cutout_url=cutout_url,
                theme=theme
            )

            # Step 3: Save the result
            output_path = self.output_dir / "images" / f"{moment.moment_id}_{theme_name}.png"
            card_image.save(output_path, "PNG")

            logger.info(f"✅ Share card saved: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"❌ Failed to generate share card: {e}")
            # Fallback to simple keyframe-based card
            return await self._generate_fallback_card(moment, keyframe_path, theme_name)

    async def _remove_background(self, image_path: str) -> str:
        """Remove background from image using BiRefNet."""

        # Upload image to fal
        with open(image_path, "rb") as f:
            image_data = f.read()

        # Convert to base64 data URL
        base64_image = base64.b64encode(image_data).decode("utf-8")
        data_url = f"data:image/png;base64,{base64_image}"

        def _run():
            return fal_client.run(
                "fal-ai/birefnet",
                arguments={
                    "image_url": data_url,
                    "model": "General Use (Light)",
                    "output_format": "png"
                }
            )

        result = await asyncio.to_thread(_run)

        # Return the URL of the cutout image
        return result["image"]["url"]

    async def _generate_with_nano_banana(
        self,
        moment: MomentAnalysis,
        cutout_url: str,
        theme: Dict[str, Any]
    ) -> Image.Image:
        """Generate share card using Nano Banana Pro with the subject cutout."""

        # Build a prompt that describes the desired share card
        moment_type = moment.moment_type.value if hasattr(moment.moment_type, 'value') else str(moment.moment_type)

        prompt = f"""Create a professional sports social media share card (1200x630 pixels).

The image should feature the person from the reference image prominently in the center-right.
Style: {theme['prompt_style']}

Include stylized text overlays:
- "🔥 {moment.scores.hype}% HYPE" in large bold text at top-left
- "{moment_type.upper()}" as a badge/label
- Brief caption area at bottom

Make it look like an ESPN or Bleacher Report highlight card.
Dynamic composition, the subject should look heroic and energetic.
High contrast, vibrant colors, broadcast quality."""

        def _run():
            return fal_client.run(
                "fal-ai/nano-banana-pro",
                arguments={
                    "prompt": prompt,
                    "image_url": cutout_url,  # Reference image (the cutout)
                    "image_size": {"width": 1200, "height": 630},
                    "num_inference_steps": 30,
                    "guidance_scale": 7.5,
                }
            )

        result = await asyncio.to_thread(_run)
        image_url = result["images"][0]["url"]

        # Download the generated image
        response = requests.get(image_url)
        return Image.open(BytesIO(response.content))

    async def _generate_text_only_card(
        self,
        moment: MomentAnalysis,
        theme_name: str
    ) -> str:
        """Generate a text-only card when no keyframe is available."""
        theme = THEMES.get(theme_name, THEMES["stadium"])
        moment_type = moment.moment_type.value if hasattr(moment.moment_type, 'value') else str(moment.moment_type)

        prompt = f"""Create a professional sports social media graphic (1200x630 pixels).
Style: {theme['prompt_style']}

Text to include:
- "🔥 {moment.scores.hype}% HYPE" prominently displayed
- "{moment_type.upper()}" as the main headline
- "{moment.summary[:100]}" as subtitle

Make it look like a breaking news sports graphic.
Bold typography, dynamic composition, broadcast quality."""

        def _run():
            return fal_client.run(
                "fal-ai/nano-banana-pro",
                arguments={
                    "prompt": prompt,
                    "image_size": {"width": 1200, "height": 630},
                    "num_inference_steps": 30,
                    "guidance_scale": 7.5,
                }
            )

        result = await asyncio.to_thread(_run)
        image_url = result["images"][0]["url"]

        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))

        output_path = self.output_dir / "images" / f"{moment.moment_id}_{theme_name}.png"
        img.save(output_path, "PNG")

        return str(output_path)

    async def _generate_fallback_card(
        self,
        moment: MomentAnalysis,
        keyframe_path: str,
        theme_name: str
    ) -> str:
        """Simple fallback: just use the keyframe with minimal processing."""
        from PIL import ImageDraw, ImageFont

        img = Image.open(keyframe_path)
        img = img.resize((1200, 630), Image.Resampling.LANCZOS)

        # Add a dark gradient overlay
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Draw gradient from bottom
        for y in range(img.height // 2, img.height):
            alpha = int(200 * (y - img.height // 2) / (img.height // 2))
            draw.line([(0, y), (img.width, y)], fill=(0, 0, 0, alpha))

        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay)

        # Add text
        draw = ImageDraw.Draw(img)
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Draw hype score
        draw.text((50, 500), f"🔥 HYPE: {moment.scores.hype}%", fill="white", font=font_large)

        # Draw moment type
        moment_type = moment.moment_type.value if hasattr(moment.moment_type, 'value') else str(moment.moment_type)
        draw.text((50, 560), moment_type.upper(), fill="#FFD700", font=font_small)

        output_path = self.output_dir / "images" / f"{moment.moment_id}_{theme_name}.png"
        img.convert("RGB").save(output_path, "PNG")

        logger.info(f"✅ Fallback card saved: {output_path}")
        return str(output_path)

    async def generate_animated_loop(
        self,
        moment: MomentAnalysis,
        static_card_path: str,
        theme_name: str = "stadium"
    ) -> str:
        """Generate animated version - disabled for performance."""
        logger.info("⏭️ Animated loop generation disabled")
        return ""
