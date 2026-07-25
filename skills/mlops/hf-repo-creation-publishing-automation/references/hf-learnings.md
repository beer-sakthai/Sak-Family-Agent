# HF Learnings — Repo Creation & Publishing Automation

**Topic:** hf-repo-creation-publishing-automation
**Date:** 2026-07-24
**author:** SakThai
**license:** MIT

## Summary

Comprehensive deep-dive into programmatic repository lifecycle management on Hugging Face Hub. Covers all `HfApi` methods for repo CRUD (create, delete, duplicate, move, squash), metadata/settings management, file upload strategies (single file, folder, multi-operation commits), the `hf` CLI equivalents, and CI/CD automation patterns for zero-cost headless publishing pipelines.

## Key Sources

- Source: `huggingface_hub/hf_api.py` (v1.24.0+) — `HfApi` class
- CLI: `hf repos --help`
- Official docs: https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api
- CLI docs: https://huggingface.co/docs/huggingface_hub/en/guides/cli

---

## 1. Repository CRUD — Complete API Reference

All methods live on `HfApi()` and work for models, datasets, and Spaces via the `repo_type` parameter.

### 1.1 create_repo()

```python
from huggingface_hub import HfApi
api = HfApi()

url = api.create_repo(
    repo_id="user/my-model",
    repo_type="model",           # "model" | "dataset" | "space"
    private=False,               # or True for private repos
    visibility="public",         # "public" | "private" | "protected" (Spaces only)
    exist_ok=False,              # if True, no error if already exists
    resource_group_id=None,      # Enterprise Hub: resource group ID
    region=None,                 # "us" | "eu" (requires Team plan+)
    # Space-specific parameters (ignored for model/dataset):
    space_sdk=None,              # "gradio" | "streamlit" | "docker" | "static"
    space_hardware=None,         # SpaceHardware enum or string
    space_storage=None,          # deprecated, use space_volumes
    space_sleep_time=None,       # seconds before sleep (-1 = never sleep)
    space_secrets=None,          # [{"key": "K", "value": "V", "description": "..."}]
    space_variables=None,        # [{"key": "K", "value": "V"}]
    space_volumes=None,          # [Volume(...)]
    space_template=None,         # Space template repo ID
)
# Returns: RepoUrl(url="https://huggingface.co/user/my-model")
```

**Key behavior:**
- Returns `RepoUrl` with `.url` and `.endpoint` attributes
- Creates an **empty** repo — you must then upload files
- `exist_ok=True` is idempotent-safe for CI/CD pipelines
- `private` and `visibility` are **mutually exclusive** (cannot pass both)
- Space secrets/variables set at creation time bypass the need for a second API call
- `space_template` imports an existing Space's structure as a starting point

### 1.2 delete_repo()

```python
api.delete_repo(
    repo_id="user/my-model",
    repo_type="model",
    missing_ok=False,     # if True, no error if repo doesn't exist
)
# Returns: None
```

**CAUTION:** This is **irreversible**. All files, commits, and history are permanently removed. There is no trash/recycle bin on the Hub.

### 1.3 duplicate_repo()

```python
url = api.duplicate_repo(
    from_id="source-user/model",
    to_id="my-org/my-copy",       # optional; defaults to same name in your namespace
    repo_type="model",
    private=False,
    exist_ok=False,
    # Space-specific:
    space_hardware=None,
    space_storage=None,
    space_sleep_time=None,
    space_secrets=None,
    space_variables=None,
    space_volumes=None,
)
# Returns: RepoUrl
```

**Key insight:** `duplicate_repo` performs a **server-side copy** — full git history, all LFS objects, no local download/upload round-trip. This is the programmatic equivalent of the Hub UI's "Duplicate Space" button. For Spaces, you can override hardware, secrets, volumes, and sleep time in the copy.

### 1.4 move_repo()

```python
api.move_repo(
    from_id="old-user/model",
    to_id="new-user/model",
    repo_type="model",
)
# Returns: None
```

