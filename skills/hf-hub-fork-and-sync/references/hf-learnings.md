# HF Hub Fork & Sync — Complete Source Reference (Deep Dive)

> *Entry 378 → 379 in cumulative HF learnings*
> *Topic: `hf-hub-fork-and-sync` (deep-dive: sync_bucket, sync_job_volume, fork lifecycle, CLI workflows)*
> *Date: 2026-07-25*
> *Sources: `huggingface_hub` source code (`HfApi`), `hf` CLI, HF REST API*

---

## Architecture: What "Fork" Actually Means on HF Hub

Unlike GitHub (where a fork creates a linked upstream/downstream relationship), **HF Hub does not have a true fork relationship**. A "fork" via `duplicate_repo()` is a **server-side git clone** — it copies all commits, history, LFS objects, and branch structure into a brand-new, independent repository. There is:

- ✅ No automatic link back to the "parent" repo
- ✅ No "Fetch upstream" button in the UI
- ✅ No fork network graph
- ✅ No `/forks` REST endpoint (returns 404)
- ✅ No `source` or `forkedFrom` metadata in `/api/models` responses

The only trace of origin is that the git history itself contains the original commits. If a user deletes their fork, the parent repo is unaffected, and vice versa.

**Implication:** To "sync" a fork with upstream changes, you must either:
1. **Re-fork** (`duplicate_repo` again — overwrites the old fork)
2. **Use git** (add upstream remote, fetch, rebase/merge, push)
3. **Selective file copy** (`copy_files` or `hf repos cp` for individual changed files)

---

## 1. `duplicate_repo()` — Full Server-Side Repo Duplication

*(Full details already documented in previous entry — this section adds CLI perspective and practical workflows.)*

**Python API:**
```python
from huggingface_hub import duplicate_repo

# Simple fork to your account
duplicate_repo("openai-community/gpt2")
# → RepoUrl('https://huggingface.co/<you>/gpt2')

# Fork with explicit namespace and type
duplicate_repo("openai/gdpval", to_id="myorg/my-gdpval", repo_type="dataset")
```

**CLI equivalent:**
```bash
# Simple fork
hf repos duplicate openai-community/gpt2

# Fork with type and target
hf repos duplicate openai/gdpval myorg/my-gdpval --type dataset

# Fork a Space with hardware and env vars
hf repos duplicate multimodalart/dreambooth-training my-dream \
  --type space --flavor t4-medium --sleep-time -1 \
  --env PUBLIC_VAR=value \
  --secrets API_KEY=sk-...

# Fork with volume mounts
hf repos duplicate org/my-space my-space --type space \
  -v hf://org/my-model:/models \
  -v hf://buckets/org/b:/data:ro

# Quiet fork (suppress output)
hf repos duplicate openai-community/gpt2 -q
```

**Key CLI options not in Python API directly:**
| Option | Description |
|--------|-------------|
| `--flavor` | Hardware flavor for Spaces (`cpu-basic`, `t4-medium`, `l4x4`, etc.) |
| `--secrets-file` | Read secrets from a file |
| `--env-file` | Read env vars from a file |
| `-v, --volume` | Mount volumes at fork time (repeated) |
| `--format json` | Machine-readable output |
| `-q` | Quiet — just print the new repo ID |

---

## 2. Fork Re-creation (Forced Re-Sync)

The simplest "sync" is to re-fork, overwriting the old fork:

```python
from huggingface_hub import duplicate_repo

# Re-create fork (overwrites existing repo at myorg/my-gpt2)
duplicate_repo("openai-community/gpt2", to_id="myorg/my-gpt2", exist_ok=True)
```

```bash
# CLI: re-create with --exist-ok
hf repos duplicate openai-community/gpt2 myorg/my-gpt2 --exist-ok
```

**Warning:** `duplicate_repo()` with `exist_ok=True` **overwrites** the target repo entirely. Any local customizations (branches, additional files, model fine-tunes) are lost. Use only for fresh syncs where you haven't made changes.

---

## 3. Git-Based Fork Sync (Upstream Remote)

For keeping customizations while pulling upstream changes, use native git:

```bash
# Clone your fork locally
git clone https://huggingface.co/<you>/<model>
cd <model>

# Add upstream remote (the original repo)
git remote add upstream https://huggingface.co/<original_author>/<model>

# Fetch upstream changes
git fetch upstream

# Merge upstream into your fork's main branch
git checkout main
git merge upstream/main

# Push changes back to your HF fork
git push origin main
```

**Zero-cost note:** Git operations against HF Hub are free. This approach only costs local disk space and bandwidth.

