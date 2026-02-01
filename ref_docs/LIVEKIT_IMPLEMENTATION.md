# LiveKit + Gemini Live Integration Plan (30-Second Demo)

## Goal
Add screen sharing capability to Vibe Check that uses Gemini Live API to watch a 30-second sports clip and detect exciting moments in real-time.

## Time Budget: 3.5 Hours (1:00 PM - 4:30 PM)

## Scope
- **Keep:** Existing upload flow (unchanged)
- **Add:** Screen share flow with Gemini Live detection
- **Limit:** 30-second demo only (fits within 2-minute Gemini Live limit)

## Architecture Overview

```
Frontend (Home Page)
  ↓
User clicks "Share Screen" → selects broadcast window
  ↓
LiveKit room created + screen track published
  ↓
Python LiveKit Agent subscribes to screen track
  ↓
Agent starts Gemini Live session (audio + video)
  ↓
Screen frames (1 FPS) → Gemini Live API
  ↓
Gemini watches for 30 seconds, detects exciting moments
  ↓
Gemini responds: "Exciting moment at 15 seconds - dunk over defender"
  ↓
Agent parses response → creates moment in backend
  ↓
Frontend polls /api/moments → displays with "LIVE" badge
```

## Implementation Steps

### 1. Frontend: Add Screen Share Button (1 hour)

**File:** `frontend/app/page.tsx`

**Changes:**
- Add "Share Screen" button next to "Upload Video"
- Install `livekit-client` package
- Create LiveKit room connection
- Capture screen track using `getDisplayMedia()`
- Publish screen track to room
- Show "Monitoring..." state during 30s session
- Auto-stop after 30 seconds

**UI Flow:**
```
[Upload Video]  [Share Screen] ← NEW button
     ↓
Click "Share Screen"
     ↓
Browser prompt: Select window/tab/screen
     ↓
"Monitoring for moments... (30s)"
     ↓
Countdown: 30, 29, 28...
     ↓
"Session complete. Check Producer view for moments."
```

**Dependencies to add:**
```bash
cd frontend
bun add livekit-client
```

### 2. Backend: LiveKit Agent with Gemini Live (2 hours)

**New directory:** `backend/agent/`

**Files to create:**

#### `backend/agent/agent.py`
- Main agent entry point
- Subscribe to LiveKit room
- Capture screen track frames
- Initialize Gemini Live API session
- Send prompt: "Watch this basketball game for 30 seconds. When you see exciting moments like dunks, buzzer beaters, or big plays, tell me the timestamp and describe what happened."
- Stream frames to Gemini (1 FPS)
- Parse Gemini responses
- Call backend API to create moments

#### `backend/agent/requirements.txt`
```
livekit
livekit-agents
google-generativeai
aiohttp
python-dotenv
```

**Environment variables needed:**
```
LIVEKIT_URL=ws://localhost:7880  # or LiveKit Cloud URL
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
GOOGLE_API_KEY=your_gemini_key
VIBE_CHECK_BACKEND_URL=http://localhost:8002
```

### 3. Backend: API Endpoint for Agent (30 minutes)

**File:** `backend/main.py`

**Add endpoint:**
```python
@app.post("/api/moments/create_from_agent")
async def create_moment_from_agent(moment_data: dict):
    """
    Called by LiveKit agent when Gemini detects a moment.

    Expected payload:
    {
        "timestamp": 15.0,
        "description": "Dunk over defender",
        "excitement_level": 9,
        "source": "livekit_screenshare",
        "session_id": "session_abc123"
    }
    """
    # Create moment without clip (just metadata for now)
    moment = MomentAnalysis(
        moment_id=f"m_{uuid.uuid4().hex[:8]}",
        source="livekit_screenshare",
        session_id=moment_data["session_id"],
        summary=moment_data["description"],
        scores={"hype": moment_data["excitement_level"] * 10, "risk": 0},
        # ... other fields with defaults
    )
    moments_store[moment.moment_id] = moment
    return {"success": True, "moment_id": moment.moment_id}
```

### 4. Frontend: Display Live Moments (30 minutes)

**File:** `frontend/types/moments.ts`

**Update Moment type:**
```typescript
type Moment = {
  moment_id: string;
  source: "upload" | "livekit_screenshare";  // NEW
  session_id?: string;  // NEW (for LiveKit sessions)
  // ... existing fields
}
```

