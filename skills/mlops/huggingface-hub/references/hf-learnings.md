# HF Learnings — Hugging Face Hub

## 2026-07-24: hf-hub-exception-reference — Complete Exception Hierarchy (Topic #130)

### Summary
Comprehensive reference of all custom exceptions in the `huggingface_hub` library (v1.24.0+). Covers the full exception hierarchy (50+ classes), inheritance relationships, attributes, when each error is raised, and error-handling patterns for production use. Source: `huggingface_hub/errors.py` on GitHub.

### Exception Hierarchy Overview

All custom exceptions in huggingface_hub. Indentation = inheritance:

```
Exception
├── CacheNotFound
├── CorruptedCacheException
├── CachedRepoTreeNotFoundError
├── OIDCError
├── DeviceCodeError
├── EntryNotFoundError (abstract base)
│   ├── RemoteEntryNotFoundError (also HfHubHTTPError)
│   └── LocalEntryNotFoundError (also FileNotFoundError)
│       └── IncompleteSnapshotError
├── InferenceEndpointError
│   └── InferenceEndpointTimeoutError (also TimeoutError)
├── SafetensorsParsingError
├── NotASafetensorsRepoError
├── DDUFError
│   ├── DDUFCorruptedFileError
│   └── DDUFExportError
│       └── DDUFInvalidEntryNameError
├── StrictDataclassError
│   ├── StrictDataclassDefinitionError
│   ├── StrictDataclassFieldValidationError
│   └── StrictDataclassClassValidationError
├── XetDownloadError
├── FileDuplicationError
├── CLIError
│   ├── ConfirmationError
│   └── CLIExtensionInstallError
├── SandboxError
│   └── SandboxCommandError
├── HfHubHTTPError (also httpx.HTTPError, OSError)
│   ├── RepositoryNotFoundError
│   │   └── GatedRepoError
│   ├── DisabledRepoError
│   ├── RevisionNotFoundError
│   ├── RemoteEntryNotFoundError (also EntryNotFoundError)
│   ├── BadRequestError (also ValueError)
│   ├── BucketNotFoundError
│   └── JobNotFoundError

HTTPError (httpx)
├── InferenceTimeoutError (also TimeoutError)
└── TextGenerationError
    ├── ValidationError
    ├── GenerationError
    ├── OverloadedError
    ├── IncompleteGenerationError
    └── UnknownError

OSError
├── HfHubHTTPError (see above — multiple inheritance)
├── DryRunError
├── FileMetadataError
└── LocalTokenNotFoundError (EnvironmentError)

ConnectionError
└── OfflineModeIsEnabled

ValueError
├── HFValidationError
├── HfUriError
└── BadRequestError (also HfHubHTTPError)

FileNotFoundError
└── LocalEntryNotFoundError (also EntryNotFoundError)
```

### HTTP Errors (Most Commonly Used)

#### HfHubHTTPError — The Base
All Hub HTTP requests that fail are converted to `HfHubHTTPError` (or a subclass). Uses the `hf_raise_for_status()` utility.

```python
from huggingface_hub.utils import hf_raise_for_status, HfHubHTTPError
import httpx

response = httpx.get("https://huggingface.co/api/models/unknown-model")
try:
    hf_raise_for_status(response)
except HfHubHTTPError as e:
    print(e.request_id)         # "Root=1-xxx" — X-Request-Id header
    print(e.server_message)     # Server error detail from header/body
    print(e.response)           # Full httpx.Response object
    print(e.request)            # Full httpx.Request object
    e.append_to_message("\nCheck repo_id and try again.")  # Enrich inline
    raise
```

**Error selection logic** in `hf_raise_for_status()`:
- HTTP 400 → `BadRequestError`
- HTTP 401/404 + "Not Found" in body → `RepositoryNotFoundError`
- HTTP 403 + "gated" in body or headers → `GatedRepoError`
- HTTP 403 + "disabled" → `DisabledRepoError`
- HTTP 404 + "Revision Not Found" → `RevisionNotFoundError`
- HTTP 404 + "Entry Not Found" → `RemoteEntryNotFoundError`
- HTTP 404 + "Bucket" in body → `BucketNotFoundError`
- All other 4xx/5xx → plain `HfHubHTTPError`

#### RepositoryNotFoundError
```python
try:
    model_info("nonexistent/repo")
except RepositoryNotFoundError as e:
    print(e.repo_id)      # "nonexistent/repo"
    print(e.repo_type)    # "model"
    # Handle: check credentials, check repo_id spelling
```

#### GatedRepoError (subclass of RepositoryNotFoundError)
```python
try:
    model_info("meta-llama/Llama-2-7b")
except GatedRepoError:
    # User is not authorized — needs to request access
    # Falls through to RepositoryNotFoundError catch too (inheritance)
```

#### RevisionNotFoundError
```python
try:
    hf_hub_download("bert-base-cased", "config.json", revision="nonexistent-branch")
except RevisionNotFoundError as e:
    print(e.repo_id)      # "bert-base-cased"
    print(e.repo_type)    # "model"
```

#### RemoteEntryNotFoundError
```python
try:
    hf_hub_download("bert-base-cased", "nonexistent-file.bin")
except (RemoteEntryNotFoundError, LocalEntryNotFoundError) as e:
    # Handle missing file
    pass
```

#### BadRequestError
```python
try:
    create_repo("invalid///name")
except BadRequestError as e:
    # HTTP 400 — invalid request
    print(str(e))
```

### Cache & Local File Errors

#### LocalEntryNotFoundError
Raised in `local_files_only=True` mode when a file isn't cached:
```python
try:
    hf_hub_download("bert-base-cased", "config.json", local_files_only=True)
except LocalEntryNotFoundError:
    # File not in local cache, and network disabled
    pass
```

#### IncompleteSnapshotError
Raised by `snapshot_download` when cached snapshot is incomplete and network is unavailable:
```python
try:
    snapshot_download("bert-base-cased", local_files_only=True)
except IncompleteSnapshotError as e:
    print(e.snapshot_path)  # Path to partial snapshot
    # Use whatever files are available
```

#### CacheNotFound / CorruptedCacheException
```python
from huggingface_hub.errors import CacheNotFound
# Raised when ~/.cache/huggingface/ doesn't exist or is corrupted
```

#### CachedRepoTreeNotFoundError
Raised when `get_cached_repo_tree()` is called but no tree listing was cached by `snapshot_download`.

### Inference & TGI Errors

#### InferenceTimeoutError
```python
from huggingface_hub import InferenceClient

client = InferenceClient()
try:
    client.text_generation("meta-llama/Llama-2-7b", "Hello", max_tokens=500)
except InferenceTimeoutError:
    # Model unavailable, loading, or request timed out
    # Retry with backoff or try a different model
    pass
```

