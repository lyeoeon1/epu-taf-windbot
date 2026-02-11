from fastapi import APIRouter, Depends
from supabase import Client

from app.dependencies import get_supabase
from app.models.schemas import (
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
)

router = APIRouter(prefix="/api/chat", tags=["sessions"])


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    body: ChatSessionCreate, supabase: Client = Depends(get_supabase)
):
    """Create a new chat session."""
    result = (
        supabase.table("chat_sessions")
        .insert({"title": body.title, "language": body.language})
        .execute()
    )
    return result.data[0]


@router.get(
    "/sessions/{session_id}/messages",
    response_model=list[ChatMessageResponse],
)
async def get_messages(
    session_id: str, supabase: Client = Depends(get_supabase)
):
    """Get all messages for a chat session."""
    result = (
        supabase.table("chat_messages")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )
    return result.data
