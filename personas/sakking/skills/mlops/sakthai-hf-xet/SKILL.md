---
name: sakthai-hf-xet
description: "Hugging Face XET protocol: fast large-file transfers with chunk-based deduplication, CAS backend, and Git-LFS compatibility."
version: 1.0.0
author: Hugging Face
license: Apache-2.0
tags: [huggingface, xet, hf-xet, deduplication, transfer, protocol, cas, git-lfs]
platforms: [linux, macos, windows]
dependencies:
  - huggingface_hub >= 1.2.2
---

# Hugging Face XET Protocol & `hf-xet`

XET (eXtremely fast Transfer) is Hugging Face's system for uploading and downloading very large binary files (models, datasets, etc.) with **chunk-based deduplication**, **concurrent transfer**, and **backwards compatibility with Git LFS**.

## Big Picture

- **Not for direct standalone use.** `hf-xet` is a low-level library consumed by `huggingface_hub` (and the `hf` CLI). End users interact with it indirectly when they run `hf download` / `hf upload-large-folder`.
- **Underlying repo:** [`huggingface/xet-core`](https://github.com/huggingface/xet-core) (Rust).
- **PyPI package:** [`hf-xet`](https://pypi.org/project/hf-xet/) (Python bindings via PyO3/maturin). Current stable: **1.5.1** (as of 2026-06).
- **Docs:** `https://huggingface.co/docs/xet/` (protocol overview) and the xet-core README.

## Key Concepts

### 1. Chunk-Based Deduplication
- Binary files are split into **content-defined chunks**.
- Identical chunks across different files map to a single **Content-Addressable Storage (CAS)** entry.
- **Benefit:** if two models share a 2 GB shard, you upload/store that shard only once.
- Deduplication happens **across** files, not just within a single file.

### 2. Content-Addressable Storage (CAS) Backend
- Chunks are addressed by their **MerkleHash** (SHA-256 style hash).
- The Hub runs a CAS service (`xet-core` backend) that stores and serves chunks.
- This enables **concurrent** upload and download pipelines.

### 3. Local Disk Cache
- A **chunk-based cache** lives alongside the standard `huggingface_hub` cache (`~/.cache/huggingface/hub`).
- Re-downloaded chunks are served from disk when possible, reducing network I/O.
- Cache keying is based on chunk hashes, so cache validity is content-determined.

### 4. Git LFS Backward Compatibility
- `hf-xet` is designed to be a **drop-in successor** to Git LFS for large files in the ML ecosystem.
- A `git-xet` CLI bridges the gap for existing Git LFS workflows.
- Existing `.gitattributes` with `filter=lfs` patterns can often work with XET-aware Git wrappers.

### 5. Architecture Components (xet-core)

| Crate / Pkg | Role |
|-------------|------|
| `hf-xet` | High-level session API (upload/download with deduplication). |
| `xet-client` | HTTP client for CAS and Hub backend services. |
| `xet-data` | Chunking, deduplication, and file reconstruction pipeline. |
| `xet-core-structures` | MerkleHash, metadata shards, Xorb objects, shared types. |
| `xet-runtime` | Async runtime, config, logging, utilities. |
| `hf_xet` (PyPI) | Python bindings (`import hf_xet`). Used by `huggingface_hub`. |
| `git-xet` | Git LFS-compatible CLI. |
| `hf_xet_thin_wasm` | Thin WASM client for browser environments. |

## How It Works (Upload Flow)

1. **Chunking:** `xet-data` splits the input file into variable-sized chunks.
2. **Hashing & Dedup:** Each chunk is hashed (MerkleHash). Already-known chunks are skipped.
3. **Upload:** Only new chunks are sent concurrently to the Hub CAS backend via `xet-client`.
4. **Pointer File:** A small pointer file (similar to Git LFS pointer) is committed to the repo, referencing the Merkle root of the chunk tree.

## How It Works (Download Flow)

1. **Pointer Resolution:** `huggingface_hub` reads the pointer file to learn the Merkle root.
2. **Chunk Request:** `xet-client` requests only the chunks needed (concurrently).
3. **Reassembly:** `xet-data` concatenates chunks back into the original file, verifying hashes along the way.
4. **Caching:** Retreived chunks land in the local chunk cache for future reuse.

## Version & Compatibility Notes

- `huggingface_hub >= 1.2.2` declares a dependency on `hf-xet`. Older `huggingface_hub` versions do **not** use XET.
- The first public release was **0.1.0** on **2025-01-10**.
- Current stable: **1.5.1** (2026-06-08), with a 1.5.1rc1 also available.
- Supports Python 3.8+; wheels ship CPython 3.8, 3.10, 3.11, 3.12, 3.13, 3.14, and PyPy/PyPy3.
- WASM build (`hf_xet_thin_wasm`) targets browser/Node environments.

## Debugging & Diagnostics

`xet-core` ships platform-specific diagnostic scripts under `scripts/diag/`:
- Linux: `scripts/diag/hf-xet-diag-linux.sh`
- macOS: `scripts/diag/hf-xet-diag-macos.sh`
- Windows (Git-Bash): `scripts/diag/hf-xet-diag-windows.sh`

Useful env vars for debugging:

```bash
RUST_BACKTRACE=full          # full Rust backtraces on panic
RUST_LOG=info                # enable hf-xet logging
HF_XET_LOG_FILE=/tmp/xet.log # write logs to a file (defaults to stdout)
```

## Practical Tips

- When `huggingface_hub` is recent enough, **all** large file uploads/downloads flow through `hf-xet` automatically — users do not need to change their code.
- If you see `hf-xet` working via `tokio-console`, compile with:
  ```bash
  RUSTFLAGS="--cfg tokio_unstable" maturin develop -r --features tokio-console
  ```
- For CI/browser testing, `hf_xet_wasm` exposes both upload and download JS APIs (not a published SDK; smoke-test only).
- On macOS, build a universal2 wheel from `hf_xet/`:
  ```bash
  MACOSX_DEPLOYMENT_TARGET=10.9 maturin build --release --target universal2-apple-darwin --features openssl_vendored
  ```

## Common Misconceptions

| Misconception | Reality |
|---------------|---------|
| "I should `pip install hf-xet`." | It is a **transitive dependency** of `huggingface_hub`. Install that instead. |
| "XET replaces Git entirely." | It replaces **Git LFS** for large binary storage; normal Git versioning remains. |
| "Chunking is expensive." | Chunking is a fast rolling-hash pass; the savings from dedup and concurrent I/O outweigh the cost. |
| "XET only works on Linux." | Wheels ship for macOS (Intel + Apple Silicon), Windows, musllinux, and many Linux variants. |

## Verifying Installation

```bash
python3 -c "import huggingface_hub; print(huggingface_hub.__version__)"
# If >= 1.2.2, XET is a transitive dependency.

python3 -c "import importlib.metadata; print(importlib.metadata.version('hf-xet'))"
# Should print a version like 1.5.1 if installed.
```

## Further Reading

- Hugging Face docs: `https://huggingface.co/docs/xet/`
- xet-core repo (Rust source, design docs, benchmarks): `https://github.com/huggingface/xet-core`
- PyPI: `https://pypi.org/project/hf-xet/`

## References

- `references/research-notes.md` — condensed research notes from this session (PyPI metadata, xet-core README excerpts, version history, and motiving use-cases).
