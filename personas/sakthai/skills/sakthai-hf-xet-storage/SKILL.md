---
name: sakthai-hf-xet-storage
category: mlops
description: Use when working with Hugging Face Xet storage — chunk-level deduplication
  for faster uploads/downloads, the hf_xet Python package, git-xet, the Xet protocol
  (xorbs, shards, CDC), Parquet content-defined chunking, and Xet environment variables.
version: 1.0.0
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

## Parquet Content-Defined Chunking (PyArrow / pandas)

Parquet is the dominant dataset format on the Hub — HF hosts **~21 PB of datasets**, with Parquet alone accounting for **over 4 PB**. Parquet CDC is now available in PyArrow (≥ 21) and pandas, and integrates with the `hf://` URI scheme so you can write directly to Hub storage with chunk-level dedup.

### Enable CDC on write

```python
import pandas as pd
import pyarrow.parquet as pq

# pandas
df.to_parquet(
    "hf://datasets/{user}/{repo}/path.parquet",
    use_content_defined_chunking=True,
)

# PyArrow
pq.write_table(
    table,
    "hf://datasets/{user}/{repo}/path.parquet",
    use_content_defined_chunking=True,
)
```

### What CDC solves

Parquet's column-chunk compression produces *entirely different byte-level representations* when even a single row is added or removed near the start. Without CDC, the entire downstream compressed block changes and dedup ratio collapses. CDC chunks each column by **content** (not by position) before serialization, so:

| Operation | Without CDC | With CDC |
|-----------|-------------|----------|
| Insert rows at top | 89.8 MB transferred (out of 99.1 MB) | 6.0 MB transferred |
| Delete rows at top | 78.2 MB transferred (out of 92.2 MB) | 7.6 MB transferred |
| Add a column | 575 KB transferred (out of 96.6 MB) | 575 KB (same — small change) |
| Append rows at end | 10.3 MB transferred (out of 106 MB) | 10.3 MB (mostly unchanged) |
| Re-upload exact copy | 96.1 MB | 0 bytes |