**File:** `frontend/app/producer/page.tsx`

**Add badge to moment cards:**
```tsx
{moment.source === "livekit_screenshare" && (
  <span className="px-2 py-1 bg-red-500 text-white text-xs rounded">
    LIVE
  </span>
)}
```

### 5. Testing & Integration (30 minutes)

**Test scenario:**
1. Start backend: `uvicorn main:app --reload --port 8002`
2. Start LiveKit agent: `cd backend/agent && python agent.py`
3. Start frontend: `cd frontend && bun dev`
4. Open browser → click "Share Screen"
5. Select window playing 30s NBA highlight clip
6. Watch for moments to appear in Producer view with "LIVE" badge

**Success criteria:**
- ✅ Screen sharing starts successfully
- ✅ Agent connects to LiveKit room
- ✅ Gemini receives frames and watches for 30s
- ✅ At least 1 moment detected and appears in Producer view
- ✅ Moment has "LIVE" badge
- ✅ Upload flow still works unchanged

## Files to Create/Modify

### New Files:
- `backend/agent/agent.py` - LiveKit agent main loop
- `backend/agent/requirements.txt` - Agent dependencies

### Modified Files:
- `frontend/app/page.tsx` - Add screen share button
- `frontend/package.json` - Add livekit-client
- `frontend/types/moments.ts` - Add source field
- `frontend/app/producer/page.tsx` - Display LIVE badge
- `backend/main.py` - Add /api/moments/create_from_agent endpoint
- `backend/models.py` - Add source and session_id fields to MomentAnalysis

## Dependencies to Install

**Frontend:**
```bash
bun add livekit-client
```

**Backend Agent:**
```bash
cd backend/agent
python -m venv venv
source venv/bin/activate
pip install livekit livekit-agents google-generativeai aiohttp python-dotenv
```

## Environment Setup

**Create `.env` in `backend/agent/`:**
```
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
GOOGLE_API_KEY=your_gemini_api_key
VIBE_CHECK_BACKEND_URL=http://localhost:8002
```

**Note:** For quick testing, you can use LiveKit's local dev server or sign up for LiveKit Cloud free tier.

## Fallback Plan (if blocked by 4:00 PM)

If LiveKit integration hits major blockers:
1. Keep upload flow (already working)
2. Pivot to Fal integration for share card generation (1-2 hours, lower risk)
3. Still have solid demo with upload + AI detection + share cards

## Key Simplifications for 30s Demo

1. **No recording:** Don't save screen share to file, just detect moments
2. **No clips:** Moments from screen share won't have video clips (just metadata)
3. **No Stage A:** Skip motion/audio detection, let Gemini do all detection
4. **No voice commands:** Just screen watching (voice agent deferred to future)
5. **Single session:** One 30s session per screen share (no continuous monitoring)

## Gemini Live Prompt Template

```
You are watching a live basketball game broadcast for 30 seconds.

Your task:
1. Watch for exciting moments like dunks, three-pointers, blocks, or buzzer beaters
2. When you see something exciting, respond with JSON:
   {
     "moment_detected": true,
     "timestamp": <seconds from start>,
     "description": "<brief description>",
     "excitement_level": <1-10>
   }

3. Only report truly exciting moments (7+ excitement level)
4. Be concise in descriptions (under 10 words)

Start watching now.
```

## Critical Success Path

**Must have working by 4:30 PM:**
1. Screen share button works (browser captures screen)
2. LiveKit agent receives screen track
3. Gemini Live API connection established
4. At least 1 moment detected from 30s clip
5. Moment appears in Producer view with "LIVE" badge

**Nice to have (if time permits):**
- Countdown timer during 30s session
- Better error handling
- Session history/replay
- Multiple moment detection in one session

## Questions Resolved

1. **Recording:** No - just detection for 30s demo
2. **Duration:** Exactly 30 seconds (auto-stop)
3. **Clips:** Not generated for screen share (just metadata)
4. **Voice:** Not included (screen watching only)
5. **LiveKit setup:** Use local dev server or Cloud free tier

## Next Steps After Demo

If successful:
1. Add session recording for clip extraction
2. Extend beyond 30s using session resumption
3. Add voice commands for hands-free control
4. Integrate with existing Stage A/B pipeline
5. Support continuous monitoring (restart sessions)

Ready to implement!
