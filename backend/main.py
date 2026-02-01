"""FastAPI main application - Vibe Check backend."""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
import os
import shutil
from dotenv import load_dotenv

from models import (
    MomentAnalysis,
    CandidateEvent,
    ApprovalEvent,
    VideoIngestRequest,
)
from pipeline import VideoPipeline
from typing import Optional

# Load environment variables
load_dotenv()

# Storage paths
STORAGE_PATHS = {
    "videos": os.getenv("VIDEO_STORAGE_PATH", "./storage/videos"),
    "clips": os.getenv("CLIPS_OUTPUT_PATH", "./storage/clips"),
    "segments": os.getenv("SEGMENTS_PATH", "./storage/segments"),
    "share_cards": "./storage/share_cards",
}

# Create storage directories
for path in STORAGE_PATHS.values():
    os.makedirs(path, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global pipeline
    print("🚀 Vibe Check backend starting up...")
    print(f"📁 Storage paths: {STORAGE_PATHS}")

    # Initialize pipeline with audio-optimized thresholds
    try:
        pipeline = VideoPipeline(
            motion_threshold=0.7,   # Catch high-motion action
            audio_threshold=0.22,   # Balanced for significant crowd reactions (peaks at 0.25-0.3)
        )
        print("✅ Video pipeline initialized with audio processing enabled")
    except Exception as e:
        print(f"⚠️  Pipeline initialization failed: {e}")
        print("   (Gemini API key might be missing)")

    yield
    print("👋 Vibe Check backend shutting down...")


app = FastAPI(
    title="Vibe Check API",
    description="Realtime producer copilot for sports and live entertainment",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for network access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-memory storage (replace with database later)
moments_store: dict[str, MomentAnalysis] = {}
candidates_store: dict[str, CandidateEvent] = {}

# Pipeline instance
pipeline: Optional[VideoPipeline] = None


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Vibe Check API",
        "version": "0.1.0",
    }


@app.get("/api/moments")
async def get_moments(status: Optional[str] = None):
    """
    Get all detected moments.

    Args:
        status: Optional filter by approval status (pending/approved/held)
    """
    moments = list(moments_store.values())

    # Filter by status if provided
    if status:
        moments = [m for m in moments if m.approval_status == status]

    return {
        "moments": moments,
        "count": len(moments),
    }


@app.get("/api/moments/{moment_id}")
async def get_moment(moment_id: str):
    """Get a specific moment by ID."""
    if moment_id not in moments_store:
        raise HTTPException(status_code=404, detail="Moment not found")
    return moments_store[moment_id]


@app.post("/api/moments/approve")
async def approve_moment(approval: ApprovalEvent):
    """Approve or hold a moment."""
    if approval.moment_id not in moments_store:
        raise HTTPException(status_code=404, detail="Moment not found")

    # Update moment status
    moment = moments_store[approval.moment_id]
    if approval.type == "moment.approved":
        moment.approval_status = "approved"
        print(f"✅ Moment approved: {approval.moment_id} by {approval.by}")
    else:
        moment.approval_status = "held"
        print(f"⏸️  Moment held: {approval.moment_id} by {approval.by}")

    # TODO: Send approval event via LiveKit data channel

    return {"status": "ok", "approval": approval, "moment": moment}


@app.post("/api/moments/{moment_id}/send_to_exec")
async def send_to_exec(moment_id: str):
    """Producer sends a moment to exec for approval."""
    if moment_id not in moments_store:
        raise HTTPException(status_code=404, detail="Moment not found")

    moment = moments_store[moment_id]
    moment.approval_status = "sent_to_exec"
    print(f"📤 Moment sent to exec: {moment_id}")

    return {"status": "ok", "moment": moment}


@app.post("/api/moments/{moment_id}/regenerate_share_card")
async def regenerate_share_card(moment_id: str, theme_name: str = "stadium"):
    """Regenerate a share card for a moment with a specific theme."""
    if moment_id not in moments_store:
        raise HTTPException(status_code=404, detail="Moment not found")
    
    moment = moments_store[moment_id]
    
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        # Re-save keyframe if needed
        keyframe_path = await pipeline._save_keyframe(moment)
        
        # Generate new static card
        card_path = await pipeline.share_card_generator.generate_static_card(
            moment, 
            theme_name=theme_name,
            keyframe_path=keyframe_path
        )
        
        if card_path:
            moment.share_card_url = f"/api/share_cards/images/{os.path.basename(card_path)}"
            
            # Re-start animation
            import asyncio
            asyncio.create_task(
                pipeline.share_card_generator.generate_animated_loop(
                    moment, 
                    card_path,
                    theme_name=theme_name
                )
            )
        
        return {"status": "ok", "moment": moment}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")


@app.post("/api/upload")
async def upload_video(video: UploadFile = File(...)):
    """
    Upload a video file to the server.

    Returns:
        - video_path: Server path to the uploaded video
        - filename: Original filename
        - size: File size in bytes
    """
    try:
        # Generate unique filename to avoid conflicts
        import time
        timestamp = int(time.time())
        original_filename = video.filename or "video.mp4"
        # Sanitize filename
        safe_filename = "".join(c for c in original_filename if c.isalnum() or c in "._- ")
        unique_filename = f"{timestamp}_{safe_filename}"

        # Save to storage path
        video_path = os.path.join(STORAGE_PATHS["videos"], unique_filename)

        # Write uploaded file to disk
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        file_size = os.path.getsize(video_path)

        print(f"📤 Video uploaded: {unique_filename} ({file_size / 1024 / 1024:.1f}MB)")

        return {
            "status": "ok",
            "video_path": video_path,
            "filename": unique_filename,
            "size": file_size,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/ingest/start")
async def start_ingestion(request: VideoIngestRequest):
    """Start ingesting and processing a video file."""
    if not os.path.exists(request.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    if pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="Pipeline not initialized (check Gemini API key)"
        )

    print(f"🎥 Starting pipeline: {request.stream_id} from {request.video_path}")

    # Callbacks to store detected moments
    async def on_candidate(candidate: CandidateEvent):
        candidates_store[candidate.candidate_id] = candidate

    async def on_moment(moment: MomentAnalysis):
        moments_store[moment.moment_id] = moment
        print(f"✅ Moment ready: {moment.moment_id}")

    # Process video (runs in background)
    import asyncio
    asyncio.create_task(
        pipeline.process_video(
            request.video_path,
            request.stream_id,
            on_candidate=on_candidate,
            on_moment=on_moment,
        )
    )

    return {
        "status": "processing",
        "stream_id": request.stream_id,
        "video_path": request.video_path,
        "message": "Processing started. Check /api/moments for results.",
    }


@app.get("/api/candidates")
async def get_candidates():
    """Get all candidate events."""
    return {
        "candidates": list(candidates_store.values()),
        "count": len(candidates_store),
    }


@app.get("/api/clips/{filename}")
async def get_clip(filename: str):
    """Serve a generated clip file."""
    clip_path = os.path.join(STORAGE_PATHS["clips"], filename)

    if not os.path.exists(clip_path):
        raise HTTPException(status_code=404, detail="Clip not found")

    return FileResponse(
        clip_path,
        media_type="video/mp4",
        filename=filename,
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            "Accept-Ranges": "bytes",  # Enable partial content/seeking
        },
    )


@app.get("/api/share_cards/{subfolder}/{filename}")
async def get_share_card(subfolder: str, filename: str):
    """Serve a generated share card file (image or video)."""
    # subfolder should be 'images' or 'videos'
    if subfolder not in ["images", "videos", "keyframes"]:
        raise HTTPException(status_code=400, detail="Invalid subfolder")

    card_path = os.path.join(STORAGE_PATHS["share_cards"], subfolder, filename)

    if not os.path.exists(card_path):
        raise HTTPException(status_code=404, detail="Share card file not found")

    media_type = "image/png" if subfolder in ["images", "keyframes"] else "video/mp4"
    return FileResponse(
        card_path,
        media_type=media_type,
        filename=filename,
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            "Accept-Ranges": "bytes",
        },
    )


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
    import uuid
    from models import MomentType, MomentScores, PostCopy, ClipRecipe

    try:
        # Create moment without clip (just metadata for now)
        moment = MomentAnalysis(
            moment_id=f"m_{uuid.uuid4().hex[:8]}",
            source="livekit_screenshare",
            session_id=moment_data.get("session_id", "unknown"),
            t0=moment_data.get("timestamp", 0.0),
            tr=moment_data.get("timestamp", 0.0),  # Same as t0 for live moments
            moment_type=MomentType.OTHER,  # Default to OTHER for now
            summary=moment_data.get("description", "Exciting moment detected"),
            why_it_matters=["Detected live by Gemini"],
            scores=MomentScores(
                hype=moment_data.get("excitement_level", 8) * 10,
                risk=0
            ),
            risk_notes=[],
            clip_recipe=[],  # No clips for live moments yet
            post_copy=PostCopy(
                hype=moment_data.get("description", "Exciting moment!"),
                neutral=moment_data.get("description", "Exciting moment."),
                brand_safe=moment_data.get("description", "Exciting moment.")
            ),
            clip_url=None,
            share_card_url=None,
            approval_status="pending"
        )

        moments_store[moment.moment_id] = moment
        print(f"✨ Live moment created: {moment.moment_id} - {moment.summary}")

        return {"success": True, "moment_id": moment.moment_id, "moment": moment}
    except Exception as e:
        print(f"❌ Error creating moment from agent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create moment: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
    )