#### Text Generation Error Family (TGI)
```python
from huggingface_hub import InferenceClient
from huggingface_hub.errors import (
    ValidationError, GenerationError, OverloadedError,
    IncompleteGenerationError, UnknownError
)

client = InferenceClient()
try:
    client.text_generation("meta-llama/Llama-2-7b", "Hello")
except OverloadedError:
    # Model is busy — retry with exponential backoff
    pass
except ValidationError:
    # Bad input — fix the prompt
    pass
except GenerationError:
    # Generation failed mid-stream
    pass
except IncompleteGenerationError:
    # Response was truncated — partial output available in response
    pass
except UnknownError:
    # Unclassified TGI error
    pass
```

### Auth & Token Errors

#### LocalTokenNotFoundError
```python
from huggingface_hub.errors import LocalTokenNotFoundError

try:
    # Operation requires token but none found
    whoami()
except LocalTokenNotFoundError:
    print("Please run `huggingface-cli login` or set HF_TOKEN")
```

#### DeviceCodeError
Raised during OAuth device code flow:
```python
from huggingface_hub.errors import DeviceCodeError, OAuthErrorCode

try:
    login()
except DeviceCodeError as e:
    if e.error_code == OAuthErrorCode.ACCESS_DENIED:
        print("User denied authorization")
    elif e.error_code == OAuthErrorCode.EXPIRED_TOKEN:
        print("Device code expired, restart flow")
```

The `OAuthErrorCode` enum provides known error codes: `AUTHORIZATION_PENDING`, `SLOW_DOWN`, `EXPIRED_TOKEN`, `ACCESS_DENIED`, `INVALID_GRANT`.

#### OIDCError
Raised when Trusted Publishers / OIDC token exchange fails:
```python
from huggingface_hub.errors import OIDCError

try:
    create_repo("my-private-model", private=True)
except OIDCError:
    # Not running in a supported CI provider or HF_OIDC_ID_TOKEN unset
    pass
```

### Offline Mode

#### OfflineModeIsEnabled
```python
from huggingface_hub.errors import OfflineModeIsEnabled
import os

os.environ["HF_HUB_OFFLINE"] = "1"
try:
    hf_hub_download("bert-base-cased", "config.json")
except OfflineModeIsEnabled:
    print("Cannot download: offline mode is active")
```

### Validation Errors

#### HFValidationError
Generic validation for repo IDs, token formats, etc.:
```python
from huggingface_hub.utils import HFValidationError

try:
    hf_hub_download("Invalid Repo ID!!!", "file.txt")
except HFValidationError as e:
    print(f"Invalid input: {e}")
```

#### HfUriError
Raised for malformed `hf://...` URIs:
```python
from huggingface_hub.errors import HfUriError

try:
    hf_hub_download("hf://invalid-uri")
except HfUriError as e:
    print(e.uri)   # The malformed URI
    print(e.msg)   # Human-readable explanation
```

### Resource-Specific Errors

#### BucketNotFoundError
```python
from huggingface_hub import bucket_info
from huggingface_hub.errors import BucketNotFoundError

try:
    bucket_info("nonexistent/bucket")
except BucketNotFoundError as e:
    print(e.bucket_id)  # "nonexistent/bucket"
    # Handle: wrong bucket path, or bucket deleted
```

#### JobNotFoundError
```python
from huggingface_hub.errors import JobNotFoundError

try:
    get_job_status("nonexistent-job-id")
except JobNotFoundError as e:
    print(e.job_id)  # "nonexistent-job-id"
```

### Safetensors Errors

```python
from huggingface_hub.errors import SafetensorsParsingError, NotASafetensorsRepoError

try:
    get_safetensors_metadata("user/repo")
except NotASafetensorsRepoError:
    print("Repo doesn't use safetensors format")
except SafetensorsParsingError:
    print("safetensors file is corrupted or invalid")
```

### Sandbox Errors

```python
from huggingface_hub import Sandbox
from huggingface_hub.errors import SandboxCommandError, SandboxError

sandbox = Sandbox()
try:
    result = sandbox.run("python script.py")
except SandboxCommandError as e:
    print(e.cmd)               # The command that failed
    print(e.result.exit_code)  # Exit code
    print(e.result.stderr)     # Stderr output
    print(e.result.timed_out)  # Was it a timeout?
```

### Strict Dataclass Errors (Advanced)

The `StrictDataclass` system validates HuggingFace Hub API response models:

```python
from huggingface_hub.errors import (
    StrictDataclassDefinitionError,
    StrictDataclassFieldValidationError,
    StrictDataclassClassValidationError,
)
```

### Error Handling Best Practices

**1. Broad catch with HfHubHTTPError**
```python
from huggingface_hub.utils import HfHubHTTPError

try:
    result = some_hub_operation()
except HfHubHTTPError as e:
    # All Hub API errors inherit from this
    status = e.response.status_code
    if status == 429:
        # Rate limited — exponential backoff
        time.sleep(2 ** attempt)
    elif status >= 500:
        # Server error — retry
        pass
    else:
        # Client error — don't retry
        raise
```

**2. Distinguish network vs Hub errors**
```python
import httpx

try:
    result = some_hub_operation()
except HfHubHTTPError as e:
    # Server responded with error
    handle_hub_error(e)
except httpx.ConnectError:
    # Network unreachable (no response at all)
    handle_network_error()
except httpx.TimeoutException:
    # Request timed out
    handle_timeout()
```

**3. Offline-aware fallback**
```python
from huggingface_hub import hf_hub_download
from huggingface_hub.errors import OfflineModeIsEnabled, LocalEntryNotFoundError

try:
    path = hf_hub_download(repo_id, filename, local_files_only=True)
except (OfflineModeIsEnabled, LocalEntryNotFoundError):
    # No network or not cached
    path = DEFAULT_FALLBACK_PATH
```

**4. Gated repo detection**
```python
try:
    info = model_info("meta-llama/Llama-2-7b")
except GatedRepoError:
    # Known pattern: repo exists but needs access request
    print("Request access at https://huggingface.co/meta-llama/Llama-2-7b")
except RepositoryNotFoundError:
    # Repo genuinely doesn't exist (or wrong permissions)
    print("Repository not found")
```

### The `hf_raise_for_status()` Utility

The main entry point for converting httpx responses to native errors:

```python
from huggingface_hub.utils import hf_raise_for_status, HfHubHTTPError
import httpx

response = httpx.get("https://huggingface.co/api/models/bert-base-uncased")
try:
    hf_raise_for_status(response)
except HfHubHTTPError:
    # Automatically catches all HTTP error subclasses
    raise
```

Internal dispatch logic:
1. Extracts `X-Request-Id`, `X-Amzn-Trace-Id`, or `x-amz-cf-id` → `request_id`
2. Reads `X-Error-Message` header → `server_message`
3. Falls back to parsing response body for error context
4. Selects the most specific exception class based on status code and body content
5. The exception can be enriched post-creation with `append_to_message()`

