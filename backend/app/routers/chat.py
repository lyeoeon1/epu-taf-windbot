import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from llama_index.core.llms import ChatMessage, MessageRole
from openai import OpenAI
from supabase import Client

from app.dependencies import get_index, get_supabase
from app.models.schemas import ChatRequest
from app.prompts.system import get_suggestion_prompt
from app.services.chat_history import get_session_messages, save_message
from app.services.rag import get_chat_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


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
    # Save user message
    await save_message(supabase, request.session_id, "user", request.message)

    # Load conversation history
    history = await get_session_messages(supabase, request.session_id)

    # Create chat engine and pre-load history
    chat_engine = get_chat_engine(index, language=request.language)
    for msg in history[:-1]:  # exclude the message we just saved
        role = (
            MessageRole.USER
            if msg["role"] == "user"
            else MessageRole.ASSISTANT
        )
        chat_engine.chat_history.append(
            ChatMessage(role=role, content=msg["content"])
        )

    # Stream the response
    streaming_response = chat_engine.stream_chat(request.message)

    async def event_generator():
        full_response = ""
        for token in streaming_response.response_gen:
            full_response += token
            yield f"data: {json.dumps({'token': token})}\n\n"

        # Save complete assistant response
        await save_message(
            supabase,
            request.session_id,
            "assistant",
            full_response,
            metadata={"language": request.language},
        )

        # Generate follow-up suggestions
        try:
            prompt = get_suggestion_prompt(request.language).format(
                user_message=request.message,
                assistant_answer=full_response[:500],
            )
            client = OpenAI()
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300,
            )
            raw = completion.choices[0].message.content.strip()
            suggestions = json.loads(raw)
            if isinstance(suggestions, list) and len(suggestions) >= 3:
                yield f"data: {json.dumps({'suggestions': suggestions[:3]})}\n\n"
        except Exception as e:
            logger.warning("Failed to generate suggestions: %s", e, exc_info=True)

        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
