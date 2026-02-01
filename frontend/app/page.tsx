"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/vibecheck-api";
import ScreenShare from "@/components/ScreenShare";

type UploadState = "idle" | "uploading" | "processing" | "ready" | "error";

export default function Home() {
  const router = useRouter();
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [dragActive, setDragActive] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [videoPath, setVideoPath] = useState<string>("");

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileInput = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await handleFile(e.target.files[0]);
    }
  }, []);

  const handleFile = async (file: File) => {
    console.log("🎬 handleFile called with:", file.name, file.type, file.size);

    // Validate file type
    if (!file.type.startsWith("video/")) {
      setErrorMessage("Please upload a video file");
      setUploadState("error");
      return;
    }

    // Validate file size (max 2GB)
    const maxSize = 2 * 1024 * 1024 * 1024;
    if (file.size > maxSize) {
      setErrorMessage("File size must be less than 2GB");
      setUploadState("error");
      return;
    }

    setUploadState("uploading");
    setErrorMessage("");
    setUploadProgress(0);

    try {
      console.log("🚀 Starting upload...");

      // Simulate upload progress (actual upload happens instantly for small files)
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      console.log("📤 Calling api.uploadVideo...");
      // Upload file to backend storage
      const uploadResult = await api.uploadVideo(file);
      console.log("✅ Upload result:", uploadResult);

      clearInterval(progressInterval);
      setUploadProgress(100);
      setVideoPath(uploadResult.video_path);

      // Start processing
      setUploadState("processing");
      console.log("🎬 Starting ingestion...");

      // Start video ingestion
      await api.startIngestion(uploadResult.video_path, "upload_stream");
      console.log("✅ Ingestion started");

      setUploadState("ready");
      console.log("✅ Upload complete!");
    } catch (error) {
      console.error("❌ Upload failed:", error);
      setErrorMessage(error instanceof Error ? error.message : "Upload failed");
      setUploadState("error");
    }
  };

  const navigateTo = (path: string) => {
    router.push(path);
  };

  return (
    <div className="min-h-screen flex flex-col bg-background-dark text-white font-display">
      {/* Top Header */}
      <header className="flex items-center justify-between border-b border-border-subtle px-10 py-4 bg-panel-dark">
        <div className="flex items-center gap-4">
          <div className="w-8 h-8 text-primary">
            <svg fill="currentColor" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
              <path d="M4 42.4379C4 42.4379 14.0962 36.0744 24 41.1692C35.0664 46.8624 44 42.2078 44 42.2078L44 7.01134C44 7.01134 35.068 11.6577 24.0031 5.96913C14.0971 0.876274 4 7.27094 4 7.27094L4 42.4379Z"></path>
            </svg>
          </div>
          <h1 className="text-white text-2xl font-extrabold leading-tight tracking-tighter">
            VIBE CHECK
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-primary/10 border border-primary/40 rounded">
            <span className="w-2 h-2 rounded-full bg-primary"></span>
            <span className="text-[10px] font-black tracking-widest text-primary">SYSTEM READY</span>
          </div>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-4xl">
          {uploadState === "idle" || uploadState === "uploading" || uploadState === "error" ? (
            <>
              {/* Mission Brief */}
              <div className="text-center mb-12">
                <div className="flex items-center justify-center gap-2 text-primary mb-3">
                  <span className="text-2xl">⚡</span>
                  <span className="text-xs font-black tracking-widest uppercase">Mission Control</span>
                </div>
                <h2 className="text-white text-5xl font-black tracking-tighter uppercase italic mb-4">
                  REALTIME PRODUCER COPILOT
                </h2>
                <p className="text-text-muted text-lg max-w-2xl mx-auto">
                  AI-powered moment detection for live sports and entertainment. Upload your video to begin tactical analysis.
                </p>
              </div>

              {/* Upload Zone */}
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`relative border-2 border-dashed rounded-xl p-16 transition-all ${
                  dragActive
                    ? "border-primary bg-primary/10 scale-[1.02]"
                    : uploadState === "error"
                    ? "border-red-500/50 bg-red-500/5"
                    : "border-border-subtle bg-panel-dark hover:border-primary/50"
                }`}
              >
                <input
                  type="file"
                  id="video-upload"
                  accept="video/*"
                  onChange={handleFileInput}
                  disabled={uploadState === "uploading"}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
                />

                <div className="text-center pointer-events-none">
                  {uploadState === "uploading" ? (
                    <>
                      <div className="text-6xl mb-6 animate-pulse">📤</div>
                      <h3 className="text-white text-2xl font-bold mb-3">UPLOADING VIDEO...</h3>
                      <div className="max-w-md mx-auto">
                        <div className="h-2 bg-border-subtle rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-primary via-accent-gold to-primary rounded-full transition-all duration-300"
                            style={{ width: `${uploadProgress}%` }}
                          />
                        </div>
                        <p className="text-accent-gold text-sm font-mono mt-2">{uploadProgress}% COMPLETE</p>
                      </div>
                    </>
                  ) : uploadState === "error" ? (
                    <>
                      <div className="text-6xl mb-6">⚠️</div>
                      <h3 className="text-red-400 text-2xl font-bold mb-3">UPLOAD FAILED</h3>
                      <p className="text-text-muted mb-4">{errorMessage}</p>
                      <button
                        onClick={() => setUploadState("idle")}
                        className="px-6 py-3 bg-primary text-white text-sm font-black tracking-widest rounded-lg hover:bg-red-700 transition-all pointer-events-auto"
                      >
                        TRY AGAIN
                      </button>
                    </>
                  ) : (
                    <>
                      <div className="text-6xl mb-6">🎬</div>
                      <h3 className="text-white text-2xl font-bold mb-3">DRAG & DROP VIDEO FILE</h3>
                      <p className="text-text-muted mb-6">or click to browse</p>
                      <div className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-white text-sm font-black tracking-widest rounded-lg pointer-events-auto">
                        <span>📁</span>
                        <span>SELECT FILE</span>
                      </div>
                      <p className="text-[10px] text-text-muted mt-6 uppercase tracking-wider">
                        Supported: MP4, MOV, AVI • Max size: 2GB
                      </p>
                    </>
                  )}
                </div>
              </div>

              {/* OR Divider */}
              <div className="flex items-center gap-4 my-12">
                <div className="flex-1 h-px bg-border-subtle"></div>
                <span className="text-text-muted text-sm font-bold tracking-widest uppercase">OR</span>
                <div className="flex-1 h-px bg-border-subtle"></div>
              </div>

              {/* Screen Share Option */}
              <ScreenShare onComplete={() => navigateTo("/producer")} />

              {/* Feature Overview */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
                <div className="bg-panel-dark p-6 rounded-lg border border-border-subtle">
                  <div className="text-3xl mb-3">🎯</div>
                  <h3 className="text-white text-sm font-black tracking-widest uppercase mb-2">
                    AI Detection
                  </h3>
                  <p className="text-text-muted text-xs">
                    Motion + audio analysis powered by Gemini 3 Flash
                  </p>
                </div>
                <div className="bg-panel-dark p-6 rounded-lg border border-border-subtle">
                  <div className="text-3xl mb-3">✂️</div>
                  <h3 className="text-white text-sm font-black tracking-widest uppercase mb-2">
                    Smart Clips
                  </h3>
                  <p className="text-text-muted text-xs">
                    Automatic assembly with reaction-first stitching
                  </p>
                </div>
                <div className="bg-panel-dark p-6 rounded-lg border border-border-subtle">
                  <div className="text-3xl mb-3">📝</div>
                  <h3 className="text-white text-sm font-black tracking-widest uppercase mb-2">
                    Post Copy
                  </h3>
                  <p className="text-text-muted text-xs">
                    Three AI-generated variants: hype, neutral, brand-safe
                  </p>
                </div>
              </div>
            </>
          ) : uploadState === "processing" ? (
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-32 h-32 rounded-full bg-primary/20 border-4 border-primary/40 mb-8 animate-pulse">
                <span className="text-5xl">⚙️</span>
              </div>
              <h2 className="text-white text-4xl font-black tracking-tighter uppercase italic mb-4">
                ANALYZING VIDEO
              </h2>
              <p className="text-text-muted text-lg mb-8">
                AI is detecting high-energy moments and generating clips...
              </p>
              <div className="max-w-md mx-auto space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-accent-gold font-bold">⚡ Stage A: Motion + Audio Detection</span>
                  <span className="text-green-500">✓</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white font-bold">🤖 Stage B: Gemini Analysis</span>
                  <div className="animate-spin w-4 h-4 border-2 border-primary border-t-transparent rounded-full"></div>
                </div>
                <div className="flex items-center justify-between text-sm opacity-50">
                  <span className="text-text-muted">✂️ Clip Assembly</span>
                  <span className="text-text-muted">—</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-32 h-32 rounded-full bg-green-600/20 border-4 border-green-500/40 mb-8">
                <span className="text-5xl">✅</span>
              </div>
              <h2 className="text-white text-4xl font-black tracking-tighter uppercase italic mb-4">
                MISSION READY
              </h2>
              <p className="text-text-muted text-lg mb-12">
                Video processed successfully. Select your tactical view.
              </p>

              {/* Navigation Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <button
                  onClick={() => navigateTo("/producer")}
                  className="group bg-panel-dark border-2 border-border-subtle hover:border-primary p-8 rounded-xl transition-all hover:scale-105 hover:shadow-xl hover:shadow-primary/20 text-left"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-3xl">🎬</span>
                    <h3 className="text-white text-xl font-black tracking-tight uppercase">Producer</h3>
                  </div>
                  <p className="text-text-muted text-sm mb-4">
                    Full tactical view with moment details, AI copy variants, and publishing controls
                  </p>
                  <div className="flex items-center gap-2 text-primary text-xs font-bold">
                    <span>ENTER WAR ROOM</span>
                    <span className="group-hover:translate-x-1 transition-transform">→</span>
                  </div>
                </button>

                <button
                  onClick={() => navigateTo("/exec")}
                  className="group bg-panel-dark border-2 border-border-subtle hover:border-accent-gold p-8 rounded-xl transition-all hover:scale-105 hover:shadow-xl hover:shadow-accent-gold/20 text-left"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-3xl">⚖️</span>
                    <h3 className="text-white text-xl font-black tracking-tight uppercase">Executive</h3>
                  </div>
                  <p className="text-text-muted text-sm mb-4">
                    One-at-a-time decision flow for high-stakes content approval
                  </p>
                  <div className="flex items-center gap-2 text-accent-gold text-xs font-bold">
                    <span>MAKE DECISIONS</span>
                    <span className="group-hover:translate-x-1 transition-transform">→</span>
                  </div>
                </button>

                <button
                  onClick={() => navigateTo("/social")}
                  className="group bg-panel-dark border-2 border-border-subtle hover:border-green-500 p-8 rounded-xl transition-all hover:scale-105 hover:shadow-xl hover:shadow-green-500/20 text-left"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <span className="text-3xl">📱</span>
                    <h3 className="text-white text-xl font-black tracking-tight uppercase">Social</h3>
                  </div>
                  <p className="text-text-muted text-sm mb-4">
                    Gallery of approved moments ready for social media publishing
                  </p>
                  <div className="flex items-center gap-2 text-green-500 text-xs font-bold">
                    <span>VIEW APPROVED</span>
                    <span className="group-hover:translate-x-1 transition-transform">→</span>
                  </div>
                </button>
              </div>

              {/* Quick Actions */}
              <div className="mt-12 flex items-center justify-center gap-4">
                <button
                  onClick={() => {
                    setUploadState("idle");
                    setUploadProgress(0);
                    setVideoPath("");
                  }}
                  className="px-6 py-3 bg-white/10 border border-white/20 text-white text-sm font-bold tracking-widest rounded-lg hover:bg-white/20 transition-all"
                >
                  ← UPLOAD ANOTHER
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* System Footer */}
      <footer className="h-10 bg-black border-t border-border-subtle px-8 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
            <span className="text-[10px] font-black text-text-muted tracking-widest uppercase">System Online</span>
          </div>
          <span className="text-[10px] text-text-muted">
            {uploadState !== "idle" && videoPath && `VIDEO: ${videoPath.split("/").pop()}`}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-[10px] font-mono text-accent-gold">VIBE_CHECK_V1.0.0</span>
        </div>
      </footer>
    </div>
  );
}