**Limitations:**
- Cannot move to a different repo type
- Org → user and user → org moves have specific restrictions
- See https://hf.co/docs/hub/repositories-settings#renaming-or-transferring-a-repo

### 1.5 super_squash_history()

```python
api.super_squash_history(
    repo_id="user/my-model",
    branch="main",               # defaults to "main"
    commit_message="Initial release",  # optional
    repo_type="model",
)
# Returns: None
```

**WARNING:** Non-revertible operation. Collapses entire commit history into a single commit. After squashing, the branch cannot be merged into another branch because their histories will have diverged. Useful for cleaning up bloated histories from automated upload pipelines before a public release.

---

## 2. Repo Metadata & Existence Checks

### 2.1 repo_exists()

```python
exists = api.repo_exists("user/my-model", repo_type="model")
# Returns: bool
```

Lightweight HEAD request — no data transfer. Ideal for pre-flight checks in automation scripts.

### 2.2 repo_info()

```python
info = api.repo_info(
    repo_id="google/gemma-7b",
    repo_type="model",
    revision="main",
    files_metadata=False,         # if True, includes file sizes/types
    expand=["trendingScore", "inference"],  # optional expansion fields
)
# Returns: ModelInfo | DatasetInfo | SpaceInfo | KernelInfo
```

**Return types by repo_type:**

| repo_type | Return type | Key attributes |
|-----------|-------------|----------------|
| `"model"` | `ModelInfo` | `id`, `sha`, `private`, `downloads`, `likes`, `tags`, `pipeline_tag`, `cardData`, `siblings` (file list), `spaces`, `created_at`, `last_modified` |
| `"dataset"` | `DatasetInfo` | `id`, `sha`, `private`, `downloads`, `tags`, `cardData`, `siblings`, `created_at` |
| `"space"` | `SpaceInfo` | `id`, `sha`, `private`, `sdk`, `hardware`, `storage`, `runtime`, `variables`, `secrets`, `created_at` |

**Expandable fields:** `["cardData", "siblings", "trendingScore", "inference", "widgetData", "modelIndex"]` — each adds data that's excluded by default for performance.

### 2.3 update_repo_settings()

```python
api.update_repo_settings(
    repo_id="user/my-model",
    repo_type="model",
    private=False,               # or True — conflicts with visibility
    visibility="public",         # "public" | "private" | "protected" (Space)
    gated="auto",                # "auto" | "manual" | False (disable gating)
)
# Returns: None
```

**Gated repo options:**
- `"auto"` — auto-approve/deny access requests based on HF's criteria
- `"manual"` — require manual approval for each access request
- `False` — open access (no gates)

Gating is commonly used for model repos that need license acceptance (e.g., Gemma, Llama).

### 2.4 list_repo_files()

```python
files = api.list_repo_files(
    repo_id="user/my-model",
    revision="main",
    repo_type="model",
)
# Returns: list[str] — e.g., ["config.json", "model.safetensors", "tokenizer.json"]
```

Does not return file sizes or metadata — use `repo_info(files_metadata=True).siblings` for that.

### 2.5 list_repo_commits()

```python
commits = api.list_repo_commits(
    repo_id="user/my-model",
    repo_type="model",
    revision="main",
    reverse=False,               # chronological (True) or reverse-chronological (False)
)
# Returns: list[CommitInfo] — each with .commit_id, .title, .message, .created_at, .author
```

Useful for checking when a repo was last updated, auditing commits, or verifying a push succeeded.

---

## 3. File Upload Operations

### 3.1 upload_file() — Single File Upload

```python
result = api.upload_file(
    path_or_fileobj="./local/model.safetensors",  # str | Path | bytes | BinaryIO
    path_in_repo="model.safetensors",
    repo_id="user/my-model",
    repo_type="model",
    revision="main",
    commit_message="Upload safetensors weights",
    commit_description="Optional longer description",
    create_pr=False,             # set True to open a PR instead of direct push
    parent_commit=None,          # optimistic locking: ensures linear history
)
# Returns: CommitInfo
```

**Three input modes:**

