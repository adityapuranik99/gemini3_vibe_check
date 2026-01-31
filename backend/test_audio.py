"""Quick test of audio extraction."""

import sys
import logging
from ingest.video_ingester import VideoIngester

logging.basicConfig(level=logging.INFO)

# Use the tennis video
video_path = "/home/aditya.puranik@corsairhq.com/gex/YTDowncom_YouTube_This-Alcaraz-Sinner-point-was-so-ridicul_Media_r3UFpeA1vJw_001_1080p.mp4"

print("Testing audio extraction...")
print("=" * 60)

try:
    ingester = VideoIngester(video_path, "test_stream", realtime_mode=False)

    print(f"\nVideo Info:")
    print(f"  Duration: {ingester.duration_seconds:.2f}s")
    print(f"  FPS: {ingester.fps:.2f}")
    print(f"  Total frames: {ingester.total_frames}")

    if ingester.audio_samples is not None:
        print(f"\nAudio Info:")
        print(f"  Sample rate: {ingester.audio_sample_rate} Hz")
        print(f"  Total samples: {len(ingester.audio_samples)}")
        print(f"  Duration: {len(ingester.audio_samples) / ingester.audio_sample_rate:.2f}s")
        print(f"  Audio range: [{ingester.audio_samples.min():.3f}, {ingester.audio_samples.max():.3f}]")

        print(f"\nTesting RMS extraction at different timestamps:")
        test_timestamps = [0.0, 1.0, 2.0, 3.0, 4.0]
        for t in test_timestamps:
            frame_idx = int(t * ingester.fps)
            if frame_idx < ingester.total_frames:
                ingester.current_frame_idx = frame_idx
                rms = ingester.extract_audio_rms()
                print(f"  t={t:.1f}s: RMS = {rms:.3f}")
    else:
        print("\n⚠️  No audio extracted (video may not have audio track)")

    ingester.close()
    print("\n✅ Audio extraction test complete!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
