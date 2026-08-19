"""Hybrid Dense-Sparse Vector Mesh Index combining Cosine Similarity and BM25 with RRF."""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from typing import Any


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculate cosine similarity between two float vectors without external deps."""
    if len(v1) != len(v2) or not v1:
        return 0.0

    dot = sum(a * b for a, b in zip(v1, v2, strict=False))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    return dot / (norm1 * norm2)


def tokenize(text: str) -> list[str]:
    """Simple alphanumeric tokenizer for BM25 indexing."""
    return re.findall(r"\w+", text.lower())


class BM25Index:
    """Lightweight in-memory BM25 sparse keyword ranking engine."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.docs: dict[str, list[str]] = {}
        self.doc_lens: dict[str, int] = {}
        self.avg_doc_len: float = 0.0
        self.inverted_index: dict[str, dict[str, int]] = defaultdict(dict)
        self.df: dict[str, int] = defaultdict(int)

    def add_document(self, doc_id: str, text: str) -> None:
        tokens = tokenize(text)
        self.docs[doc_id] = tokens
        self.doc_lens[doc_id] = len(tokens)
        self.avg_doc_len = sum(self.doc_lens.values()) / max(len(self.doc_lens), 1)

        counts = Counter(tokens)
        for term, freq in counts.items():
            self.inverted_index[term][doc_id] = freq

        # Recompute doc frequencies
        self.df = defaultdict(int)
        for term, posting in self.inverted_index.items():
            self.df[term] = len(posting)

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        q_tokens = tokenize(query)
        if not q_tokens or not self.docs:
            return []

        scores: dict[str, float] = defaultdict(float)
        n = len(self.docs)

        for term in q_tokens:
            if term not in self.df:
                continue

            df = self.df[term]
            idf = math.log((n - df + 0.5) / (df + 0.5) + 1.0)

            for doc_id, tf in self.inverted_index[term].items():
                doc_len = self.doc_lens.get(doc_id, 1)
                num = tf * (self.k1 + 1.0)
                denom = tf + self.k1 * (
                    1.0 - self.b + self.b * (doc_len / max(self.avg_doc_len, 1.0))
                )
                scores[doc_id] += idf * (num / max(denom, 1e-6))

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


def reciprocal_rank_fusion(ranked_lists: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """Combine rankings from multiple search modalities using RRF."""
    rrf_scores: dict[str, float] = defaultdict(float)

    for rank_list in ranked_lists:
        for rank, doc_id in enumerate(rank_list):
            rrf_scores[doc_id] += 1.0 / (k + rank + 1)

    return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)


class VectorMeshIndex:
    """Hybrid Semantic Vector Mesh combining dense embeddings and BM25 sparse search."""

    def __init__(self) -> None:
        self.bm25 = BM25Index()
        self.vectors: dict[str, list[float]] = {}
        self.metadata: dict[str, dict[str, Any]] = {}

    def add_item(
        self,
        item_id: str,
        text: str,
        vector: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.bm25.add_document(item_id, text)
        if vector:
            self.vectors[item_id] = vector
        self.metadata[item_id] = metadata or {"text": text}

    def search_dense(self, query_vector: list[float], top_k: int = 10) -> list[tuple[str, float]]:
        scores: list[tuple[str, float]] = []
        for doc_id, vec in self.vectors.items():
            sim = cosine_similarity(query_vector, vec)
            scores.append((doc_id, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def search_sparse(self, query_text: str, top_k: int = 10) -> list[tuple[str, float]]:
        return self.bm25.search(query_text, top_k=top_k)

    def search_hybrid(
        self,
        query_text: str,
        query_vector: list[float] | None = None,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        dense_results: list[tuple[str, float]] = []
        if query_vector and self.vectors:
            dense_results = self.search_dense(query_vector, top_k=top_k * 2)

        sparse_results = self.search_sparse(query_text, top_k=top_k * 2)

        dense_ranked_ids = [doc_id for doc_id, _ in dense_results]
        sparse_ranked_ids = [doc_id for doc_id, _ in sparse_results]

        if not dense_ranked_ids:
            final_ranked = sparse_results[:top_k]
        elif not sparse_ranked_ids:
            final_ranked = dense_results[:top_k]
        else:
            fused = reciprocal_rank_fusion([dense_ranked_ids, sparse_ranked_ids])
            final_ranked = fused[:top_k]

        return [
            {
                "id": doc_id,
                "score": score,
                "metadata": self.metadata.get(doc_id, {}),
            }
            for doc_id, score in final_ranked
        ]
