"use client";

import { MomentAnalysis } from "@/types/moments";
import { getFullClipUrl, api } from "@/lib/api";
import { useState } from "react";

interface MomentCardProps {
  moment: MomentAnalysis;
  role: "producer" | "social" | "exec";
}

export default function MomentCard({ moment, role }: MomentCardProps) {
  const [status, setStatus] = useState(moment.approval_status || "pending");
  const [isSubmitting, setIsSubmitting] = useState(false);

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
      <div className="bg-black aspect-video flex items-center justify-center">
        {moment.clip_url ? (
          <video
            controls
            className="w-full h-full"
            src={getFullClipUrl(moment.clip_url)}
          >
            Your browser does not support video playback.
          </video>
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

        <div>
          <h4 className="text-sm font-semibold text-gray-400 mb-2">Post Copy Variants</h4>
          <div className="space-y-3">
            <div className="bg-gray-800 p-3 rounded">
              <div className="text-xs text-gray-400 mb-1">HYPE</div>
              <p className="text-sm">{moment.post_copy.hype}</p>
            </div>
            <div className="bg-gray-800 p-3 rounded">
              <div className="text-xs text-gray-400 mb-1">NEUTRAL</div>
              <p className="text-sm">{moment.post_copy.neutral}</p>
            </div>
            <div className="bg-gray-800 p-3 rounded">
              <div className="text-xs text-gray-400 mb-1">BRAND SAFE</div>
              <p className="text-sm">{moment.post_copy.brand_safe}</p>
            </div>
          </div>
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
    </div>
  );
}
