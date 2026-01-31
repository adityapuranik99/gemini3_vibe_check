# LiveKit + Gemini Live Voice Agent Integration Plan

## Goal: Voice-Controlled Producer Copilot

Integrate **LiveKit Agents framework** with **Gemini Live API** to enable hands-free voice commands for clip editing, approvals, and moment management during live event coverage.

## What Changed from Original Plan

**Original approach:** LiveKit rooms for human-to-human voice chat + data channels

**New approach:** LiveKit Agents + Gemini Live for AI-powered voice assistant that:
- Listens to producer voice commands
- Executes actions on moments and clips
- Responds with voice confirmation
- Still uses data channels for event sync

## Use Case: Hands-Free Producer Override

### Scenario: NBA game night, producer in the war room

**Current workflow (manual):**
1. Moment detected → producer reviews on screen
2. Producer clicks buttons to approve/adjust
3. Switches between keyboard/mouse during live event
4. Context switching slows down response time

**With Voice Agent:**
1. Moment detected → AI announces: "Detected dunk at 5:23, hype score 87"
2. Producer: "Start the clip 3 seconds earlier"
3. AI: "Adjusting clip start time..." → regenerates clip
4. Producer: "Approve that moment"
5. AI: "Moment approved and ready for social" → triggers approval event

**Key Benefit:** No context switching - producer stays focused on the game while commanding the system.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  LiveKit Room + Voice Agent                 │
│                                                              │
│  Audio Tracks:                                              │
│  ├── Producer mic ──────────> Voice Agent (listening)      │
│  └── Voice Agent ───────────> Producer speakers            │
│                                                              │
│  Data Channel:                                              │
│  ├── candidate.created ────> All participants              │
│  ├── moment.ready ─────────> All participants              │
│  ├── moment.approved ──────> All participants              │
│  └── clip.updated ─────────> All participants              │
└───────┬─────────────────────────────────────────────────────┘
        │
        │ LiveKit Agents SDK
        │
┌───────┴─────────────────────────────────────────────────────┐
│              Voice Agent (Python)                            │
│                                                              │
│  • Gemini Live API for speech-to-text + intent parsing     │
│  • Command routing: approve, adjust, info, export          │
│  • Calls Vibe Check backend API                            │
│  • Text-to-speech for confirmations                        │
└───────┬─────────────────────────────────────────────────────┘
        │
        │ HTTP POST /api/voice/command
        │
┌───────┴─────────────────────────────────────────────────────┐
│              Vibe Check Backend (FastAPI)                    │
│                                                              │
│  • VoiceCommandRouter                                       │
│  • Moment CRUD operations                                   │
│  • Clip regeneration pipeline                               │
│  • Event broadcasting                                        │
└─────────────────────────────────────────────────────────────┘
```

## Voice Commands Supported

### 1. Approval Commands
- "Approve that last moment"
- "Approve moment m_001"
- "Hold that moment"

### 2. Clip Editing Commands
- "Start the clip 3 seconds earlier"
- "End the clip 2 seconds later"
- "Remove the reaction button segment"
- "Make it 5 seconds shorter"

### 3. Information Queries
- "What's the hype score?"
- "What moments are pending?"
- "Tell me about the last moment"

### 4. Export Commands
- "Generate a vertical version"
- "Export for Instagram"
- "Create a 15-second cut"

## Implementation Plan

### Phase 1: LiveKit Agent Setup (2 hours)

**1. Clone starter kit:**
```bash
brew install livekit-cli
lk cloud auth
lk app create  # Select Python agent template
```

**2. Modify `src/agent.py`:**
```python
from livekit import agents, rtc
from livekit.agents import llm
import aiohttp

