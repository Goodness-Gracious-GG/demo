# AI Code Analyzer - Professor Mode Backend

A FastAPI backend that analyzes code using the Gemini API with a professor mode approach - guiding students through questions rather than just giving answers.

## Features

- **Professor Mode**: Analyzes code through guided questioning
- **3-Phase Analysis**:
  1. Code Understanding
  2. Observations (issues identified)
  3. Socratic Questions (to guide learning)
  4. Suggestions (improvements)

## API Endpoints

### `GET /`
Root endpoint returning API info.

### `POST /analyze`
Analyze code with the professor mode.

**Request Body:**
```json
{
  "code": "def find_max(arr):\\n    max = 0\\n    for i in arr:\\n        if i > max:\\n            max = i\\n    return max",
  "language": "python"
}
```

**Response:**
```json
{
  "understanding": "The code finds the maximum value in an array...",
  "observations": ["Issue 1", "Issue 2"],
  "questions": ["Question 1", "Question 2"],
  "suggestions": ["Suggestion 1", "Suggestion 2"]
}
```

## Setup

1. Install dependencies:
```bash
# On macOS/Linux
pip3 install -r requirements.txt

# Or if you have Python 3 with pip
python3 -m pip install -r requirements.txt
```

2. Set your Gemini API key in `.env`:
```
GEMINI_API_KEY=your_api_key_here
```
   - Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

3. Run the server:
```bash
# On macOS/Linux
uvicorn main:app --reload

# Or using python3
python3 -m uvicorn main:app --reload
```

## Important Notes

### Regional Availability
The Gemini API is not available in all countries. If you get an error `"User location is not supported for the API use"`, you need to:
- Use a VPN connected to a supported country (e.g., US, UK, etc.)
- Or use Google Cloud Vertex AI which may have different regional availability

### Quota Limits
The free tier has rate limits. If you get `RESOURCE_EXHAUSTED` errors:
- Check your quota at https://ai.google.dev/gemini-api/docs/rate-limits
- Free tier quotas reset daily (usually at midnight PST)
- For higher quotas, add billing to your Google Cloud project
- The app uses `gemini-2.5-flash-lite` model which has the most generous free tier

### Model Selection
The app uses `gemini-2.5-flash-lite` by default, which:
- Is currently the most available model
- Has good performance for code analysis
- Supports the free tier (subject to quotas)

### Troubleshooting 500 Errors
Common causes of 500 errors:
1. **Invalid API key**: Ensure your API key is correct in `.env`
2. **Quota exceeded**: Wait for quota reset or add billing
3. **Regional restriction**: Use VPN if in unsupported region
4. **Model unavailable**: The app automatically uses available models

## Tech Stack

- **FastAPI** - Web framework
- **Google Gemini API** (via `google-genai` package) - AI model for code analysis
- **Pydantic** - Data validation
- **python-dotenv** - Environment variable management