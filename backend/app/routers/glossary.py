from fastapi import APIRouter, Depends, Query
from supabase import Client

from app.dependencies import get_supabase
from app.models.schemas import GlossaryEntry

router = APIRouter(prefix="/api", tags=["glossary"])


@router.get("/glossary", response_model=list[GlossaryEntry])
async def search_glossary(
    term: str | None = Query(None, description="Search term (partial match)"),
    category: str | None = Query(None, description="Filter by category"),
    language: str = Query("en", description="Search language: en or vi"),
    supabase: Client = Depends(get_supabase),
) -> list[GlossaryEntry]:
    """Search glossary by term or category."""
    query = supabase.table("glossary").select("*")

    if term:
        col = "term_en" if language == "en" else "term_vi"
        query = query.ilike(col, f"%{term}%")

    if category:
        query = query.eq("category", category)

    query = query.order("term_en")
    result = query.execute()
    return [GlossaryEntry(**row) for row in result.data]


@router.get("/glossary/{term_id}", response_model=GlossaryEntry)
async def get_glossary_entry(
    term_id: str,
    supabase: Client = Depends(get_supabase),
) -> GlossaryEntry:
    """Get a single glossary entry by ID."""
    result = supabase.table("glossary").select("*").eq("id", term_id).single().execute()
    return GlossaryEntry(**result.data)