### Complete List of All 50+ Exception Classes

| # | Exception | Parent(s) | When Raised |
|---|-----------|-----------|-------------|
| 1 | `HfHubHTTPError` | `HTTPError, OSError` | All failed Hub HTTP requests |
| 2 | `RepositoryNotFoundError` | `HfHubHTTPError` | Repo doesn't exist or no access |
| 3 | `GatedRepoError` | `RepositoryNotFoundError` | Gated repo, not authorized |
| 4 | `DisabledRepoError` | `HfHubHTTPError` | Repo disabled by author |
| 5 | `RevisionNotFoundError` | `HfHubHTTPError` | Invalid revision/branch/tag |
| 6 | `BadRequestError` | `HfHubHTTPError, ValueError` | HTTP 400 bad request |
| 7 | `BucketNotFoundError` | `HfHubHTTPError` | Bucket not found |
| 8 | `JobNotFoundError` | `HfHubHTTPError` | Job not found |
| 9 | `RemoteEntryNotFoundError` | `HfHubHTTPError, EntryNotFoundError` | File not found on Hub |
| 10 | `EntryNotFoundError` | `Exception` | Abstract base for entry errors |
| 11 | `LocalEntryNotFoundError` | `FileNotFoundError, EntryNotFoundError` | File not cached locally |
| 12 | `IncompleteSnapshotError` | `LocalEntryNotFoundError` | Cached snapshot incomplete |
| 13 | `CacheNotFound` | `Exception` | Cache directory missing |
| 14 | `CorruptedCacheException` | `Exception` | Cache has unexpected structure |
| 15 | `CachedRepoTreeNotFoundError` | `Exception` | No cached tree listing |
| 16 | `OfflineModeIsEnabled` | `ConnectionError` | `HF_HUB_OFFLINE=1` set |
| 17 | `InferenceTimeoutError` | `HTTPError, TimeoutError` | Model unavailable/timeout |
| 18 | `InferenceEndpointError` | `Exception` | Generic IE error |
| 19 | `InferenceEndpointTimeoutError` | `InferenceEndpointError, TimeoutError` | IE timeout |
| 20 | `TextGenerationError` | `HTTPError` | Generic TGI error |
| 21 | `ValidationError` | `TextGenerationError` | TGI bad input |
| 22 | `GenerationError` | `TextGenerationError` | TGI generation failure |
| 23 | `OverloadedError` | `TextGenerationError` | TGI overloaded |
| 24 | `IncompleteGenerationError` | `TextGenerationError` | TGI truncated response |
| 25 | `UnknownError` | `TextGenerationError` | TGI unclassified |
| 26 | `LocalTokenNotFoundError` | `EnvironmentError` | No HF token found |
| 27 | `OIDCError` | `Exception` | OIDC token exchange failed |
| 28 | `DeviceCodeError` | `Exception` | OAuth device code flow failed |
| 29 | `HFValidationError` | `ValueError` | Generic validation failure |
| 30 | `HfUriError` | `ValueError` | Malformed hf:// URI |
| 31 | `SafetensorsParsingError` | `Exception` | Corrupt safetensors file |
| 32 | `NotASafetensorsRepoError` | `Exception` | No safetensors in repo |
| 33 | `DryRunError` | `OSError` | Dry run cannot proceed |
| 34 | `FileMetadataError` | `OSError` | Missing ETag/commit_hash |
| 35 | `DDUFError` | `Exception` | Base DDUF error |
| 36 | `DDUFCorruptedFileError` | `DDUFError` | Corrupt DDUF file |
| 37 | `DDUFExportError` | `DDUFError` | Base DDUF export error |
| 38 | `DDUFInvalidEntryNameError` | `DDUFExportError` | Invalid DDUF entry name |
| 39 | `StrictDataclassError` | `Exception` | Base strict dataclass error |
| 40 | `StrictDataclassDefinitionError` | `StrictDataclassError` | Incorrect definition |
| 41 | `StrictDataclassFieldValidationError` | `StrictDataclassError` | Field validation failed |
| 42 | `StrictDataclassClassValidationError` | `StrictDataclassError` | Class validator failed |
| 43 | `XetDownloadError` | `Exception` | Xet storage download failed |
| 44 | `FileDuplicationError` | `Exception` | File duplication failed |
| 45 | `CLIError` | `Exception` | Base CLI error |
| 46 | `ConfirmationError` | `CLIError` | Confirmation declined |
| 47 | `CLIExtensionInstallError` | `CLIError` | CLI extension install failed |
| 48 | `SandboxError` | `Exception` | Base sandbox error |
| 49 | `SandboxCommandError` | `SandboxError` | Sandbox command failed |
| 50 | `OAuthErrorCode` | `Enum` | Known OAuth error codes |

### Key Design Patterns

1. **Multiple inheritance for compatibility**: `HfHubHTTPError` inherits both `httpx.HTTPError` and `OSError` so that `except OSError` and `except httpx.HTTPError` both catch Hub errors.

2. **GatedRepoError is a RepositoryNotFoundError** — backward compatible: code catching `RepositoryNotFoundError` will also catch gate errors, preventing silent breakage when repos switch from open to gated.

3. **EntryNotFoundError is abstract** — never raised directly; always subclassed by `LocalEntryNotFoundError` or `RemoteEntryNotFoundError`.

4. **Error enrichment**: Use `HfHubHTTPError.append_to_message()` to add context without losing the original error data.

5. **Request ID tracing**: Every `HfHubHTTPError` carries a `request_id` from Hub response headers, enabling correlation with server-side logs.

### Resources
- Source: `huggingface_hub/errors.py` — all 50+ exception classes
- `huggingface_hub/utils/_errors.py` — `hf_raise_for_status()` dispatch
- `huggingface_hub/utils/_validators.py` — validation error triggers
- OAuth error codes: RFC 6749 (Authorization Code), RFC 8628 (Device Code)

---

## 2026-07-24: hf-hub-buckets-api-deep-dive — Bucket Object Storage (Topic #105)

### Summary
Comprehensive deep-dive into the **Hugging Face Hub Buckets API** — a full S3-compatible object storage system built into `huggingface_hub` v1.24.0+. Buckets provide file storage outside the Git/LFS model, accessible via `hf://buckets/...` URIs with batch operations, bidirectional sync, file filtering, and plan/apply workflows.

This is a **major new feature** in huggingface-hub v1.x — not available in the 0.x series.

### Core Concept

Buckets are **object storage containers** on the Hugging Face Hub. Unlike repos (which use Git + LFS), buckets are:
- **Git-free** — no commit history, no branching, no pull requests
- **Flat-ish** — hierarchical paths but no Git tree overhead
- **Batch-optimized** — add/delete multiple files in a single API call
- **Sync-native** — designed for bidirectional sync with local directories
- **XET-powered** — uses the Xet protocol for fast, deduplicated storage