| Mode | Example | Use case |
|------|---------|----------|
| File path | `path_or_fileobj="./local/file.bin"` | Local file upload |
| Bytes | `path_or_fileobj=b"raw content"` | Generated content, no temp file |
| BinaryIO | `path_or_fileobj=open("f", "rb")` | Streaming large files |

**Automatic LFS detection:** Files larger than 10 MB are automatically uploaded as Git LFS. The library handles the multipart upload transparently.

### 3.2 upload_folder() — Directory Upload

```python
result = api.upload_folder(
    folder_path="./outputs",           # local folder to upload
    path_in_repo="experiment-results", # target path in repo (optional)
    repo_id="user/my-model",
    repo_type="model",
    revision="main",
    commit_message="Upload experiment results",
    allow_patterns=["*.json", "*.png"],    # include only matching files
    ignore_patterns=["*.tmp", "*.log"],    # exclude matching files
    delete_patterns=["old-*"],             # delete matching files in repo before upload
    create_pr=False,
    parent_commit=None,
)
# Returns: CommitInfo
```

**Pattern filtering uses Unix glob syntax:**
- `allow_patterns` — only files matching at least one pattern are uploaded
- `ignore_patterns` — files matching any pattern are skipped (takes precedence over allow)
- `delete_patterns` — delete files in the repo matching these patterns before uploading new ones

Useful for CI/CD pipelines that generate artifacts in a directory and need to sync them atomically.

### 3.3 create_commit() — Multi-Operation Commits

```python
from huggingface_hub import CommitOperationAdd, CommitOperationDelete, CommitOperationCopy

# Build operations list
operations = [
    CommitOperationAdd(
        path_in_repo="config.json",
        path_or_fileobj=b'{"model_type": "my_model"}',
    ),
    CommitOperationAdd(
        path_in_repo="model.safetensors",
        path_or_fileobj="./local/model.safetensors",
    ),
    CommitOperationDelete(
        path_in_repo="old_weights.bin",
    ),
    CommitOperationCopy(
        src_path_in_repo="backup/config.json",
        path_in_repo="config.json",
        src_revision="backup-branch",  # optional; default = same branch
    ),
    # Cross-repo copy (server-side)
    CommitOperationCopy(
        src_path_in_repo="tokenizer.json",
        path_in_repo="tokenizer.json",
        src_repo_id="other-user/source-model",
        src_repo_type="model",
        src_revision="main",
    ),
]

commit = api.create_commit(
    repo_id="user/my-model",
    operations=operations,
    commit_message="Update config, add weights, clean up",
    commit_description="Multi-operation atomic commit",
    repo_type="model",
    revision="main",
    create_pr=False,
    num_threads=5,            # parallel LFS upload threads
    parent_commit=None,       # optimistic locking
)
# Returns: CommitInfo
```

**Critical constraints:**
- Max **25,000 LFS files** per commit
- Max **1 GB** payload for regular (non-LFS) files
- The `operations` list **will be mutated** — do not reuse objects
- Repo must already exist (create it first with `create_repo()`)
- Empty `commit_message` raises `ValueError`

**CommitOperationAdd** accepts the same three input modes as `upload_file`:
1. `str | Path` — local file path
2. `bytes` — raw content
3. `BinaryIO` — open file handle

**CommitOperationCopy** is the most efficient way to duplicate files within or across repos — no download/upload, purely server-side.

### 3.4 parent_commit — Optimistic Locking

```python
# Before uploading, get current HEAD
info = api.repo_info("user/my-model", repo_type="model")
head_commit = info.sha  # current HEAD commit hash

# Do some work...

# Upload with parent_commit = the exact HEAD we read
api.upload_file(
    ...,
    parent_commit=head_commit,
)
```

If another upload modified the repo between your `repo_info` call and your commit, the server rejects the commit with a 409 conflict. This is **optimistic locking** — it prevents race conditions in concurrent CI/CD pipelines.

Without `parent_commit`, the server auto-merges (fast-forward), which can cause subtle ordering issues in parallel jobs.

### 3.5 create_pr — Pull Request Workflow

