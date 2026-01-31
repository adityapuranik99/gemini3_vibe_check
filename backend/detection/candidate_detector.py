"""Candidate detector - decides when to trigger Gemini analysis."""

from collections import deque
import numpy as np
from typing import Optional
import logging
import time

from models import CandidateEvent, CandidateSignals

logger = logging.getLogger(__name__)


class CandidateDetector:
    """
    Stage A: Cheap signal processing to detect moment candidates.

    Uses motion, audio, and optionally fan buzz to identify peaks.
    When a peak exceeds threshold, emit a candidate event.
    """

    def __init__(
        self,
        motion_threshold: float = 0.6,
        audio_threshold: float = 0.6,
        combined_threshold: float = 0.5,
        cooldown_seconds: float = 5.0,
        smoothing_window: int = 5,
    ):
        """
        Initialize candidate detector.

        Args:
            motion_threshold: Threshold for motion-only trigger
            audio_threshold: Threshold for audio-only trigger
            combined_threshold: Threshold for combined signal
            cooldown_seconds: Minimum time between candidate triggers
            smoothing_window: Number of frames to smooth signals over
        """
        self.motion_threshold = motion_threshold
        self.audio_threshold = audio_threshold
        self.combined_threshold = combined_threshold
        self.cooldown_seconds = cooldown_seconds
        self.smoothing_window = smoothing_window

        # Signal history for smoothing
        self.motion_history: deque[float] = deque(maxlen=smoothing_window)
        self.audio_history: deque[float] = deque(maxlen=smoothing_window)

        # State tracking
        self.last_trigger_time: Optional[float] = None
        self.candidate_counter = 0

    def process_frame(
        self,
        timestamp: float,
        features: dict,
        audio_rms: float = 0.5,
        fan_buzz: float = 0.0,
    ) -> Optional[CandidateEvent]:
        """
        Process a frame and decide if we have a candidate moment.

        Args:
            timestamp: Current timestamp in seconds
            features: Feature dict from FeatureExtractor
            audio_rms: Audio RMS level (0-1)
            fan_buzz: Fan reaction signal (0-1)

        Returns:
            CandidateEvent if triggered, None otherwise
        """
        # Extract motion score (combine motion + scene_change + visual_energy)
        motion = features.get("motion", 0.0)
        scene_change = features.get("scene_change", 0.0)
        visual_energy = features.get("visual_energy", 0.0)

        # Combine visual signals (weighted average)
        motion_score = (motion * 0.5) + (scene_change * 0.3) + (visual_energy * 0.2)

        # Update histories
        self.motion_history.append(motion_score)
        self.audio_history.append(audio_rms)

        # Compute smoothed signals
        motion_smooth = np.mean(self.motion_history) if self.motion_history else 0.0
        audio_smooth = np.mean(self.audio_history) if self.audio_history else 0.0

        # Check cooldown
        if self.last_trigger_time is not None:
            time_since_last = timestamp - self.last_trigger_time
            if time_since_last < self.cooldown_seconds:
                return None

        # Trigger conditions
        triggered = False
        trigger_reason = ""

        # 1. High motion alone
        if motion_smooth >= self.motion_threshold:
            triggered = True
            trigger_reason = f"motion_peak={motion_smooth:.2f}"

        # 2. High audio alone
        elif audio_smooth >= self.audio_threshold:
            triggered = True
            trigger_reason = f"audio_peak={audio_smooth:.2f}"

        # 3. Combined signal (moderate motion + moderate audio)
        elif (motion_smooth + audio_smooth) / 2 >= self.combined_threshold:
            triggered = True
            trigger_reason = f"combined={((motion_smooth + audio_smooth) / 2):.2f}"

        if triggered:
            self.candidate_counter += 1
            self.last_trigger_time = timestamp

            # Audio peak indicates crowd reaction AFTER the play
            # Set t0 to 10 seconds BEFORE the audio peak to capture the actual action
            lookback_seconds = 10.0
            play_start_time = max(0.0, timestamp - lookback_seconds)

            candidate = CandidateEvent(
                candidate_id=f"c_{self.candidate_counter:04d}",
                t0=play_start_time,  # Action starts BEFORE crowd reacts
                signals=CandidateSignals(
                    motion=motion_smooth,
                    audio_rms=audio_smooth,
                    fan_buzz=fan_buzz,
                ),
            )

            logger.info(
                f"🔔 Candidate detected: audio peak at t={timestamp:.2f}s, "
                f"play starts at t={play_start_time:.2f}s: {trigger_reason} "
                f"(motion={motion_smooth:.2f}, audio={audio_smooth:.2f})"
            )

            return candidate

        return None

    def reset(self):
        """Reset detector state."""
        self.motion_history.clear()
        self.audio_history.clear()
        self.last_trigger_time = None
        logger.debug("Candidate detector state reset")
