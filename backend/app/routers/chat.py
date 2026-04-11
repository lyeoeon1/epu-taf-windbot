import asyncio
import json
import logging
import re
import threading

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from llama_index.core.llms import ChatMessage, MessageRole
from openai import OpenAI
from supabase import Client

from app.dependencies import get_glossary_expander, get_index, get_reranker, get_supabase
from app.models.schemas import ChatRequest
from app.prompts.system import get_suggestion_prompt
from app.services.chat_history import get_session_messages, save_message
from app.services.corrections import (
    CorrectionDetector,
    collect_corrections_from_history,
    detect_input_language,
    extract_correction,
    format_corrections_block,
)
from app.services.rag import get_chat_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


def renumber_citations(text: str, source_nodes: list) -> tuple[str, list]:
    """Renumber [N] citations sequentially by order of first appearance.

    E.g., if text contains [5], [9], [10], they become [1], [2], [3].
    source_nodes are reordered and renumbered to match.
    """
    # Find all [N] in order of first appearance
    seen = []
    for match in re.finditer(r'\[(\d{1,2})\]', text):
        num = int(match.group(1))
        if num not in seen:
            seen.append(num)

    if not seen:
        return text, source_nodes

    # Build old→new mapping
    old_to_new = {old: new for new, old in enumerate(seen, 1)}

    # Replace in text using placeholders to avoid collision
    new_text = text
    for old_num in sorted(old_to_new.keys(), reverse=True):
        new_text = new_text.replace(f'[{old_num}]', f'[__CITE_{old_to_new[old_num]}__]')
    for new_num in range(1, len(old_to_new) + 1):
        new_text = new_text.replace(f'[__CITE_{new_num}__]', f'[{new_num}]')

    # Reorder source_nodes to match new numbering
    source_map = {}
    for node in source_nodes:
        sn = node.node.metadata.get("source_number")
        if sn is not None:
            source_map[sn] = node

    reordered = []
    for old_num in seen:
        if old_num in source_map:
            node = source_map[old_num]
            node.node.metadata["source_number"] = old_to_new[old_num]
            reordered.append(node)

    return new_text, reordered

# Cached OpenAI client for suggestions (lazy-initialized)
_openai_client = None


def get_openai_client():
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI()
    return _openai_client


@router.post("/chat")
async def chat(
    request: ChatRequest,
    index=Depends(get_index),
    supabase: Client = Depends(get_supabase),
):
    """Send a message and receive a streaming response via SSE.

    The response is streamed token-by-token using Server-Sent Events.
    Each event contains either a token or a done signal:
    - data: {"token": "..."}\n\n
    - data: {"done": true}\n\n
    """
    try:
        # Save user message and load history in parallel
        session_id = str(request.session_id)
        _, history = await asyncio.gather(
            save_message(supabase, session_id, "user", request.message),
            get_session_messages(supabase, session_id),
        )

        # Determine if there's prior history (exclude the message we just saved)
        prior_history = history[:-1] if history else []
        has_history = len(prior_history) > 0

        # Collect cached corrections from prior messages' metadata
        corrections = collect_corrections_from_history(prior_history)

        # Detect if current message is a correction (regex, <1ms)
        detector = CorrectionDetector()
        is_correction_msg = detector.is_correction(request.message)

        # Extract structured correction if detected (~500ms LLM call)
        new_correction = None
        if is_correction_msg:
            new_correction = await asyncio.to_thread(
                extract_correction,
                get_openai_client(),
                request.message,
                history,
            )
            if new_correction:
                corrections.append(new_correction)

        # Build chat history as ChatMessage objects for the engine
        chat_history_messages = []
        for msg in prior_history:
            role = (
                MessageRole.USER
                if msg["role"] == "user"
                else MessageRole.ASSISTANT
            )
            chat_history_messages.append(
                ChatMessage(role=role, content=msg["content"])
            )

        # Build corrections block (with language hint) and create chat engine
        lang_hint = detect_input_language(request.message)
        corrections_block = format_corrections_block(corrections, user_language_hint=lang_hint)
        chat_engine = get_chat_engine(
            index,
            language=request.language,
            has_history=has_history,
            corrections_block=corrections_block,
            corrections=corrections or None,
            chat_history=chat_history_messages or None,
            supabase_client=supabase,
            glossary_expander=get_glossary_expander(),
            reranker=get_reranker(),
        )

        # Stream the response (run blocking call on thread pool)
        streaming_response = await asyncio.to_thread(
            chat_engine.stream_chat, request.message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Chat endpoint failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    async def event_generator():
        full_response = ""

        # Bridge the blocking sync token generator to async using a Queue + Thread.
        # This prevents the event loop from being blocked while waiting for each LLM token.
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def produce_tokens():
            try:
                for token in streaming_response.response_gen:
                    loop.call_soon_threadsafe(queue.put_nowait, token)
            except Exception as e:
                logger.error("Error during token streaming: %s", e)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

        threading.Thread(target=produce_tokens, daemon=True).start()

        while True:
            token = await queue.get()
            if token is None:
                break
            full_response += token
            yield f"data: {json.dumps({'token': token})}\n\n"

        # Renumber citations sequentially by first appearance
        context_nodes = getattr(streaming_response, "source_nodes", None) or []
        full_response, context_nodes = renumber_citations(full_response, context_nodes)

        # Extract source nodes with renumbered IDs
        sources = []
        try:
            for node_ws in context_nodes:
                metadata = node_ws.node.metadata or {}
                num = metadata.get("source_number")
                if num is None:
                    continue
                # Strip the "[Source N] " prefix from content for display
                content = node_ws.node.get_content()
                prefix = f"[Source {num}] "
                if content.startswith(prefix):
                    content = content[len(prefix):]
                sources.append({
                    "id": num,
                    "text": content[:300],
                    "filename": metadata.get("filename", ""),
                    "page": metadata.get("page"),
                    "score": round(node_ws.score, 3) if node_ws.score else None,
                })
        except Exception as e:
            logger.warning("Failed to extract source nodes: %s", e)

        # Save complete assistant response (cache corrections + sources in metadata)
        save_metadata = {"language": request.language}
        if corrections:
            save_metadata["corrections"] = corrections
        if sources:
            save_metadata["sources"] = sources
        await save_message(
            supabase,
            session_id,
            "assistant",
            full_response,
            metadata=save_metadata,
        )

        # Send done signal immediately so user sees complete response
        yield f"data: {json.dumps({'done': True})}\n\n"

        # Send source citations + renumbered content after done signal
        if sources:
            yield f"data: {json.dumps({'sources': sources, 'content': full_response})}\n\n"

        # Generate follow-up suggestions after done signal (non-blocking)
        try:
            prompt = get_suggestion_prompt(request.language).format(
                user_message=request.message,
                assistant_answer=full_response[:500],
            )

            def fetch_suggestions():
                completion = get_openai_client().chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=300,
                )
                return completion.choices[0].message.content.strip()

            raw = await asyncio.to_thread(fetch_suggestions)
            suggestions = json.loads(raw)
            if isinstance(suggestions, list) and len(suggestions) >= 3:
                yield f"data: {json.dumps({'suggestions': suggestions[:3]})}\n\n"
        except Exception as e:
            logger.warning("Failed to generate suggestions: %s", e, exc_info=True)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