Numbers from the [Parquet CDC blog post](https://huggingface.co/blog/parquet-cdc) (OpenOrca subset, Snappy compression).

### Read CDC-written Parquet

Any reader that can read regular Parquet reads CDC-written Parquet — the file is still a valid Parquet file on the Hub, and the Hub reconstructs the requested bytes on read.

## CAS API Surface (for custom clients)

The Xet protocol exposes four HTTP service areas, defined in the [CAS API spec](https://huggingface.co/docs/xet/en/api):

| Endpoint family | Purpose |
|-----------------|---------|
| **Reconstruction** | Given a file's shard, return the bytes for a byte-range request. |
| **Global chunk dedupe** | Query which chunks the server already has; client skips uploading duplicates. |
| **Xorb upload** | Upload a 64 MiB xorb; server returns per-chunk dedup status. |
| **Shard upload** | Commit the (file → xorb-ranges) mapping for a newly uploaded file. |

Auth is via the same `HF_TOKEN` model used elsewhere on the Hub; upload endpoints require a `write`-scoped token. See the [Authentication and Authorization spec](https://huggingface.co/docs/xet/en/auth) and the `hf-write-from-environment` skill for token-issuance workflow on environments without browser access.

## Common Pitfalls

1. **Assuming `pip install huggingface_hub` always gets Xet.** Only ≥ 0.32.0 pulls `hf_xet` transitively. On 0.30.0 – 0.31.x, run `pip install -U hf-xet` explicitly; on < 0.30.0 you're on the LFS bridge and will see the old transfer speeds.

2. **Setting `HF_XET_HIGH_PERFORMANCE=1` on a small VM.** The flag assumes ≥ 64 GB RAM. On a 4 GB CI runner it will allocate aggressively and OOM-kill the process. Either remove the env var or pin concurrency with `HF_XET_FIXED_*_CONCURRENCY` to small values.

3. **Confusing CDC with Xet.** They are not the same. **Xet** is the storage backend (chunk-level dedup at the Hub). **CDC (content-defined chunking)** is the chunking *algorithm* used by Xet to make dedup work in the face of small edits. Parquet CDC is a *client-side* application of the same idea inside Parquet's column compression.

4. **Routing tiny files through Xet.** `.gitattributes` should be specific (`*.safetensors`, not `*`). A 4 KB JSON config doesn't benefit from chunked storage and just adds shard overhead.

5. **Forgetting the `write` token role for uploads.** Reads work with a read-scoped token. Uploads (including PyArrow's `hf://` write path) require a `write` token. See `hf-write-from-environment` for the protocol for issuing one in headless environments.

6. **Comparing Xet speeds to LFS apples-to-apples.** Xet is faster because it (a) dedupes chunks locally and on the server, (b) parallelizes xorb fetches, and (c) caches xorbs across the `hf_xet` cache (`~/.cache/huggingface/xet/`). If you purge the cache between runs, downloads will appear slower the first time.

7. **Not pinning `huggingface_hub` in CI.** Versions 0.30.0 → 0.32.0 are a transition window for Xet auto-install. Pin the version you test against.

8. **Mixing `git lfs` and `git xet` on the same repo.** `git-xet` registers a custom LFS transfer agent; standard `git lfs push` will still work but bypasses Xet. Use `git xet install` and let it handle everything.

## Verification Checklist

- [ ] `python -c "import huggingface_hub; print(huggingface_hub.__version__)"` reports `>= 0.32.0`
- [ ] `python -c "import hf_xet"` succeeds (or `pip show hf-xet` shows it installed)
- [ ] For Git workflow: `git xet --version` returns a version (not "command not found")
- [ ] Test upload: a 100 MB+ file pushes with chunked progress bars (not LFS-style single-file progress)
- [ ] Test download: same file pulls with multiple parallel xorb transfers visible in logs
- [ ] For Parquet CDC: `pq.write_table(..., use_content_defined_chunking=True, filesystem=...)` to `hf://` succeeds and the resulting file is readable back via `pq.read_table(...)`
- [ ] `HF_TOKEN` env var set with appropriate scope (read for downloads, write for uploads)
- [ ] `HF_XET_HIGH_PERFORMANCE` only set on hosts with ≥ 64 GB RAM
- [ ] No `git lfs install` needed when using `git xet install` (don't mix)

## One-Shot Recipes

### Recipe: Speed up a 50 GB model upload

```bash
pip install -U huggingface_hub   # >= 0.32.0
export HF_TOKEN=hf_xxxxxxxxxxxxx  # write scope
huggingface-cli upload myorg/big-model ./weights/ .
```

That's it. Xet handles the rest. Second push of a 50 GB model with 200 MB of new weights transfers ~200 MB of chunks.

### Recipe: Migrate an existing LFS repo to Xet

Existing LFS pointers in a repo continue to work — the LFS bridge serves them. To actually re-store files as Xet xorbs (freeing storage via global dedup), re-upload them:

```bash
git lfs fetch --all        # ensure you have all LFS objects locally
git lfs ls-files           # list LFS-tracked files
# then re-push; Xet is opportunistic and will store new revisions as xorbs
```

The Hub runs a background migration that re-stores LFS objects as Xet xorbs when accessed — you don't usually need to do anything.

### Recipe: Tune Xet for a flaky CI runner

```bash
export HF_XET_CLIENT_ENABLE_ADAPTIVE_CONCURRENCY=false
export HF_XET_FIXED_DOWNLOAD_CONCURRENCY=2
export HF_XET_FIXED_UPLOAD_CONCURRENCY=1
```

### Recipe: Write a Parquet dataset to Hub with CDC

```python
import pyarrow.parquet as pq
import pyarrow as pa

table = pa.table({"a": [1, 2, 3], "b": ["x", "y", "z"]})
pq.write_table(
    table,
    "hf://datasets/myorg/mydataset/data.parquet",
    use_content_defined_chunking=True,
)
```

Re-uploading a modified version transfers only the changed chunks.

### Recipe: Force the legacy (LFS bridge) path for debugging

```python
import os
os.environ["HF_HUB_DISABLE_XET"] = "1"
# now any huggingface_hub download/upload bypasses Xet
```

Use this to reproduce "is this a Xet-specific bug?" — if the legacy path works fine, the bug is in `xet-core` and worth a GitHub issue.
