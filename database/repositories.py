"""
database/repositories.py — Repository pattern for LMS application data.

Each repository class takes an AsyncSession at construction time and exposes
typed async methods. All repositories are stateless beyond the session reference.

Repositories:
  UserRepository   — user account CRUD
  QuizRepository   — quiz sessions, questions, answers, history, retry
  TutorRepository  — tutor sessions, message append / replace, history
  NotesRepository  — learning notes save / retrieve

All methods are async. Call from async context or via asyncio.run_coroutine_threadsafe().
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    CommunityItem,
    ItemUpvote,
    LearningNote,
    QuizAnswer,
    QuizQuestion,
    QuizSession,
    TutorMessage,
    TutorSession,
    User,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────────────────────
# UserRepository
# ─────────────────────────────────────────────────────────────────────────────


class UserRepository:
    """CRUD for the `users` table."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def create(
        self,
        username: str,
        email: str,
        hashed_password: str,
    ) -> User:
        """
        Insert a new user row.
        Raises sqlalchemy.exc.IntegrityError if username or email already exists.
        """
        user = User(
            username=username.lower().strip(),
            email=email.lower().strip(),
            hashed_password=hashed_password,
        )
        self._s.add(user)
        await self._s.flush()  # assign PK without committing
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return await self._s.get(User, user_id)

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self._s.execute(
            select(User).where(User.username == username.lower().strip())
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._s.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def username_exists(self, username: str) -> bool:
        result = await self._s.execute(
            select(func.count())
            .select_from(User)
            .where(User.username == username.lower().strip())
        )
        return (result.scalar() or 0) > 0

    async def email_exists(self, email: str) -> bool:
        result = await self._s.execute(
            select(func.count())
            .select_from(User)
            .where(User.email == email.lower().strip())
        )
        return (result.scalar() or 0) > 0

    async def set_active(self, user_id: uuid.UUID, active: bool) -> None:
        await self._s.execute(
            update(User).where(User.id == user_id).values(is_active=active)
        )


# ─────────────────────────────────────────────────────────────────────────────
# QuizRepository
# ─────────────────────────────────────────────────────────────────────────────


class QuizRepository:
    """
    Manages quiz_sessions, quiz_questions, and quiz_answers.

    Design decisions:
    - start_session() flushes to get the session PK before inserting questions.
    - record_answer() also increments current_score atomically via UPDATE.
    - complete_session() sets final_score = current_score and stamps completed_at.
    - Retry sessions are created via start_retry_session() which sets the FK.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ── Session lifecycle ──────────────────────────────────────────────────

    async def start_session(
        self,
        user_id: uuid.UUID,
        document_name: str,
        questions_list: List[Dict[str, Any]],
        adk_session_id: Optional[str] = None,
    ) -> QuizSession:
        """
        Create a new quiz session and insert all question rows.

        questions_list format (from Gemini structured output / tool_context.state):
        [
          {
            "question": "...",
            "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
            "correct_answer": "B",
            "hint": "...",
            "explanation": "...",
            "question_number": 1,   # optional — we use enumerate if missing
          },
          ...
        ]
        """
        qs = QuizSession(
            user_id=user_id,
            document_name=document_name,
            total_questions=len(questions_list),
            adk_session_id=adk_session_id,
        )
        self._s.add(qs)
        await self._s.flush()  # need qs.id before inserting questions

        for i, q in enumerate(questions_list, start=1):
            opts = q.get("options", {})
            qq = QuizQuestion(
                session_id=qs.id,
                question_number=q.get("question_number", i),
                question_text=q.get("question", ""),
                option_a=opts.get("A", ""),
                option_b=opts.get("B", ""),
                option_c=opts.get("C", ""),
                option_d=opts.get("D", ""),
                correct_answer=(q.get("correct_answer") or "A")[0].upper(),
                hint=q.get("hint"),
                explanation=q.get("explanation"),
            )
            self._s.add(qq)

        return qs

    async def start_retry_session(
        self,
        user_id: uuid.UUID,
        original_session_id: uuid.UUID,
        document_name: str,
        questions_list: List[Dict[str, Any]],
        adk_session_id: Optional[str] = None,
    ) -> QuizSession:
        """Create a new session flagged as a retry of original_session_id."""
        qs = await self.start_session(
            user_id=user_id,
            document_name=document_name,
            questions_list=questions_list,
            adk_session_id=adk_session_id,
        )
        qs.is_retry = True
        qs.retry_of_session_id = original_session_id
        return qs

    async def get_by_id(self, session_id: uuid.UUID) -> Optional[QuizSession]:
        return await self._s.get(QuizSession, session_id)

    async def get_active_session(
        self,
        user_id: uuid.UUID,
        document_name: Optional[str] = None,
    ) -> Optional[QuizSession]:
        """Return the most recent in_progress session for a user (optionally by document)."""
        q = (
            select(QuizSession)
            .where(QuizSession.user_id == user_id, QuizSession.status == "in_progress")
            .order_by(QuizSession.started_at.desc())
            .limit(1)
        )
        if document_name:
            q = q.where(QuizSession.document_name == document_name)
        result = await self._s.execute(q)
        return result.scalar_one_or_none()

    async def complete_session(self, session_id: uuid.UUID) -> bool:
        """Mark a session as completed, stamp final_score = current_score."""
        result = await self._s.execute(
            select(QuizSession).where(QuizSession.id == session_id)
        )
        qs = result.scalar_one_or_none()
        if not qs:
            return False
        qs.status = "completed"
        qs.final_score = qs.current_score
        qs.completed_at = _utcnow()
        qs.updated_at = _utcnow()
        return True

    async def abandon_session(self, session_id: uuid.UUID) -> bool:
        await self._s.execute(
            update(QuizSession)
            .where(QuizSession.id == session_id)
            .values(status="abandoned", updated_at=_utcnow())
        )
        return True

    async def update_progress(
        self,
        session_id: uuid.UUID,
        current_question_index: int,
        current_score: int,
    ) -> None:
        await self._s.execute(
            update(QuizSession)
            .where(QuizSession.id == session_id)
            .values(
                current_question_index=current_question_index,
                current_score=current_score,
                updated_at=_utcnow(),
            )
        )

    # ── History / analytics ────────────────────────────────────────────────

    async def get_history(
        self,
        user_id: uuid.UUID,
        limit: int = 10,
        document_name: Optional[str] = None,
    ) -> List[QuizSession]:
        """Return sessions ordered newest-first."""
        q = (
            select(QuizSession)
            .where(QuizSession.user_id == user_id)
            .order_by(QuizSession.started_at.desc())
            .limit(limit)
        )
        if document_name:
            q = q.where(QuizSession.document_name == document_name)
        result = await self._s.execute(q)
        return list(result.scalars().all())

    async def get_last_completed(self, user_id: uuid.UUID) -> Optional[QuizSession]:
        result = await self._s.execute(
            select(QuizSession)
            .where(
                QuizSession.user_id == user_id,
                QuizSession.status == "completed",
            )
            .order_by(QuizSession.completed_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_attempts_by_doc(
        self, user_id: uuid.UUID, limit: int = 50
    ) -> List[QuizSession]:
        """Return completed sessions for analytics grouping by document."""
        result = await self._s.execute(
            select(QuizSession)
            .where(
                QuizSession.user_id == user_id,
                QuizSession.status == "completed",
            )
            .order_by(QuizSession.completed_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # ── Answers ────────────────────────────────────────────────────────────

    async def record_answer(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        question_number: int,
        user_answer: str,
        correct_answer: str,
        is_correct: bool,
    ) -> QuizAnswer:
        """
        Insert an answer row and atomically increment session score if correct.
        Looks up the question row to satisfy the FK constraint.
        """
        # Look up question row (needed for FK)
        q_result = await self._s.execute(
            select(QuizQuestion).where(
                QuizQuestion.session_id == session_id,
                QuizQuestion.question_number == question_number,
            )
        )
        question = q_result.scalar_one()

        answer = QuizAnswer(
            session_id=session_id,
            question_id=question.id,
            user_id=user_id,
            question_number=question_number,
            question_text=question.question_text,
            user_answer=user_answer.upper(),
            correct_answer=correct_answer.upper(),
            is_correct=is_correct,
        )
        self._s.add(answer)

        # Atomically update session progress
        await self._s.execute(
            update(QuizSession)
            .where(QuizSession.id == session_id)
            .values(
                current_question_index=question_number,
                current_score=QuizSession.current_score + (1 if is_correct else 0),
                updated_at=_utcnow(),
            )
        )
        return answer

    async def get_session_answers(self, session_id: uuid.UUID) -> List[QuizAnswer]:
        result = await self._s.execute(
            select(QuizAnswer)
            .where(QuizAnswer.session_id == session_id)
            .order_by(QuizAnswer.question_number.asc())
        )
        return list(result.scalars().all())

    async def get_session_questions(self, session_id: uuid.UUID) -> List[QuizQuestion]:
        result = await self._s.execute(
            select(QuizQuestion)
            .where(QuizQuestion.session_id == session_id)
            .order_by(QuizQuestion.question_number.asc())
        )
        return list(result.scalars().all())


# ─────────────────────────────────────────────────────────────────────────────
# TutorRepository
# ─────────────────────────────────────────────────────────────────────────────


class TutorRepository:
    """
    Manages tutor_sessions and tutor_messages.

    Two message-persistence strategies are provided:
    - append_message()   — used by ask_followup_tool (adds one message at a time)
    - replace_history()  — backward-compat with in-memory state dict pattern
                           (replaces all messages in bulk)
    """

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ── Session lifecycle ──────────────────────────────────────────────────

    async def start_session(
        self,
        user_id: uuid.UUID,
        document_name: str,
        topic: str,
        difficulty_level: str = "intermediate",
        adk_session_id: Optional[str] = None,
    ) -> TutorSession:
        ts = TutorSession(
            user_id=user_id,
            document_name=document_name,
            topic=topic,
            difficulty_level=difficulty_level,
            adk_session_id=adk_session_id,
        )
        self._s.add(ts)
        await self._s.flush()
        return ts

    async def get_by_id(self, session_id: uuid.UUID) -> Optional[TutorSession]:
        return await self._s.get(TutorSession, session_id)

    async def get_active_session(
        self, user_id: uuid.UUID, document_name: Optional[str] = None
    ) -> Optional[TutorSession]:
        q = (
            select(TutorSession)
            .where(TutorSession.user_id == user_id, TutorSession.status == "active")
            .order_by(TutorSession.started_at.desc())
            .limit(1)
        )
        if document_name:
            q = q.where(TutorSession.document_name == document_name)
        result = await self._s.execute(q)
        return result.scalar_one_or_none()

    async def get_by_adk_session(
        self, user_id: uuid.UUID, adk_session_id: str
    ) -> Optional[TutorSession]:
        result = await self._s.execute(
            select(TutorSession)
            .where(
                TutorSession.user_id == user_id,
                TutorSession.adk_session_id == adk_session_id,
            )
            .order_by(TutorSession.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def end_session(self, session_id: uuid.UUID) -> None:
        await self._s.execute(
            update(TutorSession)
            .where(TutorSession.id == session_id)
            .values(status="ended", ended_at=_utcnow(), updated_at=_utcnow())
        )

    # ── Message management ─────────────────────────────────────────────────

    async def append_message(
        self,
        session_id: uuid.UUID,
        role: str,
        content: str,
    ) -> TutorMessage:
        """
        Append one message to a session.
        message_order is determined by the current message count (0-based).
        """
        count_result = await self._s.execute(
            select(func.count())
            .select_from(TutorMessage)
            .where(TutorMessage.session_id == session_id)
        )
        order = count_result.scalar() or 0

        msg = TutorMessage(
            session_id=session_id,
            role=role,
            content=content,
            message_order=order,
        )
        self._s.add(msg)

        # Touch updated_at on parent session
        await self._s.execute(
            update(TutorSession)
            .where(TutorSession.id == session_id)
            .values(updated_at=_utcnow())
        )
        return msg

    async def replace_history(
        self,
        session_id: uuid.UUID,
        history: List[Dict[str, str]],
    ) -> None:
        """
        Delete all existing messages for a session and re-insert from history list.

        Used by update_tutor_session_history() in db_handler.py which receives
        the full in-memory history dict from ask_followup_tool.

        history format: [{"role": "tutor"|"student", "content": "..."}, ...]
        """
        await self._s.execute(
            sa_delete(TutorMessage).where(TutorMessage.session_id == session_id)
        )
        for i, msg in enumerate(history):
            role = msg.get("role", "tutor")
            if role not in ("tutor", "student"):
                role = "tutor"
            self._s.add(
                TutorMessage(
                    session_id=session_id,
                    role=role,
                    content=msg.get("content", ""),
                    message_order=i,
                )
            )
        await self._s.execute(
            update(TutorSession)
            .where(TutorSession.id == session_id)
            .values(updated_at=_utcnow())
        )

    async def get_history(self, session_id: uuid.UUID) -> List[Dict[str, str]]:
        """
        Return ordered message history as a list of dicts.
        """
        result = await self._s.execute(
            select(TutorMessage)
            .where(TutorMessage.session_id == session_id)
            .order_by(TutorMessage.message_order.asc())
        )
        return [{"role": m.role, "content": m.content} for m in result.scalars()]


# ─────────────────────────────────────────────────────────────────────────────
# NotesRepository
# ─────────────────────────────────────────────────────────────────────────────


class NotesRepository:
    """CRUD for learning_notes table."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def save_note(
        self,
        user_id: uuid.UUID,
        document_name: str,
        topic: str,
        insight: str,
        tutor_session_id: Optional[uuid.UUID] = None,
    ) -> LearningNote:
        note = LearningNote(
            user_id=user_id,
            document_name=document_name,
            topic=topic,
            insight=insight,
            tutor_session_id=tutor_session_id,
        )
        self._s.add(note)
        await self._s.flush()
        return note

    async def get_notes(
        self,
        user_id: uuid.UUID,
        topic: Optional[str] = None,
        document_name: Optional[str] = None,
        limit: int = 20,
    ) -> List[LearningNote]:
        q = (
            select(LearningNote)
            .where(LearningNote.user_id == user_id)
            .order_by(LearningNote.created_at.desc())
            .limit(limit)
        )
        if topic:
            q = q.where(LearningNote.topic == topic)
        if document_name:
            q = q.where(LearningNote.document_name == document_name)
        result = await self._s.execute(q)
        return list(result.scalars().all())

    async def delete_note(self, note_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a note only if it belongs to the requesting user."""
        result = await self._s.execute(
            sa_delete(LearningNote)
            .where(LearningNote.id == note_id, LearningNote.user_id == user_id)
            .returning(LearningNote.id)
        )
        return result.fetchone() is not None


# ─────────────────────────────────────────────────────────────────────────────
# CommunityRepository
# ─────────────────────────────────────────────────────────────────────────────


class CommunityRepository:
    """CRUD for community_items and item_upvotes tables."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def publish_item(
        self,
        author_id: uuid.UUID,
        item_type: str,
        title: str,
        content_json: str,
        description: Optional[str] = None,
    ) -> CommunityItem:
        """Publish a new quiz or flashcard set to the community."""
        item = CommunityItem(
            author_id=author_id,
            item_type=item_type,
            title=title,
            description=description,
            content_json=content_json,
        )
        self._s.add(item)
        await self._s.flush()
        return item

    async def get_items(
        self,
        item_type: Optional[str] = None,
        sort_by: str = "recent",  # "recent" or "popular"
        limit: int = 20,
        offset: int = 0,
    ) -> List[CommunityItem]:
        """Fetch community items, optionally filtered and sorted."""
        q = select(CommunityItem)
        if item_type:
            q = q.where(CommunityItem.item_type == item_type)

        if sort_by == "popular":
            q = q.order_by(
                CommunityItem.upvotes.desc(), CommunityItem.created_at.desc()
            )
        else:
            q = q.order_by(CommunityItem.created_at.desc())

        q = q.offset(offset).limit(limit)
        result = await self._s.execute(q)
        return list(result.scalars().all())

    async def get_item_by_id(self, item_id: uuid.UUID) -> Optional[CommunityItem]:
        return await self._s.get(CommunityItem, item_id)

    async def toggle_upvote(self, user_id: uuid.UUID, item_id: uuid.UUID) -> bool:
        """
        Toggles an upvote for a user on a specific item.
        Returns True if upvoted, False if removed.
        """
        # Check if upvote exists
        existing = await self._s.execute(
            select(ItemUpvote).where(
                ItemUpvote.user_id == user_id, ItemUpvote.item_id == item_id
            )
        )
        upvote = existing.scalar_one_or_none()

        if upvote:
            # Remove upvote
            await self._s.delete(upvote)
            # Decrement denormalized counter
            await self._s.execute(
                update(CommunityItem)
                .where(CommunityItem.id == item_id)
                .values(upvotes=CommunityItem.upvotes - 1)
            )
            return False
        else:
            # Add upvote
            new_upvote = ItemUpvote(user_id=user_id, item_id=item_id)
            self._s.add(new_upvote)
            # Increment denormalized counter
            await self._s.execute(
                update(CommunityItem)
                .where(CommunityItem.id == item_id)
                .values(upvotes=CommunityItem.upvotes + 1)
            )
            return True


