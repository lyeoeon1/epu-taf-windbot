from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.chat_engine.types import BaseChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.supabase import SupabaseVectorStore

from app.prompts.system import get_system_prompt


def configure_settings():
    """Set global LlamaIndex settings."""
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.3)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    Settings.chunk_size = 1024
    Settings.chunk_overlap = 200


def create_vector_store(connection_string: str) -> SupabaseVectorStore:
    """Create a Supabase vector store instance."""
    return SupabaseVectorStore(
        postgres_connection_string=connection_string,
        collection_name="wind_turbine_docs",
        dimension=1536,
    )


def create_index(vector_store: SupabaseVectorStore) -> VectorStoreIndex:
    """Create a VectorStoreIndex from an existing vector store."""
    return VectorStoreIndex.from_vector_store(vector_store)


def get_chat_engine(
    index: VectorStoreIndex, language: str = "en"
) -> BaseChatEngine:
    """Create a chat engine with condense_plus_context mode.

    Args:
        index: The VectorStoreIndex to query against.
        language: Language for system prompt and metadata filtering ("en" or "vi").
    """
    memory = ChatMemoryBuffer.from_defaults(token_limit=4000)
    system_prompt = get_system_prompt(language)

    chat_engine = index.as_chat_engine(
        chat_mode="condense_plus_context",
        memory=memory,
        similarity_top_k=5,
        system_prompt=system_prompt,
        verbose=False,
    )
    return chat_engine
