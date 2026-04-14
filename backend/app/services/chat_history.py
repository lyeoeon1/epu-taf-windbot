import asyncio

from supabase import Client

from app.services.supabase_retry import with_retry


async def save_message(
    supabase: Client,
    session_id: str,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> dict:
    """Save a chat message to Supabase."""

    def _save():
        from app.dependencies import get_supabase
        client = get_supabase()
        return (
            client.table("chat_messages")
            .insert(
                {
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "metadata": metadata or {},
                }
            )
            .execute()
        )

    result = await asyncio.to_thread(with_retry, _save)
    return result.data[0]


async def get_session_messages(
    supabase: Client, session_id: str, limit: int = 40
) -> list[dict]:
    """Get recent messages for a chat session, ordered by creation time."""

    def _fetch():
        from app.dependencies import get_supabase
        client = get_supabase()
        return (
            client.table("chat_messages")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

    result = await asyncio.to_thread(with_retry, _fetch)
    # Reverse to chronological order
    return list(reversed(result.data))
