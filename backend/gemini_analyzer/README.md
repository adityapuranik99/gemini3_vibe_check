# Gemini 3 Analyzer

Stage B intelligence for Vibe Check - analyzes sports moments using Google's Gemini 3 model.

## Features

- **Multimodal Understanding**: Analyzes video frames + audio context
- **Structured Outputs**: Returns JSON with strict schema validation
- **Moment Packaging**: Generates hype/risk scores, clip recipes, and post copy variants
- **Fallback Handling**: Graceful degradation when API unavailable

## Setup

1. Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

2. Add to your `.env` file:
```bash
GOOGLE_API_KEY=your_api_key_here
```

3. Test the analyzer:
```bash
cd backend
source venv/bin/activate
python test_gemini.py
```

## Usage

### Basic Analysis

```python
from gemini_analyzer import GeminiAnalyzer

# Initialize
analyzer = GeminiAnalyzer()

# Analyze a moment
moment = analyzer.analyze_moment(
    candidate_id="c_0001",
    t0=120.5,           # Play timestamp
    tr=135.2,           # Reaction timestamp
    frames=frame_list,  # List of (timestamp, frame) tuples
    motion_score=0.85,
    audio_rms=0.92,
    sport_type="football"
)

print(f"Hype: {moment.scores.hype}, Risk: {moment.scores.risk}")
print(f"Summary: {moment.summary}")
print(f"Post copy: {moment.post_copy.hype}")
```

### With Video File

```python
# Upload entire video file to Gemini
moment = analyzer.analyze_with_video_file(
    candidate_id="c_0001",
    t0=120.5,
    tr=135.2,
    video_path="/path/to/clip.mp4",
    motion_score=0.85,
    audio_rms=0.92,
)
```

## Output Structure

The analyzer returns a `MomentAnalysis` object with:

```python
{
    "moment_id": "m_0001",
    "t0": 120.5,                    # Play timestamp
    "tr": 135.2,                    # Reaction timestamp
    "moment_type": "touchdown",     # goal, ace, dunk, save, etc.
    "summary": "Wilson to Metcalf 45-yard TD",
    "why_it_matters": [
        "Ties the game with 2:00 remaining",
        "Metcalf's first TD of the season"
    ],
    "scores": {
        "hype": 87,                 # 0-100
        "risk": 22                  # 0-100
    },
    "risk_notes": [
        "Opposing team fans may react negatively"
    ],
    "clip_recipe": [
        {"label": "reaction_lead", "start_s": 133.0, "end_s": 139.0},
        {"label": "play", "start_s": 115.0, "end_s": 125.0},
        {"label": "reaction_button", "start_s": 139.0, "end_s": 143.0}
    ],
    "post_copy": {
        "hype": "🔥 WILSON TO METCALF FOR THE TD!",
        "neutral": "Wilson connects with Metcalf for 45-yard TD",
        "brand_safe": "What a throw! Metcalf scores."
    }
}
```

## Scoring Guidelines

### Hype Score (0-100)
- **90-100**: Game-changing, viral-worthy moment
- **70-89**: Very exciting, high engagement potential
- **50-69**: Notable moment, worth posting
- **<50**: Routine play, low priority

### Risk Score (0-100)
- **70-100**: High controversy, injury, or sensitive content
- **40-69**: Moderate caution needed
- **<40**: Safe to post immediately

## Prompt Engineering

The analyzer uses a carefully crafted prompt (see [prompts.py](prompts.py)) that:
- Explains the two-stage detection system (t0 play, tr reaction)
- Provides context about delayed crowd reactions
- Requests structured JSON output
- Includes scoring rubrics and guidelines

You can customize prompts by modifying `prompts.py`.

## Model Selection

Currently using **Gemini 3 Flash** for:
- Low latency (~2-3 seconds per analysis)
- Cost efficiency
- Good balance of quality and speed

For production, consider:
- **Gemini 3 Pro**: Higher quality, slower, more expensive
- **Thinking level**: Adjust `thinking_level` for quality/speed tradeoff

## Troubleshooting

### "GOOGLE_API_KEY not found"
Add your API key to `backend/.env`

### "Model not available"
Check if `gemini-3-flash-001` is available in your region. Update `model_name` in `analyzer.py` if needed.

### API Rate Limiting
Gemini Flash has generous limits, but if you hit them:
- Add retry logic with exponential backoff
- Use `thinking_level` to reduce token usage
- Cache analysis results

## Performance

Typical analysis times:
- Keyframe analysis (4 frames): ~2-3 seconds
- Video file upload + analysis: ~5-10 seconds
- Fallback mode: <100ms

## Integration

The analyzer is integrated into the full pipeline via [pipeline.py](../pipeline.py):

```
Video → Ingestion → Feature Extraction → Candidate Detection
                                              ↓
                                         Gemini Analyzer
                                              ↓
                                          Moment Ready!
```

See [main.py](../main.py) for API endpoints.
