"""
Tools/db_handler.py — Async facade over the PostgreSQL repository layer.

Provides simple async functions that tool implementations can call directly.
Each function opens a short-lived async session, delegates to the appropriate
repository, commits, and returns a plain dict or primitive.

All public functions return dicts with an '_id' key for backwards compatibility.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from sqlalchemy.exc import IntegrityError

from database.connection import create_tables, get_session
from database.models import QuizSession, TutorSession
from database.repositories import (
    NotesRepository,
    QuizRepository,
    TutorRepository,
    UserRepository,
)


# ─── Schema ───────────────────────────────────────────────────────────────────


async def setup_database_indexes() -> bool:
    """
    Bootstrap the PostgreSQL schema (idempotent).

    All indexes are defined in database/models.py and created via
    SQLAlchemy's metadata.create_all().

    Returns:
        bool: True if successful
    """
    try:
        await create_tables()
        return True
    except Exception as e:
        logger.error("[db_handler] setup_database_indexes error: %s", e)
        return False


# ─── Serializers ─────────────────────────────────────────────────────────────


def _user_to_dict(user) -> Dict[str, Any]:
    return {
        "_id": str(user.id),
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "hashed_password": user.hashed_password,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _quiz_session_to_dict(qs) -> Dict[str, Any]:
    return {
        "_id": str(qs.id),
        "id": str(qs.id),
        "user_id": str(qs.user_id),
        "document_name": qs.document_name,
        "status": qs.status,
        "current_score": qs.current_score,
        "final_score": qs.final_score,
        "total_questions": qs.total_questions,
        "current_question_index": qs.current_question_index,
        "is_retry": qs.is_retry,
        "retry_of_session_id": str(qs.retry_of_session_id) if qs.retry_of_session_id else None,
        "adk_session_id": qs.adk_session_id,
        "started_at": qs.started_at.isoformat() if qs.started_at else None,
        "completed_at": qs.completed_at.isoformat() if qs.completed_at else None,
        "updated_at": qs.updated_at.isoformat() if qs.updated_at else None,
    }


def _answer_to_dict(a) -> Dict[str, Any]:
    return {
        "_id": str(a.id),
        "id": str(a.id),
        "session_id": str(a.session_id),
        "user_id": str(a.user_id),
        "question_number": a.question_number,
        "question_text": a.question_text,
        "user_answer": a.user_answer,
        "correct_answer": a.correct_answer,
        "is_correct": a.is_correct,
        "answered_at": a.answered_at.isoformat() if a.answered_at else None,
    }


def _note_to_dict(n) -> Dict[str, Any]:
    return {
        "_id": str(n.id),
        "id": str(n.id),
        "user_id": str(n.user_id),
        "document_name": n.document_name,
        "topic": n.topic,
        "insight": n.insight,
        "tutor_session_id": str(n.tutor_session_id) if n.tutor_session_id else None,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }


# ─── User CRUD ────────────────────────────────────────────────────────────────


async def create_user(
    username: str,
    email: str,
    hashed_password: str,
) -> Dict[str, Any]:
    """
    Insert a new user and return their dict.

    Raises:
        ValueError: if username or email already exists
    """
    async with get_session() as session:
        repo = UserRepository(session)
        try:
            user = await repo.create(username, email, hashed_password)
            await session.commit()
            return _user_to_dict(user)
        except IntegrityError as e:
            await session.rollback()
            raise ValueError(f"Username or email already exists: {e}")


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Look up a user by username.

    Returns:
        Dict with user data, or None
    """
    async with get_session() as session:
        repo = UserRepository(session)
        user = await repo.get_by_username(username)
        return _user_to_dict(user) if user else None


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Look up a user by their UUID string.

    Returns:
        Dict with user data, or None
    """
    async with get_session() as session:
        repo = UserRepository(session)
        user = await repo.get_by_id(uuid.UUID(user_id))
        return _user_to_dict(user) if user else None


# ─── Quiz CRUD ────────────────────────────────────────────────────────────────


async def start_quiz_session(
    user_id: str,
    session_id: str,
    document_name: str,
    questions_list: List[Dict[str, Any]],
) -> str:
    """
    Create a new quiz session in PostgreSQL.

    Args:
        user_id: UUID string from tool_context.state["current_user_id"]
        session_id: ADK session ID (stored as adk_session_id)
        document_name: Name of the PDF document
        questions_list: Array of question objects from generate_quiz

    Returns:
        str: PostgreSQL UUID of created session (as string)
    """
    async with get_session() as session:
        repo = QuizRepository(session)
        qs = await repo.start_session(
            user_id=uuid.UUID(user_id),
            document_name=document_name,
            questions_list=questions_list,
            adk_session_id=session_id,
        )
        await session.commit()
        return str(qs.id)


async def validate_session(quiz_session_id: str) -> Optional[Dict[str, Any]]:
    """
    Check if a session exists and is active (in_progress).

    Args:
        quiz_session_id: UUID string of the session

    Returns:
        Session dict if valid and in_progress, None otherwise
    """
    async with get_session() as session:
        repo = QuizRepository(session)
        qs = await repo.get_by_id(uuid.UUID(quiz_session_id))
        if qs and qs.status == "in_progress":
            return _quiz_session_to_dict(qs)
        return None


async def record_answer(
    quiz_session_id: str,
    question_number: int,
    question_text: str,
    user_answer: str,
    correct_answer: str,
    is_correct: bool,
) -> bool:
    """
    Record a user's answer to a quiz question.

    Also updates the session's current_question_index and current_score.

    Args:
        quiz_session_id: UUID string of the quiz session
        question_number: Question number (1-5)
        question_text: The question text (kept for signature compat — re-read from DB)
        user_answer: User's choice ("A", "B", "C", "D")
        correct_answer: Correct choice
        is_correct: Whether the answer was correct

    Returns:
        bool: True if successful
    """
    async with get_session() as session:
        qs_row = await session.get(QuizSession, uuid.UUID(quiz_session_id))
        if not qs_row:
            return False
        repo = QuizRepository(session)
        await repo.record_answer(
            session_id=uuid.UUID(quiz_session_id),
            user_id=qs_row.user_id,
            question_number=question_number,
            user_answer=user_answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
        )
        await session.commit()
        return True


async def update_session_progress(
    quiz_session_id: str,
    current_question_index: int,
    current_score: int,
) -> bool:
    async with get_session() as session:
        repo = QuizRepository(session)
        await repo.update_progress(
            session_id=uuid.UUID(quiz_session_id),
            current_question_index=current_question_index,
            current_score=current_score,
        )
        await session.commit()
        return True


async def complete_quiz_session(quiz_session_id: str) -> bool:
    """
    Mark a quiz session as completed.

    Args:
        quiz_session_id: UUID string of the session

    Returns:
        bool: True if successful
    """
    async with get_session() as session:
        repo = QuizRepository(session)
        result = await repo.complete_session(uuid.UUID(quiz_session_id))
        await session.commit()
        return result


async def abandon_quiz_session(quiz_session_id: str) -> bool:
    """
    Mark a quiz session as abandoned.

    Args:
        quiz_session_id: UUID string of the session

    Returns:
        bool: True if successful
    """
    async with get_session() as session:
        repo = QuizRepository(session)
        result = await repo.abandon_session(uuid.UUID(quiz_session_id))
        await session.commit()
        return result


async def get_quiz_history(
    user_id: str,
    limit: int = 10,
    document_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get user's quiz history.

    Args:
        user_id: User identifier
        limit: Maximum number of results
        document_name: Optional filter by document

    Returns:
        List of quiz session dictionaries
    """
    async with get_session() as session:
        repo = QuizRepository(session)
        sessions = await repo.get_history(
            user_id=uuid.UUID(user_id),
            limit=limit,
            document_name=document_name,
        )
        return [_quiz_session_to_dict(s) for s in sessions]


