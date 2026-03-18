# LMS Agent

An AI-powered Learning Management System built with Google ADK and Gemini 2.5 Flash. Upload PDFs, ask questions, take quizzes, generate flashcards, get summaries, and receive personalized Socratic tutoring — all backed by Gemini File Search and PostgreSQL (Neon).

## Features

- **PDF Management**: Upload single or batch PDFs; list your documents in your personal File Search store
- **Document Q&A**: Ask questions grounded in your uploaded documents using Gemini's semantic search
- **Summaries**: Generate brief, detailed, or key-point summaries of any document
- **Flashcards**: Auto-generate study cards (front/back, category, difficulty) from document content
- **Interactive Quizzes**: Take 5-question MCQ quizzes generated from your documents; retry wrong answers
- **Quiz History & Analytics**: Review past quiz sessions, scores, and per-document performance stats
- **Community Hub & Leaderboard**: Publish and discover crowdsourced quizzes/flashcards, upvote items, and compete on the global leaderboard
- **AI Tutor**: Personalized Socratic tutoring with follow-up questions, comprehension checks, and learning notes
- **Learning Notes**: Save and retrieve key insights from tutoring sessions
- **User-Scoped Storage**: Each user has an isolated Gemini File Search store and their own PostgreSQL data
- **Next.js UI**: Full-featured chat interface with sidebar controls, PDF uploader, quick action buttons, and interactive quiz rendering
- **Futuristic Design System**: Glassmorphism visuals, immersive dark/light theme toggle, dynamic "Ring of Power" buffering animations, and structured Markdown output for agent responses
- **Real-Time Streaming**: SSE-powered word-by-word streaming of agent responses with live agent activity indicators (tool calls, agent transfers)
- **Robust Scrolling Architecture**: Built natively to withstand iframe/workspace clipping by utilizing strict flex-column document clamping
- **Resizable Sidebar**: Drag-and-drop resizable sidebar with persistent document list and session history
- **FastAPI REST API**: Backend that bridges the Next.js frontend to the Google ADK agent, featuring structured Python logging
- **Persistent Sessions**: Chat history persists across restarts via ADK's PostgreSQL-backed `DatabaseSessionService`

## Architecture

```
Next.js UI  ──HTTP/SSE──>  FastAPI Backend  ──ADK──>  LMS_Executive (root agent)
                                                        │
                    ┌───────────────────────────────────┼────────────────────────────┐
                    │               │                   │                            │
              PDF_Handler     Quiz_Master        Quiz_Historian   LearningContent_Agent
                            Community_Agent                             AI_Tutor
```

### Sub-Agents

| Agent | Name | Responsibilities |
|-------|------|-----------------|
| PDF Handler | `PDF_Handler` | Upload and list PDFs |
| Quiz Master | `Quiz_Master` | Generate MCQ quizzes, record answers, complete/retry quizzes |
| Quiz Historian | `Quiz_Historian` | Quiz history, session details, document performance stats |
| Learning Content | `LearningContent_Agent` | Document Q&A, summaries, flashcard generation |
| AI Tutor | `AI_Tutor` | Socratic tutoring, follow-ups, comprehension checks, learning notes |
| Community Agent | `Community_Agent` | Publish generated quizzes and flashcards to the community hub |

## Prerequisites