**URL scheme:** `hf://buckets/{namespace}/{bucket_name}(/path/to/file)`

### Bucket Data Model

| Concept | Description |
|---------|-------------|
| **Bucket** | Top-level storage container, owned by a user or org |
| **File** | A blob stored in a bucket at a path (no Git tracking) |
| **Folder** | Virtual directory — created implicitly by file paths |
| **Prefix** | Path prefix for scoping operations (like S3 prefix) |
| **Namespace** | User or organization name that owns the bucket |

### CLI Commands (`hf buckets`)

The `hf` CLI (not `huggingface-cli`) provides full bucket management:

| Command | Description | Example |
|---------|-------------|---------|
| `create` | Create a new bucket | `hf buckets create user/my-bucket` |
| `list` / `ls` | List buckets or files in a bucket | `hf buckets list user/my-bucket -R` |
| `info` | Get bucket metadata | `hf buckets info user/my-bucket` |
| `delete` | Delete entire bucket and contents | `hf buckets delete user/my-bucket -y` |
| `remove` / `rm` | Remove individual files | `hf buckets rm user/my-bucket/file.txt` |
| `move` | Rename/move a bucket | `hf buckets move user/old user/new` |
| `cp` | Copy files to/from buckets | `hf cp file.txt hf://buckets/user/my-bucket/` |
| `sync` | Bidirectional sync local↔bucket | `hf sync /local/data hf://buckets/user/my-bucket` |

**`hf buckets create` options:**
- `--private` — create a private bucket (default: public)
- `--region` — `us` or `eu` (requires Team plan+)
- `--exist-ok` — don't error if bucket already exists

**`hf buckets ls`** has two modes:
1. **List buckets** (no argument or namespace only): `hf buckets list`
2. **List files** (bucket_id given): `hf buckets list user/my-bucket -R --tree`

Flags: `-R` (recursive), `-h` (human-readable sizes), `--tree` (tree format)

**`hf buckets rm`** supports:
- `-R` / `--recursive` — delete files under a prefix
- `--include "*.safetensors"` / `--exclude "*.tmp"` — filter patterns
- `--dry-run` — preview without deleting
- `-y` — skip confirmation

**`hf cp`** (unified copy across repos and buckets):
```bash
# Upload to bucket
hf cp ./model.safetensors hf://buckets/user/my-bucket/models/

# Download from bucket
hf cp hf://buckets/user/my-bucket/config.json ./config.json

# Pipe to stdout
hf cp hf://buckets/user/my-bucket/log.txt -

# Remote-to-remote (same region)
hf cp hf://buckets/user/source/path hf://buckets/user/dest/path
```

**`hf buckets sync`** — bidirectional sync:
```bash
# Upload local → bucket
hf sync ./data hf://buckets/user/my-bucket

# Download bucket → local
hf sync hf://buckets/user/my-bucket ./data

# Dry-run first
hf sync ./data hf://buckets/user/my-bucket --dry-run

# Delete remote files not in source
hf sync ./data hf://buckets/user/my-bucket --delete

# Pattern filtering
hf sync ./data hf://buckets/user/my-bucket --include "*.safetensors" --exclude "*.tmp"

# Ignore existing files (only upload new ones)
hf sync ./data hf://buckets/user/my-bucket --ignore-existing

# Only update existing files (don't upload new)
hf sync ./data hf://buckets/user/my-bucket --existing

# Save plan, review, apply
hf sync ./data hf://buckets/user/my-bucket --plan sync-plan.jsonl
hf sync --apply sync-plan.jsonl
```

### Python API (`HfApi`)

All bucket operations available via `HfApi`:

```python
from huggingface_hub import HfApi

api = HfApi()

# Create bucket
url = api.create_bucket("my-bucket", private=True)
print(url.uri.to_uri())  # hf://buckets/user/my-bucket

# List buckets
for bucket in api.list_buckets(namespace="user"):
    print(bucket.id, bucket.size, bucket.total_files)

# Bucket info
info = api.bucket_info("user/my-bucket")
print(info.size, info.total_files, info.private)

# List files (lazy iterator)
for item in api.list_bucket_tree("user/my-bucket", prefix="data/", recursive=True):
    if item.type == "file":
        print(f"  {item.path} ({item.size} bytes)")
    elif item.type == "directory":
        print(f"  {item.path}/")

# Upload files (batch)
api.batch_bucket_files(
    "user/my-bucket",
    add=[
        ("/local/file1.txt", "remote/path/file1.txt"),
        ("/local/file2.txt", "remote/path/file2.txt"),
        (b"raw bytes content", "config.json"),  # bytes also accepted
    ],
)

# Delete files (batch)
api.batch_bucket_files(
    "user/my-bucket",
    delete=["old-file.txt", "temp/data.tmp"],
)

# Copy files (cross-bucket or repo-to-bucket)
api.batch_bucket_files(
    "user/my-bucket",
    copy=[("xet_hash_here", "destination/path", "source_repo_type", "source_repo_id")],
)

# Download files
api.download_bucket_files(
    "user/my-bucket",
    files=[
        ("remote/path/file1.txt", "/local/destination/file1.txt"),
        # Can also pass BucketFile object (more efficient — skips metadata fetch)
    ],
)

# Get file metadata
meta = api.get_bucket_file_metadata("user/my-bucket", "config.json")
print(meta.size, meta.xet_file_data.hash)

# Bidirectional sync
plan = api.sync_bucket(
    source="./data",
    dest="hf://buckets/user/my-bucket",
    delete=True,           # delete remote files not in source
    include=["*.py"],      # only sync .py files
    exclude=["__pycache__"],
    dry_run=True,          # preview without executing
)
print(plan.summary())
```

### Sync API Details

`sync_bucket()` returns a `SyncPlan` object:

```python
plan = api.sync_bucket("./data", "hf://buckets/user/my-bucket")
summary = plan.summary()
# {'uploads': 3, 'downloads': 0, 'deletes': 0, 'skips': 1, 'total_size': 4096}

# Plan/apply pattern for review workflows:
plan = api.sync_bucket("./data", "hf://buckets/user/my-bucket", plan="plan.jsonl")
# ... review plan.jsonl ...
api.sync_bucket(apply="plan.jsonl")
```

**Sync comparison logic** (determines if a file needs upload/download):
1. If file exists on only one side → upload/download (new file)
2. If both sides exist → compare size AND mtime (within 1s window)
   - Size differs → upload/download
   - Source newer → upload/download  
   - Identical → skip
3. Modes:
   - `--ignore-sizes` → only compare mtime
   - `--ignore-times` → only compare size
   - `--existing` → skip files that don't exist on receiver
   - `--ignore-existing` → skip files that DO exist on receiver
   - `--delete` → remove files at destination not present in source

