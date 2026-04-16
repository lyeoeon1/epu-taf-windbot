"""Shared slowapi Limiter instance.

Backend runs behind Cloudflare Tunnel / Ngrok, so the immediate peer is always
localhost. We honor X-Forwarded-For (left-most hop) as the client identifier
when present, falling back to the remote address otherwise.
"""

from fastapi import Request
from slowapi import Limiter


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # left-most entry is the original client (subsequent entries are proxies)
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "anonymous"


limiter = Limiter(key_func=_client_ip)
