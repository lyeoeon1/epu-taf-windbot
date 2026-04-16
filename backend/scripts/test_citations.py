"""Standalone test harness for citation post-processing logic.

Targets the three pure functions in `backend/app/routers/chat.py`:
    - renumber_citations(text, source_nodes) -> (text, nodes)
    - verify_citations(text, source_nodes) -> text
    - _extract_keywords(text) -> set[str]

Why this exists
---------------
Citation handling is the most fragile pipeline in WINDBOT (see audit
in docs/superpowers/specs/2026-04-16-windbot-maintainability-design.md).
A keyword-overlap heuristic with a hard-coded threshold (>=2) decides
whether to keep, swap, or drop each `[N]` reference returned by the LLM.
Tweaking the threshold, the regex, or the keyword extractor without a
safety net silently changes how every answer is annotated.

This harness pins down the *current* behavior with focused edge cases
so future maintainers (the author, or the Qualcomm engineer who
inherits the project) can refactor with confidence: any change that
breaks an assertion will surface here before reaching production.

Usage
-----
    cd backend
    python scripts/test_citations.py
    python scripts/test_citations.py -v   # show passing test details

Exit codes
----------
    0  all assertions hold
    1  one or more assertions failed
    2  unable to import target module (env / dependency problem)

No network, no OpenAI key, no Supabase needed — pure CPU.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make `app.*` importable when running from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from app.routers.chat import (  # noqa: E402
        _extract_keywords,
        renumber_citations,
        verify_citations,
    )
except Exception as exc:  # pragma: no cover - environment problem
    print(f"FAIL: could not import citation functions: {exc}")
    sys.exit(2)


# ── Stubs for llama_index NodeWithScore ────────────────────────────────
# We only need .node.metadata and .node.get_content() — anything heavier
# would couple the test to llama_index internals.


class _StubNode:
    def __init__(self, source_number: int | None, content: str) -> None:
        self.metadata: dict = {} if source_number is None else {"source_number": source_number}
        self._content = content

    def get_content(self) -> str:
        return self._content


class _StubNodeWithScore:
    def __init__(self, source_number: int | None, content: str, score: float = 0.5) -> None:
        self.node = _StubNode(source_number, content)
        self.score = score


def make_node(source_number: int, content: str) -> _StubNodeWithScore:
    return _StubNodeWithScore(source_number, content)


# ── Test runner ────────────────────────────────────────────────────────


class Results:
    def __init__(self, verbose: bool) -> None:
        self.passed: list[str] = []
        self.failed: list[tuple[str, str]] = []
        self.verbose = verbose

    def check(self, name: str, condition: bool, detail: str = "") -> None:
        if condition:
            self.passed.append(name)
            if self.verbose:
                print(f"  PASS  {name}" + (f" — {detail}" if detail else ""))
        else:
            self.failed.append((name, detail))
            print(f"  FAIL  {name}" + (f" — {detail}" if detail else ""))

    def summary(self) -> int:
        total = len(self.passed) + len(self.failed)
        print()
        print(f"Summary: {len(self.passed)}/{total} passed")
        if self.failed:
            print("Failures:")
            for name, detail in self.failed:
                print(f"  - {name}: {detail}")
            return 1
        return 0


# ── _extract_keywords ──────────────────────────────────────────────────


def test_extract_keywords(r: Results) -> None:
    print("\n[_extract_keywords]")

    kw = _extract_keywords("The wind turbine is large")
    r.check(
        "stopwords removed",
        "the" not in kw and "is" not in kw,
        f"got {sorted(kw)}",
    )
    r.check(
        "content words kept",
        "wind" in kw and "turbine" in kw and "large" in kw,
        f"got {sorted(kw)}",
    )

    kw = _extract_keywords("Tua-bin gió là thiết bị lớn")
    r.check(
        "vietnamese stopwords removed",
        "là" not in kw,
        f"got {sorted(kw)}",
    )
    r.check(
        "vietnamese content kept (with diacritics)",
        "tua" in kw and "bin" in kw and "gió" in kw,
        f"got {sorted(kw)}",
    )

    # Documented limitation: hyphenated terms split into parts, never
    # match the unhyphenated form. Pin behavior so a refactor that
    # changes it surfaces as a deliberate update.
    kw_hyphen = _extract_keywords("gear-box assembly")
    kw_compound = _extract_keywords("gearbox assembly")
    r.check(
        "hyphen splits word (current behavior)",
        "gear" in kw_hyphen and "box" in kw_hyphen and "gearbox" not in kw_hyphen,
        f"hyphen={sorted(kw_hyphen)}",
    )
    r.check(
        "hyphenated and compound do NOT share keywords (known limitation)",
        not (kw_hyphen & {"gearbox"}),
        "documented in design doc; consider tokenizer upgrade if becomes a problem",
    )

    r.check(
        "single-char tokens dropped",
        _extract_keywords("a I x") == set(),
        "regex requires \\w{2,}",
    )

    r.check(
        "empty input returns empty set",
        _extract_keywords("") == set(),
    )


# ── renumber_citations ─────────────────────────────────────────────────


def test_renumber_citations(r: Results) -> None:
    print("\n[renumber_citations]")

    # No citations → text & nodes pass through untouched
    text = "Tua-bin gió là thiết bị chuyển hóa năng lượng gió."
    nodes = [make_node(1, "x"), make_node(2, "y")]
    new_text, new_nodes = renumber_citations(text, nodes)
    r.check("no-citation text returns unchanged", new_text == text)
    r.check("no-citation nodes returned untouched", new_nodes is nodes)

    # Out-of-order citations are renumbered by first appearance
    text = "Foo [5] bar [9] baz [10]"
    nodes = [make_node(5, "alpha"), make_node(9, "beta"), make_node(10, "gamma")]
    new_text, new_nodes = renumber_citations(text, nodes)
    r.check(
        "[5][9][10] -> [1][2][3]",
        new_text == "Foo [1] bar [2] baz [3]",
        f"got {new_text!r}",
    )
    r.check(
        "nodes reordered + renumbered",
        [n.node.metadata["source_number"] for n in new_nodes] == [1, 2, 3],
        f"got {[n.node.metadata['source_number'] for n in new_nodes]}",
    )

    # Repeats keep the same new number
    text = "A [7] B [3] C [7] D [3]"
    nodes = [make_node(3, "x"), make_node(7, "y")]
    new_text, _ = renumber_citations(text, nodes)
    r.check(
        "repeated [N] reuse same new number",
        new_text == "A [1] B [2] C [1] D [2]",
        f"got {new_text!r}",
    )

    # 10+ distinct citations exercise the placeholder swap loop
    text = " ".join(f"[{i}]" for i in range(20, 32))  # [20]..[31]
    nodes = [make_node(i, f"src{i}") for i in range(20, 32)]
    new_text, new_nodes = renumber_citations(text, nodes)
    expected = " ".join(f"[{i}]" for i in range(1, 13))
    r.check(
        "12 distinct citations renumber sequentially",
        new_text == expected,
        f"got {new_text!r}",
    )

    # Nodes whose source_number is missing from text are dropped
    text = "Only [3] is cited"
    nodes = [make_node(1, "a"), make_node(3, "b"), make_node(7, "c")]
    new_text, new_nodes = renumber_citations(text, nodes)
    r.check(
        "uncited nodes dropped from output",
        len(new_nodes) == 1 and new_nodes[0].node.metadata["source_number"] == 1,
        f"got {[n.node.metadata['source_number'] for n in new_nodes]}",
    )

    # KNOWN ISSUE: literal `[__CITE_N__]` in user-controlled text collides
    # with the placeholder used during renumbering. We pin the *current*
    # buggy behavior so a future fix has to update this test.
    text = "Real cite [4] and noise [__CITE_1__]"
    nodes = [make_node(4, "x")]
    new_text, _ = renumber_citations(text, nodes)
    r.check(
        "placeholder collision corrupts noise (known issue)",
        "[__CITE_1__]" not in new_text,
        f"got {new_text!r} — bug: literal placeholder in input is overwritten",
    )


# ── verify_citations ───────────────────────────────────────────────────


def test_verify_citations(r: Results) -> None:
    print("\n[verify_citations]")

    # Empty source list short-circuits
    r.check(
        "empty source_nodes returns text unchanged",
        verify_citations("anything [1]", []) == "anything [1]",
    )

    # Citation with strong overlap is preserved
    text = "The nacelle houses the gearbox and generator [1]."
    nodes = [make_node(1, "Nacelle is the housing on top of the tower; contains gearbox and generator.")]
    r.check(
        "valid citation kept (overlap >= 2)",
        verify_citations(text, nodes) == text,
        f"got {verify_citations(text, nodes)!r}",
    )

    # Wrong source citation, no better candidate → citation removed
    text = "The nacelle houses the gearbox [1]."
    nodes = [make_node(1, "Cooking instructions for pasta. Boil water, add salt.")]
    out = verify_citations(text, nodes)
    r.check(
        "irrelevant citation removed",
        "[1]" not in out,
        f"got {out!r}",
    )

    # Wrong source citation, better source available → swap
    text = "The nacelle houses the gearbox [1]."
    nodes = [
        make_node(1, "Cooking instructions for pasta. Boil water."),
        make_node(2, "Nacelle housing contains the gearbox, generator, yaw drive."),
    ]
    out = verify_citations(text, nodes)
    r.check(
        "wrong citation swapped to better source",
        "[2]" in out and "[1]" not in out,
        f"got {out!r}",
    )

    # Citation referencing a source_number that doesn't exist → drop
    text = "Some claim [99] about turbines."
    nodes = [make_node(1, "Wind turbines convert kinetic energy.")]
    out = verify_citations(text, nodes)
    r.check(
        "unknown source_number citation dropped",
        "[99]" not in out,
        f"got {out!r}",
    )

    # Citation at very start of text — verifier looks forward 150 chars
    text = "[1] Wind turbines have rotors and blades."
    nodes = [make_node(1, "Wind turbines have rotors and blades and yaw mechanisms.")]
    out = verify_citations(text, nodes)
    r.check(
        "citation at text start uses forward window",
        out == text,
        f"got {out!r}",
    )

    # Sentence with no extractable keywords (only stopwords) → continue, keep citation
    text = "Of the and is [1]"
    nodes = [make_node(1, "Wind turbine technical content.")]
    out = verify_citations(text, nodes)
    r.check(
        "no-keyword sentence leaves citation intact",
        "[1]" in out,
        f"got {out!r}",
    )

    # Multiple citations, mixed validity
    text = "Nacelle and gearbox [1]. Pasta recipe [2]. Yaw drive [3]."
    nodes = [
        make_node(1, "Nacelle assembly with gearbox and generator inside."),
        make_node(2, "Wind turbine yaw drive aligns rotor with the wind."),
        make_node(3, "Yaw bearing supports the nacelle rotation against wind direction."),
    ]
    out = verify_citations(text, nodes)
    r.check(
        "valid citation 1 preserved",
        "Nacelle and gearbox [1]" in out,
        f"got {out!r}",
    )
    r.check(
        "irrelevant citation 2 removed or swapped",
        "[2]." not in out or "Pasta recipe [3]" in out,
        f"got {out!r}",
    )


# ── verify + renumber pipeline ─────────────────────────────────────────


def test_pipeline(r: Results) -> None:
    print("\n[verify -> renumber pipeline]")

    # Pipeline test requires sentences rich enough that overlap >= 2 with the
    # cited source — otherwise verify_citations strips the [N] and there's
    # nothing for renumber_citations to renumber. This mirrors what a real
    # LLM answer looks like (multi-sentence, keyword-dense paragraphs).
    text = (
        "The nacelle assembly contains the gearbox and generator [5]. "
        "The gearbox transmits rotor torque to the generator shaft [9]. "
        "Bogus claim with no source [99]."
    )
    nodes = [
        make_node(5, "Nacelle assembly contains gearbox and generator on tower top."),
        make_node(9, "Gearbox transmits rotor torque to generator shaft via planetary stages."),
    ]
    verified = verify_citations(text, nodes)
    final, final_nodes = renumber_citations(verified, nodes)

    r.check(
        "bogus [99] dropped before renumber",
        "[99]" not in final,
        f"got {final!r}",
    )
    r.check(
        "remaining citations renumbered to [1]/[2]",
        "[1]" in final and "[2]" in final and "[5]" not in final and "[9]" not in final,
        f"got {final!r}",
    )
    r.check(
        "nodes renumbered to 1, 2",
        [n.node.metadata["source_number"] for n in final_nodes] == [1, 2],
        f"got {[n.node.metadata['source_number'] for n in final_nodes]}",
    )


# ── Entry point ────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="Citation logic test harness")
    parser.add_argument("-v", "--verbose", action="store_true", help="show passing tests")
    args = parser.parse_args()

    print("WINDBOT citation logic — pinning current behavior")
    print("=" * 60)

    r = Results(verbose=args.verbose)
    test_extract_keywords(r)
    test_renumber_citations(r)
    test_verify_citations(r)
    test_pipeline(r)

    return r.summary()


if __name__ == "__main__":
    sys.exit(main())
