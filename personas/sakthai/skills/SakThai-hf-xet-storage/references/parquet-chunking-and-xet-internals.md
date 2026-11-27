# Parquet Content-Defined Chunking & Xet Storage Protocol

(PyArrow / pandas)

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
