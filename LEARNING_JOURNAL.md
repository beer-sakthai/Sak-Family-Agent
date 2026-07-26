# Learning Journal

## 2026-07-26: House of Sak narrative consistency — v7 dataset gap fixed

### Narrative Audit Findings
- **README.md** and **HF dataset card** both said "1,408 examples" (v6) but actual dataset on HF has **2,003 train + 113 test** (v7 content was uploaded but cards never updated)
- **Shared SOUL.md** (`docs/SOUL.md`) lists SakTan as active but he's deleted — secondary inconsistency
- **Agent model runtimes** in shared SOUL say "local Ollama" but SakThai actually runs on deepseek-v4-flash

### Improvement Made
1. **HF dataset card** — rewrote `Nanthasit/sakthai-combined-v6` README.md: version v6→v7, count 1,408→2,003, added evolution table, test split info, edge case category. Commit pushed.
2. **Repo README.md** — updated dataset section: v6→v7, 1,408→2,003 train/113 test, added edge cases category, safety count 30→73. Committed locally (push blocked by Zero-Exposure policy).

### Lesson
Cards are not self-updating. Every time a dataset or model gets new content, the corresponding README must be updated explicitly — the hub doesn't auto-detect upload size changes.

## 2026-07-26: Social growth metrics — flat

- **Ecosystem flat:** 2,897 total model downloads, 245 dataset downloads — no change from last snapshot. Context-1.5b leads at 942 dl.
- **Zero-dl stuck:** Vision, TTS, multilingual embedding still at 0 — card enrichment alone doesn't drive discovery. Need demo Spaces or cross-promotion.
- **No community signals:** Zero likes across all models, datasets, and Spaces. Organic discoverability is the bottleneck — no search ranking without engagement.

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
