"""
Models/models.py — Pydantic data models for structured LLM output and application data.

Used as response_schema in Gemini GenerateContentConfig for two-pass generation.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ─── Quiz Models ──────────────────────────────────────────────────────────────

class QuestionOptions(BaseModel):
    A: str
    B: str
    C: str
    D: str


class QuizQuestion(BaseModel):
    question_number: int
    question: str
    options: QuestionOptions
    correct_answer: str  # "A", "B", "C", or "D"
    hint: Optional[str] = None
    explanation: Optional[str] = None


class Quiz(BaseModel):
    document_name: str
    questions: List[QuizQuestion]


# ─── Summary Models ───────────────────────────────────────────────────────────

class Summary(BaseModel):
    summary_type: str  # "brief", "detailed", or "key-points"
    summary: str
    key_takeaways: List[str] = Field(default_factory=list)


# ─── Flashcard Models ─────────────────────────────────────────────────────────

class Flashcard(BaseModel):
    front: str
    back: str
    category: Optional[str] = None
    difficulty: Optional[str] = None  # "easy", "medium", "hard"


class FlashcardList(BaseModel):
    document_name: str
    flashcards: List[Flashcard]


# ─── Tutoring Models ──────────────────────────────────────────────────────────

class TutoringMessage(BaseModel):
    role: str  # "tutor" or "student"
    content: str
    timestamp: Optional[str] = None


class TutoringOpening(BaseModel):
    introduction: str
    opening_question: str
    suggested_topics: List[str] = Field(default_factory=list)


class TutoringSession(BaseModel):
    topic: str
    difficulty_level: str
    history: List[TutoringMessage] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


# ─── DB Serialization Models ──────────────────────────────────────────────────

class QuizSessionDB(BaseModel):
    id: str
    user_id: str
    document_name: str
    status: str
    current_score: int = 0
    final_score: Optional[int] = None
    total_questions: int = 5
    current_question_index: int = 0
    is_retry: bool = False
    retry_of_session_id: Optional[str] = None
    adk_session_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class QuizAnswerDB(BaseModel):
    id: str
    session_id: str
    user_id: str
    question_number: int
    question_text: str
    user_answer: str
    correct_answer: str
    is_correct: bool
    answered_at: Optional[datetime] = None


# ─── Learning Notes Model ─────────────────────────────────────────────────────

class LearningNote(BaseModel):
    id: str
    user_id: str
    document_name: str
    topic: str
    insight: str
    tutor_session_id: Optional[str] = None
    created_at: Optional[datetime] = None


# ─── Resource Models ──────────────────────────────────────────────────────────

class ResourceRanking(BaseModel):
    reason: str
    relevance_score: float


class ResourceSuggestion(BaseModel):
    document_name: str
    relevance_score: float
    reason: str
