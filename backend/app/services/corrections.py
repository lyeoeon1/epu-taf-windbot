"""Correction detection, extraction, and prompt injection.

Implements System Prompt Injection (guide 3.1): detect user corrections
via regex, extract structured facts via LLM, inject into system prompt
as a high-priority context block.
"""

import json
import logging
import re

from openai import OpenAI

logger = logging.getLogger(__name__)

CORRECTION_PATTERNS = [
    r"không đúng|sai rồi|chưa chính xác|không chính xác",
    r"ghi nhớ|nhớ điều này|remember this",
    r"thực tế là|đúng ra là|chính xác là|thực ra là",
    r"chứ không phải|không phải là|khác với",
    r"hãy sửa|cập nhật lại|sửa lại",
    r"that's wrong|actually it's|correct that|not correct",
]


class CorrectionDetector:
    """Detect if a message is a correction using regex patterns."""

    def is_correction(self, message: str) -> bool:
        return any(
            re.search(p, message, re.IGNORECASE) for p in CORRECTION_PATTERNS
        )


def extract_correction(
    client: OpenAI, user_message: str, recent_history: list[dict]
) -> dict | None:
    """Extract structured correction facts using LLM.

    Returns dict with entity, attribute, old_value, new_value or None.
    """
    history_text = ""
    for msg in recent_history[-4:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_text += f"{role}: {msg['content'][:300]}\n"

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            temperature=0,
            max_tokens=200,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract correction info from the user message. "
                        "Return ONLY valid JSON, no explanation."
                    ),
                },
                {
                    "role": "user",
                    "content": f"""Recent conversation:
{history_text}
Current user message: "{user_message}"

Extract the correction as JSON:
{{"entity": "object being corrected", "attribute": "property being corrected", "old_value": "wrong value (if mentioned)", "new_value": "correct value from user"}}

If the message is not actually a correction, return {{"skip": true}}""",
                },
            ],
        )
        result = json.loads(response.choices[0].message.content.strip())
        if result.get("skip"):
            return None
        return result
    except Exception as e:
        logger.warning("Failed to extract correction: %s", e)
        return None


def collect_corrections_from_history(history: list[dict]) -> list[dict]:
    """Scan loaded chat history for cached corrections in message metadata."""
    corrections = []
    for msg in history:
        metadata = msg.get("metadata") or {}
        if "corrections" in metadata:
            corrections.extend(metadata["corrections"])
    return corrections


def detect_input_language(message: str) -> str:
    """Detect if message is primarily English or Vietnamese.

    Returns "English", "Vietnamese", or "" (unknown).
    """
    vi_chars = set(
        "àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệ"
        "ìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụ"
        "ưứừửữựỳýỷỹỵđ"
    )
    has_vi = any(c in vi_chars for c in message.lower())
    if has_vi:
        return "Vietnamese"
    alpha_count = sum(1 for c in message if c.isascii() and c.isalpha())
    total = max(len(message), 1)
    if alpha_count / total > 0.7:
        return "English"
    return ""


def format_corrections_block(
    corrections: list[dict], user_language_hint: str = ""
) -> str:
    """Format corrections list into a text block for system prompt injection."""
    if not corrections and not user_language_hint:
        return ""
    lines = []
    if user_language_hint:
        lines.append(
            f"\n[RESPOND IN: {user_language_hint.upper()}. "
            f"You MUST write your entire response in {user_language_hint}.]"
        )
    if not corrections:
        return "\n".join(lines)
    lines.extend([
        "\n[USER CORRECTIONS — ƯU TIÊN TỐI ĐA / HIGHEST PRIORITY]",
        "The following facts were provided/corrected by the user in this session.",
        "These ARE your context — using them is NOT fabrication.",
        "Always attribute as 'theo thông tin bạn cung cấp' / 'as you mentioned'.",
        "",
    ])
    for i, c in enumerate(corrections, 1):
        entity = c.get("entity", "?")
        attr = c.get("attribute", "?")
        new_val = c.get("new_value", "?")
        old_val = c.get("old_value", "")
        if old_val:
            lines.append(
                f"{i}. {entity} — {attr}: {new_val} (corrected from: {old_val})"
            )
        else:
            lines.append(f"{i}. {entity} — {attr}: {new_val}")
    lines.append("[END USER CORRECTIONS]")
    return "\n".join(lines)
