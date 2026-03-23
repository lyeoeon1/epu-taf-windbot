import asyncio
import json
import logging
import threading

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from llama_index.core.llms import ChatMessage, MessageRole
from openai import OpenAI
from supabase import Client

from app.dependencies import get_index, get_supabase
from app.models.schemas import ChatRequest
from app.prompts.system import get_suggestion_prompt
from app.services.chat_history import get_session_messages, save_message
from app.services.corrections import (
    CorrectionDetector,
    collect_corrections_from_history,
    extract_correction,
    format_corrections_block,
)
from app.services.rag import get_chat_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

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

    # Build corrections block and create chat engine
    corrections_block = format_corrections_block(corrections)
    chat_engine = get_chat_engine(
        index,
        language=request.language,
        has_history=has_history,
        corrections_block=corrections_block,
        corrections=corrections or None,
    )
    for msg in prior_history:
        role = (
            MessageRole.USER
            if msg["role"] == "user"
            else MessageRole.ASSISTANT
        )
        chat_engine.chat_history.append(
            ChatMessage(role=role, content=msg["content"])
        )

    # Stream the response (run blocking call on thread pool)
    streaming_response = await asyncio.to_thread(
        chat_engine.stream_chat, request.message
    )

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

        # Save complete assistant response (cache corrections in metadata)
        save_metadata = {"language": request.language}
        if corrections:
            save_metadata["corrections"] = corrections
        await save_message(
            supabase,
            session_id,
            "assistant",
            full_response,
            metadata=save_metadata,
        )

        # Send done signal immediately so user sees complete response
        yield f"data: {json.dumps({'done': True})}\n\n"

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
