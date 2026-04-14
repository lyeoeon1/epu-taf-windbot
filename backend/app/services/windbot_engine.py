"""Custom chat engine optimized for WindBot's RAG pipeline.

Replaces CondensePlusContextChatEngine with speculative retrieval:
- For follow-ups: condense + initial retrieval run in parallel
  (speculative retrieval with the raw message while LLM condenses)

The engine reuses LlamaIndex's CompactAndRefine synthesizer for
response generation, ensuring identical output quality.
"""

import asyncio
import concurrent.futures
import logging
from typing import List, Optional

from llama_index.core.base.llms.generic_utils import messages_to_history_str
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole
from llama_index.core.base.response.schema import StreamingResponse
from llama_index.core.callbacks import CallbackManager
from llama_index.core.chat_engine.types import (
    BaseChatEngine,
    StreamingAgentChatResponse,
    ToolOutput,
)
from llama_index.core.chat_engine.utils import (
    get_prefix_messages_with_context,
    get_response_synthesizer,
)
from llama_index.core.indices.base_retriever import BaseRetriever
from llama_index.core.indices.query.schema import QueryBundle
from llama_index.core.llms.llm import LLM
from llama_index.core.memory import BaseMemory, ChatMemoryBuffer
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.prompts import PromptTemplate
from llama_index.core.response_synthesizers import CompactAndRefine
from llama_index.core.schema import NodeWithScore
from llama_index.core.settings import Settings

logger = logging.getLogger(__name__)

DEFAULT_CONTEXT_PROMPT_TEMPLATE = """
  The following is a friendly conversation between a user and an AI assistant.
  The assistant is talkative and provides lots of specific details from its context.
  If the assistant does not know the answer to a question, it truthfully says it
  does not know.

  Here are the relevant documents for the context:

  {context_str}

  Instruction: Based on the above documents, provide a detailed answer for the user question below.
  Answer "don't know" if not present in the document.
  """