```python
# Open a PR with new content
api.upload_folder(
    folder_path="./new-version",
    path_in_repo=".",
    repo_id="user/my-model",
    create_pr=True,            # opens PR instead of direct push
    commit_message="Add new version via PR",
)
```

When `create_pr=True`:
1. A new branch is created (auto-named)
2. Files are committed to that branch
3. A PR is opened from that branch to `main`
4. The return value includes `pr_url` and `pr_revision`

For repos you don't own, this is the standard open-source contribution pattern.

---

## 4. CLI Equivalents (`hf repos`)

The `hf repos` command group provides terminal access to all repo lifecycle operations.

### 4.1 Create

```bash
# Simple model repo
hf repos create my-model

# Private dataset
hf repos create my-dataset --repo-type dataset --private

# Space with hardware, secrets, and volumes
hf repos create my-space --type space --sdk gradio --flavor t4-medium \
    --secrets HF_TOKEN -e THEME=dark --protected \
    -v hf://buckets/org/b:/data

# From a template
hf repos create my-jupyterlab --type space --template SpacesExamples/jupyterlab

# With explicit region
hf repos create my-model --region us
```

### 4.2 Delete

```bash
hf repos delete my-model --repo-type model
# Add --missing-ok to suppress error if already deleted
```

### 4.3 Duplicate

```bash
# Simple duplicate (into your namespace)
hf repos duplicate openai/gdpval --type dataset

# Space duplicate with overrides
hf repos duplicate org/my-space my-space --type space \
    --flavor l4x4 --secrets HF_TOKEN --private \
    -v hf://org/my-model:/models
```

### 4.4 Move/Rename

```bash
hf repos move old-namespace/my-model new-namespace/my-model
```

### 4.5 Settings

```bash
hf repos settings my-model --private
hf repos settings my-model --gated auto
hf repos settings my-space --repo-type space --protected
```

### 4.6 Copy Files (`hf repos cp`)

```bash
# Local → Hub
hf repos cp config.json hf://username/my-model/config.json

# Hub → Local
hf repos cp hf://username/my-model/config.json config.json

# Hub → Hub (server-side copy)
hf repos cp hf://user/model-a/config.json hf://user/model-b/config.json
```

### 4.7 List Repos (`hf repos ls`)

```bash
# List all repos with storage info
hf repos ls

# Filter by type
hf repos ls --type model
hf repos ls --type dataset
hf repos ls --type space

# JSON output for scripting
hf repos ls --json
```

### 4.8 List Files

```bash
# List files in a repo (not via `hf repos` but `hf files`)
hf files ls hf://username/my-model
```

---

## 5. CI/CD Automation Patterns

### 5.1 GitHub Actions — Push Model to Hub

```yaml
# .github/workflows/publish-model.yml
name: Publish Model to HF Hub
on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install huggingface_hub
      - name: Upload to HF Hub
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
        run: |
          python -c "
          from huggingface_hub import HfApi
          api = HfApi(token='$HF_TOKEN')
          # Create repo if needed
          api.create_repo('org/model-name', exist_ok=True)
          # Upload all artifacts
          api.upload_folder(
              folder_path='./dist',
              path_in_repo='.',
              repo_id='org/model-name',
              commit_message='Release ${{ github.ref_name }}'
          )
          "
```

### 5.2 Idempotent Publishing Pattern

The safe pattern for any automated pipeline:

```python
def publish_to_hub(local_dir: str, repo_id: str, repo_type: str = "model"):
    """Idempotent publish — safe to run multiple times."""
    api = HfApi()

    # Step 1: Ensure repo exists (no-op if already exists)
    api.create_repo(repo_id, repo_type=repo_type, exist_ok=True)

    # Step 2: Optional — read current HEAD for optimistic locking
    # (skip if you don't need it — auto-merge is usually fine for simple uploads)
    try:
        info = api.repo_info(repo_id, repo_type=repo_type)
        parent = info.sha
    except Exception:
        parent = None

    # Step 3: Upload
    api.upload_folder(
        folder_path=local_dir,
        path_in_repo=".",
        repo_id=repo_id,
        repo_type=repo_type,
        commit_message=f"Auto-publish from pipeline",
        parent_commit=parent,
    )
```

