# Track 003 Specification: Hybrid Semantic Memory Vector Mesh

## Overview
High-performance dense-sparse hybrid vector search (BM25 + Cosine Similarity with RRF) across all 6 Sak-Family personas.

## PRD Reference
[`docs/prds/0003_prd_hybrid_memory_vector_mesh.md`](file:///home/beern/Sak-Family-Agent/docs/prds/0003_prd_hybrid_memory_vector_mesh.md)

## Core Requirements
1. `VectorMeshIndex` with dense cosine search and BM25 text indexer.
2. `search_hybrid` method on `MemoryStore`.
3. Dashboard `/api/memory/vector` endpoint.
4. 100% hermetic unit tests with $\ge 96\%$ branch coverage.
