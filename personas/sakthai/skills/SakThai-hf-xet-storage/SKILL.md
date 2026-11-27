---
name: SakThai-hf-xet-storage
version: 1.0.0
description: Use when working with Hugging Face Xet storage — chunk-level deduplication
  for faster uploads/downloads, the hf_xet Python package, git-xet, the Xet protocol
  (xorbs, shards, CDC), Parquet content-defined chunking, and Xet environment variables.
category: mlops
tags:
- backend
- cas
- content-addressed-store
- deduplication
- git-lfs
- hermes
- hf
- hf-hub
- hf-xet
- huggingface
- infrastructure
- mlops
- storage
- xet
author: SakThai
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  sakthai:
    tags:
    - hermes
    - mlops
    related_skills: []
    source: hermes:hf-xet-storage
---

# Hugging Face Xet Storage

Xet is Hugging Face's content-addressable storage backend. Where Git LFS stores whole files, Xet splits files into chunks, hashes the chunks, and deduplicates them globally across the Hub — so identical byte ranges uploaded by different users in different repos count once. The user-facing effect is faster uploads (only new chunks go over the wire) and faster downloads (parallel chunk fetches via `xet-core`, the Rust client).

This skill is the deep-dive on Xet specifically. For day-to-day `hf` CLI usage, repo management, and download/upload commands, see `huggingface-hub`.

## Overview

