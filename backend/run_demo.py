"""Quick script to trigger video processing via API."""

import requests
import time

API_URL = "http://localhost:8001"
VIDEO_PATH = "/home/aditya.puranik@corsairhq.com/gex/YTDowncom_YouTube_This-Alcaraz-Sinner-point-was-so-ridicul_Media_r3UFpeA1vJw_001_1080p.mp4"

print("🎾 Starting Vibe Check Demo\n")

# Check backend health
print("1. Checking backend health...")
try:
    response = requests.get(f"{API_URL}/")
    print(f"   ✅ Backend is running: {response.json()}")
except Exception as e:
    print(f"   ❌ Backend not reachable: {e}")
    print("   Make sure backend is running on port 8001")
    exit(1)

# Start video ingestion
print("\n2. Starting video ingestion...")
try:
    response = requests.post(
        f"{API_URL}/api/ingest/start",
        json={
            "video_path": VIDEO_PATH,
            "stream_id": "tennis_demo"
        }
    )
    print(f"   ✅ Ingestion started: {response.json()}")
except Exception as e:
    print(f"   ❌ Failed to start ingestion: {e}")
    exit(1)

# Poll for moments
print("\n3. Waiting for moments to be detected...")
print("   (This will take 30-60 seconds as the video is processed)\n")

for i in range(30):
    time.sleep(2)
    try:
        response = requests.get(f"{API_URL}/api/moments")
        data = response.json()
        count = data.get("count", 0)

        print(f"   [{i*2}s] Moments detected: {count}")

        if count > 0:
            print(f"\n   ✅ {count} moments ready!")
            break
    except Exception as e:
        print(f"   ⚠️  Error polling: {e}")

# Show final results
print("\n4. Final results:")
try:
    response = requests.get(f"{API_URL}/api/moments")
    data = response.json()
    moments = data.get("moments", [])

    print(f"   Total moments: {len(moments)}")
    for moment in moments:
        print(f"\n   Moment {moment['moment_id']}:")
        print(f"     Summary: {moment['summary']}")
        print(f"     Hype: {moment['scores']['hype']}, Risk: {moment['scores']['risk']}")
        if moment.get('clip_url'):
            print(f"     Clip: {API_URL}{moment['clip_url']}")

except Exception as e:
    print(f"   ❌ Failed to fetch moments: {e}")

print("\n🎉 Demo complete!")
print(f"\n📱 Open frontend to see moments: http://localhost:3001/producer")
