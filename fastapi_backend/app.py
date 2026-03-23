import os
import sys
import time
from pathlib import Path
from typing import Optional

import logging

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Request,
    UploadFile,
    File,
    Form,
)
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from fastapi_backend.adk_runner import (
    run_agent_stream,
    create_new_session,
    list_user_sessions,
    delete_session,
    get_session_history,
)

from auth import register_user, authenticate_user, create_access_token
from auth.models import UserCreate, UserLogin
from auth.handler import AuthError
from auth.fastapi_middleware import get_current_user
from database.connection import create_tables

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
for p in (str(_HERE), str(_PROJECT_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Logging setup — single call configures the whole application ───────────────
from utils.logging_config import setup_logging  # noqa: E402

setup_logging(log_dir=_PROJECT_ROOT / "logs")
logger = logging.getLogger(__name__)


app = FastAPI(title="LMS Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every HTTP request with method, path, status code, and duration."""
    start = time.monotonic()
    # Extract user identity from Authorization header (best-effort, no exception on failure)
    user_hint = ""
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        # Only log that a token is present — never log the token value
        user_hint = " auth=bearer"
    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        logger.error(
            "[http] %s %s → UNHANDLED ERROR %s duration_ms=%d%s",
            request.method,
            request.url.path,
            exc,
            duration_ms,
            user_hint,
        )
        raise
    duration_ms = int((time.monotonic() - start) * 1000)
    level = logging.WARNING if response.status_code >= 400 else logging.INFO
    logger.log(
        level,
        "[http] %s %s → %d duration_ms=%d%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        user_hint,
    )
    return response


@app.on_event("startup")
async def startup_event():
    try:
        await create_tables()
        logger.info("[app] PostgreSQL application tables ready.")
    except Exception as exc:
        logger.warning(f"[app] Warning: could not bootstrap DB tables: {exc}")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/auth/signup", status_code=201)
async def signup(payload: UserCreate):
    try:
        user = await register_user(payload)
        return {
            "message": "Account created successfully.",
            "user_id": user["id"],
            "username": user["username"],
        }
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))


@app.post("/api/auth/login")
async def login(payload: UserLogin):
    try:
        user = await authenticate_user(payload.username, payload.password)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))

    token = create_access_token(user_id=user["id"], username=user["username"])
    return {"access_token": token}


