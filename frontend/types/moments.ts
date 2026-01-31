// Data contracts from the spec

export interface CandidateEvent {
  type: "candidate.created";
  candidate_id: string;
  t0: number; // timestamp in seconds
  signals: {
    motion: number;
    audio_rms: number;
    fan_buzz: number;
  };
}

export interface ClipRecipe {
  label: "reaction_lead" | "play" | "reaction_button";
  start_s: number;
  end_s: number;
}

export interface MomentAnalysis {
  type: "moment.ready";
  moment_id: string;
  t0: number; // play moment time
  tr: number; // reaction peak time
  moment_type: "goal" | "touchdown" | "ace" | "dunk" | "save" | "rally" | "winner" | "other";
  summary: string;
  why_it_matters: string[];
  scores: {
    hype: number; // 0-100
    risk: number; // 0-100
  };
  risk_notes: string[];
  clip_recipe: ClipRecipe[];
  post_copy: {
    hype: string;
    neutral: string;
    brand_safe: string;
  };
  clip_url?: string; // URL to the generated clip
  share_card_url?: string; // URL to the share card image
  approval_status?: "pending" | "approved" | "held";
}

export interface ApprovalEvent {
  type: "moment.approved" | "moment.held";
  moment_id: string;
  by: "exec" | "producer" | "social";
  at: number; // timestamp
}

export type WarRoomEvent = CandidateEvent | MomentAnalysis | ApprovalEvent;