---

## 4. `copy_files()` — Selective File Sync

For syncing only specific files (e.g., updated config files, tokenizer files) without recreating the entire fork:

**Python:**
```python
from huggingface_hub import copy_files

# Copy a single file between repos
copy_files(
    "hf://openai-community/gpt2/tokenizer.json",
    "hf://myorg/my-gpt2/tokenizer.json"
)

# Copy a folder (rsync-style with trailing /)
copy_files(
    "hf://openai-community/gpt2/vocab/",
    "hf://myorg/my-gpt2/vocab/"
)

# Copy from dataset to dataset
copy_files(
    "hf://datasets/org/original-data/train/",
    "hf://datasets/me/forked-data/train/"
)

# Copy from bucket to repo
copy_files(
    "hf://buckets/my-bucket/models/weights.safetensors",
    "hf://myorg/my-model/weights.safetensors"
)
```

**CLI:**
```bash
# Copy a single file between repos
hf repos cp hf://openai-community/gpt2/config.json hf://myorg/my-gpt2/config.json

# Copy folder contents (rsync-style)
hf repos cp hf://openai-community/gpt2/vocab/ hf://myorg/my-gpt2/vocab/

# Copy from dataset
hf repos cp hf://datasets/org/original-data/train/ hf://datasets/me/forked-data/train/
```

**Shortcut: `hf cp` is the same as `hf repos cp`:**
```bash
hf cp hf://source/model/config.json hf://dest/model/config.json
```

**Limitations:**
- ❌ Bucket-to-repo copies not supported
- ❌ Cross-region copies not supported (error if regions differ)
- ⚠️ `.gitattributes` auto-excluded for repo→bucket copies
- ⚠️ Each copy creates a new commit on the destination repo
- ✅ Works with `hf://` URIs for models (`hf://user/model`), datasets (`hf://datasets/user/data`), spaces (`hf://spaces/user/space`), and buckets (`hf://buckets/user/b`)

---

## 5. `sync_bucket()` — Rsync-Style Local↔Bucket Sync

**What it is:** A full bidirectional sync between a local directory and a Hugging Face bucket (S3-compatible storage on the Hub). This is the `hf sync` CLI command.

**Python API:**
```python
from huggingface_hub import HfApi
api = HfApi()

# Upload local data to bucket
plan = api.sync_bucket(
    source="./training-data",
    dest="hf://buckets/username/my-bucket/training-data",
)

# Download bucket to local
api.sync_bucket(
    source="hf://buckets/username/my-bucket/checkpoints",
    dest="./checkpoints",
)

# Sync with delete (remove files on destination not present in source)
api.sync_bucket(
    "./data", "hf://buckets/username/my-bucket/data",
    delete=True,
    include=["*safetensors"],
)

# Dry run — preview without executing
plan = api.sync_bucket("./data", "hf://buckets/username/my-bucket/data", dry_run=True)
print(plan.summary())
# → {'uploads': 3, 'downloads': 0, 'deletes': 0, 'skips': 1, 'total_size': 4096}

# Save plan to JSONL for review, then apply
api.sync_bucket("./data", "hf://buckets/username/my-bucket/data", plan="sync-plan.jsonl")
api.sync_bucket(apply="sync-plan.jsonl")
```

**CLI:**
```bash
# Upload (local → bucket)
hf sync ./training-data hf://buckets/username/my-bucket

# Download (bucket → local)
hf sync hf://buckets/username/my-bucket/checkpoints ./checkpoints

# Dry run (JSONL preview)
hf sync ./data hf://buckets/username/my-bucket --dry-run

# Delete remote files not present locally
hf sync ./data hf://buckets/username/my-bucket --delete

# Include/exclude filtering
hf sync ./data hf://buckets/username/my-bucket --include "*.safetensors" --exclude "*.tmp"

# Save plan file, then apply
hf sync ./data hf://buckets/username/my-bucket --plan sync-plan.jsonl
hf sync --apply sync-plan.jsonl
```

**Sync rules (rsync-inspired):**
| Flag | Behavior |
|------|----------|
| Default | Copy new/changed files based on modification time + size |
| `--delete` | Remove destination files not in source |
| `--ignore-times` | Only compare by size (ignore mtime) |
| `--ignore-sizes` | Only compare by mtime (ignore size) |
| `--existing` | Only update files that already exist on receiver |
| `--ignore-existing` | Only create new files, skip updates |
| `--include` / `--exclude` | fnmatch-style pattern filtering |
| `--filter-from` | Read include/exclude rules from a file |

