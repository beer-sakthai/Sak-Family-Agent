# HF Learnings — hf-hub-doi

## 2026-07-25: Initial Research

### Summary
DOI (Digital Object Identifier) on Hugging Face Hub. Covers generation workflow, DataCite integration, versioning, repo locking, and citation integration.

### Key Points
- DOI generation is UI-only (Settings page) — no programmatic API in huggingface_hub
- DataCite consent flow requires interactive acceptance
- Repos with DOIs are locked against deletion, rename, and visibility change
- Versioning: new revision → generate new DOI → old DOI deprecated
- Free to generate, no cost
- Scope: models and datasets only

### Sources
- https://huggingface.co/docs/hub/en/doi
- https://huggingface.co/blog/introducing-doi
