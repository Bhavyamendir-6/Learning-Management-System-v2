# CLAUDE.md — LMS Agent UI

This file contains project context for Claude Code to reference when working on this codebase.

---

## Project Overview

**LMS Agent UI** is an AI-powered Learning Management System. Users upload PDF documents and interact with them through a conversational chat interface to:

- Ask questions grounded in their documents (semantic Q&A)
- Generate summaries (brief / detailed / key-points)
- Create flashcard sets
- Take interactive MCQ quizzes with scoring and retry
- Review quiz history and per-document analytics
- Publish quizzes and flashcards to the Community Hub and browse other users' content
- Compete on the global leaderboard
- Have Socratic one-on-one tutoring sessions with an AI tutor
- Save and retrieve learning notes from tutoring sessions

The system is a three-tier application:
```
Next.js UI  <--HTTP/SSE-->  FastAPI REST API  <--ADK-->  Google Gemini Agent Pipeline
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI/LLM | Google Gemini 2.5 Flash (`gemini-2.5-flash`, configurable via `config.py`) |
| Agent Framework | Google ADK (`google-adk`) — `Agent`, `Runner`, `DatabaseSessionService` |
| Vector Store | Gemini File Search Stores (per-user, cloud-hosted by Google) |
| Frontend | Next.js 16 (React 19, Tailwind CSS 4, react-markdown, rehype-highlight, glassmorphism) |
| Backend API | FastAPI + CORS (REST on port 5001) |
| Database | PostgreSQL via Neon (async SQLAlchemy 2.0 + asyncpg) |
| ADK Sessions | PostgreSQL via ADK's `DatabaseSessionService` (`POSTGRES_URL`) |
| Authentication | PyJWT (HS256, 24h expiry) + bcrypt (work factor 12) |
| Data Validation | Pydantic v2 (all models, structured LLM outputs) |
| Structured Output | Gemini `response_schema` with Pydantic models |
| Async | Native async — FastAPI/Uvicorn runs the asyncio event loop directly |
| Config | `python-dotenv` for `.env` loading; `config.py` for global model name |
| Launch | Manual launch with `npm run dev` (Frontend) and `python -m fastapi_backend.app` (Backend) |

---

## Project Structure

```
LMS_Project/
├── agent.py                          # Root agent (LMS_Executive) + before_tool_callback assignment
├── __init__.py                       # Exports root_agent
├── config.py                         # Global config: GEMINI_MODEL_NAME from .env
├── prompts.py                        # Root agent system prompt (ROOT_AGENT_INSTRUCTION)
├── requirements.txt                  # Python dependencies
├── README.md                         # Project documentation
├── QUICKSTART.md                     # Quick start guide
├── TEST_PROMPTS.md                   # Example prompts for testing
├── .env                              # Environment variables (never commit)
│
├── Models/
│   └── models.py                     # All Pydantic data models
│
├── Tools/
│   ├── db_handler.py                 # PostgreSQL CRUD facade (quiz sessions, tutor sessions, notes, users)
│   └── file_search_store_manager.py  # Gemini File Search store management + user ID extraction
│
├── utils/
│   └── callbacks.py                  # before_tool_callback (PDF binary injection for ADK Web uploads)
│
├── database/                         # PostgreSQL abstraction layer
│   ├── __init__.py
│   ├── connection.py                 # Async SQLAlchemy engine + session factory (Neon-tuned)
│   ├── models.py                     # SQLAlchemy ORM models (User, QuizSession, QuizAnswer, UploadedDocument, etc.)
│   └── repositories.py              # Repository classes (QuizRepository, TutorRepository, etc.)
│
├── auth/
│   ├── __init__.py                   # Public API exports (register_user, authenticate_user, etc.)
│   ├── handler.py                    # Auth logic: register, authenticate, JWT create/decode
│   ├── fastapi_middleware.py         # get_current_user FastAPI dependency
│   ├── middleware.py                 # Legacy Flask require_auth decorator (unused with FastAPI)
│   ├── models.py                     # UserCreate, UserLogin, UserInDB Pydantic models
│   └── password_utils.py            # bcrypt hash/verify utilities
│
├── fastapi_backend/
│   ├── app.py                        # FastAPI REST API (all routes)
│   └── adk_runner.py                 # ADK Runner wrapper (native async, session management, SSE streaming)
│
├── nextjs_frontend/                  # Next.js React frontend application
│   └── src/
│       ├── app/                      # Next.js App Router (page.tsx, login/page.tsx, layout.tsx, globals.css)
│       ├── components/
│       │   ├── ChatBubble.tsx        # Message bubble with Markdown rendering + quiz JSON detection
│       │   ├── Sidebar.tsx           # Resizable sidebar (sessions, docs, quick actions, PDF upload)
│       │   ├── QuizRenderer.tsx      # Interactive MCQ quiz UI
│       │   ├── Flashcard.tsx         # Flashcard display component
│       │   ├── PdfUploader.tsx       # PDF upload button & file picker
│       │   ├── BufferingAnimation.tsx # Dynamic "Ring of Power" loading animation
│       │   ├── AgentThinkingIndicator.tsx # Live agent activity status (tool calls, transfers)
│       │   ├── theme-provider.tsx    # Dark/light theme context provider
│       │   └── theme-toggle.tsx      # Theme switch button
│       └── lib/
│           ├── api.ts               # API client (auth, chat, sessions, upload)
│           └── theme.ts             # Theme utility functions
│
└── subagents/
    ├── __init__.py                   # Re-exports all agents and tools
    ├── pdf_handler/                  # PDF_Handler agent
    ├── quiz_agent/                   # Quiz_Master agent
    ├── quiz_history_agent/           # Quiz_Historian agent
    ├── learning_content_agent/       # LearningContent_Agent
    ├── tutor_agent/                  # AI_Tutor agent
    └── community_agent/              # Community_Agent
