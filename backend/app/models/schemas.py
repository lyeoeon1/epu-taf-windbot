from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: UUID
    message: str
    language: str = "en"


class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Chat"
    language: str = "en"


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    language: str
    created_at: datetime


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    metadata: dict = {}
    created_at: datetime


class IngestResponse(BaseModel):
    status: str
    chunks_created: int
    filename: str


class HealthResponse(BaseModel):
    status: str
    version: str


class QAPair(BaseModel):
    id: str
    question: str
    answer: str
    difficulty: str = "basic"
    tags: list[str] = []
    source: str = "general_knowledge"


class QACorpus(BaseModel):
    category: str
    language: str
    version: str = "1.0"
    generated_at: datetime
    pairs: list[QAPair]


class GlossaryEntry(BaseModel):
    id: str
    term_en: str
    term_vi: str
    definition_en: str
    definition_vi: str
    category: str
    abbreviation: Optional[str] = None
    related_terms: list[str] = []


class EvalResult(BaseModel):
    qa_id: str
    question: str
    expected_answer: str
    actual_answer: str
    accuracy: float
    completeness: float
    relevance: float
    clarity: float
    tone: float
    retrieval_hit: bool


class FeedbackRequest(BaseModel):
    session_id: UUID
    message_content: str
    feedback_tags: list[str] = []
    feedback_text: str = ""
