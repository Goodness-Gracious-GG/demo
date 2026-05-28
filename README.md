# Mirror Mentor

AI-powered educational platform that helps students improve programming skills through guided Socratic questioning instead of direct answers.

Built during ACM TechSprint: Asteria using FastAPI, Supabase, Gemini API, and Vercel.

---

## Features

* AI-assisted code analysis using Google Gemini API
* 17 REST API endpoints for authentication and conversation workflows
* 4-phase guided feedback pipeline
* JWT authentication and session management
* Real-time conversation persistence with Supabase
* Row Level Security (RLS) for user data isolation
* Persistent AI conversation history
* Health monitoring and runtime configuration reloads

---

## Tech Stack

### Backend

* FastAPI
* Python
* Supabase
* PostgreSQL
* Gemini API

### Frontend

* HTML
* CSS
* JavaScript

### Infrastructure

* Vercel
* JWT Authentication
* Supabase Realtime

---

## Architecture

```text
Frontend (HTML/CSS/JS)
        |
        v
FastAPI Backend
        |
 -------------------------
 |           |           |
Gemini    Supabase    Auth
 API      Database     JWT
```

---

## Project Structure

```text
backend/
├── main.py
├── routes/
├── services/
├── models/
├── supabase_client.py
├── migrations/
└── utils/

frontend/
├── index.html
├── styles/
└── scripts/
```

---

## Core Features

### AI Code Analysis

Mirror Mentor analyzes code using a professor-style learning approach rather than directly giving answers.

The analysis pipeline includes:

1. Code Understanding
2. Observations and Issue Detection
3. Socratic Questioning
4. Improvement Suggestions

---

### Authentication System

Implemented authentication and session management using Supabase Auth with JWT validation.

Supported authentication workflows:

* User registration
* User login
* Session persistence
* Password reset
* Secure sign out

---

### Conversation Persistence

User conversations are stored using Supabase with:

* Row Level Security (RLS)
* Real-time synchronization
* JSONB message storage
* Protected user-specific access

---

## API Endpoints

### Authentication

* `POST /auth/signup`
* `POST /auth/signin`
* `POST /auth/signout`
* `POST /auth/reset-password`
* `GET /auth/session`
* `POST /auth/refresh`

### Conversations

* `POST /conversations`
* `GET /conversations`
* `GET /conversations/{id}`
* `PUT /conversations/{id}`
* `DELETE /conversations/{id}`
* `POST /conversations/{id}/messages`

### AI Analysis

* `POST /analyze`

### Monitoring

* `GET /health`
* `POST /admin/reload-config`

---

## Security Features

* JWT-based authentication
* Row Level Security (RLS)
* Protected conversation endpoints
* Input validation
* Environment variable validation
* Secure session handling
* CORS configuration

---

## Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd mirror-mentor
```

---

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Configure Environment Variables

Create a `.env` file:

```env
GEMINI_API_KEY=
SUPABASE_URL=
SUPABASE_ANON_KEY=
```

---

### 4. Run the Backend Server

```bash
python -m uvicorn main:app --reload
```

---

### 5. Open the Frontend

Open `index.html` in your browser.

---

## Health Monitoring

### GET /health

Checks:

* Gemini API connectivity
* Supabase connectivity
* Backend health status

---

## Development Testing

The platform was tested with 5 student users during development to evaluate:

* AI feedback quality
* Conversation flow
* Authentication workflows
* Overall usability

---

## Deployment

Mirror Mentor is deployed using:

* Vercel
* Supabase
* Gemini API

---

## Future Improvements

* Multi-language code analysis
* Shared collaborative workspaces
* AI-generated coding exercises
* Analytics dashboard
* Instructor review system

---

## License

MIT License