### Filter System

```python
# CLI:
hf sync ./data hf://buckets/user/data --include "*.py" --exclude "__pycache__"

# Filter file (--filter-from):
#   +*.py
#   -__pycache__/*
#   +*.json
#   -*.tmp

# Python:
plan = api.sync_bucket(
    "./data", "hf://buckets/user/data",
    include=["*.py", "*.json"],
    exclude=["*.tmp"],
    filter_from="./.hfignore",
)
```

Filter rules process in order: filter file first, then CLI patterns, then defaults. First matching rule wins.

### Bucket File Metadata

```python
meta = api.get_bucket_file_metadata("user/my-bucket", "model.safetensors")
# BucketFileMetadata:
#   size: int (bytes)
#   xet_file_data: XetFileData (hash + refresh route)

# Bulk metadata:
for file_info in api.get_bucket_paths_info("user/my-bucket", ["a.txt", "b.txt"]):
    print(file_info.path, file_info.size, file_info.xet_hash)
```

### `hf cp` Unified Copy

The `hf cp` command is a single, unified command for copying files across:
- Local ↔ Repo (models/datasets/spaces)
- Local ↔ Bucket
- Repo ↔ Repo (same region)
- Repo ↔ Bucket (repo-to-bucket only; bucket-to-repo not supported)

Sub-aliases `hf repos cp` and `hf buckets cp` provide context-guarded variants.

```bash
# Pipe support
cat config.json | hf cp - hf://buckets/user/my-bucket/config.json
hf cp hf://buckets/user/my-bucket/log.txt -  # pipe to stdout
```

### Zero-Cost Strategy

**Buckets are free** on Hugging Face Hub with per-user storage limits:
- Public buckets: free, unlimited storage (part of Hub's free tier)
- Private buckets: free with storage limits (same as private repos)
- No GPU/compute cost — pure object storage

**Practical uses for zero-cost setup:**
1. Backup model weights to buckets instead of repo LFS (reduces clutter)
2. Share large datasets as flat buckets (no Git overhead for contributors)
3. Store cron outputs, logs, and artifacts from scheduled jobs
4. Sync data between Spaces and local development without Git commits
5. Use `hf://buckets/...` URIs as simple file servers for web content

### Error Handling

- `BucketNotFoundError` — bucket doesn't exist (catch when listing for new buckets)
- `ValueError` — invalid bucket ID format, missing prefix, conflicting sync options
- Batch operations are atomic within a single `batch_bucket_files` call

### CLI — Hidden Features

- **`hf buckets create`** accepts short names (`my-bucket`) — auto-prepends namespace
- **`hf buckets ls` without args** lists all your buckets globally
- **`--tree`** flag gives a nice hierarchical view of files
- **`hf buckets rm --recursive`** with `--include` enables selective mass deletion
- **`hf buckets sync --plan`** saves a JSONL file; `--apply` replays it — enables CI review gate pattern

### Resources
- Source: `huggingface_hub/_buckets.py` (1244 lines) — core bucket logic
- Source: `huggingface_hub/cli/buckets.py` (679 lines) — CLI interface
- Source: `huggingface_hub/cli/_cp.py` — unified `hf cp` command
- 🔗 Hugging Face Hub docs: https://huggingface.co/docs/hub/storage-buckets
- 🔗 CLI reference: https://huggingface.co/docs/hub/en/cli/buckets

---

## 2026-07-24: hf-hub-python-api-v2 — Complete HfApi v1.x Reference (Topic #6 — Deep Dive v2)

### Summary
Comprehensive deep-dive into the **`huggingface_hub` Python library (v1.24.0)** — 161 public `HfApi` methods covering the complete Hugging Face Hub API surface. This is a v2 deep dive of Topic #6 (originally covered early in the learning cycle) and focuses on the **v1.x architecture** which introduced major new features: Buckets object storage, Webhooks API, Hub Jobs, Scheduled UV Jobs, Branches/Tags API, Discussion API, Access Request management, LFS management, Safetensors metadata inspection, Daily Papers API, and expanded Space management (25 methods).

### v1.x vs 0.x — What Changed

| Area | 0.x | 1.x |
|------|-----|-----|
| **API methods** | ~60 | **161** |
| **Object storage** | Git + LFS only | **Buckets** (`hf://buckets/...`) — Git-free, S3-compatible |
| **Jobs** | None | `run_job`, `run_uv_job`, `create_scheduled_job`, `create_scheduled_uv_job` |
| **Webhooks** | None | Full CRUD (7 methods) |
| **Collections** | Manual REST only | 8 methods |
| **Discussions** | None | 8 methods |
| **Branches/Tags** | `main` only | `create_branch`, `delete_branch`, `create_tag`, `delete_tag`, `list_repo_refs` |
| **Access requests** | None | 7 methods for gated repo management |
| **Space management** | Minimal (`space_info`) | 25 methods |
| **LFS management** | None | `list_lfs_files`, `permanently_delete_lfs_files`, `verify_repo_checksums` |
| **Safetensors metadata** | None | `get_safetensors_metadata`, `parse_safetensors_file_metadata` |
| **Large uploads** | `upload_folder` only | + `upload_large_folder` (parallel, resumable, progress reports) |
| **Repo refactoring** | None | `move_repo`, `duplicate_repo`, `super_squash_history` |

### Full Reference
See the main learnings file at `skills/references/hf-learnings.md` (appended under the same date/topic) for the complete comprehensive reference covering all 161 HfApi methods with code examples across all API categories: Repository CRUD, File Operations, Buckets, Spaces, Jobs, Webhooks, Collections, Discussions, Access Requests, Branches/Tags, LFS/Safetensors, Discovery, User/Org, and Zero-Cost recipes.

---

## 2026-07-24: hf-inference-client-chat-completion-source-deep-dive — InferenceClient Chat Completion Typed API Internals (Topic #100 — Deep Dive v3)

### Summary
Source-level analysis of `InferenceClient.chat_completion()` in `huggingface_hub` v1.24.0 — the typed type system, streaming SSE parsing, structured output handling, tool calling mechanics, and the provider routing architecture. This deep-dive goes beyond usage patterns into the actual implementation by examining the installed package source code.

### Source Files Examined
- `/huggingface_hub/inference/_client.py` (3394 lines) — `InferenceClient` class with all methods
- `/huggingface_hub/inference/_common.py` (432 lines) — streaming helpers and TGI fallback logic
- `/huggingface_hub/inference/_generated/types/chat_completion.py` (347 lines) — full type hierarchy auto-generated from `@huggingface/tasks` JSON schema specs
- `/huggingface_hub/inference/_providers/` — provider helper routing

### Chat Completion Type Hierarchy (Auto-Generated)

The entire type tree is code-generated from `@huggingface/tasks` specs via the script at `huggingface.js/packages/tasks/scripts/inference-codegen.ts`. Every type inherits from `BaseInferenceType` via `@dataclass_with_extra` (which allows extra fields without breaking — important for forward-compatibility with new server-side fields).

#### Response Format Union — `ChatCompletionInputGrammarType`

```python
ChatCompletionInputGrammarType = Union[
    ChatCompletionInputResponseFormatText,       # type: "text" (default)
    ChatCompletionInputResponseFormatJSONSchema, # type: "json_schema" + json_schema object
    ChatCompletionInputResponseFormatJSONObject, # type: "json_object"
]
```

**Key insight:** Despite the type hint, the method also accepts **plain dicts** — they pass through directly into the JSON payload. The `@dataclass_with_extra` base class silently converts typed objects to dicts during serialization. So both forms work:
```python
# Typed (type-safe, IDE support)
from huggingface_hub import ChatCompletionInputResponseFormatJSONSchema
response_format = ChatCompletionInputResponseFormatJSONSchema(
    json_schema=ChatCompletionInputJSONSchema(name="schema", schema={...})
)

# Dict (shorter, works in dynamic contexts)
response_format = {"type": "json_object"}
```

Internally, `provider_helper.prepare_request()` serializes the entire parameters dict to JSON. Typed objects are converted via `.to_dict()` (from `BaseInferenceType`).

#### `ChatCompletionInputJSONSchema` — The Schema Object

```python
class ChatCompletionInputJSONSchema(BaseInferenceType):
    name: str                      # Required — name of the response format
    description: str | None = None # Hint to model about what to generate
    schema: dict[str, object] | None = None  # JSON Schema object
    strict: bool | None = None     # Enable strict schema adherence (TGI >= 2.0+)
```

**`strict: True`** is the key differentiator — when set, TGI enforces exact schema compliance via grammar-guided generation (backed by `outlines` FSM engine under the hood). Without it, the model simply gets the schema as a system prompt hint.

#### Message Input Types — Multimodal Support

```python
# System/user/assistant messages
class ChatCompletionInputMessage(BaseInferenceType):
    role: str                     # "system" | "user" | "assistant" | "tool"
    content: list[ChatCompletionInputMessageChunk] | str | None = None
    name: str | None = None
    tool_calls: list[ChatCompletionInputToolCall] | None = None  # For assistant messages

# Multimodal content chunks
ChatCompletionInputMessageChunkType = Literal["text", "image_url"]

class ChatCompletionInputMessageChunk(BaseInferenceType):
    type: "ChatCompletionInputMessageChunkType"
    image_url: ChatCompletionInputURL | None = None  # For image_url type
    text: str | None = None                          # For text type

class ChatCompletionInputURL(BaseInferenceType):
    url: str  # Remote URL or base64 data URI
```

**Practical usage — multi-turn with tool calls:**
```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What's the weather in Paris?"},
    {"role": "assistant", "content": None, "tool_calls": [
        {"id": "call_1", "type": "function", "function": {
            "name": "get_weather", "parameters": {"location": "Paris"}
        }}
    ]},
    {"role": "tool", "content": "22°C, sunny", "tool_call_id": "call_1"},
]
```

Note: For tool messages, the dict format is preferred since `ChatCompletionInputMessage` in the typed version doesn't expose `tool_call_id` (that's only on the output side as `ChatCompletionOutputMessage.tool_call_id`). The dict bypasses the type constraint.

