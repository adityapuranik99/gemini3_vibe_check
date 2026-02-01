"""Prompt templates for Gemini moment analysis."""

MOMENT_ANALYSIS_PROMPT = """You are a world-class sports social media copywriter analyzing a moment from a live broadcast. Your job is to understand what happened, assess its significance, and write ELECTRIC social media copy that gets engagement.

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
    "hype": "<MAX ENERGY! All caps moments, fire emojis, exclamation marks. Make fans FEEL IT. Under 200 chars>",
    "neutral": "<Still engaging but conversational. Use storytelling, 'Did you see that?' energy. Ask questions. Make people want to watch. Under 200 chars>",
    "brand_safe": "<Professional but NOT boring. Highlight the athleticism, the skill, the drama. Avoid generic phrases like 'Great play'. Under 200 chars>"
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

**POST COPY GUIDELINES - THIS IS CRITICAL:**
Write copy like a top sports social media manager, not a boring news anchor.

HYPE variant:
- ALL CAPS for emphasis, strategic emoji use 🔥💥
- Short punchy sentences. Build excitement.
- Make fans feel like they're watching it live

NEUTRAL variant:
- Still exciting but more conversational
- Use rhetorical questions: "Did you see that?", "How does he do it?"
- Paint a picture with words - help people visualize the play
- Can include 1-2 emojis tastefully

BRAND_SAFE variant:
- Professional but NEVER boring
- Focus on athleticism, skill, and drama
- Avoid generic phrases like "Great play", "Nice shot", "Good effort"
- Be specific about what made this moment special

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


PLAYER_IDENTIFICATION_PROMPT = """Analyze these keyframes from a sports broadcast and identify:

1. **Jersey number** - What jersey number is visible on the key player?
2. **Team identification** - What team colors, logos, or uniforms do you see?
3. **Sport type** - What sport is being played?

Respond with JSON in this format:
```json
{
  "jersey_number": "string or null",
  "team_colors": ["color1", "color2"],
  "team_logo": "description of logo if visible",
  "sport": "basketball|football|soccer|tennis|hockey|baseball|other"
}
```

Focus on the most prominent player in the action. Be specific about jersey numbers and team identifiers.
"""


def build_player_identification_prompt() -> str:
    """Build Phase 1 prompt for visual player identification."""
    return PLAYER_IDENTIFICATION_PROMPT


def build_search_grounding_prompt(visual_info: dict) -> str:
    """
    Build Phase 2 prompt for search-grounded player and match stats.

    Args:
        visual_info: Dict with jersey_number, team_colors, team_logo, sport

    Returns:
        Prompt string for search-grounded query
    """
    jersey = visual_info.get("jersey_number", "unknown")
    team_logo = visual_info.get("team_logo", "unknown")
    sport = visual_info.get("sport", "unknown")

    return f"""Based on visual analysis of a {sport} broadcast showing:
- Jersey number: {jersey}
- Team identifier: {team_logo}

Use Google Search to find:

1. **Player identification**:
   - Full name of the player wearing #{jersey}
   - Their team name
   - Their position

2. **Match context** (if this is from a recent/current game):
   - What teams are playing?
   - Current or final score
   - What quarter/period/inning?
   - Game date and venue
   - Any key statistics or highlights

Respond with JSON:
```json
{{
  "player_info": {{
    "name": "Player Full Name",
    "team": "Team Name",
    "jersey_number": "{jersey}",
    "position": "Position"
  }},
  "match_stats": {{
    "teams": ["Team A", "Team B"],
    "score": "score if available",
    "quarter_period": "quarter/period/inning",
    "game_date": "date if available",
    "venue": "venue if available",
    "key_stats": ["stat 1", "stat 2"]
  }}
}}
```

If you cannot find specific information, use null for individual fields. Use Google Search to get the most current information.
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
            "hype": "🔥 WILSON TO METCALF! 45 YARDS OF ABSOLUTE FILTH! THE STADIUM JUST EXPLODED! 💥🏈 #Seahawks",
            "neutral": "Did you just see that throw?! Wilson under pressure, rolls right, finds Metcalf streaking down the sideline. 45 yards. Game. Tied. 🎯",
            "brand_safe": "Russell Wilson threads the needle to DK Metcalf for a spectacular 45-yard touchdown. The kind of clutch play that defines championship quarterbacks."
        }
    }
