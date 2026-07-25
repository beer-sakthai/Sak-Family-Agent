# HF Hub Fork & Sync — Complete Source Reference

> *Entry 378 in cumulative HF learnings*
> *Topic: `hf-hub-fork-and-sync`*
> *Date: 2026-07-25*
> *Source: `huggingface_hub` library source code (`HfApi.duplicate_repo`, `HfApi.copy_files`)*

---

## 1. `duplicate_repo()` — Full Server-Side Repo Duplication

**Signature:**
```python
def duplicate_repo(
    from_id: str,
    to_id: str | None = None,
    *,
    repo_type: str | None = None,
    private: bool | None = None,
    visibility: RepoVisibility_T | None = None,
    token: bool | str | None = None,
    exist_ok: bool = False,
    space_hardware: SpaceHardware | None = None,
    space_storage: SpaceStorage | None = None,
    space_sleep_time: int | None = None,
    space_secrets: list[dict[str, str]] | None = None,
    space_variables: list[dict[str, str]] | None = None,
    space_volumes: list[Volume] | None = None,
) -> RepoUrl
```

### How It Works
1. Resolves source repo from `from_id` (supports bare IDs like `"openai/gdpval"`, URLs, or `hf://` URIs)
2. Resolves target namespace+name from `to_id`. If `to_id` is omitted, the source name is reused under the caller's account
3. Builds a JSON payload with target repo info and optional Space configuration
4. Sends `POST /api/{models|datasets|spaces}/{from_id}/duplicate`
5. Returns `RepoUrl` pointing to the newly created repo

### Key Design Points

**Server-side copy preserves:**
- Full git history (all commits)
- LFS objects (large files)
- Repository structure
- Branch structure

**No local download/upload required** — the operation happens entirely on HF servers.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `from_id` | `str` | Source repo ID. E.g., `"openai/gdpval"`. Required. |
| `to_id` | `str \| None` | Target repo ID. E.g., `"myorg/my-gdpval"`. If None, uses source name under your account. |
| `repo_type` | `str \| None` | `None` or `"model"` for models, `"dataset"` for datasets, `"space"` for Spaces. |
| `private` | `bool \| None` | Whether new repo is private. Defaults to source's privacy. Cannot use with `visibility`. |
| `visibility` | `Literal["public", "private", "protected"]` | Explicit visibility. `"protected"` only for Spaces. |
| `exist_ok` | `bool` | If True, suppress 409 error when target already exists. |
| `space_hardware` | `SpaceHardware \| None` | Hardware tier for Spaces. E.g., `"t4-medium"`. |
| `space_storage` | `SpaceStorage \| None` | *Deprecated* — use `space_volumes`. |
| `space_sleep_time` | `int \| None` | Seconds of inactivity before sleep. `-1` = never sleep. Fixed at 48h for CPU_BASIC. |
| `space_secrets` | `list[dict]` | `[{"key": "...", "value": "...", "description": "..."}]` |
| `space_variables` | `list[dict]` | Same format as secrets but for public env vars. |
| `space_volumes` | `list[Volume]` | Volume mounts at duplication time. Each has `type`, `source`, `mount_path`, optional `revision`, `read_only`, `path`. |

### Return Value
`RepoUrl` — a subclass of `str` with attributes:
- `endpoint` — HF endpoint (e.g., `https://huggingface.co`)
- `repo_type` — type of repo
- `repo_id` — full repo ID (e.g., `"nateraw/gemma-7b"`)

### Error Handling
| Error | HTTP Status | Cause |
|-------|-------------|-------|
| `RepositoryNotFoundError` | 404 | Source or target repo not found or access denied |
| `HfHubHTTPError` | 409 | Target already exists (use `exist_ok=True` to suppress) |
| `HfHubHTTPError` | 403 | Permission denied |
| `ValueError` | — | Invalid `repo_type` |

### Usage Examples
```python
from huggingface_hub import duplicate_repo

# Simple duplicate — model goes to your account
duplicate_repo("google/gemma-7b")
# → RepoUrl('https://huggingface.co/nateraw/gemma-7b')

# Custom name and different account/organization
duplicate_repo("openai/gdpval", to_id="myorg/my-gdpval", repo_type="dataset")
# → RepoUrl('https://huggingface.co/datasets/myorg/my-gdpval')

# Duplicate a Space with hardware upgrade
duplicate_repo(
    "multimodalart/dreambooth-training",
    repo_type="space",
    space_hardware="t4-medium",
    space_sleep_time=-1,
)
# → RepoUrl('https://huggingface.co/spaces/nateraw/dreambooth-training')

# Duplicate with all Space options
duplicate_repo(
    "open-llm-leaderboard/open-llm-leaderboard",
    repo_type="space",
    to_id="myorg/my-leaderboard",
    visibility="public",
    space_hardware="t4-medium",
    space_secrets=[{"key": "API_KEY", "value": "sk-..."}],
    space_variables=[{"key": "PUBLIC_VAR", "value": "value"}],
    space_volumes=[
        Volume(
            type="model",
            source="myorg/my-model",
            mount_path="/models/my-model",
            read_only=True,
        )
    ],
)
```

