# LiveKit + Gemini Live Integration - Setup Guide

## 🎯 What Was Implemented

The LiveKit integration adds real-time screen share capability to Vibe Check, allowing producers to share their broadcast window and have AI detect exciting moments live during the game.

### Key Features Added

1. **Screen Share Button** - One-click screen sharing from the home page
2. **LiveKit Agent** - Python agent that monitors screen shares using Gemini AI
3. **Real-time Moment Detection** - Gemini analyzes frames at 1 FPS for 30 seconds
4. **LIVE Badge** - Moments detected from screen share are marked with a red "LIVE" badge
5. **Seamless Integration** - Works alongside existing video upload flow

## 📁 Files Created/Modified

### Backend Files

**Created:**
- `backend/agent/agent.py` - Main LiveKit agent with Gemini integration
- `backend/agent/requirements.txt` - Agent dependencies
- `backend/agent/.env.example` - Environment configuration template
- `backend/agent/README.md` - Detailed agent documentation

**Modified:**
- `backend/models.py` - Added `source` and `session_id` fields to MomentAnalysis
- `backend/main.py` - Added `/api/moments/create_from_agent` endpoint

### Frontend Files

**Created:**
- `frontend/components/ScreenShare.tsx` - Screen share UI component
- `frontend/app/api/livekit-token/route.ts` - LiveKit token generation endpoint
- `frontend/.env.example` - Frontend environment configuration

**Modified:**
- `frontend/app/page.tsx` - Added screen share button to home page
- `frontend/types/moments.ts` - Added `source` and `session_id` to MomentAnalysis interface
- `frontend/app/producer/page.tsx` - Added "LIVE" badge display for screen share moments
- `frontend/package.json` - Added livekit-client and livekit-server-sdk dependencies

## 🚀 Quick Start

### 1. Install Dependencies

**Backend Agent:**
```bash
cd backend/agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

**Frontend:**
```bash
cd frontend
bun install  # Already done - livekit packages installed
cp .env.example .env.local
# Edit .env.local if needed
```

### 2. Get API Keys

**Google Gemini API Key:**
1. Visit https://aistudio.google.com/app/apikey
2. Create new API key
3. Add to `backend/agent/.env` as `GOOGLE_API_KEY`

**LiveKit (Option A - Local Dev):**
```bash
# Install LiveKit CLI
brew install livekit  # macOS
# or
curl -sSL https://get.livekit.io | bash  # Linux

# Start local server
livekit-server --dev
```

This gives you:
- URL: `ws://localhost:7880`
- API Key: `devkey`
- API Secret: `secret`

**LiveKit (Option B - Cloud):**
1. Sign up at https://livekit.io
2. Create project
3. Copy credentials to `.env` files

### 3. Start Everything

**Terminal 1 - Backend:**
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8002
```

**Terminal 2 - LiveKit Agent:**
```bash
cd backend/agent
source venv/bin/activate
python agent.py
```

**Terminal 3 - Frontend:**
```bash
cd frontend
bun dev
```

### 4. Test the Flow

1. Open browser to http://localhost:3000
2. Click **"Share Screen (30s Demo)"** button
3. Select your broadcast window (play a basketball highlight video)
4. Watch the countdown - agent analyzes for 30 seconds
5. Click "Producer" view to see detected moments with 🔴 LIVE badge

## 🎬 Demo Flow

```
Home Page
  ↓
[Share Screen (30s Demo)] button
  ↓
Browser asks: "Select window to share"
  ↓
User selects broadcast window with basketball game
  ↓
"MONITORING LIVE" - 30 second countdown
  ↓
LiveKit Agent receives frames at 1 FPS
  ↓
Gemini analyzes each frame for exciting moments
  ↓
Moments automatically appear in Producer view
  ↓
