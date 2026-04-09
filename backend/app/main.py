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
from app.services.rag import configure_settings, create_index, create_vector_store
from app.state import app_state

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize LlamaIndex and vector store on startup."""
    configure_settings()
    try:
        vector_store = create_vector_store(settings.supabase_connection_string)
        index = create_index(vector_store)
        app_state["vector_store"] = vector_store
        app_state["index"] = index
        logger.info("Vector store and index initialized successfully")
    except Exception as e:
        logger.warning(
            "Failed to connect to Supabase vector store: %s. "
            "Chat and ingest endpoints will not work until configured.",
            e,
        )
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
