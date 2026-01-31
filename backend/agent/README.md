# LiveKit Agent - Vibe Check

AI-powered screen share monitoring agent that uses Gemini Live API to detect exciting moments in real-time.

## Overview

This agent connects to LiveKit rooms, subscribes to screen share video tracks, and analyzes frames using Google's Gemini AI to detect exciting moments in basketball games (or other live sports).

## Features

- 🖥️ **Screen Share Monitoring**: Subscribes to screen share tracks from LiveKit rooms
- 🤖 **Gemini AI Analysis**: Uses Gemini 1.5 Flash for real-time frame analysis
- ⚡ **Moment Detection**: Identifies exciting moments like dunks, three-pointers, blocks, etc.
- 🔄 **Backend Integration**: Automatically sends detected moments to Vibe Check backend
- ⏱️ **30-Second Sessions**: Optimized for quick demo sessions

## Prerequisites

1. **Python 3.9+** installed
2. **LiveKit Server** running (local or cloud)
3. **Google API Key** with Gemini API access
4. **Vibe Check Backend** running

## Installation

### 1. Create Virtual Environment

```bash
cd backend/agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
# LiveKit Configuration
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret

# Google AI Configuration
GOOGLE_API_KEY=your_gemini_api_key_here

# Backend URL
VIBE_CHECK_BACKEND_URL=http://localhost:8002
```

## LiveKit Setup

### Option 1: Local Development Server

Install LiveKit CLI:

```bash
brew install livekit  # macOS
# or
curl -sSL https://get.livekit.io | bash  # Linux
```

Start local server:

```bash
livekit-server --dev
```

This starts a local server with dev credentials:
- URL: `ws://localhost:7880`
- API Key: `devkey`
- API Secret: `secret`

### Option 2: LiveKit Cloud

1. Sign up at [livekit.io](https://livekit.io)
2. Create a project
3. Get your API key and secret
4. Update `.env` with your cloud credentials

## Getting a Google API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Copy the key to your `.env` file
4. Make sure Gemini API is enabled for your project

## Running the Agent

### 1. Start Vibe Check Backend

In a separate terminal:

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8002
```

### 2. Start LiveKit Agent

```bash
cd backend/agent
source venv/bin/activate
python agent.py
```

You should see:

```
🚀 Agent started
⏳ Waiting for participant to join...
```

### 3. Start Frontend

In another terminal:

```bash
cd frontend
bun dev
```

### 4. Test the Flow

1. Open browser to `http://localhost:3000`
2. Click "Share Screen (30s Demo)" button
3. Select your broadcast window (playing a basketball game)
4. Agent will analyze frames for 30 seconds
5. Detected moments appear in Producer view with "LIVE" badge

## How It Works

### Flow Diagram

```
User clicks "Share Screen"
         ↓
Frontend creates LiveKit room
         ↓
Frontend publishes screen share track
         ↓
Agent subscribes to screen share track
         ↓
Agent captures frames at 1 FPS
         ↓
Each frame sent to Gemini for analysis
         ↓
Gemini detects exciting moments
         ↓
Agent sends moment to backend API
         ↓
Moment appears in Producer view with "LIVE" badge
```

### Frame Processing

- **Frame Rate**: 1 FPS (one frame per second)
- **Resolution**: Captured at source resolution, sent to Gemini
- **Duration**: 30 seconds per session
- **Format**: JPEG compression for efficient transmission

### Gemini Prompt

The agent uses a specialized prompt that asks Gemini to:
1. Watch for exciting basketball moments
2. Rate excitement level (1-10)
3. Provide brief descriptions
4. Return structured JSON responses

Only moments with excitement level ≥7 are sent to the backend.

## Troubleshooting

### Agent won't start

**Error**: `GOOGLE_API_KEY not set`
- Make sure `.env` file exists in `backend/agent/`
- Verify `GOOGLE_API_KEY` is set

**Error**: `Cannot connect to LiveKit`
- Check if LiveKit server is running
- Verify `LIVEKIT_URL` is correct
- Try `ws://localhost:7880` for local dev server

### No moments detected

- Check if Gemini API key is valid
- Verify the video content is actually exciting (high-energy moments)
- Look at agent logs for frame processing status
- Check backend logs to see if moments are being created

### Screen share not working

- Browser must support `getDisplayMedia` (Chrome, Firefox, Edge)
- Check browser permissions for screen sharing
- Verify LiveKit token generation is working

### Agent crashes during frame processing

- May be a frame format issue
- Check logs for specific error messages
- Try adjusting frame rate or quality settings

## Development Tips

### Adjust Frame Rate

In `agent.py`, change:

```python
FRAME_RATE = 1  # Change to 2 for 2 FPS, etc.
```

### Modify Session Duration

```python
SESSION_DURATION = 30  # Change to desired seconds
```

### Test with Different Sports

Update the Gemini prompt in `analyze_frame_with_gemini()` to detect moments for different sports:

```python
prompt = f"""You are watching a live soccer match...
Analyze for: goals, near-misses, saves, celebrations...
```

### Debug Mode

Add more logging:

```python
print(f"Frame analysis result: {result}")
```

## API Reference

### Backend Endpoint

The agent calls this endpoint to create moments:

```
POST http://localhost:8002/api/moments/create_from_agent
```

**Request Body**:
```json
{
  "timestamp": 15.0,
  "description": "Dunk over defender",
  "excitement_level": 9,
  "source": "livekit_screenshare",
  "session_id": "screenshare_1234567890"
}
```

**Response**:
```json
{
  "success": true,
  "moment_id": "m_abc12345",
  "moment": { ... }
}
```

## Future Enhancements

- [ ] Support for longer sessions (session resumption)
- [ ] Voice command integration
- [ ] Multi-sport detection
- [ ] Real-time clip extraction from screen share
- [ ] Support for multiple concurrent screen shares
- [ ] Advanced prompt customization UI
- [ ] Webhook support for external integrations

## License

Part of the Vibe Check project.
