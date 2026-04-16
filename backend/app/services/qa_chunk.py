"""Single source of truth for: "is this NodeWithScore from the QA corpus?"

Both `AdvancedRetriever` and `QACorpusFilterPostprocessor` need to filter out
AI-generated QA pairs so they don't crowd out detailed handbook passages
during reranking. Before this module existed each owned a near-identical
copy of the detection rule, which drifted in style (one used `@staticmethod`
plus slice-then-strip-then-startswith, the other used an instance method
with strip-inside-startswith). Both are now thin wrappers around `is_qa_chunk`.

Detection rule reflects how `backend/scripts/ingest_qa.py` writes QA pairs:
    - Metadata `filename` is set to `f"qa_corpus/{cat_name}"` at lines 57, 76.
    - Content body starts with `f"Q: {question}\\nA: ..."` at lines 47, 66.

If either format ever changes, update this module (and `test_qa_chunk.py`)
as the single edit point — no more two-file synchronization.
"""

from llama_index.core.schema import NodeWithScore


def is_qa_chunk(node_ws: NodeWithScore) -> bool:
    """Return True iff the node was created by `scripts/ingest_qa.py`.

    Detection is filename-first (cheap, no content read); content prefix is
    a fallback for nodes whose filename metadata was lost in transit.
    """
    filename = (node_ws.node.metadata.get("filename") or "").lower()
    if filename.startswith("qa"):
        return True
    content = node_ws.node.get_content()[:50].strip()
    return content.startswith("Q:") or content.startswith("Q :")
