# RAG Server with Sentence-Transformers

Created 2026-07-24. Semantic search for SOUL.md files using sentence-transformers.

## Setup
```bash
uv pip install sentence-transformers numpy
```

## Files
- `rag-server.py` — HTTP server on port 3003
- `cache/rag_index.json` — pre-built index

## API
```bash
curl http://localhost:3003/
curl "http://localhost:3003/search?q=Hugging+Face+master"
```

## Notes
- Model: all-MiniLM-L6-v2 (384-dim)
- Index build: ~7s, ~1 GB RAM
- Only index SOULs + key docs — all skills causes OOM
