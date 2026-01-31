# Fal.ai Share Card Generation Integration Plan

## Goal: Automatic Social Media Share Cards

Integrate **Fal.ai** to automatically generate eye-catching share card images for approved moments using FLUX text-to-image models.

## What is a Share Card?

A share card is a visually designed image (typically 1200x630px for social media) that includes:
- Moment highlight snapshot
- Hype/risk scores visualized
- Post copy text overlay
- Branding elements
- Call-to-action

Think: Instagram story-style cards that can be posted alongside the video clip.

## Use Case

### Scenario: Moment approved → instant share assets

**Current workflow:**
1. Moment approved → clip video generated
2. Social team manually creates graphics in Canva/Photoshop
3. 5-10 minutes of design work per moment
4. Inconsistent visual style

**With Fal Integration:**
1. Moment approved → clip video + share card generated simultaneously
2. AI-designed card with consistent branding
3. Ready in ~3 seconds
4. `share_card_url` populated in `MomentAnalysis` model

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Vibe Check Pipeline                             │
│                                                              │
│  Moment Analysis (Gemini) ──> Clip Assembler               │
│                           │                                  │
│                           └──> Share Card Generator (Fal)   │
│                                       │                      │
│                                       ▼                      │
│                              storage/share_cards/           │
│                                 m_001_card.png              │
└─────────────────────────────────────────────────────────────┘
```

### Integration Points

**File: `backend/share_card_generator.py`** (new)
- `ShareCardGenerator` class
- Uses Fal FLUX model for image generation
- Template-based prompt engineering
- Returns image URL

**File: `backend/pipeline.py`**
- Add share card generation after Gemini analysis
- Populate `moment.share_card_url`

**File: `backend/models.py`**
- Already has `share_card_url` field (line 62) ✅

## Fal.ai Model Selection

### Recommended: FLUX.1 [schnell]

**Why?**
- **Ultra-fast**: Generates images in ~1-2 seconds
- **High quality**: Professional-looking social graphics
- **Cost-effective**: Optimized for scale
- **Consistent style**: Reliable for templated designs

**Model ID:** `fal-ai/flux/schnell`

**Alternative:** `fal-ai/flux/dev` for higher quality (slower, more expensive)

## Share Card Design Strategy

### Template 1: "Hype Moment" Card
```
┌──────────────────────────────────────┐
│  🔥 HYPE: 87  ⚠️  RISK: 22         │
│                                      │
│  [Key Frame from Moment]             │
│                                      │
│  "BUZZER BEATER! Jordan's          │
│   clutch three-pointer sends        │
│   crowd into frenzy"                 │
│                                      │
│  ⏱️ 5:23 | 🎯 Goal | #NBATonight   │
└──────────────────────────────────────┘
```

### Template 2: "Stats Overlay" Card
```
┌──────────────────────────────────────┐
│  MOMENT DETECTED                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│                                      │
│  [Key Frame]                         │
│                                      │
│  🔥 87    Motion: ████████░░ 81%   │
│  ⚠️  22    Audio:  ███████░░░ 77%   │
│                                      │
│  Type: DUNK | Time: 5:23            │
└──────────────────────────────────────┘
```

### Prompt Engineering Strategy

Instead of generating the entire card with Fal (hard to control layout), we'll use a **hybrid approach**:

1. **Fal generates:** Stylized background gradient/pattern
2. **PIL/Pillow adds:** Text overlays, stats, frame composite

This gives us:
- Fast generation (simple prompts)
- Precise layout control
- Consistent branding

## Implementation Plan

### Phase 1: Fal Client Setup (30 min)

**1. Install dependencies:**
```bash
pip install fal-client
```

**2. Add to `backend/requirements.txt`:**
```txt
fal-client==0.11.0
```

**3. Add environment variable:**
```bash
# backend/.env
FAL_KEY=your_fal_api_key
```

### Phase 2: Share Card Generator (2 hours)

**Create `backend/share_card_generator.py`:**
```python
"""Generate share cards for moments using Fal.ai + PIL."""

import os
import logging
from typing import Optional
import fal_client
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from pathlib import Path

from models import MomentAnalysis

logger = logging.getLogger(__name__)


