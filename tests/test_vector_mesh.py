# tests/test_vector_mesh.py
import pytest

from sakthai.memory.vector_mesh import (
    BM25Index,
    VectorMeshIndex,
    cosine_similarity,
    reciprocal_rank_fusion,
)


def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert cosine_similarity(v1, v2) == pytest.approx(1.0)

    v3 = [0.0, 1.0, 0.0]
    assert cosine_similarity(v1, v3) == pytest.approx(0.0)


def test_bm25_sparse_search():
    index = BM25Index()
    index.add_document("doc-1", "FastAPI endpoint with rate limiting")
    index.add_document("doc-2", "SQLite WAL mode with busy timeout")
    index.add_document("doc-3", "Next.js React dashboard panel")

    results = index.search("SQLite WAL", top_k=2)
    assert len(results) >= 1
    assert results[0][0] == "doc-2"


def test_reciprocal_rank_fusion():
    dense_ranks = ["doc-1", "doc-2", "doc-3"]
    sparse_ranks = ["doc-2", "doc-1", "doc-4"]

    fused = reciprocal_rank_fusion([dense_ranks, sparse_ranks], k=60)
    assert len(fused) == 4
    # doc-1 and doc-2 appear in top 2 in both, should be highest scored
    top_ids = [doc_id for doc_id, _score in fused[:2]]
    assert "doc-1" in top_ids
    assert "doc-2" in top_ids


def test_vector_mesh_hybrid_search():
    mesh = VectorMeshIndex()
    mesh.add_item(
        "item-1", text="Database deadlock and transaction rollback", vector=[0.9, 0.1, 0.0]
    )
    mesh.add_item(
        "item-2", text="Frontend CSS styling with Tailwind dark mode", vector=[0.0, 0.1, 0.9]
    )
    mesh.add_item("item-3", text="Network timeout and connection reset", vector=[0.5, 0.5, 0.0])

    # Hybrid search
    results = mesh.search_hybrid(
        query_text="deadlock rollback",
        query_vector=[0.9, 0.1, 0.0],
        top_k=2,
    )
    assert len(results) == 2
    assert results[0]["id"] == "item-1"
