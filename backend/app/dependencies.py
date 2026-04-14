import logging
import os
import time

from fastapi import HTTPException
from supabase import Client, create_client

from app.config import settings
from app.state import app_state

logger = logging.getLogger(__name__)

# Recreate the Supabase client every 5 minutes to avoid stale HTTP/2 connections
# (Cloudflare closes idle connections after ~100-300s)
_CLIENT_TTL = 300


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
    pid = os.getpid()
    info = app_state.get("supabase_info")

    if (
        info is None
        or info["pid"] != pid
        or (time.monotonic() - info["created_at"]) > _CLIENT_TTL
    ):
        reason = (
            "init" if info is None
            else "fork" if info["pid"] != pid
            else "ttl"
        )
        logger.info("Creating Supabase client (reason=%s, pid=%d)", reason, pid)
        client = create_client(settings.supabase_url, settings.supabase_service_key)
        app_state["supabase_info"] = {
            "client": client,
            "pid": pid,
            "created_at": time.monotonic(),
        }
        return client

    return info["client"]


def recreate_supabase() -> Client:
    """Force-recreate the Supabase client after a connection error."""
    logger.warning("Force-recreating Supabase client (pid=%d)", os.getpid())
    app_state.pop("supabase_info", None)
    return get_supabase()


def get_glossary_expander():
    """Get the GlossaryExpander instance (initialized at startup)."""
    return app_state.get("glossary_expander")


def get_reranker():
    """Get the FlashReranker instance (initialized at startup)."""
    return app_state.get("reranker")
