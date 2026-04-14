import asyncio

from fastapi import APIRouter, Depends
from supabase import Client

from app.dependencies import get_supabase
from app.models.schemas import (
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionResponse,
)
from app.services.supabase_retry import with_retry

router = APIRouter(prefix="/api/chat", tags=["sessions"])


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_session(
    body: ChatSessionCreate, supabase: Client = Depends(get_supabase)
):
    """Create a new chat session."""

    def _create():
        client = get_supabase()
        return (
            client.table("chat_sessions")
            .insert({"title": body.title, "language": body.language})
            .execute()
        )

    result = await asyncio.to_thread(with_retry, _create)
    return result.data[0]


@router.get(
    "/sessions/{session_id}/messages",
    response_model=list[ChatMessageResponse],
)
async def get_messages(
    session_id: str, supabase: Client = Depends(get_supabase)
):
    """Get all messages for a chat session."""

    def _fetch():
        client = get_supabase()
        return (
            client.table("chat_messages")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at")
            .execute()
        )

    result = await asyncio.to_thread(with_retry, _fetch)
    return result.data
