/**
 * API client for Vibe Check backend
 */

import { MomentAnalysis, ApprovalEvent, CandidateEvent } from "@/types/moments";

export class VibeCheckAPI {
  // Dynamic base URL - computed on each request
  private get baseUrl(): string {
    if (typeof window !== "undefined") {
      // In browser: use same hostname as frontend, port 8000
      return `http://${window.location.hostname}:8000`;
    }
    // Server-side fallback
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }

  constructor() {}

  /**
   * Get all detected moments
   */
  async getMoments(): Promise<MomentAnalysis[]> {
    const response = await fetch(`${this.baseUrl}/api/moments`);

    if (!response.ok) {
      throw new Error(`Failed to fetch moments: ${response.statusText}`);
    }

    const data = await response.json();
    return data.moments || [];
  }

  /**
   * Get a specific moment by ID
   */
  async getMoment(momentId: string): Promise<MomentAnalysis> {
    const response = await fetch(`${this.baseUrl}/api/moments/${momentId}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch moment: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Approve or hold a moment
   */
  async approveMoment(approval: ApprovalEvent): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/moments/approve`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(approval),
    });

    if (!response.ok) {
      throw new Error(`Failed to approve moment: ${response.statusText}`);
    }
  }

  /**
   * Upload a video file to the server
   */
  async uploadVideo(file: File): Promise<{ video_path: string; filename: string; size: number }> {
    const formData = new FormData();
    formData.append("video", file);

    const response = await fetch(`${this.baseUrl}/api/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Failed to upload video: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Start video ingestion
   */
  async startIngestion(videoPath: string, streamId: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/ingest/start`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        video_path: videoPath,
        stream_id: streamId,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to start ingestion: ${response.statusText}`);
    }
  }

  /**
   * Get all candidates
   */
  async getCandidates(): Promise<CandidateEvent[]> {
    const response = await fetch(`${this.baseUrl}/api/candidates`);

    if (!response.ok) {
      throw new Error(`Failed to fetch candidates: ${response.statusText}`);
    }

    const data = await response.json();
    return data.candidates || [];
  }

  /**
   * Get clip URL for a moment
   */
  getClipUrl(clipFilename: string): string {
    return `${this.baseUrl}/api/clips/${clipFilename}`;
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/`);
      return response.ok;
    } catch {
      return false;
    }
  }
}

// Singleton instance
export const api = new VibeCheckAPI();

// Helper to get clip URL with correct host
export const getFullClipUrl = (clipPath: string): string => {
  if (typeof window !== "undefined") {
    return `http://${window.location.hostname}:8000${clipPath}`;
  }
  return `http://localhost:8000${clipPath}`;
};