### 5.3 Atomic Multi-File Update

When you need to replace multiple files atomically:

```python
def atomic_update(repo_id: str, new_config: dict, new_weights_path: str):
    """Replace config.json and weights in a single atomic commit."""
    api = HfApi()

    operations = [
        CommitOperationDelete(path_in_repo="old_config.json"),
        CommitOperationDelete(path_in_repo="legacy_weights.bin"),
        CommitOperationAdd(
            path_in_repo="config.json",
            path_or_fileobj=json.dumps(new_config).encode(),
        ),
        CommitOperationAdd(
            path_in_repo="model.safetensors",
            path_or_fileobj=new_weights_path,
        ),
    ]

    api.create_commit(
        repo_id=repo_id,
        operations=operations,
        commit_message="Atomic config + weights update",
        repo_type="model",
    )
```

### 5.4 Space Duplication with Secrets

```python
# Duplicate a Space and inject secrets + hardware
api.duplicate_repo(
    from_id="multimodalart/dreambooth-training",
    to_id="my-org/dreambooth-instance",
    repo_type="space",
    space_hardware=SpaceHardware.L4X4,  # or "l4x4"
    space_secrets=[
        {"key": "HF_TOKEN", "value": "hf_...", "description": "Token for model access"},
        {"key": "WANDB_API_KEY", "value": "..."},
    ],
    private=True,
)
```

### 5.5 Tag Management (`hf repos tag`)

```bash
# Add a tag
hf repos tag my-model v1.0.0

# List tags
hf repos tag my-model --list

# Delete a tag
hf repos tag my-model --delete v1.0.0
```

Tags on the Hub correspond to Git tags on the repo. They are useful for marking release points.

---

## 6. Dataset Management Patterns

### 6.1 Appending to an Existing Dataset

When you need to **add** examples to an existing dataset on the Hub (rather than replace it), follow the download-append-reupload pattern:

```python
from huggingface_hub import hf_hub_download, HfApi
import json

# 1. Download existing
path = hf_hub_download("user/my-dataset", "data/train.jsonl",
                       repo_type="dataset", force_download=True)
with open(path) as f:
    existing = [json.loads(line) for line in f if line.strip()]

# 2. Load your new examples
with open("my_new_examples.jsonl") as f:
    new_examples = [json.loads(line) for line in f if line.strip()]

# 3. Combine and write
combined = existing + new_examples
combined_path = "/tmp/train_combined.jsonl"
with open(combined_path, "w") as f:
    for ex in combined:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

# 4. Upload (replaces the existing file, so include ALL examples)
api = HfApi()
api.upload_file(
    path_or_fileobj=combined_path,
    path_in_repo="data/train.jsonl",
    repo_id="user/my-dataset",
    repo_type="dataset",
    commit_message=f"Add {len(new_examples)} new examples (was {len(existing)}, now {len(combined)})",
)
```

**Critical pitfall:** `upload_file` **replaces** the target file entirely — it does not merge or append server-side. Always download first and combine locally. An upload without downloading first will silently overwrite the entire dataset.

### 6.2 Tool-Calling Dataset Format

Tool-calling training datasets on the Hub use **OpenAI-style `tool_calls` arrays** under a `"messages"` key. Do NOT use `<tool_call>` markup in content strings.

**✅ Correct format (Hub convention):**

```python
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What's the weather in Tokyo?"},
    {
      "role": "assistant",
      "content": None,
      "tool_calls": [
        {
          "id": "call_00000001",
          "type": "function",
          "function": {
            "name": "get_weather",
            "arguments": "{\"location\": \"Tokyo\"}"
          }
        }
      ]
    },
    {
      "role": "tool",
      "tool_call_id": "call_00000001",
      "content": "{\"temperature\": 28, \"condition\": \"sunny\"}"
    },
    {"role": "assistant", "content": "Tokyo is 28°C and sunny."}
  ],
  "tools": [...]
}
```