- Python 3.10 or higher
- Node.js 18+ installed
- Google ADK installed (`pip install google-adk`)
- Gemini API key (with File Search API access)
- PostgreSQL database — [Neon](https://neon.tech) free tier recommended

## Installation

1. **Navigate to the project directory**:
   ```bash
   cd LMS_Project
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies**:
   ```bash
   cd nextjs_frontend
   npm install
   cd ..
   ```

5. **Configure environment variables**:

   Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   POSTGRES_URL=postgresql+asyncpg://user:password@host/dbname
   JWT_SECRET_KEY=your_random_secret_here
   ```

   - Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Get a free PostgreSQL connection string from [Neon](https://neon.tech)
   - Generate a JWT secret: `python -c "import secrets; print(secrets.token_hex(32))"`

## Running the Application

### Option 1: Next.js UI + FastAPI Backend (Recommended)

**Manual launch (two terminals):**

Terminal 1 — FastAPI backend:
```bash
source .venv/bin/activate
python -m fastapi_backend.app
```

Terminal 2 — Next.js frontend:
```bash
cd nextjs_frontend
npm run dev
```

Then open `http://localhost:3000` in your browser.

### Option 2: ADK Web Interface

```bash
adk web
```

Starts the ADK Web UI for direct agent interaction with drag-and-drop PDF upload support.

### Option 3: ADK CLI

```bash
adk run .
```

Interactive command-line mode. Example prompts:
```
> Upload C:/path/to/document.pdf
> What is the main topic of this document?
> Generate a quiz on chapter 3
> Teach me about neural networks
> Show my quiz history
```

## Project Structure

```
LMS_Project/
├── agent.py                              # Root agent (LMS_Executive) + before_tool_callback
├── __init__.py                           # Exports root_agent
├── config.py                             # Global config (GEMINI_MODEL_NAME, .env loading)
├── prompts.py                            # Root agent system prompt (ROOT_AGENT_INSTRUCTION)
├── requirements.txt                      # Python dependencies
│
├── Models/
│   └── models.py                         # Pydantic models (Quiz, Flashcard, Summary, TutoringSession, etc.)
│
├── Tools/
│   ├── db_handler.py                     # PostgreSQL CRUD facade (sync wrapper over async repositories)
│   └── file_search_store_manager.py      # Gemini File Search store management + user ID extraction
│
├── utils/
│   └── callbacks.py                      # before_tool_callback (PDF binary injection for ADK Web)
│
├── database/
│   ├── connection.py                     # Async SQLAlchemy engine + session factory (Neon-tuned)
│   ├── models.py                         # ORM models (User, QuizSession, QuizAnswer, UploadedDocument, etc.)
│   └── repositories.py                   # Repository classes for each domain
│
├── auth/
│   ├── handler.py                        # Auth logic: register, authenticate, JWT create/decode
│   ├── fastapi_middleware.py             # get_current_user FastAPI dependency
│   ├── middleware.py                     # Legacy Flask require_auth decorator
│   ├── models.py                        # UserCreate, UserLogin, UserInDB Pydantic models
│   └── password_utils.py                # bcrypt hash/verify utilities
│
├── fastapi_backend/
│   ├── app.py                            # FastAPI REST API (all routes)
│   └── adk_runner.py                     # ADK Runner wrapper (native async, session management)
│
├── nextjs_frontend/                      # Next.js React frontend application
│   └── src/
│       ├── app/                          # Next.js App Router pages (home, login)
│       ├── components/                   # React components
│       │   ├── ChatBubble.tsx            # Message bubble with Markdown, quiz JSON detection
│       │   ├── Sidebar.tsx               # Resizable sidebar (sessions, docs, quick actions, PDF upload)
│       │   ├── QuizRenderer.tsx          # Interactive MCQ quiz UI
│       │   ├── Flashcard.tsx             # Flashcard display component
│       │   ├── PdfUploader.tsx           # PDF upload button & file picker
│       │   ├── BufferingAnimation.tsx    # Dynamic "Ring of Power" loading animation
│       │   ├── AgentThinkingIndicator.tsx # Live agent activity status display
│       │   ├── theme-provider.tsx        # Dark/light theme context provider
│       │   └── theme-toggle.tsx          # Theme switch button
│       └── lib/                          # API client & theme utilities
│
└── subagents/
    ├── pdf_handler/
    │   ├── agent.py
    │   └── tools/
    │       ├── upload_pdf_tool.py        # Single PDF upload to File Search store
    │       ├── batch_upload_pdf_tool.py  # Batch PDF upload
    │       └── list_files_tool.py        # List documents in user's store
    │
    ├── quiz_agent/
    │   └── tools/
    │       ├── generate_quiz_tool.py     # Generate 5-question MCQ quiz from a document
    │       ├── record_answer_tool.py     # Record a user's quiz answer
    │       ├── complete_quiz_tool.py     # Mark quiz as completed, show final score
    │       └── retry_quiz_tool.py        # Retry incorrect answers from last quiz
    │
    ├── quiz_history_agent/
    │   └── tools/
    │       ├── quiz_history_tool.py      # List past quiz sessions and scores
    │       ├── session_details_tool.py   # Detailed view of a single quiz session
    │       └── document_stats_tool.py    # Per-document quiz performance statistics
    │
    ├── learning_content_agent/
    │   └── tools/
    │       ├── ask_question_tool.py      # Document Q&A via File Search
    │       ├── generate_summary_tool.py  # Brief/detailed/key-points summary
    │       └── generate_flashcards_tool.py  # Flashcard generation
    │
    ├── tutor_agent/
    │   └── tools/
    │       ├── start_tutoring_session_tool.py
    │       ├── ask_followup_tool.py
    │       ├── check_understanding_tool.py
    │       ├── save_learning_notes_tool.py
    │       └── get_learning_notes_tool.py
    │
    └── community_agent/
        └── tools/
            └── publish_to_community_tool.py # Publish quizzes/flashcards
```

## How It Works

1. **User Identification**: `user_id` (UUID from JWT) is seeded into ADK session state at creation time. Every tool reads it from `tool_context.state` — no callback injection required.

2. **Document Storage**: PDFs are uploaded to a user-scoped Gemini File Search store. Files are processed, chunked, embedded, and indexed for semantic retrieval. Upload metadata is also persisted to the `uploaded_documents` table for sidebar display.

3. **Query / Learning**: Questions are answered using Gemini's File Search API which performs semantic search on the user's documents.

4. **Quiz Persistence**: Quiz sessions, questions, and answers are stored in PostgreSQL. This enables history, analytics, and retry functionality.

5. **Tutoring**: The AI Tutor uses a Socratic dialogue approach — asking questions rather than lecturing. Session history and learning notes are persisted to PostgreSQL.

6. **Session Persistence**: ADK chat history is stored in PostgreSQL via `DatabaseSessionService` and survives API restarts.

7. **Frontend**: The Next.js UI communicates with the FastAPI REST API via standard fetch and SSE, which runs the ADK agent and streams text responses word-by-word in real-time. Agent activity (tool calls, agent transfers) is streamed as status events for live UI indicators.

## FastAPI Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/health` | Public | Health check |
| POST | `/api/auth/signup` | Public | Register new user |
| POST | `/api/auth/login` | Public | Login, returns JWT |
| GET | `/api/auth/me` | JWT | Current user info |
| POST | `/api/sessions/new` | JWT | Create a new ADK session |
| GET | `/api/sessions` | JWT | List sessions for a user |
| DELETE | `/api/sessions/<id>` | JWT | Delete a session |
| GET | `/api/sessions/<id>/history` | JWT | Get chat history for a session |
| POST | `/api/chat` | JWT | Send a message to the agent (SSE stream) |
| POST | `/api/upload` | JWT | Upload a PDF file (SSE stream) |
| GET | `/api/documents` | JWT | List uploaded documents for sidebar |
| POST | `/api/quiz/record-answers` | JWT | Directly persist quiz answers to PostgreSQL |
| GET | `/api/community/items` | JWT | Get crowdsourced quizzes and flashcards |
| POST | `/api/community/items/<id>/upvote` | JWT | Upvote a community item |
| GET | `/api/leaderboard` | JWT | Get top users by quiz score |
| GET | `/api/leaderboard/me` | JWT | Get current user's rank |

## PostgreSQL Tables

| Table | Purpose |
|-------|---------|
| `users` | User accounts (username, email, hashed password) |
| `quiz_sessions` | Quiz session state, scores, and metadata |
| `quiz_questions` | Normalized per-question data (question text, options, answer, hint) |
| `quiz_answers` | Individual answer records per question |
| `tutor_sessions` | Tutoring session metadata (topic, difficulty, document) |
| `tutor_messages` | Ordered conversation log for tutoring sessions |
| `learning_notes` | User-saved key insights from tutoring |
| `uploaded_documents` | Document upload metadata for sidebar display |
| `community_items` | Crowdsourced quizzes and flashcards |
| `item_upvotes` | Tracks user upvotes on community items |
| `sessions` / `events` | ADK session state (managed by `DatabaseSessionService`) |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `POSTGRES_URL` | Yes | PostgreSQL connection string (Neon or any PostgreSQL) |
| `JWT_SECRET_KEY` | Yes | Secret key for signing JWTs |
| `GEMINI_MODEL_NAME` | No | LLM model name (default: `gemini-2.5-flash`) |
| `JWT_EXPIRY_HOURS` | No | JWT lifetime in hours (default: 24) |
| `JWT_ALGORITHM` | No | JWT signing algorithm (default: HS256) |
| `FASTAPI_PORT` | No | FastAPI port (default: 5001) |

## Troubleshooting

### FastAPI backend not starting
- Ensure `POSTGRES_URL` and `JWT_SECRET_KEY` are set in `.env`
- Run `pip install -r requirements.txt` to ensure all dependencies are installed
- Verify the Neon database is accessible from your network

### API Key / File Search errors
- Verify `GEMINI_API_KEY` is set correctly in `.env`
- Ensure the API key has File Search API access enabled

### PostgreSQL connection errors
- Check that `POSTGRES_URL` is a valid connection string (must start with `postgresql://`, `postgres://`, or `postgresql+asyncpg://`)
- Neon databases may sleep after inactivity — the first request after a cold start may be slow

### Import errors
- Make sure you are running commands from the project root (`LMS_Project/`)
- Verify Python 3.10+ is being used
- Activate your virtual environment before running

### Frontend errors
- Make sure you run `npm run dev` from inside the `nextjs_frontend/` folder, not the project root
- Run `npm install` first if `node_modules/` is missing

## Notes

- All agents use `gemini-2.5-flash` by default (configurable via `GEMINI_MODEL_NAME` env var in `config.py`)
- File Search stores are created automatically on first upload per user
- Large PDFs may take a moment to index before queries return accurate results
- Document deletion is not supported — uploaded documents are permanent in your File Search store
- The database schema is bootstrapped automatically on first FastAPI startup (`CREATE TABLE IF NOT EXISTS`)
