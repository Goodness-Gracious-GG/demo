import os
import re
from google import genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

load_dotenv()

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")
client = genai.Client(api_key=api_key)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Code Twins",
    description="Backend API for analyzing code with guided questioning",
    version="1.0.0"
)

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class CodeAnalysisRequest(BaseModel):
    code: str
    language: str = "python"

# Response model
class CodeAnalysisResponse(BaseModel):
    understanding: str
    observations: list[str]
    questions: list[str]
    suggestions: list[str]

# Professor Mode System Prompt
PROFESSOR_MODE_PROMPT = """
You are an expert programming professor and code reviewer.

Your role is to help students deeply understand their code through guided questioning, not by immediately giving answers.

When a user submits code, respond in 3 phases:

### PHASE 1 — OBSERVATIONS
- Briefly describe what the code is doing
- Point out potential issues (without solving them yet)

### PHASE 2 — SOCRATIC QUESTIONS (MOST IMPORTANT)
- Ask 3-6 thoughtful questions
- Questions should challenge assumptions, highlight edge cases, encourage better design
- DO NOT give answers yet

### PHASE 3 — GUIDED SUGGESTIONS
- Only AFTER questions
- Provide improvements and best practices
- Show corrected code ONLY if necessary

Format your response exactly as:

### 🧠 Code Understanding
(Short explanation of what the code does)

### ⚠️ Observations
- Issue 1
- Issue 2
- Issue 3

### ❓ Questions (Think Before You Code)
- Question 1
- Question 2
- Question 3

### 💡 Suggestions
- Improvement 1
- Improvement 2
"""

@app.get("/")
async def root():
    return {"message": "Code Twins", "version": "1.0.0"}

@app.post("/analyze", response_model=CodeAnalysisResponse)
async def analyze_code(request: CodeAnalysisRequest):
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    
    try:
        logger.info(f"Analyzing {request.language} code of length: {len(request.code)}")
        
        # For the new google.genai API, we construct the contents differently
        prompt = f"""
{PROFESSOR_MODE_PROMPT}

Analyze this {request.language} code:

```
{request.code}
"""
        
        logger.info("Sending request to Gemini API...")
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config={
                "http_options": {
                    "timeout": 30000  # 30 second timeout
                }
            }
        )
        analysis_text = response.text
        logger.info(f"Received response from Gemini API: {analysis_text[:100]}...")
        
        return parse_analysis_response(analysis_text)
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error during analysis: {error_message}", exc_info=True)
        
        # Provide user-friendly error messages
        if "User location is not supported" in error_message:
            detail = "Gemini API is not available in your region. Please use a VPN connected to a supported country (e.g., US, UK) or use Google Cloud Vertex AI."
        elif "API key not valid" in error_message or "invalid api key" in error_message.lower() or "API_KEY_INVALID" in error_message:
            detail = "Invalid Gemini API key. Please check your API key in the .env file and ensure it's correctly formatted."
        elif "leaked" in error_message.lower() or "reported as leaked" in error_message.lower():
            detail = "Your API key has been flagged as leaked. Please generate a new API key at https://aistudio.google.com/app/apikey and update the .env file."
        elif "quota" in error_message.lower() or "RESOURCE_EXHAUSTED" in error_message:
             # Extract retry delay if available
             retry_match = re.search(r'retry in ([\d.]+)s', error_message)
             if retry_match:
                 retry_seconds = float(retry_match.group(1))
                 detail = f"API quota exceeded. Please wait {retry_seconds:.0f} seconds before trying again. The free tier allows 20 requests per day per model. Consider adding billing to your Google Cloud project for higher quotas."
             else:
                 detail = "API quota exceeded. The free tier quota for this project has been exhausted. Please: 1) Check https://ai.google.dev/gemini-api/docs/rate-limits 2) Add billing to your Google Cloud project 3) Wait for quota reset (usually daily) 4) Or use a different API key with available quota."
        elif "PERMISSION_DENIED" in error_message or "denied" in error_message.lower():
            detail = "Permission denied. Your API key may not have access to the Gemini API. Please check your Google Cloud project and API key permissions."
        elif "UNAVAILABLE" in error_message or "high demand" in error_message:
            detail = "The model is currently experiencing high demand. Please try again in a few minutes or use a different model."
        else:
            detail = f"Analysis failed: {error_message}"
        
        raise HTTPException(status_code=500, detail=detail)

def parse_analysis_response(text: str) -> CodeAnalysisResponse:
    """Parse the AI response into structured format."""
    sections = {
        "understanding": "",
        "observations": [],
        "questions": [],
        "suggestions": []
    }
    
    current_section = None
    
    for line in text.split("\n"):
        line = line.strip()
        
        if "### 🧠 Code Understanding" in line:
            current_section = "understanding"
        elif "### ⚠️ Observations" in line:
            current_section = "observations"
        elif "### ❓ Questions" in line:
            current_section = "questions"
        elif "### 💡 Suggestions" in line:
            current_section = "suggestions"
        elif line.startswith("- ") and current_section in ["observations", "questions", "suggestions"]:
            sections[current_section].append(line[2:])
        elif current_section == "understanding" and line and not line.startswith("###"):
            sections["understanding"] += line + " "
    
    return CodeAnalysisResponse(
        understanding=sections["understanding"].strip(),
        observations=sections["observations"],
        questions=sections["questions"],
        suggestions=sections["suggestions"]
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