**Key rules:**
- Use `"messages"` top-level key (not `"conversations"`)
- Tool calls in `"tool_calls"` list, not embedded in `content`
- Arguments are **stringified JSON** (not a raw dict)
- Each call needs a unique `"id"` (e.g. `"call_xxxxxxxx"`)
- Tool results: `"role": "tool"` with matching `"tool_call_id"`
- Assistant `content` is `null` when tool calls are present
- Parallel calls: put multiple objects in the same `tool_calls` array

**Converting from `<tool_call>` markup to OpenAI format:** parse each `<tool_call>\n{"name":"X","arguments":{...}}\n</tool_call>` block, assign a unique call id, create the `tool_calls` array, and pair tool results via ordered matching.

### 6.3 `hf upload` CLI Path Pitfall

The CLIs `hf upload` command requires an explicit `path_in_repo` — passing `"."` fails with `Error: Invalid value`. Always use a specific path:

```bash
# ✅ Correct
hf upload user/my-repo local_file.jsonl data/train.jsonl

# ❌ Wrong — fails with path error
hf upload user/my-repo local_file.jsonl .
```

When the CLI gives cryptic path errors, fall back to `HfApi.upload_file()` — it handles path parsing consistently and gives clearer error messages.

---

## 7. Direct Hub API (REST)

The `HfApi` Python client wraps the Hub's REST API. The underlying HTTP endpoints are:

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Create repo | `POST` | `/api/repos/create` |
| Delete repo | `DELETE` | `/api/repos/{type}/{repo_id}` |
| Repo info | `GET` | `/api/{type}s/{repo_id}` |
| Upload file | `POST` | `/api/{type}s/{repo_id}/upload/{revision}` |
| File list | `GET` | `/api/{type}s/{repo_id}/tree/{revision}` |

Using `HfApi` is preferred over raw HTTP — it handles auth, retries, LFS uploads, error mapping, and rate limiting automatically.

---

## 9. Rate Limiting & Best Practices

### Rate Limits
- Unauthenticated: ~100 requests/minute
- Authenticated (HF_TOKEN): ~1000 requests/minute (varies by token tier)
- Uploads have higher limits but may be throttled for large payloads

### Best Practices

1. **Always use `exist_ok=True`** in CI/CD — prevents race conditions in concurrent runs
2. **Set `create_pr=True` for external contributions** — standard OSS pattern
3. **Use `parent_commit` for optimistic locking** in parallel pipeline stages
4. **Prefer `upload_folder()` over individual `upload_file()` calls** — fewer commits, cleaner history
5. **Use `CommitOperationCopy` for cross-repo file copies** — zero bandwidth, instant
6. **Combine multiple operations in one `create_commit()`** — atomicity matters
7. **Run `super_squash_history()` before a public release** to clean up messy dev commits
8. **Set Space secrets/variables at creation time** — one call instead of two
9. **Use `missing_ok=True` for `delete_repo`** in cleanup scripts
10. **Batch independent tasks into a single `HfApi()` instance** — connection pooling
11. **Format CLI output with `--json` for scripting** — avoids parsing the human table
12. **Use `hf://` URIs** with `hf repos cp` for simple file transfers without Python

---

## 9. Repo Type Comparison

| Aspect | Model | Dataset | Space |
|--------|-------|---------|-------|
| `repo_type` | `"model"` (or `None`) | `"dataset"` | `"space"` |
| Required at creation | Nothing extra | Nothing extra | `space_sdk` (gradio/streamlit/docker/static) |
| Key creation params | `private` | `private` | `space_hardware`, `space_secrets`, `space_sleep_time` |
| Pipeline tags | `pipeline_tag` | N/A | N/A |
| File types | Weights, config, tokenizer | Data files (parquet, JSONL) | App code, requirements |
| Special CLI type prefix | `models` | `datasets` | `spaces` |
| Duplicate preserve | Full history | Full history | Full history + hardware override |

---

## 9. Error Handling Reference

