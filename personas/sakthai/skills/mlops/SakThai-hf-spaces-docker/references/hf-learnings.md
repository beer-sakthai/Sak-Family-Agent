# HF Learnings — Deeper Dive: Zero-Cost Persistent Storage for HF Spaces

**Date:** 2026-07-24
**Topic:** `hf-spaces-persistent-storage-zero-cost` — Deep dive into persisting data across Space restarts without spending money
**Author:** SakThai
**License:** MIT

> **Core problem:** HF Spaces have **ephemeral disk** — all data written to `/data` or any container path is **lost on restart/stop**. Persisting data requires deliberate strategies. Some cost money. Beer has no income. This document exhaustively covers the free options.

---

## 1. The Ephemeral Disk Reality

Every HF Space (Gradio, Docker, Streamlit, Static) gets:

| Resource | Free Tier | PRO Tier |
|----------|-----------|----------|
| RAM | 16 GB | 16 GB+ |
| vCPU | 2 cores | 2–8 cores |
| **Disk (ephemeral)** | **50 GB** | **50 GB** |
| Disk persistence | ❌ Lost on restart | ❌ Lost on restart |

### When data is lost

Your Space disk is wiped clean when:
- The Space is **stopped** manually
- The Space **goes to sleep** after inactivity (free CPU tier only)
- The Space **restarts** after a git push / config change
- The underlying **host is migrated** (infrequent, but can happen)

### What survives

- **Nothing on disk survives.** No `/data`, no `/app`, no `/tmp` — everything is fresh on every boot.
- **Git repo contents survive** (they're in the Space's git checkout, restored on each boot from the Hub).
- **Secrets and env vars survive** (configured in Space settings, injected at runtime).
- **Storage Buckets** survive (but they cost money — see below).

---

## 2. Zero-Cost Storage Strategy Matrix

| Strategy | Free? | Persistence | Capacity | Speed | Complexity |
|----------|-------|-------------|----------|-------|------------|
| **Dataset Hub (Git LFS)** | ✅ Free | ✅ Forever | Up to repo storage limits | Slow (git push/pull) | Low |
| **Model repo as storage** | ✅ Free | ✅ Forever | Up to repo storage limits | Slow (git push/pull) | Low |
| **Hub API upload/download** | ✅ Free | ✅ Forever | Same as repo | Medium (API) | Medium |
| **Mount model/dataset volumes** | ✅ Free | ✅ Read-only | Unlimited (Hub) | Fast (mounted FS) | Low |
| **Hugging Face Storage Bucket** | ❌ Paid | ✅ Full | Unlimited | Fast (S3) | Low |
| **External S3 / cloud storage** | ❌ Paid | ✅ Full | Unlimited | Fast | Medium |
| **Git LFS in the Space's own repo** | ✅ Free | ✅ Forever | Space repo limit | Medium | Low |
| **`hf://` paths (buckets)** | ❌ Paid | ✅ Full | Unlimited | Fast | Low |

### Key insight: Datasets repos are the free persistent storage

Every Hugging Face account gets **free storage** for datasets and models repos (with Git LFS support). A Dataset repo can hold **any file type** up to its storage quota — and data pushed there persists indefinitely.

**For Beer's zero-cost constraint, Dataset repos are the only reliable free persistent storage backend for Spaces.**

---

## 3. Strategy A: Dataset Hub as Persistent Storage (Best Free Option)

### How it works

Your Space writes data to ephemeral disk at runtime. On shutdown (or periodically), it pushes that data to a Dataset repo on the Hub. On restart, it pulls the latest data from the same repo.

### Architecture

```
┌──────────────┐     git push     ┌────────────────┐
│   HF Space   │ ──────────────▶  │  Dataset Repo   │
│  (ephemeral) │ ◀──────────────  │  (persistent)   │
└──────────────┘     git pull     └────────────────┘
```

### Implementation (Python)

```python
import os
import json
from huggingface_hub import HfApi, create_repo

api = HfApi()
DATASET_REPO = "beer-sakthai/my-space-data"  # your dataset repo

def init_storage():
    """Ensure the dataset repo exists."""
    try:
        create_repo(DATASET_REPO, repo_type="dataset", exist_ok=True)
        print(f"Dataset repo {DATASET_REPO} ready")
    except Exception as e:
        print(f"Could not create repo: {e}")

def save_state(data: dict, filename="state.json"):
    """Save data to the dataset repo (ephemeral → persistent)."""
    # Write to local
    with open(f"/tmp/{filename}", "w") as f:
        json.dump(data, f)
    # Upload via API (no git needed)
    api.upload_file(
        path_or_fileobj=f"/tmp/{filename}",
        path_in_repo=filename,
        repo_id=DATASET_REPO,
        repo_type="dataset",
    )

def load_state(filename="state.json") -> dict:
    """Load data from the dataset repo (persistent → ephemeral)."""
    try:
        return api.hf_hub_download(
            repo_id=DATASET_REPO,
            filename=filename,
            repo_type="dataset",
        )
    except Exception:
        return {}  # First run — no data yet

# Usage from a Space
init_storage()
# ... during runtime, periodically:
# save_state({"counter": 42, "last_run": "2026-07-24"})
# On restart:
# state = load_state()
```

