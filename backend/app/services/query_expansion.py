"""Glossary-powered query expansion for wind turbine domain.

Loads the bilingual glossary (90+ entries with EN/VI terms, abbreviations,
and related terms) into an in-memory inverted index. When a query matches
any term, the query is expanded with all synonyms and related terms.

This addresses Failure Mode 1 (Vocabulary Mismatch): a query for "phanh"
will be expanded to include "brake", "braking system", etc.

Performance: O(n) scan where n = number of unique terms (~300).
Typical execution: <1ms.
"""

import json
import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Default path to glossary data
DEFAULT_GLOSSARY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "knowledge_base", "glossary_seed.json"
)


class GlossaryExpander:
    """Expand queries using a bilingual wind turbine glossary.

    Builds an inverted index mapping every term variant (EN, VI, abbreviation)
    to a set of all synonyms for that concept. When a query contains a known
    term, the query is augmented with all synonym variants.

    Example:
        Input:  "hệ thống phanh trong turbine gió"
        Match:  "phanh" → {"phanh", "Braking system", "Hệ thống phanh", ...}
        Output: "hệ thống phanh trong turbine gió braking system brake ..."
    """

    def __init__(self, glossary_path: Optional[str] = None):
        self._term_to_synonyms: dict[str, set[str]] = {}
        self._all_terms_lower: list[tuple[str, str]] = []  # (lower_term, original_term)
        path = glossary_path or DEFAULT_GLOSSARY_PATH
        self._load_glossary(path)

    def _load_glossary(self, path: str):
        """Load glossary JSON and build inverted index."""
        if not os.path.exists(path):
            logger.warning("Glossary file not found: %s", path)
            return

        with open(path, "r", encoding="utf-8") as f:
            entries = json.load(f)

        for entry in entries:
            # Collect all term variants for this concept
            term_en = entry.get("term_en", "").strip()
            term_vi = entry.get("term_vi", "").strip()
            abbreviation = (entry.get("abbreviation") or "").strip()
            related = entry.get("related_terms") or []

            # All forms of this concept
            synonyms = set()
            if term_en:
                synonyms.add(term_en)
            if term_vi:
                synonyms.add(term_vi)
            if abbreviation:
                synonyms.add(abbreviation)
            # Related terms are additional search angles
            for rt in related:
                if rt and isinstance(rt, str):
                    synonyms.add(rt.strip())

            # Map each variant to the full synonym set
            for term in list(synonyms):
                key = term.lower()
                if key not in self._term_to_synonyms:
                    self._term_to_synonyms[key] = set()
                self._term_to_synonyms[key].update(synonyms)

            # Track all terms for substring matching
            for term in synonyms:
                lower = term.lower()
                if len(lower) >= 2:  # Skip single-char terms
                    self._all_terms_lower.append((lower, term))

        # Sort by length descending for longest-match-first
        self._all_terms_lower.sort(key=lambda x: len(x[0]), reverse=True)

        logger.info(
            "GlossaryExpander loaded: %d entries, %d unique terms",
            len(entries),
            len(self._term_to_synonyms),
        )

    def find_matching_terms(self, query: str) -> set[str]:
        """Find all glossary terms that appear in the query.

        Returns the union of all synonym sets for matched terms.
        """
        query_lower = query.lower()
        matched_synonyms = set()

        for lower_term, original_term in self._all_terms_lower:
            # Short terms (< 4 chars) use word boundary matching to avoid
            # false positives (e.g., "AC" matching inside "education")
            if len(lower_term) < 4:
                if not re.search(r'\b' + re.escape(lower_term) + r'\b', query_lower):
                    continue
            elif lower_term not in query_lower:
                continue

            # Found a match — add all synonyms for this concept
            synonyms = self._term_to_synonyms.get(lower_term, set())
            matched_synonyms.update(synonyms)

        return matched_synonyms

    def expand(self, query: str) -> str:
        """Expand a query with glossary synonyms.

        Args:
            query: Original user query.

        Returns:
            Expanded query string with synonyms appended.
            If no matches found, returns the original query unchanged.
        """
        synonyms = self.find_matching_terms(query)

        if not synonyms:
            return query

        # Remove terms that are already in the query (case-insensitive)
        query_lower = query.lower()
        new_terms = [s for s in synonyms if s.lower() not in query_lower]

        if not new_terms:
            return query

        # Append new synonym terms to the original query
        expansion = " ".join(new_terms)
        expanded = f"{query} {expansion}"

        logger.debug(
            "Query expanded: '%s' → added %d terms",
            query[:50],
            len(new_terms),
        )
        return expanded

    @property
    def term_count(self) -> int:
        """Number of unique terms in the inverted index."""
        return len(self._term_to_synonyms)
