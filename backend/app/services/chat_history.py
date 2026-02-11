from supabase import Client


async def save_message(
    supabase: Client,
    session_id: str,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> dict:
    """Save a chat message to Supabase."""
    result = (
        supabase.table("chat_messages")
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
    return result.data[0]


async def get_session_messages(
    supabase: Client, session_id: str
) -> list[dict]:
    """Get all messages for a chat session, ordered by creation time."""
    result = (
        supabase.table("chat_messages")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )
    return result.data
