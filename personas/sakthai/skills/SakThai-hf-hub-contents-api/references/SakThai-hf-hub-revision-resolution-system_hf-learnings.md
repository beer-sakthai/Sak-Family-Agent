# HF Learnings Log

## 2026-07-25: hf-hub-revision-resolution-system-deep-dive — Complete Revision Resolution Pipeline (Topic #238)

### Summary

Source code deep-dive on how the Hugging Face Hub resolves Git revisions — from string input (branch name, tag, commit SHA, special ref) to resolved commit SHA and file path. Verified from `huggingface_hub v1.24.0` source at `/opt/data/.venv/lib/python3.13/site-packages/huggingface_hub/`. Covers REST API endpoints (model info, file listing, commit history), the `/resolve` URL pattern for file downloads, the `hf://` file system URI scheme, the local cache refs/snapshots layout, special ref handling for PRs and convert refs, and the URL encoding rules at each layer.

---

### 1. Architecture — Four-Layer Resolution

```
User-specified revision string ("main", "v1.0", "e7da7f2...", "refs/pr/5")
│
├── Layer 1: Defaulting → "main" if None provided (constants.DEFAULT_REVISION)
│
├── Layer 2: Type Detection
│   ├── Commit SHA?  → REGEX_COMMIT_HASH match (40 hex chars)
│   ├── Special Ref? → SPECIAL_REFS_REVISION_REGEX match (refs/convert/*, refs/pr/*)
│   └── Branch/Tag   → Everything else
│
├── Layer 3: URL Encoding
│   ├── REST API:   quote(revision, safe="") — always quote
│   ├── Download:   quote(revision, safe="") — always quote
│   └── HfFileSystem: safe_revision() — quote unless special ref
│
└── Layer 4: Server-Side Resolution
    ├── Named ref → Git refs lookup → commit SHA
    ├── Full SHA  → Direct blob lookup
    └── Special   → Server handles refs/ namespace
```

### 2. URL Structure

```python
# constants.py (line 69)
HUGGINGFACE_CO_URL_TEMPLATE = ENDPOINT + "/{repo_id}/resolve/{revision}/{filename}"
# Default: "https://huggingface.co/{repo_id}/resolve/{revision}/{filename}"
```

**With repo type prefix:**
```python
REPO_TYPES_URL_PREFIXES = {
    "dataset": "datasets/",
    "space": "spaces/",
    "kernel": "kernels/",
}
# Model:   https://huggingface.co/bert-base-uncased/resolve/main/config.json
# Dataset: https://huggingface.co/datasets/truthful_qa/resolve/main/README.md
# Space:   https://huggingface.co/spaces/black-forest-labs/FLUX.1-dev/resolve/main/app.py
```

### 3. REST API Endpoint Patterns

Every endpoint that accepts a `revision` parameter follows the same pattern:

#### 3a. Model Info (hf_api.py:3297-3301)
```python
# No revision → returns data at default branch (main)
f"{endpoint}/api/models/{repo_id}"

# With revision → revision is URL-quoted
f"{endpoint}/api/models/{repo_id}/revision/{quote(revision, safe='')}"
```

**Key finding:** When no revision is specified, the API path omits the `/revision/` segment entirely — the server returns the current state of the default branch. When a revision IS specified, it's appended as `/revision/{quoted_revision}`. This is true for all three repo types (`model_info`, `dataset_info`, `space_info`).

#### 3b. File Tree Listing (hf_api.py:3949-3953)
```python
revision = quote(revision, safe="") if revision is not None else constants.DEFAULT_REVISION
tree_url = f"{self.endpoint}/api/{repo_type}s/{repo_id}/tree/{revision}{encoded_path_in_repo}"
# Example: GET https://huggingface.co/api/models/gpt2/tree/main/
```

#### 3c. Path Info (hf_api.py:4248-4252)
```python
revision = quote(revision, safe="") if revision is not None else constants.DEFAULT_REVISION
# POST {endpoint}/api/{repo_type}s/{repo_id}/paths-info/{revision}
# Body: {"paths": [...], "expand": bool}
```

#### 3d. Commits Listing (hf_api.py:4183-4184)
```python
revision = quote(revision, safe="") if revision is not None else constants.DEFAULT_REVISION
f"{self.endpoint}/api/{repo_type}s/{repo_id}/commits/{revision}"
```

#### 3e. Refs Listing (hf_api.py:4083-4084)
```python
# Lists ALL refs (branches and tags) — no revision needed
f"{self.endpoint}/api/{repo_type}s/{repo_id}/refs"
# Response: GitRefs(branches=[GitRefInfo(...)], converts=[GitRefInfo(...)], tags=[...])
```