@app.get("/api/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return user


@app.post("/api/sessions/new")
async def new_session(user: dict = Depends(get_current_user)):
    user_id = user["user_id"]
    session_id = await create_new_session(user_id)
    return {"session_id": session_id, "user_id": user_id}


@app.get("/api/sessions")
async def get_sessions(user: dict = Depends(get_current_user)):
    user_id = user["user_id"]
    sessions = await list_user_sessions(user_id)
    return {"sessions": sessions}


@app.delete("/api/sessions/{session_id}")
async def remove_session(session_id: str, user: dict = Depends(get_current_user)):
    user_id = user["user_id"]
    ok = await delete_session(user_id, session_id)
    return {"deleted": ok, "session_id": session_id}


@app.get("/api/sessions/{session_id}/history")
async def session_history(session_id: str, user: dict = Depends(get_current_user)):
    user_id = user["user_id"]
    try:
        messages = await get_session_history(user_id, session_id)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(request: Request, user: dict = Depends(get_current_user)):
    data = await request.json()
    user_id = user["user_id"]
    session_id = data.get("session_id")
    if not session_id:
        session_id = await create_new_session(user_id)

    message = data.get("message", "")
    if not message.strip():
        raise HTTPException(status_code=400, detail="message is required")

    async def stream_generator():
        try:
            # Yield SSE blocks
            async for chunk in run_agent_stream(user_id, session_id, message):
                yield {"data": chunk}

            # Send an explicit "[DONE]" signal for the client
            yield {"data": "[DONE]"}
        except Exception as e:
            yield {"event": "error", "data": str(e)}

    return EventSourceResponse(stream_generator())


@app.post("/api/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    user: dict = Depends(get_current_user),
):
    from database.connection import get_session
    from database.models import UploadedDocument
    from sqlalchemy.dialects.postgresql import insert
    import uuid
    import tempfile

    user_id = user["user_id"]
    if not session_id:
        session_id = await create_new_session(user_id)

    title = file.filename
    if not title or not title.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()

    # Save to a temp file so the upload_pdf tool can read it via file_path.
    # This avoids relying on the private _invocation_context API to inject
    # file bytes through the before_tool_callback.
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.write(file_bytes)
    tmp.close()
    tmp_path = tmp.name.replace("\\", "/")

    message = f'Please upload this PDF document: file_path="{tmp_path}" with display name "{title}"'

    # Upsert the document metadata
    async with get_session() as db:
        stmt = insert(UploadedDocument).values(
            user_id=uuid.UUID(user_id), filename=title
        )
        # Assuming you may upload same name document multiple times
        stmt = stmt.on_conflict_do_nothing(index_elements=["user_id", "filename"])
        try:
            await db.execute(stmt)
        except Exception as e:
            logger.error(f"[upload_pdf] Error inserting UploadedDocument: {e}")

    async def stream_generator():
        try:
            async for chunk in run_agent_stream(
                user_id=user_id,
                session_id=session_id,
                message=message,
            ):
                yield {"data": chunk}
            yield {"data": "[DONE]"}
        except Exception as e:
            yield {"event": "error", "data": str(e)}
        finally:
            # Clean up temp file
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    return EventSourceResponse(stream_generator())


@app.get("/api/documents")
async def get_uploaded_documents(user: dict = Depends(get_current_user)):
    from database.connection import get_session
    from database.models import UploadedDocument
    from sqlalchemy import select
    import uuid

    user_id = user["user_id"]
    documents = []

    try:
        async with get_session() as db:
            result = await db.execute(
                select(UploadedDocument)
                .where(UploadedDocument.user_id == uuid.UUID(user_id))
                .order_by(UploadedDocument.uploaded_at.desc())
            )
            rows = result.scalars().all()

            for row in rows:
                documents.append(
                    {
                        "id": str(row.id),
                        "filename": row.filename,
                        "uploaded_at": row.uploaded_at.isoformat(),
                    }
                )
    except Exception as e:
        logger.error(f"[get_uploaded_documents] Error: {e}")
        # Return empty list on error safely
        pass

    return {"documents": documents}


@app.post("/api/quiz/record-answers")
async def record_quiz_answers(request: Request, user: dict = Depends(get_current_user)):
    from database.connection import get_session
    from database.repositories import QuizRepository
    from database.models import QuizSession
    import uuid
    from sqlalchemy import select

    data = await request.json()
    quiz_session_id = data.get("quiz_session_id", "").strip()
    answers = data.get("answers", [])

    if not quiz_session_id:
        raise HTTPException(status_code=400, detail="quiz_session_id is required")
    if not answers:
        raise HTTPException(status_code=400, detail="answers list is required")

    recorded = 0
    failed = 0

    async with get_session() as db:
        repo = QuizRepository(db)

        # Get the underlying user_id for the quiz session
        result = await db.execute(
            select(QuizSession).where(QuizSession.id == uuid.UUID(quiz_session_id))
        )
        qs = result.scalar_one_or_none()
        if not qs:
            raise HTTPException(status_code=404, detail="Quiz session not found")

        for ans in answers:
            try:
                await repo.record_answer(
                    session_id=uuid.UUID(quiz_session_id),
                    user_id=qs.user_id,
                    question_number=int(ans["question_number"]),
                    user_answer=ans.get("user_answer", ""),
                    correct_answer=ans.get("correct_answer", ""),
                    is_correct=bool(ans.get("is_correct", False)),
                )
                recorded += 1
            except Exception as e:
                failed += 1
                logger.error(f"[record_quiz_answers] Error recording answer: {e}")

        # Mark session as completed
        if recorded > 0:
            try:
                await repo.complete_session(uuid.UUID(quiz_session_id))
            except Exception as e:
                logger.error(f"[record_quiz_answers] Error completing session: {e}")

    return {"recorded": recorded, "failed": failed}


# ─────────────────────────────────────────────────────────────────────────────
# Community & Crowdsourced APIs
# ─────────────────────────────────────────────────────────────────────────────


@app.get("/api/community/items")
async def get_community_items(
    item_type: Optional[str] = None,
    sort_by: str = "recent",
    limit: int = 20,
    offset: int = 0,
    user: dict = Depends(get_current_user),
):
    from database.connection import get_session
    from database.repositories import CommunityRepository

    async with get_session() as db:
        repo = CommunityRepository(db)
        items = await repo.get_items(item_type, sort_by, limit, offset)

        # Serialize
        results = []
        for item in items:
            results.append(
                {
                    "id": str(item.id),
                    "author_id": str(item.author_id),
                    "item_type": item.item_type,
                    "title": item.title,
                    "description": item.description,
                    "content_json": item.content_json,
                    "upvotes": item.upvotes,
                    "created_at": item.created_at.isoformat(),
                }
            )

        return {"items": results}


@app.post("/api/community/items/{item_id}/upvote")
async def toggle_item_upvote(item_id: str, user: dict = Depends(get_current_user)):
    from database.connection import get_session
    from database.repositories import CommunityRepository
    import uuid

    user_id = user["user_id"]
    async with get_session() as db:
        repo = CommunityRepository(db)
        try:
            is_upvoted = await repo.toggle_upvote(
                uuid.UUID(user_id), uuid.UUID(item_id)
            )
            await db.commit()
            return {"success": True, "upvoted": is_upvoted}
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Leaderboard APIs
# ─────────────────────────────────────────────────────────────────────────────


@app.get("/api/leaderboard")
async def get_leaderboard(user: dict = Depends(get_current_user)):
    from database.connection import get_session
    from database.repositories import LeaderboardRepository
    import uuid

    user_id = user["user_id"]
    async with get_session() as db:
        repo = LeaderboardRepository(db)
        top = await repo.get_top_by_quiz_score(limit=10)
        my_rank = await repo.get_user_rank(uuid.UUID(user_id))

    return {
        "leaderboard": top,
        "my_rank": my_rank,
    }


@app.get("/api/leaderboard/me")
async def get_my_leaderboard_rank(user: dict = Depends(get_current_user)):
    from database.connection import get_session
    from database.repositories import LeaderboardRepository
    import uuid

    user_id = user["user_id"]
    async with get_session() as db:
        repo = LeaderboardRepository(db)
        my_rank = await repo.get_user_rank(uuid.UUID(user_id))

    return {"my_rank": my_rank}


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting LMS Agent FastAPI backend on http://localhost:5000")
    uvicorn.run("fastapi_backend.app:app", host="0.0.0.0", port=5001, reload=True)