# ─────────────────────────────────────────────────────────────────────────────
# LeaderboardRepository
# ─────────────────────────────────────────────────────────────────────────────


class LeaderboardRepository:
    """Aggregates completed quiz scores to produce a ranked leaderboard."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_top_by_quiz_score(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Return the top `limit` users ranked by total quiz score (sum of final_score
        across all completed sessions).  Each entry includes rank, username,
        total_score, and quizzes_completed.
        """
        stmt = (
            select(
                User.username,
                func.coalesce(func.sum(QuizSession.final_score), 0).label(
                    "total_score"
                ),
                func.count(QuizSession.id).label("quizzes_completed"),
            )
            .join(QuizSession, QuizSession.user_id == User.id)
            .where(QuizSession.status == "completed")
            .group_by(User.id, User.username)
            .order_by(func.sum(QuizSession.final_score).desc())
            .limit(limit)
        )
        result = await self._s.execute(stmt)
        rows = result.all()
        return [
            {
                "rank": idx + 1,
                "username": row.username,
                "total_score": int(row.total_score),
                "quizzes_completed": int(row.quizzes_completed),
            }
            for idx, row in enumerate(rows)
        ]

    async def get_user_rank(self, user_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Return the rank, total_score, and quizzes_completed for a specific user.
        Returns None if the user has no completed quizzes.
        """
        # Subquery: all users with completed quizzes
        sub = (
            select(
                QuizSession.user_id,
                func.coalesce(func.sum(QuizSession.final_score), 0).label(
                    "total_score"
                ),
                func.count(QuizSession.id).label("quizzes_completed"),
            )
            .where(QuizSession.status == "completed")
            .group_by(QuizSession.user_id)
            .subquery()
        )

        # Rank via ROW_NUMBER ordered by total_score DESC
        ranked = select(
            sub.c.user_id,
            sub.c.total_score,
            sub.c.quizzes_completed,
            func.row_number().over(order_by=sub.c.total_score.desc()).label("rank"),
        ).subquery()

        stmt = (
            select(
                ranked.c.rank,
                ranked.c.total_score,
                ranked.c.quizzes_completed,
                User.username,
            )
            .join(User, User.id == ranked.c.user_id)
            .where(ranked.c.user_id == user_id)
        )
        result = await self._s.execute(stmt)
        row = result.one_or_none()
        if not row:
            return None
        return {
            "rank": int(row.rank),
            "username": row.username,
            "total_score": int(row.total_score),
            "quizzes_completed": int(row.quizzes_completed),
        }
