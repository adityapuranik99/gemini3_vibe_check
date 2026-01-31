"""
LiveKit Agent with Gemini Live API integration.
Monitors screen share and detects exciting moments in real-time.
Uses Gemini's Realtime model for continuous context across frames.

Key insight: Video input is passive - we need to periodically prompt
the model to analyze what it's seeing since there's no audio conversation.
"""

import asyncio
import os
import time
import logging
from typing import Optional
from dotenv import load_dotenv
import aiohttp

from livekit.agents import (
    JobContext, JobProcess, Agent, AgentSession, AgentServer,
    cli, room_io, function_tool, RunContext
)
from livekit.plugins import silero, google

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("vibe-check-agent")
logger.setLevel(logging.INFO)

# Configuration
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "devkey")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "secret")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
BACKEND_URL = os.getenv("VIBE_CHECK_BACKEND_URL", "http://localhost:8002")

# Analysis interval in seconds - how often to prompt the model to analyze
ANALYSIS_INTERVAL = 3.0

# Maximum session duration in seconds
MAX_SESSION_DURATION = 30.0

# Create the agent server
server = AgentServer()


class PlayState:
    """Tracks the current state of play detection."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.current_play_id: Optional[str] = None
        self.play_start_time: Optional[float] = None
        self.play_description: Optional[str] = None
        self.plays_detected: list = []
        self.start_time = time.time()
        self.is_watching = False

    def get_elapsed_time(self) -> float:
        """Get elapsed time since session start."""
        return time.time() - self.start_time

    def start_play(self, description: str) -> str:
        """Start tracking a new play."""
        self.current_play_id = f"play_{int(time.time() * 1000)}"
        self.play_start_time = self.get_elapsed_time()
        self.play_description = description
        logger.info(f"🎬 Play started: {description} at {self.play_start_time:.1f}s")
        return self.current_play_id

    def end_play(self, excitement_rating: int, final_description: str) -> dict:
        """End the current play and return the play data."""
        if not self.current_play_id:
            return {"error": "No active play"}

        end_time = self.get_elapsed_time()
        play_data = {
            "play_id": self.current_play_id,
            "start_time": self.play_start_time,
            "end_time": end_time,
            "duration": end_time - self.play_start_time,
            "description": final_description or self.play_description,
            "excitement_rating": excitement_rating,
            "session_id": self.session_id
        }

        self.plays_detected.append(play_data)
        logger.info(f"🏁 Play ended: {final_description} | Rating: {excitement_rating}/10 | Duration: {play_data['duration']:.1f}s")

        # Reset state
        self.current_play_id = None
        self.play_start_time = None
        self.play_description = None

        return play_data


async def send_play_to_backend(play_data: dict):
    """Send detected play to Vibe Check backend."""
    try:
        async with aiohttp.ClientSession() as http_session:
            moment_data = {
                "timestamp": play_data["start_time"],
                "end_timestamp": play_data["end_time"],
                "description": play_data["description"],
                "excitement_level": play_data["excitement_rating"],
                "source": "livekit_screenshare",
                "session_id": play_data["session_id"],
                "play_id": play_data["play_id"]
            }

            async with http_session.post(
                f"{BACKEND_URL}/api/moments/create_from_agent",
                json=moment_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"✅ Play sent to backend: {result.get('moment_id')}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to send play: {response.status} - {error_text}")
    except Exception as e:
        logger.error(f"❌ Error sending play to backend: {e}")


class VibeCheckAssistant(Agent):
    """
    Sports commentator agent that watches screen share and detects exciting plays.
    Uses Gemini Live for continuous context across video frames.
    """

    def __init__(self, play_state: PlayState) -> None:
        super().__init__(
            instructions="""You are an expert sports analyst watching a live sports broadcast via screen share.

YOUR MISSION: Detect and rate exciting plays as they happen by watching the video.

## WHAT MAKES A PLAY EXCITING:
1. **Visual action**: Goals, dunks, touchdowns, big hits, amazing catches, saves
2. **Body language**: Player celebrations, coach reactions, team huddles after big plays
3. **Game context**: Close games, clutch moments, comebacks, upsets
4. **Replay indicators**: Slow-motion replays often indicate something exciting just happened

## YOUR WORKFLOW:
When I ask you to analyze, look at what's happening on screen and:
1. If you see exciting action STARTING, call `start_play` with a brief description
2. If the play you started is ENDING/CONCLUDED, call `end_play` with rating and description
3. If nothing exciting, just briefly say what you see (no tool call needed)

## EXCITEMENT RATING SCALE (1-10):
- 1-2: Routine play, nothing special
- 3-4: Minor moment of interest
- 5-6: Good play, noticeable action
- 7-8: Exciting play, highlight worthy
- 9-10: INCREDIBLE moment, game-changing

