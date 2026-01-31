"""Candidate detection module - Stage A (cheap signals)."""

from .feature_extractor import FeatureExtractor
from .candidate_detector import CandidateDetector

__all__ = ["FeatureExtractor", "CandidateDetector"]
