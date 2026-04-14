from fastapi import APIRouter

from app.models.schemas import HealthResponse
from app.state import app_state

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthResponse)
async def health():
    return {"status": "ok", "version": "0.1.0"}


@router.get("/api/health/debug")
async def health_debug():
    """Debug endpoint showing reranker status and config."""
    reranker = app_state.get("reranker")
    return {
        "reranker_type": type(reranker).__name__ if reranker else None,
        "reranker_available": reranker.is_available if reranker else False,
        "glossary_loaded": "glossary_expander" in app_state,
        "index_loaded": "index" in app_state,
    }