async def get_active_quiz(
    user_id: str,
    document_name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get user's active (in-progress) quiz session.

    Args:
        user_id: User identifier
        document_name: Optional filter by document

    Returns:
        Dict with quiz session data, or None if no active quiz
    """
    async with get_session() as session:
        repo = QuizRepository(session)
        qs = await repo.get_active_session(
            user_id=uuid.UUID(user_id),
            document_name=document_name,
        )
        return _quiz_session_to_dict(qs) if qs else None


async def get_last_completed_quiz(
    user_id: str,
    document_name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get the user's most recent completed quiz session.

    Args:
        user_id: User identifier
        document_name: Optional filter by document name

    Returns:
        Dict with quiz session data, or None if no completed quiz found
    """
    async with get_session() as session:
        repo = QuizRepository(session)
        qs = await repo.get_last_completed(user_id=uuid.UUID(user_id))
        if qs and document_name and qs.document_name != document_name:
            return None
        return _quiz_session_to_dict(qs) if qs else None


async def get_session_answers(quiz_session_id: str) -> List[Dict[str, Any]]:
    """
    Get all answers for a quiz session.

    Args:
        quiz_session_id: UUID string of the session

    Returns:
        List of answer dictionaries sorted by question_number
    """
    async with get_session() as session:
        repo = QuizRepository(session)
        answers = await repo.get_session_answers(uuid.UUID(quiz_session_id))
        return [_answer_to_dict(a) for a in answers]


async def get_quiz_attempts_by_doc(
    user_id: str,
    document_name: str,
) -> int:
    """
    Count quiz attempts for a specific document.

    Args:
        user_id: User identifier
        document_name: Name of the document

    Returns:
        Number of quiz attempts (completed + in_progress)
    """
    async with get_session() as session:
        repo = QuizRepository(session)
        sessions = await repo.get_attempts_by_doc(user_id=uuid.UUID(user_id))
        count = sum(1 for s in sessions if s.document_name == document_name)
        return count


# ─── Tutor CRUD ───────────────────────────────────────────────────────────────


async def start_tutor_session(
    user_id: str,
    session_id: str,
    document_name: str,
    topic: str,
    difficulty_level: str = "intermediate",
) -> str:
    """
    Create a new tutoring session in PostgreSQL.

    Args:
        user_id: UUID string from tool_context
        session_id: ADK session ID (stored as adk_session_id)
        document_name: Name of the PDF document being studied
        topic: The topic being tutored
        difficulty_level: beginner, intermediate, or advanced

    Returns:
        str: PostgreSQL UUID of created session (as string)
    """
    async with get_session() as session:
        repo = TutorRepository(session)
        ts = await repo.start_session(
            user_id=uuid.UUID(user_id),
            document_name=document_name,
            topic=topic,
            difficulty_level=difficulty_level,
            adk_session_id=session_id,
        )
        await session.commit()
        return str(ts.id)


async def end_tutor_session(tutor_session_id: str) -> bool:
    """
    Mark a tutoring session as ended.

    Args:
        tutor_session_id: UUID string of the tutor session

    Returns:
        bool: True if successful
    """
    async with get_session() as session:
        repo = TutorRepository(session)
        await repo.end_session(uuid.UUID(tutor_session_id))
        await session.commit()
        return True


async def update_tutor_session_history(
    user_id: str,
    session_id: str,
    history: List[Dict[str, str]],
) -> bool:
    """
    Replace the message history for a tutoring session.

    Resolves the PostgreSQL tutor_session UUID from the ADK session ID.

    Args:
        user_id: UUID string
        session_id: ADK session ID
        history: List of {"role": ..., "content": ...} dicts

    Returns:
        bool: True if successful
    """
    async with get_session() as session:
        repo = TutorRepository(session)
        ts = await repo.get_by_adk_session(
            user_id=uuid.UUID(user_id),
            adk_session_id=session_id,
        )
        if not ts:
            return False
        await repo.replace_history(ts.id, history)
        await session.commit()
        return True


async def get_tutor_session_history(
    user_id: str,
    document_name: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Retrieve past tutoring sessions for a user, optionally filtered by document.

    NOTE: This returns session metadata dicts (not message history).
    To get messages for a specific session use update_tutor_session_history.

    Args:
        user_id: User identifier
        document_name: Optional filter by document
        limit: Maximum number of sessions to return

    Returns:
        List of tutor session dicts (most recent first)
    """
    async with get_session() as session:
        from sqlalchemy import select
        from database.models import TutorSession as TutorSessionModel
        q = (
            select(TutorSessionModel)
            .where(TutorSessionModel.user_id == uuid.UUID(user_id))
            .order_by(TutorSessionModel.started_at.desc())
            .limit(limit)
        )
        if document_name:
            q = q.where(TutorSessionModel.document_name == document_name)
        result = await session.execute(q)
        sessions_list = list(result.scalars().all())
        return [
            {
                "_id": str(s.id),
                "id": str(s.id),
                "user_id": str(s.user_id),
                "document_name": s.document_name,
                "topic": s.topic,
                "difficulty_level": s.difficulty_level,
                "status": s.status,
                "adk_session_id": s.adk_session_id,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "ended_at": s.ended_at.isoformat() if s.ended_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in sessions_list
        ]


# ─── Notes CRUD ───────────────────────────────────────────────────────────────


async def save_tutor_note(
    user_id: str,
    session_id: str,
    document_name: str,
    topic: str,
    insight: str,
) -> str:
    """
    Save a learning note from a tutoring session.

    Attempts to resolve the PostgreSQL tutor_session UUID from the ADK session ID.

    Args:
        user_id: UUID string
        session_id: ADK session ID (used to look up the tutor_session FK)
        document_name: The document the note relates to
        topic: The topic the note relates to
        insight: The key insight to save

    Returns:
        str: PostgreSQL UUID of the saved note (as string)
    """
    async with get_session() as session:
        tutor_session_id = None
        try:
            repo_t = TutorRepository(session)
            ts = await repo_t.get_by_adk_session(
                user_id=uuid.UUID(user_id),
                adk_session_id=session_id,
            )
            if ts:
                tutor_session_id = ts.id
        except Exception:
            pass

        repo = NotesRepository(session)
        note = await repo.save_note(
            user_id=uuid.UUID(user_id),
            document_name=document_name,
            topic=topic,
            insight=insight,
            tutor_session_id=tutor_session_id,
        )
        await session.commit()
        return str(note.id)


async def get_tutor_notes(
    user_id: str,
    topic: Optional[str] = None,
    document_name: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Retrieve saved learning notes for a user.

    Args:
        user_id: User identifier
        topic: Optional filter by topic
        document_name: Optional filter by document
        limit: Maximum number of notes to return

    Returns:
        List of note dicts (most recent first)
    """
    async with get_session() as session:
        repo = NotesRepository(session)
        notes = await repo.get_notes(
            user_id=uuid.UUID(user_id),
            topic=topic,
            document_name=document_name,
            limit=limit,
        )
        return [_note_to_dict(n) for n in notes]