### Upload strategies

| Method | Pros | Cons | Best for |
|--------|------|------|----------|
| `api.upload_file()` | Simple, no git | Per-file, no directory sync | Small state (JSON, config) |
| `api.snapshot_download()` + `api.upload_folder()` | Directory sync | Two-step, slower | Checkpoints, logs |
| Git LFS (subprocess) | Full git power | Heavy, needs git | Large binary files |
| `huggingface_hub` commit API | Atomic multi-file | More code | Transactional updates |

### Limitations of this approach

1. **Latency:** Each upload/download is a full HTTP round-trip. Not suitable for real-time sync.
2. **Rate limits:** HF has API rate limits (though generous for personal accounts).
3. **Storage limits:** Dataset repos have size limits — check your account's storage quota at `hf.co/settings/billing`.
4. **Not a filesystem:** You can't `open()` files from a Dataset repo as if they were local. You must explicitly download them.
5. **Git history bloat:** Every upload creates a new commit. Over time, the repo history grows. For frequently-changing state, consider using the `hf_api.upload_file()` method (still creates a commit, but is simpler than full git).

---

## 4. Strategy B: Mounting Models/Datasets as Read-Only Volumes (Free)

Hugging Face lets you mount **any public model or dataset repo** as a read-only volume in your Space — **free of charge**.

### How to do it

Via `huggingface_hub` Python API:

```python
from huggingface_hub import update_space_volume

# Mount a dataset as a read-only volume
update_space_volume(
    repo_id="username/my-dataset",   # the source repo
    space_id="username/my-space",    # your Space
    repo_type="dataset",
    mount_path="/data/models",       # where it appears in the container
    read_only=True,                  # always read-only for non-bucket sources
)
```

Via the **`hf` CLI**:

```bash
hf spaces volume add my-space \
  --repo username/my-dataset \
  --repo-type dataset \
  --mount-path /data/reference
```

### What shows up

Once mounted, the repo's contents appear as local files at `mount_path` inside your Space container. You can read them with normal file I/O:

```python
with open("/data/reference/some-file.json", "r") as f:
    data = json.load(f)
```

### Key constraints

| Property | Value |
|----------|-------|
| **Cost** | ✅ Free |
| **Writable** | ❌ Read-only only (for non-bucket repos) |
| **What can be mounted** | Models, datasets, other Spaces (all as read-only) |
| **Private repos** | ✅ Yes (Space owner must have access) |
| **Visibility** | If volume is private → other users see masked `****/******` |
| **Removal** | Via Space settings dropdown → "Volumes" |

### When to use this

- Your Space needs to **reference large datasets** without downloading them at startup
- You want to serve a **static model** whose weights live on the Hub
- You're building a **data processing Space** that needs reference corpora
- You want to share **configuration files** from a central repo

### Pro tip: Volume + Dataset write-back hybrid

Combine Strategy B (mount for reads) with Strategy A (dataset repo upload for writes):

```python
# Read reference data from mounted volume (free, fast, persistent)
with open("/data/reference/model_config.json") as f:
    config = json.load(f)

# Process and produce results
results = process_data(config)

# Save results to Dataset repo (free, persistent, slower)
api.upload_file(
    path_or_fileobj=json.dumps(results).encode(),
    path_in_repo=f"outputs/run_{timestamp}.json",
    repo_id="beer-sakthai/my-space-data",
    repo_type="dataset",
)
```

---

## 5. Strategy C: Using the Space's Own Git Repo (Free, but Limited)

Every Space is a git repository. You can commit and push data back to the Space's own repo.

```python
import subprocess
import os

def save_to_git(filepath, content):
    """Commit a file to the Space's own git repo."""
    with open(filepath, "w") as f:
        f.write(content)
    subprocess.run(["git", "add", filepath], cwd=os.getenv("SPACE_REPO_NAME", "."))
    subprocess.run(["git", "commit", "-m", "auto-save state"], cwd=".")
    subprocess.run(["git", "push"], cwd=".")
```

### Why this is usually a bad idea

