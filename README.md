# Vibe Check - Realtime Producer Copilot

AI-powered moment detection for live sports and entertainment, built for the Gemini 3 SuperHack.

## 🎯 What It Does

Vibe Check is an AI copilot that helps content producers create viral sports highlights in real-time. It watches live streams and automatically:

1. **Detects Candidate Moments** - Motion + audio analysis identifies exciting plays
2. **Analyzes with Gemini 3 Flash** - Multimodal AI understands context, players, and game dynamics
3. **Identifies Players & Stats** - Search grounding extracts player names, teams, and match statistics
4. **Generates Post Copy** - Three variants (hype, neutral, brand-safe) for different audiences
5. **Creates Share Cards** - AI-generated social media graphics with player images (via fal.ai)
6. **Routes Through Workflow** - Producer → Executive → Social approval system
7. **Supports Live Screenshare** - Real-time moment detection from broadcast feeds

## 🏗️ Architecture

### Three-Stage Pipeline

- **Stage A: Fast Detection** - Motion tracking + audio RMS analysis (cheap, real-time)
- **Stage B: Gemini Analysis** - Multimodal understanding with search grounding for player/match identification
- **Stage C: Asset Generation** - Reaction-first clip assembly + AI share cards with player images

### War Room Interface

- **Producer View**: Filter, review, and select moments with post copy variants
- **Executive View**: One-at-a-time approval flow for quality control
- **Social View**: Publish approved moments to social platforms

### Live Capabilities

