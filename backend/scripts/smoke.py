"""Smoke test for a running WINDBOT backend.

Hits the five endpoints that matter for end-to-end functionality and
asserts each returns a valid response shape. Designed to run before a
deploy is declared successful (`deploy/deploy.sh` invokes this), or
manually after restarting the systemd service on the VPS.

Endpoints covered
-----------------
    GET  /api/health
    POST /api/chat/sessions
    POST /api/chat                  (SSE; needs OpenAI key on backend)
    GET  /api/glossary?term=turbine
    POST /api/feedback              (synthetic message_content; no DB FK)

Usage
-----
    python scripts/smoke.py                              # default http://localhost:8001
    python scripts/smoke.py https://botai.example.com    # remote
    python scripts/smoke.py --skip-chat                  # no OpenAI cost
    python scripts/smoke.py -v                           # show response bodies

Exit codes
----------
    0  every endpoint passed
    1  at least one endpoint failed (CI / deploy.sh should abort)
    2  backend unreachable at all (no /api/health response)

Environment
-----------
    Backend must be running with a real Supabase + OpenAI configuration
    for `/api/chat/sessions`, `/api/chat`, and `/api/feedback` to pass.
    `/api/health` and `/api/glossary` work even with a stub backend.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from dataclasses import dataclass

import requests


DEFAULT_BASE_URL = "http://localhost:8001"
REQUEST_TIMEOUT_S = 30        # per endpoint, except SSE
CHAT_STREAM_TIMEOUT_S = 60    # streaming chat may take longer (LLM TTFT)


@dataclass
class Result:
    name: str
    passed: bool
    detail: str = ""
    duration_ms: int = 0


# ── Individual checks ──────────────────────────────────────────────────


def check_health(base: str, verbose: bool) -> Result:
    t0 = time.monotonic()
    try:
        r = requests.get(f"{base}/api/health", timeout=REQUEST_TIMEOUT_S)
        dur = int((time.monotonic() - t0) * 1000)
        if r.status_code != 200:
            return Result("GET /api/health", False, f"status={r.status_code}", dur)
        body = r.json()
        if body.get("status") != "ok":
            return Result("GET /api/health", False, f"status field != 'ok': {body!r}", dur)
        if verbose:
            print(f"    body={body}")
        return Result("GET /api/health", True, f"version={body.get('version')}", dur)
    except Exception as e:
        return Result("GET /api/health", False, f"unreachable: {e}")


def check_create_session(base: str, verbose: bool) -> tuple[Result, str | None]:
    t0 = time.monotonic()
    try:
        r = requests.post(
            f"{base}/api/chat/sessions",
            json={"title": "smoke-test", "language": "en"},
            timeout=REQUEST_TIMEOUT_S,
        )
        dur = int((time.monotonic() - t0) * 1000)
        if r.status_code != 200:
            return Result("POST /api/chat/sessions", False, f"status={r.status_code} body={r.text[:200]}", dur), None
        body = r.json()
        sid = body.get("id")
        if not sid:
            return Result("POST /api/chat/sessions", False, f"no id in response: {body!r}", dur), None
        if verbose:
            print(f"    session_id={sid}")
        return Result("POST /api/chat/sessions", True, f"session_id={sid[:8]}", dur), sid
    except Exception as e:
        return Result("POST /api/chat/sessions", False, f"exception: {e}"), None


def check_chat_stream(base: str, session_id: str, verbose: bool) -> Result:
    """Send a greeting (fast-path, low cost) and assert SSE returns at least one token + done."""
    t0 = time.monotonic()
    try:
        r = requests.post(
            f"{base}/api/chat",
            json={"session_id": session_id, "message": "xin chào", "language": "vi"},
            stream=True,
            timeout=CHAT_STREAM_TIMEOUT_S,
        )
        dur = int((time.monotonic() - t0) * 1000)
        if r.status_code != 200:
            return Result("POST /api/chat (SSE)", False, f"status={r.status_code} body={r.text[:200]}", dur)

        token_count = 0
        saw_done = False
        for raw in r.iter_lines(decode_unicode=True):
            if not raw or not raw.startswith("data: "):
                continue
            try:
                event = json.loads(raw[6:])
            except json.JSONDecodeError:
                continue
            if "token" in event:
                token_count += 1
            if event.get("done"):
                saw_done = True
                break

        if not saw_done:
            return Result("POST /api/chat (SSE)", False, f"never received done event (tokens={token_count})", dur)
        if token_count == 0:
            return Result("POST /api/chat (SSE)", False, "done arrived but no tokens streamed", dur)
        if verbose:
            print(f"    tokens={token_count}, saw_done={saw_done}")
        return Result("POST /api/chat (SSE)", True, f"tokens={token_count}", dur)
    except Exception as e:
        return Result("POST /api/chat (SSE)", False, f"exception: {e}")


def check_glossary(base: str, verbose: bool) -> Result:
    t0 = time.monotonic()
    try:
        r = requests.get(
            f"{base}/api/glossary",
            params={"term": "turbine", "language": "en"},
            timeout=REQUEST_TIMEOUT_S,
        )
        dur = int((time.monotonic() - t0) * 1000)
        if r.status_code != 200:
            return Result("GET /api/glossary", False, f"status={r.status_code} body={r.text[:200]}", dur)
        body = r.json()
        if not isinstance(body, list):
            return Result("GET /api/glossary", False, f"expected list, got {type(body).__name__}", dur)
        if verbose:
            print(f"    matches={len(body)} sample={body[0] if body else None}")
        # Empty list is acceptable (glossary may not be seeded yet); shape is the real test.
        return Result("GET /api/glossary", True, f"matches={len(body)}", dur)
    except Exception as e:
        return Result("GET /api/glossary", False, f"exception: {e}")


def check_feedback(base: str, session_id: str, verbose: bool) -> Result:
    t0 = time.monotonic()
    try:
        r = requests.post(
            f"{base}/api/feedback",
            json={
                "session_id": session_id,
                "message_content": "smoke test feedback content",
                "feedback_tags": [],
                "feedback_text": "",
            },
            timeout=REQUEST_TIMEOUT_S,
        )
        dur = int((time.monotonic() - t0) * 1000)
        if r.status_code not in (200, 201):
            return Result("POST /api/feedback", False, f"status={r.status_code} body={r.text[:200]}", dur)
        body = r.json()
        if body.get("status") != "ok":
            return Result("POST /api/feedback", False, f"unexpected body: {body!r}", dur)
        if verbose:
            print(f"    body={body}")
        return Result("POST /api/feedback", True, f"id={body.get('id')}", dur)
    except Exception as e:
        return Result("POST /api/feedback", False, f"exception: {e}")


# ── Driver ─────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="WINDBOT backend smoke test")
    parser.add_argument(
        "base_url",
        nargs="?",
        default=DEFAULT_BASE_URL,
        help=f"Backend base URL (default {DEFAULT_BASE_URL})",
    )
    parser.add_argument("--skip-chat", action="store_true", help="Skip /api/chat (avoid OpenAI cost)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show response bodies")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    print(f"WINDBOT smoke test against {base}")
    print("=" * 60)

    results: list[Result] = []

    # 1. Health (gates everything else — if dead, abort with exit 2)
    health = check_health(base, args.verbose)
    print(f"  {'PASS' if health.passed else 'FAIL'}  {health.name} ({health.duration_ms}ms) — {health.detail}")
    results.append(health)
    if not health.passed:
        print()
        print("Backend unreachable, skipping remaining checks.")
        return 2

    # 2. Create session (needed by chat + feedback)
    session_result, sid = check_create_session(base, args.verbose)
    print(f"  {'PASS' if session_result.passed else 'FAIL'}  {session_result.name} ({session_result.duration_ms}ms) — {session_result.detail}")
    results.append(session_result)

    # 3. Chat streaming (uses session)
    if args.skip_chat:
        print("  SKIP  POST /api/chat (SSE) — --skip-chat")
    elif sid:
        chat = check_chat_stream(base, sid, args.verbose)
        print(f"  {'PASS' if chat.passed else 'FAIL'}  {chat.name} ({chat.duration_ms}ms) — {chat.detail}")
        results.append(chat)
    else:
        print("  SKIP  POST /api/chat (SSE) — no session_id")

    # 4. Glossary (independent)
    glossary = check_glossary(base, args.verbose)
    print(f"  {'PASS' if glossary.passed else 'FAIL'}  {glossary.name} ({glossary.duration_ms}ms) — {glossary.detail}")
    results.append(glossary)

    # 5. Feedback (uses session)
    if sid:
        fb = check_feedback(base, sid, args.verbose)
        print(f"  {'PASS' if fb.passed else 'FAIL'}  {fb.name} ({fb.duration_ms}ms) — {fb.detail}")
        results.append(fb)
    else:
        print("  SKIP  POST /api/feedback — no session_id")

    failures = [r for r in results if not r.passed]
    print()
    print(f"Summary: {len(results) - len(failures)}/{len(results)} endpoints OK")
    if failures:
        print("Failed endpoints:")
        for f in failures:
            print(f"  - {f.name}: {f.detail}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
