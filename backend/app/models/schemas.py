from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
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
