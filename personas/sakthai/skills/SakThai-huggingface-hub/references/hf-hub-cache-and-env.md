# huggingface_hub: Cache Internals, Environment Variables & HfApi Utilities

Everything `huggingface_hub` (the Python library) provides beyond `InferenceClient` — the cache system, environment configuration, and programmatic repository management with `HfApi`.

> **Key rule:** All environment variables are read **at import time** of `huggingface_hub`. Set them before importing or they won't take effect.

---

## 1. Environment Variables Reference

| Variable | Default | Purpose |
|---|---|---|
| `HF_HOME` | `~/.cache/huggingface` (or `$XDG_CACHE_HOME/huggingface`) | Root directory for token, cache, and config. Overrides the default location. |
| `HF_HUB_CACHE` | `$HF_HOME/hub` | Where models, datasets, and Spaces are cached locally. |
| `HF_XET_CACHE` | `$HF_HOME/xet` | Xet chunk cache — byte ranges from files managed by Xet backend. |
| `HF_ASSETS_CACHE` | `$HF_HOME/assets` | Assets created by downstream libraries (preprocessed data, logs, etc.). |
| `HF_TOKEN` | — | User Access Token. Overrides any stored token. |
| `HF_TOKEN_PATH` | `$HF_HOME/token` | Where the token file is stored/read. |
| `HF_ENDPOINT` | `https://huggingface.co` | Hub API base URL. Set for Private Hub. |
| `HF_HUB_VERBOSITY` | `"warning"` | Logger verbosity: `debug`, `info`, `warning`, `error`, `critical`. |
| `HF_HUB_ETAG_TIMEOUT` | `10` | Seconds to wait for metadata before falling back to cached files. |
| `HF_HUB_DOWNLOAD_TIMEOUT` | `10` | Seconds to wait per download request before `TimeoutError`. |
| `HF_HUB_ENABLE_HF_TRANSFER` | `0` | Set to `1` to use Rust-based `hf_transfer` for faster downloads. |
| `HF_HUB_DISABLE_SYMLINKS_WARNING` | `0` | Set to `1` to suppress the symlink warning on Windows. |
| `HF_INFERENCE_ENDPOINT` | `https://api-inference.huggingface.co` | Inference API base URL. |

### Setting them properly (before import)

```python
import os
os.environ["HF_HOME"] = "/custom/path/huggingface"
os.environ["HF_HUB_CACHE"] = "/custom/path/hub"
os.environ["HF_TOKEN"] = "hf_..."

# Now import huggingface_hub
from huggingface_hub import HfApi, hf_hub_download
```

For shell scripts:
```bash
export HF_HOME=/mnt/storage/huggingface
export HF_HUB_CACHE=/mnt/storage/hub
export HF_TOKEN=hf_xxx
```

---

## 2. Cache System Deep Dive

The cache was redesigned in `huggingface_hub` v0.8.0. It's the **central cache shared across all Hub-dependent libraries** (transformers, diffusers, etc.).

### Directory Structure

```
<CACHE_DIR>  (default: ~/.cache/huggingface/hub)
├── models--bert-base-uncased
│   ├── refs/
│   │   └── main          # contains the commit hash of latest main branch
│   ├── blobs/
│   │   ├── ab12cd34...   # files named by their hash (content-addressable)
│   │   └── ef56gh78...
│   ├── snapshots/
│   │   └── a1b2c3d4...   # symlinks to blobs, one folder per commit
│   │       ├── config.json -> ../../blobs/ab12cd34...
│   │       └── model.safetensors -> ../../blobs/ef56gh78...
│   └── trees/            # file listings per commit (metadata)
├── datasets--glue/
│   └── ...
└── spaces--dalle-mini--dalle-mini/
    └── ...
```

- **`refs/`**: Points named refs (branch/tag) to commit hashes. Updated on download.
- **`blobs/`**: Content-addressed storage. File name = SHA256 hash of contents.
- **`snapshots/`**: One folder per commit, full of symlinks into `blobs/`. This is how multiple revisions share the same files without duplication.
- **`trees/`**: Cached file listings per commit (for fast `repo_info`-style lookups).

On Windows, when developer mode is off and symlinks are unavailable, files are **copied** into snapshots instead of symlinked.

### scan_cache_dir() — Programmatic Cache Inspection

```python
from huggingface_hub import scan_cache_dir

cache_info = scan_cache_dir()  # or scan_cache_dir("/custom/cache/path")

# Inspect repos in cache
print(f"Total size: {cache_info.size_on_disk / 1e9:.2f} GB")
for repo in cache_info.repos:
    print(f"  {repo.repo_id:50s}  {repo.size_on_disk / 1e6:.1f} MB  "
          f"({len(repo.revisions)} revisions)")
    for rev in repo.revisions:
        print(f"    └─ {rev.commit_hash[:12]}  "
              f"{rev.size_on_disk / 1e6:.1f} MB  "
              f"{'ref: ' + str(rev.refs) if rev.refs else 'detached'}")
```

#### CachedRepoInfo properties

