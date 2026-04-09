"""Multi-Query and HyDE (Hypothetical Document Embedding) generation.

Addresses both failure modes by generating multiple search perspectives:

1. Multi-Query: Generates 3 query variants approaching the topic from
   different angles — synonym-based, principle-based, and system-level.
   This casts a wider retrieval net.

2. HyDE: Generates a hypothetical document passage that answers the query.
   The embedding of this passage is semantically closer to the actual
   answer chunks than the short query alone. This bridges the concept gap
   (Failure Mode 2).

Both functions run in parallel via asyncio.gather for minimal latency.
"""

import asyncio
import logging

from openai import OpenAI

logger = logging.getLogger(__name__)

MULTI_QUERY_PROMPT = """\
You are an expert in wind turbine engineering and wind energy technology.
The user asked: "{query}"

Generate exactly 3 alternative search queries to find relevant technical documents. \
Each query should approach the topic from a DIFFERENT angle:

1. SYNONYM QUERY: Rephrase using different terminology — include BOTH Vietnamese \
AND English technical terms. Example: if user says "phanh" → use "brake", "braking system", "thắng".
2. PRINCIPLE QUERY: Ask about the underlying physical principle, mechanism, or theory \
that explains the answer. Example: if user asks "hộp số" → ask about "torque-speed \
relationship" / "mối quan hệ momen xoắn-tốc độ".
3. SYSTEM QUERY: Ask about the broader system or component group that contains the \
topic. Example: if user asks "pitch control" → ask about "blade control systems and \
safety mechanisms".

RULES:
- Write each query in the SAME language as the user's original query.
- Include bilingual technical terms (both VN and EN) in each query.
- Each query should be 1-2 sentences, concise and search-friendly.
- Output ONLY the 3 queries, one per line, no numbering or labels."""

HYDE_PROMPT = """\
You are a professor of wind energy engineering at a Vietnamese university.
Write a short technical passage (3-5 sentences) that answers the following question.
Write in the SAME language as the question.

IMPORTANT:
- Use precise technical terminology from wind turbine engineering.
- Include BOTH Vietnamese and English terms for key concepts.
- Include specific relationships, mechanisms, or values if relevant.
- Write as if this is from a technical textbook or reference manual.
- The passage does NOT need to be factually perfect — it should use \
the RIGHT vocabulary and concepts so it matches real document passages.

Question: {query}

Technical passage:"""


def generate_multi_queries(
    client: OpenAI,
    query: str,
    n: int = 3,
    model: str = "gpt-4o-mini",
) -> list[str]:
    """Generate n alternative query variants for the given query.

    Args:
        client: OpenAI client instance.
        query: Original user query.
        n: Number of variants to generate (default 3).
        model: LLM model to use.

    Returns:
        List of alternative query strings.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.3,
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": MULTI_QUERY_PROMPT.format(query=query),
                },
            ],
        )
        raw = response.choices[0].message.content.strip()
        # Parse: one query per line, skip empty lines
        queries = [
            line.strip().lstrip("0123456789.-) ")
            for line in raw.split("\n")
            if line.strip() and len(line.strip()) > 5
        ]
        return queries[:n]
    except Exception as e:
        logger.warning("Multi-query generation failed: %s", e)
        return []


def generate_hyde_document(
    client: OpenAI,
    query: str,
    model: str = "gpt-4o-mini",
) -> str:
    """Generate a hypothetical document passage that answers the query.

    The embedding of this passage will be used for dense search, so it
    should contain the RIGHT terminology and concepts even if the facts
    aren't perfectly accurate.

    Args:
        client: OpenAI client instance.
        query: Original user query.
        model: LLM model to use.

    Returns:
        Hypothetical document passage (3-5 sentences).
        Returns empty string on failure.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.3,
            max_tokens=250,
            messages=[
                {
                    "role": "user",
                    "content": HYDE_PROMPT.format(query=query),
                },
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("HyDE generation failed: %s", e)
        return ""


async def generate_query_variants(
    client: OpenAI,
    query: str,
    enable_multi_query: bool = True,
    enable_hyde: bool = True,
    multi_query_count: int = 2,
    model: str = "gpt-4o-mini",
) -> tuple[list[str], str]:
    """Generate both multi-query variants and HyDE document in parallel.

    Args:
        client: OpenAI client instance.
        query: Original user query.
        enable_multi_query: Whether to generate multi-query variants.
        enable_hyde: Whether to generate HyDE document.
        model: LLM model to use.

    Returns:
        Tuple of (multi_queries: list[str], hyde_document: str).
    """
    async def _noop_list():
        return []

    async def _noop_str():
        return ""

    multi_query_task = (
        asyncio.to_thread(generate_multi_queries, client, query, multi_query_count, model)
        if enable_multi_query
        else _noop_list()
    )
    hyde_task = (
        asyncio.to_thread(generate_hyde_document, client, query, model)
        if enable_hyde
        else _noop_str()
    )

    results = await asyncio.gather(multi_query_task, hyde_task, return_exceptions=True)

    multi_queries = results[0] if not isinstance(results[0], Exception) else []
    hyde_doc = results[1] if not isinstance(results[1], Exception) else ""

    if isinstance(results[0], Exception):
        logger.warning("Multi-query failed: %s", results[0])
    if isinstance(results[1], Exception):
        logger.warning("HyDE failed: %s", results[1])

    logger.debug(
        "Generated %d multi-queries + HyDE (%d chars) for: '%s'",
        len(multi_queries),
        len(hyde_doc),
        query[:50],
    )
    return multi_queries, hyde_doc
