"""
Supabase Client Initialization Module

Provides Supabase client for authentication and database operations.
Includes conversation persistence and user session management.
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables"
    )

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def get_supabase_client() -> Client:
    """Get the Supabase client instance."""
    return supabase


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get the currently authenticated user from session."""
    try:
        auth_result = supabase.auth.get_user()
        return auth_result.user if auth_result.user else None
    except Exception:
        return None


def get_current_user_id() -> Optional[str]:
    """Get the current user's ID."""
    user = get_current_user()
    return user.id if user else None


# ============================================================
# AUTHENTICATION OPERATIONS
# ============================================================

def sign_up(email: str, password: str, options: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Register a new user.
    
    Args:
        email: User's email address
        password: User's password
        options: Optional signup options (e.g., data, captcha_token)
    
    Returns:
        Dict containing user and session info
    """
    response = supabase.auth.sign_up(
        {
            "email": email,
            "password": password,
            **(options or {})
        }
    )
    return {
        "user": response.user,
        "session": response.session,
        "data": response.data
    }


def sign_in(email: str, password: str) -> Dict[str, Any]:
    """
    Sign in a user with email and password.
    
    Args:
        email: User's email address
        password: User's password
    
    Returns:
        Dict containing user and session info
    """
    response = supabase.auth.sign_in_with_password(
        {
            "email": email,
            "password": password
        }
    )
    return {
        "user": response.user,
        "session": response.session
    }


def sign_in_with_oauth(
    provider: str,
    options: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Sign in with OAuth provider.
    
    Args:
        provider: OAuth provider (e.g., 'google', 'github')
        options: Optional OAuth options
    
    Returns:
        OAuth sign-in response
    """
    return supabase.auth.sign_in_with_oauth(
        {
            "provider": provider,
            **(options or {})
        }
    )


def sign_out() -> Dict[str, Any]:
    """
    Sign out the current user.
    
    Returns:
        Logout response
    """
    return supabase.auth.sign_out()


def reset_password(email: str) -> Dict[str, Any]:
    """
    Send password reset email.
    
    Args:
        email: User's email address
    
    Returns:
        Reset password response
    """
    return supabase.auth.reset_password_for_email(email)


def get_session() -> Optional[Dict[str, Any]]:
    """
    Get the current session.
    
    Returns:
        Current session info or None
    """
    try:
        return supabase.auth.get_session()
    except Exception:
        return None


def refresh_session() -> Dict[str, Any]:
    """
    Refresh the current session.
    
    Returns:
        Refreshed session info
    """
    return supabase.auth.refresh_session()


# ============================================================
# CONVERSATION CRUD OPERATIONS
# ============================================================

def create_conversation(
    user_id: str,
    messages: List[Dict[str, Any]],
    title: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new conversation.
    
    Args:
        user_id: ID of the user (FK to auth.users)
        messages: List of message objects (JSONB)
        title: Optional conversation title
    
    Returns:
        Created conversation record
    """
    data = {
        "user_id": user_id,
        "messages": messages
    }
    if title:
        data["title"] = title
    
    response = supabase.table("conversations").insert(data).execute()
    return response.data[0] if response.data else None


def get_conversation(
    conversation_id: str,
    user_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get a conversation by ID.
    
    Args:
        conversation_id: UUID of the conversation
        user_id: Optional user ID for explicit filtering
    
    Returns:
        Conversation record or None
    """
    query = supabase.table("conversations").select("*").eq("id", conversation_id)
    
    if user_id:
        query = query.eq("user_id", user_id)
    
    response = query.execute()
    return response.data[0] if response.data else None


def get_user_conversations(
    user_id: str,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Get all conversations for a user.
    
    Args:
        user_id: ID of the user
        limit: Maximum number of conversations to return
        offset: Number of conversations to skip
    
    Returns:
        List of conversation records
    """
    response = (
        supabase.table("conversations")
        .select("*", count="exact")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return response.data


def update_conversation(
    conversation_id: str,
    messages: Optional[List[Dict[str, Any]]] = None,
    title: Optional[str] = None,
    user_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Update a conversation's messages or title.
    
    Args:
        conversation_id: UUID of the conversation
        messages: New messages list (JSONB)
        title: New title (optional)
        user_id: Optional user ID for explicit filtering
    
    Returns:
        Updated conversation record or None
    """
    data = {}
    if messages is not None:
        data["messages"] = messages
    if title is not None:
        data["title"] = title
    
    if not data:
        return None
    
    query = supabase.table("conversations").update(data).eq("id", conversation_id)
    
    if user_id:
        query = query.eq("user_id", user_id)
    
    response = query.execute()
    return response.data[0] if response.data else None


def delete_conversation(
    conversation_id: str,
    user_id: Optional[str] = None
) -> bool:
    """
    Delete a conversation.
    
    Args:
        conversation_id: UUID of the conversation
        user_id: Optional user ID for explicit filtering
    
    Returns:
        True if deleted, False otherwise
    """
    query = supabase.table("conversations").delete().eq("id", conversation_id)
    
    if user_id:
        query = query.eq("user_id", user_id)
    
    response = query.execute()
    return len(response.data) > 0


def add_message_to_conversation(
    conversation_id: str,
    message: Dict[str, Any],
    user_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Append a message to a conversation's messages array.
    
    Args:
        conversation_id: UUID of the conversation
        message: Message object to append
        user_id: Optional user ID for explicit filtering
    
    Returns:
        Updated conversation record or None
    """
    query = supabase.rpc(
        "append_message_to_conversation",
        {
            "conv_id": conversation_id,
            "new_message": message
        }
    )
    
    if user_id:
        query = query.eq("user_id", user_id)
    
    response = query.execute()
    return response.data[0] if response.data else None


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def is_authenticated() -> bool:
    """Check if a user is currently authenticated."""
    return get_current_user() is not None


def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user profile from auth.users."""
    try:
        response = supabase.auth.admin.get_user_by_id(user_id)
        return response.user
    except Exception:
        return None


def update_user_metadata(
    user_id: str,
    metadata: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Update user metadata."""
    try:
        response = supabase.auth.admin.update_user_by_id(
            user_id,
            {"user_metadata": metadata}
        )
        return response.user
    except Exception:
        return None


# ============================================================
# DATABASE MIGRATION SQL
# ============================================================

CONVERSATIONS_TABLE_SQL = """
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT,
    messages JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on user_id for faster queries
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);

-- Create index on updated_at for sorting
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);

-- Create trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_conversations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updated_at
CREATE TRIGGER update_conversations_updated_at_trigger
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_conversations_updated_at();

-- Create function to append message to conversation
CREATE OR REPLACE FUNCTION append_message_to_conversation(
    conv_id UUID,
    new_message JSONB
)
RETURNS conversations AS $$
DECLARE
    updated_conversation conversations;
BEGIN
    UPDATE conversations
    SET messages = messages || new_message,
        updated_at = NOW()
    WHERE id = conv_id
    RETURNING * INTO updated_conversation;
    
    RETURN updated_conversation;
END;
$$ LANGUAGE plpgsql;
"""


# ============================================================
# ROW LEVEL SECURITY POLICIES
# ============================================================

RLS_POLICIES_SQL = """
-- Enable Row Level Security on conversations table
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Policy 1: Users can view their own conversations
CREATE POLICY "Users can view their own conversations"
    ON conversations FOR SELECT
    USING (auth.uid() = user_id);

-- Policy 2: Users can create their own conversations
CREATE POLICY "Users can create their own conversations"
    ON conversations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy 3: Users can update their own conversations
CREATE POLICY "Users can update their own conversations"
    ON conversations FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Policy 4: Users can delete their own conversations
CREATE POLICY "Users can delete their own conversations"
    ON conversations FOR DELETE
    USING (auth.uid() = user_id);
"""


if __name__ == "__main__":
    print("Supabase Client Module")
    print(f"SUPABASE_URL: {SUPABASE_URL}")
    print(f"Client initialized: {supabase is not None}")
