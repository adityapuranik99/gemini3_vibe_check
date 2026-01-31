"""Test script for Gemini analyzer (requires API key)."""

import os
import sys
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for API key
if not os.getenv("GOOGLE_API_KEY"):
    print("❌ GOOGLE_API_KEY not found in .env file")
    print("Please add your Gemini API key to backend/.env:")
    print("GOOGLE_API_KEY=your_key_here")
    sys.exit(1)

from gemini_analyzer import GeminiAnalyzer, build_analysis_prompt


def test_prompt_building():
    """Test prompt generation."""
    print("\n🧪 Testing prompt building...")

    prompt = build_analysis_prompt(
        candidate_id="c_0001",
        t0=120.5,
        tr_estimate=135.2,
        motion_score=0.85,
        audio_rms=0.92,
        sport_type="football",
    )

    assert "c_0001" in prompt
    assert "120.5" in prompt
    assert "football" in prompt

    print("✅ Prompt building works!")
    print(f"\nSample prompt (first 500 chars):\n{prompt[:500]}...")


def test_analyzer_init():
    """Test Gemini analyzer initialization."""
    print("\n🧪 Testing Gemini analyzer initialization...")

    try:
        analyzer = GeminiAnalyzer()
        print(f"✅ Gemini analyzer initialized successfully")
        print(f"   Model: gemini-3-flash-001")
        return analyzer
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        sys.exit(1)


def test_keyframe_selection(analyzer):
    """Test keyframe selection logic."""
    print("\n🧪 Testing keyframe selection...")

    # Create mock frames
    frames = []
    for i in range(20):
        timestamp = float(i)
        frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        frames.append((timestamp, frame))

    keyframes = analyzer._select_keyframes(
        frames,
        t0=8.0,  # Play at 8s
        tr=15.0,  # Reaction at 15s
        max_frames=4,
    )

    print(f"   Selected {len(keyframes)} keyframes from {len(frames)} total frames")
    print(f"   Keyframe timestamps: {[f'{t:.2f}s' for t, _ in keyframes]}")

    assert len(keyframes) <= 4
    assert len(keyframes) > 0

    print("✅ Keyframe selection works!")


def test_fallback_moment(analyzer):
    """Test fallback moment creation."""
    print("\n🧪 Testing fallback moment generation...")

    moment = analyzer._create_fallback_moment(
        candidate_id="c_0042",
        t0=100.0,
        tr=115.0,
    )

    print(f"   Moment ID: {moment.moment_id}")
    print(f"   Type: {moment.moment_type}")
    print(f"   Summary: {moment.summary}")
    print(f"   Hype: {moment.scores.hype}, Risk: {moment.scores.risk}")

    assert moment.moment_id == "m_0042"
    assert moment.t0 == 100.0
    assert moment.tr == 115.0

    print("✅ Fallback moment generation works!")


def test_real_analysis(analyzer):
    """Test real Gemini API call with mock frames."""
    print("\n🧪 Testing real Gemini API analysis...")
    print("⚠️  This will make an actual API call and may take a few seconds")

    # Create mock frames (simulate a sports moment)
    frames = []
    for i in range(10):
        timestamp = 100.0 + i
        # Create a simple gradient frame (mock video frame)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:, :, 0] = np.linspace(0, 255, 480).reshape(-1, 1)  # Red gradient
        frame[:, :, 1] = i * 25  # Green increases over time
        frames.append((timestamp, frame))

    try:
        moment = analyzer.analyze_moment(
            candidate_id="c_test",
            t0=102.0,
            tr=108.0,
            frames=frames,
            motion_score=0.85,
            audio_rms=0.9,
            sport_type="football",
        )

        print(f"\n✅ Gemini API call successful!")
        print(f"\n📊 Analysis Results:")
        print(f"   Moment ID: {moment.moment_id}")
        print(f"   Type: {moment.moment_type}")
        print(f"   Summary: {moment.summary}")
        print(f"   Why it matters: {moment.why_it_matters}")
        print(f"   Hype score: {moment.scores.hype}")
        print(f"   Risk score: {moment.scores.risk}")
        print(f"   Clip segments: {len(moment.clip_recipe)}")
        print(f"\n   Post copy (hype): {moment.post_copy.hype}")

        return True

    except Exception as e:
        print(f"\n⚠️  Gemini API call failed: {e}")
        print("This might be due to:")
        print("  - Invalid API key")
        print("  - Model not available (gemini-3-flash-001)")
        print("  - Rate limiting")
        print("  - Network issues")
        return False


if __name__ == "__main__":
    print("🚀 Testing Gemini Analyzer\n")

    try:
        # Test 1: Prompt building
        test_prompt_building()

        # Test 2: Analyzer initialization
        analyzer = test_analyzer_init()

        # Test 3: Keyframe selection
        test_keyframe_selection(analyzer)

        # Test 4: Fallback moment
        test_fallback_moment(analyzer)

        # Test 5: Real API call (optional, requires working API key)
        print("\n" + "=" * 60)
        response = input("\n🤔 Do you want to test a real Gemini API call? (y/n): ")

        if response.lower() == 'y':
            success = test_real_analysis(analyzer)
            if not success:
                print("\n⚠️  API call failed, but other tests passed")
        else:
            print("\nSkipping real API test")

        print("\n" + "=" * 60)
        print("✅ All basic tests passed!")
        print("\nThe Gemini analyzer is ready to use.")
        print("Make sure your GOOGLE_API_KEY is set correctly in .env")

    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