Xet is built around three building blocks defined in the [Xet Protocol Specification](https://huggingface.co/docs/xet/en/index) (v1.0.0):

- **Chunks** — variable-size pieces of a file, produced by a content-defined chunker (Gearhash-based CDC). Each chunk has a Merkle hash.
- **Xorbs** — 64 MiB containers that group chunks. Xorbs are what actually get uploaded to CAS; clients download xorbs then reassemble files.
- **Shards** — small metadata files that list which xorb ranges reconstruct a given file. The Hub stores shards; clients fetch shards to learn which xorbs they need.

Two reference implementations ship today: **xet-core** (Rust; used by `hf_xet` Python bindings and the `git-xet` LFS custom transfer agent) and **huggingface.js** (TypeScript; used by `@huggingface/hub` and the JS download path via `XetBlob`). Interoperability is guaranteed by the protocol — both implementations produce identical hashes, xorbs, and shards.

## When to Use

- You're pushing a model, dataset, or Space file via `huggingface_hub` and want to know why it's faster than Git LFS.
- You're advising a team on whether to install `hf_xet` or `git-xet` for their workflow.
- You're tuning Xet transfer behavior — concurrency, buffer size, the `HF_XET_HIGH_PERFORMANCE` flag.
- You need to write Parquet files directly to the Hub with content-defined chunking (PyArrow ≥ 21 / pandas `use_content_defined_chunking=True`).
- You're debugging a slow upload, a chunk-cache issue, or an LFS→Xet migration question.
- You write a custom Xet client or want to understand the CAS API surface (reconstruction, global chunk dedupe, xorb upload, shard upload).

**Don't use for:** generic `hf` CLI recipes (`huggingface-hub` covers those), dataset streaming via the `datasets` library (use `datasets` docs), or local fine-tuning (no GPU/runtime available in this environment — see `evaluating-llms-harness` for eval workflows).

## Quick Start

### Python — `huggingface_hub` already ships Xet

```bash
pip install -U huggingface_hub
```

As of `huggingface_hub` 0.32.0, this installs **`hf_xet`** automatically. Anyone using `transformers` or `datasets` on a recent version is already on Xet. No code changes — `huggingface_hub.hf_hub_download`, `snapshot_download`, and `HfApi.upload_file` automatically route eligible files through Xet.

For `huggingface_hub` 0.30.0 – 0.31.x, install `hf_xet` explicitly:

```bash
pip install -U hf-xet
```

For `huggingface_hub` < 0.30.0, uploads/downloads still work via the [LFS backwards-compatibility bridge](https://huggingface.co/docs/hub/en/xet/legacy-git-lfs#backward-compatibility-with-lfs) — no Xet speedup, but no breakage either.

Verify the Xet path is active:

```python
import huggingface_hub
print(huggingface_hub.__version__)  # should be >= 0.32.0
import hf_xet  # present means Xet uploads/downloads are enabled
```

### Git — `git-xet` LFS custom transfer agent

```bash
# macOS / Linux (amd64 or aarch64)
curl --proto '=https' --tlsv1.2 -sSf https://raw.githubusercontent.com/huggingface/xet-core/refs/heads/main/git_xet/install.sh | sh

# or via Homebrew
brew install git-xet
git xet install

# Windows
winget install git-xet

# Verify
git xet --version
```

Once installed, normal `git` workflows use Xet transparently — no `lfs` install or `lfs.track` config required. Large files specified in `.gitattributes` (e.g. `*.safetensors filter=lfs diff=lfs merge=lfs -text`) are transferred as Xet xorbs, not LFS objects.

## Xet Protocol Building Blocks

| Concept | What it is | Why it matters |
|---------|-----------|----------------|
| **Chunk** | A variable-size slice of a file (typically a few KB) | The unit of deduplication. Identical chunks → identical Merkle hash → counted once. |
| **CDC (Content-Defined Chunker)** | Gearhash-based sliding window that picks chunk boundaries from content | Insert one byte in the middle of a 10 GB file → only the affected chunks change, the rest dedup against previous uploads. |
| **Merkle hash** | SHA-256-based hash of a chunk's bytes | Identity for CAS dedup and integrity verification. |
| **Xorb** | A 64 MiB container holding many chunks + their hashes | The actual upload/download object. Bundling reduces API calls and amortizes TLS overhead. |
| **Shard** | Metadata file: for a given file, list `(xorb_hash, chunk_range)` pairs | What a client fetches first to learn which xorbs reconstruct a file. |
| **CAS (Content-Addressable Storage)** | The HTTP service: `xorb upload`, `shard upload`, `reconstruction`, `global chunk dedupe` | The API surface every client implements. |
| **HMAC key in shard footer** | Integrity/auth for shard metadata | Prevents tampering with file-to-xorb mapping. |

A file is reconstructed by: fetch its shard → parse the term list → fetch the referenced xorbs in parallel → extract the needed chunk ranges → concatenate locally.

## Python: Enabling and Tuning Xet

### Default install (zero-config path)

```bash
pip install -U huggingface_hub   # pulls hf_xet on >=0.32.0
```

From here, `huggingface_hub` automatically:

- Uses Xet for downloads when the file is stored as Xet on the Hub.
- Uses Xet for uploads when the file is large enough to benefit (default threshold routes small files through regular HTTP and large files through Xet).
- Runs **adaptive concurrency** by default — `xet-core` watches real-time throughput and adjusts the number of parallel xorb fetches/uploads to saturate the link without thrashing.

### Explicit install for older `huggingface_hub`

```bash
pip install -U hf-xet
```

### High-bandwidth hosts (≥64 GB RAM)

```bash
export HF_XET_HIGH_PERFORMANCE=1
```

Convenience flag that raises concurrency bounds, buffer sizes, and parallel file limits. **Do not set this on memory-constrained machines** — it will degrade performance and can OOM-kill the process.

### Pin concurrency explicitly

If adaptive concurrency misbehaves on your network (e.g. cellular uplinks, shared CI runners):

```bash
export HF_XET_FIXED_DOWNLOAD_CONCURRENCY=8
export HF_XET_FIXED_UPLOAD_CONCURRENCY=4
export HF_XET_CLIENT_ENABLE_ADAPTIVE_CONCURRENCY=false
```

### Disable Xet (fall back to plain HTTP / LFS bridge)

```python
import os
os.environ["HF_HUB_DISABLE_XET"] = "1"  # noqa: E402 — set before any hf_hub call
```

Useful when debugging "did Xet actually run?" or when reproducing a bug on the legacy path.

## Environment Variables (Xet-specific)

Most users need none of these. They exist for tuning and debugging.

| Variable | Default | Purpose |
|----------|---------|---------|
| `HF_XET_HIGH_PERFORMANCE` | unset | Bulk tuning for ≥64 GB RAM hosts. Raises concurrency/buffer ceilings. |
| `HF_XET_CLIENT_ENABLE_ADAPTIVE_CONCURRENCY` | `true` | Master switch for adaptive concurrency. |
| `HF_XET_CLIENT_AC_INITIAL_UPLOAD_CONCURRENCY` | `1` | Starting concurrency for uploads; adaptive controller ramps it. |
| `HF_XET_CLIENT_AC_INITIAL_DOWNLOAD_CONCURRENCY` | `1` | Starting concurrency for downloads. |
| `HF_XET_FIXED_UPLOAD_CONCURRENCY` | unset | Override adaptive upload concurrency with a fixed value. |
| `HF_XET_FIXED_DOWNLOAD_CONCURRENCY` | unset | Override adaptive download concurrency with a fixed value. |
| `HF_HUB_DISABLE_XET` | unset | Force `huggingface_hub` to skip the Xet path entirely. |
| `HF_TOKEN` | unset | HF auth token. Uploads need a token with the `write` role. |

Full list lives in the [`huggingface_hub` env-var reference](https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables#xet).

## Git Workflow with `git-xet`

After `git xet install`, the standard Hub Git workflow is unchanged:

```bash
git clone https://huggingface.co/<user>/<repo>
cd <repo>
# edit / add large files
git add .
git commit -m "Add fine-tuned weights"
git push
```

Xet kicks in automatically for any file large enough to be worth chunking. `.gitattributes` should be **specific** about file extensions so small files (configs, JSON metadata) don't get unnecessarily routed through large-file storage:

```gitattributes
*.safetensors filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text
*.gguf filter=lfs diff=lfs merge=lfs -text
```

**Tip:** commit incrementally. Since only changed chunks transfer, the second push of a 10 GB repo with 50 MB of new content transfers roughly 50 MB of chunks, not 10 GB.

---

## Deep Dive Reference

For exhaustive reference specifications, cookbook snippets, and extended documentation, see [Parquet Content-Defined Chunking & Xet Storage Protocol](./references/parquet-chunking-and-xet-internals.md).
