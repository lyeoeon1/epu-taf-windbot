"""Gunicorn configuration for BotAI Backend.

Run: gunicorn app.main:app -c gunicorn.conf.py
"""
import logging
import multiprocessing
import os

# Socket — bind all interfaces for direct access
bind = "0.0.0.0:" + os.getenv("BACKEND_PORT", "8001")
backlog = 2048

# Workers — use CPU count for async workers
workers = int(os.getenv("WORKERS", multiprocessing.cpu_count()))
worker_class = "uvicorn.workers.UvicornWorker"

# Auto-restart workers after N requests to prevent memory leaks
max_requests = 2000
max_requests_jitter = 200

# Timeouts — increased for SSE streaming responses
timeout = 300
graceful_timeout = 30
keepalive = 5

# Preload app — save memory via copy-on-write
preload_app = True

# Logging — JSON format via logging_config
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")

# Wire structured JSON logging (imported at gunicorn config load time)
try:
    from app.logging_config import LOGGING_CONFIG
    logconfig_dict = LOGGING_CONFIG
except ImportError:
    pass

# Process naming
proc_name = "botai-backend"

# Security limits
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190


# --- Worker lifecycle hooks ---

def post_worker_init(worker):
    """Clear pre-fork Supabase client state so each worker creates its own."""
    try:
        from app.state import app_state
        app_state.pop("supabase_info", None)
        app_state.pop("supabase", None)  # legacy key cleanup
    except ImportError:
        pass


def worker_exit(server, worker):
    """Log when a worker exits for debugging."""
    logging.getLogger("gunicorn.worker").warning(
        "Worker exiting (pid=%d)", worker.pid
    )