Producer sees moments with 🔴 LIVE badge
```

## 🔧 Configuration

### Environment Variables

**backend/agent/.env:**
```env
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
GOOGLE_API_KEY=your_key_here
VIBE_CHECK_BACKEND_URL=http://localhost:8002
```

**frontend/.env.local:**
```env
NEXT_PUBLIC_LIVEKIT_URL=ws://localhost:7880
NEXT_PUBLIC_LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
NEXT_PUBLIC_API_URL=http://localhost:8002
```

### Customization

**Change Session Duration:**
In `backend/agent/agent.py`:
```python
SESSION_DURATION = 30  # Change to desired seconds
```

**Change Frame Rate:**
```python
FRAME_RATE = 1  # Frames per second (1 = one frame per second)
```

**Customize Detection Prompt:**
Edit the prompt in `agent.py` → `analyze_frame_with_gemini()` to detect different types of moments or sports.

## 🎯 How It Works

### Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Browser   │────────▶│   LiveKit    │────────▶│   Agent     │
│  (Screen    │  Screen │    Server    │  Video  │  (Python)   │
│   Share)    │  Track  │              │  Frames │             │
└─────────────┘         └──────────────┘         └──────┬──────┘
                                                         │
                                                         ▼
                                                  ┌─────────────┐
                                                  │   Gemini    │
                                                  │   AI API    │
                                                  └──────┬──────┘
                                                         │
                                                         ▼
                                                  ┌─────────────┐
                                                  │  Backend    │
                                                  │  (Moments)  │
                                                  └─────────────┘
```

### Data Flow

1. **Frontend** captures screen using `getDisplayMedia()`
2. **Frontend** publishes video track to LiveKit room
3. **Agent** subscribes to the screen share track
4. **Agent** extracts frames at 1 FPS
5. **Agent** sends each frame to Gemini with detection prompt
6. **Gemini** analyzes frame and returns JSON with excitement level
7. **Agent** filters moments (excitement ≥7) and posts to backend
8. **Backend** creates moment with `source: "livekit_screenshare"`
9. **Frontend** polls `/api/moments` and displays with LIVE badge

## 🐛 Troubleshooting

### "Screen share permission denied"
- Browser blocked screen share permission
- Try again and click "Allow"

### "Failed to get token"
- LiveKit server not running
- Check `LIVEKIT_URL` in `.env` files
- Verify API key/secret match

### "GOOGLE_API_KEY not set"
- Missing or incorrect API key in `backend/agent/.env`
- Get key from https://aistudio.google.com/app/apikey

### No moments detected
- Video content may not be exciting enough
- Check agent logs for frame processing
- Verify Gemini API key is valid
- Try lowering excitement threshold in agent code

### Agent crashes
- Check frame format compatibility
- Review error logs in terminal
- Verify all dependencies installed correctly

## 📊 Monitoring

**Check Agent Status:**
```bash
# In agent terminal, you'll see:
📸 Frame 1 at 0.0s
📸 Frame 2 at 1.0s
🎯 Moment detected at 5.2s: Dunk over defender
✅ Moment sent to backend: m_abc12345
```

**Check Backend:**
```bash
# In backend terminal, you'll see:
✨ Live moment created: m_abc12345 - Dunk over defender
```

**Check Frontend:**
- Open Producer view
- Look for moments with red 🔴 LIVE badge
- Badge appears in both detail view and sidebar

## 🎉 What's Next

After confirming the basic flow works:

1. **Extend Duration** - Support longer sessions with session resumption
2. **Voice Commands** - Add voice control for hands-free operation
3. **Clip Extraction** - Record and extract clips from screen share
4. **Multi-Sport** - Customize prompts for different sports
5. **Advanced Analysis** - Use Gemini Live API's streaming features
6. **Production Deploy** - Set up proper token generation and security

## 📚 Additional Resources

- [LiveKit Documentation](https://docs.livekit.io/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Agent Implementation Details](backend/agent/README.md)
- [LiveKit Implementation Plan](ref_docs/LIVEKIT_IMPLEMENTATION.md)

---

**Questions or Issues?**
Check the detailed README in `backend/agent/README.md` or review the implementation plan in `ref_docs/LIVEKIT_IMPLEMENTATION.md`.
