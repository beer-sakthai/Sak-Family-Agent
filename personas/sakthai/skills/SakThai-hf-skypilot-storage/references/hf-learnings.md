# HF Learning: SkyPilot + HF Storage — Zero-Egress Multi-Cloud Storage

> **Topic**: `hf-hub-skypilot-storage-integration`
> **Date**: 2026-07-25
> **Source**: Hugging Face Blog "Run AI workloads on any cloud, store on Hugging Face: zero-egress storage with SkyPilot", HF Storage Buckets Docs, HF Xet Storage Docs, SkyPilot Storage Reference

---

## 1. The Problem: Egress Tax Pins Workloads to One Cloud

- GPU capacity is fragmented across 20+ cloud vendors (AWS, GCP, Azure, Nebius, Lambda, CoreWeave, etc.)
- Teams hold reserved/committed capacity across multiple vendors
- Object stores are regional and per-cloud — reading data from a different vendor's GPU cluster means paying egress (~$0.09/GB out of AWS, often even between regions inside one cloud)
- Teams pin each run to whichever vendor holds the data, leaving other capacity idle

## 2. The Solution: Hugging Face Storage + SkyPilot

**Hugging Face Storage** is now a first-class SkyPilot backend. Together they provide:
- **Zero egress on reads**: reading data from HF Storage onto GPUs on any cloud costs nothing
- **Write-back still costs** your compute cloud's usual egress (same as any off-cloud store), but reads dominate in AI workloads (datasets streamed over epochs, weights pulled onto new nodes)

### Architecture

```
User's training job → SkyPilot → finds cheapest GPU across 20+ clouds
                                   │
                                   ▼
                    Mounts HF Storage (hf-mount FUSE)
                                   │
                                   ▼
                    Reads/writes data with zero egress
```

- SkyPilot schedules the job across 20+ clouds, Kubernetes, Slurm, and on-prem
- `HF_TOKEN` works on any cloud — one token, no per-cloud bucket keys
- The same HF Storage bucket is reachable from every cluster

### Pricing Comparison

| Storage | Price | Egress |
|---------|-------|--------|
| HF Storage | $12–18/TB/month | Free (reads) |
| AWS S3 | ~$23/TB/month | ~$0.09/GB out |

## 3. HF Storage Types

The Hub offers two storage types:

| Type | Use Case | Features |
|------|----------|----------|
| **Git-based repos** (models, datasets, Spaces) | Version history, collaboration (PRs, discussions), library integrations | Git-backed, versioned |
| **Storage Buckets** | Fast mutable storage for checkpoints, logs, intermediate artifacts | S3-like, files overwrite/delete in place, no version history |

### Storage Buckets (`hf://buckets/<owner>/<name>`)

- S3-like object storage on the Hub, powered by Xet backend
- Available to all users and organizations
- Three interaction methods:
  1. **Hub web interface** — browse, drag-and-drop upload
  2. **`hf` CLI** — `hf buckets list`, `cp`, `sync`, `pipe`
  3. **Python API** — `huggingface_hub` library with `hf://` URIs
- **Sync command**: `hf <src> <dst>` — compares source/destination, only transfers changed files
- **Plan/apply workflow**: `hf <src> <dst> --plan sync-plan.jsonl` to review before executing
- Public or private, with optional README.md per directory

## 4. SkyPilot Storage Modes for HF

SkyPilot tasks reference HF storage via `store: hf` and `source: hf://...` URIs.

### Mode: MOUNT / MOUNT_CACHED (default)

- Uses **hf-mount FUSE backend** — repo/bucket shows up as local path
- Lazy reads: only bytes your code touches cross the network
- On-disk cache: repeat reads stay local
- MOUNT and MOUNT_CACHED behave identically for HF (hf-mount has its own cache)
- **Configuration** via `config.mount.hf_mount_args`:
  ```yaml
  config:
    mount:
      hf_mount_args: ['--cache-dir', '/mnt/nvme/hf-cache', '--cache-size', '100GB']
  ```

### Mode: COPY

- Downloads via `huggingface_hub` directly — no FUSE needed
- Good fallback if FUSE is unavailable (e.g., unprivileged K8s containers)
- Full file copies before processing starts

### Example SkyPilot YAML

```yaml
# Mount a model repo (read-only)
storage:
  my-model:
    source: hf://Qwen/Qwen2.5-3B
    store: hf
    mode: MOUNT

# Mount a dataset (read-only)
  my-data:
    source: hf://datasets/my-org/my-dataset
    store: hf

# Mount a bucket (read-write) for checkpoints
  checkpoints:
    source: hf://buckets/my-org/my-bucket
    store: hf
    mode: MOUNT
```

## 5. Xet Storage & Content-Defined Chunking (CDC)

Xet is the storage backend powering both Git-based repos and Storage Buckets.

### How CDC Works

