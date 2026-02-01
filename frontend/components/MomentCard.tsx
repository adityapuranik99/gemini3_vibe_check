"use client";

import { MomentAnalysis } from "@/types/moments";
import { getFullClipUrl, api } from "@/lib/vibecheck-api";
import { useState, useRef } from "react";

const THEMES = ["stadium", "cyberpunk", "retro", "neon"];

interface MomentCardProps {
  moment: MomentAnalysis;
  role: "producer" | "social" | "exec";
}

export default function MomentCard({ moment, role }: MomentCardProps) {
  const [status, setStatus] = useState(moment.approval_status || "pending");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedTheme, setSelectedTheme] = useState("stadium");
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [shareCardUrl, setShareCardUrl] = useState(moment.share_card_url);
  const [isVideoLoading, setIsVideoLoading] = useState(true);
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleApprove = async () => {
    setIsSubmitting(true);
    try {
      await api.approveMoment({
        type: "moment.approved",
        moment_id: moment.moment_id,
        by: role,
        at: Date.now() / 1000,
      });
      setStatus("approved");
      console.log(`✅ Approved moment ${moment.moment_id}`);
    } catch (error) {
      console.error("Failed to approve moment:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleHold = async () => {
    setIsSubmitting(true);
    try {
      await api.approveMoment({
        type: "moment.held",
        moment_id: moment.moment_id,
        by: role,
        at: Date.now() / 1000,
      });
      setStatus("held");
      console.log(`⏸️  Held moment ${moment.moment_id}`);
    } catch (error) {
      console.error("Failed to hold moment:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRegenerate = async () => {
    setIsRegenerating(true);
    try {
      const response = await fetch(`${api.baseUrl}/api/moments/${moment.moment_id}/regenerate_share_card?theme_name=${selectedTheme}`, {
        method: "POST",
      });
      if (!response.ok) throw new Error("Failed to regenerate");
      const data = await response.json();
      setShareCardUrl(data.moment.share_card_url);
    } catch (error) {
      console.error("Regeneration failed:", error);
    } finally {
      setIsRegenerating(false);
    }
  };

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-800 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="px-3 py-1 bg-blue-600 rounded-full text-sm font-semibold">
            {moment.moment_type.toUpperCase()}
          </span>
          <span className="text-gray-400 text-sm">ID: {moment.moment_id}</span>
        </div>
        <div className="flex gap-3">
          <div className="text-center">
            <div className="text-xs text-gray-400">HYPE</div>
            <div className={`text-lg font-bold ${moment.scores.hype > 70 ? "text-green-400" : "text-yellow-400"}`}>
              {moment.scores.hype}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-400">RISK</div>
            <div className={`text-lg font-bold ${moment.scores.risk > 50 ? "text-red-400" : "text-green-400"}`}>
              {moment.scores.risk}
            </div>
          </div>
        </div>
      </div>

      {/* Video Player */}
      <div className="bg-black aspect-video flex items-center justify-center relative">
        {moment.clip_url ? (
          <>
            {isVideoLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
                <div className="text-gray-400">
                  <svg className="w-10 h-10 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                </div>
              </div>
            )}
            <video
              ref={videoRef}
              controls
              preload="metadata"
              className="w-full h-full"
              src={getFullClipUrl(moment.clip_url)}
              onLoadedData={() => setIsVideoLoading(false)}
              onWaiting={() => setIsVideoLoading(true)}
              onPlaying={() => setIsVideoLoading(false)}
            >
              Your browser does not support video playback.
            </video>
          </>
        ) : (
          <div className="text-gray-500">
            <svg className="w-16 h-16 mx-auto mb-2" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" />
            </svg>
            <p className="text-sm">Clip being generated...</p>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-6 space-y-4">
        <div>
          <h3 className="text-xl font-semibold mb-2">{moment.summary}</h3>
        </div>

        {role === "producer" && (
          <>
            <div>
              <h4 className="text-sm font-semibold text-gray-400 mb-2">Why It Matters</h4>
              <ul className="space-y-1">
                {moment.why_it_matters.map((reason, idx) => (
                  <li key={idx} className="text-gray-300 text-sm flex items-start">
                    <span className="text-blue-400 mr-2">•</span>
                    {reason}
                  </li>
                ))}
              </ul>
            </div>

            {moment.risk_notes.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-orange-400 mb-2">Risk Notes</h4>
                <ul className="space-y-1">
                  {moment.risk_notes.map((note, idx) => (
                    <li key={idx} className="text-gray-300 text-sm flex items-start">
                      <span className="text-orange-400 mr-2">⚠</span>
                      {note}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div>
              <h4 className="text-sm font-semibold text-gray-400 mb-2">Clip Recipe</h4>
              <div className="space-y-2">
                {moment.clip_recipe.map((segment, idx) => (
                  <div key={idx} className="flex items-center gap-3 text-sm bg-gray-800 p-2 rounded">
                    <span className="font-mono text-blue-400">{segment.label}</span>
                    <span className="text-gray-400">
                      {segment.start_s.toFixed(1)}s → {segment.end_s.toFixed(1)}s
                    </span>
                    <span className="text-gray-500">
                      ({(segment.end_s - segment.start_s).toFixed(1)}s)
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

      </div>

      {/* Social Share Card Section */}
      <div className="border-t border-gray-800 pt-4 mt-2">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-sm font-semibold text-gray-400">Social Share Assets</h4>
          <div className="flex items-center gap-2">
            <select
              value={selectedTheme}
              onChange={(e) => setSelectedTheme(e.target.value)}
              className="bg-gray-800 text-xs rounded border border-gray-700 px-2 py-1 outline-none"
            >
              {THEMES.map(t => (
                <option key={t} value={t}>{t.toUpperCase()}</option>
              ))}
            </select>
            <button
              onClick={handleRegenerate}
              disabled={isRegenerating}
              className="text-xs bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 px-2 py-1 rounded transition-colors"
            >
              {isRegenerating ? "..." : "Regen"}
            </button>
          </div>
        </div>

        {shareCardUrl ? (
          <div className="space-y-3">
            <div className="relative group rounded-lg overflow-hidden border border-gray-700 bg-black aspect-[1200/630]">
              <img
                src={getFullClipUrl(shareCardUrl)}
                alt="Share card"
                className="w-full h-full object-cover"
                loading="eager"
              />
              <div className="absolute top-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <a
                  href={getFullClipUrl(shareCardUrl)}
                  download={`${moment.moment_id}_card.png`}
                  className="bg-black/60 hover:bg-black p-2 rounded-full"
                  title="Download"
                >
                  📸
                </a>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-gray-800/50 rounded-lg p-8 text-center">
            <p className="text-sm text-gray-500">Generating assets...</p>
          </div>
        )}
      </div>

      {/* Actions */}
      {role === "exec" && (
        <div className="flex gap-3 pt-4">
          {status === "approved" ? (
            <div className="flex-1 bg-green-600/20 border border-green-500 text-green-400 font-semibold py-3 rounded-lg text-center">
              ✅ Approved
            </div>
          ) : status === "held" ? (
            <div className="flex-1 bg-yellow-600/20 border border-yellow-500 text-yellow-400 font-semibold py-3 rounded-lg text-center">
              ⏸️ On Hold
            </div>
          ) : (
            <>
              <button
                onClick={handleApprove}
                disabled={isSubmitting}
                className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-lg transition-colors"
              >
                {isSubmitting ? "..." : "Approve"}
              </button>
              <button
                onClick={handleHold}
                disabled={isSubmitting}
                className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-lg transition-colors"
              >
                {isSubmitting ? "..." : "Hold"}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
