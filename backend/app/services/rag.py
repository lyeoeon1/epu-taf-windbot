import logging

import vecs
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.chat_engine.types import BaseChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.supabase import SupabaseVectorStore

from app.prompts.system import get_system_prompt

logger = logging.getLogger(__name__)


def configure_settings():
    """Set global LlamaIndex settings."""
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.3)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    Settings.chunk_size = 1024
    Settings.chunk_overlap = 200


def create_vector_store(connection_string: str) -> SupabaseVectorStore:
    """Create a Supabase vector store instance."""
    vector_store = SupabaseVectorStore(
        postgres_connection_string=connection_string,
        collection_name="wind_turbine_docs",
        dimension=1536,
    )

    # Create cosine distance index to avoid full table scans
    try:
        vx = vecs.create_client(connection_string)
        collection = vx.get_or_create_collection(
            "wind_turbine_docs", dimension=1536
        )
        collection.create_index(
            measure=vecs.IndexMeasure.cosine_distance, replace=False
        )
        logger.info("Vector index verified/created for cosine distance")
    except Exception as e:
        logger.warning("Could not create vector index: %s", e)

    return vector_store


def create_index(vector_store: SupabaseVectorStore) -> VectorStoreIndex:
    """Create a VectorStoreIndex from an existing vector store."""
    return VectorStoreIndex.from_vector_store(vector_store)


def get_chat_engine(
    index: VectorStoreIndex, language: str = "en", has_history: bool = False
) -> BaseChatEngine:
    """Create a chat engine with appropriate mode based on history.

    Uses "context" mode when no history (1 LLM call),
    "condense_plus_context" when history exists (2 LLM calls but better quality).

    Args:
        index: The VectorStoreIndex to query against.
        language: Language for system prompt and metadata filtering ("en" or "vi").
        has_history: Whether the conversation has prior messages.
    """
    memory = ChatMemoryBuffer.from_defaults(token_limit=4000)
    system_prompt = get_system_prompt(language)
    mode = "condense_plus_context" if has_history else "context"

    chat_engine = index.as_chat_engine(
        chat_mode=mode,
        memory=memory,
        similarity_top_k=5,
        system_prompt=system_prompt,
        verbose=False,
    )
    return chat_engine