- Files are split into **~64 KB variable-sized chunks**
- Chunk boundaries are determined by a **rolling hash** (content-defined, not fixed positions)
- Each chunk is identified by its SHA-256 hash
- Only **new chunks** are uploaded; duplicates are deduplicated

### CDC vs Fixed-Size Chunking

```
Fixed-size (bad):  |The qu|ick br|own fo|x jump|s over| the l|azy do|g
Insert "very ":     |The qu|ick br|own fo|x jump|s over| the v|ery la|zy dog|
                   ↑ same only first 5 chunks survive, 3 chunks changed!

CDC (good):         |The quick |brown fox |jumps over |the lazy dog|
Insert "very ":     |The quick |brown fox |jumps over |the very lazy dog|
                   ↑ same   ↑ same    ↑ same    ↑ only 1 chunk changed
```

### Deduplication Pipeline (4 Levels)

1. **Session cache** — chunks already seen in current upload session
2. **Local metadata cache** — previously uploaded chunk metadata
3. **Global dedup query** — subset of chunks checked against all Xet storage
4. **Content-Addressed Store (CAS)** — new chunks grouped into 64 MB blocks

### What CDC Enables

| Use Case | Benefit |
|----------|---------|
| Incremental checkpoints | Only changed chunks upload (freeze layers, train adapters → most weights unchanged) |
| Fine-tune variants | Shared chunks stored once across all variants of a base model |
| Append-only logs (Parquet) | Only new row groups transfer (10K rows appended to 100K → ~10 MB instead of ~106 MB) |
| Re-upload existing data | ~8s vs ~24s for first upload (only chunk hashes move) |
| Server-side copy | Repo-to-repo copies by reference, no byte re-upload |
| Appending dataset rows | Only new rows transferred, existing chunks stay byte-identical |

### File Size Limit

Xet limits individual files to **200 GB**. At a 64 KB chunk size, a 20 GB file = 312,500 chunks.

## 6. Authentication

- **HF_TOKEN** environment variable or `huggingface-cli login`
- One token works across all clouds — no per-cloud keys to manage
- Required for both `huggingface_hub` library and `hf-mount` FUSE

## 7. Key APIs & CLI Commands

### HF CLI

```bash
# List bucket contents
hf buckets list <owner>/<bucket-name> -h
hf buckets list <owner>/<bucket-name>/path -R

# Copy files
hf cp ./model.safetensors hf://buckets/<owner>/<bucket>/model.safetensors

# Sync directories (incremental)
hf sync ./data hf://buckets/<owner>/<bucket>/data
hf sync hf://buckets/<owner>/<bucket>/data ./data

# Sync with delete (mirror)
hf sync ./data hf://buckets/<owner>/<bucket>/data --delete

# Dry-run preview
hf sync ./data hf://buckets/<owner>/<bucket>/data --dry-run

# Plan and apply
hf sync ./data hf://buckets/<owner>/<bucket>/data --plan plan.jsonl

# Pipe to stdout
hf cat hf://buckets/<owner>/<bucket>/config.json | jq .
```

### Python API

```python
from huggingface_hub import upload_bucket_files, download_bucket_files

# Upload
upload_bucket_files(
    "username/my-bucket",
    [("./model.safetensors", "models/model.safetensors"),
     ("./config.json", "config.json")]
)

# Download
download_bucket_files(
    "username/my-bucket",
    [("models/model.safetensors", "./model.safetensors")]
)
```

## 8. Performance Benchmarks

From the blog post's benchmark (Qwen SFT training):

- **Model mount on first epoch** (~30s to be ready, up to ~500 MB/s) — free, no egress cost
- **S3 alternative**: would have been billed egress (~$0.09/GB) on every read to a GPU on another cloud
- **Checkpoint writes**: ~170 MB/s (8.43 GB weights each), persisted past GPU instance

## 9. Troubleshooting

### hf-mount FUSE fails
- **Cause**: hf-mount v0.6.5+ dynamically linked against glibc 2.34+
- **Cause**: Some K8s clusters don't allow `/dev/fuse` in unprivileged containers
- **Fix**: Use `mode: COPY` instead (falls back to `huggingface_hub`)

### Slow first-epoch reads
- **Cause**: Nothing cached yet — Xet streams on demand
- **Benefit**: GPU starts almost immediately instead of blocking on full file download

## 10. References

- [HF Blog: SkyPilot + HF Storage](https://huggingface.co/blog/skypilot-hf-storage)
- [HF Storage Buckets Docs](https://huggingface.co/docs/hub/storage-buckets)
- [HF Xet Overview](https://huggingface.co/docs/hub/xet/overview)
- [HF Xet Deduplication](https://huggingface.co/docs/hub/xet/deduplication)
- [SkyPilot Storage Reference](https://docs.skypilot.co/en/latest/reference/storage.html)
- [SkyPilot HF Setup](https://docs.skypilot.co/en/latest/reference/storage.html#using-hugging-face-hub-storage)
- [hf-mount README](https://github.com/huggingface/hf-mount)
