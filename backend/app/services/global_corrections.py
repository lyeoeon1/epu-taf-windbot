"""Persistent cross-session corrections.

Stores validated corrections so the chatbot remembers user feedback
across all future sessions. Corrections are promoted from session-level
when positive feedback is received.
"""

import logging

from supabase import Client

from app.services.supabase_retry import with_retry

logger = logging.getLogger(__name__)


def get_active_corrections(supabase: Client) -> list[dict]:
    """Fetch all active global corrections."""
    try:
        def _fetch():
            from app.dependencies import get_supabase
            client = get_supabase()
            return (
                client.table("global_corrections")
                .select("entity, attribute, old_value, new_value")
                .eq("is_active", True)
                .execute()
            )

        result = with_retry(_fetch)
        return result.data or []
    except Exception as e:
        logger.warning("Failed to load global corrections: %s", e)
        return []


def promote_correction(
    supabase: Client, correction: dict, session_id: str
) -> dict | None:
    """Upsert a correction into the global table.

    Uses UNIQUE(entity, attribute) to update existing corrections
    for the same entity+attribute pair.
    """
    try:
        def _upsert():
            from app.dependencies import get_supabase
            client = get_supabase()
            return (
                client.table("global_corrections")
                .upsert(
                    {
                        "entity": correction["entity"],
                        "attribute": correction["attribute"],
                        "old_value": correction.get("old_value", ""),
                        "new_value": correction["new_value"],
                        "source_session_id": session_id,
                        "is_active": True,
                    },
                    on_conflict="entity,attribute",
                )
                .execute()
            )

        result = with_retry(_upsert)
        logger.info(
            "Promoted correction to global: %s.%s = %s",
            correction["entity"],
            correction["attribute"],
            correction["new_value"],
        )
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error("Failed to promote correction: %s", e)
        return None


def merge_corrections(
    global_corrs: list[dict], session_corrs: list[dict]
) -> list[dict]:
    """Merge global and session corrections.

    Session corrections override global for the same entity+attribute.
    """
    merged = {}
    for c in global_corrs:
        key = (c["entity"].lower().strip(), c["attribute"].lower().strip())
        merged[key] = c
    for c in session_corrs:
        key = (c.get("entity", "").lower().strip(), c.get("attribute", "").lower().strip())
        merged[key] = c
    return list(merged.values())
