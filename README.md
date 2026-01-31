# Vibe Check - Realtime Producer Copilot

AI-powered moment detection for live sports and entertainment, built for the Gemini 3 SuperHack.

## 🎯 What It Does

Vibe Check watches live streams and automatically:
1. Detects candidate moments (motion + audio)
2. Analyzes with Gemini 3 Flash (multimodal understanding)
3. Generates ready-to-post clips with reaction-first editing
4. Routes through Producer → Executive → Social approval workflow

## 🏗️ Architecture

- **Stage A**: Cheap detection (motion, audio RMS)
- **Stage B**: Gemini 3 analysis (structured JSON outputs)
- **Stage C**: Clip assembly with reaction-first stitching
- **War Room**: Three role-based views (Producer/Exec/Social)

## 🚀 Quick Start

### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0
```

### Frontend
```bash
cd frontend
bun install
bun run dev
```

Visit `http://localhost:3003` to upload a video and start detecting moments!

## 🎨 Features

- ✅ Two-stage detection (fast signals → Gemini analysis)
- ✅ Reaction-first clip assembly
- ✅ Three role-based views with SF 49ers tactical theme
- ✅ Producer: Filter, review, copy post variants
- ✅ Executive: One-at-a-time approval flow
- ✅ Social: Publish approved moments with toast notifications
- 🚧 LiveKit + Gemini Live voice agent (planned - see LIVEKIT_INTEGRATION_PLAN.md)
- 🚧 Fal.ai share card generation (planned - see FAL_INTEGRATION_PLAN.md)

## 📚 Tech Stack

**Backend**: Python, FastAPI, OpenCV, ffmpeg, Gemini 3 Flash
**Frontend**: Next.js 15, TypeScript, Tailwind CSS, Bun
**Sponsors**: Gemini 3, fal, LiveKit (integration planned)

## 📋 Hackathon Track

**Statement Three: The Crowd** - Creating systems for people engaging with the game through social media, dynamic media content, and clipping tools.

## 📖 Documentation

- **VIBE_CHECK_END_TO_END_KARPATHY.md** - Full technical specification
- **ref_docs/LIVEKIT_INTEGRATION_PLAN.md** - Voice agent integration strategy
- **ref_docs/FAL_INTEGRATION_PLAN.md** - Share card generation plan
- **ref_docs/IMPLEMENTATION_STATUS.md** - Current status and roadmap
- **ref_docs/REPO_RESET_GUIDE.md** - Timeline recreation guide

## 📄 License

MIT
