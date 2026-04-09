import logging
import os
from typing import Optional

from llama_cloud import AsyncLlamaCloud
from llama_index.core import SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.supabase import SupabaseVectorStore
from supabase import Client as SupabaseClient

from app.config import settings

logger = logging.getLogger(__name__)

# File extensions that should use LlamaParse for better parsing
LLAMAPARSE_EXTENSIONS = {".pdf", ".docx", ".doc", ".pptx", ".xlsx"}

# File extensions handled directly by SimpleDirectoryReader
SIMPLE_EXTENSIONS = {".txt", ".md", ".csv"}


async def parse_with_llamaparse(
    file_path: str,
    language: str,
    tier: str = "agentic",
) -> list[Document]:
    """Parse a document using LlamaParse (LlamaCloud API).

    Best for PDFs, DOCX, and other complex document formats with
    tables, images, and structured layouts.
    """
    client = AsyncLlamaCloud(api_key=settings.llama_cloud_api_key)
    filename = os.path.basename(file_path)

    # Upload file to LlamaCloud
    file_obj = await client.files.create(file=file_path, purpose="parse")

    # Parse with OCR support for both Vietnamese and English
    result = await client.parsing.parse(
        file_id=file_obj.id,
        tier=tier,
        version="latest",
        processing_options={
            "ocr_parameters": {"languages": ["en", "vi"]},
        },
        expand=["markdown"],
    )

    # Convert parsed pages to LlamaIndex Documents
    documents = []
    for page in result.markdown.pages:
        doc = Document(
            text=page.markdown,
            metadata={
                "language": language,
                "domain": "wind_turbine",
                "filename": filename,
                "page": page.page_number,
            },
        )
        documents.append(doc)

    return documents


def parse_with_simple_reader(
    file_path: str,
    language: str,
) -> list[Document]:
    """Parse simple text-based documents using SimpleDirectoryReader."""
    filename = os.path.basename(file_path)
    reader = SimpleDirectoryReader(input_files=[file_path])
    documents = reader.load_data()

    for doc in documents:
        doc.metadata["language"] = language
        doc.metadata["domain"] = "wind_turbine"
        doc.metadata["filename"] = filename

    return documents


def _populate_chunk_fts(
    supabase_client: SupabaseClient,
    nodes: list,
) -> None:
    """Insert ingested chunks into the chunk_fts table for BM25 search.

    This ensures new ingestions are immediately searchable via both
    dense (pgvector) and sparse (tsvector) search.
    """
    for node in nodes:
        try:
            supabase_client.table("chunk_fts").upsert({
                "chunk_id": node.node_id,
                "content": node.get_content(),
                "filename": node.metadata.get("filename", ""),
                "page": node.metadata.get("page"),
                "language": node.metadata.get("language", "vi"),
            }).execute()
        except Exception as e:
            logger.warning("Failed to insert chunk %s into FTS: %s", node.node_id, e)


async def ingest_documents(
    file_path: str,
    language: str,
    vector_store: SupabaseVectorStore,
    tier: str = "agentic",
    supabase_client: Optional[SupabaseClient] = None,
) -> int:
    """Ingest a document into the vector store.

    Automatically selects LlamaParse or SimpleDirectoryReader based on
    file extension. If supabase_client is provided, also populates the
    chunk_fts table for BM25 search.

    Returns the number of chunks created.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext in LLAMAPARSE_EXTENSIONS:
        documents = await parse_with_llamaparse(file_path, language, tier)
    elif ext in SIMPLE_EXTENSIONS:
        documents = parse_with_simple_reader(file_path, language)
    else:
        # Default to SimpleDirectoryReader for unknown types
        documents = parse_with_simple_reader(file_path, language)

    # Build and run ingestion pipeline
    pipeline = IngestionPipeline(
        transformations=[
            SentenceSplitter(chunk_size=1024, chunk_overlap=200),
            OpenAIEmbedding(model="text-embedding-3-small"),
        ],
        vector_store=vector_store,
    )

    nodes = await pipeline.arun(documents=documents)

    # Also populate FTS table for BM25 search
    if supabase_client and nodes:
        _populate_chunk_fts(supabase_client, nodes)
        logger.info("Populated %d chunks into FTS table", len(nodes))

    return len(nodes)
