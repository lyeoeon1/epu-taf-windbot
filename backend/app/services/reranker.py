"""Cross-encoder reranking with ONNX Runtime (primary) or FlashRank (fallback).

ONNX Runtime with INT8 quantization provides 5-10x faster inference than
FlashRank's PyTorch backend on CPU, reducing reranking from 4-5s to <0.5s.

Model: cross-encoder/ms-marco-MiniLM-L-12-v2 (~33M params).
"""

import logging
import os
import time
from typing import Optional

import numpy as np
from llama_index.core.schema import NodeWithScore

logger = logging.getLogger(__name__)


class OnnxReranker:
    """Rerank using ONNX Runtime with batched cross-encoder inference.

    Loads an ONNX-exported cross-encoder model and runs batched inference
    on all (query, passage) pairs in a single forward pass.
    """

    def __init__(
        self,
        model_dir: str = "models/reranker-int8",
        num_threads: int = 4,
        max_length: int = 256,
    ):
        self._session = None
        self._tokenizer = None
        self._max_length = max_length
        self._input_names = []

        try:
            import onnxruntime as ort
            from transformers import AutoTokenizer

            # Find ONNX model file
            onnx_path = self._find_model(model_dir)
            if not onnx_path:
                logger.warning("No ONNX model found in %s", model_dir)
                return

            # Configure session for CPU performance
            sess_options = ort.SessionOptions()
            sess_options.intra_op_num_threads = num_threads
            sess_options.inter_op_num_threads = 1
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

            self._session = ort.InferenceSession(
                onnx_path,
                sess_options=sess_options,
                providers=["CPUExecutionProvider"],
            )
            self._input_names = [inp.name for inp in self._session.get_inputs()]
            self._tokenizer = AutoTokenizer.from_pretrained(model_dir)

            # Warmup with dummy inference
            self._warmup()
            logger.info(
                "OnnxReranker initialized: %s (%d threads)",
                onnx_path, num_threads,
            )
        except ImportError as e:
            logger.warning("OnnxReranker deps missing (%s). Install: pip install onnxruntime transformers", e)
        except Exception as e:
            logger.warning("Failed to initialize OnnxReranker: %s", e)

    @staticmethod
    def _find_model(model_dir: str) -> Optional[str]:
        """Find the ONNX model file in the directory."""
        candidates = ["model_quantized.onnx", "model.onnx"]
        for name in candidates:
            path = os.path.join(model_dir, name)
            if os.path.exists(path):
                return path
        return None

    def _warmup(self):
        """Run dummy inference to JIT-compile the ONNX graph."""
        if not self._session or not self._tokenizer:
            return
        dummy = self._tokenizer(
            ["warmup query"], ["warmup passage"],
            padding=True, truncation=True, max_length=32,
            return_tensors="np",
        )
        feed = {k: v for k, v in dummy.items() if k in self._input_names}
        self._session.run(None, feed)

    @property
    def is_available(self) -> bool:
        return self._session is not None and self._tokenizer is not None

    def rerank(
        self,
        query: str,
        nodes: list[NodeWithScore],
        top_k: int = 8,
    ) -> list[NodeWithScore]:
        """Rerank nodes using ONNX cross-encoder scoring.

        All (query, passage) pairs are batched into a single forward pass
        for maximum throughput.
        """
        if not nodes:
            return []

        if not self.is_available:
            logger.debug("OnnxReranker unavailable, returning top %d by score", top_k)
            return sorted(nodes, key=lambda n: n.score or 0, reverse=True)[:top_k]

        start = time.perf_counter()

        try:
            passages = [n.node.get_content() for n in nodes]
            queries = [query] * len(passages)

            # Batch tokenize all (query, passage) pairs
            encoded = self._tokenizer(
                queries, passages,
                padding=True,
                truncation=True,
                max_length=self._max_length,
                return_tensors="np",
            )

            # Run batched inference
            feed = {k: v for k, v in encoded.items() if k in self._input_names}
            outputs = self._session.run(None, feed)

            # Extract relevance scores from model output
            # ms-marco-MiniLM-L-12-v2 outputs [batch, 1] — single relevance score
            logits = outputs[0]
            if logits.ndim == 2:
                scores = logits[:, 0]
            else:
                scores = logits.flatten()

            # Build scored results
            scored = list(zip(scores, nodes))
            scored.sort(key=lambda x: x[0], reverse=True)

            result = [
                NodeWithScore(node=node.node, score=float(score))
                for score, node in scored[:top_k]
            ]

            elapsed = time.perf_counter() - start
            logger.info(
                "OnnxReranker: %d → %d nodes in %.3fs (top=%.4f)",
                len(nodes), len(result), elapsed,
                result[0].score if result else 0,
            )
            return result

        except Exception as e:
            logger.warning("ONNX reranking failed: %s. Falling back to score sort.", e)
            return sorted(nodes, key=lambda n: n.score or 0, reverse=True)[:top_k]


# ── FlashRank fallback ──────────────────────────────────────────────

_flashrank_available = None


def _check_flashrank():
    global _flashrank_available
    if _flashrank_available is None:
        try:
            import flashrank  # noqa: F401
            _flashrank_available = True
        except ImportError:
            _flashrank_available = False
    return _flashrank_available


class FlashReranker:
    """Fallback reranker using FlashRank (PyTorch-based)."""

    def __init__(self, model_name: str = "ms-marco-MiniLM-L-12-v2"):
        self._ranker = None
        if _check_flashrank():
            try:
                from flashrank import Ranker
                self._ranker = Ranker(model_name=model_name)
                logger.info("FlashReranker initialized: %s", model_name)
            except Exception as e:
                logger.warning("Failed to initialize FlashReranker: %s", e)

    @property
    def is_available(self) -> bool:
        return self._ranker is not None

    def rerank(
        self,
        query: str,
        nodes: list[NodeWithScore],
        top_k: int = 8,
    ) -> list[NodeWithScore]:
        if not nodes:
            return []
        if not self.is_available:
            return sorted(nodes, key=lambda n: n.score or 0, reverse=True)[:top_k]

        try:
            from flashrank import RerankRequest

            passages = []
            for node_ws in nodes:
                passages.append({
                    "id": node_ws.node.node_id or node_ws.node.id_,
                    "text": node_ws.node.get_content(),
                    "meta": node_ws.node.metadata,
                })

            request = RerankRequest(query=query, passages=passages)
            ranked = self._ranker.rerank(request)

            node_by_id = {
                (n.node.node_id or n.node.id_): n for n in nodes
            }

            result = []
            for r in ranked[:top_k]:
                node_id = r["id"]
                if node_id in node_by_id:
                    result.append(NodeWithScore(
                        node=node_by_id[node_id].node,
                        score=float(r["score"]),
                    ))

            logger.debug("FlashReranker: %d → %d nodes", len(nodes), len(result))
            return result

        except Exception as e:
            logger.warning("FlashRank failed: %s", e)
            return sorted(nodes, key=lambda n: n.score or 0, reverse=True)[:top_k]


def create_reranker(
    onnx_model_dir: str = "models/reranker-int8",
    num_threads: int = 4,
) -> OnnxReranker | FlashReranker:
    """Create the best available reranker: ONNX (preferred) → FlashRank (fallback)."""
    onnx = OnnxReranker(model_dir=onnx_model_dir, num_threads=num_threads)
    if onnx.is_available:
        return onnx

    logger.info("ONNX reranker not available, falling back to FlashRank")
    return FlashReranker()
