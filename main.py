import os
import re
from google import genai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

# Import Supabase client
from supabase_client import (
    supabase,
    get_current_user,
    get_current_user_id,
    sign_up,
    sign_in,
    sign_out,
    reset_password,
    get_session,
    refresh_session,
    create_conversation,
    get_conversation,
    get_user_conversations,
    update_conversation,
    delete_conversation,
    add_message_to_conversation,
    is_authenticated
)

load_dotenv()

print("DEBUG GEMINI KEY:", os.getenv("GEMINI_API_KEY"))

# Configure Gemini API
def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY")
    return genai.Client(api_key=api_key)

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

# ============================================================
# AUTHENTICATION MODELS
# ============================================================

class SignUpRequest(BaseModel):
    email: str
    password: str
    data: Optional[Dict[str, Any]] = None

class SignInRequest(BaseModel):
    email: str
    password: str

class SignInResponse(BaseModel):
    user: Dict[str, Any]
    session: Dict[str, Any]

class SignOutResponse(BaseModel):
    message: str

class ResetPasswordRequest(BaseModel):
    email: str

class ResetPasswordResponse(BaseModel):
    message: str

class SessionResponse(BaseModel):
    session: Optional[Dict[str, Any]]
    user: Optional[Dict[str, Any]]

class RefreshSessionResponse(BaseModel):
    session: Dict[str, Any]

# ============================================================
# CONVERSATION MODELS
# ============================================================

class ConversationCreateRequest(BaseModel):
    messages: List[Dict[str, Any]]
    title: Optional[str] = None

class ConversationUpdateRequest(BaseModel):
    messages: Optional[List[Dict[str, Any]]] = None
    title: Optional[str] = None

class ConversationResponse(BaseModel):
    id: str
    user_id: str
    messages: List[Dict[str, Any]]
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

class ConversationListResponse(BaseModel):
    conversations: List[ConversationResponse]
    total: int

class MessageAppendRequest(BaseModel):
    message: Dict[str, Any]

# ============================================================
# AUTHENTICATION DEPENDENCY
# ============================================================

def get_current_user_id_from_header(
    authorization: Optional[str] = Header(None)
) -> Optional[str]:
    """
    Extract user ID from Supabase JWT in Authorization header.
    Header format: "Bearer <jwt_token>"
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    try:
        # Set the auth header for supabase client
        supabase.auth.set_session(token)
        user = get_current_user()
        return user.id if user else None
    except Exception:
        return None

# ============================================================
# PROFESSOR MODE SYSTEM PROMPT
# ============================================================
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


@app.get("/config")
async def get_config():
    return {
        "supabaseUrl": os.getenv("SUPABASE_URL"),
        "supabaseAnonKey": os.getenv("SUPABASE_ANON_KEY")
    }


# ============================================================
# AUTHENTICATION ENDPOINTS
# ============================================================

@app.post("/auth/signup", response_model=SignInResponse)
async def signup(request: SignUpRequest):
    """
    Register a new user.
    
    Creates a new user account and returns the user and session.
    """
    try:
        result = sign_up(
            email=request.email,
            password=request.password,
            options={"data": request.data} if request.data else None
        )
        return SignInResponse(
            user=result["user"],
            session=result["session"]
        )
    except Exception as e:
        logger.error(f"Signup error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Signup failed: {str(e)}"
        )


@app.post("/auth/signin", response_model=SignInResponse)
async def signin(request: SignInRequest):
    """
    Sign in a user with email and password.
    
    Returns the user and session on successful authentication.
    """
    try:
        result = sign_in(
            email=request.email,
            password=request.password
        )
        return SignInResponse(
            user=result["user"],
            session=result["session"]
        )
    except Exception as e:
        logger.error(f"Signin error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=401,
            detail=f"Invalid email or password"
        )


@app.post("/auth/signout", response_model=SignOutResponse)
async def signout():
    """
    Sign out the current user.
    
    Invalidates the current session.
    """
    try:
        sign_out()
        return SignOutResponse(message="Signed out successfully")
    except Exception as e:
        logger.error(f"Signout error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Signout failed: {str(e)}"
        )


@app.post("/auth/reset-password", response_model=ResetPasswordResponse)
async def reset_password_endpoint(request: ResetPasswordRequest):
    """
    Send a password reset email to the user.
    """
    try:
        reset_password(request.email)
        return ResetPasswordResponse(
            message="Password reset email sent"
        )
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Reset password failed: {str(e)}"
        )


@app.get("/auth/session", response_model=SessionResponse)
async def get_session_endpoint():
    """
    Get the current session.
    
    Returns the current session and user if authenticated.
    """
    try:
        session_data = get_session()
        user = get_current_user()
        return SessionResponse(
            session=session_data,
            user=user
        )
    except Exception as e:
        logger.error(f"Get session error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session: {str(e)}"
        )


@app.post("/auth/refresh", response_model=RefreshSessionResponse)
async def refresh_session_endpoint():
    """
    Refresh the current session.
    
    Extends the session expiry time.
    """
    try:
        result = refresh_session()
        return RefreshSessionResponse(
            session=result["session"]
        )
    except Exception as e:
        logger.error(f"Refresh session error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=401,
            detail=f"Session refresh failed: {str(e)}"
        )


# ============================================================
# CONVERSATION ENDPOINTS
# ============================================================

@app.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=201
)
async def create_conversation_endpoint(
    request: ConversationCreateRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Create a new conversation.
    
    Requires authentication via Bearer token in Authorization header.
    """
    user_id = get_current_user_id_from_header(authorization)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    try:
        conversation = create_conversation(
            user_id=user_id,
            messages=request.messages,
            title=request.title
        )
        return ConversationResponse(
            id=str(conversation["id"]),
            user_id=str(conversation["user_id"]),
            messages=conversation["messages"],
            title=conversation.get("title"),
            created_at=conversation["created_at"],
            updated_at=conversation["updated_at"]
        )
    except Exception as e:
        logger.error(f"Create conversation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create conversation: {str(e)}"
        )