| Issue | Explanation |
|-------|-------------|
| **Restart loop** | Pushing to the Space repo triggers a **rebuild + restart** — you'd create an infinite loop |
| **Commit history bloat** | Frequent commits pollute the repo history |
| **Race condition** | If two pushes happen simultaneously, one fails |
| **Git credentials** | Need HF_TOKEN with write access configured in the Space |

### Only do this for

- **One-shot initialization**: Generating a `README.md` or config on first boot
- **Admin-triggered saves**: Only committing when a user explicitly clicks "Save"
- **Separate data repo**: Committing to a **different** repo (see Strategy A) — not the Space's own repo

---

## 6. Strategy D: URL-Based External Storage (Free, But Limited)

For small amounts of data, you can use free external services:

| Service | Free Tier | Limitation | Persistence |
|---------|-----------|------------|-------------|
| **GitHub Gist API** | Unlimited gists | 10 MB per file, 10 MB per month unauthenticated | ✅ Yes |
| **pastebin.com API** | Free tier | 512 KB per paste, rate limited | ✅ Yes |
| **Your own git repo** | Free | Set up required | ✅ Yes |
| **IPFS (via free gateways)** | Varies | Slow, unreliable | ❌ Can be lost |

**Recommendation:** Don't use these for Spaces. The Dataset Hub approach (Strategy A) is more reliable and uses the same auth/API you already have.

---

## 7. Storage Buckets — What You Get for Free vs Paid

Storage Buckets are the **official** persistent storage for HF Spaces. Here's the pricing reality:

| Plan | Bucket Storage Included | Additional |
|------|------------------------|------------|
| **Free personal** | ❌ **No bucket storage** | You must buy storage |
| **PRO** | 50 GB included | $0.023/GB/month |
| **Team** | 100 GB included | $0.023/GB/month |
| **Enterprise** | 500 GB included | $0.023/GB/month |

### S3-compatible API (for bucketed data)

If you do have a bucket, you can use standard S3 tools:

```bash
# Using AWS CLI
aws s3 ls s3://my-bucket --endpoint-url https://huggingface.co
```

```python
# Using boto3
import boto3
client = boto3.client(
    "s3",
    endpoint_url="https://huggingface.co",
    aws_access_key_id="your-hf-username",
    aws_secret_access_key="your-hf-token",
)
```

**For Beer's zero-cost constraint:** Buckets are not an option. Skip them and use Dataset repos.

---

## 8. ZeroGPU + Storage Interaction

ZeroGPU Spaces have **extra constraints** on storage:

| Aspect | Detail |
|--------|--------|
| **Disk** | Same ephemeral 50 GB — lost on restart |
| **GPU quota** | 5 min/day (free), resets 24h after first use |
| **Sleep** | No sleep on free ZeroGPU (active always, until stopped) |
| **Disk persistence** | ❌ Same as regular Spaces — restarts wipe data |
| **Model weight caching** | ✅ PyTorch CUDA emulation at module load, real GPU in `@spaces.GPU` |

### ZeroGPU storage best practices

1. **Load models at module level** (outside `@spaces.GPU`) — they're cached via CUDA emulation
2. **Use `@spaces.GPU(duration=60)`** with accurate duration estimates to maximize queue priority
3. **Push results to Dataset repo** after GPU computation completes
4. **Pull reference data from mounted volumes** (Strategy B) before GPU work

```python
import spaces
from diffusers import DiffusionPipeline
from huggingface_hub import HfApi

# Load model at module level (CUDA emulation outside @spaces.GPU)
pipe = DiffusionPipeline.from_pretrained("black-forest-labs/FLUX.1-dev")
pipe.to("cuda")

api = HfApi()

@spaces.GPU(duration=120)
def generate(prompt: str):
    images = pipe(prompt).images

    # Save results to Dataset repo for persistence
    for i, img in enumerate(images):
        img.save(f"/tmp/output_{i}.png")
    api.upload_folder(
        folder_path="/tmp",
        repo_id="beer-sakthai/my-space-data",
        repo_type="dataset",
        path_in_repo=f"outputs/{prompt[:20]}",
    )
    return images
```

---

## 9. Practical Patterns for Beer's Use Case

### Pattern 1: Chat history persistence (Gradio Space)

```python
import json
import os
from huggingface_hub import HfApi
from pathlib import Path

api = HfApi()
DATA_REPO = "beer-sakthai/space-chat-history"

def load_history() -> list:
    """Load chat history from persistent dataset repo."""
    try:
        path = api.hf_hub_download(
            repo_id=DATA_REPO,
            filename="chat_history.json",
            repo_type="dataset",
        )
        with open(path) as f:
            return json.load(f)
    except Exception:
        return []

def save_history(history: list):
    """Save chat history back to dataset repo."""
    api.upload_file(
        path_or_fileobj=json.dumps(history).encode(),
        path_in_repo="chat_history.json",
        repo_id=DATA_REPO,
        repo_type="dataset",
    )

# In your Gradio app:
history = load_history()
# ... user interacts ...
save_history(updated_history)
```

