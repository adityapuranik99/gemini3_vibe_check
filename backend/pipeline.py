"""
End-to-end video processing pipeline.

Combines ingestion → detection → Gemini analysis.
"""

import logging
from typing import Optional
import asyncio
import os
from pathlib import Path

from ingest import VideoIngester, RingBuffer
from detection import FeatureExtractor, CandidateDetector
from gemini_analyzer import GeminiAnalyzer
from clips import ClipAssembler
from share_card_generator import ShareCardGenerator
from models import CandidateEvent, MomentAnalysis

logger = logging.getLogger(__name__)


class VideoPipeline:
    """
    Full video processing pipeline.

    Ingests video → extracts features → detects candidates → analyzes with Gemini.
    """

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        motion_threshold: float = 0.65,
        audio_threshold: float = 0.65,
        clips_output_dir: str = "./storage/clips",
    ):
        """
        Initialize pipeline.

        Args:
            gemini_api_key: API key for Gemini (optional, uses env var)
            motion_threshold: Threshold for motion detection
            audio_threshold: Threshold for audio detection
            clips_output_dir: Directory for generated clips
        """
        self.feature_extractor = FeatureExtractor()
        self.candidate_detector = CandidateDetector(
            motion_threshold=motion_threshold,
            audio_threshold=audio_threshold,
            smoothing_window=3,      # Faster reaction to audio spikes (was 5)
            cooldown_seconds=10.0,   # Longer cooldown to avoid duplicate detections (was 5)
        )
        self.gemini_analyzer = GeminiAnalyzer(api_key=gemini_api_key)
        self.clip_assembler = ClipAssembler(output_dir=clips_output_dir)
        self.share_card_generator = ShareCardGenerator()
        self.ring_buffer = RingBuffer(duration_seconds=70.0, fps=30.0)

        logger.info("🎬 Video pipeline initialized")

    async def process_video(
        self,
        video_path: str,
        stream_id: str,
        on_candidate: Optional[callable] = None,
        on_moment: Optional[callable] = None,
    ) -> list[MomentAnalysis]:
        """
        Process a video file end-to-end.

        Args:
            video_path: Path to MP4 file
            stream_id: Unique stream identifier
            on_candidate: Callback when candidate detected
            on_moment: Callback when moment analyzed

        Returns:
            List of analyzed moments
        """
        logger.info(f"🎥 Starting pipeline for {stream_id}: {video_path}")

        moments = []

        with VideoIngester(video_path, stream_id, realtime_mode=False) as ingester:
            logger.info(f"📹 Video info: {ingester.get_info()}")

            # Process frames
            for timestamp, frame in ingester.ingest_frames():
                # Store in ring buffer
                self.ring_buffer.push_frame(timestamp, frame)

                # Extract features
                features = self.feature_extractor.extract_features(frame)
                self.ring_buffer.push_features(timestamp, features)

                # Check for candidate
                audio_rms = ingester.extract_audio_rms()
                candidate = self.candidate_detector.process_frame(
                    timestamp, features, audio_rms
                )

                if candidate:
                    logger.info(f"🔔 Candidate detected: {candidate.candidate_id} at t={timestamp:.2f}s")

                    if on_candidate:
                        await on_candidate(candidate)

                    # Analyze with Gemini
                    moment = await self._analyze_candidate(candidate, ingester)

                    if moment:
                        # Generate clip for the moment
                        clip_path = await self._generate_clip(moment, ingester.video_path)
                        if clip_path:
                            moment.clip_url = f"/api/clips/{Path(clip_path).name}"

                        # Generate share card (Static only - animation disabled for performance)
                        try:
                            # Save a keyframe from the ring buffer for the card
                            keyframe_path = await self._save_keyframe(moment)

                            # Generate static card
                            card_path = await self.share_card_generator.generate_static_card(
                                moment,
                                theme_name="stadium", # Default theme
                                keyframe_path=keyframe_path
                            )
                            if card_path:
                                moment.share_card_url = f"/api/share_cards/images/{Path(card_path).name}"
                        except Exception as e:
                            logger.warning(f"⚠️ Share card generation failed: {e}")

                        moments.append(moment)

                        if on_moment:
                            await on_moment(moment)

        logger.info(f"✅ Pipeline complete: {len(moments)} moments detected")
        return moments

    async def _analyze_candidate(
        self,
        candidate: CandidateEvent,
        ingester: VideoIngester,
    ) -> Optional[MomentAnalysis]:
        """
        Analyze a candidate with Gemini.

        Args:
            candidate: Detected candidate event
            ingester: Video ingester for context

        Returns:
            MomentAnalysis or None if analysis fails
        """
        t0 = candidate.t0

        # Get video duration from ingester
        video_duration = ingester.duration_seconds

        # Estimate reaction time (use audio peak as proxy)
        # In production, we'd wait for actual reaction, but for demo we estimate
        tr_estimate = t0 + 15.0  # Assume reaction peaks ~15s after play

        # Clamp tr to video duration (can't be beyond the video end)
        tr = min(tr_estimate, video_duration - 1.0)

        # Ensure tr is at least t0 + 5s (minimum reaction window)
        if tr < t0 + 5.0:
            tr = min(t0 + 5.0, video_duration - 1.0)

        logger.debug(f"Reaction time: t0={t0:.2f}s, tr={tr:.2f}s (duration={video_duration:.2f}s)")

        # Get frames from ring buffer around the moment
        frame_window_start = max(0, t0 - 10.0)
        frame_window_end = min(tr + 10.0, video_duration)
        frames = self.ring_buffer.get_frames_in_window(frame_window_start, frame_window_end)

        if not frames:
            logger.warning(f"⚠️  No frames in buffer for moment {candidate.candidate_id}")
            return None

        logger.info(f"🤖 Analyzing with Gemini: {candidate.candidate_id}")

        try:
            # Run Gemini analysis (this is a blocking call, but fast with Flash model)
            moment = await asyncio.to_thread(
                self.gemini_analyzer.analyze_moment,
                candidate_id=candidate.candidate_id,
                t0=t0,
                tr=tr,
                frames=frames,
                motion_score=candidate.signals.motion,
                audio_rms=candidate.signals.audio_rms,
            )

            logger.info(
                f"✅ Moment analyzed: {moment.moment_id} "
                f"(type={moment.moment_type}, hype={moment.scores.hype})"
            )

            return moment

        except Exception as e:
            logger.error(f"❌ Gemini analysis failed for {candidate.candidate_id}: {e}")
            return None

    async def _generate_clip(
        self,
        moment: MomentAnalysis,
        source_video: str,
    ) -> Optional[str]:
        """
        Generate a video clip for a moment.

        Args:
            moment: MomentAnalysis with clip recipe
            source_video: Path to source video

        Returns:
            Path to generated clip or None
        """
        try:
            logger.info(f"✂️  Generating clip for {moment.moment_id}")

            # Run clip assembly in thread (ffmpeg is blocking)
            clip_path = await asyncio.to_thread(
                self.clip_assembler.assemble_moment_clip,
                source_video,
                moment,
            )

            logger.info(f"✅ Clip generated: {clip_path}")
            return clip_path

        except Exception as e:
            logger.error(f"❌ Clip generation failed for {moment.moment_id}: {e}")
            return None

    async def _save_keyframe(self, moment: MomentAnalysis) -> Optional[str]:
        """Save a keyframe image from the ring buffer for the share card."""
        try:
            # Pick frame at t0
            frames = self.ring_buffer.get_frames_in_window(moment.t0 - 0.1, moment.t0 + 0.1)
            if not frames:
                return None
            
            # Use the middle frame in the window
            _, frame = frames[len(frames) // 2]
            
            # Convert to PIL and save
            from PIL import Image
            import numpy as np
            
            # BGR to RGB
            frame_rgb = frame[:, :, ::-1]
            img = Image.fromarray(frame_rgb)
            
            output_path = f"./storage/share_cards/keyframes/{moment.moment_id}_keyframe.png"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            img.save(output_path)
            
            return output_path
        except Exception as e:
            logger.warning(f"Could not save keyframe: {e}")
            return None


async def process_video_simple(
    video_path: str,
    stream_id: str = "demo",
) -> list[MomentAnalysis]:
    """
    Simple helper to process a video and return moments.

    Args:
        video_path: Path to video file
        stream_id: Stream identifier

    Returns:
        List of detected and analyzed moments
    """
    pipeline = VideoPipeline()
    moments = await pipeline.process_video(video_path, stream_id)
    return moments
