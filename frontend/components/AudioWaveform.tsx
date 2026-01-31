"use client";

import { useEffect, useState } from "react";

interface AudioWaveformProps {
  audioLevel?: number; // 0-1 normalized audio RMS
  className?: string;
}

export default function AudioWaveform({ audioLevel = 0.5, className = "" }: AudioWaveformProps) {
  const [bars, setBars] = useState<number[]>(Array(20).fill(0.3));

  useEffect(() => {
    // Animate bars based on audio level
    const interval = setInterval(() => {
      setBars((prev) => {
        const newBars = prev.map((_, i) => {
          // Simulate waveform with some randomness around the audio level
          const variation = (Math.random() - 0.5) * 0.4;
          return Math.max(0.1, Math.min(1, audioLevel + variation));
        });
        return newBars;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [audioLevel]);

  return (
    <div className={`flex items-end gap-1 h-12 ${className}`}>
      {bars.map((height, i) => (
        <div
          key={i}
          className={`w-1 rounded-t transition-all duration-100 ${
            height > 0.8
              ? "bg-white"
              : height > 0.6
              ? "bg-primary"
              : height > 0.4
              ? "bg-primary/80"
              : height > 0.2
              ? "bg-primary/60"
              : "bg-primary/40"
          }`}
          style={{ height: `${height * 100}%` }}
        />
      ))}
    </div>
  );
}
