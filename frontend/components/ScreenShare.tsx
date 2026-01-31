"use client";

import { useState, useCallback } from "react";
import { Room, RoomEvent, Track } from "livekit-client";

type ScreenShareState = "idle" | "connecting" | "monitoring" | "complete" | "error";

interface ScreenShareProps {
  onComplete?: () => void;
}

export default function ScreenShare({ onComplete }: ScreenShareProps) {
  const [shareState, setShareState] = useState<ScreenShareState>("idle");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [countdown, setCountdown] = useState<number>(30);
  const [sessionId, setSessionId] = useState<string>("");
  const [showComingSoonModal, setShowComingSoonModal] = useState<boolean>(false);

  const startScreenShare = useCallback(async () => {
    try {
      setShareState("connecting");
      setErrorMessage("");

      // Generate session ID
      const newSessionId = `screenshare_${Date.now()}`;
      setSessionId(newSessionId);

      // Get screen share track
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: {
          width: { ideal: 1920 },
          height: { ideal: 1080 },
          frameRate: { ideal: 30 }
        },
        audio: false
      });

      const videoTrack = stream.getVideoTracks()[0];

      // Connect to LiveKit
      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
      });

      // Handle track stopped (user cancelled screen share)
      videoTrack.addEventListener("ended", () => {
        console.log("Screen share stopped by user");
        room.disconnect();
        if (shareState === "monitoring") {
          setShareState("complete");
          onComplete?.();
        }
      });

      // Connect to LiveKit room
      // TODO: Get token from backend endpoint
      const wsUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL || "ws://localhost:7880";
      const token = await getToken(newSessionId);

      await room.connect(wsUrl, token);
      console.log("Connected to LiveKit room:", newSessionId);

      // Publish screen share track
      await room.localParticipant.publishTrack(videoTrack, {
        name: "screenshare",
        source: Track.Source.ScreenShare,
      });

      console.log("Screen share track published");
      setShareState("monitoring");

      // Start countdown
      let timeLeft = 30;
      setCountdown(timeLeft);

      const countdownInterval = setInterval(() => {
        timeLeft--;
        setCountdown(timeLeft);

        if (timeLeft <= 0) {
          clearInterval(countdownInterval);
          // Stop screen share
          videoTrack.stop();
          room.disconnect();
          setShareState("complete");
          onComplete?.();
        }
      }, 1000);

    } catch (error) {
      console.error("Screen share failed:", error);
      if (error instanceof Error) {
        if (error.name === "NotAllowedError") {
          setErrorMessage("Screen share permission denied");
        } else {
          setErrorMessage(error.message);
        }
      } else {
        setErrorMessage("Failed to start screen share");
      }
      setShareState("error");
    }
  }, [shareState, onComplete]);

  const reset = () => {
    setShareState("idle");
    setErrorMessage("");
    setCountdown(30);
    setSessionId("");
  };

  return (
    <div className="w-full">
      {shareState === "idle" || shareState === "error" ? (
        <div className="text-center">
          {shareState === "error" && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
              <p className="text-red-400 text-sm font-bold">⚠️ {errorMessage}</p>
            </div>
          )}

          <button
            onClick={() => setShowComingSoonModal(true)}
            className="w-full px-8 py-6 bg-gradient-to-r from-primary to-accent-gold text-white text-lg font-black tracking-widest rounded-xl hover:scale-105 transition-all shadow-xl hover:shadow-2xl hover:shadow-primary/50 uppercase"
          >
            <div className="flex items-center justify-center gap-3">
              <span className="text-2xl">🖥️</span>
              <span>Share Screen (30s Demo)</span>
            </div>
          </button>

          <p className="text-text-muted text-xs mt-4 uppercase tracking-wider">
            Share your broadcast window for live moment detection
          </p>

          {/* Coming Soon Modal */}
          {showComingSoonModal && (
            <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
              <div className="bg-panel-dark border border-border-subtle rounded-2xl max-w-md w-full p-8 relative">
                <button
                  onClick={() => setShowComingSoonModal(false)}
                  className="absolute top-4 right-4 text-text-muted hover:text-white transition-colors"
                >
                  ✕
                </button>

                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-accent-gold/20 border-2 border-accent-gold mb-6">
                    <span className="text-3xl">🚧</span>
                  </div>

                  <h3 className="text-white text-2xl font-black tracking-tighter uppercase mb-4">
                    Coming Soon
                  </h3>

                  <p className="text-text-muted mb-4">
                    Live screen share analysis works with the <span className="text-accent-gold font-bold">Gemini Realtime API</span>, but is currently constrained by API limitations.
                  </p>

                  <div className="bg-primary/10 border border-primary/30 rounded-lg p-4 mb-6">
                    <p className="text-sm text-text-muted">
                      <span className="text-primary font-bold">Technical limitation:</span> The Realtime API requires audio input for proper video context. Without voice activity, the model cannot reliably process video frames.
                    </p>
                  </div>

                  <p className="text-accent-gold text-sm font-bold uppercase tracking-wider">
                    Stay tuned for updates!
                  </p>
                </div>

                <div className="flex gap-3 mt-6">
                  <button
                    onClick={() => setShowComingSoonModal(false)}
                    className="flex-1 px-6 py-3 bg-border-subtle text-text-muted text-sm font-black tracking-widest rounded-lg hover:bg-border-subtle/80 transition-all uppercase"
                  >
                    Close
                  </button>
                  <button
                    onClick={() => {
                      setShowComingSoonModal(false);
                      startScreenShare();
                    }}
                    className="flex-1 px-6 py-3 bg-primary text-white text-sm font-black tracking-widest rounded-lg hover:bg-primary/80 transition-all uppercase"
                  >
                    Try Anyway
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : shareState === "connecting" ? (
        <div className="text-center p-8 bg-panel-dark rounded-xl border border-border-subtle">
          <div className="animate-spin w-12 h-12 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
          <h3 className="text-white text-xl font-bold mb-2">CONNECTING...</h3>
          <p className="text-text-muted text-sm">Setting up screen share session</p>
        </div>
      ) : shareState === "monitoring" ? (
        <div className="text-center p-8 bg-gradient-to-br from-primary/20 to-accent-gold/20 rounded-xl border-2 border-primary">
          <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-red-600/30 border-4 border-red-500 mb-6 animate-pulse">
            <span className="text-4xl">🔴</span>
          </div>
          <h3 className="text-white text-3xl font-black tracking-tighter uppercase italic mb-3">
            MONITORING LIVE
          </h3>
          <p className="text-text-muted mb-6">
            Gemini AI is watching for exciting moments...
          </p>
          <div className="text-6xl font-black text-primary mb-2 font-mono">
            {countdown}s
          </div>
          <div className="max-w-md mx-auto h-2 bg-border-subtle rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary via-accent-gold to-primary rounded-full transition-all duration-1000"
              style={{ width: `${((30 - countdown) / 30) * 100}%` }}
            />
          </div>
          <p className="text-accent-gold text-xs mt-4 font-bold uppercase tracking-widest">
            Session: {sessionId}
          </p>
        </div>
      ) : (
        <div className="text-center p-8 bg-green-600/10 rounded-xl border-2 border-green-500">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-green-600/30 border-4 border-green-500 mb-6">
            <span className="text-4xl">✅</span>
          </div>
          <h3 className="text-white text-2xl font-black tracking-tighter uppercase mb-3">
            SESSION COMPLETE
          </h3>
          <p className="text-text-muted mb-6">
            Check the Producer view for detected moments with the LIVE badge
          </p>
          <button
            onClick={reset}
            className="px-6 py-3 bg-primary text-white text-sm font-black tracking-widest rounded-lg hover:bg-primary/80 transition-all"
          >
            START ANOTHER SESSION
          </button>
        </div>
      )}
    </div>
  );
}

// Helper function to get LiveKit token
async function getToken(roomName: string): Promise<string> {
  // For development, we'll generate a simple token on the client
  // In production, this should be generated by your backend
  const apiKey = process.env.NEXT_PUBLIC_LIVEKIT_API_KEY || "devkey";
  const apiSecret = process.env.NEXT_PUBLIC_LIVEKIT_API_SECRET || "secret";

  // Use AccessToken from livekit-server-sdk
  // For now, we'll make a request to a backend endpoint
  // TODO: Create backend endpoint for token generation

  // Temporary: Use dev credentials directly
  // This is NOT secure for production!
  try {
    const response = await fetch("/api/livekit-token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ roomName, identity: "screenshare_user" }),
    });

    if (!response.ok) {
      throw new Error("Failed to get token");
    }

    const data = await response.json();
    return data.token;
  } catch (error) {
    console.error("Error getting token:", error);
    // Fallback: return a basic token (this won't work in production)
    // You'll need to implement proper token generation
    throw new Error("Token generation not implemented. Please set up /api/livekit-token endpoint");
  }
}
