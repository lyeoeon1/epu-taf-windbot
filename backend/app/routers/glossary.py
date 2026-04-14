import asyncio

from fastapi import APIRouter, Depends, Query
from supabase import Client

from app.dependencies import get_supabase
from app.models.schemas import GlossaryEntry
from app.services.supabase_retry import with_retry

router = APIRouter(prefix="/api", tags=["glossary"])


@router.get("/glossary", response_model=list[GlossaryEntry])
async def search_glossary(
    term: str | None = Query(None, description="Search term (partial match)"),
    category: str | None = Query(None, description="Filter by category"),
    language: str = Query("en", description="Search language: en or vi"),
    supabase: Client = Depends(get_supabase),
) -> list[GlossaryEntry]:
    """Search glossary by term or category."""

    def _query():
        client = get_supabase()
        q = client.table("glossary").select("*")
        if term:
            col = "term_en" if language == "en" else "term_vi"
            q = q.ilike(col, f"%{term}%")
        if category:
            q = q.eq("category", category)
        q = q.order("term_en")
        return q.execute()

    result = await asyncio.to_thread(with_retry, _query)
    return [GlossaryEntry(**row) for row in result.data]


@router.get("/glossary/{term_id}", response_model=GlossaryEntry)
async def get_glossary_entry(
    term_id: str,
    supabase: Client = Depends(get_supabase),
) -> GlossaryEntry:
    """Get a single glossary entry by ID."""

    def _fetch():
        client = get_supabase()
        return client.table("glossary").select("*").eq("id", term_id).single().execute()

    result = await asyncio.to_thread(with_retry, _fetch)
    return GlossaryEntry(**result.data)