| Error | Raised When | How to Avoid |
|-------|-------------|--------------|
| `RepositoryNotFoundError` | `delete_repo(missing_ok=False)` or `repo_info()` on non-existent repo | Use `repo_exists()` before, or set `missing_ok=True` / `exist_ok=True` |
| `BadRequestError` (409) | `create_commit(parent_commit=old_hash)` when HEAD has moved | Re-read `repo_info().sha` and retry |
| `ValueError` | Empty `commit_message` in `create_commit()` | Always provide a message |
| `GatedRepoError` | Accessing a gated repo without accepted license | Use `update_repo_settings(gated=False)` to open |
| `PermissionError` | Token lacks write access to the target namespace | Verify token scope and org membership |

---

## 10. Token Management for Automation

```python
# Explicit token (best for CI/CD)
api = HfApi(token="hf_...")

# Token from env var (falls back to HF_TOKEN env)
import os
api = HfApi(token=os.environ["HF_TOKEN"])

# Implicit token (uses ~/.cache/huggingface/token)
api = HfApi()

# Fine-grained tokens for different operations
read_api = HfApi(token="hf_read_...")   # read-only operations
write_api = HfApi(token="hf_write_...") # write operations
```

**Token types available:**
- **Read tokens**: Can only read public/gated repos
- **Write tokens**: Can create repos, upload files, update settings
- **Fine-grained tokens** (v1.22+): Scoped to specific repos or operations

---

---

## 11. REST API Deep-Dive — Raw Endpoint Contracts

The `HfApi` Python client wraps the Hub's REST API, but the raw HTTP endpoints expose additional parameters and settings not yet surfaced in the Python library. Below is the complete contract for repo management endpoints sourced from the official [OpenAPI spec](https://huggingface.co/.well-known/openapi.json).

### 11.1 POST /api/repos/create — Create a Repository

**Full request body schema:**

```json
{
  "name": "my-repo",                          // (required) repo name
  "organization": "my-org",                   // (optional) org namespace
  "type": "model",                            // "model" | "dataset" | "space"
  "private": false,                           // bool | null (default: public)
  "visibility": "public",                     // "public" | "private" | "protected" (Spaces only)
  "region": "us",                             // "us" | "eu" (activates regional hosting)
  "license": "mit",                           // HF license enum (50+ values)
  "license_name": "my-custom-license",         // custom license slug (if license="other")
  "license_link": "LICENSE",                  // "LICENSE" | "LICENSE.md" | URL
  "resourceGroupId": "66670e51631...",        // Enterprise Hub resource group (24-char hex)
  "files": [                                  // seed with initial files
    {"content": "# Model Card\n...", "path": "README.md", "encoding": "utf-8"}
  ]
}
```

**Key details:**
- The `type` field defaults to `"model"` if omitted
- `private` and `visibility` are mutually exclusive — pass one, not both
- `region` requires a Team/Enterprise plan (free tier uses the default region)
- The `files` array lets you seed a repo with initial content in one request, avoiding a follow-up commit
- `organization` creates the repo under an org — equivalent to passing `repo_id="org/repo"` in the Python API

### 11.2 POST /api/repos/move — Move or Rename a Repository

**Full request body schema:**

```json
{
  "fromRepo": "source-user/old-name",          // (required) current repo ID
  "toRepo": "target-user/new-name",            // (required) new repo ID
  "type": "model"                              // "model" | "dataset" | "space" | "bucket" | "kernel"
}
```

**Move rules based on permissions:**

| Source → Target | Permission Required | Status |
|-----------------|-------------------|--------|
| User → same user (rename) | Ownership | ✅ Supported |
| Org → same org (rename) | write/admin | ✅ Supported |
| User → Org | Org membership (contributor+) | ✅ Supported |
| Org → self | Org admin | ✅ Supported |
| Org1 → Org2 | Admin in source, contributor+ in target | ✅ Supported |
| User A → User B | — | ❌ Not supported |
| Org → non-self user | — | ❌ Not supported |

**Behavior:** A redirect is auto-setup from the old URL → new URL. Download counts and likes are preserved. If the old repo was private, the new repo inherits the same visibility.

### 11.3 PUT /api/models/{namespace}/{repo}/settings — Update Repo Settings