class ShareCardGenerator:
    """
    Generate social media share cards for moments.

    Uses Fal.ai FLUX for background generation + PIL for text overlays.
    """

    def __init__(
        self,
        fal_api_key: Optional[str] = None,
        output_dir: str = "./storage/share_cards",
    ):
        """
        Initialize share card generator.

        Args:
            fal_api_key: Fal API key (defaults to FAL_KEY env var)
            output_dir: Directory for generated share cards
        """
        self.fal_api_key = fal_api_key or os.getenv("FAL_KEY")
        if not self.fal_api_key:
            raise ValueError("FAL_KEY not found. Set it in .env or pass as parameter.")

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"📸 Share card generator initialized")

    async def generate_share_card(
        self,
        moment: MomentAnalysis,
        keyframe_path: Optional[str] = None,
    ) -> str:
        """
        Generate a share card for a moment.

        Args:
            moment: MomentAnalysis with all moment data
            keyframe_path: Optional path to key frame image

        Returns:
            Path to generated share card image
        """
        logger.info(f"🎨 Generating share card for {moment.moment_id}")

        try:
            # Step 1: Generate background with Fal
            background_prompt = self._build_background_prompt(moment)
            background_img = await self._generate_fal_background(background_prompt)

            # Step 2: Composite with text overlays using PIL
            card_img = self._add_overlays(
                background=background_img,
                moment=moment,
                keyframe_path=keyframe_path,
            )

            # Step 3: Save to disk
            card_path = self.output_dir / f"{moment.moment_id}_card.png"
            card_img.save(card_path, "PNG", quality=95)

            logger.info(f"✅ Share card saved: {card_path}")
            return str(card_path)

        except Exception as e:
            logger.error(f"❌ Share card generation failed: {e}")
            raise

    def _build_background_prompt(self, moment: MomentAnalysis) -> str:
        """Build Fal prompt for background generation."""

        # Map moment type to visual style
        style_map = {
            "goal": "dynamic sports action, blue and orange gradient, energy burst",
            "dunk": "explosive basketball energy, red and gold gradient, dramatic lighting",
            "touchdown": "green field stadium atmosphere, triumphant gold rays",
            "ace": "tennis court elegance, clean white and green gradient",
            "save": "intense goalkeeper drama, red and black gradient",
            "rally": "fast-paced volleyball energy, yellow and blue gradient",
            "winner": "championship celebration, purple and gold gradient",
            "other": "modern sports aesthetic, teal and gray gradient",
        }

        style = style_map.get(moment.moment_type, style_map["other"])

        prompt = f"""
Modern sports social media background, {style},
smooth gradients, abstract geometric patterns,
professional design, high contrast, vibrant colors,
1200x630 aspect ratio, minimalist, Instagram-ready
"""

        return prompt.strip()

    async def _generate_fal_background(self, prompt: str) -> Image.Image:
        """Call Fal FLUX model to generate background."""
        logger.debug(f"Fal prompt: {prompt}")

        # Call Fal FLUX schnell (fast model)
        response = fal_client.run(
            "fal-ai/flux/schnell",
            arguments={
                "prompt": prompt,
                "image_size": {
                    "width": 1200,
                    "height": 630,
                },
                "num_inference_steps": 4,  # Fast generation
                "num_images": 1,
            },
        )

        # Download generated image
        image_url = response["images"][0]["url"]
        logger.debug(f"Fal image URL: {image_url}")

        img_response = requests.get(image_url)
        img = Image.open(BytesIO(img_response.content))

        return img

    def _add_overlays(
        self,
        background: Image.Image,
        moment: MomentAnalysis,
        keyframe_path: Optional[str] = None,
    ) -> Image.Image:
        """Add text overlays and keyframe composite using PIL."""

        # Create drawing context
        draw = ImageDraw.Draw(background)

        # Load fonts (use system fonts or bundled fonts)
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
            small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            logger.warning("Custom fonts not found, using default")
            title_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Add semi-transparent overlay for text readability
        overlay = Image.new("RGBA", background.size, (0, 0, 0, 180))
        background = background.convert("RGBA")
        background = Image.alpha_composite(background, overlay)
        draw = ImageDraw.Draw(background)

        # Title: Hype + Risk scores
        title = f"🔥 HYPE: {moment.scores.hype}  ⚠️  RISK: {moment.scores.risk}"
        draw.text((60, 60), title, fill="white", font=title_font)

        # Moment summary (truncate if too long)
        summary = moment.summary[:100] + "..." if len(moment.summary) > 100 else moment.summary

        # Word wrap summary
        words = summary.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            test_line = " ".join(current_line)
            bbox = draw.textbbox((0, 0), test_line, font=body_font)
            if bbox[2] > 1080:  # Max width
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))

        y_offset = 300
        for line in lines[:3]:  # Max 3 lines
            draw.text((60, y_offset), line, fill="white", font=body_font)
            y_offset += 45

        # Footer: Type + Time
        footer = f"⏱️  {moment.t0:.1f}s | 🎯 {moment.moment_type.upper()} | #VibeCheck"
        draw.text((60, 540), footer, fill="#FFD700", font=small_font)

        # Optional: Add keyframe thumbnail (if provided)
        if keyframe_path and os.path.exists(keyframe_path):
            try:
                keyframe = Image.open(keyframe_path)
                keyframe.thumbnail((400, 225))  # 16:9 aspect ratio
                background.paste(keyframe, (740, 200))
            except Exception as e:
                logger.warning(f"Could not add keyframe: {e}")

        return background.convert("RGB")

    def generate_share_card_sync(
        self,
        moment: MomentAnalysis,
        keyframe_path: Optional[str] = None,
    ) -> str:
        """Synchronous wrapper for generate_share_card."""
        import asyncio
        return asyncio.run(self.generate_share_card(moment, keyframe_path))
```

### Phase 3: Pipeline Integration (30 min)

**Update `backend/pipeline.py`:**
```python
from share_card_generator import ShareCardGenerator