#### Tool Types

```python
class ChatCompletionInputFunctionDefinition(BaseInferenceType):
    name: str
    parameters: Any  # JSON Schema dict
    description: str | None = None

class ChatCompletionInputTool(BaseInferenceType):
    function: ChatCompletionInputFunctionDefinition
    type: str  # e.g. "function"

class ChatCompletionInputToolCall(BaseInferenceType):
    function: ChatCompletionInputFunctionDefinition
    id: str
    type: str

# Tool choice control
class ChatCompletionInputToolChoiceClass(BaseInferenceType):
    function: ChatCompletionInputFunctionName  # {"name": "specific_tool"}

ChatCompletionInputToolChoiceEnum = Literal["auto", "none", "required"]
```

**`tool_choice`** accepts:
- `"auto"` — model decides whether to call a tool
- `"none"` — no tool calling
- `"required"` — must call a tool
- `ChatCompletionInputToolChoiceClass(function=...)` — force a specific tool by name

**`tool_prompt`** — a string prepended before the tools definition. Some models perform better with a custom tool prompt.

#### Output Types — Non-Streaming

```python
class ChatCompletionOutput(BaseInferenceType):
    choices: list[ChatCompletionOutputComplete]
    created: int
    id: str
    model: str
    system_fingerprint: str
    usage: ChatCompletionOutputUsage

class ChatCompletionOutputComplete(BaseInferenceType):
    finish_reason: str            # "eos_token" | "stop" | "length" | "tool_calls"
    index: int
    message: ChatCompletionOutputMessage
    logprobs: ChatCompletionOutputLogprobs | None = None

class ChatCompletionOutputMessage(BaseInferenceType):
    role: str                     # "assistant"
    content: str | None = None
    reasoning: str | None = None  # 🔑 NEW in v1.24 — reasoning content (for R1, Gemini 2.5, etc.)
    tool_call_id: str | None = None
    tool_calls: list[ChatCompletionOutputToolCall] | None = None

class ChatCompletionOutputUsage(BaseInferenceType):
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int
```

**`reasoning` field (NEW):** Models like DeepSeek-R1 and Gemini 2.5 Pro return chain-of-thought reasoning tokens. These are separated from `content` in the `output.message.reasoning` field. This is distinct from the model's visible thinking — it's the reasoning/thinking content the model generates before its final answer.

**`finish_reason` values:**
| Value | Meaning |
|-------|---------|
| `"eos_token"` | Natural end (model generated end-of-sequence) |
| `"stop"` | Hit a stop sequence |
| `"length"` | Hit `max_tokens` limit |
| `"tool_calls"` | Model decided to call a tool (content is None, tool_calls is set) |

#### Output Types — Streaming

```python
class ChatCompletionStreamOutput(BaseInferenceType):
    choices: list[ChatCompletionStreamOutputChoice]
    created: int
    id: str
    model: str
    system_fingerprint: str
    usage: ChatCompletionStreamOutputUsage | None = None  # Only on final chunk when stream_options.include_usage=True

class ChatCompletionStreamOutputChoice(BaseInferenceType):
    delta: ChatCompletionStreamOutputDelta
    index: int
    finish_reason: str | None = None
    logprobs: ChatCompletionStreamOutputLogprobs | None = None

class ChatCompletionStreamOutputDelta(BaseInferenceType):
    role: str | None = None          # Only in first chunk
    content: str | None = None       # Token increment (joined across chunks)
    reasoning: str | None = None     # Reasoning token increment
    tool_call_id: str | None = None
    tool_calls: list[ChatCompletionStreamOutputDeltaToolCall] | None = None
```