## IMPORTANT:
- Use tools to report plays - start_play when action begins, end_play when it concludes
- Be generous - if there's any doubt, lean toward detecting the play
- Keep verbal responses SHORT (under 10 words) so we can keep analyzing quickly
- If you see a replay, that often means something exciting just happened"""
        )
        self.play_state = play_state
        self._analysis_task: Optional[asyncio.Task] = None

    async def on_enter(self) -> None:
        """Called when the agent session is ready."""
        logger.info("🎬 Agent entered, starting analysis loop...")
        # Start the periodic analysis loop
        self._analysis_task = asyncio.create_task(self._analysis_loop())

    async def on_exit(self) -> None:
        """Called when the agent is exiting."""
        logger.info("👋 Agent exiting, stopping analysis loop...")
        self.play_state.is_watching = False
        if self._analysis_task:
            self._analysis_task.cancel()
            try:
                await self._analysis_task
            except asyncio.CancelledError:
                pass

    async def _analysis_loop(self):
        """Periodically prompt the model to analyze what it's seeing."""
        # Wait a bit for the session to stabilize
        await asyncio.sleep(2.0)

        # Initial greeting - await the speech handle
        try:
            speech_handle = self.session.generate_reply(
                instructions="Briefly greet the user (under 10 words) and say you're ready to watch their sports broadcast."
            )
            await speech_handle
        except Exception as e:
            logger.warning(f"Initial greeting failed: {e}")

        # Wait for screen share to potentially start
        await asyncio.sleep(3.0)

        self.play_state.is_watching = True
        logger.info("👁️ Starting continuous video analysis...")

        analysis_count = 0
        while self.play_state.is_watching:
            try:
                analysis_count += 1
                elapsed = self.play_state.get_elapsed_time()

                # Check if we've exceeded max session duration
                if elapsed >= MAX_SESSION_DURATION:
                    logger.info(f"⏱️ Max session duration ({MAX_SESSION_DURATION}s) reached, stopping analysis")
                    self.play_state.is_watching = False
                    break

                # Craft the analysis prompt based on current state
                if self.play_state.current_play_id:
                    # We're tracking a play - check if it's done
                    prompt = (
                        f"[{elapsed:.0f}s] You started tracking a play. "
                        f"Look at the screen - is the play still happening or has it concluded? "
                        f"If concluded, call end_play with your excitement rating. "
                        f"If still going, just say 'still watching' (very brief)."
                    )
                else:
                    # Not tracking a play - look for new action
                    prompt = (
                        f"[{elapsed:.0f}s] Quick scan - what's happening on screen? "
                        f"If you see exciting sports action starting, call start_play. "
                        f"Keep response under 10 words."
                    )

                logger.debug(f"📊 Analysis #{analysis_count} at {elapsed:.1f}s")

                # Trigger the model to analyze and potentially call tools
                # Await the speech handle to ensure we don't overlap requests
                speech_handle = self.session.generate_reply(instructions=prompt)
                await speech_handle

                # Wait before next analysis
                await asyncio.sleep(ANALYSIS_INTERVAL)

            except asyncio.CancelledError:
                logger.info("Analysis loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}")
                await asyncio.sleep(1.0)

    @function_tool()
    async def start_play(self, ctx: RunContext, description: str) -> str:
        """
        Call this when you detect the START of an exciting play or moment.

        Args:
            description: Brief description of what's starting (e.g., "fast break", "shot attempt", "big hit")

        Returns:
            Confirmation that play tracking started
        """
        play_id = self.play_state.start_play(description)
        return f"Tracking play: {description}. Call end_play when it concludes."

    @function_tool()
    async def end_play(
        self,
        ctx: RunContext,
        excitement_rating: int,
        final_description: str
    ) -> str:
        """
        Call this when the current play ENDS. Rate the excitement and describe what happened.

        Args:
            excitement_rating: 1-10 rating of how exciting the play was
            final_description: What happened (e.g., "player scored with a dunk")

        Returns:
            Confirmation of the recorded play
        """
        play_data = self.play_state.end_play(excitement_rating, final_description)

        if "error" in play_data:
            return f"Error: {play_data['error']}. Call start_play first."

        # Send to backend asynchronously
        asyncio.create_task(send_play_to_backend(play_data))

        return f"Play recorded! Rating: {excitement_rating}/10. Keep watching!"


def prewarm(proc: JobProcess):
    """Preload VAD model for faster connections."""
    proc.userdata["vad"] = silero.VAD.load()
    logger.info("✅ VAD model preloaded")


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    """Main entry point for the LiveKit agent."""
    logger.info(f"🚀 Agent started for room: {ctx.room.name}")

    session_id = ctx.room.name or f"session_{int(time.time())}"
    play_state = PlayState(session_id)

    # Create the agent session with Gemini Realtime
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.5-flash-native-audio-preview-12-2025",
            # Proactivity lets the model speak up when it wants to
            proactivity=True,
            # Affective dialog for more natural responses
            enable_affective_dialog=True,
            api_key=GOOGLE_API_KEY,
        ),
        vad=ctx.proc.userdata["vad"],
    )

    # Start the session with video input enabled
    await session.start(
        room=ctx.room,
        agent=VibeCheckAssistant(play_state),
        room_options=room_io.RoomOptions(
            # Enable video input to receive screen share frames
            video_input=True,
            # Disable audio input since we're focusing on video only
            audio_input=False,
            # Keep the agent running even if the participant disconnects
            close_on_disconnect=False,
        )
    )

    # Connect to the room
    await ctx.connect()
    logger.info(f"✅ Connected to room: {ctx.room.name}")
    logger.info("🎬 Agent ready and watching for plays!")


def main():
    """Run the agent."""
    if not GOOGLE_API_KEY:
        logger.error("❌ Error: GOOGLE_API_KEY not set in environment")
        return

    logger.info(f"🔧 LiveKit URL: {LIVEKIT_URL}")
    logger.info(f"🔧 Backend URL: {BACKEND_URL}")

    cli.run_app(server)


if __name__ == "__main__":
    main()
