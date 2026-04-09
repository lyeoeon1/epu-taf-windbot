import logging
from typing import Optional

import vecs
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.chat_engine.types import BaseChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.supabase import SupabaseVectorStore
from pydantic import Field

from app.prompts.system import get_condense_prompt, get_system_prompt

logger = logging.getLogger(__name__)


class CorrectionOverridePostprocessor(BaseNodePostprocessor):
    """Mark retrieved nodes that conflict with user corrections.

    When corrections exist, scans each retrieved chunk and prepends
    an override notice if the chunk contains a conflicting value.
    This ensures the LLM sees the conflict explicitly.
    """

    corrections: list[dict] = Field(default_factory=list)

    def _postprocess_nodes(
        self,
        nodes: list[NodeWithScore],
        query_bundle: Optional[QueryBundle] = None,
    ) -> list[NodeWithScore]:
        if not self.corrections:
            return nodes
        for node_ws in nodes:
            text = node_ws.node.get_content().lower()
            for corr in self.corrections:
                old_val = (corr.get("old_value") or "").lower().strip()
                attr = (corr.get("attribute") or "").lower().strip()
                new_val = (corr.get("new_value") or "").lower().strip()
                entity = (corr.get("entity") or "").lower().strip()

                # Match on: old_value, attribute with different value,
                # OR entity name appearing in this chunk
                matched = False
                if old_val and old_val in text:
                    matched = True
                elif attr and attr in text and new_val and new_val not in text:
                    matched = True
                elif entity and entity in text:
                    matched = True

                if matched:
                    prefix = (
                        f"[USER CORRECTED: {corr.get('entity', '?')} — "
                        f"{corr.get('attribute', '?')}="
                        f"{corr.get('new_value', '?')}. "
                        f"IGNORE conflicting values below.]\n"
                    )
                    node_ws.node.set_content(
                        prefix + node_ws.node.get_content()
                    )
                    break
        return nodes


def configure_settings():
    """Set global LlamaIndex settings."""
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.1)
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
    index: VectorStoreIndex,
    language: str = "en",
    has_history: bool = False,
    corrections_block: str = "",
    corrections: Optional[list[dict]] = None,
    chat_history: Optional[list] = None,
) -> BaseChatEngine:
    """Create a chat engine using condense_plus_context mode.

    Uses "condense_plus_context" mode which automatically condenses
    follow-up questions into standalone queries before retrieval.
    This ensures short/ambiguous follow-ups like "có thể có 4 ko?"
    are reformulated into clear queries (e.g., "Tua-bin gió có thể
    có 4 cánh quạt không?") before hitting the vector store.

    The full chat history (including user corrections) remains visible
    to the LLM for generation, so corrections are naturally retained.

    Args:
        index: The VectorStoreIndex to query against.
        language: Language for system prompt and metadata filtering ("en" or "vi").
        has_history: Whether the conversation has prior messages.
        corrections_block: Formatted corrections to inject into system prompt.
        corrections: Raw correction dicts for node post-processing.
        chat_history: Prior chat messages to pre-load into memory.
    """
    memory = ChatMemoryBuffer.from_defaults(
        token_limit=8000,
        chat_history=chat_history,
    )
    system_prompt = get_system_prompt(language, corrections_block=corrections_block)

    postprocessors = [SimilarityPostprocessor(similarity_cutoff=0.25)]
    if corrections:
        postprocessors.append(
            CorrectionOverridePostprocessor(corrections=corrections)
        )

    chat_engine = index.as_chat_engine(
        chat_mode="condense_plus_context",
        memory=memory,
        similarity_top_k=10,
        system_prompt=system_prompt,
        node_postprocessors=postprocessors,
        condense_prompt=get_condense_prompt(language),
        verbose=False,
    )
    return chat_engine