---

## 2. `duplicate_space()` — Legacy Space Duplication

**Status:** Deprecated since v2.0 — use `duplicate_repo` with `repo_type="space"`.

Identical functionality but without the unified interface. Internally calls the same REST endpoint.

```python
duplicate_space(from_id, to_id, private, visibility, token, exist_ok,
                hardware, storage, sleep_time, secrets, variables)
```

All parameters map one-to-one to `duplicate_repo` space-specific params.

---

## 3. `copy_files()` — Inter-Repo File Copying

**Signature:**
```python
def copy_files(
    source: str,
    destination: str,
    *,
    token: str | bool | None = None,
) -> None
```

### How It Works
- Source and destination are `hf://` URIs
- Supports files or folders from/to repos or buckets
- Trailing `/` on source = rsync-style (copy *contents* into destination)
- No trailing `/` on source = cp-style (copy source folder *nested* inside destination)
- Repo-to-repo copies use `CommitOperationCopy` internally (creates a commit on destination)
- `.gitattributes` files auto-excluded when copying from repo to bucket
- Only works within the same storage region

### Path Examples
| Source URI | Semantics |
|-----------|-----------|
| `hf://username/my-model/weights.bin` | Copy single file |
| `hf://datasets/username/my-dataset/data/` | Copy folder contents into destination |
| `hf://buckets/my-bucket/path/to/file` | Copy from bucket |

### Limitations
- ❌ Bucket-to-repo copies not supported
- ❌ Cross-region copies not supported
- ⚠️ `.gitattributes` excluded in repo→bucket copies

---

## 4. REST API Endpoint

**`POST /api/{repo_type}/{from_id}/duplicate`**

Repository types:
- `models` (for models, default)
- `datasets` (for datasets)
- `spaces` (for Spaces)

**Request body (JSON):**
```json
{
  "repository": "target_namespace/target_name",
  "visibility": "public|private|protected",
  "hardware": "t4-medium",
  "sleepTimeSeconds": -1,
  "secrets": [{"key": "...", "value": "..."}],
  "variables": [{"key": "...", "value": "..."}],
  "volumes": [{"type": "model", "source": "...", "mountPath": "/models/..."}]
}
```

**Response:**
```json
{
  "url": "https://huggingface.co/spaces/target_namespace/target_name"
}
```

---

## 5. Internal Implementation Details

### Namespace Resolution
The function uses three strategies to parse `to_id`:
1. `parse_hf_uri()` — for HF URLs and `hf://` URIs
2. `rsplit("/", 1)` — for bare `"namespace/name"` IDs
3. Falls back to `whoami()` to get caller's namespace

### Payload Construction
- `"repository"` — always included (required)
- `"visibility"` — only if explicitly set (private/visibility)
- Space options — only added when `repo_type == "space"` AND values are not None
- Warning emitted if Space options provided for non-Space repos

### Validation
- `repo_type` validated against `REPO_TYPES` constant
- CPU_BASIC hardware with custom sleep_time triggers a warning (48h is fixed for free tier)
- `private` and `visibility` cannot be used together (`_resolve_repo_visibility` helper)

---

## 6. Practical Use Cases

| Use Case | Code Pattern |
|----------|-------------|
| Fork a model to your account | `duplicate_repo("org/model")` |
| Fork under an org | `duplicate_repo("org/model", to_id="myorg/model")` |
| Make private copy | `duplicate_repo("org/model", private=True)` |
| Copy a dataset for experimentation | `duplicate_repo("org/data", to_id="me/experiment", repo_type="dataset")` |
| Deploy a Space with custom HW | `duplicate_repo("org/space", repo_type="space", space_hardware="t4-medium")` |
| Copy specific files between repos | `copy_files("hf://org/model/weights.bin", "hf://me/model/weights.bin")` |
| Sync dataset folder | `copy_files("hf://datasets/org/data/train/", "hf://datasets/me/data/")` |

---

## 7. Reference — Related API Methods

| Method | Purpose |
|--------|---------|
| `duplicate_repo()` | Full repo duplication |
| `duplicate_space()` | Legacy Space duplication |
| `copy_files()` | File/folder copy between repos/buckets |
| `create_repo()` | Create an empty repo (pre-requisite for manual push) |
| `upload_file()` | Upload a single file |
| `upload_folder()` | Upload a folder |
| `CommitOperationCopy` | Low-level file copy operation used by `copy_files()` |

---

## 8. Zero-Cost Considerations
- `duplicate_repo()` is **free** for all repo types within storage limits
- Spaces duplicated with `CPU_BASIC` hardware are free (48h sleep)
- Any hardware upgrade (`t4-medium`, `t4-large`, etc.) incurs billing
- `copy_files()` within same storage region is free
- Cross-region copies may incur egress costs if files must be re-uploaded
- Storage usage of forked repos counts against your account's total storage