| Field | Type | Description |
|---|---|---|
| `repo_id` | `str` | Full repo ID (e.g. `bert-base-uncased`) |
| `repo_type` | `str` | `model`, `dataset`, or `space` |
| `size_on_disk` | `int` | Total bytes across all revisions |
| `nb_files` | `int` | Total file count (blobs) |
| `revisions` | `List[CachedRevisionInfo]` | All cached revisions |

#### CachedRevisionInfo properties

| Field | Type | Description |
|---|---|---|
| `commit_hash` | `str` | Full commit hash |
| `size_on_disk` | `int` | Bytes for this revision |
| `nb_files` | `int` | File count |
| `refs` | `List[str]` | Branch/tag names pointing here |
| `snapshot_path` | `Path` | Path to snapshot directory |

#### Cleanup Operations

All cleanup is non-destructive and gives you a `DeleteCacheStrategy` to review before committing:

```python
# Strategy 1: Delete specific revisions
strategy = cache_info.delete_revisions("a1b2c3d...", "e4f5g6h...")

# Strategy 2: Delete by age (all revisions older than N days)
from datetime import timedelta
strategy = cache_info.delete_revisions(*[
    rev.commit_hash for repo in cache_info.repos
    for rev in repo.revisions
    if rev.last_accessed < some_date
])

# Preview what would be deleted
print(f"Would free: {strategy.expected_freed_size_str}")

# Actually execute
strategy.execute()
```

The `hf cache` CLI wraps this:
```bash
hf cache list                # human-readable
hf cache list --format json  # machine-readable
hf cache prune                # remove detached revisions (no ref pointing to them)
hf cache verify               # checksum check on all blobs
```

### try_to_load_from_cache() — Quick Cache Lookup

```python
from huggingface_hub import try_to_load_from_cache, _CACHED_NO_EXIST

filepath = try_to_load_from_cache(
    repo_id="bert-base-uncased",
    filename="config.json",
    revision="main"
)

if isinstance(filepath, str):
    print(f"Found at: {filepath}")
elif filepath is _CACHED_NO_EXIST:
    print("File is known to not exist at this revision (cached miss)")
else:
    print("File not in cache (will need to download)")
```

This never raises an exception. Returns `None` if not cached at all.

### cached_assets_path() — Canonical Asset Storage

For downstream libraries that need to cache non-Hub files:

```python
from huggingface_hub import cached_assets_path

path = cached_assets_path(
    library_name="my-library",
    namespace="datasets",
    subfolder="cache"
)
# Returns: <ASSETS_DIR>/my-library/datasets/cache/
```

Guaranteed to create the directory. Follows `HF_ASSETS_CACHE` variable.

---

## 3. HfApi Utilities for Programmatic Workflows

The `HfApi` class wraps the Hugging Face Hub HTTP API. All methods are also available as top-level functions.

### Standard Setup

```python
from huggingface_hub import HfApi

# Option A: using default token (from env or ~/.cache/huggingface/token)
api = HfApi()

# Option B: with explicit token (no persistence, overrides env)
api = HfApi(token="hf_...")

# Option C: custom endpoint (e.g., Private Hub)
api = HfApi(endpoint="https://huggingface.co", token="hf_...")
```

### Repository Management

```python
# Create repo
api.create_repo(repo_id="my-model", repo_type="model", private=True)
# Returns: RepoUrl(url="https://huggingface.co/username/my-model")

# Delete repo (irreversible!)
api.delete_repo(repo_id="username/my-model", repo_type="model")

# Move/rename repo
api.move_repo(from_id="old/name", to_id="new/name")

# Duplicate repo
api.duplicate_repo(from_id="org/source", to_id="personal/copy")
```

### File Management

```python
# Upload a single file
api.upload_file(
    path_or_fileobj="local_config.json",
    path_in_repo="config.json",
    repo_id="username/my-model",
    commit_message="Add config"
)

# Upload an entire folder (recursive)
api.upload_folder(
    folder_path="./model_artifacts/",
    repo_id="username/my-model",
    repo_type="model",
    commit_message="Upload model artifacts"
)

# Download a single file
from huggingface_hub import hf_hub_download

local_path = hf_hub_download(
    repo_id="bert-base-uncased",
    filename="config.json",
    revision="main",
    local_dir="./local_models/bert"
)

# Download entire repo snapshot
from huggingface_hub import snapshot_download

local_dir = snapshot_download(
    repo_id="mistralai/Mistral-7B-v0.1",
    revision="main",
    local_dir="./models/mistral",
    ignore_patterns=["*.pt", "*.bin"]  # skip pytorch checkpoints if using safetensors
)
```

### Multi-File Commits (Atomic)

```python
from huggingface_hub import CommitOperationAdd, CommitOperationDelete

operations = [
    CommitOperationAdd(path_in_repo="config.json", path_or_fileobj="./config.json"),
    CommitOperationAdd(path_in_repo="model.safetensors", path_or_fileobj="./model.safetensors"),
    CommitOperationDelete(path_in_repo="old_weights.pt"),
]

api.create_commit(
    repo_id="username/my-model",
    operations=operations,
    commit_message="Replace model v1 with v2",
    parent_commit=None  # will auto-resolve current HEAD
)
```

### Listing & Searching