**Return value:** `SyncPlan` object with `.summary()` giving transfer statistics.

**Zero-cost:** Bucket operations and sync are free within storage limits. Buckets have 50 GB free per user.

---

## 6. `sync_job_volume()` — Jobs Data Sync

**What it is:** A convenience wrapper that syncs a local directory to a bucket and returns a `Volume` object ready to mount in a Job (via `run_job`, `run_uv_job`, `create_scheduled_job`).

**Python API:**
```python
from huggingface_hub import sync_job_volume, run_uv_job

# Sync training data and mount in job (read-only)
volume = sync_job_volume(
    source="./training-data",
    mount_path="/data",
)
run_uv_job(
    "train.py",
    script_args=["--learning-rate", "0.01"],
    volumes=[volume],
)

# Read-write volume for output retrieval
volume = sync_job_volume(
    source="./outputs",
    mount_path="/outputs",
    read_only=False,
)
job = run_uv_job("process.py", volumes=[volume])
```

**How it works:**
1. Auto-creates a private bucket at `{namespace}/jobs-artifacts` (if not exist)
2. Syncs local directory to `hf://buckets/{namespace}/jobs-artifacts/{remote_name}`
3. Returns `Volume(type="bucket", source=bucket_id, mount_path=mount_path, path=folder, read_only=bool)`
4. If source directory is empty, uploads a `.keep` placeholder so the volume can still be mounted

**Key details:**
| Parameter | Description |
|-----------|-------------|
| `source` | Local directory path (required, must exist) |
| `mount_path` | Absolute path inside container, e.g. `/data` |
| `remote_name` | Custom bucket subfolder name. Default: `{dirname}-{hostname-hash}` |
| `read_only` | Mount read-only (default `True`). Set `False` for output volumes |
| `namespace` | Bucket owner namespace. Defaults to current user |

**Zero-cost:** Buckets and Jobs have free tiers. Only pay for compute if using paid hardware tiers.

---

## 7. Practical Fork Sync Workflows

### Scenario A: Fresh Fork (No Local Changes)
Goal: Get an exact copy of a model/dataset/Space.

```bash
# One-liner
hf repos duplicate google/gemma-2b my-gemma-2b --exist-ok
```

### Scenario B: Custom Fork with Upstream Merge
Goal: Keep your custom fork in sync with upstream while preserving modifications.

```bash
# Clone your fork
git clone https://huggingface.co/<you>/my-gemma-2b
cd my-gemma-2b

# Add upstream
git remote add upstream https://huggingface.co/google/gemma-2b

# Periodic sync:
git fetch upstream
git checkout main
git merge upstream/main
# Resolve conflicts, then:
git push origin main
```

### Scenario C: Selective File Sync
Goal: Only pull specific updated files from upstream without merging history.

```python
from huggingface_hub import copy_files

# Sync only the config and tokenizer
for file in ["config.json", "tokenizer.json", "generation_config.json"]:
    copy_files(
        f"hf://google/gemma-2b/{file}",
        f"hf://<you>/my-gemma-2b/{file}",
    )
```

### Scenario D: Periodic Re-Create
Goal: Automated fresh fork (CI/CD pipeline).

```bash
# In a cron/CI job:
hf repos duplicate google/gemma-2b my-gemma-2b --exist-ok --quiet
```

### Scenario E: Bucket-Based Data Sync for Training
Goal: Keep training data and checkpoints synced between local and cloud.

```bash
# Upload new training data
hf sync ./training-data hf://buckets/me/jobs-artifacts/training-data

# Download latest checkpoints
hf sync hf://buckets/me/jobs-artifacts/checkpoints ./checkpoints

# Bidirectional sync with cleanup
hf sync ./experiments hf://buckets/me/jobs-artifacts/experiments --delete --verbose
```

---

## 8. Storage Regions and Cross-Region Limitations

HF Hub operates multiple storage regions (US, EU, Asia). This affects fork and copy operations:

| Operation | Cross-Region Support |
|-----------|---------------------|
| `duplicate_repo()` | ✅ Works (server-side, HF handles routing) |
| `copy_files()` / `hf cp` | ❌ Fails — must be same region |
| `sync_bucket()` | ✅ Works (uses standard HTTP) |
| Git push/pull | ✅ Works globally |

**Workaround for cross-region copy:** Download to local, then upload:
```bash
# Download from source region
hf download source-org/model config.json

# Upload to destination
hf upload config.json dest-org/model config.json
```

---

## 9. Zero-Cost Patterns

