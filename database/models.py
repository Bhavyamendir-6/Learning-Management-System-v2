"""
database/models.py — SQLAlchemy 2.0 async ORM models for LMS Agent UI.

Tables:
  users            — application user accounts
  quiz_sessions    — quiz state machine
  quiz_questions   — normalized per-question data (extracted from embedded array)
  quiz_answers     — individual answer records
  tutor_sessions   — tutoring session metadata
  tutor_messages   — ordered message log
  learning_notes   — saved insights from tutoring

All timestamps are stored as TIMESTAMPTZ (UTC-aware).
All primary keys are UUIDs (gen_random_uuid() on the PG side; uuid4() in Python).
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Shared declarative base for all LMS application models."""

    pass


# ─────────────────────────────────────────────────────────────────────────────
# users
# ─────────────────────────────────────────────────────────────────────────────


class User(Base):
    """
    Application user account.
    Stored in PostgreSQL `users` table.
    """

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint(
            "char_length(username) BETWEEN 3 AND 50", name="ck_users_username_len"
        ),
        CheckConstraint(
            "email ~* '^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$'", name="ck_users_email_fmt"
        ),
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
        Index("idx_users_created", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    quiz_sessions: Mapped[List["QuizSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    quiz_answers: Mapped[List["QuizAnswer"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    tutor_sessions: Mapped[List["TutorSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    learning_notes: Mapped[List["LearningNote"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    community_items: Mapped[List["CommunityItem"]] = relationship(
        back_populates="author", cascade="all, delete-orphan", passive_deletes=True
    )
    item_upvotes: Mapped[List["ItemUpvote"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"


# ─────────────────────────────────────────────────────────────────────────────
# quiz_sessions
# ─────────────────────────────────────────────────────────────────────────────


class QuizSession(Base):
    """
    Quiz session state machine.
    Stored in PostgreSQL `quiz_sessions` table.
    status:  in_progress | completed | abandoned
    """

    __tablename__ = "quiz_sessions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('in_progress', 'completed', 'abandoned')",
            name="ck_qs_status",
        ),
        CheckConstraint("current_score >= 0", name="ck_qs_score_nonneg"),
        CheckConstraint("total_questions > 0", name="ck_qs_total_positive"),
        # Partial indexes (Neon-friendly — smaller index footprint)
        Index("idx_qs_user_id", "user_id"),
        Index("idx_qs_user_status", "user_id", "status"),
        Index("idx_qs_user_doc", "user_id", "document_name"),
        Index("idx_qs_started_at", "started_at"),
        Index("idx_qs_completed_at", "completed_at"),
        Index("idx_qs_adk_session", "adk_session_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Links to the ADK session that spawned this quiz (from tool_context.state["session_id"])
    adk_session_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="in_progress"
    )
    current_question_index: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    current_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    final_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_retry: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Self-referential FK for retry chains
    retry_of_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="quiz_sessions")
    questions: Mapped[List["QuizQuestion"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="QuizQuestion.question_number",
    )
    answers: Mapped[List["QuizAnswer"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    # Self-referential: the session this is a retry of
    retry_of: Mapped[Optional["QuizSession"]] = relationship(
        "QuizSession",
        foreign_keys=[retry_of_session_id],
        remote_side="QuizSession.id",
    )

    def __repr__(self) -> str:
        return (
            f"<QuizSession id={self.id} user_id={self.user_id} "
            f"doc={self.document_name!r} status={self.status!r}>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# quiz_questions
# ─────────────────────────────────────────────────────────────────────────────


class QuizQuestion(Base):
    """
    Individual MCQ question linked to a quiz session.
    Normalized into its own table for analytics and retry-targeting.
    """

    __tablename__ = "quiz_questions"
    __table_args__ = (
        UniqueConstraint("session_id", "question_number", name="uq_qq_session_qnum"),
        CheckConstraint("question_number > 0", name="ck_qq_qnum_positive"),
        CheckConstraint(
            "correct_answer IN ('A','B','C','D')", name="ck_qq_correct_answer"
        ),
        Index("idx_qq_session_id", "session_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    option_a: Mapped[str] = mapped_column(Text, nullable=False)
    option_b: Mapped[str] = mapped_column(Text, nullable=False)
    option_c: Mapped[str] = mapped_column(Text, nullable=False)
    option_d: Mapped[str] = mapped_column(Text, nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(1), nullable=False)
    hint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    session: Mapped["QuizSession"] = relationship(back_populates="questions")
    answer: Mapped[Optional["QuizAnswer"]] = relationship(
        back_populates="question", uselist=False
    )

    def __repr__(self) -> str:
        return (
            f"<QuizQuestion id={self.id} session_id={self.session_id} "
            f"q#{self.question_number}>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# quiz_answers
# ─────────────────────────────────────────────────────────────────────────────


class QuizAnswer(Base):
    """
    Individual quiz answer record.
    Stored in PostgreSQL `quiz_answers` table.
    question_text is denormalized for query convenience (avoids JOIN in history view).
    """

    __tablename__ = "quiz_answers"
    __table_args__ = (
        UniqueConstraint("session_id", "question_number", name="uq_qa_session_qnum"),
        CheckConstraint(
            "user_answer    IN ('A','B','C','D')", name="ck_qa_user_answer"
        ),
        CheckConstraint(
            "correct_answer IN ('A','B','C','D')", name="ck_qa_correct_answer"
        ),
        Index("idx_qa_session_id", "session_id"),
        Index("idx_qa_user_id", "user_id"),
        Index("idx_qa_answered_at", "answered_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    user_answer: Mapped[str] = mapped_column(String(1), nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(1), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    session: Mapped["QuizSession"] = relationship(back_populates="answers")
    question: Mapped["QuizQuestion"] = relationship(back_populates="answer")
    user: Mapped["User"] = relationship(back_populates="quiz_answers")

    def __repr__(self) -> str:
        return (
            f"<QuizAnswer id={self.id} q#{self.question_number} "
            f"correct={self.is_correct}>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# tutor_sessions
# ─────────────────────────────────────────────────────────────────────────────


class TutorSession(Base):
    """
    Tutoring session metadata (messages stored separately in tutor_messages).
    Stored in PostgreSQL `tutor_sessions` table.
    status: active | ended
    """

    __tablename__ = "tutor_sessions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'ended')",
            name="ck_ts_status",
        ),
        CheckConstraint(
            "difficulty_level IN ('beginner', 'intermediate', 'advanced')",
            name="ck_ts_difficulty",
        ),
        Index("idx_ts_user_id", "user_id"),
        Index("idx_ts_user_status", "user_id", "status"),
        Index("idx_ts_user_doc", "user_id", "document_name"),
        Index("idx_ts_started_at", "started_at"),
        Index("idx_ts_adk_session", "adk_session_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    adk_session_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_name: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="intermediate"
    )
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="active")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="tutor_sessions")
    messages: Mapped[List["TutorMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TutorMessage.message_order",
    )
    notes: Mapped[List["LearningNote"]] = relationship(back_populates="tutor_session")

    def __repr__(self) -> str:
        return (
            f"<TutorSession id={self.id} user_id={self.user_id} "
            f"topic={self.topic!r} status={self.status!r}>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# tutor_messages
# ─────────────────────────────────────────────────────────────────────────────


class TutorMessage(Base):
    """
    Ordered message in a tutoring session.
    Stored in PostgreSQL `tutor_messages` table.
    message_order is 0-based, guaranteeing deterministic retrieval order.
    """

    __tablename__ = "tutor_messages"
    __table_args__ = (
        UniqueConstraint("session_id", "message_order", name="uq_tm_session_order"),
        CheckConstraint("role IN ('tutor', 'student')", name="ck_tm_role"),
        Index("idx_tm_session_id", "session_id"),
        Index("idx_tm_session_order", "session_id", "message_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tutor_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(10), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    session: Mapped["TutorSession"] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return (
            f"<TutorMessage id={self.id} session_id={self.session_id} "
            f"role={self.role!r} order={self.message_order}>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# learning_notes
# ─────────────────────────────────────────────────────────────────────────────


class LearningNote(Base):
    """
    User-saved insight from a tutoring session.
    Stored in PostgreSQL `learning_notes` table.
    tutor_session_id is nullable (notes can exist without a linked tutor session).
    """

    __tablename__ = "learning_notes"
    __table_args__ = (
        Index("idx_ln_user_id", "user_id"),
        Index("idx_ln_user_doc", "user_id", "document_name"),
        Index("idx_ln_user_topic", "user_id", "topic"),
        Index("idx_ln_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    tutor_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tutor_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    document_name: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    insight: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="learning_notes")
    tutor_session: Mapped[Optional["TutorSession"]] = relationship(
        back_populates="notes"
    )

    def __repr__(self) -> str:
        return (
            f"<LearningNote id={self.id} user_id={self.user_id} topic={self.topic!r}>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# uploaded_documents
# ─────────────────────────────────────────────────────────────────────────────


class UploadedDocument(Base):
    """
    Metadata for a document a user has uploaded.
    Used to show history in the sidebar UI.
    """

    __tablename__ = "uploaded_documents"
    __table_args__ = (
        UniqueConstraint("user_id", "filename", name="uq_ud_user_filename"),
        Index("idx_ud_user_id", "user_id"),
        Index("idx_ud_uploaded_at", "uploaded_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<UploadedDocument id={self.id} filename={self.filename!r}>"


# ─────────────────────────────────────────────────────────────────────────────
# community_items
# ─────────────────────────────────────────────────────────────────────────────


class CommunityItem(Base):
    """
    A crowdsourced flashcard set or quiz published by a user.
    """

    __tablename__ = "community_items"
    __table_args__ = (
        CheckConstraint("item_type IN ('quiz', 'flashcard_set')", name="ck_ci_type"),
        Index("idx_ci_item_type", "item_type"),
        Index("idx_ci_created_at", "created_at"),
        Index("idx_ci_author_id", "author_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_json: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # Stores the actual quiz/flashcard JSON
    upvotes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    author: Mapped["User"] = relationship(back_populates="community_items")
    item_upvotes_list: Mapped[List["ItemUpvote"]] = relationship(
        back_populates="item", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:
        return (
            f"<CommunityItem id={self.id} type={self.item_type!r} title={self.title!r}>"
        )


# ─────────────────────────────────────────────────────────────────────────────
# item_upvotes
# ─────────────────────────────────────────────────────────────────────────────


class ItemUpvote(Base):
    """
    Tracks which user upvoted which community item.
    """

    __tablename__ = "item_upvotes"
    __table_args__ = (
        UniqueConstraint("user_id", "item_id", name="uq_iu_user_item"),
        Index("idx_iu_item_id", "item_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("community_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="item_upvotes")
    item: Mapped["CommunityItem"] = relationship(back_populates="item_upvotes_list")

    def __repr__(self) -> str:
        return f"<ItemUpvote user={self.user_id} item={self.item_id}>"