```python
# List all models with a filter
models = api.list_models(author="bert", sort="downloads", direction=-1, limit=5)

# List datasets
datasets = api.list_datasets(author="username")

# List files in a repo
files = api.list_repo_files(repo_id="username/my-model", repo_type="model")

# Get repo info
info = api.repo_info(repo_id="username/my-model", repo_type="model")
print(f"Downloads: {info.downloads}")
print(f"Likes: {info.likes}")
print(f"Tags: {info.tags}")
print(f"Siblings: {[s.rfilename for s in info.siblings]}")
```

### Space Management

```python
# Create a Space
from huggingface_hub import SpaceHardware

api.create_repo(
    repo_id="username/my-space",
    repo_type="space",
    space_sdk="gradio",        # or "streamlit", "static", "docker"
    space_hardware=SpaceHardware.CPU_BASIC
)

# Set Space secrets
api.add_space_secret(
    repo_id="username/my-space",
    key="API_KEY",
    value="sk-xxx"
)

# Manage Space hardware
api.request_space_hardware(repo_id="username/my-space", hardware=SpaceHardware.T4_MID)
api.pause_space(repo_id="username/my-space")
api.restart_space(repo_id="username/my-space")
```

### Collections

```python
# Create a collection
api.create_collection(title="Awesome Models", namespace="username")

# Add items
api.add_collection_item(
    collection_slug="username/awesome-models",
    item_id="mistralai/Mistral-7B-v0.1",
    item_type="model"
)

# List collections
api.list_collections(owner="username")
```

### Webhooks (programmatic)

```python
# List webhooks
webhooks = api.list_webhooks()

# Create webhook
api.create_webhook(
    url="https://my-server.com/hf-webhook",
    watched=[{"type": "user", "value": "username"}],
    domains=["model", "dataset"]
)
```

---

## 4. Common Automation Patterns

### One-shot download with cache bypass

```python
# Skip HF cache and download directly to a local directory
path = hf_hub_download(
    repo_id="...",
    filename="...",
    local_dir="./data",
    local_dir_use_symlinks=False  # make real copies, not symlinks
)
```

### CI-ready token management

```python
import os
from huggingface_hub import HfApi, login

# Option A: Use HF_TOKEN env var (best for CI)
api = HfApi()  # reads HF_TOKEN automatically

# Option B: Programmatic login (writes token to disk)
login(token="hf_...", add_to_git_credential=True)

# Option C: Token from file
with open(os.path.expanduser("~/.hf_token")) as f:
    token = f.read().strip()
api = HfApi(token=token)
```

### Check repo existence without error

```python
from huggingface_hub import repo_exists

if repo_exists(repo_id="username/my-model"):
    print("Repo exists!")
else:
    print("Repo does not exist")
```

### Upload after training (full pipeline)

```python
from huggingface_hub import HfApi, create_repo

api = HfApi()
url = create_repo(repo_id="username/my-finetuned-model", private=True)

api.upload_folder(
    folder_path="./output/checkpoint-1000",
    repo_id="username/my-finetuned-model",
    commit_message="Upload checkpoint"
)

# Update model card
api.upload_file(
    path_or_fileobj="README.md",
    path_in_repo="README.md",
    repo_id="username/my-finetuned-model"
)
```

---

## 5. Troubleshooting & Best Practices

| Problem | Solution |
|---|---|
| Cache growing too large | Run `hf cache prune` to remove detached revisions, then `scan_cache_dir().delete_revisions()` for fine-grained control |
| Download timeouts | Increase `HF_HUB_DOWNLOAD_TIMEOUT` or `HF_HUB_ETAG_TIMEOUT` |
| Symlink warnings on Windows | `export HF_HUB_DISABLE_SYMLINKS_WARNING=1` or enable Developer Mode in Windows |
| Want faster downloads | `export HF_HUB_ENABLE_HF_TRANSFER=1` (requires `pip install hf_transfer`) |
| Token not persisting | Check `HF_TOKEN_PATH` or set `HF_TOKEN` explicitly |
| Private Hub endpoint | Set `HF_ENDPOINT` or pass `endpoint=` to `HfApi()` |
| Multiple accounts | Manage with `hf auth list` / `hf auth switch` or instantiate `HfApi(token=...)` per account |

### Verbosity control

```python
import huggingface_hub.utils.logging as hf_logging
hf_logging.set_verbosity_debug()    # full debug output
hf_logging.set_verbosity_info()     # info + warnings + errors
hf_logging.set_verbosity_warning()  # default
hf_logging.set_verbosity_error()    # errors only
hf_logging.set_verbosity_critical() # nothing
```

Or via `HF_HUB_VERBOSITY=debug` in env.

---

> **Sources:** Official Hugging Face docs — [Cache Management Guide](https://huggingface.co/docs/huggingface_hub/en/guides/manage-cache), [Cache System Reference](https://huggingface.co/docs/huggingface_hub/en/package_reference/cache), [Environment Variables](https://huggingface.co/docs/huggingface_hub/en/package_reference/environment_variables), [HfApi Reference](https://huggingface.co/docs/huggingface_hub/package_reference/hf_api).
