"""Ring buffer for storing recent video frames and features."""

from collections import deque
from typing import Any, Tuple
import numpy as np


class RingBuffer:
    """
    Fixed-size ring buffer to store recent frames and their metadata.

    We need to buffer at least 60+ seconds of history because:
    - Pre-roll: 30-40s before reaction to capture the play context
    - Post-roll: ~10s after reaction
    - Slack for late decisions
    """

    def __init__(self, duration_seconds: float = 70.0, fps: float = 30.0):
        """
        Initialize ring buffer.

        Args:
            duration_seconds: How many seconds of video to buffer
            fps: Frames per second (used to calculate buffer size)
        """
        self.duration_seconds = duration_seconds
        self.fps = fps
        self.max_size = int(duration_seconds * fps)

        # Deques for different data types
        self.frames: deque[Tuple[float, np.ndarray]] = deque(maxlen=self.max_size)
        self.features: deque[Tuple[float, dict]] = deque(maxlen=self.max_size)

    def push_frame(self, timestamp: float, frame: np.ndarray):
        """Add a frame to the buffer."""
        self.frames.append((timestamp, frame))

    def push_features(self, timestamp: float, features: dict):
        """Add extracted features for a timestamp."""
        self.features.append((timestamp, features))

    def get_frames_in_window(
        self, start_time: float, end_time: float
    ) -> list[Tuple[float, np.ndarray]]:
        """
        Get all frames in a time window [start_time, end_time].

        Returns:
            List of (timestamp, frame) tuples
        """
        return [
            (ts, frame)
            for ts, frame in self.frames
            if start_time <= ts <= end_time
        ]

    def get_features_in_window(
        self, start_time: float, end_time: float
    ) -> list[Tuple[float, dict]]:
        """Get all features in a time window."""
        return [
            (ts, feats)
            for ts, feats in self.features
            if start_time <= ts <= end_time
        ]

    def get_latest_frame(self) -> Tuple[float, np.ndarray] | None:
        """Get the most recent frame."""
        return self.frames[-1] if self.frames else None

    def get_latest_features(self) -> Tuple[float, dict] | None:
        """Get the most recent features."""
        return self.features[-1] if self.features else None

    def clear(self):
        """Clear the buffer."""
        self.frames.clear()
        self.features.clear()

    def __len__(self) -> int:
        return len(self.frames)

    @property
    def is_full(self) -> bool:
        """Check if buffer is at capacity."""
        return len(self.frames) >= self.max_size
