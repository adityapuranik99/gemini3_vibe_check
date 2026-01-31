"""Test audio extraction in the pipeline with detailed logging."""

import logging
import asyncio
from ingest import VideoIngester, RingBuffer
from detection import FeatureExtractor, CandidateDetector

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

VIDEO_PATH = "/home/aditya.puranik@corsairhq.com/gex/YTDowncom_YouTube_This-Alcaraz-Sinner-point-was-so-ridicul_Media_r3UFpeA1vJw_001_1080p.mp4"

async def main():
    print("🎾 Testing Audio in Detection Pipeline")
    print("=" * 70)

    feature_extractor = FeatureExtractor()
    candidate_detector = CandidateDetector(
        motion_threshold=0.65,
        audio_threshold=0.65,
        combined_threshold=0.5,
    )

    with VideoIngester(VIDEO_PATH, "test", realtime_mode=False) as ingester:
        print(f"\nVideo: {ingester.duration_seconds:.1f}s @ {ingester.fps:.0f} fps")
        if ingester.audio_samples is not None:
            print(f"Audio: {len(ingester.audio_samples)} samples @ {ingester.audio_sample_rate} Hz")
        else:
            print("⚠️  No audio found!")

        print("\nProcessing frames...\n")
        print(f"{'Time':>6} | {'Motion':>6} | {'Audio':>6} | {'Combined':>8} | Status")
        print("-" * 70)

        frame_count = 0
        candidates = []

        for timestamp, frame in ingester.ingest_frames():
            # Extract features
            features = feature_extractor.extract_features(frame)

            # Get audio RMS
            audio_rms = ingester.extract_audio_rms()

            # Check for candidate
            candidate = candidate_detector.process_frame(timestamp, features, audio_rms)

            # Log every second
            if frame_count % int(ingester.fps) == 0:
                motion = features.get("motion", 0.0)
                combined = (motion + audio_rms) / 2
                status = "🔔 TRIGGER" if candidate else ""
                print(f"{timestamp:>6.1f} | {motion:>6.3f} | {audio_rms:>6.3f} | {combined:>8.3f} | {status}")

            if candidate:
                candidates.append(candidate)

            frame_count += 1

        print("\n" + "=" * 70)
        print(f"✅ Processed {frame_count} frames in {timestamp:.1f}s")
        print(f"🔔 Detected {len(candidates)} candidates")

        if candidates:
            print("\nCandidates:")
            for c in candidates:
                print(f"  - {c.candidate_id} at t={c.t0:.1f}s: motion={c.signals.motion:.3f}, audio={c.signals.audio_rms:.3f}")

if __name__ == "__main__":
    asyncio.run(main())