@app.get(
    "/conversations",
    response_model=ConversationListResponse
)
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    authorization: Optional[str] = Header(None)
):
    """
    List all conversations for the authenticated user.
    
    Requires authentication via Bearer token in Authorization header.
    """
    user_id = get_current_user_id_from_header(authorization)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    try:
        conversations = get_user_conversations(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        return ConversationListResponse(
            conversations=[
                ConversationResponse(
                    id=str(conv["id"]),
                    user_id=str(conv["user_id"]),
                    messages=conv["messages"],
                    title=conv.get("title"),
                    created_at=conv["created_at"],
                    updated_at=conv["updated_at"]
                )
                for conv in conversations
            ],
            total=len(conversations)
        )
    except Exception as e:
        logger.error(f"List conversations error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list conversations: {str(e)}"
        )


@app.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse
)
async def get_conversation_endpoint(
    conversation_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Get a specific conversation by ID.
    
    Requires authentication via Bearer token in Authorization header.
    """
    user_id = get_current_user_id_from_header(authorization)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    try:
        conversation = get_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )
        return ConversationResponse(
            id=str(conversation["id"]),
            user_id=str(conversation["user_id"]),
            messages=conversation["messages"],
            title=conversation.get("title"),
            created_at=conversation["created_at"],
            updated_at=conversation["updated_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversation: {str(e)}"
        )


@app.put(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse
)
async def update_conversation_endpoint(
    conversation_id: str,
    request: ConversationUpdateRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Update a conversation's messages or title.
    
    Requires authentication via Bearer token in Authorization header.
    """
    user_id = get_current_user_id_from_header(authorization)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    try:
        conversation = update_conversation(
            conversation_id=conversation_id,
            messages=request.messages,
            title=request.title,
            user_id=user_id
        )
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )
        return ConversationResponse(
            id=str(conversation["id"]),
            user_id=str(conversation["user_id"]),
            messages=conversation["messages"],
            title=conversation.get("title"),
            created_at=conversation["created_at"],
            updated_at=conversation["updated_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update conversation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update conversation: {str(e)}"
        )


@app.delete("/conversations/{conversation_id}")
async def delete_conversation_endpoint(
    conversation_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Delete a conversation.
    
    Requires authentication via Bearer token in Authorization header.
    """
    user_id = get_current_user_id_from_header(authorization)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    try:
        success = delete_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete conversation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete conversation: {str(e)}"
        )


@app.post(
    "/conversations/{conversation_id}/messages",
    response_model=ConversationResponse
)
async def add_message_endpoint(
    conversation_id: str,
    request: MessageAppendRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Append a message to a conversation.
    
    Requires authentication via Bearer token in Authorization header.
    """
    user_id = get_current_user_id_from_header(authorization)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    try:
        conversation = add_message_to_conversation(
            conversation_id=conversation_id,
            message=request.message,
            user_id=user_id
        )
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found"
            )
        return ConversationResponse(
            id=str(conversation["id"]),
            user_id=str(conversation["user_id"]),
            messages=conversation["messages"],
            title=conversation.get("title"),
            created_at=conversation["created_at"],
            updated_at=conversation["updated_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add message error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add message: {str(e)}"
        )


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

        client = get_gemini_client()

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
