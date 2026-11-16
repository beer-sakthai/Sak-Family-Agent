# HF Learning: Storage Buckets as Spaces Persistent Storage — Deep Dive

> author: SakThai  
> license: MIT  
> date: 2026-07-25  
> topic: hf-hub-storage-buckets-spaces-persistent-storage-deep-dive  
> extends: hf-spaces-persistent-storage-zero-cost (#94), hf-hub-storage-buckets-deep-dive (#102)

---

## Summary

Spaces persistent storage has undergone a **major architectural shift**. The old ephemeral-only disk model (16GB / 50GB per Space, lost on restart) has been augmented — and effectively superseded — by **Storage Buckets as attachable volumes**. Buckets provide S3-compatible object storage that can be mounted directly into Space containers, surviving restarts, rebuilds, and hardware upgrades.

This doc covers the full picture: how buckets work, how to attach them to Spaces, free-tier implications, and the new repo-as-volume feature that lets you mount models/datasets/Spaces as read-only volumes.

---

## 1. Spaces Disk: The Baseline

Every Space gets:
- **CPU Basic (free):** 16GB RAM, 2 CPU cores, 50GB ephemeral disk
- **All tiers:** ephemeral disk — content is **LOST** on Space restart or stop
- **No separate "persistent storage addon" anymore** — buckets are the answer

> Old (pre-2025): Spaces had a "persistent storage" toggle that added a small persistent volume.  
> **Current:** That feature is gone. The recommended path is Storage Buckets attached as volumes.

---

## 2. Storage Buckets Fundamentals

Buckets are a **fifth repo type** on the Hub (alongside models, datasets, Spaces, and Docs):

| Feature | Git Repos (Models/Datasets/Spaces) | Storage Buckets |
|---------|-----------------------------------|-----------------|
| Version control | Full Git history | No versioning — mutable |
| File operations | Git push/pull | Direct PUT/GET/DELETE |
| S3 compatible | No | Yes (AWS CLI, boto3, s5cmd) |
| Best for | Models, code, configs | Checkpoints, logs, artifacts, large volumes |
| Free tier | Generous public storage | Same quota — generous free public |
| Path scheme | `hf://datasets/...` | `hf://buckets/owner/name/path` |

### Creating a Bucket

```python
from huggingface_hub import HfApi
api = HfApi()
api.create_bucket(
    name="my-training-data",
    namespace="beer-sakthai",   # user or org
    private=False,               # public buckets count toward free tier
    region="us-east-1"           # optional, for data locality
)
```

CLI equivalent:
```bash
hf buckets create beer-sakthai/my-training-data --public
```

### Uploading Files

```bash
# Single file
hf buckets upload ./model.safetensors hf://buckets/beer-sakthai/my-bucket/model.safetensors

# Directory
hf buckets upload ./checkpoints/ hf://buckets/beer-sakthai/my-bucket/checkpoints/

# Stdin pipe
echo '{"text":"hello"}' | hf buckets upload - hf://buckets/beer-sakthai/my-bucket/data.jsonl
```

Python:
```python
api.upload_to_bucket(
    "beer-sakthai/my-bucket",
    path_or_fileobj="./checkpoint.pt",
    path_in_bucket="runs/run-001/checkpoint.pt"
)
```

### Downloading

```bash
hf buckets download hf://buckets/beer-sakthai/my-bucket/model.safetensors ./model.safetensors
hf buckets download hf://buckets/beer-sakthai/my-bucket/config.json - | jq .
```

### Syncing (Idempotent Transfer)

```bash
# Upload only changed files
hf buckets sync ./data hf://buckets/beer-sakthai/my-bucket/data

# Bidirectional: download only changed
hf buckets sync hf://buckets/beer-sakthai/my-bucket/data ./data

# With deletion (mirror local → remote exactly)
hf buckets sync ./data hf://buckets/beer-sakthai/my-bucket/data --delete

# Preview (dry run)
hf buckets sync hf://buckets/beer-sakthai/my-bucket/data ./data --dry-run
```

### Server-Side Copy

Copy between repos/buckets **without re-uploading** (only Xet hashes move):

```bash
hf buckets copy \
  --source hf://buckets/beer-sakthai/source-bucket/checkpoint.pt \
  --dest hf://buckets/beer-sakthai/dest-bucket/checkpoint.pt
```

**Limitation:** Only works source→bucket (not bucket→git repo yet). That's on the roadmap.

---

## 3. Attaching Buckets to Spaces as Volumes

This is the **killer feature** for persistent storage. Buckets are mounted into the Space container filesystem.

### Via Python API (recommended)

```python
from huggingface_hub import HfApi
api = HfApi()

# Create a Space with a bucket attached
api.create_repo(
    "my-persistent-space",
    repo_type="space",
    space_sdk="gradio",
    space_storage="cpu-basic"  # free tier
)

# Attach bucket as volume
api.add_space_volume(
    "beer-sakthai/my-persistent-space",
    bucket="beer-sakthai/my-data-bucket",
    mount_path="/data",        # where it appears inside the Space
    read_only=False            # default: read-write
)
```

### Via Space Settings UI

1. Go to your Space → Settings → "Attached Volumes" section
2. Click "Attach Volume"
3. Select bucket, mount path, read-only toggle
4. Save — Space restarts automatically with volume mounted

### Via CLI

```bash
hf space volume add beer-sakthai/my-space \
  --bucket beer-sakthai/my-data \
  --mount-path /data \
  --read-write
```

### In Your Space Code

Once mounted, files appear at the mount path:

```python
# In your Gradio app:
import os
DATA_DIR = "/data"
os.makedirs(DATA_DIR, exist_ok=True)

# Write — persists across restarts!
with open(f"{DATA_DIR}/counter.txt", "w") as f:
    f.write(str(count))

# Read — survives restarts
with open(f"{DATA_DIR}/counter.txt") as f:
    count = int(f.read())
```

**Key benefit:** Data written to `/data` survives Space restarts, rebuilds, and even hardware upgrades. The bucket is the source of truth.

### Viewing Attached Volumes

From the Space page → Actions dropdown → "Attached Volumes". Shows:
- Source bucket name
- Mount path inside container
- Access mode (read-only / read-write)

---

## 4. Mounting Models, Datasets, and Spaces as Volumes

Beyond buckets, you can mount **any Git-based repo** (model, dataset, or Space) as a **read-only volume**:

```python
api.add_space_volume(
    "beer-sakthai/my-space",
    repo="beer-sakthai/my-model",     # model repo
    repo_type="model",                 # model | dataset | space
    mount_path="/models/my-model",
    read_only=True                     # always read-only for repos
)
```

This means:
- No need to `snapshot_download()` — model files appear as local files
- Private repos require appropriate token; masked in UI for non-collaborators
- Works with any model, dataset, or Space on the Hub

---

## 5. Free Tier & Zero-Cost Strategies

### Free Storage Quota

| Plan | Public Storage | Private Storage |
|------|---------------|-----------------|
| **Free (User)** | Generous free tier (several GB) | Limited |
| **PRO** | Higher limits | 1TB included |
| **Team** | Higher limits | 1TB/seat included |
| **Enterprise** | Custom | Custom |

*Exact free limits are intentionally soft — HF asks for responsible use. Beyond the first few GB, content should be "genuinely useful to the community."*

### Zero-Cost Persistent Storage for Spaces

1. **Public buckets are free.** Create a public bucket and attach it to your Space — no charges as long as you stay within the free tier.
2. **Space disk is free (ephemeral).** Use Space disk for temp/cache data, bucket for persistent data → optimal free tier usage.
3. **Repo volumes cost nothing.** Mounting models/datasets as read-only volumes is free.
4. **Avoid storage waste:** Delete old bucket files you no longer need. Use `hf buckets sync --delete` to mirror a clean state.
5. **No per-file size limits beyond 500GB hard cap.** Most free-tier users won't hit this.

### Cost-Avoidance Checklist

- [ ] Keep bucket **public** unless data is sensitive (public storage counts toward generous free quota)
- [ ] Use `--dry-run` before big syncs to preview what will be transferred
- [ ] Clean up stale checkpoints/artifacts regularly
- [ ] Mount models as read-only volumes instead of downloading them in app code
- [ ] Use Space ephemeral disk for scratch/temp, bucket for persistence

---

## 6. S3 Compatibility

Buckets support S3-compatible tooling:

```bash
# AWS CLI
aws s3 ls s3://beer-sakthai/my-bucket/ --endpoint-url https://huggingface.co

# boto3
import boto3
s3 = boto3.client("s3", endpoint_url="https://huggingface.co")
s3.list_objects_v2(Bucket="beer-sakthai/my-bucket")
```

Data libraries that work:
- **pandas:** `pd.read_parquet("hf://buckets/owner/name/data.parquet")`
- **Dask, Spark:** mount bucket as filesystem
- **fsspec:** unified filesystem interface

---

## 7. Best Practices

### Bucket Organization
```
beer-sakthai/
├── my-bucket/
│   ├── checkpoints/       # training checkpoints
│   ├── logs/              # training logs, metrics
│   ├── artifacts/         # final model artifacts
│   └── data/              # datasets, preprocessed data
```

### Space Volume Layout
```
/ (container root)
├── app/                   # Space app code (from Git)
├── /data                  # Attached bucket (persistent)
└── /models/my-model       # Attached model repo (read-only)
```

### Performance Tips
- Use `hf buckets sync` (not upload/download) for repeated transfers — it's incremental
- Server-side copy for moving data between buckets: instant, no bandwidth cost
- Multiple buckets can be attached to a single Space at different mount points
- One bucket can be shared across multiple Spaces

---

## 8. Migration from Old Persistent Storage

If you had Spaces using the old (deprecated) persistent storage:
1. Create a Storage Bucket
2. Use `hf buckets sync` to upload existing data
3. Attach bucket to Space as volume
4. Update app code to use the new mount path
5. Remove old persistent storage attachment

---

## 9. Key Differences from Previous Model

| Aspect | Old Model (pre-2025) | New Model (2026) |
|--------|---------------------|------------------|
| Storage type | Small dedicated persistent volume | Storage Buckets as volumes |
| Capacity | Fixed small size | Up to TBs (quota-dependent) |
| Sharing | Per-Space only | Shared across Spaces |
| Persistence | Survived restarts | Survives restarts |
| Accessibility | Space only | Web UI, CLI, Python API, S3 tools |
| Cost | Free (limited) | Free public; paid for high private usage |
| Backup | Manual | Built-in via bucket sync |

---

## 10. Limitations to Know

- **Read-only repos:** Models/datasets/Spaces mounted as volumes are read-only (by design)
- **Bucket→Git not supported** for server-side copy yet
- **500GB hard limit** per single file (unchanged from Git repos)
- **Region matters:** Server-side copy requires same region source/dest
- **Free tier is soft-limited:** Responsible use expected; HF may rate-limit abusive usage

---

## References

- [Spaces Disk Usage & Storage](https://huggingface.co/docs/hub/en/spaces-storage)
- [Storage Buckets Documentation](https://huggingface.co/docs/hub/en/storage-buckets)
- [Storage Limits & Plans](https://huggingface.co/docs/hub/en/storage-limits)
- [Billing Overview](https://huggingface.co/docs/hub/en/billing)
- [HuggingFace Hub Python Library](https://huggingface.co/docs/hub/en/quick-start)
- [huggingface_hub API: create_bucket](https://huggingface.co/docs/huggingface_hub/main/en/package_reference/hf_api#huggingface_hub.HfApi.create_bucket)
- [huggingface_hub API: add_space_volume](https://huggingface.co/docs/huggingface_hub/main/en/package_reference/hf_api#huggingface_hub.HfApi.add_space_volume)