```

Each sub-agent folder follows this convention:
```
subagents/<name>/
├── __init__.py
├── agent.py       # Agent definition (imports prompt + tools)
├── prompt.py      # System prompt as a string constant
└── tools/
    ├── __init__.py
    └── <action>_tool.py   # One file per tool function
```

**Note:** Document deletion is not supported. The `PDF_Handler` agent only supports upload and list operations.

---

## Architecture & Key Patterns

### 1. Multi-Agent Orchestration
`LMS_Executive` (root agent) acts as a pure router. Its system prompt (in `prompts.py`) describes routing rules. Sub-agents do **not** call each other — all routing goes through the root. The `description` field on each sub-agent guides the orchestrator's transfer decisions.

### 2. `before_tool_callback` (utils/callbacks.py)
A single callback applied to all sub-agents handles **one** cross-cutting concern:
- **PDF binary injection**: Auto-detects PDF `inline_data` attachments from the ADK Web interface and populates `file_content` / `filename` args for the `upload_pdf` tool.

User identity is **not** injected here. See pattern #10 below.

### 3. Two-Pass Gemini Generation (Structured Output + FileSearch)
Gemini cannot combine `FileSearch` tools and `response_schema` in a single call. The pattern:
- **Pass 1**: Call Gemini with `FileSearch` enabled → retrieve document content as plain text
- **Pass 2**: Call Gemini with `response_schema=<PydanticModel>` (no tools) using retrieved text → get validated structured JSON

Used in: `generate_quiz_tool.py`, `generate_summary_tool.py`, `generate_flashcards_tool.py`, `start_tutoring_session_tool.py`.

### 4. Native Async Architecture
`adk_runner.py` uses FastAPI/Uvicorn's native asyncio event loop directly. No background thread or `asyncio.run_coroutine_threadsafe()` is needed. ADK's `DatabaseSessionService` creates an asyncpg connection pool bound to this loop. All operations (`run_agent_stream`, `create_new_session`, `list_user_sessions`, etc.) are `async def` functions.

### 5. JWT-Centric Identity (Server-Side Enforcement)
The FastAPI API ignores any `user_id` in request bodies. User identity is read **only** from the decoded JWT in the `get_current_user` dependency (`auth/fastapi_middleware.py`).

### 6. User-Scoped Gemini File Search Stores
Every user gets their own store: `lms-agent-store-{sanitized_user_id}`. `sanitize_user_id()` strips special characters (keeps alphanumeric, `-`, `_`) and falls back to MD5 hash if result is empty. An in-process `_store_name_cache` dict maps display names to real `fileSearchStores/<id>` paths to avoid repeated API calls.

### 7. SSE Streaming with Activity Events
Agent calls can take 10–30 seconds. The FastAPI backend sends responses token-by-token via Server-Sent Events (SSE) using `sse-starlette`. The stream emits two types of events:
- **`status`** events: agent transfers and tool calls (displayed by `AgentThinkingIndicator.tsx`)
- **`text`** events: final response content (streamed word-by-word by `ChatBubble.tsx`)

**UI Note:** The frontend uses strict `position: fixed` and flex-column boundaries to prevent the page from moving structurally inside external workspaces/iframes.

### 8. Quiz UI Detection via JSON Parsing
`nextjs_frontend/src/components/ChatBubble.tsx` uses regex to detect JSON blocks in agent responses (looks for a `questions` key in fenced ` ```json ``` ` or bare JSON objects). When detected, renders an interactive `QuizRenderer` instead of raw text. After submission, answers are persisted directly via `POST /api/quiz/record-answers` (bypasses the agent for this write).

### 9. Pydantic for Structured LLM Output
Pydantic v2 models are passed as `response_schema` to Gemini's `GenerateContentConfig`. Code uses `response.parsed` first, then falls back to `json.loads(response.text)` + manual Pydantic construction for robustness against partial responses.

### 10. ADK-Native User Identity via Session State
User identity is seeded into session state at creation time in `adk_runner.py`:
```python
state={"current_user_id": user_id}
```
Every tool reads it from `tool_context.state.get("current_user_id")` via `extract_user_id_from_context(tool_context)`. No `before_tool_callback` whitelist, no private `_invocation_context` API. See the **Tool Function Signature Convention** section for the full pattern.

### 11. PostgreSQL Database Layer
Application data (users, quiz sessions, answers, tutor sessions, notes, uploaded documents) lives in PostgreSQL (Neon). ADK session/event data also lives in the same database via `DatabaseSessionService`.

- **`database/models.py`** — SQLAlchemy ORM: `User`, `QuizSession`, `QuizQuestion`, `QuizAnswer`, `TutorSession`, `TutorMessage`, `LearningNote`, `UploadedDocument`
- **`database/connection.py`** — Async engine (Neon-tuned pool), `get_session()` context manager, `create_tables()` bootstrap
- **`database/repositories.py`** — `UserRepository`, `QuizRepository`, `TutorRepository`, `NotesRepository`
- **`Tools/db_handler.py`** — Sync facade over the async repositories; all public functions return dicts with `_id` key for backwards compatibility

Schema is bootstrapped automatically on FastAPI startup via `@app.on_event("startup")` in `app.py`.

### 12. Centralized Model Configuration
The Gemini model name is abstracted into `config.py`:
```python
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
```
All agents import from `config` instead of hardcoding the model string.

---

## Agents & Sub-Agents

| Agent | Class Name | Responsibility |
|-------|-----------|----------------|
| Root Orchestrator | `LMS_Executive` | Routes user intent to the correct sub-agent |
| PDF Management | `PDF_Handler` | Upload and list PDFs in user's File Search store (deletion not supported) |
| Quiz | `Quiz_Master` | Generate quizzes, record answers, complete/retry sessions |
| Quiz History | `Quiz_Historian` | Retrieve past sessions, scores, per-document stats |
| Learning Content | `LearningContent_Agent` | Q&A, summaries, flashcard generation from documents |
| Tutoring | `AI_Tutor` | Socratic tutoring, follow-ups, examples, comprehension checks, notes |
| Community | `Community_Agent` | Publish user-generated content to the community hub |

---

## PostgreSQL Tables

| Table | Purpose | Key Fields |
|-------|---------|-----------| 
| `users` | Auth — unique indexes on `username` and `email` | `id` (UUID), `username`, `email`, `hashed_password`, `is_active`, `created_at` |
| `quiz_sessions` | Quiz state machine | `id`, `user_id`, `document_name`, `status` (`in_progress`/`completed`/`abandoned`), `current_score`, `final_score`, `is_retry`, `adk_session_id` |
| `quiz_questions` | Normalized per-question data | `id`, `session_id` (FK), `question_number`, `question_text`, `option_a`–`option_d`, `correct_answer`, `hint`, `explanation` |
| `quiz_answers` | Individual answer records | `id`, `session_id` (FK), `question_id` (FK), `user_id`, `question_number`, `user_answer`, `correct_answer`, `is_correct` |
| `tutor_sessions` | Tutoring session metadata | `id`, `user_id`, `document_name`, `topic`, `difficulty_level`, `status`, `adk_session_id` |
| `tutor_messages` | Ordered conversation log | `id`, `session_id` (FK), `role` (`tutor`/`student`), `content`, `message_order`, `created_at` |
| `learning_notes` | User-saved insights from tutoring | `id`, `user_id`, `document_name`, `topic`, `insight`, `tutor_session_id` (FK nullable), `created_at` |
| `uploaded_documents` | Document upload metadata for sidebar | `id`, `user_id` (FK), `filename`, `uploaded_at` |
| `community_items` | Crowdsourced quizzes and flashcards | `id`, `author_id` (FK), `item_type`, `title`, `description`, `content_json`, `upvotes`, `created_at` |
| `item_upvotes` | Tracks user upvotes on items | `id`, `user_id` (FK), `item_id` (FK), `created_at` |

ADK session/event tables (`sessions`, `events`) are also in the same database, managed by ADK's `DatabaseSessionService`.

---

## FastAPI Routes

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| GET | `/api/health` | Public | Health check |
| POST | `/api/auth/signup` | Public | Register new user |
| POST | `/api/auth/login` | Public | Login, returns JWT |
| GET | `/api/auth/me` | JWT | Get current user info |
| POST | `/api/sessions/new` | JWT | Create new ADK chat session |
| GET | `/api/sessions` | JWT | List user's chat sessions |
| DELETE | `/api/sessions/<id>` | JWT | Delete a chat session |
| GET | `/api/sessions/<id>/history` | JWT | Get chat history for a session |
| POST | `/api/chat` | JWT | Send message to agent (SSE stream) |
| POST | `/api/upload` | JWT | Upload PDF (multipart form, SSE stream) |
| GET | `/api/documents` | JWT | List uploaded document metadata |
| POST | `/api/quiz/record-answers` | JWT | Persist quiz answers directly to DB |
| GET | `/api/community/items` | JWT | List community items (quizzes, flashcards) |
| POST | `/api/community/items/<id>/upvote` | JWT | Toggle upvote on an item |
| GET | `/api/leaderboard` | JWT | Get top users by quiz score |
| GET | `/api/leaderboard/me` | JWT | Get current user's rank |

---

## Environment Variables (`.env`)

```
GEMINI_API_KEY=<your Gemini API key>
POSTGRES_URL=<Neon/PostgreSQL connection string>   # e.g. postgresql+asyncpg://user:pass@host/db
JWT_SECRET_KEY=<random secret string>
GEMINI_MODEL_NAME=gemini-2.5-flash   # optional, defaults to gemini-2.5-flash
JWT_EXPIRY_HOURS=24          # optional, defaults to 24
JWT_ALGORITHM=HS256          # optional, defaults to HS256
FASTAPI_PORT=5001            # optional
```

---

## Running the Project

**Manual:**
```bash
# Terminal 1 — FastAPI backend
source .venv/bin/activate
python -m fastapi_backend.app