### Pattern 2: Periodic snapshot (long-running Spaces)

For Spaces that run continuously (ZeroGPU or paid), take periodic snapshots:

```python
import time
import json
from huggingface_hub import HfApi

api = HfApi()
SNAPSHOT_REPO = "beer-sakthai/space-snapshots"

def snapshot_loop(interval_seconds=300):
    """Every N seconds, save state to persistent storage."""
    while True:
        time.sleep(interval_seconds)
        state = collect_current_state()
        api.upload_file(
            path_or_fileobj=json.dumps(state).encode(),
            path_in_repo=f"snapshots/snapshot_{int(time.time())}.json",
            repo_id=SNAPSHOT_REPO,
            repo_type="dataset",
        )
```

### Pattern 3: First-boot initialization

Check if this is a fresh boot (no persisted state) vs a restart:

```python
from huggingface_hub import HfApi
import os

api = HfApi()

def is_first_boot():
    """Check if the Space has ever persisted state before."""
    try:
        api.file_exists(
            repo_id="beer-sakthai/space-metadata",
            filename="boot_count.json",
            repo_type="dataset",
        )
        return False
    except Exception:
        return True

# On restart: load persisted data or start fresh
boot_count = 0
if not is_first_boot():
    path = api.hf_hub_download(
        repo_id="beer-sakthai/space-metadata",
        filename="boot_count.json",
        repo_type="dataset",
    )
    with open(path) as f:
        data = json.load(f)
        boot_count = data.get("count", 0) + 1
else:
    boot_count = 1

# Save incremented count
api.upload_file(
    path_or_fileobj=json.dumps({"count": boot_count}).encode(),
    path_in_repo="boot_count.json",
    repo_id="beer-sakthai/space-metadata",
    repo_type="dataset",
)
```

---

## 10. Limitations & Pitfalls (Summary)

### What you CANNOT do for free

| Goal | Why it's not free |
|------|-------------------|
| **Real-time file sync** | Dataset pushes are too slow for sub-second sync |
| **Writeable mounted storage** | Only buckets support R/W mounts |
| **>1 GB persistent storage** | Dataset repos have limits — check your plan |
| **S3-compatible API** | Only buckets have S3 API — and buckets cost |
| **Filesystem-level persistence** | No FUSE or NFS mounts for free repos |
| **Database-like random access** | Each read/write is a full HTTP round-trip |

### What to watch out for

1. **API rate limits**: ~100 requests/min on free tier for `huggingface_hub` API
2. **Upload token permissions**: Your Space's HF_TOKEN needs `write` permission on the target dataset repo
3. **File size**: Individual file uploads via API are limited to ~50 MB
4. **Large files**: Use Git LFS directly for files >50 MB (more complex, needs git credentials in the Space)
5. **Concurrent writes**: Two Spaces writing to the same file = last write wins. Use unique filenames with timestamps.
6. **404 on first boot**: Always wrap `hf_hub_download` in try/except — the file won't exist on the very first run
7. **Space doesn't autoscale**: Disk is fixed at 50 GB regardless of how much data you push to the Hub

---

## 11. Reference: All Data Flow Options in HF Spaces

```
                     ┌──────────────────────────────────────┐
                     │           HF Space Container          │
                     │                                      │
  Startup: ─────────▶│  ├── /app (git checkout from repo)   │
  git clone repo     │  ├── /data (ephemeral, 50GB max)     │
                     │  ├── /tmp (ephemeral)                 │
                     │  └── /mnt/bucket (if attached)        │
                     │                                      │
                     └───────────┬──────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
   ┌──────────┐          ┌──────────────┐        ┌──────────┐
   │ Dataset  │          │ Storage      │        │ Model/   │
   │ Repo     │          │ Bucket       │        │ Dataset  │
   │ (free)   │          │ (paid)       │        │ Mount    │
   │          │          │              │        │ (free    │
   │ Git LFS  │          │ S3 API       │        │ read-    │
   │ upload   │          │ R/W mount    │        │ only)    │
   └──────────┘          └──────────────┘        └──────────┘
    Best for:              Best for:              Best for:
    State, logs,           Large data,            Reference data,
    config, outputs        checkpoints,           models, corpora
    (free)                 databases (paid)       (free, RO)
```

**Recommendation for Beer:** Use **Strategy A (Dataset Hub)** for any data your Space needs to write persistently, and **Strategy B (mounted volumes)** for any reference data it needs to read. Together, they cover all persistence needs at zero cost.