- **LiveKit Screen Share**: Share broadcast window for real-time AI analysis (30s demo mode)
- **Gemini Live Agent**: Python agent analyzes frames at 1 FPS and auto-detects moments
- **LIVE Badge**: Screen share moments marked with distinctive red badge

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (or Bun)
- ffmpeg
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))
- fal.ai API key ([Sign up here](https://fal.ai))
- LiveKit (optional, for screen share) - [Local dev setup](https://docs.livekit.io/)

### Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys:
# - GOOGLE_API_KEY (required)
# - FAL_KEY (required for share cards)

# Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

### Frontend Setup

```bash
cd frontend
bun install  # or npm install

# Start development server
bun run dev  # or npm run dev
```

### LiveKit Agent Setup (Optional)

For real-time screen share detection:

```bash
cd backend/agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure LiveKit
cp .env.example .env
# Edit .env with LiveKit credentials

# Start agent
python agent.py
```

See [LIVEKIT_SETUP.md](LIVEKIT_SETUP.md) for detailed LiveKit configuration.

### Access the App

Visit `http://localhost:3000` and:
- Upload a video to detect moments, or
- Click "Share Screen (30s Demo)" to analyze live broadcast feeds

## 🎨 Features

### Core Detection & Analysis
- ✅ **Two-Stage Pipeline** - Fast motion/audio detection → Gemini multimodal analysis
- ✅ **Gemini 3 Flash** - Latest multimodal model with structured JSON output
- ✅ **Search Grounding** - Automatic player identification and match statistics extraction
- ✅ **Moment Classification** - Detects dunks, three-pointers, blocks, assists, clutch plays, and more
- ✅ **Hype & Risk Scoring** - AI-powered content safety and virality predictions
- ✅ **Reaction-First Editing** - Clips preserve crowd/commentator reactions after the play

### Content Creation
- ✅ **Post Copy Generation** - Three variants (hype, neutral, brand-safe) for each moment
- ✅ **AI Share Cards** - Automatic generation via fal.ai with player images
- ✅ **Player Image Service** - Smart fallback system (Wikipedia → Google Images → placeholder)
- ✅ **Clip Assembly** - Automatic video editing with configurable recipe segments
- ✅ **Multiple Export Formats** - Optimized for different social platforms

### Workflow & UI
- ✅ **Producer Dashboard** - Filter, sort, and review detected moments
- ✅ **Executive Approval** - One-at-a-time review flow with approve/reject
- ✅ **Social Publisher** - Queue management with publish/unpublish controls
- ✅ **SF 49ers Theme** - Tactical war room aesthetic with role-based views
- ✅ **Toast Notifications** - Real-time feedback for all actions
- ✅ **Responsive Design** - Works on desktop and tablet devices

### Live Capabilities
- ✅ **LiveKit Screen Share** - Share broadcast window for real-time analysis
- ✅ **Python AI Agent** - Monitors screen share at 1 FPS with Gemini
- ✅ **30-Second Demo Mode** - Quick proof-of-concept for live detection
- ✅ **LIVE Badge** - Distinctive marker for screen share moments
- ✅ **Auto-Polling** - Frontend automatically discovers new live moments

### Developer Experience
- ✅ **Type-Safe Models** - Pydantic backend + TypeScript frontend
- ✅ **Structured Logging** - Comprehensive debug output
- ✅ **Error Handling** - Graceful fallbacks for API failures
- ✅ **Modular Architecture** - Clean separation of concerns
- ✅ **Environment Config** - Easy setup with .env files

## 📚 Tech Stack

### Backend
- **Python 3.10+** - Core runtime
- **FastAPI** - REST API framework
- **OpenCV** - Video processing and frame extraction
- **ffmpeg** - Video encoding and clip assembly
- **NumPy/SciPy** - Motion detection and signal processing
- **Pydantic** - Type-safe data models

### AI & ML
- **Gemini 3 Flash Preview** - Multimodal moment analysis with structured JSON output
- **Google Search Grounding** - Player and match statistics extraction
- **google-generativeai** - Primary SDK for Gemini API
- **google-genai** - New SDK for search grounding features
- **fal.ai** - AI-generated share cards with player images

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Bun** - Fast package manager and runtime
- **React** - UI component library

### Real-Time Features
- **LiveKit** - WebRTC infrastructure for screen sharing
- **livekit-agents** - Python SDK for AI agent development
- **livekit-client** - Browser SDK for WebRTC
- **livekit-server-sdk** - Server-side LiveKit integration

### Infrastructure
- **Docker** - Containerization (optional)
- **Git** - Version control

## 📋 Hackathon Track

**Statement Three: The Crowd** - Creating systems for people engaging with the game through social media, dynamic media content, and clipping tools.

## 🔑 API Keys Required

1. **Google Gemini API** (Required)
   - Get it: https://aistudio.google.com/app/apikey
   - Used for: Moment analysis, player identification, search grounding
   - Free tier: Generous quota for development

2. **fal.ai API** (Required for share cards)
   - Get it: https://fal.ai
   - Used for: AI-generated social media graphics
   - Free tier: 100 requests/month

3. **LiveKit** (Optional, for screen share)
   - Local dev: `livekit-server --dev` (no key needed)
   - Cloud: https://livekit.io (free tier available)
   - Used for: Real-time screen sharing and live analysis

## 📖 Documentation

- [VIBE_CHECK_END_TO_END_KARPATHY.md](VIBE_CHECK_END_TO_END_KARPATHY.md) - Full technical specification
- [LIVEKIT_SETUP.md](LIVEKIT_SETUP.md) - LiveKit screen share setup guide
- [ref_docs/LIVEKIT_IMPLEMENTATION.md](ref_docs/LIVEKIT_IMPLEMENTATION.md) - LiveKit implementation details
- [ref_docs/FAL_INTEGRATION_PLAN.md](ref_docs/FAL_INTEGRATION_PLAN.md) - Share card generation architecture
- [ref_docs/IMPLEMENTATION_STATUS.md](ref_docs/IMPLEMENTATION_STATUS.md) - Current status and roadmap
- [ref_docs/PLAN_match_stats_player_images.md](ref_docs/PLAN_match_stats_player_images.md) - Player/match extraction plan
- [backend/agent/README.md](backend/agent/README.md) - LiveKit agent documentation

## 🎮 Usage Guide

### Upload Mode

1. Navigate to home page (`http://localhost:3000`)
2. Click "Upload Video" or drag & drop a game video
3. Wait for processing (motion detection → Gemini analysis)
4. Review detected moments in the Producer view
5. Approve through Executive view
6. Publish from Social view

### Screen Share Mode (Live)

1. Start LiveKit server and agent (see [LIVEKIT_SETUP.md](LIVEKIT_SETUP.md))
2. Click "Share Screen (30s Demo)" on home page
3. Select your broadcast window (e.g., YouTube highlight video)
4. Agent analyzes frames in real-time for 30 seconds
5. Moments appear automatically in Producer view with 🔴 LIVE badge

### Producer Workflow

- **Filter by type**: Dunk, 3PT, block, assist, etc.
- **Sort options**: Hype score, risk score, time detected
- **Review details**: Watch clips, read AI analysis, check player info
- **Choose copy variant**: Hype, neutral, or brand-safe text
- **Generate share card**: AI-generated graphics with player images
- **Submit for approval**: Send to Executive queue

### Executive Workflow

- **One-at-a-time review**: Focused approval flow
- **Approve**: Move to Social queue
- **Reject**: Remove from workflow with feedback

### Social Workflow

- **Publish**: Mark as ready for distribution
- **Queue management**: Track published vs. pending moments
- **Unpublish**: Remove from live rotation if needed

## 🏗️ Project Structure

```
vibe_check/
├── backend/
│   ├── agent/              # LiveKit AI agent
│   │   ├── agent.py        # Main agent logic
│   │   └── requirements.txt
│   ├── detection/          # Stage A: Motion/audio detection
│   ├── gemini_analyzer/    # Stage B: Gemini analysis
│   │   ├── analyzer.py     # Main analyzer with search grounding
│   │   └── prompts.py      # Prompt templates
│   ├── ingest/             # Video ingestion and frame extraction
│   ├── storage/            # Video storage and cache
│   ├── main.py             # FastAPI application
│   ├── models.py           # Pydantic data models
│   ├── pipeline.py         # End-to-end processing pipeline
│   ├── share_card_generator.py  # fal.ai integration
│   └── player_image_service.py  # Player image fetching
├── frontend/
│   ├── app/
│   │   ├── page.tsx        # Home page with upload/screenshare
│   │   ├── producer/       # Producer dashboard
│   │   ├── executive/      # Executive approval view
│   │   ├── social/         # Social publisher view
│   │   └── api/            # API routes (LiveKit token)
│   ├── components/         # React components
│   │   └── ScreenShare.tsx # Screen share UI
│   └── types/              # TypeScript type definitions
├── ref_docs/               # Documentation
├── LIVEKIT_SETUP.md        # LiveKit setup guide
└── README.md               # This file
```

## 🐛 Troubleshooting

### Backend Issues

**"GOOGLE_API_KEY not found"**
- Add your API key to `backend/.env`
- Get one from https://aistudio.google.com/app/apikey

**"Module not found" errors**
- Activate virtual environment: `source .venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

**Video processing fails**
- Install ffmpeg: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux)
- Check video format compatibility (MP4, MOV supported)

### Frontend Issues

**"Failed to fetch moments"**
- Ensure backend is running on port 8002
- Check `NEXT_PUBLIC_API_URL` in `.env.local`

**Screen share not working**
- LiveKit server must be running
- Check LiveKit credentials in `.env.local`
- Try using `ws://localhost:7880` for local dev

### LiveKit Agent Issues

**"No frames received"**
- Verify screen share is active in browser
- Check agent logs for connection status
- Ensure LiveKit URL/credentials match across all configs

**"No moments detected"**
- Content may not be exciting enough (try highlight reels)
- Check Gemini API key is valid
- Lower excitement threshold in `agent.py`

## 🚀 Future Enhancements

- [ ] Voice commands for hands-free operation
- [ ] Extended live sessions (beyond 30s demo)
- [ ] Clip extraction from screen share (not just upload)
- [ ] Multi-sport support (football, soccer, hockey)
- [ ] Real social media publishing (Twitter/X, Instagram)
- [ ] Analytics dashboard for engagement metrics
- [ ] Collaborative review features (comments, annotations)
- [ ] Mobile app for on-the-go monitoring

## 📄 License

MIT
