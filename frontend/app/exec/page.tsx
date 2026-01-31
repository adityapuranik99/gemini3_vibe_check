"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { MomentAnalysis } from "@/types/moments";
import { api, getFullClipUrl } from "@/lib/api";

export default function ExecView() {
  const router = useRouter();
  const [moments, setMoments] = useState<MomentAnalysis[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const fetchMoments = async () => {
      try {
        const data = await api.getMoments();
        setMoments(data);
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

  const currentMoment = moments[currentIndex];

  const handleApprove = async () => {
    if (!currentMoment || isSubmitting) return;

    setIsSubmitting(true);
    try {
      await api.approveMoment({
        type: "moment.approved",
        moment_id: currentMoment.moment_id,
        by: "exec",
        at: Date.now() / 1000,
      });

      // Move to next moment
      if (currentIndex < moments.length - 1) {
        setCurrentIndex(currentIndex + 1);
      }
    } catch (error) {
      console.error("Failed to approve:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleHold = async () => {
    if (!currentMoment || isSubmitting) return;

    setIsSubmitting(true);
    try {
      await api.approveMoment({
        type: "moment.held",
        moment_id: currentMoment.moment_id,
        by: "exec",
        at: Date.now() / 1000,
      });

      // Move to next moment
      if (currentIndex < moments.length - 1) {
        setCurrentIndex(currentIndex + 1);
      }
    } catch (error) {
      console.error("Failed to hold:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getCurrentTime = () => {
    const now = new Date();
    return now.toLocaleTimeString("en-US", { hour12: false });
  };

  return (
    <div className="min-h-screen bg-background-dark text-white font-display">
      {/* Top Navigation */}
      <header className="flex items-center justify-between border-b border-primary/20 bg-background-dark px-10 py-3 sticky top-0 z-50">
        <button onClick={() => router.push("/")} className="flex items-center gap-4 hover:opacity-80 transition-opacity">
          <div className="w-6 h-6">
            <span className="text-3xl">⚖️</span>
          </div>
          <h2 className="text-white text-lg font-bold leading-tight tracking-tight">
            VIBE CHECK
          </h2>
        </button>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 bg-primary/20 border border-primary/40 rounded text-primary animate-pulse">
            <span className="w-2 h-2 rounded-full bg-primary"></span>
            <span className="text-[10px] font-black tracking-tighter">
              {moments.length - currentIndex} PENDING
            </span>
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
              className="px-4 h-8 bg-primary/20 border-2 border-primary text-white text-[10px] font-black tracking-widest rounded"
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

      <main className="flex flex-1 flex-col items-center py-8">
        <div className="flex flex-col max-w-[1200px] w-full px-6 gap-6">
          {/* Page Heading */}
          <div className="flex flex-wrap justify-between items-end gap-3 bg-card-dark p-6 rounded-xl border border-primary/20">
            <div className="flex min-w-72 flex-col gap-1">
              <div className="flex items-center gap-2 text-primary">
                <span className="text-lg">⚖️</span>
                <span className="text-xs font-bold uppercase tracking-widest">
                  {moments.length - currentIndex} Decision{moments.length - currentIndex !== 1 && "s"} Required
                </span>
              </div>
              <p className="text-white text-4xl font-black leading-tight tracking-tight">Executive Decision Room</p>
              <p className="text-slate-400 text-base font-normal leading-normal">
                High-stakes content moderation for live coverage
              </p>
            </div>
            <div className="flex gap-3">
              <div className="flex flex-col items-end">
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-tighter">Current Time (PST)</span>
                <span className="text-xl font-mono font-bold text-slate-200">{getCurrentTime()}</span>
              </div>
              <button className="px-6 h-12 bg-primary/10 border border-primary/30 text-white text-sm font-bold rounded-lg hover:bg-primary/20 transition-colors">
                View Live Feed
              </button>
            </div>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-96">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
          ) : moments.length === 0 ? (
            <div className="bg-card-dark border border-primary/20 rounded-xl p-12 text-center">
              <p className="text-slate-400 text-lg">No moments awaiting approval</p>
              <p className="text-slate-500 text-sm mt-2">All clear</p>
            </div>
          ) : !currentMoment ? (
            <div className="bg-card-dark border border-green-500/20 rounded-xl p-12 text-center">
              <span className="text-6xl mb-4 block">✅</span>
              <p className="text-white text-2xl font-bold">All Decisions Complete</p>
              <p className="text-slate-400 text-sm mt-2">
                {moments.length} moment{moments.length !== 1 && "s"} reviewed
              </p>
            </div>
          ) : (
            <>
              {/* Stats Overview */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex flex-1 flex-col gap-2 rounded-xl p-6 border border-primary/20 bg-card-dark shadow-sm">
                  <div className="flex justify-between items-start">
                    <p className="text-slate-300 text-base font-medium">Hype Level</p>
                    <span className="text-primary text-2xl">🔥</span>
                  </div>
                  <p className="text-white tracking-tight text-3xl font-black italic">
                    {currentMoment.scores.hype >= 85
                      ? "CRITICAL 🔥🔥🔥"
                      : currentMoment.scores.hype >= 70
                      ? "HIGH 🔥🔥"
                      : "MODERATE 🔥"}
                  </p>
                  <div className="w-full bg-primary/10 h-3 rounded-full overflow-hidden mt-2">
                    <div className="bg-primary h-full" style={{ width: `${currentMoment.scores.hype}%` }} />
                  </div>
                  <p className="text-green-400 text-sm font-bold mt-1">Score: {currentMoment.scores.hype}/100</p>
                </div>

                <div className="flex flex-1 flex-col gap-2 rounded-xl p-6 border border-primary/20 bg-card-dark shadow-sm">
                  <div className="flex justify-between items-start">
                    <p className="text-slate-300 text-base font-medium">Risk Level</p>
                    <span className="text-accent-gold text-2xl">⚠️</span>
                  </div>
                  <p className="text-white tracking-tight text-3xl font-black italic">
                    {currentMoment.scores.risk >= 70
                      ? "SEVERE ⚠️⚠️⚠️"
                      : currentMoment.scores.risk >= 40
                      ? "MODERATE ⚠️⚠️"
                      : "LOW ⚠️"}
                  </p>
                  <div className="w-full bg-primary/10 h-3 rounded-full overflow-hidden mt-2">
                    <div
                      className={`h-full ${
                        currentMoment.scores.risk > 50
                          ? "bg-red-500"
                          : currentMoment.scores.risk > 30
                          ? "bg-accent-gold"
                          : "bg-green-500"
                      }`}
                      style={{ width: `${currentMoment.scores.risk}%` }}
                    />
                  </div>
                  <p className="text-slate-400 text-sm font-medium mt-1 italic">
                    {currentMoment.risk_notes.length > 0 ? currentMoment.risk_notes[0] : "No risk factors identified"}
                  </p>
                </div>
              </div>

              {/* Main Decision Card */}
              <div className="bg-card-dark rounded-xl border-2 border-primary overflow-hidden shadow-2xl">
                <div className="bg-primary px-6 py-2 flex justify-between items-center">
                  <span className="text-white text-xs font-black uppercase tracking-[0.2em]">
                    Priority Alpha: Immediate Action
                  </span>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-white animate-pulse"></div>
                    <span className="text-white text-xs font-bold">MOMENT {currentIndex + 1}/{moments.length}</span>
                  </div>
                </div>

                <div className="flex flex-col lg:flex-row">
                  {/* Media Preview */}
                  <div className="w-full lg:w-3/5 p-6 border-b lg:border-b-0 lg:border-r border-primary/10">
                    <div className="relative w-full aspect-video rounded-lg overflow-hidden bg-black group">
                      {currentMoment.clip_url ? (
                        <>
                          <video
                            controls
                            className="w-full h-full"
                            src={getFullClipUrl(currentMoment.clip_url)}
                          />
                          <div className="absolute bottom-4 left-4 flex items-center gap-3">
                            <div className="bg-primary px-2 py-1 rounded text-[10px] font-bold text-white">
                              {currentMoment.moment_type.toUpperCase()}
                            </div>
                            <div className="text-white text-sm font-mono bg-black/50 px-2 py-1 rounded">
                              {Math.floor(currentMoment.tr - currentMoment.t0)}s
                            </div>
                          </div>
                        </>
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <span className="text-white/20">NO CLIP AVAILABLE</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Content Info & Decision */}
                  <div className="w-full lg:w-2/5 p-8 flex flex-col">
                    <div className="flex-1">
                      <p className="text-primary text-xs font-black uppercase tracking-widest mb-2">
                        Internal Review Note
                      </p>
                      <h3 className="text-white text-2xl font-bold leading-tight mb-4 tracking-tight">
                        {currentMoment.summary}
                      </h3>

                      <div className="space-y-6">
                        <div>
                          <h4 className="text-slate-400 text-[10px] uppercase font-black tracking-widest mb-2">
                            Why It Matters
                          </h4>
                          <ul className="space-y-2">
                            {currentMoment.why_it_matters.map((reason, i) => (
                              <li key={i} className="flex items-start gap-2 text-sm text-slate-200">
                                <span className="text-green-500 text-sm mt-0.5">✓</span>
                                {reason}
                              </li>
                            ))}
                          </ul>
                        </div>

                        {currentMoment.risk_notes.length > 0 && (
                          <div>
                            <h4 className="text-slate-400 text-[10px] uppercase font-black tracking-widest mb-2">
                              Risk Notes
                            </h4>
                            <ul className="space-y-2">
                              {currentMoment.risk_notes.map((note, i) => (
                                <li key={i} className="flex items-start gap-2 text-sm text-slate-200">
                                  <span className="text-primary text-sm mt-0.5">⚠</span>
                                  {note}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Post Copy Preview */}
                        <div>
                          <h4 className="text-slate-400 text-[10px] uppercase font-black tracking-widest mb-2">
                            Post Copy (Hype Variant)
                          </h4>
                          <p className="text-sm text-slate-300 italic bg-white/5 p-3 rounded border-l-2 border-primary">
                            "{currentMoment.post_copy.hype}"
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="mt-8 flex flex-col gap-3">
                      <button
                        onClick={handleApprove}
                        disabled={isSubmitting || currentMoment.approval_status === "approved"}
                        className="w-full h-14 bg-primary text-white text-lg font-black uppercase tracking-widest rounded-lg shadow-xl shadow-primary/30 hover:brightness-110 transition-all flex items-center justify-center gap-2 border-b-4 border-black/20 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {currentMoment.approval_status === "approved" ? (
                          <>✅ APPROVED</>
                        ) : (
                          <>
                            🚀 {isSubmitting ? "APPROVING..." : "APPROVE & POST"}
                          </>
                        )}
                      </button>
                      <button
                        onClick={handleHold}
                        disabled={isSubmitting || currentMoment.approval_status === "held"}
                        className="w-full h-12 bg-white/10 text-white text-sm font-bold uppercase tracking-widest rounded-lg hover:bg-white/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {currentMoment.approval_status === "held" ? "⏸️ ON HOLD" : "HOLD CONTENT"}
                      </button>
                    </div>

                    {/* Navigation */}
                    {moments.length > 1 && (
                      <div className="mt-4 flex gap-2">
                        <button
                          onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
                          disabled={currentIndex === 0}
                          className="flex-1 px-4 py-2 bg-white/5 text-white text-xs font-bold rounded hover:bg-white/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                          ← PREV
                        </button>
                        <button
                          onClick={() => setCurrentIndex(Math.min(moments.length - 1, currentIndex + 1))}
                          disabled={currentIndex === moments.length - 1}
                          className="flex-1 px-4 py-2 bg-white/5 text-white text-xs font-bold rounded hover:bg-white/10 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                          NEXT →
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Footer Stats */}
              <footer className="mt-4 flex flex-wrap items-center justify-between px-6 py-4 bg-card-dark border border-primary/20 rounded-xl">
                <div className="flex gap-8">
                  <div className="flex flex-col">
                    <span className="text-[10px] font-black uppercase text-slate-400">Decisions Made</span>
                    <span className="text-lg font-bold text-primary italic">
                      {moments.filter((m) => m.approval_status !== "pending").length}/{moments.length}
                    </span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[10px] font-black uppercase text-slate-400">Approved</span>
                    <span className="text-lg font-bold text-green-500">
                      {moments.filter((m) => m.approval_status === "approved").length}
                    </span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[10px] font-black uppercase text-slate-400">On Hold</span>
                    <span className="text-lg font-bold text-yellow-500">
                      {moments.filter((m) => m.approval_status === "held").length}
                    </span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-[10px] font-black uppercase text-slate-400">Stream Health</span>
                    <span className="text-lg font-bold text-green-500">Nominal</span>
                  </div>
                </div>
                <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                  System v1.0.0 // Executive Portal
                </div>
              </footer>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