# Terminal 2 — Next.js frontend
cd nextjs_frontend
npm run dev
```

**ADK Web UI (alternative frontend):**
```bash
adk web
```
Runs the standard ADK web interface which also works with the root agent. PDF uploads via ADK Web use `inline_data` which the `before_tool_callback` handles automatically.

**ADK CLI:**
```bash
adk run .
```

---

## Tool Function Signature Convention

### User Identity Pattern (ADK-native)

User identity flows through ADK session state, not through tool parameters or callbacks.

**Step 1 — Session creation** (`fastapi_backend/adk_runner.py`):
```python
await session_service.create_session(
    app_name=APP_NAME,
    user_id=user_id,
    session_id=session_id,
    state={"current_user_id": user_id},   # seeded once here
)
```

**Step 2 — Tool reads it** via `tool_context.state` (public ADK API):
```python
from Tools.file_search_store_manager import extract_user_id_from_context

def some_tool(arg1: str, tool_context=None) -> str:
    user_id = extract_user_id_from_context(tool_context) or "anonymous-user"
    # or, when calling get_user_store:
    store_name = get_user_store(tool_context=tool_context)
```

**What `extract_user_id_from_context` does** (`Tools/file_search_store_manager.py`):
```python
def extract_user_id_from_context(tool_context) -> Optional[str]:
    if not tool_context:
        return None
    return tool_context.state.get("current_user_id") or None
