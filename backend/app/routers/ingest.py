import os
import tempfile

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.dependencies import get_supabase, get_vector_store, verify_admin_key
from app.models.schemas import IngestResponse
from app.services.ingestion import ingest_documents

router = APIRouter(prefix="/api", tags=["ingest"])


@router.post(
    "/ingest",
    response_model=list[IngestResponse],
    dependencies=[Depends(verify_admin_key)],
)
async def ingest(
    files: list[UploadFile] = File(...),
    language: str = Form("en"),
    tier: str = Form("agentic"),
    vector_store=Depends(get_vector_store),
    supabase=Depends(get_supabase),
):
    """Ingest documents into the wind turbine knowledge base.

    - PDF, DOCX, PPTX, XLSX -> parsed via LlamaParse (high quality)
    - TXT, MD, CSV -> parsed via SimpleDirectoryReader (fast, no credits)

    Args:
        files: Document files to ingest.
        language: Document language - "en" or "vi".
        tier: LlamaParse tier - "cost_effective", "agentic", or "agentic_plus".
    """
    results = []

    for file in files:
        # Save uploaded file to temp location
        suffix = os.path.splitext(file.filename or "file")[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            num_chunks = await ingest_documents(
                tmp_path, language, vector_store, tier,
                supabase_client=supabase,
            )

            # Save metadata to Supabase
            supabase.table("documents_metadata").insert(
                {
                    "filename": file.filename,
                    "file_type": suffix.lstrip("."),
                    "language": language,
                    "num_chunks": num_chunks,
                }
            ).execute()

            results.append(
                {
                    "status": "success",
                    "chunks_created": num_chunks,
                    "filename": file.filename or "unknown",
                }
            )
        finally:
            os.unlink(tmp_path)

    return results
