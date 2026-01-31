"""Test with more realistic thresholds."""

import logging
import asyncio
from dotenv import load_dotenv
from pipeline import VideoPipeline

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)

VIDEO_PATH = "/home/aditya.puranik@corsairhq.com/gex/YTDowncom_YouTube_This-Alcaraz-Sinner-point-was-so-ridicul_Media_r3UFpeA1vJw_001_1080p.mp4"

async def main():
    print("🎾 Testing Pipeline with Lower Thresholds")
    print("=" * 70)

    # Use lower thresholds that match real-world signals
    pipeline = VideoPipeline(
        motion_threshold=0.8,  # Lower from 0.65
        audio_threshold=0.25,  # Much lower - audio peaks at 0.3
    )

    candidates = []
    moments = []

    async def on_candidate(candidate):
        candidates.append(candidate)
        print(f"  🔔 Candidate: {candidate.candidate_id} at t={candidate.t0:.1f}s")
        print(f"      motion={candidate.signals.motion:.3f}, audio={candidate.signals.audio_rms:.3f}")

    async def on_moment(moment):
        moments.append(moment)
        print(f"  ✨ Moment: {moment.moment_type} (hype={moment.scores.hype}, risk={moment.scores.risk})")

    print("\nProcessing video...\n")
    result = await pipeline.process_video(
        VIDEO_PATH,
        "tennis_test",
        on_candidate=on_candidate,
        on_moment=on_moment,
    )

    print("\n" + "=" * 70)
    print(f"✅ Complete: {len(candidates)} candidates → {len(result)} moments")

    if result:
        print("\nMoments:")
        for m in result:
            print(f"  - {m.moment_type} at t={m.t0:.1f}s: hype={m.scores.hype}, risk={m.scores.risk}")
            print(f"    Post: {m.post_copy.hype[:80]}...")

if __name__ == "__main__":
    asyncio.run(main())