```

### Why not `before_tool_callback` injection?
The old approach maintained a `TOOLS_WITH_USER_ID` whitelist and used the private `_invocation_context` API (which is unstable and known to break on Agentspace). The state-seeding pattern uses only the public `tool_context.state` API and requires no whitelist — any new tool just calls `tool_context.state.get("current_user_id")` directly.

### Tool signature template
```python
def my_tool(
    required_arg: str,
    optional_arg: Optional[str] = None,
    tool_context=None,          # ADK injects this; never listed in docstring
) -> str:
    """
    Tool description for the LLM.

    Args:
        required_arg: ...
        optional_arg: ...
        # Do NOT document tool_context — it must be invisible to the LLM

    Returns:
        str: ...
    """
    user_id = extract_user_id_from_context(tool_context) or "anonymous-user"
    ...
```

---

## Key File Locations

| Purpose | File |
|---------|------|
| Root agent + callback | [agent.py](agent.py) |
| Global model config | [config.py](config.py) |
| Root agent prompt | [prompts.py](prompts.py) |
| before_tool_callback | [utils/callbacks.py](utils/callbacks.py) |
| All Pydantic models | [Models/models.py](Models/models.py) |
| PostgreSQL CRUD facade | [Tools/db_handler.py](Tools/db_handler.py) |
| File Search store manager | [Tools/file_search_store_manager.py](Tools/file_search_store_manager.py) |
| DB engine + session factory | [database/connection.py](database/connection.py) |
| SQLAlchemy ORM models | [database/models.py](database/models.py) |
| Repository layer | [database/repositories.py](database/repositories.py) |
| FastAPI Backend | [fastapi_backend/app.py](fastapi_backend/app.py) |
| ADK runner integration | [fastapi_backend/adk_runner.py](fastapi_backend/adk_runner.py) |
| Auth handler | [auth/handler.py](auth/handler.py) |
| Auth middleware (FastAPI) | [auth/fastapi_middleware.py](auth/fastapi_middleware.py) |
| Next.js main page | [nextjs_frontend/src/app/page.tsx](nextjs_frontend/src/app/page.tsx) |
| Chat bubble + markdown | [nextjs_frontend/src/components/ChatBubble.tsx](nextjs_frontend/src/components/ChatBubble.tsx) |
| Sidebar component | [nextjs_frontend/src/components/Sidebar.tsx](nextjs_frontend/src/components/Sidebar.tsx) |
| Quiz UI renderer | [nextjs_frontend/src/components/QuizRenderer.tsx](nextjs_frontend/src/components/QuizRenderer.tsx) |
| Agent activity indicator | [nextjs_frontend/src/components/AgentThinkingIndicator.tsx](nextjs_frontend/src/components/AgentThinkingIndicator.tsx) |
| Theme provider | [nextjs_frontend/src/components/theme-provider.tsx](nextjs_frontend/src/components/theme-provider.tsx) |
| API client | [nextjs_frontend/src/lib/api.ts](nextjs_frontend/src/lib/api.ts) |
