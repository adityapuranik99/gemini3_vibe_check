"""Service for fetching official player photos for share card generation."""

import os
import logging
import hashlib
import json
import re
from pathlib import Path
from typing import Optional
import requests
from datetime import datetime, timedelta

# Try to import google-genai SDK for search grounding
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

logger = logging.getLogger(__name__)


class PlayerImageService:
    """
    Fetches and caches official player photos for accurate share card generation.

    Uses Google Search (or other sources) to find official player photos,
    then caches them locally to avoid repeated lookups.
    """

    def __init__(self, cache_dir: str = "./storage/player_photos"):
        """
        Initialize player image service.

        Args:
            cache_dir: Directory to cache player photos
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(days=7)  # Photos don't change often

        # Initialize Gemini client for search grounding
        self.genai_client = None
        if HAS_GENAI:
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                try:
                    self.genai_client = genai.Client(api_key=api_key)
                    logger.info("✅ Gemini search grounding enabled for player photos")
                except Exception as e:
                    logger.warning(f"Failed to initialize Gemini client: {e}")
            else:
                logger.warning("GOOGLE_API_KEY not set, player photo search disabled")
        else:
            logger.warning("google-genai SDK not available, player photo search disabled")

        logger.info(f"📸 Player image service initialized (cache: {self.cache_dir})")

    async def get_player_photo(
        self,
        player_name: str,
        team: Optional[str] = None,
    ) -> Optional[str]:
        """
        Get official player photo URL or local path.

        Args:
            player_name: Full name of the player
            team: Team name (helps with search accuracy)

        Returns:
            Local file path to cached photo, or None if not found
        """
        if not player_name:
            return None

        # Generate cache key
        cache_key = self._generate_cache_key(player_name, team)
        cached_path = self.cache_dir / f"{cache_key}.jpg"

        # Check cache
        if self._is_cache_valid(cached_path):
            logger.info(f"✅ Using cached photo for {player_name}")
            return str(cached_path)

        # Fetch new photo
        logger.info(f"🔍 Fetching official photo for {player_name} ({team})")
        photo_url = await self._search_player_photo(player_name, team)

        if not photo_url:
            logger.warning(f"❌ No photo found for {player_name}")
            return None

        # Download and cache
        try:
            downloaded_path = await self._download_and_cache(photo_url, cached_path)
            logger.info(f"✅ Cached photo for {player_name}")
            return str(downloaded_path)
        except Exception as e:
            logger.error(f"❌ Failed to download photo: {e}")
            return None

    async def _search_player_photo(
        self,
        player_name: str,
        team: Optional[str],
    ) -> Optional[str]:
        """
        Search for official player photo using Gemini search grounding.

        Uses Google Search via Gemini to find official headshot/portrait URLs
        from trusted sources like official league sites, ESPN, etc.

        Returns:
            URL to player photo, or None
        """
        if not self.genai_client:
            logger.warning("Gemini client not available, skipping photo search")
            return None

        try:
            # Build search prompt
            team_context = f" who plays for {team}" if team else ""
            prompt = f"""Find an official headshot or portrait photo URL for the professional athlete {player_name}{team_context}.

Search for their official photo and return ONLY the direct image URL.

Priority sources (in order):
1. Official league websites (nba.com, nfl.com, mlb.com, etc.)
2. Official team websites
3. ESPN player pages
4. Sports Reference
5. Wikipedia (if it has a clear headshot)

Requirements for the image URL:
- Must be a direct link to an image file (ending in .jpg, .jpeg, .png, or containing /image/ or /photo/ in path)
- Should be a professional headshot or portrait (not action shot)
- Should be high quality (at least 200x200 pixels)
- Must be publicly accessible (no authentication required)

Respond with JSON:
```json
{{
  "image_url": "https://example.com/player-photo.jpg",
  "source": "nba.com",
  "confidence": "high|medium|low"
}}
```

If you cannot find a suitable image, respond with:
```json
{{
  "image_url": null,
  "source": null,
  "confidence": "none"
}}
```
"""

            # Use search grounding
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            config = types.GenerateContentConfig(
                tools=[grounding_tool],
                response_mime_type="application/json",
            )

            logger.info(f"🔍 Searching for photo of {player_name}...")
            response = self.genai_client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
                config=config,
            )

            # Parse response
            result_text = response.text
            logger.debug(f"Gemini photo search response: {result_text}")

            # Try to parse JSON
            try:
                data = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                json_match = re.search(r'\{[^}]+\}', result_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                else:
                    logger.warning("Could not parse JSON from photo search response")
                    return None

            image_url = data.get("image_url")
            source = data.get("source", "unknown")
            confidence = data.get("confidence", "unknown")

            if image_url and confidence != "none":
                logger.info(f"✅ Found player photo from {source} (confidence: {confidence})")
                # Validate the URL looks like an image
                if self._is_valid_image_url(image_url):
                    return image_url
                else:
                    logger.warning(f"URL doesn't look like a valid image: {image_url}")
                    return None
            else:
                logger.warning(f"No suitable photo found for {player_name}")
                return None

        except Exception as e:
            logger.error(f"❌ Photo search failed: {e}")
            return None

    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL looks like a valid image URL."""
        if not url:
            return False

        url_lower = url.lower()

        # Check for image extensions
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        if any(url_lower.endswith(ext) or f"{ext}?" in url_lower for ext in image_extensions):
            return True

        # Check for common image path patterns
        image_patterns = ['/image/', '/photo/', '/headshot/', '/player/', '/athletes/']
        if any(pattern in url_lower for pattern in image_patterns):
            return True

        # Check for image CDN patterns
        cdn_patterns = ['cloudinary', 'imgix', 'akamai', 'fastly', 'cdn']
        if any(pattern in url_lower for pattern in cdn_patterns):
            return True

        return False

    async def _download_and_cache(
        self,
        photo_url: str,
        cache_path: Path,
    ) -> Path:
        """
        Download photo and save to cache.

        Args:
            photo_url: URL of the photo to download
            cache_path: Where to save the cached file

        Returns:
            Path to cached file
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(photo_url, timeout=15, stream=True, headers=headers)
        response.raise_for_status()

        # Check content type
        content_type = response.headers.get("content-type", "")
        if not any(img_type in content_type.lower() for img_type in ["image/", "octet-stream"]):
            logger.warning(f"Unexpected content type: {content_type}")

        with open(cache_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Verify the file is a valid image
        try:
            from PIL import Image
            img = Image.open(cache_path)
            img.verify()
            logger.info(f"✅ Downloaded valid image: {img.format} {img.size}")
        except Exception as e:
            logger.error(f"Downloaded file is not a valid image: {e}")
            cache_path.unlink(missing_ok=True)
            raise ValueError(f"Invalid image file: {e}")

        return cache_path

    def _generate_cache_key(self, player_name: str, team: Optional[str]) -> str:
        """Generate cache key from player name and team."""
        key_string = f"{player_name}_{team or 'unknown'}".lower()
        return hashlib.md5(key_string.encode()).hexdigest()

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cached photo exists and is within TTL."""
        if not cache_path.exists():
            return False

        # Check age
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime

        return age < self.cache_ttl

    def clear_cache(self):
        """Clear all cached photos."""
        for file in self.cache_dir.glob("*.jpg"):
            file.unlink()
        logger.info("🗑️  Player photo cache cleared")
