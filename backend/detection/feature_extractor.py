"""Feature extraction from video frames - motion, scene changes, visual intensity."""

import cv2
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Extracts cheap, fast features from video frames for candidate detection.

    Features:
    - Motion score: frame-to-frame difference (proxy for action intensity)
    - Scene change: large visual changes (shot boundaries)
    - Visual energy: overall brightness/contrast changes
    """

    def __init__(self):
        self.prev_frame_gray: Optional[np.ndarray] = None
        self.prev_histogram: Optional[np.ndarray] = None

    def extract_features(self, frame: np.ndarray) -> dict:
        """
        Extract all features from a frame.

        Args:
            frame: BGR frame from OpenCV (H, W, 3)

        Returns:
            Dictionary with feature scores (0-1 normalized)
        """
        # Convert to grayscale for processing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        features = {
            "motion": self._compute_motion_score(gray),
            "scene_change": self._detect_scene_change(frame),
            "visual_energy": self._compute_visual_energy(gray),
        }

        # Update state for next frame
        self.prev_frame_gray = gray.copy()

        return features

    def _compute_motion_score(self, gray_frame: np.ndarray) -> float:
        """
        Compute motion score using frame difference.

        Higher values = more motion/action.
        """
        if self.prev_frame_gray is None:
            return 0.0

        # Compute absolute difference
        diff = cv2.absdiff(self.prev_frame_gray, gray_frame)

        # Threshold to remove noise
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

        # Normalize by image size
        motion_pixels = np.sum(thresh > 0)
        total_pixels = thresh.shape[0] * thresh.shape[1]
        motion_score = motion_pixels / total_pixels

        # Clamp to 0-1 range
        return min(motion_score * 10, 1.0)  # Scale up and clamp

    def _detect_scene_change(self, frame: np.ndarray) -> float:
        """
        Detect scene changes using histogram comparison.

        Large changes indicate shot boundaries or dramatic transitions.
        """
        # Compute color histogram
        hist = cv2.calcHist([frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist = cv2.normalize(hist, hist).flatten()

        if self.prev_histogram is None:
            self.prev_histogram = hist
            return 0.0

        # Compare histograms using correlation
        correlation = cv2.compareHist(self.prev_histogram, hist, cv2.HISTCMP_CORREL)

        # Update state
        self.prev_histogram = hist

        # Low correlation = big change (scene change)
        scene_change_score = 1.0 - correlation
        return max(0.0, scene_change_score)

    def _compute_visual_energy(self, gray_frame: np.ndarray) -> float:
        """
        Compute visual energy using Laplacian variance (edge detection).

        Higher values = more visual activity/detail.
        """
        laplacian = cv2.Laplacian(gray_frame, cv2.CV_64F)
        variance = laplacian.var()

        # Normalize to 0-1 (empirically tuned threshold)
        energy_score = min(variance / 1000.0, 1.0)
        return energy_score

    def reset(self):
        """Reset internal state (e.g., when starting a new video)."""
        self.prev_frame_gray = None
        self.prev_histogram = None
        logger.debug("Feature extractor state reset")