class WindBotChatEngine(BaseChatEngine):
    """Chat engine with speculative retrieval for follow-up messages.

    For first messages (no history): condense is skipped, retrieval starts
    immediately — same as CondensePlusContextChatEngine.

    For follow-up messages: condense runs IN PARALLEL with initial retrieval
    using the raw message. The condensed query is then used for a second
    retrieval pass if it differs significantly from the raw message.
    Results from both passes are merged and deduplicated.
    """

    def __init__(
        self,
        retriever: BaseRetriever,
        llm: LLM,
        memory: BaseMemory,
        condense_prompt: Optional[PromptTemplate] = None,
        context_prompt: Optional[PromptTemplate] = None,
        system_prompt: Optional[str] = None,
        node_postprocessors: Optional[List[BaseNodePostprocessor]] = None,
        verbose: bool = False,
    ):
        self._retriever = retriever
        self._llm = llm
        self._memory = memory
        self._condense_prompt = condense_prompt or PromptTemplate(
            "Given the following conversation between a user and an AI assistant "
            "and a follow up question from user, rephrase the follow up question "
            "to be a standalone question.\n\n"
            "Chat History:\n{chat_history}\n"
            "Follow Up Input: {question}\n"
            "Standalone question:"
        )
        self._context_prompt = context_prompt or PromptTemplate(
            DEFAULT_CONTEXT_PROMPT_TEMPLATE
        )
        self._system_prompt = system_prompt
        self._node_postprocessors = node_postprocessors or []
        self.callback_manager = CallbackManager([])
        for pp in self._node_postprocessors:
            pp.callback_manager = self.callback_manager
        self._verbose = verbose

    @classmethod
    def from_defaults(
        cls,
        retriever: BaseRetriever,
        llm: Optional[LLM] = None,
        memory: Optional[BaseMemory] = None,
        chat_history: Optional[List[ChatMessage]] = None,
        system_prompt: Optional[str] = None,
        condense_prompt: Optional[PromptTemplate] = None,
        context_prompt: Optional[PromptTemplate] = None,
        node_postprocessors: Optional[List[BaseNodePostprocessor]] = None,
        verbose: bool = False,
        **kwargs,
    ) -> "WindBotChatEngine":
        llm = llm or Settings.llm
        chat_history = chat_history or []
        memory = memory or ChatMemoryBuffer.from_defaults(
            chat_history=chat_history,
            token_limit=llm.metadata.context_window - 256,
        )
        if condense_prompt and isinstance(condense_prompt, str):
            condense_prompt = PromptTemplate(condense_prompt)
        if context_prompt and isinstance(context_prompt, str):
            context_prompt = PromptTemplate(context_prompt)
        return cls(
            retriever=retriever,
            llm=llm,
            memory=memory,
            condense_prompt=condense_prompt,
            context_prompt=context_prompt,
            system_prompt=system_prompt,
            node_postprocessors=node_postprocessors,
            verbose=verbose,
        )

    def _condense_question(
        self, chat_history: List[ChatMessage], message: str
    ) -> str:
        """Condense follow-up question into standalone query."""
        if len(chat_history) == 0:
            return message
        history_str = messages_to_history_str(chat_history)
        prompt = self._condense_prompt.format(
            chat_history=history_str, question=message,
        )
        return str(self._llm.complete(prompt))

    def _retrieve_and_postprocess(self, query: str) -> List[NodeWithScore]:
        """Retrieve nodes and apply postprocessors."""
        nodes = self._retriever.retrieve(query)
        for pp in self._node_postprocessors:
            nodes = pp.postprocess_nodes(
                nodes, query_bundle=QueryBundle(query)
            )
        return nodes

    def _dedup_nodes(self, *node_lists: List[NodeWithScore]) -> List[NodeWithScore]:
        """Merge and deduplicate nodes from multiple retrieval passes."""
        seen = set()
        result = []
        for nodes in node_lists:
            for n in nodes:
                nid = n.node.node_id or n.node.id_
                if nid not in seen:
                    seen.add(nid)
                    result.append(n)
        return result

    def _build_synthesizer(
        self, chat_history: List[ChatMessage], streaming: bool = False
    ) -> CompactAndRefine:
        """Build the response synthesizer with context + system prompt."""
        system_prompt = self._system_prompt or ""
        qa_messages = get_prefix_messages_with_context(
            self._context_prompt,
            system_prompt,
            [],
            chat_history,
            self._llm.metadata.system_role,
        )
        # Reuse same template for refine
        refine_messages = get_prefix_messages_with_context(
            self._context_prompt,
            system_prompt,
            [],
            chat_history,
            self._llm.metadata.system_role,
        )
        return get_response_synthesizer(
            self._llm,
            self.callback_manager,
            qa_messages,
            refine_messages,
            streaming,
        )

    def stream_chat(
        self, message: str, chat_history: Optional[List[ChatMessage]] = None,
    ) -> StreamingAgentChatResponse:
        """Stream a chat response with speculative retrieval.

        For follow-ups: condense and initial retrieval run in parallel.
        """
        if chat_history is not None:
            self._memory.set(chat_history)

        memory_history = self._memory.get(input=message)
        has_history = len(memory_history) > 0

        if not has_history:
            # First message — no condense needed, direct retrieval
            condensed = message
            context_nodes = self._retrieve_and_postprocess(message)
        else:
            # Follow-up — speculative parallel execution
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                # Start condense + initial retrieval simultaneously
                condense_future = pool.submit(
                    self._condense_question, memory_history, message
                )
                retrieve_future = pool.submit(
                    self._retrieve_and_postprocess, message
                )

                condensed = condense_future.result(timeout=15)
                raw_nodes = retrieve_future.result(timeout=15)

            logger.info("Condensed question: %s", condensed[:100])

            # If condensed query is substantially different, do a second retrieval
            if condensed.strip().lower() != message.strip().lower():
                condensed_nodes = self._retrieve_and_postprocess(condensed)
                context_nodes = self._dedup_nodes(condensed_nodes, raw_nodes)
                logger.info(
                    "Speculative retrieval: %d condensed + %d raw → %d merged",
                    len(condensed_nodes), len(raw_nodes), len(context_nodes),
                )
            else:
                context_nodes = raw_nodes

        context_source = ToolOutput(
            tool_name="retriever",
            content=str(context_nodes),
            raw_input={"message": condensed},
            raw_output=context_nodes,
        )

        # Build synthesizer and generate streaming response
        synthesizer = self._build_synthesizer(memory_history, streaming=True)
        response = synthesizer.synthesize(message, context_nodes)

        def wrapped_gen(response: StreamingResponse):
            full_response = ""
            for token in response.response_gen:
                full_response += token
                yield ChatResponse(
                    message=ChatMessage(
                        content=full_response, role=MessageRole.ASSISTANT
                    ),
                    delta=token,
                )
            # Update memory after streaming completes
            self._memory.put(ChatMessage(content=message, role=MessageRole.USER))
            self._memory.put(
                ChatMessage(content=full_response, role=MessageRole.ASSISTANT)
            )

        return StreamingAgentChatResponse(
            chat_stream=wrapped_gen(response),
            sources=[context_source],
            source_nodes=context_nodes,
            is_writing_to_memory=False,
        )

    def chat(
        self, message: str, chat_history: Optional[List[ChatMessage]] = None,
    ):
        """Non-streaming chat (delegates to stream_chat and collects)."""
        streaming_resp = self.stream_chat(message, chat_history)
        # Consume the stream to get the full response
        full = ""
        for chunk in streaming_resp.chat_stream:
            full = chunk.message.content
        from llama_index.core.chat_engine.types import AgentChatResponse
        return AgentChatResponse(
            response=full,
            sources=streaming_resp.sources,
            source_nodes=streaming_resp.source_nodes,
        )

    async def achat(self, message, chat_history=None):
        return await asyncio.to_thread(self.chat, message, chat_history)

    async def astream_chat(self, message, chat_history=None):
        return await asyncio.to_thread(self.stream_chat, message, chat_history)

    def reset(self):
        self._memory.reset()

    @property
    def chat_history(self) -> List[ChatMessage]:
        return self._memory.get_all()