| Operation | Cost | Notes |
|-----------|------|-------|
| `duplicate_repo()` | **Free** | Within storage limits (50 GB default) |
| `copy_files()` | **Free** | Same-region only |
| `sync_bucket()` | **Free** | Buckets: 50 GB free storage |
| `sync_job_volume()` | **Free** | Bucket storage free; Jobs compute tier separate |
| Git clone/push/pull | **Free** | Free bandwidth for git operations |
| Re-fork (`--exist-ok`) | **Free** | Overwrites existing repo |
| Cross-region copy | **Free** | VIA manual download/upload (no egress fees) |

**Storage costs:**
- Forks count against your account's total storage quota (50 GB free for most users)
- Buckets: 50 GB free, larger plans available via billing
- To save storage: delete old forks you no longer need using `hf repos delete <repo>` or `api.delete_repo()`

---

## 10. Related CLI Commands Reference

| Command | Purpose | Equivalent Python API |
|---------|---------|---------------------|
| `hf repos duplicate` | Fork a repo | `duplicate_repo()` |
| `hf repos cp` | Copy files between repos | `copy_files()` |
| `hf cp` | Copy files (alias) | `copy_files()` |
| `hf sync` | Sync local↔bucket | `sync_bucket()` |
| `hf upload` | Upload file/folder | `upload_file()` / `upload_folder()` |
| `hf download` | Download file/folder | `hf_hub_download()` / `snapshot_download()` |
| `hf repos create` | Create empty repo | `create_repo()` |
| `hf repos delete` | Delete repo | `delete_repo()` |
| `hf repos list` | List repos with storage | `list_repos()` |
| `hf repos settings` | Update repo settings | `update_repo_settings()` |

---

## 11. API Comparison: GitHub Fork vs. HF Duplicate

| Aspect | GitHub Fork | HF `duplicate_repo()` |
|--------|------------|----------------------|
| Relationship tracking | ✅ Linked fork network | ❌ No link (independent clone) |
| "Sync fork" button | ✅ Yes (fetch upstream) | ❌ No built-in UI |
| Network graph | ✅ Yes | ❌ Not available |
| `/forks` endpoint | ✅ Yes | ❌ 404 (does not exist) |
| Preserves history | ✅ Full git history | ✅ Full git history |
| LFS objects | ✅ Copied | ✅ Copied |
| Overwrite existing | ❌ Must delete first | ✅ `exist_ok=True` |
| Server-side | ✅ Yes | ✅ Yes |
| Storage cost | ✅ Free (within limits) | ✅ Free (within limits) |

**Bottom line:** HF `duplicate_repo()` is better described as "server-side clone" or "copy" rather than "fork" in the GitHub sense. The term "fork" in HF UI and CLI is legacy/convenience nomenclature.

---

## 12. Source Reference — Key Implementation Details

### `sync_bucket` internal flow:
1. Determines direction (local→bucket or bucket→local) based on which argument is an `hf://` URI
2. Walks source directory tree (or lists bucket objects)
3. Compares files by mtime + size (or as configured by flags)
4. Builds a `SyncPlan` with uploads, downloads, deletes, skips
5. If `dry_run=True`, returns plan without executing
6. If `plan=path`, saves plan as JSONL for review
7. If `apply=path`, loads saved plan and executes it
8. Otherwise executes immediately

### `sync_job_volume` internal flow:
1. Validates mount_path starts with `/`
2. Validates source is an existing directory
3. Creates private bucket `{namespace}/jobs-artifacts` (`create_bucket`)
4. Verifies bucket privacy (warns if public)
5. Calls `sync_bucket` to upload files
6. Creates `.keep` placeholder if directory is empty
7. Returns `Volume(type="bucket", ...)` ready for Jobs API

---

## 13. Complete API Error Handling

| Error | When | Recovery |
|-------|------|----------|
| `RepositoryNotFoundError` (404) | Source or target repo doesn't exist | Check `from_id` and `to_id` spelling |
| `HfHubHTTPError` (409) | Target already exists and `exist_ok=False` | Set `exist_ok=True` or use different name |
| `HfHubHTTPError` (403) | No permission to duplicate source | Check token scopes; source may be private |
| `ValueError` | Invalid `repo_type` | Use `"model"`, `"dataset"`, or `"space"` |
| `ValueError` | `private` and `visibility` both set | Use one or the other |
| `EnvironmentError` | Cross-region copy | Download locally, then upload |
| `HfHubHTTPError` (404) in sync | Bucket doesn't exist | Auto-created in `sync_job_volume` but not in `sync_bucket` |