**Streaming with `stream_options=ChatCompletionInputStreamOptions(include_usage=True)`:**
The final SSE chunk includes a `usage` field with token counts. This chunk has `choices[0].delta.content = None` and `delta.finish_reason = None` — detect it by checking `chunk.usage is not None`.

### Streaming SSE Parsing Mechanics

Source: `huggingface_hub/inference/_common.py` lines 307–350.

```python
def _stream_chat_completion_response(lines: Iterable[str]) -> Iterable[ChatCompletionStreamOutput]:
    for line in lines:
        try:
            output = _format_chat_completion_stream_output(line)
        except StopIteration:
            break  # [DONE] signal
        if output is not None:
            yield output

def _format_chat_completion_stream_output(line: str) -> ChatCompletionStreamOutput | None:
    if not line.startswith("data:"):
        return None  # Skip empty/heartbeat lines
    if line.strip() == "data: [DONE]":
        raise StopIteration("[DONE] signal received.")
    json_payload = json.loads(line.lstrip("data:").strip())
    if json_payload.get("error") is not None:
        raise _parse_text_generation_error(json_payload["error"], json_payload.get("error_type"))
    return ChatCompletionStreamOutput.parse_obj_as_instance(json_payload)
```

**Key details:**
1. The raw HTTP response is iterated line-by-line (SSE format)
2. Lines starting with `data:` are parsed as JSON
3. `data: [DONE]` terminates the stream via `StopIteration`
4. Server-side errors are surfaced as Python exceptions
5. Each chunk is deserialized into `ChatCompletionStreamOutput` via `.parse_obj_as_instance()` — this uses pydantic-like parsing from `BaseInferenceType`
6. Empty lines (keep-alive heartbeats) are silently skipped

### Request Flow

```
chat_completion(messages, response_format, tools, ...)
 │
 ├─ 1. Determine model_id_or_url (from self.model or arg)
 ├─ 2. Get provider_helper via get_provider_helper(provider, task="conversational", model)
 │     (Provider hierarchy: explicit → auto → HF inference API)
 ├─ 3. Build parameters dict:
 │     { "model", "messages", "response_format", "tools", "tool_choice",
 │       "temperature", "max_tokens", "stream", "stream_options",
 │       "frequency_penalty", "presence_penalty", "top_p", "stop",
 │       "seed", "logprobs", "top_logprobs", "logit_bias", "n",
 │       "tool_prompt", **(extra_body or {}) }
 ├─ 4. provider_helper.prepare_request(inputs=messages, parameters=parameters, ...)
 │     - Converts typed objects to dicts
 │     - Builds the HTTP request (URL, headers, JSON body)
 │     - Handles provider-specific transformations (e.g., Together, Novita, fal.ai)
 ├─ 5. self._inner_post(request_parameters, stream=stream)
 │     - Sends HTTP POST
 │     - If not stream: returns parsed JSON dict
 │     - If stream: returns iterable of raw lines
 ├─ 6. if stream → _stream_chat_completion_response(data) → Iterable[ChatCompletionStreamOutput]
 │    else       → ChatCompletionOutput.parse_obj_as_instance(data)
 └─ 7. Return result
```

### Provider Routing Architecture

```python
from huggingface_hub.inference._providers import get_provider_helper

provider_helper = get_provider_helper(
    provider,        # None | "auto" | "together" | "novita" | "fal-ai" | "replicate" | ...
    task="conversational",
    model=model_id_or_url,
)
```

The provider helper system:
1. If `provider` is explicitly set (e.g., `provider="together"`), that provider is used
2. If `provider="auto"` (default), the fastest available provider is selected based on throughput metrics
3. The `provider` parameter can also be a per-call override: `client.chat_completion(provider="novita", ...)`
4. Each provider has its own `TaskProviderHelper` that handles:
   - URL routing (different providers have different base URLs)
   - Header transformation (API keys, auth)
   - Body transformation (parameter name differences between providers)

### `extra_body` — Provider-Specific Passthrough

The `extra_body` dict is merged directly into the parameters payload (line 921 of `_client.py`):

```python
parameters = {
    ...
    **(extra_body or {}),
}
```

**Common uses:**
- Together AI: `{"safety_model": "Meta-Llama/Llama-Guard-7b"}`
- Together AI: `{"raw": True}` (return logprobs in raw format)
- Novita: `{"repetition_penalty": 1.1}` (not in the standard params list)
- Any provider-specific parameter that isn't in the standard params

### OpenAI-Compatible Alias

```python
# Both are equivalent — same method, same implementation
client.chat_completion(...)
client.chat.completions.create(...)
```

The `client.chat` property returns a `_ChatCompletionProxy` object whose `.completions.create` method is literally `lambda **kwargs: self.chat_completion(**kwargs)` (with model unpacking for positional compat). This means:
- All parameters, types, and behaviors are identical
- The OpenAI-compatible syntax doesn't lose any HF-specific features
- The `model` positional arg in OpenAI's `create(model, messages)` works identically

### `base_url` + `api_key` — Drop-in OpenAI Replacement

```python
client = InferenceClient(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ["HF_TOKEN"],
)
result = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1:fastest",
    messages=[{"role": "user", "content": "Hello"}],
    stream=True,
    max_tokens=1024,
)
```

When `base_url` is set, `InferenceClient` bypasses the provider helper entirely and sends requests directly to `base_url` with `api_key` as the bearer token. This is the **zero-migration path** from OpenAI SDK — switch the import, change nothing else.

### Key Source-Level Insights

1. **Dicts vs Typed objects:** Both work for all parameters (`messages`, `tools`, `response_format`, etc.). Dicts bypass type checking but are silently serialized the same way. The typed objects provide IDE autocomplete and are safer for complex schemas.

2. **`reasoning` field** is append-only in streaming: Every streaming chunk may have `delta.reasoning` tokens interleaved with `delta.content`. The model decides when to switch from reasoning to answering. To reconstruct the full reasoning, concatenate all `chunk.choices[0].delta.reasoning` across chunks.

3. **Tool calling in streaming:** When `finish_reason: "tool_calls"` appears, the final chunk has `delta.content = None` and `delta.tool_calls` populated. The function arguments come as a string (JSON) — parse them with `json.loads()`.

4. **No max_tokens default:** The server-side default is typically 100 for chat_completion — always set `max_tokens` explicitly unless you want the short default.

5. **`n > 1` is UNUSED** (per source docstring): The server ignores it for most providers. Only the first choice is meaningful.

6. **`logit_bias` is UNUSED:** Marked as "UNUSED" in the auto-generated spec. Use `extra_body` for provider-specific logit bias.