class VibeCheckVoiceAgent(agents.Agent):
    """Voice agent for producer commands."""

    def __init__(self, backend_url: str):
        self.backend_url = backend_url
        self.last_moment_id = None

    async def on_voice_command(self, transcript: str):
        """Parse and execute voice command."""
        # Use Gemini Live to understand intent
        intent = await self.parse_intent(transcript)

        # Route to backend
        result = await self.execute_command(intent)

        # Respond with voice
        await self.speak(result["message"])

    async def execute_command(self, intent: dict):
        """Call Vibe Check backend API."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.backend_url}/api/voice/command",
                json=intent
            ) as resp:
                return await resp.json()
```

**3. Configure Gemini Live API:**
```python
# In agent.py
from google import generativeai as genai

llm_config = {
    "model": "gemini-3-flash-preview",
    "instructions": """
You are a voice assistant for a live sports producer.
Parse commands related to:
- Approvals: approve, hold
- Clip edits: adjust start/end time, remove segments
- Info queries: hype score, moment details
- Exports: generate versions

Output structured JSON intent.
"""
}
```

### Phase 2: Backend Voice API (1.5 hours)

**1. Add VoiceCommandRouter (`backend/voice_router.py`):**
```python
"""Voice command routing and execution."""

from typing import Optional
from models import MomentAnalysis

class VoiceCommandRouter:
    """Routes voice commands to pipeline actions."""

    def __init__(self, moments_store: dict, pipeline):
        self.moments_store = moments_store
        self.pipeline = pipeline

    async def approve_moment(self, moment_id: str, by: str = "producer") -> dict:
        """Approve a moment via voice."""
        if moment_id not in self.moments_store:
            return {"status": "error", "message": f"Moment {moment_id} not found"}

        moment = self.moments_store[moment_id]
        moment.approval_status = "approved"

        return {
            "status": "ok",
            "message": f"Approved {moment.moment_type} moment with hype score {moment.scores.hype}"
        }

    async def adjust_clip_timing(
        self,
        moment_id: str,
        segment_label: str,
        start_offset: Optional[float] = None,
        end_offset: Optional[float] = None,
    ) -> dict:
        """Adjust clip recipe timing."""
        moment = self.moments_store[moment_id]

        for segment in moment.clip_recipe:
            if segment.label == segment_label or segment_label == "all":
                if start_offset:
                    segment.start_s += start_offset
                if end_offset:
                    segment.end_s += end_offset

        # Regenerate clip
        # TODO: Call pipeline._generate_clip()

        return {
            "status": "ok",
            "message": f"Adjusted {segment_label} timing"
        }

    async def get_moment_info(self, moment_id: str) -> dict:
        """Get moment details for voice response."""
        moment = self.moments_store[moment_id]

        message = (
            f"{moment.moment_type} at {moment.t0:.1f} seconds. "
            f"Hype score {moment.scores.hype}, risk score {moment.scores.risk}. "
            f"Status: {moment.approval_status}"
        )

        return {"status": "ok", "message": message}

    async def get_last_moment(self) -> Optional[str]:
        """Get most recent pending moment ID."""
        pending = [m for m in self.moments_store.values() if m.approval_status == "pending"]
        if pending:
            latest = max(pending, key=lambda m: m.t0)
            return latest.moment_id
        return None
```

**2. Add voice endpoint to `backend/main.py`:**
```python
from voice_router import VoiceCommandRouter

# Initialize voice router
voice_router: Optional[VoiceCommandRouter] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline, voice_router
    # ... existing setup ...

    # Initialize voice router
    voice_router = VoiceCommandRouter(moments_store, pipeline)

    yield

@app.post("/api/voice/command")
async def handle_voice_command(command: dict):
    """
    Handle voice commands from LiveKit agent.

    Expected payload:
    {
        "intent": "approve" | "adjust_clip" | "get_info",
        "params": {
            "moment_id": "m_001",
            "offset": -3.0,
            ...
        }
    }
    """
    if voice_router is None:
        raise HTTPException(status_code=503, detail="Voice router not initialized")

    intent = command.get("intent")
    params = command.get("params", {})

    if intent == "approve":
        result = await voice_router.approve_moment(
            moment_id=params.get("moment_id") or await voice_router.get_last_moment()
        )
    elif intent == "adjust_clip":
        result = await voice_router.adjust_clip_timing(
            moment_id=params["moment_id"],
            segment_label=params.get("segment_label", "all"),
            start_offset=params.get("start_offset"),
            end_offset=params.get("end_offset"),
        )
    elif intent == "get_info":
        result = await voice_router.get_moment_info(params["moment_id"])
    else:
        raise HTTPException(status_code=400, detail=f"Unknown intent: {intent}")

    return result
```

### Phase 3: Frontend LiveKit Integration (1 hour)

**1. Install dependencies:**
```bash
cd frontend
npm install livekit-client @livekit/components-react
```

**2. Create voice UI component (`frontend/components/VoiceAgent.tsx`):**
```typescript
'use client';

import { useVoiceAssistant, VoiceAssistantControlBar } from '@livekit/components-react';
import { LiveKitRoom } from '@livekit/components-react';

export function VoiceAgent({ roomName, token }: { roomName: string; token: string }) {
  return (
    <LiveKitRoom
      serverUrl={process.env.NEXT_PUBLIC_LIVEKIT_URL}
      token={token}
      connect={true}
    >
      <div className="flex items-center gap-4 p-4 bg-gray-800 rounded-lg">
        <div className="flex-1">
          <p className="text-sm text-gray-400">Voice Assistant Active</p>
          <p className="text-xs text-gray-500">Try: "Approve that last moment"</p>
        </div>
        <VoiceAssistantControlBar />
      </div>
    </LiveKitRoom>
  );
}
```

**3. Add to producer view (`frontend/app/producer/page.tsx`):**
```typescript
import { VoiceAgent } from '@/components/VoiceAgent';

// Inside ProducerView component
<VoiceAgent roomName={`war-room-${streamId}`} token={liveKitToken} />
```

### Phase 4: Testing & Refinement (1 hour)

**Test scenarios:**
1. Voice command: "Approve that last moment" → verify approval event fires
2. Voice command: "Start the clip 3 seconds earlier" → verify clip regenerates
3. Edge cases: no moments, invalid moment ID, ambiguous commands
4. Latency: measure command → execution → response time

## Dependencies

### Backend
```txt
# Add to backend/requirements.txt
livekit==0.17.5
livekit-api==0.7.2
aiohttp==3.9.1
```

### Frontend
```json
// Add to frontend/package.json
{
  "dependencies": {
    "livekit-client": "^2.0.0",
    "@livekit/components-react": "^2.0.0"
  }
}
```

### Voice Agent
```txt
# In agent directory (from lk app create)
livekit-agents
google-generativeai
aiohttp
```

## Environment Variables

```bash
# Backend .env
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
LIVEKIT_URL=wss://your-project.livekit.cloud

# Frontend .env.local
NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud

# Voice agent .env
GOOGLE_API_KEY=your_gemini_api_key
VIBE_CHECK_BACKEND_URL=http://localhost:8000
```

## Effort Estimate

| Phase | Time | Complexity |
|-------|------|-----------|
| Phase 1: Agent setup | 2h | Medium |
| Phase 2: Backend API | 1.5h | Low |
| Phase 3: Frontend UI | 1h | Low |
| Phase 4: Testing | 1h | Low |
| **Total** | **5.5h** | **Medium** |

## Resources

- LiveKit Gemini SuperHack: https://www.livekit.info/geminisuperhack
- LiveKit Agents Docs: https://docs.livekit.io/agents/overview/
- Gemini Live API: https://ai.google.dev/gemini-api/docs/live-api
- Quickstart repo: `lk app create` (select Python agent)

## Success Criteria

✅ Producer can approve moments by voice
✅ Producer can adjust clip timing by voice
✅ Agent responds with voice confirmation
✅ Sub-3 second latency from command to execution
✅ Data channel broadcasts updates to all roles

## Future Enhancements

- Multi-language support (Spanish, Portuguese)
- Contextual awareness ("What happened in that last play?")
- Proactive suggestions ("This moment is trending on Twitter")
- Multi-stream monitoring ("Watch camera 2 for better angle")
