"""Quick test script to verify the video processing pipeline."""

import sys
from pathlib import Path

# Test imports
try:
    from ingest import VideoIngester, RingBuffer
    from detection import FeatureExtractor, CandidateDetector
    from models import CandidateEvent
    print("✅ All imports successful!")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def test_feature_extractor():
    """Test feature extraction with dummy frames."""
    import numpy as np

    print("\n🧪 Testing FeatureExtractor...")
    extractor = FeatureExtractor()

    # Create dummy frames (simulating video frames)
    frame1 = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    frame2 = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)

    features1 = extractor.extract_features(frame1)
    features2 = extractor.extract_features(frame2)

    print(f"  Frame 1 features: {features1}")
    print(f"  Frame 2 features: {features2}")

    assert "motion" in features1
    assert "scene_change" in features1
    assert "visual_energy" in features1
    print("✅ FeatureExtractor working!")


def test_candidate_detector():
    """Test candidate detection logic."""
    print("\n🧪 Testing CandidateDetector...")
    detector = CandidateDetector(
        motion_threshold=0.75,  # Higher threshold
        audio_threshold=0.75,
        cooldown_seconds=3.0
    )

    # Fill up some history first (smoothing needs a few frames)
    for i in range(5):
        features_warmup = {"motion": 0.5, "scene_change": 0.4, "visual_energy": 0.5}
        detector.process_frame(float(i) * 0.1, features_warmup, audio_rms=0.5)

    # Test with low signals (should not trigger)
    features_low = {"motion": 0.3, "scene_change": 0.2, "visual_energy": 0.1}
    candidate = detector.process_frame(1.0, features_low, audio_rms=0.3)
    assert candidate is None
    print("  ✓ Low signals: No trigger (expected)")

    # Test with high motion (should trigger)
    features_high = {"motion": 0.9, "scene_change": 0.8, "visual_energy": 0.85}
    # Push it multiple times to build up smoothed average
    for i in range(5):
        candidate = detector.process_frame(2.0 + i * 0.1, features_high, audio_rms=0.8)
        if candidate:
            break
    assert candidate is not None, f"Expected trigger with high signals"
    assert isinstance(candidate, CandidateEvent)
    print(f"  ✓ High signals: Triggered! {candidate.candidate_id}")

    # Test cooldown (should not trigger even with high signals)
    candidate2 = detector.process_frame(3.0, features_high, audio_rms=0.8)
    assert candidate2 is None
    print("  ✓ Cooldown: No trigger (expected)")

    print("✅ CandidateDetector working!")


def test_ring_buffer():
    """Test ring buffer storage."""
    import numpy as np

    print("\n🧪 Testing RingBuffer...")
    buffer = RingBuffer(duration_seconds=5.0, fps=30.0)

    # Push some frames
    for i in range(10):
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        buffer.push_frame(float(i), frame)
        buffer.push_features(float(i), {"motion": 0.5, "audio": 0.3})

    print(f"  Buffer size: {len(buffer)} frames")

    # Get frames in window
    frames = buffer.get_frames_in_window(2.0, 6.0)
    features = buffer.get_features_in_window(2.0, 6.0)

    print(f"  Window [2.0, 6.0]: {len(frames)} frames, {len(features)} feature sets")
    assert len(frames) == 5
    assert len(features) == 5

    print("✅ RingBuffer working!")


def test_video_ingestion_basic():
    """Test VideoIngester initialization (no actual video file needed)."""
    print("\n🧪 Testing VideoIngester initialization...")

    # This will fail without a real video file, but we can test the class exists
    print("  ✓ VideoIngester class available")
    print("  ⚠ Skipping actual video test (need .mp4 file)")
    print("✅ VideoIngester structure ready!")


if __name__ == "__main__":
    print("🚀 Running Vibe Check Pipeline Tests\n")

    try:
        test_feature_extractor()
        test_candidate_detector()
        test_ring_buffer()
        test_video_ingestion_basic()

        print("\n" + "="*50)
        print("✅ ALL TESTS PASSED!")
        print("="*50)
        print("\nNext steps:")
        print("1. Add a test video file (NFL or Tennis MP4)")
        print("2. Test full video ingestion pipeline")
        print("3. Integrate Gemini 3 analyzer")
        print("4. Build clip assembler")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
