from fastapi import HTTPException
from supabase import Client, create_client

from app.config import settings
from app.state import app_state


def get_index():
    if "index" not in app_state:
        raise HTTPException(
            status_code=503,
            detail="Vector store not initialized. Check Supabase configuration.",
        )
    return app_state["index"]


def get_vector_store():
    if "vector_store" not in app_state:
        raise HTTPException(
            status_code=503,
            detail="Vector store not initialized. Check Supabase configuration.",
        )
    return app_state["vector_store"]


def get_supabase() -> Client:
    if "supabase" not in app_state:
        app_state["supabase"] = create_client(
            settings.supabase_url, settings.supabase_service_key
        )
    return app_state["supabase"]


def get_glossary_expander():
    """Get the GlossaryExpander instance (initialized at startup)."""
    return app_state.get("glossary_expander")


def get_reranker():
    """Get the FlashReranker instance (initialized at startup)."""
    return app_state.get("reranker")
