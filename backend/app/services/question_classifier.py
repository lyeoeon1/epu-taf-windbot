"""Hybrid question classifier: regex first, LLM fallback for ambiguous cases.

Follows the same two-stage pattern as CorrectionDetector:
- Stage 1 (regex, <1ms): pattern match for high-confidence cases
- Stage 2 (LLM, ~200ms): gpt-4o-mini for ambiguous questions
"""

import logging
import re

from openai import OpenAI

logger = logging.getLogger(__name__)

# Confidence threshold below which we fall back to LLM classification
CONFIDENCE_THRESHOLD = 0.7

# Regex patterns per question type (Vietnamese + English)
# Each pattern list is checked in order; first type to match wins.
# Types are checked in priority order: more specific types first.
PATTERNS: dict[str, dict] = {
    "COMPARISON": {
        "patterns": [
            r"so sánh",
            r"khác nhau|khác biệt|khác gì",
            r"giống nhau|giống gì",
            r"\bcompare\b",
            r"\bdifference\b",
            r"\bvs\.?\b",
            r"\bversus\b",
            r"ưu điểm.*nhược điểm|nhược điểm.*ưu điểm",
            r"advantage.*disadvantage|disadvantage.*advantage",
            r"pros.*cons|cons.*pros",
            r"nào tốt hơn|nào hơn",
            r"which.*(better|prefer)",
        ],
        "confidence": 0.9,
    },
    "TROUBLESHOOT": {
        "patterns": [
            r"sự cố",
            r"hỏng|hư hỏng",
            r"\blỗi\b(?!.*\blịch sử\b)",  # "loi" but not "loi lich su"
            r"nứt|gãy|vỡ",
            r"troubleshoot",
            r"\bfault\b|\bfailure\b",
            r"\bbroken\b|\bcrack\b",
            r"xử lý khi|xử lý sự cố",
            r"nếu.*bị",
            r"what if.*fail",
            r"khẩn cấp|emergency",
            r"dừng khẩn",
            r"không hoạt động|ngừng hoạt động",
            r"(does|did)n'?t work",
        ],
        "confidence": 0.85,
    },
    "PROCEDURE": {
        "patterns": [
            r"quy trình",
            r"các bước",
            r"cách (bảo trì|lắp đặt|sửa|kiểm tra|vận hành|thay thế)",
            r"procedure|steps|how to (maintain|install|fix|inspect|operate|replace)",
            r"bảo trì|bảo dưỡng",
            r"\bmaintenance\b",
            r"lắp đặt|installation",
            r"kiểm tra định kỳ|periodic inspection",
            r"vận hành|operation procedure",
        ],
        "confidence": 0.85,
    },
    "PRINCIPLE": {
        "patterns": [
            r"hoạt động (như thế nào|ra sao|thế nào)",
            r"nguyên lý|nguyên tắc",
            r"\bcơ chế\b",
            r"how does.*work",
            r"\bprinciple\b|\bmechanism\b",
            r"chuyển đổi.*năng lượng|energy conversion",
            r"tại sao.*(quay|chạy|hoạt động)",
            r"why does.*(rotate|spin|work)",
            r"quá trình.*chuyển đổi",
        ],
        "confidence": 0.8,
    },
    "STRUCTURE": {
        "patterns": [
            r"cấu tạo|cấu trúc",
            r"thành phần|bộ phận",
            r"gồm (những|các|gì|bao nhiêu)",
            r"components?|structure|parts? of",
            r"là gì\s*\??$",  # ends with "là gì?"
            r"^.{0,30}(what is|what are)\b",  # short "what is X" questions
            r"bao gồm",
            r"consists? of|made (up )?of|comprised? of",
        ],
        "confidence": 0.8,
    },
}

# LLM classification prompt — compact for speed
CLASSIFICATION_PROMPT = """\
Classify this wind turbine question into ONE type. Reply with ONLY the type name, nothing else.

Types:
- STRUCTURE: What is X, components, parts, definition, structure
- PRINCIPLE: How does X work, physics, mechanism, energy conversion
- PROCEDURE: Maintenance steps, installation, inspection, operation procedure
- COMPARISON: Compare X vs Y, differences, advantages/disadvantages
- TROUBLESHOOT: Fault diagnosis, failure handling, emergency, broken/cracked
- GENERAL: Greetings, continuations, unclear, or none of the above

Question: "{message}"
Type:"""


class QuestionClassifier:
    """Hybrid question classifier using regex + LLM fallback."""

    def classify_sync(self, message: str) -> tuple[str, float]:
        """Stage 1: Regex-based classification.

        Returns (question_type, confidence). If no pattern matches,
        returns ("GENERAL", 0.3) — low confidence triggers LLM fallback.
        """
        message_lower = message.lower().strip()

        # Skip classification for very short messages (likely continuations)
        if len(message_lower) < 5:
            return ("GENERAL", 0.9)

        for qtype, config in PATTERNS.items():
            for pattern in config["patterns"]:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    logger.info(
                        "Question classified as %s (regex, confidence=%.2f): %s",
                        qtype,
                        config["confidence"],
                        message[:80],
                    )
                    return (qtype, config["confidence"])

        # No pattern matched — low confidence, should trigger LLM fallback
        return ("GENERAL", 0.3)

    def classify_llm(self, client: OpenAI, message: str) -> str:
        """Stage 2: LLM-based classification for ambiguous cases.

        Uses gpt-4o-mini with minimal tokens for fast classification.
        Returns question type string or "GENERAL" on failure.
        """
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                max_tokens=20,
                seed=42,
                messages=[
                    {
                        "role": "user",
                        "content": CLASSIFICATION_PROMPT.format(message=message[:200]),
                    },
                ],
            )
            result = response.choices[0].message.content.strip().upper()

            # Validate result is a known type
            valid_types = {"STRUCTURE", "PRINCIPLE", "PROCEDURE", "COMPARISON", "TROUBLESHOOT", "GENERAL"}
            if result in valid_types:
                logger.info(
                    "Question classified as %s (LLM): %s",
                    result,
                    message[:80],
                )
                return result

            logger.warning("LLM returned unknown type '%s', falling back to GENERAL", result)
            return "GENERAL"

        except Exception as e:
            logger.warning("LLM classification failed: %s, falling back to GENERAL", e)
            return "GENERAL"

    def classify(self, message: str, client: OpenAI | None = None) -> tuple[str, str]:
        """Hybrid classification: regex first, LLM fallback if low confidence.

        Args:
            message: The user's question.
            client: OpenAI client for LLM fallback. If None, regex-only.

        Returns:
            Tuple of (question_type, classification_method).
            classification_method is "regex" or "llm".
        """
        qtype, confidence = self.classify_sync(message)

        if confidence >= CONFIDENCE_THRESHOLD:
            return (qtype, "regex")

        # Low confidence — try LLM if client available
        if client is not None:
            llm_type = self.classify_llm(client, message)
            return (llm_type, "llm")

        # No LLM client — use regex result anyway
        return (qtype, "regex")
