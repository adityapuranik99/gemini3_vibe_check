"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { MomentAnalysis } from "@/types/moments";
import { api, getFullClipUrl } from "@/lib/api";

export default function SocialView() {
  const router = useRouter();
  const [moments, setMoments] = useState<MomentAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [pendingCount, setPendingCount] = useState(0);
  const [publishedMoments, setPublishedMoments] = useState<Set<string>>(new Set());
  const [showToast, setShowToast] = useState<string | null>(null);

  useEffect(() => {
    const fetchMoments = async () => {
      try {
        const allData = await api.getMoments();
        const approved = allData.filter((m) => m.approval_status === "approved");
        const pending = allData.filter((m) => m.approval_status === "pending");

        setMoments(approved);
        setPendingCount(pending.length);
        setLoading(false);
      } catch (err) {
        console.error("Failed to fetch moments:", err);
        setLoading(false);
      }
    };

    fetchMoments();
    const interval = setInterval(fetchMoments, 2000);
    return () => clearInterval(interval);
  }, []);

  const handlePostNow = (momentId: string) => {
    // Mark as published and remove from view
    setPublishedMoments(prev => new Set([...prev, momentId]));
    setShowToast("Posted to Instagram & TikTok!");
    setTimeout(() => setShowToast(null), 3000);
  };

  // Filter out published moments
  const visibleMoments = moments.filter(m => !publishedMoments.has(m.moment_id));

  // Mock stats (can be replaced with real data later)
  const stats = {
    impressions: "18.4M",
    shares: "412.5K",
    sentiment: 88,
    velocity: "High",
    totalReach: "2,348,912",
    growth: "+14.2%",
  };

  return (
    <div className="min-h-screen bg-background-dark text-white font-display pb-32">
      {/* Top Nav */}
      <header className="border-b border-white/10 px-6 py-3 bg-panel-dark/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-[1440px] mx-auto flex items-center justify-between">
          <button onClick={() => router.push("/")} className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <div className="w-8 h-8 text-primary">
              <svg fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                <path
                  clipRule="evenodd"
                  d="M24 0.757355L47.2426 24L24 47.2426L0.757355 24L24 0.757355ZM21 35.7574V12.2426L9.24264 24L21 35.7574Z"
                  fill="currentColor"
                  fillRule="evenodd"
                />
              </svg>
            </div>
            <h2 className="text-white text-xl font-black leading-tight tracking-tighter uppercase italic">
              VIBE CHECK
            </h2>
          </button>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1 bg-green-500/20 border border-green-500/40 rounded text-green-400 text-[10px] font-black tracking-tighter">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
              {visibleMoments.length} READY
            </div>
            <div className="flex items-center gap-2 border-l border-border-subtle pl-4">
              <button
                onClick={() => router.push("/producer")}
                className="px-4 h-8 bg-white/5 border border-white/20 text-white text-[10px] font-black tracking-widest rounded hover:bg-white/10 transition-all"
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
                className="px-4 h-8 bg-primary/20 border-2 border-primary text-white text-[10px] font-black tracking-widest rounded"
              >
                📱 SOCIAL
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1440px] mx-auto px-6 py-8">
        {/* Page Heading */}
        <div className="flex flex-wrap justify-between items-end gap-4 mb-8">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2 text-accent-gold text-xs font-bold uppercase tracking-widest">
              <span className="w-2 h-2 bg-primary rounded-full animate-pulse"></span>
              Live Event Coverage
            </div>
            <h1 className="text-4xl font-black text-white leading-tight">Social Manager Pipeline</h1>
            <p className="text-white/50 text-base">Managing real-time publishing workflow</p>
          </div>
          <div className="flex gap-3">
            <div className="text-white/40 text-sm font-medium">
              {publishedMoments.size} published today
            </div>
          </div>
        </div>

        {/* Pending Approval Section */}
        {pendingCount > 0 && (
          <section className="mb-10">
            <div className="flex items-center justify-between mb-4 px-1">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <span className="text-accent-gold">🔒</span>
                Pending Approval
              </h3>
              <span className="font-mono text-xs text-white/40 bg-white/5 px-2 py-1 rounded">
                {pendingCount} ASSETS QUEUED
              </span>
            </div>
            <div className="bg-panel-dark/50 border border-white/5 rounded-xl p-8 text-center">
              <p className="text-white/40 text-sm">
                {pendingCount} moment{pendingCount !== 1 && "s"} awaiting executive approval
              </p>
            </div>
          </section>
        )}

        {/* Approved & Ready Section */}
        <section className="mb-20">
          <div className="flex items-center justify-between mb-4 px-1">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <span className="text-green-500">✅</span>
              Approved & Ready
            </h3>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
          ) : visibleMoments.length === 0 ? (
            <div className="bg-panel-dark/50 border border-white/5 rounded-xl p-12 text-center">
              <p className="text-white/40 text-lg mb-2">No approved moments yet</p>
              <p className="text-white/30 text-sm">Waiting for exec approval...</p>
            </div>
          ) : (
            <div className="space-y-4">
              {visibleMoments.map((moment) => (
                <div
                  key={moment.moment_id}
                  className="bg-panel-dark border border-white/10 rounded-xl p-4 flex flex-col md:flex-row gap-6 hover:bg-white/[0.02] transition-colors border-l-4 border-l-primary"
                >
                  {/* Video Preview */}
                  <div className="w-full md:w-64 aspect-video bg-center bg-cover rounded-lg relative flex-shrink-0 overflow-hidden">
                    {moment.clip_url ? (
                      <>
                        <video
                          className="w-full h-full object-cover"
                          src={getFullClipUrl(moment.clip_url)}
                          poster={getFullClipUrl(moment.clip_url)}
                        />
                        <div className="absolute inset-0 bg-black/20 hover:bg-transparent transition-colors cursor-pointer flex items-center justify-center group">
                          <span className="text-white text-4xl group-hover:scale-110 transition-transform">
                            ▶
                          </span>
                        </div>
                        <div className="absolute bottom-2 right-2 bg-black/60 px-1.5 py-0.5 rounded text-[10px] font-mono">
                          {Math.floor(moment.tr - moment.t0)}s
                        </div>
                      </>
                    ) : (
                      <div className="w-full h-full bg-black flex items-center justify-center">
                        <span className="text-white/20">NO CLIP</span>
                      </div>
                    )}
                  </div>

                  {/* Content */}
                  <div className="flex-grow flex flex-col justify-between py-1">
                    <div>
                      <div className="flex items-center gap-3 mb-1">
                        <h4 className="text-lg font-bold uppercase">
                          {moment.moment_type}: {moment.summary.slice(0, 60)}
                        </h4>
                        <span className="text-[10px] bg-green-600/20 text-green-400 px-2 py-0.5 rounded font-black tracking-widest uppercase">
                          ✅ APPROVED
                        </span>
                      </div>
                      <p className="text-white/50 text-sm max-w-xl line-clamp-2">
                        {moment.post_copy.neutral}
                      </p>

                      {/* Hype/Risk Scores */}
                      <div className="flex gap-6 mt-3">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-accent-gold font-bold uppercase">Hype</span>
                          <span className="font-mono text-sm font-bold text-white">{moment.scores.hype}</span>
                          <div className="w-16 h-1 bg-white/10 rounded-full overflow-hidden">
                            <div className="bg-primary h-full" style={{ width: `${moment.scores.hype}%` }} />
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-white/40 font-bold uppercase">Risk</span>
                          <span className="font-mono text-sm font-bold text-white">{moment.scores.risk}</span>
                          <div className="w-16 h-1 bg-white/10 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${
                                moment.scores.risk > 50
                                  ? "bg-red-500"
                                  : moment.scores.risk > 30
                                  ? "bg-yellow-500"
                                  : "bg-green-500"
                              }`}
                              style={{ width: `${moment.scores.risk}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-wrap items-center gap-6 mt-4 md:mt-0">
                      <div className="flex items-center gap-4">
                        <div className="flex flex-col">
                          <span className="text-[10px] text-white/30 uppercase font-bold mb-1">Platforms</span>
                          <div className="flex gap-2">
                            <div className="w-8 h-8 rounded bg-primary flex items-center justify-center text-white">
                              📷
                            </div>
                            <div className="w-8 h-8 rounded bg-primary flex items-center justify-center text-white">
                              🎬
                            </div>
                            <div className="w-8 h-8 rounded bg-white/10 flex items-center justify-center text-white/40">
                              📹
                            </div>
                          </div>
                        </div>
                      </div>
                      <div className="flex-grow"></div>
                      <div className="flex gap-3">
                        <button
                          onClick={() => handlePostNow(moment.moment_id)}
                          className="px-6 py-2 bg-primary hover:bg-red-700 rounded-lg text-sm font-bold shadow-lg shadow-primary/30 transition-all flex items-center gap-2"
                        >
                          🚀 POST NOW
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>

      {/* Performance Footer */}
      <footer className="fixed bottom-0 left-0 right-0 bg-panel-dark border-t border-white/10 z-40 px-6 py-4 shadow-2xl">
        <div className="max-w-[1440px] mx-auto flex flex-col lg:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-4 w-full lg:w-auto">
            <div className="bg-primary/10 p-2 rounded-lg">
              <span className="text-primary text-xl">📊</span>
            </div>
            <div>
              <h5 className="text-xs font-bold text-white/40 uppercase tracking-widest leading-none mb-1">
                Tonight's Performance
              </h5>
              <div className="flex items-baseline gap-2">
                <span className="font-mono text-2xl font-black text-white leading-none">{stats.totalReach}</span>
                <span className="text-[10px] text-green-500 font-bold uppercase tracking-tight flex items-center gap-1">
                  ↗ {stats.growth} VS AVG
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 w-full lg:w-auto">
            <div className="flex flex-col">
              <span className="text-[10px] text-white/30 uppercase font-bold mb-1">Impressions</span>
              <span className="font-mono text-base font-bold text-white">{stats.impressions}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-white/30 uppercase font-bold mb-1">Shares</span>
              <span className="font-mono text-base font-bold text-white">{stats.shares}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-white/30 uppercase font-bold mb-1">Sentiment</span>
              <div className="flex items-center gap-1.5">
                <span className="font-mono text-base font-bold text-green-400">{stats.sentiment}%</span>
                <div className="w-16 h-1 bg-white/10 rounded-full overflow-hidden">
                  <div className="bg-green-500 h-full" style={{ width: `${stats.sentiment}%` }} />
                </div>
              </div>
            </div>
            <div className="flex flex-col">
              <span className="text-[10px] text-white/30 uppercase font-bold mb-1">Velocity</span>
              <span className="font-mono text-base font-bold text-accent-gold">{stats.velocity}</span>
            </div>
          </div>

          <div className="flex gap-2 w-full lg:w-auto justify-end">
            <button
              onClick={() => router.push("/exec")}
              className="bg-accent-gold text-black px-4 py-2 rounded font-black text-xs uppercase tracking-tighter hover:bg-accent-gold/90 transition-colors"
            >
              VIEW WAR ROOM
            </button>
          </div>
        </div>
      </footer>

      {/* Toast Notification */}
      {showToast && (
        <div className="fixed top-6 right-6 z-50 animate-in slide-in-from-top">
          <div className="bg-green-600 text-white px-6 py-4 rounded-lg shadow-2xl flex items-center gap-3 border-2 border-green-400">
            <span className="text-2xl">✅</span>
            <div>
              <p className="font-bold text-sm">{showToast}</p>
              <p className="text-xs text-green-100">Content is now live</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
