# Learning Journal

## 2026-07-26: Improved sakthai-embedding-multilingual Model Card

### Summary
Enriched the model card for **Nanthasit/sakthai-embedding-multilingual** — a BERT-based 384-dim multilingual sentence embedding model. This was our most neglected model card at 695 bytes with an empty Usage section.

### Changes Made
- **Size**: 695 → 4,809 bytes (6.9× increase)
- **YAML metadata**: Added `library_name: sentence-transformers`, `bert`, `sentence-transformers`, `feature-extraction` tags
- **Architecture details**: Added model property table (BERT-base, 384-dim, 118M params, 512 tokens)
- **4 usage options**: sentence-transformers (recommended), InferenceClient, Transformers direct, curl CLI
- **Cross-lingual examples**: Multi-language sentence similarity with cosine similarity matrix
- **Use cases list**: Cross-lingual search, clustering, RAG, zero-shot classification
- **Performance table**: Dimension, speed, memory, max tokens, similarity metric
- **Family links**: Link table to all sibling SakThai models + Spaces
- **File structure**: Complete listing of repo contents
- Fixed `library_name` — now correctly reports `sentence-transformers` on HF Hub

### Target
Model had 0 downloads. Enriched card helps discoverability when users search for multilingual sentence embeddings.

### Verification
- README readback confirms content renders correctly
- HF API shows `library_name: sentence-transformers` and updated `lastModified`
- All 10 sibling files preserved intact
