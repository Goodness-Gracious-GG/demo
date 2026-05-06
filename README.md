# AI Code Analyzer - Professor Mode Backend

A FastAPI backend that analyzes code using the Gemini API with a professor mode approach - guiding students through questions rather than just giving answers. Now enhanced with **Supabase** for user authentication and conversation persistence.

## Features

- **Professor Mode**: Analyzes code through guided questioning
- **4-Phase Analysis**:
  1. Code Understanding
  2. Observations (issues identified)
  3. Socratic Questions (to guide learning)
  4. Suggestions (improvements)
- **User Authentication**: Sign up, sign in, and session management with Supabase Auth
- **Conversation Persistence**: Save and load code analysis conversations
- **Row Level Security**: Database policies ensure users can only access their own data

## Supabase Integration

### Database Schema

The `conversations` table stores user conversations:

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    messages JSONB DEFAULT '[]'::jsonb,
    title TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Row Level Security Policies

- Users can only view their own conversations
- Users can only create conversations for themselves
- Users can only update their own conversations
- Users can only delete their own conversations

See `migrations/001_create_conversations_table.sql` for the complete migration.

## API Endpoints

### Authentication

#### POST /auth/signup
Register a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "data": {"name": "Optional user metadata"}
}
```

**Response:**
```json
{
  "user": {"id": "...", "email": "..."},
  "session": {"access_token": "...", "refresh_token": "..."}
}
```

#### POST /auth/signin
Sign in with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "user": {"id": "...", "email": "..."},
  "session": {"access_token": "...", "refresh_token": "..."}
}
```

#### POST /auth/signout
Sign out the current user.

**Response:**
```json
{"message": "Signed out successfully"}
```

#### POST /auth/reset-password
Send a password reset email.

**Request:**
```json
{"email": "user@example.com"}
```

**Response:**
```json
{"message": "Password reset email sent"}
```

#### GET /auth/session
Get the current session.

**Response:**
```json
{
  "session": {...},
  "user": {...}
}
```

#### POST /auth/refresh
Refresh the current session.

**Response:**
```json
{"session": {...}}
```

### Conversations

All conversation endpoints require authentication via Bearer token in the `Authorization` header:
```
Authorization: Bearer <jwt_token>
```

#### POST /conversations
Create a new conversation.

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "title": "My Conversation"
}
```

**Response:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "messages": [...],
  "title": "My Conversation",
  "created_at": "2026-05-06T11:00:00",
  "updated_at": "2026-05-06T11:00:00"
}
```

#### GET /conversations
List all conversations for the authenticated user.

**Query Parameters:**
- `limit` (int, default: 50)
- `offset` (int, default: 0)

**Response:**
```json
{
  "conversations": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "messages": [...],
      "title": "...",
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "total": 10
}
```

#### GET /conversations/{conversation_id}
Get a specific conversation.

**Response:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "messages": [...],
  "title": "...",
  "created_at": "...",
  "updated_at": "..."
}
```

#### PUT /conversations/{conversation_id}
Update a conversation.

**Request:**
```json
{
  "messages": [...],
  "title": "Updated Title"
}
```

**Response:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "messages": [...],
  "title": "Updated Title",
  "created_at": "...",
  "updated_at": "..."
}
```

#### DELETE /conversations/{conversation_id}
Delete a conversation.

**Response:**
```json
{"message": "Conversation deleted successfully"}
```

#### POST /conversations/{conversation_id}/messages
Append a message to a conversation.

**Request:**
```json
{
  "message": {"role": "user", "content": "Hello"}
}
```

**Response:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "messages": [...],
  "title": "...",
  "created_at": "...",
  "updated_at": "..."
}
```

### Code Analysis

#### POST /analyze
Analyze code with the professor mode.

**Request:**
```json
{
  "code": "def find_max(arr):\n    max = 0\n    for i in arr:\n        if i > max:\n            max = i\n    return max",
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

#### GET /
Root endpoint returning API info.

**Response:**
```json
{"message": "Code Twins", "version": "1.0.0"}
```

## Setup

1. Install dependencies:
```bash
pip3 install -r requirements.txt
```

2. Set your API keys in `.env`:
```
GEMINI_API_KEY=your_gemini_api_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
```

3. Run the server:
```bash
python3 -m uvicorn main:app --reload
```

4. Open `index.html` in your browser

## Supabase Client Module

The `supabase_client.py` module provides:
- Supabase client initialization
- Authentication functions (sign up, sign in, sign out, etc.)
- Conversation CRUD operations
- Helper functions for user management

## Frontend Integration

The frontend (`index.html`) includes:
- Authentication modal for sign up/sign in
- Conversation sidebar for managing saved conversations
- Real-time sync with Supabase
- Automatic session persistence

## Environment Variables

- `GEMINI_API_KEY`: Google Gemini API key
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anon/public API key

## Database Migration

To set up the database schema, run the SQL in `migrations/001_create_conversations_table.sql` in your Supabase SQL Editor.

## Security

- All conversation endpoints require authentication
- Row Level Security ensures users can only access their own data
- JWT tokens are used for session management
- Passwords are hashed by Supabase Auth