class VideoPipeline:
    def __init__(self, ...):
        # ... existing init ...
        self.share_card_generator = ShareCardGenerator()

    async def process_video(self, ...):
        # ... existing code ...

        if moment:
            # Generate clip
            clip_path = await self._generate_clip(moment, ingester.video_path)
            if clip_path:
                moment.clip_url = f"/api/clips/{Path(clip_path).name}"

            # Generate share card (NEW)
            try:
                card_path = await self._generate_share_card(moment)
                if card_path:
                    moment.share_card_url = f"/api/share_cards/{Path(card_path).name}"
            except Exception as e:
                logger.warning(f"Share card generation failed: {e}")

    async def _generate_share_card(
        self,
        moment: MomentAnalysis,
    ) -> Optional[str]:
        """Generate a share card for a moment."""
        try:
            logger.info(f"🎨 Generating share card for {moment.moment_id}")

            # Run in thread (Fal client is blocking)
            card_path = await asyncio.to_thread(
                self.share_card_generator.generate_share_card_sync,
                moment,
            )

            logger.info(f"✅ Share card generated: {card_path}")
            return card_path

        except Exception as e:
            logger.error(f"❌ Share card generation failed: {e}")
            return None
```

### Phase 4: API Endpoint (15 min)

**Update `backend/main.py`:**
```python
# Add to storage paths
STORAGE_PATHS = {
    "videos": os.getenv("VIDEO_STORAGE_PATH", "./storage/videos"),
    "clips": os.getenv("CLIPS_OUTPUT_PATH", "./storage/clips"),
    "segments": os.getenv("SEGMENTS_PATH", "./storage/segments"),
    "share_cards": "./storage/share_cards",  # NEW
}

# Add endpoint to serve share cards
@app.get("/api/share_cards/{filename}")
async def get_share_card(filename: str):
    """Serve a generated share card image."""
    card_path = os.path.join(STORAGE_PATHS["share_cards"], filename)

    if not os.path.exists(card_path):
        raise HTTPException(status_code=404, detail="Share card not found")

    return FileResponse(
        card_path,
        media_type="image/png",
        filename=filename,
    )
```

### Phase 5: Frontend Display (30 min)

**Update `frontend/components/MomentCard.tsx`:**
```typescript
// Inside MomentCard component
{moment.share_card_url && (
  <div className="mt-4">
    <h4 className="text-sm font-medium mb-2">Share Card</h4>
    <img
      src={`${API_URL}${moment.share_card_url}`}
      alt="Share card"
      className="w-full rounded-lg border border-gray-700"
    />
    <button
      onClick={() => downloadImage(moment.share_card_url)}
      className="mt-2 px-4 py-2 bg-blue-600 rounded hover:bg-blue-700"
    >
      Download Share Card
    </button>
  </div>
)}
```

## Environment Setup

### Backend `.env`
```bash
FAL_KEY=your_fal_api_key  # Get from fal.ai dashboard
```

### Get Fal API Key
1. Sign up at https://fal.ai/
2. Go to dashboard → API Keys
3. Generate new key
4. Add to `.env`

## Dependencies

**Add to `backend/requirements.txt`:**
```txt
fal-client==0.11.0
requests==2.32.3  # For downloading Fal images
```

**Already have:**
- `Pillow==11.2.1` ✅ (for image compositing)

## Cost Estimate

**Fal.ai FLUX Schnell Pricing:**
- ~$0.003 per image
- 100 moments = $0.30
- 1000 moments = $3.00

**Very affordable for hackathon/demo use!**

## Effort Estimate

| Phase | Time | Complexity |
|-------|------|-----------|
| Phase 1: Fal setup | 30min | Low |
| Phase 2: Generator code | 2h | Medium |
| Phase 3: Pipeline integration | 30min | Low |
| Phase 4: API endpoint | 15min | Low |
| Phase 5: Frontend display | 30min | Low |
| **Total** | **~3.75h** | **Medium** |

## Success Criteria

✅ Share card generated automatically after moment analysis
✅ Card includes hype/risk scores, moment summary, and timestamp
✅ Consistent visual branding across all cards
✅ Generated in < 5 seconds
✅ `share_card_url` populated in moment data
✅ Downloadable from frontend

## Future Enhancements

- Multiple card templates (Instagram, Twitter, LinkedIn formats)
- Team/player branding customization
- Animated share cards (video overlays)
- A/B testing different designs
- Custom fonts and color schemes per sport

## Resources

- [Fal.ai Python Client](https://pypi.org/project/fal-client/)
- [FLUX.1 Schnell API Docs](https://fal.ai/models/fal-ai/flux/schnell)
- [Fal.ai Documentation](https://docs.fal.ai)
- [Deploy Text-to-Image Model](https://docs.fal.ai/examples/serverless/deploy-text-to-image-model)

---

**Sources:**
- [Fal.ai Docs](https://docs.fal.ai)
- [Fal.ai Python client](https://pypi.org/project/fal-client/)
- [FLUX.1 [schnell] Model](https://fal.ai/models/fal-ai/flux/schnell)
- [Generative AI APIs | fal.ai](https://fal.ai/)
