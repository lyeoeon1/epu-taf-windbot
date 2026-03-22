"""Gunicorn configuration for BotAI Backend.

Run: gunicorn app.main:app -c gunicorn.conf.py
"""
import multiprocessing
import os

# Socket — localhost only, reverse proxy in front
bind = "127.0.0.1:" + os.getenv("BACKEND_PORT", "8000")
backlog = 2048

# Workers — use CPU count for async workers
workers = int(os.getenv("WORKERS", multiprocessing.cpu_count()))
worker_class = "uvicorn.workers.UvicornWorker"

# Auto-restart workers after N requests to prevent memory leaks
max_requests = 2000
max_requests_jitter = 200

# Timeouts
timeout = 120
graceful_timeout = 30
keepalive = 5

# Preload app — save memory via copy-on-write
preload_app = True

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")

# Process naming
proc_name = "botai-backend"

# Security limits
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190
