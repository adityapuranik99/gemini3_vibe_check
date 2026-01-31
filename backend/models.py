"""Pydantic models matching the data contracts from the spec."""

from pydantic import BaseModel, Field
from typing import Literal, List
from enum import Enum


class MomentType(str, Enum):
    GOAL = "goal"
    TOUCHDOWN = "touchdown"
    ACE = "ace"
    DUNK = "dunk"
    SAVE = "save"
    RALLY = "rally"
    WINNER = "winner"
    OTHER = "other"


class CandidateSignals(BaseModel):
    motion: float = Field(..., ge=0.0, le=1.0, description="Motion score 0-1")
    audio_rms: float = Field(..., ge=0.0, le=1.0, description="Audio RMS score 0-1")
    fan_buzz: float = Field(..., ge=0.0, le=1.0, description="Fan buzz score 0-1")


class CandidateEvent(BaseModel):
    type: Literal["candidate.created"] = "candidate.created"
    candidate_id: str
    t0: float = Field(..., description="Play moment time in seconds")
    signals: CandidateSignals


class ClipRecipe(BaseModel):
    label: Literal["reaction_lead", "play", "reaction_button"]
    start_s: float = Field(..., description="Start time in seconds")
    end_s: float = Field(..., description="End time in seconds")


class PostCopy(BaseModel):
    hype: str = Field(..., description="High-energy copy variant")
    neutral: str = Field(..., description="Neutral tone copy variant")
    brand_safe: str = Field(..., description="Brand-safe copy variant")


class MomentScores(BaseModel):
    hype: int = Field(..., ge=0, le=100, description="Hype score 0-100")
    risk: int = Field(..., ge=0, le=100, description="Risk score 0-100")


class MomentAnalysis(BaseModel):
    type: Literal["moment.ready"] = "moment.ready"
    moment_id: str
    t0: float = Field(..., description="Play moment time")
    tr: float = Field(..., description="Reaction peak time")
    moment_type: MomentType
    summary: str
    why_it_matters: List[str]
    scores: MomentScores
    risk_notes: List[str]
    clip_recipe: List[ClipRecipe]
    post_copy: PostCopy
    clip_url: str | None = None
    share_card_url: str | None = None
    approval_status: Literal["pending", "sent_to_exec", "approved", "held"] = "pending"
    source: Literal["upload", "livekit_screenshare"] = "upload"  # NEW: Source of the moment
    session_id: str | None = None  # NEW: LiveKit session ID if from screen share


class ApprovalEvent(BaseModel):
    type: Literal["moment.approved", "moment.held"]
    moment_id: str
    by: Literal["exec", "producer", "social"]
    at: float = Field(..., description="Timestamp of approval/hold")


class VideoIngestRequest(BaseModel):
    video_path: str = Field(..., description="Path to MP4 file to ingest")
    stream_id: str = Field(..., description="Unique identifier for this stream")
