import logging

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.dependencies import get_supabase
from app.models.schemas import FeedbackRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["feedback"])


@router.post("/feedback", status_code=201)
async def submit_feedback(
    request: FeedbackRequest,
    supabase: Client = Depends(get_supabase),
):
    """Submit user feedback for a chat message."""
    try:
        result = supabase.table("message_feedback").insert({
            "session_id": str(request.session_id),
            "message_content": request.message_content[:2000],
            "feedback_tags": request.feedback_tags,
            "feedback_text": request.feedback_text[:1000] if request.feedback_text else "",
        }).execute()
        return {"status": "ok", "id": result.data[0]["id"] if result.data else None}
    except Exception as e:
        logger.error("Failed to save feedback: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save feedback")
