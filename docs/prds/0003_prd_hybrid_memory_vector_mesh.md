# PRD 0003: Hybrid Semantic Memory Vector Mesh

## 1. Project Overview
The **Hybrid Semantic Memory Vector Mesh** provides high-performance, dense-sparse hybrid vector search (BM25 + Cosine Semantic Similarity) across all 6 Sak-Family personas (`SakThai`, `SakKing`, `SakSee`, `SakSit`, `SakJules`, `SakTan`). It indexes episodic observations, facts, and past conversation sessions to deliver sub-millisecond associative recall.

---

## 2. Problem Statement
1. **Keyword-Only Recall**: Existing SQLite `LIKE` queries fail to retrieve semantically related facts when phrasing diverges (e.g. searching "latency spikes" misses "slow HTTP response").
2. **Pure Vector Weaknesses**: Dense embeddings alone miss exact technical keywords, error codes, and commit hashes (e.g. `HTTP 429`, `EACCES`, `sha256:459bb`).
3. **Multi-Agent Memory Silos**: Personas require a unified, thread-safe memory mesh with zero external vector database dependencies for local execution and scalable pgvector/DuckDB backends for enterprise scale.

---

## 3. Goals
- **Hybrid Retrieval (RRF - Reciprocal Rank Fusion)**: Combine BM25 sparse keyword scoring with dense cosine similarity ($S = 0.5 \cdot S_{\text{dense}} + 0.5 \cdot S_{\text{sparse}}$).
- **Embedded & Cloud Backends**: Pure Python in-memory numpy-free cosine vector index for fast CLI usage + optional DuckDB/pgvector backend for large datasets (>100,000 vectors).
- **Thread-Safe & WAL Consistent**: Integrate directly with SQLite `MemoryStore` (`facts` and `observations` tables) with zero data loss.
- **Dashboard Vector Search Visualizer**: Expose semantic search API (`/api/memory/vector`) and 2D embedding projector on the Next.js War Room dashboard.

---

## 4. Functional Requirements (P0)
- [ ] **Vector Mesh Indexer (`personas/sakthai/sakthai/memory/vector_mesh.py`)**:
  - Dense cosine similarity calculations on raw embedding vectors (`float32` arrays).
  - BM25 tokenizer and sparse inverted index over text documents.
  - Reciprocal Rank Fusion (RRF) rank combiner.
- [ ] **MemoryStore Hybrid Query Integration (`personas/sakthai/sakthai/memory/store.py`)**:
  - `search_hybrid(query_text, query_embedding, limit, alpha=0.5)`.
- [ ] **Next.js Dashboard Vector API (`apps/sak_agent_dashboard/src/app/api/memory/vector/route.ts`)**:
  - Semantic vector search endpoint with similarity scoring and latency telemetry.
