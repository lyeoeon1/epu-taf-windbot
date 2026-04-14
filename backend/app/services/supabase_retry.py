"""Retry wrapper for transient Supabase connection errors.

Supabase's HTTP/2 connections can go stale when Cloudflare closes idle
connections. This module provides a simple retry mechanism that recreates
the client on transient errors and retries once.
"""

import logging
from typing import Callable, TypeVar

import httpcore
import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")

TRANSIENT_ERRORS = (
    httpcore.RemoteProtocolError,
    httpx.RemoteProtocolError,
    httpx.ConnectError,
    ConnectionError,
    OSError,
)


def with_retry(fn: Callable[[], T], max_retries: int = 1) -> T:
    """Execute a sync Supabase operation with retry on transient errors.

    On failure, recreates the Supabase client to get a fresh connection
    pool, then retries. Only retries for connection/protocol errors —
    Supabase API errors (4xx/5xx) are NOT retried.
    """
    from app.dependencies import recreate_supabase

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except TRANSIENT_ERRORS as e:
            last_error = e
            logger.warning(
                "Supabase transient error (attempt %d/%d): %s: %s",
                attempt + 1,
                max_retries + 1,
                type(e).__name__,
                e,
            )
            if attempt < max_retries:
                recreate_supabase()
            else:
                raise
    # Unreachable, but satisfies type checker
    raise last_error  # type: ignore[misc]