#### 3f. Revision Exists Check (hf_api.py:3722-3726)
```python
def revision_exists(self, repo_id, revision, ...):
    try:
        self.repo_info(repo_id=repo_id, revision=revision, ...)
        return True
    except RevisionNotFoundError:
        return False
    except RepositoryNotFoundError:
        return False
```
Uses `repo_info` internally — if no exception is raised, the revision exists.

### 4. File Download Resolution (`/resolve/` endpoint)

The `hf_hub_download()` function in `file_download.py` implements the most complex revision resolution pipeline:

#### 4a. Default Revision (file_download.py:960-961)
```python
if revision is None:
    revision = constants.DEFAULT_REVISION  # "main"
```

#### 4b. Commit Hash Fast Path (file_download.py:1071-1084)
```python
if REGEX_COMMIT_HASH.match(revision):
    pointer_path = _get_pointer_path(storage_folder, revision, relative_filename)
    if os.path.exists(pointer_path):
        if not force_download:
            return pointer_path  # shortcut: file already in cache at this commit
```
**Fast path:** If the revision is a full 40-character hex commit SHA, the system checks the local snapshot directory directly: `<cache>/models--repo-id/snapshots/<commit_hash>/<filename>`. If the file exists, it's returned immediately with NO network request.

#### 4c. HEAD Request Resolution (file_download.py:1088-1101, 1694-1717)
For non-commit-hash revisions (branch names, tags, special refs), the system makes a HEAD request:
```python
url = hf_hub_url(repo_id, filename, repo_type=repo_type, revision=revision, endpoint=endpoint)
# Example HEAD: https://huggingface.co/bert-base-uncased/resolve/main/config.json
metadata = get_hf_file_metadata(url=url, ...)
```
The HEAD response returns:
- `X-Repo-Commit` header → the resolved commit SHA (`commit_hash`)
- `ETag` or `X-Linked-Etag` → content fingerprint for caching
- `Content-Length` or `X-Linked-Size` → file size
- `Location` → redirected URL (for CDN/LFS)

#### 4d. Local Cache Fallback (file_download.py:1113-1139)
If the HEAD request fails (offline, network error, 5xx), the system falls back to local cache:
```python
if REGEX_COMMIT_HASH.match(revision):
    commit_hash = revision  # direct lookup
else:
    ref_path = os.path.join(storage_folder, "refs", revision)
    if os.path.isfile(ref_path):
        with open(ref_path) as f:
            commit_hash = f.read()  # read commit hash from refs file
```
The `refs/` directory maps branch/tag names to commit hashes:
```
<storage>/
  refs/
    main          → contains "2439f60ef33a0d46d85da5001d52aeda5b00ce9f"
    v1.0          → contains "bbc77c8132af1cc5cf678da3f1ddf2de43606d48"
  snapshots/
    2439f60ef33a0d46d85da5001d52aeda5b00ce9f/
      config.json → ../../blobs/d7edf6bd2a681fb0175f7735299831ee1b22b812
     bbc77c8132af1cc5cf678da3f1ddf2de43606d48/
      config.json → ../../blobs/403450e234d65943a7dcf7e05a771ce3c92faa84dd07db4ac20f592037a1e4bd
  blobs/
    d7edf6bd2a681fb0175f7735299831ee1b22b812   (actual file content, deduplicated by hash)
    403450e234d65943a7dcf7e05a771ce3c92faa84dd07db4ac20f592037a1e4bd
```

#### 4e. XET Tree Cache (file_download.py:1682-1692)
For the XET storage backend, an additional optimization exists:
```python
if tree_cache_folder is not None and REGEX_COMMIT_HASH.match(revision):
    tree_metadata = _xet_file_metadata_from_tree_cache(...)
    if tree_metadata is not None:
        return tree_metadata  # skip the HEAD call entirely
```
This rebuilds file metadata from an on-disk tree listing for commit-hash lookups, eliminating the per-file HEAD request.

### 5. Refs API — Listing All Named Revisions

The `list_repo_refs()` method (hf_api.py:4032-4101) returns all branches, tags, converts, and optionally PRs:

```python
response = get_session().get(
    f"{self.endpoint}/api/{repo_type}s/{repo_id}/refs",
    headers=self._build_hf_headers(token=token),
    params={"include_prs": 1} if include_pull_requests else {},
)
```

**Response structure:**
```python
@dataclass
class GitRefs:
    branches: list[GitRefInfo]   # Regular git branches
    converts: list[GitRefInfo]   # Convert refs (e.g., refs/convert/parquet)
    tags: list[GitRefInfo]       # Git tags
    pull_requests: list[GitRefInfo] | None  # PR refs (only if include_pull_requests=True)

@dataclass
class GitRefInfo:
    name: str            # "main"
    ref: str             # "refs/heads/main"
    target_commit: str   # "e7da7f221d5bf496a48136c0cd264e630fe9fcc8"
```