7. **`model` is both URL and payload:** The `model` parameter serves double duty — it's used to build the request URL (model ID → provider endpoint) AND passed as a payload value. `self.model` (from `InferenceClient(model=...)`) takes precedence for URL resolution; the explicit `model=` argument takes precedence for the payload.

### Resources
- Source: `/huggingface_hub/inference/_client.py` (3394 lines)
- Source: `/huggingface_hub/inference/_common.py` (432 lines)
- Source: `/huggingface_hub/inference/_generated/types/chat_completion.py` (347 lines)
- Source: `/huggingface_hub/inference/_providers/` — provider routing
- 🔗 HF Inference Guide: https://huggingface.co/docs/huggingface_hub/en/guides/inference
- 🔗 InferenceClient API: https://huggingface.co/docs/huggingface_hub/en/package_reference/inference_client
- 🔗 TGI documentation: https://huggingface.co/docs/text-generation-inference/en/index

---

## 2026-07-24: hf-hub-cache-deep-dive — Cache System Internals (Topic #116)

### Summary
Deep-dive into the Hugging Face Hub cache system — where downloaded models, datasets, and Spaces are stored locally. Covers the directory structure (`blobs/`, `snapshots/`, `refs/`, `trees/`), the `scan_cache_dir()` programmatic API, the `hf cache` CLI, Xet cache integration, and strategies for managing cache under zero-cost constraints.

### Cache Directory Layout

The cache root is determined by `HF_HUB_CACHE` (default: `~/.cache/huggingface/hub/`):

```
~/.cache/huggingface/hub/
├── blobs/            # Content-addressable blob storage (SHA-256 named)
├── snapshots/        # Point-in-time views of repo revisions
│   └── <repo_id>/    # e.g. models--meta-llama--Llama-2-7b/
│       └── <revision_hash>/
│           ├── config.json → ../../blobs/<sha256>
│           └── model.safetensors → ../../blobs/<sha256>
├── refs/             # Maps branch names to revision hashes
│   └── <repo_id>/
│       └── main       # Contains the commit OID
├── trees/            # Git tree objects (used for tree-based operations)
│   └── <sha256>/
├── .locks/           # File locks for thread-safe operations
├── .cache/           # Internal cache metadata
├── CACHEDIR.TAG      # Marks directory for backup exclusion
└── hf_xet/           # Xet cache (when hf_xet extension is installed)
    └── <xet_hash>/   # Chunk-level dedup cache
```

### Blob Storage vs. Symlinks

Each downloaded file is stored once in `blobs/`, named by its SHA-256 hash. Multiple revisions that share the same file content point to the same blob via symlinks. This means:
- **Space-efficient:** Identical files across revisions are stored once
- **Revision-safe:** Each revision is a complete symlink tree — no sharing corruption
- **Atomic:** A new download writes to a temp file, then atomically moves to blobs/

### scan_cache_dir() — Programmatic Inspection

```python
from huggingface_hub import scan_cache_dir

cache_info = scan_cache_dir()
# Returns a HfHubCacheInfo with three layers:

# 1. Repos (top-level)
for repo in cache_info.repos:
    print(repo.repo_id, repo.repo_type, repo.size_on_disk)

# 2. Revisions within a repo
for repo in cache_info.repos:
    for revision in repo.revisions:
        print(f"  {revision.commit_hash}: {revision.size_on_disk} bytes, "
              f"last_accessed={revision.last_accessed}")

# 3. Files within a revision
for repo in cache_info.repos:
    for revision in repo.revisions:
        for file in revision.files:
            print(f"    {file.file_name}: {file.size_on_disk} bytes, "
                  f"blob_size={file.blob_size}, ref_pattern={file.ref_pattern}")
```

### Cache Cleanup Strategies

```python
from huggingface_hub import scan_cache_dir, DeleteCacheStrategy

cache_info = scan_cache_dir()

# Strategy 1: Delete specific revisions
strategy = DeleteCacheStrategy()
strategy.add_revision(revision)

# Strategy 2: Delete by date (e.g., not accessed in 30 days)
import datetime
cutoff = datetime.datetime.now() - datetime.timedelta(days=30)
for repo in cache_info.repos:
    for revision in repo.revisions:
        if revision.last_accessed < cutoff:
            strategy.add_revision(revision)

# Strategy 3: Delete everything except latest for each repo
for repo in cache_info.repos:
    revisions = sorted(repo.revisions, key=lambda r: r.last_accessed, reverse=True)
    for revision in revisions[1:]:  # Keep latest
        strategy.add_revision(revision)

# Execute deletion
for warning in strategy.execute():
    print(f"Deleted: {warning}")  # Each warning is a (path, error_or_message) tuple
```

### CLI Cache Management

```bash
# List cache contents
hf cache list

# Prune old revisions
hf cache prune             # Remove all but latest revision per repo
hf cache prune --days=30   # Remove revisions not accessed in 30 days

# Verify blob checksums
hf cache verify

# Cache environment
echo $HF_HUB_CACHE          # Default: ~/.cache/huggingface/hub
echo $HF_HOME               # Default: ~/.cache/huggingface
```

### Cache-Only Mode

```python
from huggingface_hub import hf_hub_download, try_to_load_from_cache

# Try loading from cache without network
cached_path = try_to_load_from_cache(
    repo_id="meta-llama/Llama-2-7b",
    filename="config.json",
)
if cached_path:
    print(f"Loaded from cache: {cached_path}")
else:
    print("File not cached, use hf_hub_download with local_files_only=True")
    cached_path = hf_hub_download(
        "meta-llama/Llama-2-7b",
        "config.json",
        local_files_only=True,  # Raises if not cached
    )
```

### Xet Cache vs. Blob Cache

| Feature | Blob Cache | Xet Cache |
|---------|-----------|-----------|
| **Granularity** | Entire files (SHA-256) | 64KB chunks |
| **Dedup scope** | Across revisions of same file | Across files, repos, and revisions |
| **Download speedup** | Cached files load instantly | Chunks shared across variants |
| **Upload speedup** | No | Yes (shard cache) |
| **Disk overhead** | Low (symlinks are cheap) | Medium (chunk index) |
| **Enabled by default** | Yes | No (unless `hf_xet` installed) |
| **Best for** | Model weight reuse | Iterative training with similar data |

### Resources
- Manage cache guide: https://huggingface.co/docs/huggingface_hub/en/guides/manage-cache
- Cache-system reference: https://huggingface.co/docs/huggingface_hub/en/package_reference/cache
- Environment variables: https://huggingface.co/docs/huggingface_hub/en/package_reference/environment_variables
- Xet guide: https://huggingface.co/docs/hub/xet/index
- `scan_cache_dir` docs: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/cache#huggingface_hub.scan_cache_dir
- `hf cache` CLI: https://huggingface.co/docs/huggingface_hub/main/en/guides/cli#hf-cache
| CACHEDIR.TAG standard: https://bford.info/cachedir/
