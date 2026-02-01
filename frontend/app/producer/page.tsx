"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { MomentAnalysis } from "@/types/moments";
import { api, getFullClipUrl } from "@/lib/vibecheck-api";
import AudioWaveform from "@/components/AudioWaveform";

type FilterType = "all" | "pending" | "approved";

export default function ProducerView() {
  const router = useRouter();
  const [moments, setMoments] = useState<MomentAnalysis[]>([]);
  const [selectedMomentId, setSelectedMomentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [audioLevel, setAudioLevel] = useState(0.5);
  const [filter, setFilter] = useState<FilterType>("all");
  const [copiedText, setCopiedText] = useState<string | null>(null);
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const hasAutoSelectedRef = useRef(false);

  // Get the actual selected moment object from the ID
  const selectedMoment = moments.find(m => m.moment_id === selectedMomentId) || null;

  // Filter moments based on current filter
  // Producer only sees "pending" moments - not ones already sent to exec
  const filteredMoments = moments.filter(m => {
    // Never show moments already sent to exec or processed
    if (m.approval_status === "sent_to_exec" || m.approval_status === "approved" || m.approval_status === "held") {
      return false;
    }
    if (filter === "all") return true;
    if (filter === "pending") return m.approval_status === "pending";
    return true;
  });

  useEffect(() => {
    const fetchMoments = async () => {
      try {
        const data = await api.getMoments();
        console.log("📊 Fetched moments:", data.length, data);
        setMoments(data);

        // Only auto-select first moment on the very first fetch
        if (data.length > 0 && !hasAutoSelectedRef.current) {
          setSelectedMomentId(data[0].moment_id);
          hasAutoSelectedRef.current = true;
        }
        setLoading(false);
      } catch (err) {
        console.error("❌ Failed to fetch moments:", err);
        setLoading(false);
      }
    };

    fetchMoments();
    const interval = setInterval(fetchMoments, 2000);

    // Simulate audio level changes
    const audioInterval = setInterval(() => {
      setAudioLevel(Math.random() * 0.6 + 0.2);
    }, 200);

    return () => {
      clearInterval(interval);
      clearInterval(audioInterval);
    };
  }, []);

  const copyToClipboard = async (text: string, variant: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedText(variant);
      setTimeout(() => setCopiedText(null), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const formatTimecode = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    const f = Math.floor((seconds % 1) * 30); // Assuming 30fps
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}:${f.toString().padStart(2, "0")}`;
  };

  const getTimeAgo = (t0: number) => {
    const now = Date.now() / 1000;
    const diff = Math.floor(now - t0);
    const mins = Math.floor(diff / 60);
    const secs = diff % 60;
    return mins > 0 ? `${mins}:${secs.toString().padStart(2, "0")} AGO` : `${secs} SEC AGO`;
  };

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background-dark text-white font-display">
      {/* Top Nav Bar */}
      <header className="flex items-center justify-between border-b border-border-subtle px-8 py-3 bg-panel-dark">
        <div className="flex items-center gap-8">
          <button onClick={() => router.push("/")} className="flex items-center gap-4 hover:opacity-80 transition-opacity">
            <div className="w-6 h-6 text-primary">
              <svg fill="currentColor" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 42.4379C4 42.4379 14.0962 36.0744 24 41.1692C35.0664 46.8624 44 42.2078 44 42.2078L44 7.01134C44 7.01134 35.068 11.6577 24.0031 5.96913C14.0971 0.876274 4 7.27094 4 7.27094L4 42.4379Z"></path>
              </svg>
            </div>
            <h2 className="text-white text-lg font-extrabold leading-tight tracking-tighter">
              VIBE CHECK
            </h2>
          </button>
          <nav className="flex items-center gap-6">
            <button
              onClick={() => setFilter("all")}
              className={`text-xs font-bold leading-normal tracking-widest transition-colors ${
                filter === "all" ? "text-white border-b-2 border-primary pb-1" : "text-text-muted hover:text-white"
              }`}
            >
              ALL MOMENTS
            </button>
            <button
              onClick={() => setFilter("pending")}
              className={`text-xs font-bold leading-normal tracking-widest transition-colors ${
                filter === "pending" ? "text-white border-b-2 border-primary pb-1" : "text-text-muted hover:text-white"
              }`}
            >
              PENDING REVIEW
            </button>
            <button
              onClick={() => setFilter("approved")}
              className={`text-xs font-bold leading-normal tracking-widest transition-colors ${
                filter === "approved" ? "text-white border-b-2 border-primary pb-1" : "text-text-muted hover:text-white"
              }`}
            >
              APPROVED
            </button>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 bg-primary/20 border border-primary/40 rounded text-primary animate-pulse">
            <span className="w-2 h-2 rounded-full bg-primary"></span>
            <span className="text-[10px] font-black tracking-tighter">{filteredMoments.length} DETECTED</span>
          </div>
          <div className="flex items-center gap-2 border-l border-border-subtle pl-4">
            <button
              onClick={() => router.push("/producer")}
              className="px-4 h-8 bg-primary/20 border-2 border-primary text-white text-[10px] font-black tracking-widest rounded"
            >
              🎬 PRODUCER
            </button>
            <button
              onClick={() => router.push("/exec")}
              className="px-4 h-8 bg-white/5 border border-white/20 text-white text-[10px] font-black tracking-widest rounded hover:bg-white/10 transition-all"
            >
              ⚖️ EXEC
            </button>
            <button
              onClick={() => router.push("/social")}
              className="px-4 h-8 bg-white/5 border border-white/20 text-white text-[10px] font-black tracking-widest rounded hover:bg-white/10 transition-all"
            >
              📱 SOCIAL
            </button>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Column: Video & Audio Monitor */}
        <div className="w-1/3 flex flex-col border-r border-border-subtle overflow-y-auto">
          <div className="p-4 border-b border-border-subtle flex items-center justify-between">
            <span className="text-xs font-black tracking-widest text-white">BROADCAST MONITOR</span>
            <span className="text-[10px] text-text-muted">CH-01 • PRIMARY FEED</span>
          </div>

          {/* Video Player */}
          <div className="p-4">
            {selectedMoment?.clip_url ? (
              <div className="relative aspect-video rounded-lg overflow-hidden border-2 border-primary/30 shadow-lg shadow-primary/20">
                <video
                  controls
                  autoPlay
                  className="w-full h-full"
                  src={getFullClipUrl(selectedMoment.clip_url)}
                />
              </div>
            ) : (
              <div className="relative aspect-video rounded-lg overflow-hidden bg-black flex items-center justify-center border border-border-subtle">
                <div className="text-text-muted text-center">
                  <div className="text-4xl mb-2">▶</div>
                  <p className="text-xs">NO ACTIVE CLIP</p>
                </div>
              </div>
            )}
          </div>

          {/* Audio Levels */}
          <div className="flex flex-col gap-4 p-4">
            <div className="bg-panel-dark p-4 rounded-xl border border-border-subtle">
              <div className="flex justify-between items-end mb-3">
                <div>
                  <p className="text-accent-gold text-[10px] font-black tracking-widest uppercase">Audio Matrix</p>
                  <h3 className="text-white text-sm font-bold tracking-tight">STADIUM AMBIENT</h3>
                </div>
                <p className="text-white text-xs font-mono">-{((1 - audioLevel) * 10).toFixed(1)}dB</p>
              </div>

              <AudioWaveform audioLevel={audioLevel} className="mb-4" />

              <div className="rounded bg-border-subtle h-1 overflow-hidden">
                <div
                  className="h-1 rounded bg-gradient-to-r from-green-500 via-yellow-400 to-primary transition-all duration-200"
                  style={{ width: `${audioLevel * 100}%` }}
                />
              </div>

              <div className="flex justify-between mt-1">
                <p className="text-text-muted text-[9px] font-bold">L-CHANNEL</p>
                <p className={`text-[9px] font-bold ${audioLevel > 0.8 ? "text-primary" : "text-green-500"}`}>
                  {audioLevel > 0.8 ? "PEAKING" : "NOMINAL"}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Center Column: Selected Moment Detail */}
        <div className="flex-1 flex flex-col bg-panel-dark overflow-y-auto">
          {selectedMoment ? (
            <>
              <div className="p-6 border-b border-border-subtle">
                <div className="flex items-center gap-2 text-primary mb-1">
                  <span className="text-lg">⚡</span>
                  <span className="text-xs font-black tracking-widest uppercase">Detection Active</span>
                  {selectedMoment.source === "livekit_screenshare" && (
                    <span className="ml-2 px-2 py-1 bg-red-500 text-white text-[10px] font-black tracking-widest rounded animate-pulse">
                      🔴 LIVE
                    </span>
                  )}
                </div>
                <h2 className="text-white text-3xl font-black tracking-tighter uppercase italic">
                  {selectedMoment.moment_type}: {selectedMoment.summary}
                </h2>

                <div className="flex gap-4 mt-4">
                  <div className="flex flex-col">
                    <span className="text-[10px] text-accent-gold font-bold tracking-widest">IN POINT</span>
                    <span className="text-sm font-mono text-white">{formatTimecode(selectedMoment.t0)}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[10px] text-accent-gold font-bold tracking-widest">OUT POINT</span>
                    <span className="text-sm font-mono text-white">{formatTimecode(selectedMoment.tr)}</span>
                  </div>
                  <div className="flex flex-col border-l border-border-subtle pl-4">
                    <span className="text-[10px] text-accent-gold font-bold tracking-widest">DURATION</span>
                    <span className="text-sm font-mono text-white">
                      {formatTimecode(selectedMoment.tr - selectedMoment.t0)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-6 flex flex-col gap-8">
                {/* AI Copy Variants */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-white text-xs font-black tracking-widest uppercase">AI Post Copy Variants</h3>
                    <button className="flex items-center gap-1 text-[10px] font-bold text-accent-gold hover:text-white transition-colors">
                      🔄 REGENERATE ALL
                    </button>
                  </div>

                  {/* Hype Variant */}
                  <div
                    onClick={() => copyToClipboard(selectedMoment.post_copy.hype, "hype")}
                    className="p-4 bg-primary/10 border-l-4 border-primary rounded-r-lg group hover:bg-primary/20 transition-all cursor-pointer relative"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="px-2 py-0.5 bg-primary text-[9px] font-black tracking-widest rounded">HYPE</span>
                      <span className="text-sm group-hover:scale-110 transition-transform">
                        {copiedText === "hype" ? "✓" : "📋"}
                      </span>
                    </div>
                    <p className="text-sm font-medium leading-relaxed">{selectedMoment.post_copy.hype}</p>
                    {copiedText === "hype" && (
                      <div className="absolute top-2 right-12 bg-green-600 text-white text-[10px] px-2 py-1 rounded font-bold">
                        COPIED!
                      </div>
                    )}
                  </div>

                  {/* Neutral Variant */}
                  <div
                    onClick={() => copyToClipboard(selectedMoment.post_copy.neutral, "neutral")}
                    className="p-4 bg-white/5 border-l-4 border-accent-gold rounded-r-lg group hover:bg-white/10 transition-all cursor-pointer relative"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="px-2 py-0.5 bg-accent-gold text-[9px] font-black tracking-widest rounded">NEUTRAL</span>
                      <span className="text-sm text-accent-gold">
                        {copiedText === "neutral" ? "✓" : "📋"}
                      </span>
                    </div>
                    <p className="text-sm font-medium leading-relaxed">{selectedMoment.post_copy.neutral}</p>
                    {copiedText === "neutral" && (
                      <div className="absolute top-2 right-12 bg-green-600 text-white text-[10px] px-2 py-1 rounded font-bold">
                        COPIED!
                      </div>
                    )}
                  </div>

                  {/* Brand Safe Variant */}
                  <div
                    onClick={() => copyToClipboard(selectedMoment.post_copy.brand_safe, "safe")}
                    className="p-4 bg-white/5 border-l-4 border-text-muted rounded-r-lg group hover:bg-white/10 transition-all cursor-pointer relative"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="px-2 py-0.5 bg-text-muted text-[9px] font-black tracking-widest rounded">SAFE</span>
                      <span className="text-sm text-text-muted">
                        {copiedText === "safe" ? "✓" : "📋"}
                      </span>
                    </div>
                    <p className="text-sm font-medium leading-relaxed">{selectedMoment.post_copy.brand_safe}</p>
                    {copiedText === "safe" && (
                      <div className="absolute top-2 right-12 bg-green-600 text-white text-[10px] px-2 py-1 rounded font-bold">
                        COPIED!
                      </div>
                    )}
                  </div>
                </div>

                {/* Match Intel Panel */}
                {(selectedMoment.player_info || selectedMoment.match_stats) && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <h3 className="text-white text-xs font-black tracking-widest uppercase">Match Intel</h3>
                      <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-[9px] font-black tracking-widest rounded">
                        SEARCH GROUNDED
                      </span>
                    </div>

                    <div className="bg-white/5 border border-border-subtle rounded-lg p-4 space-y-4">
                      {/* Player Info */}
                      {selectedMoment.player_info && (
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <span className="text-accent-gold text-[10px] font-black tracking-widest">PLAYER</span>
                            {selectedMoment.player_info.jersey_number && (
                              <span className="px-1.5 py-0.5 bg-primary/20 text-primary text-[9px] font-black tracking-widest rounded">
                                #{selectedMoment.player_info.jersey_number}
                              </span>
                            )}
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            {selectedMoment.player_info.name && (
                              <div>
                                <p className="text-text-muted text-[10px] font-bold">NAME</p>
                                <p className="text-white font-semibold">{selectedMoment.player_info.name}</p>
                              </div>
                            )}
                            {selectedMoment.player_info.team && (
                              <div>
                                <p className="text-text-muted text-[10px] font-bold">TEAM</p>
                                <p className="text-white font-semibold">{selectedMoment.player_info.team}</p>
                              </div>
                            )}
                            {selectedMoment.player_info.position && (
                              <div>
                                <p className="text-text-muted text-[10px] font-bold">POSITION</p>
                                <p className="text-white font-semibold">{selectedMoment.player_info.position}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Match Stats */}
                      {selectedMoment.match_stats && (
                        <div className="space-y-2 pt-4 border-t border-border-subtle">
                          <span className="text-accent-gold text-[10px] font-black tracking-widest">MATCH CONTEXT</span>

                          {selectedMoment.match_stats.teams.length > 0 && (
                            <div className="flex items-center gap-2 text-sm">
                              <p className="text-white font-semibold">{selectedMoment.match_stats.teams.join(" vs ")}</p>
                              {selectedMoment.match_stats.score && (
                                <span className="px-2 py-0.5 bg-white/10 text-white text-[10px] font-black rounded">
                                  {selectedMoment.match_stats.score}
                                </span>
                              )}
                            </div>
                          )}

                          <div className="grid grid-cols-2 gap-2 text-xs">
                            {selectedMoment.match_stats.quarter_period && (
                              <div>
                                <p className="text-text-muted text-[10px] font-bold">PERIOD</p>
                                <p className="text-white">{selectedMoment.match_stats.quarter_period}</p>
                              </div>
                            )}
                            {selectedMoment.match_stats.game_date && (
                              <div>
                                <p className="text-text-muted text-[10px] font-bold">DATE</p>
                                <p className="text-white">{selectedMoment.match_stats.game_date}</p>
                              </div>
                            )}
                            {selectedMoment.match_stats.venue && (
                              <div className="col-span-2">
                                <p className="text-text-muted text-[10px] font-bold">VENUE</p>
                                <p className="text-white">{selectedMoment.match_stats.venue}</p>
                              </div>
                            )}
                          </div>

                          {/* Key Stats */}
                          {selectedMoment.match_stats.key_stats.length > 0 && (
                            <div className="pt-2">
                              <p className="text-text-muted text-[10px] font-bold mb-2">KEY STATS</p>
                              <div className="space-y-1">
                                {selectedMoment.match_stats.key_stats.map((stat, idx) => (
                                  <div key={idx} className="flex items-center gap-2">
                                    <span className="text-primary text-[10px]">▸</span>
                                    <span className="text-white text-xs">{stat}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Share Card Preview */}
                {selectedMoment.share_card_url && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h3 className="text-white text-xs font-black tracking-widest uppercase">Share Card</h3>
                      <a
                        href={getFullClipUrl(selectedMoment.share_card_url)}
                        download={`${selectedMoment.moment_id}_share_card.png`}
                        className="flex items-center gap-1 text-[10px] font-bold text-accent-gold hover:text-white transition-colors"
                      >
                        📥 DOWNLOAD
                      </a>
                    </div>
                    <div className="relative rounded-lg overflow-hidden border border-border-subtle">
                      <img
                        src={getFullClipUrl(selectedMoment.share_card_url)}
                        alt="Share card preview"
                        className="w-full h-auto"
                      />
                    </div>
                  </div>
                )}

                {/* Tactical Buttons */}
                <div className="flex gap-3 pt-4 border-t border-border-subtle">
                  <button
                    onClick={() => setShowOverrideModal(true)}
                    className="flex-1 flex items-center justify-center gap-2 h-12 bg-white/10 border border-white/20 rounded-lg text-[11px] font-black tracking-widest hover:bg-white/20 transition-all"
                  >
                    ✏️ OVERRIDE CLIP
                  </button>
                  <button
                    onClick={async () => {
                      console.log("🔴 SEND TO EXEC clicked", { selectedMoment, isSending });
                      if (!selectedMoment || isSending) {
                        console.log("🔴 Early return - selectedMoment:", selectedMoment, "isSending:", isSending);
                        return;
                      }
                      setIsSending(true);
                      try {
                        console.log("🔴 Calling fetch directly for:", selectedMoment.moment_id);
                        const baseUrl = `http://${window.location.hostname}:8000`;
                        const response = await fetch(`${baseUrl}/api/moments/${selectedMoment.moment_id}/send_to_exec`, {
                          method: "POST",
                        });
                        if (!response.ok) {
                          throw new Error(`Failed to send to exec: ${response.statusText}`);
                        }
                        console.log(`📤 Sent moment ${selectedMoment.moment_id} to exec`);
                        // Clear selection since moment will disappear from list
                        setSelectedMomentId(null);
                      } catch (err) {
                        console.error("Failed to send to exec:", err);
                      } finally {
                        setIsSending(false);
                      }
                    }}
                    disabled={isSending}
                    className="flex-1 flex items-center justify-center gap-2 h-12 bg-primary rounded-lg text-[11px] font-black tracking-widest text-white shadow-lg shadow-primary/30 hover:bg-red-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSending ? "SENDING..." : "→ SEND TO EXEC"}
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              <p className="text-text-muted text-sm">SELECT A MOMENT FROM THE RIGHT PANEL</p>
            </div>
          )}
        </div>

        {/* Right Column: Active Moments List */}
        <div className="w-80 flex flex-col border-l border-border-subtle bg-background-dark overflow-y-auto">
          <div className="p-4 border-b border-border-subtle">
            <h2 className="text-white text-xs font-black tracking-widest uppercase">ACTIVE MOMENTS</h2>
            <p className="text-[10px] text-text-muted mt-1">{moments.length} DETECTED</p>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : filteredMoments.length === 0 ? (
            <div className="p-4 text-center text-text-muted">
              <p className="text-xs">NO MOMENTS IN THIS FILTER</p>
              <p className="text-[10px] mt-2">
                {filter === "pending" && "NO PENDING MOMENTS"}
                {filter === "approved" && "NO APPROVED MOMENTS"}
                {filter === "all" && "LISTENING FOR SIGNALS..."}
              </p>
            </div>
          ) : (
            <div className="flex flex-col divide-y divide-border-subtle">
              {filteredMoments.map((moment) => {
                const isSelected = selectedMoment?.moment_id === moment.moment_id;

                return (
                  <div
                    key={moment.moment_id}
                    onClick={() => setSelectedMomentId(moment.moment_id)}
                    className={`p-4 cursor-pointer transition-colors ${
                      isSelected
                        ? "bg-primary/5 border-l-4 border-primary"
                        : "hover:bg-white/5 border-l-4 border-transparent opacity-60"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] font-black tracking-widest uppercase ${
                          isSelected ? "text-primary" : "text-text-muted"
                        }`}>
                          {isSelected ? "Current Focus" : "Detected"}
                        </span>
                        {moment.source === "livekit_screenshare" && (
                          <span className="px-1.5 py-0.5 bg-red-500 text-white text-[8px] font-black tracking-widest rounded">
                            LIVE
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] font-mono text-text-muted">
                        {getTimeAgo(moment.t0)}
                      </span>
                    </div>

                    <h4 className="text-white text-sm font-bold mb-3 tracking-tight uppercase">
                      {moment.moment_type}: {moment.summary.slice(0, 40)}...
                    </h4>

                    {/* Hype/Risk Meters */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="flex flex-col gap-1">
                        <div className="flex justify-between items-end">
                          <span className="text-[9px] font-bold text-accent-gold">HYPE</span>
                          <span className="text-xs font-black text-white">{moment.scores.hype}</span>
                        </div>
                        <div className="h-1.5 w-full bg-border-subtle rounded-full overflow-hidden">
                          <div className="h-full bg-primary" style={{ width: `${moment.scores.hype}%` }} />
                        </div>
                      </div>

                      <div className="flex flex-col gap-1">
                        <div className="flex justify-between items-end">
                          <span className="text-[9px] font-bold text-text-muted">RISK</span>
                          <span className="text-xs font-black text-white">{moment.scores.risk}</span>
                        </div>
                        <div className="h-1.5 w-full bg-border-subtle rounded-full overflow-hidden">
                          <div
                            className={`h-full ${
                              moment.scores.risk > 50 ? "bg-red-500" : moment.scores.risk > 30 ? "bg-yellow-500" : "bg-green-500"
                            }`}
                            style={{ width: `${moment.scores.risk}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Approval Status Badge */}
                    {moment.approval_status && moment.approval_status !== "pending" && (
                      <div className="mt-2 pt-2 border-t border-border-subtle">
                        <span className={`text-[9px] font-black tracking-widest px-2 py-1 rounded ${
                          moment.approval_status === "approved"
                            ? "bg-green-600/20 text-green-400"
                            : "bg-yellow-600/20 text-yellow-400"
                        }`}>
                          {moment.approval_status === "approved" ? "✅ APPROVED" : "⏸️ ON HOLD"}
                        </span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* System Footer */}
      <footer className="h-8 bg-black border-t border-border-subtle px-6 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
            <span className="text-[10px] font-black text-text-muted tracking-widest uppercase">Stream Healthy</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-black text-text-muted tracking-widest uppercase">
              Lat: 0.8s
            </span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-[10px] font-mono text-accent-gold">VIBE_CHECK_V1.0.0</span>
          <span className="text-[10px] font-mono text-white">USER: PRODUCER_ALPHA</span>
        </div>
      </footer>

      {/* Override Clip Modal */}
      {showOverrideModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50" onClick={() => setShowOverrideModal(false)}>
          <div className="bg-panel-dark border-2 border-primary rounded-xl p-8 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">🎬</span>
              <h3 className="text-white text-xl font-black tracking-tight uppercase">Override Clip</h3>
            </div>
            <p className="text-text-muted text-sm mb-6">
              Manual clip editing coming soon. This feature will integrate with fal for advanced video processing and custom clip assembly.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowOverrideModal(false)}
                className="flex-1 px-4 py-3 bg-white/10 border border-white/20 text-white text-sm font-bold rounded-lg hover:bg-white/20 transition-all"
              >
                CLOSE
              </button>
              <button
                onClick={() => setShowOverrideModal(false)}
                className="flex-1 px-4 py-3 bg-primary text-white text-sm font-bold rounded-lg hover:bg-red-700 transition-all"
              >
                GOT IT
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