**Key detail:** The `converts` field lists special `refs/convert/` branches (used for dataset parquet conversions). These are regular git branches but segregated in the API response.

### 6. Special Refs — PRs, Convert Refs, and Others

#### 6a. PR Refs (`refs/pr/N`)
Pull requests on the Hub create lightweight refs at `refs/pr/<number>`. These can be used as a `revision` parameter:

```python
hf_hub_url("bert-base-uncased", "config.json", revision="refs/pr/5")
# → https://huggingface.co/bert-base-uncased/resolve/refs%2Fpr%2F5/config.json
```

The URL-encoded form (`refs%2Fpr%2F5`) is critical — without encoding, the slash would be interpreted as a path separator.

#### 6b. Convert Refs (`refs/convert/parquet`)
Used by the datasets server to store auto-converted parquet versions of datasets. These are special refs that can be listed via `list_repo_refs()` where they appear in the `converts` field.

#### 6c. SPECIAL_REFS_REVISION_REGEX (hf_api.py:265-272)
```python
SPECIAL_REFS_REVISION_REGEX = re.compile(
    r"""
    (^refs\/convert\/\w+)     # `refs/convert/parquet` revisions
    |
    (^refs\/pr\/\d+)          # PR revisions
    """,
    re.VERBOSE,
)
```
This regex is used in `HfFileSystem` path resolution to determine whether a revision should be kept **unquoted** in `hf://` URIs:
```python
def safe_revision(revision: str) -> str:
    return revision if SPECIAL_REFS_REVISION_REGEX.match(revision) else safe_quote(revision)
```
Special refs are displayed without URL-encoding in `hf://` paths for readability, but are still URL-encoded when making actual HTTP requests.

### 7. URL Encoding Rules

Different layers apply different quoting:

| Layer | Encoding | Example |
|-------|----------|---------|
| **hf_hub_url()** | `quote(revision, safe="")` — encode everything | `refs%2Fpr%2F5` |
| **REST API** (model_info, tree, commits) | `quote(revision, safe="")` | `refs%2Fpr%2F5` |
| **create_commit** | `quote(unquoted_revision, safe="")` | `refs%2Fpr%2F5` |
| **HfFileSystem hf:// URI** | `safe_revision()` — special refs unquoted, others quoted | `hf://repo@refs/pr/5` vs `hf://repo@feature%2Fbranch` |
| **Branch creation API** | `quote(branch, safe="")` — branch name itself | branch name always quoted |

**Why this matters:** A branch name like `feature/my-branch` contains a slash. In a URL, the slash would be interpreted as a path separator. URL-encoding to `feature%2Fmy-branch` ensures it stays as a single revision identifier.

### 8. Cache Layout — How Revisions Map to Local Storage

```
~/.cache/huggingface/hub/
├── models--bert-base-uncased/        (repo_folder_name = "{repo_type}s--{repo_id}")
│   ├── blobs/
│   │   ├── d7edf6bd2a681fb0175f7735299831ee1b22b812     (blob content, keyed by hash)
│   │   └── 403450e234d65943a7dcf7e05a771ce3c92faa84dd07db4ac20f592037a1e4bd
│   ├── refs/
│   │   ├── main                                           (contains commit SHA)
│   │   ├── v1.0                                           (contains commit SHA)
│   │   └── refs/pr/5                                      (revision-as-path for PR refs)
│   └── snapshots/
│       ├── 2439f60ef33a0d46d85da5001d52aeda5b00ce9f/      (commit SHA directory)
│       │   ├── config.json → ../../blobs/d7edf6bd2a...
│       │   └── model.safetensors → ../../blobs/403450e2...
│       └── bbc77c8132af1cc5cf678da3f1ddf2de43606d48/
│           └── config.json → ../../blobs/7cb18dc9baf...
```

The `repo_folder_name()` function (file_download.py:718-726):
```python
def repo_folder_name(*, repo_id: str, repo_type: str) -> str:
    parts = [f"{repo_type}s", *repo_id.split("/")]
    return REPO_ID_SEPARATOR.join(parts)  # "--" separator
# Example: repo_folder_name("bert-base-uncased", "model") → "models--bert-base-uncased"
# Example: repo_folder_name("bigcode/the-stack", "dataset") → "datasets--bigcode--the-stack"
```

### 9. snapshot_download — Multi-File Revision Resolution

The `snapshot_download()` function (`_snapshot_download.py`) resolves the revision for a batch download:

**Key code path (line 298):**
```python
if REGEX_COMMIT_HASH.match(revision):
    # Use the commit hash directly for cache lookup
    ...
else:
    # For branches/tags, resolve via HEAD request first
    # Then use the resolved commit hash for subsequent file checks
```

