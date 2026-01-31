"""Video ingestion pipeline - processes MP4 files frame by frame."""

import cv2
import numpy as np
from pathlib import Path
import time
from typing import Iterator, Tuple, Optional
import logging
import ffmpeg
import subprocess

logger = logging.getLogger(__name__)


class VideoIngester:
    """
    Ingests video files (MP4) and yields frames with timestamps and audio samples.

    For the hackathon, we simulate "realtime" by playing back pre-recorded videos
    at their native frame rate.
    """

    def __init__(self, video_path: str, stream_id: str, realtime_mode: bool = True):
        """
        Initialize video ingester.

        Args:
            video_path: Path to MP4 file
            stream_id: Unique identifier for this video stream
            realtime_mode: If True, simulate realtime playback with delays
        """
        self.video_path = Path(video_path)
        self.stream_id = stream_id
        self.realtime_mode = realtime_mode

        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Open video capture
        self.cap = cv2.VideoCapture(str(self.video_path))
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")

        # Video properties
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration_seconds = self.total_frames / self.fps if self.fps > 0 else 0

        self.current_frame_idx = 0
        self.start_time = None

        # Audio extraction - extract once and cache
        self.audio_samples: Optional[np.ndarray] = None
        self.audio_sample_rate: Optional[int] = None
        self._extract_audio_stream()

        logger.info(
            f"📹 Opened video: {self.video_path.name} "
            f"({self.width}x{self.height}, {self.fps:.2f} fps, "
            f"{self.duration_seconds:.2f}s, {self.total_frames} frames)"
        )

    def ingest_frames(self) -> Iterator[Tuple[float, np.ndarray]]:
        """
        Yield frames from the video with timestamps.

        Yields:
            Tuple of (timestamp_seconds, frame_array)
        """
        self.start_time = time.time()
        frame_duration = 1.0 / self.fps if self.fps > 0 else 0.033  # fallback to ~30fps

        while True:
            ret, frame = self.cap.read()
            if not ret:
                logger.info(f"✅ Video ingestion complete: {self.stream_id}")
                break

            # Calculate timestamp from frame index
            timestamp = self.current_frame_idx / self.fps

            # Simulate realtime playback
            if self.realtime_mode:
                elapsed = time.time() - self.start_time
                target_time = timestamp
                if elapsed < target_time:
                    time.sleep(target_time - elapsed)

            yield timestamp, frame
            self.current_frame_idx += 1

    def _extract_audio_stream(self):
        """
        Extract full audio stream from video file using ffmpeg.
        Called once during initialization to cache audio data.
        """
        try:
            # Probe video to check if it has audio
            probe = ffmpeg.probe(str(self.video_path))
            audio_streams = [s for s in probe['streams'] if s['codec_type'] == 'audio']

            if not audio_streams:
                logger.warning(f"⚠️  No audio stream found in {self.video_path.name}")
                self.audio_samples = None
                self.audio_sample_rate = None
                return

            # Extract audio as raw PCM samples
            # Output: mono, 16-bit signed integers, 44100 Hz
            self.audio_sample_rate = 44100

            out, err = (
                ffmpeg
                .input(str(self.video_path))
                .audio
                .output('pipe:', format='s16le', acodec='pcm_s16le', ac=1, ar=self.audio_sample_rate)
                .run(capture_stdout=True, capture_stderr=True, quiet=True)
            )

            # Convert bytes to numpy array
            audio_data = np.frombuffer(out, np.int16)

            # Normalize to -1.0 to 1.0 range
            self.audio_samples = audio_data.astype(np.float32) / 32768.0

            logger.info(
                f"🔊 Extracted audio: {len(self.audio_samples)} samples "
                f"at {self.audio_sample_rate} Hz "
                f"({len(self.audio_samples) / self.audio_sample_rate:.2f}s)"
            )

        except ffmpeg.Error as e:
            logger.error(f"❌ Failed to extract audio: {e.stderr.decode() if e.stderr else str(e)}")
            self.audio_samples = None
            self.audio_sample_rate = None
        except Exception as e:
            logger.error(f"❌ Unexpected error extracting audio: {e}")
            self.audio_samples = None
            self.audio_sample_rate = None

    def extract_audio_rms(self, window_size: int = 1024) -> float:
        """
        Extract audio RMS for the current frame window.

        Args:
            window_size: Number of audio samples to compute RMS over

        Returns:
            RMS value normalized to 0-1 range (0 = silence, 1 = very loud)
        """
        if self.audio_samples is None or self.audio_sample_rate is None:
            # No audio available, return neutral value
            return 0.5

        # Calculate which audio samples correspond to current frame
        timestamp = self.current_frame_idx / self.fps

        # Center the window around the current timestamp
        center_sample = int(timestamp * self.audio_sample_rate)
        start_sample = max(0, center_sample - window_size // 2)
        end_sample = min(len(self.audio_samples), start_sample + window_size)

        # Extract window
        audio_window = self.audio_samples[start_sample:end_sample]

        if len(audio_window) == 0:
            return 0.0

        # Compute RMS (Root Mean Square)
        rms = np.sqrt(np.mean(audio_window ** 2))

        # Normalize: typical speech/music RMS is around 0.1-0.3
        # Loud moments (crowd roars, impacts) can go up to 0.5-0.8
        # Scale to 0-1 range with some headroom
        rms_normalized = min(rms * 3.0, 1.0)

        return float(rms_normalized)

    def get_info(self) -> dict:
        """Get video stream information."""
        return {
            "stream_id": self.stream_id,
            "video_path": str(self.video_path),
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "duration_seconds": self.duration_seconds,
            "total_frames": self.total_frames,
        }

    def seek(self, timestamp: float):
        """Seek to a specific timestamp in seconds."""
        frame_number = int(timestamp * self.fps)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        self.current_frame_idx = frame_number
        logger.debug(f"⏩ Seeked to {timestamp:.2f}s (frame {frame_number})")

    def close(self):
        """Release video capture resources."""
        if self.cap:
            self.cap.release()
            logger.info(f"🔒 Closed video ingester: {self.stream_id}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
