"""Gemini 3 analyzer for moment understanding and packaging."""

import os
import logging
from typing import Optional
import google.generativeai as genai
from PIL import Image
import io
import numpy as np

from models import MomentAnalysis, MomentType, MomentScores, PostCopy, ClipRecipe
from .prompts import build_analysis_prompt

logger = logging.getLogger(__name__)


class GeminiAnalyzer:
    """
    Stage B: High-quality moment analysis using Gemini 3.

    Takes candidate moments and produces structured MomentAnalysis outputs
    with hype/risk scores, clip recipes, and post copy variants.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-3-flash-preview",  # Using Gemini 3 Flash preview
    ):
        """
        Initialize Gemini analyzer.

        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
            model_name: Gemini model to use
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found. Set it in .env or pass as parameter."
            )

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Initialize model with structured output schema
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 32000,  # Gemini 3 Flash supports up to 65536
            "response_mime_type": "application/json",
        }

        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
        )

        logger.info(f"🤖 Gemini analyzer initialized with model: {model_name}")

    def analyze_moment(
        self,
        candidate_id: str,
        t0: float,
        tr: float,
        frames: list[tuple[float, np.ndarray]],
        motion_score: float,
        audio_rms: float,
        sport_type: str = "unknown",
    ) -> MomentAnalysis:
        """
        Analyze a candidate moment using Gemini 3.

        Args:
            candidate_id: Candidate ID from detection
            t0: Play moment timestamp
            tr: Reaction peak timestamp
            frames: List of (timestamp, frame_array) tuples
            motion_score: Motion intensity (0-1)
            audio_rms: Audio RMS level (0-1)
            sport_type: Type of sport

        Returns:
            MomentAnalysis with structured output
        """
        logger.info(f"🔍 Analyzing moment {candidate_id} (t0={t0:.2f}s, tr={tr:.2f}s)")

        # Build prompt
        prompt = build_analysis_prompt(
            candidate_id=candidate_id,
            t0=t0,
            tr_estimate=tr,
            motion_score=motion_score,
            audio_rms=audio_rms,
            sport_type=sport_type,
        )

        # Prepare frames for Gemini (sample keyframes)
        keyframes = self._select_keyframes(frames, t0, tr)
        pil_images = [self._numpy_to_pil(frame) for _, frame in keyframes]

        try:
            # Call Gemini with multimodal input
            response = self.model.generate_content(
                [prompt] + pil_images,
            )

            # Parse structured JSON response
            result = response.text
            logger.debug(f"Gemini response: {result}")

            # Parse into MomentAnalysis
            moment = self._parse_response(result, candidate_id, t0, tr)

            logger.info(
                f"✅ Moment analyzed: {moment.moment_type} "
                f"(hype={moment.scores.hype}, risk={moment.scores.risk})"
            )

            return moment

        except Exception as e:
            logger.error(f"❌ Gemini analysis failed: {e}")
            # Return a fallback moment
            return self._create_fallback_moment(candidate_id, t0, tr)

    def _select_keyframes(
        self,
        frames: list[tuple[float, np.ndarray]],
        t0: float,
        tr: float,
        max_frames: int = 4,
    ) -> list[tuple[float, np.ndarray]]:
        """
        Select representative keyframes from the clip.

        We want frames that show:
        1. The action (around t0)
        2. The reaction (around tr)
        """
        if not frames:
            return []

        keyframes = []

        # Frame at t0 (play moment)
        play_frame = min(frames, key=lambda f: abs(f[0] - t0))
        keyframes.append(play_frame)

        # Frame at tr (reaction peak)
        reaction_frame = min(frames, key=lambda f: abs(f[0] - tr))
        if reaction_frame[0] != play_frame[0]:
            keyframes.append(reaction_frame)

        # Add 1-2 more frames for context if we have room
        if len(keyframes) < max_frames and len(frames) > 2:
            # Frame slightly before t0
            before_frame = min(frames, key=lambda f: abs(f[0] - (t0 - 2.0)))
            if before_frame not in keyframes:
                keyframes.insert(0, before_frame)

        # Sort by timestamp
        keyframes.sort(key=lambda f: f[0])

        logger.debug(f"Selected {len(keyframes)} keyframes: {[f'{t:.2f}s' for t, _ in keyframes]}")
        return keyframes[:max_frames]

    def _numpy_to_pil(self, frame: np.ndarray) -> Image.Image:
        """Convert numpy array (OpenCV BGR) to PIL Image (RGB)."""
        # OpenCV uses BGR, PIL uses RGB
        if frame.shape[2] == 3:
            frame_rgb = frame[:, :, ::-1]  # BGR to RGB
        else:
            frame_rgb = frame

        return Image.fromarray(frame_rgb)

    def _repair_truncated_json(self, json_str: str) -> str:
        """Attempt to repair truncated JSON by closing open brackets/braces."""
        # Count open brackets
        open_braces = json_str.count('{') - json_str.count('}')
        open_brackets = json_str.count('[') - json_str.count(']')

        # Remove trailing incomplete content (after last complete value)
        # Look for patterns like incomplete strings or trailing commas
        import re

        # Remove trailing incomplete string (unclosed quote)
        if json_str.count('"') % 2 != 0:
            # Find last complete key-value or array element
            last_complete = max(
                json_str.rfind('",'),
                json_str.rfind('"},'),
                json_str.rfind('],'),
                json_str.rfind('},'),
                json_str.rfind(': "'),
            )
            if last_complete > 0:
                # Try to find a good truncation point
                for end_pattern in ['",', '"},', '],', '},', '}', ']']:
                    pos = json_str.rfind(end_pattern)
                    if pos > 0:
                        json_str = json_str[:pos + len(end_pattern)]
                        break

        # Remove trailing comma if present
        json_str = re.sub(r',\s*$', '', json_str.strip())

        # Recount after cleanup
        open_braces = json_str.count('{') - json_str.count('}')
        open_brackets = json_str.count('[') - json_str.count(']')

        # Close open brackets and braces
        json_str += ']' * open_brackets
        json_str += '}' * open_braces

        return json_str

    def _parse_response(
        self,
        response_text: str,
        candidate_id: str,
        t0: float,
        tr: float,
    ) -> MomentAnalysis:
        """Parse Gemini JSON response into MomentAnalysis with robust error handling."""
        import json
        import re

        # Clean response text - remove comments and trailing commas
        cleaned_text = response_text
        cleaned_text = re.sub(r'//.*?\n|/\*.*?\*/', '', cleaned_text, flags=re.DOTALL)  # Remove comments
        cleaned_text = re.sub(r',(\s*[}\]])', r'\1', cleaned_text)  # Remove trailing commas

        data = None

        # Try 1: Parse JSON directly
        try:
            data = json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}. Attempting cleanup...")

        # Try 2: Extract from markdown code blocks
        if data is None:
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', cleaned_text, re.DOTALL)
            if json_match:
                try:
                    extracted = json_match.group(1)
                    extracted = re.sub(r',(\s*[}\]])', r'\1', extracted)
                    data = json.loads(extracted)
                    logger.info("Successfully extracted JSON from code block")
                except Exception:
                    pass

        # Try 3: Find JSON object in response
        if data is None:
            json_match = re.search(r'\{.*', cleaned_text, re.DOTALL)
            if json_match:
                try:
                    extracted = json_match.group(0)
                    extracted = re.sub(r',(\s*[}\]])', r'\1', extracted)
                    data = json.loads(extracted)
                    logger.info("Successfully extracted JSON object")
                except Exception:
                    pass

        # Try 4: Repair truncated JSON
        if data is None:
            json_match = re.search(r'\{.*', cleaned_text, re.DOTALL)
            if json_match:
                try:
                    extracted = json_match.group(0)
                    repaired = self._repair_truncated_json(extracted)
                    repaired = re.sub(r',(\s*[}\]])', r'\1', repaired)
                    data = json.loads(repaired)
                    logger.info("Successfully repaired and parsed truncated JSON")
                except Exception as ex:
                    logger.error(f"Failed to repair JSON: {ex}")
                    logger.error(f"Original: {extracted[:500]}...")
                    logger.error(f"Repaired attempt: {repaired[:500]}...")

        # If all parsing attempts failed, raise exception to trigger fallback
        if data is None:
            logger.error(f"All JSON parsing attempts failed")
            logger.error(f"Response text: {response_text[:500]}...")
            raise ValueError("Could not parse Gemini response as JSON")

        # Generate moment ID
        moment_id = f"m_{candidate_id.split('_')[1]}"

        # Safely extract moment_type with validation
        moment_type_str = data.get("moment_type", "other").lower()
        # Handle invalid moment types
        valid_types = [t.value for t in MomentType]
        if moment_type_str not in valid_types:
            logger.warning(f"Invalid moment_type '{moment_type_str}', using 'other'")
            moment_type_str = "other"

        # Safely extract scores
        scores_data = data.get("scores", {})
        if isinstance(scores_data, dict):
            hype = scores_data.get("hype", 50)
            risk = scores_data.get("risk", 50)
        else:
            hype, risk = 50, 50

        # Safely extract why_it_matters
        why_it_matters = data.get("why_it_matters", [])
        if not isinstance(why_it_matters, list):
            why_it_matters = [str(why_it_matters)] if why_it_matters else []

        # Safely extract risk_notes
        risk_notes = data.get("risk_notes", [])
        if not isinstance(risk_notes, list):
            risk_notes = [str(risk_notes)] if risk_notes else []

        # Safely extract clip_recipe
        clip_recipe_data = data.get("clip_recipe", [])
        clip_recipe = []
        if isinstance(clip_recipe_data, list):
            for seg in clip_recipe_data:
                try:
                    clip_recipe.append(ClipRecipe(**seg))
                except Exception as e:
                    logger.warning(f"Failed to parse clip segment: {e}")

        # Safely extract post_copy
        post_copy_data = data.get("post_copy", {})
        if isinstance(post_copy_data, dict):
            post_copy = PostCopy(
                hype=post_copy_data.get("hype", "Exciting moment!"),
                neutral=post_copy_data.get("neutral", "Notable play."),
                brand_safe=post_copy_data.get("brand_safe", "Great moment!"),
            )
        else:
            post_copy = PostCopy(
                hype="Exciting moment!",
                neutral="Notable play.",
                brand_safe="Great moment!",
            )

        return MomentAnalysis(
            moment_id=moment_id,
            t0=t0,
            tr=tr,
            moment_type=MomentType(moment_type_str),
            summary=data.get("summary", "Moment detected"),
            why_it_matters=why_it_matters,
            scores=MomentScores(hype=hype, risk=risk),
            risk_notes=risk_notes,
            clip_recipe=clip_recipe,
            post_copy=post_copy,
        )

    def _create_fallback_moment(
        self,
        candidate_id: str,
        t0: float,
        tr: float,
    ) -> MomentAnalysis:
        """Create a fallback moment when Gemini fails."""
        moment_id = f"m_{candidate_id.split('_')[1]}"

        return MomentAnalysis(
            moment_id=moment_id,
            t0=t0,
            tr=tr,
            moment_type=MomentType.OTHER,
            summary="Detected moment - analysis unavailable",
            why_it_matters=["High motion and audio activity detected"],
            scores=MomentScores(hype=50, risk=50),
            risk_notes=["Automated detection - manual review recommended"],
            clip_recipe=[
                ClipRecipe(label="play", start_s=max(0, t0 - 5), end_s=t0 + 5),
            ],
            post_copy=PostCopy(
                hype="Moment detected! Check it out.",
                neutral="Notable moment from the game.",
                brand_safe="Interesting play worth reviewing.",
            ),
        )

    def analyze_with_video_file(
        self,
        candidate_id: str,
        t0: float,
        tr: float,
        video_path: str,
        motion_score: float,
        audio_rms: float,
    ) -> MomentAnalysis:
        """
        Alternative method: Upload video file to Gemini for analysis.

        This is useful for longer clips where we want Gemini to see
        the full video context rather than just keyframes.
        """
        logger.info(f"📹 Uploading video for analysis: {video_path}")

        try:
            # Upload video file to Gemini
            video_file = genai.upload_file(path=video_path)
            logger.info(f"✅ Video uploaded: {video_file.uri}")

            # Wait for processing
            import time
            while video_file.state.name == "PROCESSING":
                time.sleep(1)
                video_file = genai.get_file(video_file.name)

            if video_file.state.name == "FAILED":
                raise ValueError(f"Video processing failed: {video_file.state}")

            # Build prompt
            prompt = build_analysis_prompt(
                candidate_id=candidate_id,
                t0=t0,
                tr_estimate=tr,
                motion_score=motion_score,
                audio_rms=audio_rms,
            )

            # Analyze with video
            response = self.model.generate_content(
                [prompt, video_file],
            )

            # Parse response
            moment = self._parse_response(response.text, candidate_id, t0, tr)

            # Clean up uploaded file
            genai.delete_file(video_file.name)

            return moment

        except Exception as e:
            logger.error(f"❌ Video analysis failed: {e}")
            return self._create_fallback_moment(candidate_id, t0, tr)
