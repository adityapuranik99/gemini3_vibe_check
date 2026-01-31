"""Test the full pipeline with a real video file."""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

from pipeline import process_video_simple

VIDEO_PATH = "/home/aditya.puranik@corsairhq.com/gex/YTDowncom_YouTube_This-Alcaraz-Sinner-point-was-so-ridicul_Media_r3UFpeA1vJw_001_1080p.mp4"


async def main():
    print("🎾 Testing Vibe Check Pipeline with Real Tennis Video")
    print("=" * 70)
    print(f"\n📹 Video: {Path(VIDEO_PATH).name}")
    print(f"   Path: {VIDEO_PATH}\n")

    if not Path(VIDEO_PATH).exists():
        print(f"❌ Video file not found: {VIDEO_PATH}")
        sys.exit(1)

    print("🚀 Starting pipeline...")
    print("   This will:")
    print("   1. Ingest video frame by frame")
    print("   2. Extract motion/audio features")
    print("   3. Detect candidate moments")
    print("   4. Analyze with Gemini 3")
    print("   5. Generate moment packages\n")

    try:
        moments = await process_video_simple(VIDEO_PATH, stream_id="tennis_demo")

        print("\n" + "=" * 70)
        print(f"✅ Pipeline Complete! Detected {len(moments)} moments\n")

        if not moments:
            print("⚠️  No moments detected.")
            print("   This could mean:")
            print("   - Video is too short")
            print("   - Not enough motion/audio activity")
            print("   - Detection thresholds too high")
        else:
            for i, moment in enumerate(moments, 1):
                print(f"\n{'='*70}")
                print(f"🎯 MOMENT #{i}: {moment.moment_id}")
                print(f"{'='*70}")
                print(f"\n📊 Type: {moment.moment_type}")
                print(f"⏱️  Play time: {moment.t0:.2f}s")
                print(f"👏 Reaction time: {moment.tr:.2f}s")
                print(f"\n📝 Summary:")
                print(f"   {moment.summary}")
                print(f"\n💡 Why it matters:")
                for reason in moment.why_it_matters:
                    print(f"   • {reason}")
                print(f"\n🔥 Scores:")
                print(f"   Hype: {moment.scores.hype}/100")
                print(f"   Risk: {moment.scores.risk}/100")

                if moment.risk_notes:
                    print(f"\n⚠️  Risk notes:")
                    for note in moment.risk_notes:
                        print(f"   • {note}")

                print(f"\n✂️  Clip recipe ({len(moment.clip_recipe)} segments):")
                for seg in moment.clip_recipe:
                    duration = seg.end_s - seg.start_s
                    print(f"   {seg.label:20} {seg.start_s:6.1f}s → {seg.end_s:6.1f}s ({duration:4.1f}s)")

                print(f"\n📱 Post copy variants:")
                print(f"\n   🔥 HYPE:")
                print(f"      {moment.post_copy.hype}")
                print(f"\n   📰 NEUTRAL:")
                print(f"      {moment.post_copy.neutral}")
                print(f"\n   ✅ BRAND SAFE:")
                print(f"      {moment.post_copy.brand_safe}")

        print("\n" + "=" * 70)
        print("🎉 Test complete!")

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
