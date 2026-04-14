import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

# Export API keys to os.environ so OpenAI SDK and LlamaIndex can find them.
# pydantic_settings loads .env into the Settings object but does NOT set os.environ.
if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key
if settings.llama_cloud_api_key:
    os.environ["LLAMA_CLOUD_API_KEY"] = settings.llama_cloud_api_key
from app.routers import chat, feedback, glossary, health, ingest, sessions
from app.services.query_expansion import GlossaryExpander
from app.services.rag import configure_settings, create_index, create_vector_store
from app.services.reranker import create_reranker
from app.state import app_state

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize LlamaIndex and vector store on startup."""
    # Use print() for critical startup info — always captured by systemd.
    # logging.getLogger("app.*") is unreliable under uvicorn workers + torch/transformers.
    import sys

    configure_settings()
    try:
        vector_store = create_vector_store(settings.supabase_connection_string)
        index = create_index(vector_store)
        app_state["vector_store"] = vector_store
        app_state["index"] = index
        print("[STARTUP] Vector store and index initialized", file=sys.stderr)
    except Exception as e:
        print(f"[STARTUP] FAILED vector store: {e}", file=sys.stderr)

    # Initialize advanced retrieval components
    if settings.enable_advanced_retrieval:
        try:
            glossary_expander = GlossaryExpander()
            app_state["glossary_expander"] = glossary_expander
            print(
                f"[STARTUP] GlossaryExpander loaded: {glossary_expander.term_count} terms",
                file=sys.stderr,
            )
        except Exception as e:
            print(f"[STARTUP] FAILED GlossaryExpander: {e}", file=sys.stderr)

        if settings.enable_reranking:
            try:
                # Resolve ONNX model path relative to this file's directory
                onnx_dir = settings.onnx_model_dir
                if not onnx_dir:
                    onnx_dir = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "models", "reranker-int8",
                    )
                print(f"[STARTUP] ONNX model dir: {onnx_dir}", file=sys.stderr)
                reranker = create_reranker(
                    onnx_model_dir=onnx_dir,
                    num_threads=settings.reranker_threads,
                )
                app_state["reranker"] = reranker
                print(
                    f"[STARTUP] Reranker: {type(reranker).__name__} (available={reranker.is_available})",
                    file=sys.stderr,
                )
            except Exception as e:
                print(f"[STARTUP] FAILED reranker: {e}", file=sys.stderr)

    yield


app = FastAPI(
    title="Wind Turbine Knowledge Chatbot API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(ingest.router)
app.include_router(chat.router)
app.include_router(glossary.router)
app.include_router(feedback.router)