The `dry_run` mode returns a `list[DryRunFileInfo]` with the resolved commit hash for each file:
```python
@dataclass
class DryRunFileInfo:
    commit_hash: str   # The resolved commit SHA
    file_size: int
    filename: str
    is_cached: bool
    local_path: str
    will_download: bool
```

### 10. Branch and Tag Management

The API methods for managing refs:

#### 10a. Creating Branches (hf_api.py:6901-6979)
```python
# POST {endpoint}/api/{repo_type}s/{repo_id}/branch/{quoted_branch}
# Body: {"startingPoint": revision}  # optional, defaults to main
```
The branch name itself is URL-quoted with `quote(branch, safe="")`. If `exist_ok=True`, a 409 error means the branch already exists and returns silently.

#### 10b. Creating Tags (hf_api.py:7034-7063)
```python
# POST {endpoint}/api/{repo_type}s/{repo_id}/tag/{quoted_tag}
# Body: {"startingPoint": revision, "description": tag_message}
```
Same pattern as branches but for immutable tags.

#### 10c. Deleting Branches/Tags (hf_api.py:6981-7019, 7108+)
```python
# DELETE {endpoint}/api/{repo_type}s/{repo_id}/branch/{quoted_branch}
# DELETE {endpoint}/api/{repo_type}s/{repo_id}/tag/{quoted_tag}
```
Protected branches (e.g., `main`) cannot be deleted.

### 11. Revision Error Handling

| Error | Raised When | Status Code |
|-------|-------------|-------------|
| `RepositoryNotFoundError` | Repo doesn't exist or is private without auth | 404 |
| `RevisionNotFoundError` | Repo exists but revision string doesn't resolve | 404 |
| `EntryNotFoundError` | Repo and revision exist but file not found | 404 |
| `LocalEntryNotFoundError` | Network offline and file not in local cache | — |
| `HfHubHTTPError` | Generic HTTP error (auth, rate limit, server error) | Various |

### 12. Practical Usage Patterns

```python
# 1. Check if a revision exists without downloading anything
from huggingface_hub import revision_exists
revision_exists("google/gemma-7b", "float16")  # True
revision_exists("google/gemma-7b", "nonexistent-branch")  # False

# 2. List all available revisions (branches and tags)
from huggingface_hub import HfApi
api = HfApi()
refs = api.list_repo_refs("gpt2")
for branch in refs.branches:
    print(f"  {branch.name} → {branch.target_commit}")

# 3. Get file metadata at a specific revision without downloading
from huggingface_hub import hf_hub_url, get_hf_file_metadata
url = hf_hub_url("gpt2", "config.json", revision="v1.0")
metadata = get_hf_file_metadata(url)
print(f"Commit: {metadata.commit_hash}, Size: {metadata.size}")

# 4. Download a specific PR revision
from huggingface_hub import hf_hub_download
path = hf_hub_download("user/repo", "file.txt", revision="refs/pr/5")

# 5. Get model info at a specific revision
info = api.model_info("bert-base-uncased", revision="v1.0.0")
print(f"SHA: {info.sha}")  # The resolved commit hash

# 6. Use a shortened commit SHA (7+ hex chars)
# NOTE: REGEX_COMMIT_HASH requires exactly 40 hex chars
# Shorthands are resolved server-side via the /resolve/ endpoint
# but the LOCAL CACHE FAST PATH does NOT work with shorthands
path = hf_hub_download("user/model", "config.json", revision="abc1234")
# Works via server HEAD request, but won't use fast-path local lookup
```

### 13. Key Insights

1. **Commit hash is the canonical revision.** Everything (branch, tag, special ref) ultimately resolves to a 40-character commit SHA. The local cache is organized by commit SHA, not by branch name.

2. **The `refs/` directory is the local resolution map.** When offline, branch/tag lookups fall back to reading `<storage>/refs/<name>` which contains the commit SHA. This is updated on every successful HEAD request.

3. **PR refs work as revisions but are not branches.** `refs/pr/5` is a special Git ref that can be downloaded from but never appears in the `branches` list — only in `pull_requests` (when `include_pull_requests=True`).

4. **URL encoding is asymmetric.** The `HfFileSystem` (`hf://` URIs) displays special refs without encoding for readability, but the REST API and download URL layer always encode. This means `hf://repo@refs/pr/5` is displayed unquoted but translates to a URL-encoded HTTP request.

5. **Short commit SHAs work but bypass local cache optimization.** Because `REGEX_COMMIT_HASH` requires exactly 40 hex characters, a 7-character SHA shorthand will always trigger a HEAD request (even if the file is already cached under the full commit hash).

6. **The `X-Repo-Commit` header is the source of truth.** Every HEAD response from `/resolve/` returns this header containing the resolved commit SHA. The client uses it to build the local cache snapshot path and update the `refs/` mapping.
