"""Prompt templates for Gemini moment analysis."""

MOMENT_ANALYSIS_PROMPT = """You are analyzing a sports moment from a live broadcast. Your job is to understand what happened, assess its significance, and package it for social media posting.

CRITICAL: You MUST respond with valid JSON matching EXACTLY this schema. Do NOT deviate from the field names or values.

**Required JSON Schema:**
```json
{
  "moment_type": "<ONE OF: goal, touchdown, ace, dunk, save, rally, winner, other>",
  "summary": "<One sentence describing what happened>",
  "why_it_matters": ["<reason 1>", "<reason 2>"],
  "scores": {
    "hype": <integer 0-100>,
    "risk": <integer 0-100>
  },
  "risk_notes": ["<note 1 if any>"],
  "clip_recipe": [
    {"label": "play", "start_s": <float>, "end_s": <float>},
    {"label": "reaction_lead", "start_s": <float>, "end_s": <float>},
    {"label": "reaction_button", "start_s": <float>, "end_s": <float>}
  ],
  "post_copy": {
    "hype": "<energetic copy under 200 chars with emojis>",
    "neutral": "<factual copy>",
    "brand_safe": "<cautious copy>"
  }
}
```

**IMPORTANT RULES:**
1. moment_type MUST be exactly one of: "goal", "touchdown", "ace", "dunk", "save", "rally", "winner", "other"
2. clip_recipe label MUST be exactly one of: "reaction_lead", "play", "reaction_button"
3. clip_recipe uses "start_s" and "end_s" (NOT "start" or "end")
4. All timestamps are in seconds as floats (e.g., 12.5, not "12.5s")
5. scores.hype and scores.risk MUST be integers 0-100

**Context:**
- The play moment happens around timestamp t0
- The crowd/fan reaction peaks later around timestamp tr
- We want to capture BOTH the play and the reaction for maximum impact

**Scoring Guidelines:**
- Hype: 90+ = viral-worthy; 70-89 = very exciting; 50-69 = notable; <50 = routine
- Risk: 70+ = high controversy/injury; 40-69 = moderate caution; <40 = safe to post

Be decisive and confident. This is time-sensitive content.
"""


def build_analysis_prompt(
    candidate_id: str,
    t0: float,
    tr_estimate: float,
    motion_score: float,
    audio_rms: float,
    sport_type: str = "unknown",
) -> str:
    """
    Build a context-specific prompt for Gemini analysis.

    Args:
        candidate_id: Candidate ID from detection
        t0: Play moment timestamp
        tr_estimate: Estimated reaction peak timestamp
        motion_score: Motion intensity score (0-1)
        audio_rms: Audio RMS level (0-1)
        sport_type: Type of sport (football, basketball, tennis, etc.)

    Returns:
        Formatted prompt string
    """
    return f"""
{MOMENT_ANALYSIS_PROMPT}

**Moment Context:**
- Candidate ID: {candidate_id}
- Play timestamp (t0): {t0:.2f}s
- Estimated reaction peak (tr): {tr_estimate:.2f}s
- Motion intensity: {motion_score:.2f} (0=low, 1=high)
- Audio energy: {audio_rms:.2f} (0=quiet, 1=loud)
- Sport type: {sport_type}

Based on this data, analyze the moment and provide your structured response.
"""


def get_example_moment_json() -> dict:
    """Get an example of the expected JSON structure for documentation."""
    return {
        "moment_type": "touchdown",
        "summary": "Wilson throws a 45-yard touchdown pass to Metcalf in the red zone",
        "why_it_matters": [
            "Ties the game with 2 minutes remaining",
            "Metcalf's first TD of the season",
            "Wilson under pressure, scrambled right before the throw"
        ],
        "scores": {
            "hype": 87,
            "risk": 22
        },
        "risk_notes": [
            "Opposing team fans may react negatively"
        ],
        "clip_recipe": [
            {
                "label": "reaction_lead",
                "start_s": 543.8,
                "end_s": 549.8
            },
            {
                "label": "play",
                "start_s": 517.2,
                "end_s": 527.2
            },
            {
                "label": "reaction_button",
                "start_s": 549.8,
                "end_s": 553.8
            }
        ],
        "post_copy": {
            "hype": "🔥 WILSON TO METCALF FOR THE TD! 45 YARDS OF PURE MAGIC! #GameTied",
            "neutral": "Wilson connects with Metcalf for a 45-yard touchdown. Game tied with 2:00 remaining.",
            "brand_safe": "What a throw by Wilson! Metcalf hauls it in for the score. We're tied up!"
        }
    }