**Full request body schema:**

```json
{
  "private": false,                               // bool — quick toggling
  "visibility": "public",                         // "public" | "private" | "protected"
  "discussionsDisabled": false,                   // bool — disable PRs/discussions
  "discussionsSorting": "recently-created",       // "recently-created" | "trending" | "reactions"
  "gated": false,                                 // false | "auto" | "manual"
  "orgMembersGated": true,                        // bool — org members also need gated access
  "gatedNotificationsEmail": "admin@org.com",     // email for gated request notifications
  "gatedNotificationsMode": "bulk"                // "bulk" | "real-time"
}
```

**Endpoint variation by repo type:**

| Repo Type | Settings URL |
|-----------|-------------|
| Model | `PUT /api/models/{namespace}/{repo}/settings` |
| Dataset | `PUT /api/datasets/{namespace}/{repo}/settings` |
| Space | `PUT /api/spaces/{namespace}/{repo}/settings` |

**Python wrapper vs REST API comparison:**

| Setting | `update_repo_settings()` | REST API |
|---------|------------------------|----------|
| `private` | ✅ Yes | ✅ Yes |
| `visibility` | ✅ Yes | ✅ Yes |
| `gated` | ✅ Yes (auto/manual/False) | ✅ Yes (same values) |
| `discussionsDisabled` | ❌ No | ✅ Yes |
| `discussionsSorting` | ❌ No | ✅ Yes |
| `orgMembersGated` | ❌ No | ✅ Yes |
| `gatedNotificationsEmail` | ❌ No | ✅ Yes |
| `gatedNotificationsMode` | ❌ No | ✅ Yes |

**Notes on gated access:**
- `"auto"` — Hugging Face auto-evaluates access requests and approves/denies based on the requesting user's profile
- `"manual"` — All requests land in the repo owner's queue for manual review
- `"orgMembersGated": true` — Even members of the owning org (except admins) must go through the gated flow, useful for sensitive model releases
- `"gatedNotificationsMode": "real-time"` — sends instant email per request; `"bulk"` (default) batches notifications periodically

### 11.4 REST API → Python Method Mapping

| REST Endpoint | Python HfApi Method | HTTP Method |
|--------------|-------------------|-------------|
| `POST /api/repos/create` | `create_repo()` | POST |
| `POST /api/repos/move` | `move_repo()` | POST |
| `DELETE /api/repos/{type}/{repo_id}` | `delete_repo()` | DELETE |
| `POST /api/repos/duplicate` | `duplicate_repo()` | POST |
| `PUT /api/{type}s/{ns}/{repo}/settings` | `update_repo_settings()` | PUT |
| `GET /api/{type}s/{repo_id}` | `repo_info()` | GET |
| `HEAD /api/{type}s/{repo_id}` | `repo_exists()` | HEAD |

### 11.5 Direct HTTP Example — Beyond the Python Wrapper

When you need settings not exposed by `HfApi.update_repo_settings()`, call the REST API directly with the `requests` library:

```python
import requests

HF_TOKEN = "hf_..."
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# Disable discussions and enable real-time gated notifications
resp = requests.put(
    "https://huggingface.co/api/models/my-org/my-model/settings",
    headers=headers,
    json={
        "discussionsDisabled": True,
        "gated": "manual",
        "orgMembersGated": True,
        "gatedNotificationsMode": "real-time",
    },
)
resp.raise_for_status()
```

---

## References

- HfApi docs: https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api
- CLI guide: https://huggingface.co/docs/huggingface_hub/en/guides/cli
- Hub API overview: https://huggingface.co/docs/hub/en/api
- Hub OpenAPI spec (always current): https://huggingface.co/.well-known/openapi.json
- Hub OpenAPI spec (markdown, agent-friendly): https://huggingface.co/.well-known/openapi.md
- Spaces hardware reference: https://huggingface.co/docs/hub/en/spaces-gpus
- Moving repos: https://hf.co/docs/hub/repositories-settings#renaming-or-transferring-a-repo
- Repository settings (UI): https://huggingface.co/docs/hub/en/repositories-settings
