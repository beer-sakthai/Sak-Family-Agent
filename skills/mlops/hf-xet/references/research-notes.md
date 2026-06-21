# XET Protocol Research Notes

## Sources Consulted
- PyPI `hf-xet` page: https://pypi.org/project/hf-xet/
- GitHub `huggingface/xet-core` README: https://github.com/huggingface/xet-core
- PyPI `huggingface_hub` metadata (dependency on `hf-xet`)

## Key Excerpts

### PyPI hf-xet description (v1.5.1)
> `hf-xet` enables `huggingface_hub` to utilize xet storage for uploading and downloading to HF Hub. Xet storage provides chunk-based deduplication, efficient storage/retrieval with local disk caching, and backwards compatibility with Git LFS. This library is not meant to be used directly, and is instead intended to be used from huggingface_hub.

### xet-core README (architecture)
Packages produced by the repo:
- `hf-xet` (crates.io + PyPI via maturin / `hf_xet/`) — high-level session API.
- `xet-client` — HTTP client for CAS and Hub backend services.
- `xet-data` — Chunking, deduplication, and file reconstruction pipeline.
- `xet-core-structures` — MerkleHash, metadata shards, Xorb objects.
- `xet-runtime` — Async runtime, configuration, logging, utilities.
- `git-xet` (`git_xet/`) — Git LFS compatible CLI.
- `hf_xet_thin_wasm` (`wasm/`) — Thin WASM client for browser/Node environments.

### Version history (from PyPI)
- First public release: 0.1.0 on 2025-01-10.
- Latest stable: 1.5.1 on 2026-06-08.
- rc1 of 1.5.1 also available (2026-06-08).
- Supports Python 3.8+; wheels for CPython 3.8, 3.10, 3.11, 3.12, 3.13, 3.14, PyPy, musllinux, macOS (Intel + Apple Silicon), Windows.

## Why it matters to HF users
Large model/dataset files uploaded through the Hub are now silently deduplicated at the chunk level. This reduces upload bandwidth and storage costs when files share common shards (e.g., base-model checkpoints reused in finetunes).
