---
name: SakThai-hf-xet-storage-backend
description: "Complete reference on the Xet storage backend \u2014 Hugging Face's content-addressable\
  \ storage system replacing Git LFS for scalable, deduplicated model and dataset\
  \ storage on the Hub"
---

# Xet Storage Backend — Hugging Face Hub

## Overview

**Xet** (pronounced "zet" /zɛt/) is Hugging Face's next-generation **content-addressable storage (CAS) backend** for the Hub, replacing **Git LFS** as the primary storage system. It uses **content-defined chunking (CDC)** to break files into variable-sized ~64 KB chunks, enabling byte-level deduplication across versions. Xet was developed by the **Xet Team** (formerly XetHub, acquired by Hugging Face in August 2024).

### Key facts

- **Acquired:** XetHub joined Hugging Face in August 2024 ([blog](https://huggingface.co/blog/xethub-joins-hf))
- **Public launch:** March 2025 ([Xet is on the Hub](https://huggingface.co/blog/xet-on-the-hub))
- **Default for new users/orgs:** May 2025
- **Scale:** 500,000+ repos, 20+ PB migrated (as of July 2025)
- **Users on Xet:** 1M+ (as of July 2025)
- **Storage on Hub:** ~45 PB across 2M+ repos (models, datasets, Spaces)
- **Source:** [`huggingface/xet-core`](https://github.com/huggingface/xet-core) — 542★, Rust, MIT license
- **Python integration:** [`huggingface_hub`](https://github.com/huggingface/huggingface_hub) via `hf_xet` Rust binding

### Timeline

| Date | Milestone |
|------|-----------|
| Aug 2024 | XetHub acquired by Hugging Face |
| Nov 2024 | "From Files to Chunks" — CDC foundations blog post |
| Nov 2024 | "Rearchitecting Hugging Face Uploads and Downloads" |
| Feb 2025 | "From Chunks to Blocks" — scaling CDC to production |
| Mar 2025 | **Xet is on the Hub** — first repos migrated (~6% of traffic) |
| May 2025 | Xet becomes **default storage backend** for new users/orgs |
| Jul 2025 | "Migrating the Hub from Git LFS to Xet" — 500K repos, 20 PB |
| Oct 2025 | "Streaming datasets: 100x More Efficient" — Xet-powered streaming |

## How Xet Works

### Content-Defined Chunking (CDC)

Instead of treating a file as an indivisible unit (like Git LFS), Xet breaks files into variable-sized chunks using a **rolling hash algorithm** that scans the byte sequence to determine chunk boundaries.

```text
Original file: "transformertransformertransformers\n"

After CDC:    "transformers | transformers | transformers\n"
                   (chunk A)      (chunk A)      (chunk A^)

Since content of all three chunks is identical, only ONE chunk is stored.
```

- **Average chunk size:** ~64 KB
- **Boundary condition:** `hash(data) % 2^12 == 0`
- **Result:** Only changed chunks are transmitted on updates, not the entire file

### Deduplication Benefits

When a file is modified (e.g., appending 1 MB to a 5 GB SQLite database):

| Metric | Git LFS | Xet |
|--------|---------|-----|
| Data transferred | 5 GB (full file) | ~1 MB (new chunks only) |
| Upload time (at 50 Mb/s) | ~13 min | ~0.1 sec |
| Storage for CORD-19 dataset (50 versions) | 8.9 GB | 2.1 GB |
| Avg download time (CORD-19) | 51 min | 19 min |
| Avg upload time (CORD-19) | 47 min | 24 min |

### From Chunks to Blocks: Production Scaling

To handle Hub-scale storage (~45 PB, 690B+ potential chunks), Xet groups chunks into **blocks** (~4 MB) rather than managing individual chunks:

1. **Chunks** (~64 KB) — unit of deduplication
2. **Blocks** (~4 MB) — unit of network transfer and storage I/O
3. **Manifests** — map of blocks to files, stored in metadata DB

This avoids:
- Network overhead from millions of individual chunk requests
- Infrastructure costs from billions of database entries
- Metadata explosion at Hub scale

### Git LFS Bridge

For backward compatibility, Xet provides a **Git LFS Bridge** that:
- Serves Xet-backed files via the `resolve` endpoint as presigned URLs
- Reconstructs files from chunks transparently for non-Xet-aware clients
- Allows mixed repos (some files on Xet, some on LFS)
- Enables background migration without "locks" or downtime

```
Non-Xet client → resolve endpoint → Git LFS Bridge → S3 CAS → reconstructed file
Xet-aware client → CAS API (chunk-optimized) → local reconstruction
```

## Components

### 1. `hf-xet` / `xet-core` (Rust)

The core Xet library written in Rust, providing:
- CDC chunking/blocking algorithms
- Content-addressed store (CAS) client interface
- Git integration (`git_xet`)
- WASM build for browser/JS environments
- NAPI bindings for Node.js

**Repo:** [`huggingface/xet-core`](https://github.com/huggingface/xet-core)

### 2. `hf_xet` Python binding

Python binding of the Xet Rust library, integrated into `huggingface_hub`:
- Provides chunk-aware upload/download for Python users
- Auto-detected when available (pip-installable)
- Fallback to Git LFS Bridge for older `huggingface_hub` versions

### 3. Content-Addressed Store (CAS)

The backend storage layer:
- **Chunk storage:** S3 (or compatible object storage)
- **Metadata:** DynamoDB for file/block/chunk mappings
- **CAS Bridge:** CDN-fronted API endpoint for LFS-compatible access
- **CAS endpoints:** `cas-bridge.xethub.hf.co` (production)

### 4. Hub Integration

- Xet is the **default** storage for new repos on new user/org accounts
- Background migration jobs convert LFS repos to Xet continuously
- No user action required — transparent to repository access
- Mixed repos (LFS + Xet files) supported during transition

## Impact on Hub Operations

### Upload Performance

| File Size | LFS | Xet (initial) | Xet (update) |
|-----------|-----|---------------|--------------|
| 1 MB | ~1 sec | ~1.5 sec | ~0.1 sec |
| 100 MB | ~30 sec | ~35 sec | ~2 sec |
| 1 GB | ~5 min | ~6 min | ~15 sec |
| 5 GB | ~13 min | ~15 min | ~0.1 sec* |

*\*Appending 1 MB to existing 5 GB file — Xet only transfers changed chunks*

### Background Migration

- Runs 24/7 without user-visible disruption
- ~500K repos migrated in 6 months (Jan–Jul 2025)
- No repo "locks" — read/write continues during migration
- Fewer than a few dozen GitHub issues or support tickets

## Using Xet with huggingface_hub

```python
# Xet is automatic — no special code needed
from huggingface_hub import HfApi

api = HfApi()

# Upload a model — uses Xet if the repo is Xet-enabled
api.upload_file(
    path_or_fileobj="my_model.safetensors",
    path_in_repo="model.safetensors",
    repo_id="username/my-model",
    repo_type="model",
)

# Download — Xet chunks are reconstructed transparently
api.hf_hub_download(
    repo_id="username/my-model",
    filename="model.safetensors",
)
```

For Xet-aware uploads (chunk-optimized), ensure you have the latest `huggingface_hub` and the `hf_xet` package:

```bash
pip install --upgrade huggingface_hub hf-xet
```

## Known Limitations & Considerations

- **Xet-aware client required** for chunk-level upload optimization; non-Xet clients fall back to Git LFS Bridge (slower)
- **Initial upload** may be slightly slower than LFS due to chunking overhead
- **Benefits are most visible** for large files (100MB+) that undergo iterative changes
- **Not available for Spaces repositories** (still primarily on LFS/build storage)
- **WASM/Node.js support** is experimental (via `xet_core` WASM builds)

## References

### Blog Posts
- [XetHub is joining Hugging Face!](https://huggingface.co/blog/xethub-joins-hf) (Aug 2024)
- [From Files to Chunks: Improving HF Storage Efficiency](https://huggingface.co/blog/from-files-to-chunks) (Nov 2024)
- [Rearchitecting Hugging Face Uploads and Downloads](https://huggingface.co/blog/rearchitecting-uploads-and-downloads) (Nov 2024)
- [From Chunks to Blocks: Accelerating Uploads and Downloads on the Hub](https://huggingface.co/blog/from-chunks-to-blocks) (Feb 2025)
- [Xet is on the Hub](https://huggingface.co/blog/xet-on-the-hub) (Mar 2025)
- [Migrating the Hub from Git LFS to Xet](https://huggingface.co/blog/migrating-the-hub-to-xet) (Jul 2025)
- [Streaming datasets: 100x More Efficient](https://huggingface.co/blog/streaming-datasets) (Oct 2025)

### Source Code
- [`huggingface/xet-core`](https://github.com/huggingface/xet-core) — Rust implementation, MIT license
- [`huggingface/huggingface_hub`](https://github.com/huggingface/huggingface_hub) — `hf_xet` integration

### Docs
- Hub Repositories → Storage Backend (Xet) section in [Hub documentation](https://huggingface.co/docs/hub/en/index)

## Related Skills
- `sakthai-hf-hub-storage-management` — Hub storage quotas and limits
- `sakthai-hf-hub-cache-system-deep-dive` — local cache behavior
- `sakthai-hf-datasets-streaming-deep-dive` — dataset streaming (Xet-powered)
