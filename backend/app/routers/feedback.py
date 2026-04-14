import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.dependencies import get_supabase
from app.models.schemas import FeedbackRequest
from app.services.global_corrections import promote_correction
from app.services.supabase_retry import with_retry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["feedback"])

# Tags that indicate the user validates the answer (and any corrections in it)
POSITIVE_TAGS = {"vote_positive", "accurate", "helpful", "easy_to_understand"}


@router.post("/feedback", status_code=201)
async def submit_feedback(
    request: FeedbackRequest,
    supabase: Client = Depends(get_supabase),
):
    """Submit user feedback for a chat message.

    If feedback is positive and the session contains corrections,
    those corrections are promoted to global persistence.
    """
    try:
        def _insert():
            client = get_supabase()
            return client.table("message_feedback").insert({
                "session_id": str(request.session_id),
                "message_content": request.message_content[:2000],
                "feedback_tags": request.feedback_tags,
                "feedback_text": request.feedback_text[:1000] if request.feedback_text else "",
            }).execute()

        result = await asyncio.to_thread(with_retry, _insert)

        # Check if feedback is positive → promote any session corrections to global
        is_positive = bool(set(request.feedback_tags) & POSITIVE_TAGS)
        if is_positive:
            await _promote_session_corrections(str(request.session_id))

        return {"status": "ok", "id": result.data[0]["id"] if result.data else None}
    except Exception as e:
        logger.error("Failed to save feedback: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save feedback")


async def _promote_session_corrections(session_id: str):
    """Find corrections in session message metadata and promote to global."""
    try:
        def _fetch_messages():
            client = get_supabase()
            return (
                client.table("chat_messages")
                .select("metadata")
                .eq("session_id", session_id)
                .eq("role", "assistant")
                .order("created_at", desc=True)
                .limit(5)
                .execute()
            )

        messages = await asyncio.to_thread(with_retry, _fetch_messages)
        promoted = 0
        for msg in (messages.data or []):
            metadata = msg.get("metadata") or {}
            for correction in metadata.get("corrections", []):
                if correction.get("entity") and correction.get("new_value"):
                    await asyncio.to_thread(
                        promote_correction, get_supabase(), correction, session_id
                    )
                    promoted += 1
        if promoted:
            logger.info(
                "Promoted %d corrections from session %s to global",
                promoted, session_id[:8],
            )
    except Exception as e:
        logger.warning("Failed to promote corrections from feedback: %s", e)
