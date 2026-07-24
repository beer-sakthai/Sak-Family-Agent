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
|| CACHEDIR.TAG standard: https://bford.info/cachedir/
|

---

## 2026-07-24: hf-hub-fsspec — HfFileSystem Deep Dive (Topic #59 — Deep Dive v2)

**Author:** SakThai
**License:** MIT

### Summary
Comprehensive deep-dive into `HfFileSystem` — the `fsspec`-compatible filesystem interface to the Hugging Face Hub. Covers the full architecture (path resolution, instance caching, directory caching), every method with source-verified signatures and behavior, the `hf://` URL scheme for all 4 resource types (models, datasets, Spaces, buckets), integration patterns with Pandas/DuckDB/Zarr/Dask/Polars, performance tradeoffs vs `HfApi`, and practical zero-cost workflows. Source: `huggingface_hub/hf_file_system.py` (main branch v1.24.0-dev), official HF docs.

### Architecture Overview

`HfFileSystem` extends `fsspec.AbstractFileSystem` with a custom metaclass `_Cached` for instance caching. It wraps `HfApi` internally and provides familiar filesystem operations (`ls`, `glob`, `open`, `cp`, `mv`, `rm`, `walk`, `find`, `info`, `exists`, `isdir`, `isfile`, `put`, `get`).

**Key classes:**
- **`HfFileSystem`** — The main filesystem class. Protocol: `"hf"`. Identified by `endpoint`, `token`, `block_size`, `expand_info`.
- **`HfFileSystemResolvedRepositoryPath`** — Resolved path: `repo_type`, `repo_id`, `revision`, `path_in_repo`, `_raw_revision`.
- **`HfFileSystemResolvedBucketPath`** — Resolved bucket path: `bucket_id`, `path`.
- **`HfFileSystemFile`** / **`HfFileSystemStreamFile`** — File-like objects for read/write.

### URL Scheme — `hf://` Protocol

Four URL patterns, all valid with or without the `hf://` prefix when using `HfFileSystem` directly:

| Resource | Scheme | Example |
|----------|--------|---------|
| **Models** | `hf://<repo-id>[@<revision>]/<path>` | `hf://beer-sakthai/my-model/config.json` |
| **Datasets** | `hf://datasets/<repo-id>[@<revision>]/<path>` | `hf://datasets/squad/data.json` |
| **Spaces** | `hf://spaces/<repo-id>[@<revision>]/<path>` | `hf://spaces/gradio/hello-world/app.py` |
| **Buckets** | `hf://buckets/<bucket-id>/<path>` | `hf://buckets/my-org/my-bucket/data.parquet` |

**Key rules:**
- Models have NO prefix (bare repo_id); datasets and Spaces use explicit prefixes
- Revision is optional — defaults to `"main"` (or bucket's latest)
- The `@revision` suffix can be a branch name, tag, or commit hash
- Buckets do NOT support revision at all
- Paths are case-sensitive on the Hub

### Instance Caching (`_Cached` Metaclass)

`HfFileSystem` uses a custom metaclass `_Cached` that overrides fsspec's default caching:

- **Tokenization**: `_tokenize()` produces a deterministic MD5 hash from `(cls, thread_id, args, kwargs)`. Unlike standard fsspec, PID is NOT included — instances are shared across threads in the same process.
- **Main thread reuse**: New instances in child threads copy cache state from the main thread instance if one exists.
- **Instance sharing**: Two `HfFileSystem()` calls with the same parameters share the same underlying instance (including its internal caches).
- **Skip cache**: Pass `skip_instance_cache=True` to force a fresh instance.
- **Clear cache**: `cls.clear_instance_cache()` classmethod to wipe all cached instances.

**Important**: The metaclass keeps a strong reference to each cached instance, preventing garbage collection. Call `clear_instance_cache()` explicitly when done.

### Internal Caches (3 Levels)

1. **`_repo_and_revision_exists_cache`** — Maps `(repo_type, repo_id, revision)` → `(bool, Exception)`. Validates repo and revision existence. Results cached bidirectionally: checking `(type, id, "v1.0")` also populates `(type, id, None)`.
2. **`_bucket_exists_cache`** — Maps `bucket_id` → `(bool, Exception)`. Simpler than repos — no revision dimension.
3. **`dircache`** — Maps parent directory paths to lists of file info dicts (`ls` results). Standard fsspec directory listing cache.

**Cache invalidation**: `invalidate_cache(path=None)` clears all caches; `invalidate_cache(path="specific/path")` clears only that path's entries and its ancestors.

### Complete Method Reference (Source-Verified)

All methods from `hf_file_system.py`:

| Method | Signature Highlights | Description | Better Alternative |
|--------|---------------------|-------------|-------------------|
| `resolve_path(path, revision=None)` | Returns `HfFileSystemResolvedRepositoryPath` or `HfFileSystemResolvedBucketPath` | Parse an `hf://` path into structured components | — |
| `ls(path, detail=True, refresh=False, revision=None)` | Returns `list[str]` or `list[dict]` | List directory contents | `HfApi.list_repo_tree()` |
| `find(path, maxdepth=None, withdirs=False, detail=False, refresh=False, revision=None)` | Returns paths recursively | Like `ls` but recursive — no subdirectory grouping | — |
| `walk(path)` | Returns `Iterator[(path, dirs, files)]` | os.walk-style tree traversal | — |
| `glob(path, maxdepth=None)` | Returns `list[str]` | Glob matching (`**/*.csv`) | — |
| `exists(path, revision=None)` | Returns `bool` | Check if path exists | `HfApi.file_exists()` |
| `isfile(path, revision=None)` | Returns `bool` | Check if path is a file | — |
| `isdir(path, revision=None)` | Returns `bool` | Check if path is a directory | — |
| `info(path, refresh=False, revision=None)` | Returns `dict` (type, size, commit info) | Get file/directory metadata | `HfApi.get_paths_info()` |
| `modified(path, revision=None)` | Returns `datetime` | Get last modified time | — |
| `open(path, mode="rb", block_size=None, revision=None, **kwargs)` | Returns `HfFileSystemFile` or `HfFileSystemStreamFile` | Open a file for reading/writing | `HfApi.upload_file()` / `hf_hub_download()` |
| `read_text(path, revision=None)` | Returns `str` | Read entire file as string | — |
| `read_bytes(path, revision=None)` | Returns `bytes` | Read entire file as bytes | — |
| `cp(path1, path2, revision=None)` | None | Copy file within/between repos | `HfApi.upload_file()` |
| `mv(path1, path2, revision=None)` | None | Move/rename file within/between repos | — |
| `rm(path, recursive=False, maxdepth=None, revision=None)` | None | Delete file(s) | `HfApi.delete_file()` |
| `put(lpath, rpath, callback=None, revision=None, **kwargs)` | None | Upload local file(s) to Hub | `HfApi.upload_file()` |
| `get(rpath, lpath, callback=None, outfile=None, **kwargs)` | None | Download remote file(s) | `HfApi.hf_hub_download()` |
| `url(path)` | Returns `str` (HTTP URL) | Get direct HTTP URL for a path | — |
| `invalidate_cache(path=None)` | None | Clear dircache + existence caches | — |
| `copy(path1, path2, revision=None)` | None | Alias for `cp` | — |
| `du(path, revision=None)` | Returns `int` | Disk usage (total size) | — |
| `disk_usage(path, revision=None)` | Returns `int` | Alias for `du` | — |

**Not implemented**: `quota()`, `disk_utilization()`, `setxattrs()` — all raise `NotImplementedError`.

### Path Resolution Internals

`resolve_path()` is the heart of `HfFileSystem`. It:

1. Strips the `hf://` protocol prefix via `_strip_protocol()`
2. Rejects empty paths (listing all repos not supported)
3. Rejects single-segment paths (must be `namespace/name` format)
4. Delegates to `parse_hf_uri()` to parse the HF URI into `(type, id, revision, path_in_repo)`
5. For **buckets** — validates bucket existence via `_bucket_exists()` → `bucket_info()`
6. For **repos** — validates repo + revision existence via `_repo_and_revision_exist()` → `repo_info()`
7. Handles revision conflicts (path vs explicit arg) — raises `ValueError` on mismatch
8. Special-cases special refs (`refs/pr/123`) — splits on `@` manually to avoid greedy matching by `parse_hf_uri()`
9. Preserves raw revision string for `unresolve()` fidelity (quoted refs stay quoted)

### Read/Write Operations

#### Reading (`_open` with mode `"rb"` or `"r"`)

Two file-like classes are used depending on block_size:
- **`HfFileSystemFile`** — For non-streaming reads (block_size ≥ 0). Fetches the full file content lazily on first read, caches it in `_cache`. Supports `seek()`.
- **`HfFileSystemStreamFile`** — For streaming reads (block_size is None). Downloads chunks on demand. No `seek()` support.

**Behaviour:**
- Default mode is `"rb"` (binary) — unlike Python's `"rt"` default. Always specify `"r"` for text.
- `read_text()` / `read_bytes()` are convenience wrappers that open, read, and close.

#### Writing (`_open` with mode `"wb"` or `"w"`)

Uses `HfFileSystemFile` in write mode:
- Writes are buffered locally, then committed on `close()` as a single `CommitOperationAdd`
- The temp file is created via `tempfile.mkstemp()` in a thread-safe manner
- Appending (`"a"`, `"ab"`) raises `NotImplementedError`

### Integration Patterns

#### Pandas
```python
import pandas as pd

df = pd.read_csv("hf://datasets/my-username/my-dataset/train.csv")
df = pd.read_csv("hf://buckets/my-username/my-bucket/train.parquet")

df.to_csv("hf://datasets/my-username/my-dataset/processed.csv")
```

`HfFileSystem` is auto-registered as the `hf://` filesystem, so Pandas uses it transparently.

#### DuckDB
```python
from huggingface_hub import HfFileSystem
import duckdb

fs = HfFileSystem()
duckdb.register_filesystem(fs)

result = duckdb.query(
    "SELECT * FROM 'hf://datasets/my-username/my-dataset/data.parquet' LIMIT 10"
).df()
```

#### Zarr (Array Storage)
```python
import zarr
import numpy as np

embeddings = np.random.randn(50000, 1000).astype("float32")
with zarr.open_group("hf://my-username/my-model/embeddings", mode="w") as root:
    root.zeros("experiment_0", shape=(50000, 1000), chunks=(10000, 1000), dtype='f4')[:] = embeddings

with zarr.open_group("hf://my-username/my-model/embeddings", mode="r") as root:
    first_row = root["embeddings/experiment_0"][0]
```

#### Dask & Polars
```python
import dask.dataframe as dd
df = dd.read_csv("hf://datasets/.../*.csv")

import polars as pl
df = pl.read_parquet("hf://buckets/my-org/my-bucket/data/*.parquet")
```

### Performance Considerations

Official HF docs **strongly recommend** using `HfApi` methods over `HfFileSystem` when performance matters:

| Operation | Prefer | Reason |
|-----------|--------|--------|
| Upload file | `HfApi.upload_file()` | Direct API call, no fsspec overhead |
| Download file | `HfApi.hf_hub_download()` | Proper caching, etag-based, resume support |
| Delete file | `HfApi.delete_file()` | Single API call vs file-level ops |
| List directory | `HfApi.list_repo_tree()` | Returns structured data, more efficient |
| File exists | `HfApi.file_exists()` | Direct HEAD request |
| File info | `HfApi.get_paths_info()` / `HfApi.repo_info()` | More detailed + cached |

**When to use HfFileSystem anyway:**
- Integrating with libraries that require `fsspec` (Pandas, DuckDB, Zarr, Dask, Polars)
- Quick ad-hoc browsing of Hub repos from a Python script
- Globbing and pattern matching across repo directories
- When the overhead doesn't matter (small files, infrequent ops)

### Error Handling

`HfFileSystem` wraps Hub errors into standard filesystem errors:

| Hub Error | Filesystem Behaviour |
|-----------|---------------------|
| `RepositoryNotFoundError` | `FileNotFoundError` with descriptive message |
| `RevisionNotFoundError` | `FileNotFoundError` ("No such revision") |
| `EntryNotFoundError` | `FileNotFoundError` ("No such file") |
| `BucketNotFoundError` | `FileNotFoundError` ("No such bucket") |
| `HFValidationError` | `FileNotFoundError` ("Invalid repo id") |

### Limitations & Edge Cases

1. **Appending not supported** — `"a"` / `"ab"` modes raise `NotImplementedError`
2. **Single-segment IDs not supported** — Must use `namespace/repo` format (no bare `gpt2`)
3. **Listing all repos** — `hffs.ls("")` raises `NotImplementedError`
4. **Cache invalidation** — `dircache` entries persist across operations unless explicitly invalidated
5. **Buckets don't support revision** — revision parameter is silently ignored for bucket paths
6. **Thread safety** — Instance-level caches may race in concurrent access
7. **Large files** — Streaming reads with default block_size avoid loading entire files into memory, but `read_bytes()` loads it all
8. **`quota()` / `disk_utilization()`** — Not implemented (raises error)
9. **`setxattrs()`** — Not implemented

### Global Module-Level Convenience

```python
from huggingface_hub import hffs
```

`hffs` is a module-level singleton `HfFileSystem()` at `huggingface_hub/__init__.py`. It uses the default endpoint and cached token. For custom config, instantiate `HfFileSystem()` directly:

```python
from huggingface_hub import HfFileSystem
fs = HfFileSystem(endpoint="https://huggingface.co", token="hf_...")
```

### Resources
- Guide: https://huggingface.co/docs/huggingface_hub/en/guides/hf_file_system
- Package reference: https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_file_system
- Source: `huggingface_hub/hf_file_system.py` (main branch)
- fsspec docs: https://filesystem-spec.readthedocs.io/en/latest/
- Pandas remote IO: https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#reading-writing-remote-files
- DuckDB fsspec: https://duckdb.org/docs/guides/python/filesystems
- Zarr fsspec: https://zarr.readthedocs.io/en/stable/tutorial.html#io-with-fsspec

---

## 2026-07-24: hf-hub-upload-strategies-deep-dive — Complete Upload Reference (Topic #35 Deep-Dive)

### Summary
Deep-dive into all upload strategies available in `huggingface_hub` for pushing content to the Hugging Face Hub. Covers the full API surface (`upload_file`, `upload_folder`, `create_commit`, `upload_large_folder`), the Xet-powered streamed pipeline, LFS vs regular file handling, multi-commit large-folder uploads, resumability, patterns, limitations, and best practices for zero-cost model/dataset publishing. Source code: `huggingface_hub/hf_api.py`, `huggingface_hub/_commit_api.py`, `huggingface_hub/_upload_pipeline.py` on GitHub.

### Key Concepts

**Three core upload methods:**
1. **`upload_file`** — single file upload via HTTP POST (up to 50 GB). No git/lfs required. Wraps `create_commit` with one `CommitOperationAdd`.
2. **`upload_folder`** — upload an entire local folder. With `hf_xet` installed (default): multi-commit streamed pipeline with adaptive batching, resumability, deduplication. Without: single `create_commit` (legacy, warns >30 files).
3. **`upload_large_folder`** — DEPRECATED. Multi-worker hash+preupload+commit pipeline. Replaced by `upload_folder` with Xet.

**Low-level API:**
- **`create_commit`** — the foundation. Accepts an iterable of `CommitOperation` objects. Supports up to 25k LFS files and 1 GB regular-file payload per commit.

### CommitOperation Types

| Operation | Purpose | Key Fields |
|-----------|---------|-----------|
| `CommitOperationAdd(path_or_fileobj, path_in_repo)` | Upload a file (local path, bytes, or IO stream) | `path_or_fileobj` (str/Path/bytes/BinaryIO), `path_in_repo` (str) |
| `CommitOperationDelete(path_in_repo, is_folder)` | Delete a file or folder | `path_in_repo` (str), `is_folder` (bool or "auto") |
| `CommitOperationCopy(path_in_repo, src_path_in_repo, src_repo_id, src_repo_type)` | Copy a file within/across repos | `path_in_repo`, `src_path_in_repo`, optional `src_repo_id`/`src_repo_type` for cross-repo |

### Upload Modes

Files are classified into two modes when uploaded:

**Regular files** — small files stored directly as git blobs. Base64-encoded in the commit payload. Budget: ~100 MB per commit.

**LFS files** — large files tracked by Git LFS. Two-step process:
1. **Pre-upload**: hash the file, register with LFS batch endpoint, upload chunks to blob storage
2. **Commit**: reference the LFS pointer in the git commit

The Hub automatically determines which mode applies:
- Files matching extensions in `.gitattributes` → LFS
- Files above a size threshold → automatically LFS-tracked
- Small files → regular git blobs

### Xet-Powered Streamed Upload (Default)

When `hf_xet` is installed (now default with `huggingface_hub`), `upload_folder` uses a **streamed multi-commit pipeline**:

**Architecture:**
- **Coordinator** (caller thread): walks files, asks Hub (256 at a time) to classify them (regular/xet/ignored). Xet files are registered into a `XetSession` which chunks, deduplicates, and uploads them in background. No Python-side sha256 — `hf_xet` computes it during chunking (single read pass).
- **Committer** (background thread): joins xet uploads, drops unchanged files (compares remote OIDs), creates git commits for each batch. Runs concurrently with coordinator.

**Key features:**
- **Adaptive batching**: starts at 250 files/commit, scales up (to 1000) for fast first commits, scales down on failures. Forces a commit every 5 min max.
- **Resumability**: re-running the same call skips already-committed files (no-op by remote OID comparison) and deduplicates already-uploaded Xet chunks (~0 bytes transferred).
- **No single-read-pass penalty**: files are hashed during the chunking process, not pre-hashed.
- **Automatic `.git/` folder exclusion** via `DEFAULT_IGNORE_PATTERNS`.

### Detailed Method Reference

#### `upload_file(path_or_fileobj, path_in_repo, repo_id, ...)`

```python
from huggingface_hub import upload_file

# From a file path
upload_file(
    path_or_fileobj="./local/weights.bin",
    path_in_repo="checkpoints/weights.bin",
    repo_id="username/my-model",
)

# From bytes
upload_file(
    path_or_fileobj=b"model data here",
    path_in_repo="model.bin",
    repo_id="username/my-model",
)
```

**Important params:** `repo_type`, `revision`, `create_pr`, `token`, `commit_message`, `parent_commit`.

**Limits:** Up to 50 GB per file. Assumes repo exists (404 → create it first with `create_repo`).

#### `upload_folder(folder_path, repo_id, ...)`

```python
from huggingface_hub import upload_folder

# Basic upload — entire folder
upload_folder(
    folder_path="./my-model-output",
    repo_id="username/my-model",
)

# With patterns and deletion
upload_folder(
    folder_path="./checkpoints",
    path_in_repo="experiment/checkpoints",
    repo_id="username/my-dataset",
    repo_type="dataset",
    ignore_patterns="**/logs/*.txt",        # skip local files
    delete_patterns="**/logs/*.txt",         # delete matching remote files
    create_pr=True,                          # open a PR instead of direct push
)
```

**Key params:** `path_in_repo`, `allow_patterns`, `ignore_patterns`, `delete_patterns`, `create_pr`, `revision`, `parent_commit`.

**Note:** When `create_pr=True`, PR is always against default branch. Cannot combine with `revision`. For resuming an interrupted upload into an existing PR, use `revision="refs/pr/N"` instead.

#### `create_commit(repo_id, operations, commit_message, ...)`

```python
from huggingface_hub import create_commit, CommitOperationAdd, CommitOperationDelete

operations = [
    CommitOperationAdd(path_or_fileobj="./new_weights.bin", path_in_repo="model.bin"),
    CommitOperationDelete(path_in_repo="old_weights.bin"),
]
create_commit(
    repo_id="username/my-model",
    operations=operations,
    commit_message="Update weights and cleanup",
    num_threads=5,  # parallel upload threads
)
```

**Key params:** `num_threads` (default 5), `create_pr`, `parent_commit`, `run_as_future`.

**Limits:** 25k LFS files, 1 GB regular-file payload per commit.

### Cross-Repository Copy

`CommitOperationCopy` enables server-side LFS object duplication:

```python
CommitOperationCopy(
    path_in_repo="new/path.bin",              # destination
    src_path_in_repo="original/path.bin",     # source
    src_repo_id="source-user/source-repo",     # different repo
    src_repo_type="model",
)
```

LFS objects are duplicated server-side. Regular files are downloaded and re-uploaded. Works within the same HF instance.

### Best Practices for Zero-Cost Uploads

1. **Use Xet uploads** — `pip install hf_xet` is now bundled by default. Gives you resumable, multi-commit uploads for free.
2. **Prefer `upload_folder` over `upload_file`** — unless you're uploading a single file. The Xet pipeline is more robust.
3. **Use `delete_patterns` instead of separate delete commits** — `upload_folder` optimizes by skip-deleting files that are being overwritten.
4. **Creating a new repo?** — call `create_repo()` first, then upload. `upload_*` methods assume the repo exists.
5. **Large model uploads** — organize checkpoints in folders, use `upload_folder` with Xet. It auto-batches into 250–1000 file commits.
6. **Atomicity with `parent_commit`** — pass a specific OID to ensure the repo hasn't changed since you last fetched it. Especially useful for workflows with concurrent updates.
7. **PR-based uploads for review** — use `create_pr=True`. Each call creates a new PR unless you target a specific PR branch with `revision="refs/pr/N"`.
8. **Avoid `upload_large_folder`** — deprecated. Uses old multi-worker approach without Xet deduplication.
9. **File size awareness** — single files up to 50 GB via `upload_file`. Above that, split into chunks and upload separately.
10. **Progress display** — Xet pipeline shows live progress bars on TTY and periodic summary logs on non-TTY (every 30 seconds).

### Error Handling Patterns

```python
from huggingface_hub import HfApi, RepositoryNotFoundError

api = HfApi()
try:
    api.upload_file(
        path_or_fileobj=b"data",
        path_in_repo="file.txt",
        repo_id="user/repo",
    )
except RepositoryNotFoundError:
    api.create_repo(repo_id="user/repo")
    api.upload_file(...)  # retry
except Exception as e:
    # Handle HTTP errors: 400 (bad request), 403 (gated/unauthorized), 413 (payload too large), 503 (overloaded)
    print(f"Upload failed: {e}")
```

## 2026-07-24: hf-hub-xet-streamed-upload-pipeline-deep-dive — Xet Streamed Multi-Commit Upload Pipeline (Topic #135)

### Summary
Comprehensive deep-dive into the Xet-backed streamed multi-commit upload pipeline introduced in `huggingface_hub` 1.24.0. See the full entry in `skills/references/hf-learnings.md` (main file). This is a concise reference for the huggingface-hub skill.

### Quick Architecture
Two-thread pipeline: **Coordinator** scans files 256-at-a-time via `_fetch_upload_modes()`, opens Xet upload-commits, starts uploads in background. **Committer** finalizes Xet uploads, drops unchanged files (dedup), creates git commits with adaptive batch sizes. Backpressure via `batch_queue(maxsize=1)`.

### Key Constants (from `_upload_pipeline.py`)
| Constant | Value | Purpose |
|---|---|---|
| `PREUPLOAD_BATCH_SIZE` | 256 | Files per preupload API call |
| `COMMIT_SIZE_SCALE` | [20,50,75,100,125,200,250,400,600,1000] | Adaptive batch sizes |
| `INITIAL_COMMIT_SIZE_INDEX` | 6 | Start at 256 files/commit |
| `TARGET_COMMIT_DURATION` | 40.0s | Scale up if commits faster |
| `MAX_COMMIT_INTERVAL` | 300.0s | Force commit if idle |
| `REGULAR_CONTENT_BYTES_BUDGET` | 100 MB | Regular file payload limit |

### Resume Pattern
Re-run `upload_folder()` with same args. Already-committed files are detected via `_remote_oid == _local_oid` and dropped. Partially-uploaded Xet chunks are deduplicated by backend. Resume into existing PR: use `revision="refs/pr/N"` instead of `create_pr=True`.

### Resources
- Full deep-dive: `skills/references/hf-learnings.md` (Topic #135)
- huggingface_hub source: https://github.com/huggingface/huggingface_hub
- `hf_api.py` (upload methods): https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/hf_api.py
- `_upload_pipeline.py` (Xet pipeline): https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/_upload_pipeline.py
- Xet docs: https://huggingface.co/docs/hub/en/xet/index
- `upload_folder` reference: https://huggingface.co/docs/huggingface_hub/package_reference/hf_api#huggingface_hub.HfApi.upload_folder

## 2026-07-25: hf-hub-repo-lifecycle-management — Repository CRUD & Settings API (Topic #136)

### Summary
Comprehensive deep-dive into the Hugging Face Hub repository lifecycle management API — creating, reading, updating, deleting, moving, duplicating, and squashing repositories via `huggingface_hub`'s `HfApi` class and the underlying REST API. Covers all six core methods plus settings management, with full parameter documentation, error handling, data models, free-tier constraints, and practical patterns for automated repo management. Source: `huggingface_hub/hf_api.py` on GitHub (v1.24.0+).

### Core Architecture

```
Repository Lifecycle
┌────────────────────────────────────────────────────────┐
│                    HfApi Repo Methods                   │
├──────────────┬──────────────────┬──────────────────────┤
│  Creation     │  Reading         │  Modification        │
├──────────────┼──────────────────┼──────────────────────┤
│ create_repo() │ repo_info()      │ update_repo_settings │
│ duplicate_    │ repo_exists()    │ move_repo()          │
│  repo()      │                  │ super_squash_history │
│              │                  │ delete_repo()        │
└──────────────┴──────────────────┴──────────────────────┘
```

All methods are on a single `HfApi()` instance. Authentication via `HF_TOKEN` env var, cached token file, or explicit `token=` parameter. Default `repo_type` is `"model"`.

---

### 1. `create_repo()` — Repository Creation

The universal creation method for all three repo types (models, datasets, Spaces). There is **no** separate `create_model()` / `create_dataset()` / `create_space()` — everything flows through this single method.

```python
from huggingface_hub import HfApi, SpaceHardware, SpaceStorage, Volume

api = HfApi()

# Minimal model repo
url = api.create_repo("user/my-model")

# Private dataset repo
url = api.create_repo("user/my-dataset", repo_type="dataset", private=True, exist_ok=True)

# Gradio Space with hardware and volumes
url = api.create_repo(
    "user/my-space",
    repo_type="space",
    space_sdk="gradio",
    space_hardware=SpaceHardware.CPU_BASIC,
    space_volumes=[
        Volume(type="bucket", source="my-bucket", mount_path="/data")
    ],
)
```

#### All Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `repo_id` | `str` | required | `namespace/name` or just `name` (uses your account) |
| `token` | `str\|bool\|None` | cached | Auth token |
| `private` | `bool\|None` | `None` | `True` = private. Cannot use with `visibility`. |
| `visibility` | `Literal["public","private","protected"]\|None` | `None` | Explicit visibility (`"protected"` is Space-only) |
| `repo_type` | `str\|None` | `"model"` | `"model"`, `"dataset"`, `"space"` |
| `exist_ok` | `bool` | `False` | If `True`, no error if repo already exists |
| `resource_group_id` | `str\|None` | `None` | Enterprise Hub resource group |
| `region` | `Literal["us","eu"]\|None` | `None` | Storage region (requires Team plan+) |
| `space_sdk` | `str\|None` | `None` | Space SDK: `"gradio"`, `"streamlit"`, `"docker"`, `"static"` |
| `space_hardware` | `SpaceHardware\|None` | `CPU_BASIC` | Space hardware tier |
| `space_storage` | `SpaceStorage\|None` | `None` | **Deprecated** — use volumes |
| `space_sleep_time` | `int\|None` | `None` | Inactivity timeout (seconds). `-1` = never sleep (paid only) |
| `space_secrets` | `list[dict]\|None` | `None` | `[{"key": "K", "value": "V", "description": "..."}]` |
| `space_variables` | `list[dict]\|None` | `None` | Public env vars (same format as secrets) |
| `space_volumes` | `list[Volume]\|None` | `None` | Mounted volumes at creation |
| `space_template` | `str\|None` | `None` | Seed from official Space template |

#### Returns: `RepoUrl`

`RepoUrl` is a subclass of `str` containing the repo URL, plus:
- `endpoint` — the HF endpoint URL
- `repo_type` — model/dataset/space
- `repo_id` — full `namespace/name`

```python
url = api.create_repo("user/my-model")
str(url)              # "https://huggingface.co/user/my-model"
url.endpoint          # "https://huggingface.co"
url.repo_type         # "model"
url.repo_id           # "user/my-model"
```

#### Error Handling

| Error | Status | When |
|-------|--------|------|
| `HfHubHTTPError` (409) + `exist_ok=True` | Silently returns existing repo URL | Repo already exists |
| `HfHubHTTPError` (409) + `exist_ok=False` | Raises `HfHubHTTPError` | Repo already exists |
| `HfHubHTTPError` (401) | Insufficient token scope | JWT token without create scope |
| `HfHubHTTPError` (402) | Payment required | Gradio/Docker Space for free user (Spaces quota) |
| `HfHubHTTPError` (403) | No write permission | Can't create in that namespace |
| `ValueError` | Invalid repo type | Not in `REPO_TYPES_WITH_KERNEL` |
| `ValueError` | Missing `space_sdk` | `repo_type="space"` without specifying SDK |
| `ValueError` | Invalid Space SDK | Not in `SPACES_SDK_TYPES` |

**Race condition retry:** If the Hub returns 409 with "another conflicting operation is in progress", `create_repo()` automatically retries (infinite loop with no backoff — server-side concurrency guard).

#### `exist_ok` Behavior (Deep Dive)

When `exist_ok=True` and the repo already exists, `create_repo()` accepts:
- **409 Conflict** — directly returns without raising (fast path, most common)
- **401 / 402 / 403** — Falls back to calling `repo_info()` to verify existence; if the repo exists, returns its URL; if not, re-raises the original error

This means `exist_ok=True` works even when the token lacks create permissions, as long as the repo already exists and you have read access.

#### Space Template Support

Space templates allow seeding from official templates:

```python
# List available templates
templates = api.list_space_templates()

# Create Space from template (by name or repo_id)
url = api.create_repo(
    "user/jupyter-space",
    repo_type="space",
    space_template="JupyterLab",  # or "SpacesExamples/jupyterlab"
)
```

Template resolution logic:
1. First matches against `template.repo_id` (exact)
2. Then matches against `template.name` (case-insensitive)
3. If the template recommends private visibility and user hasn't set visibility, defaults to private
4. `space_sdk` is automatically set from the template (cannot be overridden)

#### Free Tier Constraints

| Constraint | Detail |
|------------|--------|
| **Cost** | Free — all `create_repo()` operations are free |
| **Space creation limit** | Free tier can create unlimited public Spaces, but paid hardware requires PRO |
| **Space SDUs** | Free CPU-Basic Spaces get 2 SDU (shared CPU, 16GB RAM, 50GB ephemeral disk) |
| **Private repos** | Free tier supports unlimited private repos (model, dataset, space) |
| **Storage bucket repos** | Free tier gets 50GB per bucket in us region |
| **`region=` parameter** | Requires Team plan — free accounts get default (us) |
| **`resource_group_id`** | Enterprise Hub only |

---

### 2. `delete_repo()` — Repository Deletion

**IRREVERSIBLE.** Deletes the repo and all its contents from the Hub. No trash/recycle bin.

```python
# Minimal delete
api.delete_repo("user/my-model")

# With safety
api.delete_repo("user/my-model", repo_type="dataset", missing_ok=True)

# Cannot be undone — no confirmation prompt
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `repo_id` | `str` | required | `namespace/name` |
| `token` | `str\|bool\|None` | cached | Auth token |
| `repo_type` | `str\|None` | `"model"` | `"model"`, `"dataset"`, `"space"` |
| `missing_ok` | `bool` | `False` | If `True`, no error if repo doesn't exist |

#### REST Equivalent

```
DELETE https://huggingface.co/api/repos/{repo_type_prefix}{repo_id}
```

Server response on success is 200 OK with `{"message": "ok"}`. On failure:
- 404 → `RepositoryNotFoundError` (if `missing_ok=False`)
- 403 → insufficient permissions

#### Practical Pattern: Cleanup Script

```python
def safe_delete(api, repo_id, repo_type=None):
    """Delete repo with confirmation-style safety."""
    try:
        info = api.repo_info(repo_id, repo_type=repo_type)
        print(f"Deleting: {repo_id} ({info.sha[-8:] if hasattr(info, 'sha') else 'unknown'})")
        api.delete_repo(repo_id, repo_type=repo_type, missing_ok=True)
        print(f"✓ Deleted {repo_id}")
    except Exception as e:
        print(f"✗ Could not delete {repo_id}: {e}")
```

---

### 3. `repo_info()` & `repo_exists()` — Reading Repository State

#### `repo_info(repo_id, ...)`

Returns a structured data object with full repository metadata. The return type depends on `repo_type`:

| `repo_type` | Return Type | Key Fields |
|-------------|-------------|------------|
| `None` / `"model"` | `ModelInfo` | `sha`, `pipeline_tag`, `config`, `siblings`, `safetensors`, `cardData`, `tags`, `downloads`, `likes` |
| `"dataset"` | `DatasetInfo` | `sha`, `siblings`, `cardData`, `tags`, `downloads`, `likes`, `dataset_info` |
| `"space"` | `SpaceInfo` | `sha`, `sdk`, `runtime`, `siblings`, `cardData`, `tags` |
| `"kernel"` | `KernelInfo` | Limited fields, no expand/files_metadata |

```python
info = api.repo_info("user/my-model", repo_type="model")

# Basic properties
info.id              # "user/my-model"
info.sha             # Current commit OID
info.private         # bool
info.downloads       # int
info.likes           # int
info.pipeline_tag    # "text-generation"
info.tags            # ["transformers", "pytorch", ...]
info.card_data       # ModelCardData (parsed YAML frontmatter)

# Files listing (requires files_metadata=True)
info = api.repo_info("user/my-model", files_metadata=True)
for sibling in info.siblings:
    sibling.rfilename   # "model.safetensors"
    sibling.size        # File size in bytes
    if sibling.lfs:
        sibling.lfs["sha256"]   # LFS pointer SHA256
        sibling.lfs["size"]     # Actual content size
```

#### `expand` Parameter

The `expand` parameter controls which additional properties to fetch. This is more efficient than fetching all properties when you only need specific ones.

```python
# Get trending score and inference details
info = api.repo_info(
    "user/my-model",
    expand=["trendingScore", "inference"]
)
info.trending_score   # float
info.inference        # InferenceStatus
```

Available expand properties differ by repo type. Common ones:
- `trendingScore` — trending score (model, dataset, space)
- `inference` — inference status and widget config (model)
- `cardMetadata` — full card YAML metadata (model, dataset)
- `stats` — download/visit statistics (dataset, space)

#### `repo_exists(repo_id, ...)`

Simple boolean check — returns `True`/`False`, never raises.

```python
if api.repo_exists("facebook/opt-125m"):
    print("Exists!")
else:
    print("Does not exist or is private")

# Works with all repo types
if api.repo_exists("user/my-space", repo_type="space"):
    print("Space exists")
```

**Important:** Returns `False` for private repos you don't have access to (same as non-existent repos). Use `repo_info()` with proper auth to distinguish between "doesn't exist" and "exists but private."

---

### 4. `update_repo_settings()` — Repo Settings Management

Updates repository visibility and gated access settings after creation.

```python
api.update_repo_settings(
    "user/my-model",
    private=False,           # Make public
    gated="auto",            # Enable gated access (auto-approve)
)

api.update_repo_settings(
    "user/my-space",
    visibility="protected",  # Space-specific: visible but not forkable
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `repo_id` | `str` | required | `namespace/name` |
| `gated` | `Literal["auto","manual",False]\|None` | `None` | Gated access mode |
| `private` | `bool\|None` | `None` | `True` = make private. Cannot use with `visibility`. |
| `visibility` | `Literal["public","private","protected"]\|None` | `None` | Explicit visibility |
| `token` | `str\|bool\|None` | cached | Auth token |
| `repo_type` | `str\|None` | `"model"` | `"model"`, `"dataset"`, `"space"` |

#### Gated Access Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `False` | Anyone can access without signing in | Default, fully open |
| `"auto"` | Must sign in and accept terms; auto-approved | Models with terms of use |
| `"manual"` | Must sign in and request access; manually approved by owner | Models under review, sensitive datasets |

```python
# Enable manual gated access
api.update_repo_settings(
    "user/sensitive-model",
    gated="manual",
)

# Disable gated access (fully open)
api.update_repo_settings(
    "user/sensitive-model",
    gated=False,
)
```

#### REST Equivalent

```
PUT https://huggingface.co/api/{repo_type}s/{repo_id}/settings
Content-Type: application/json

{
  "visibility": "public",
  "gated": "auto"
}
```

#### Error Handling

| Error | When |
|-------|------|
| `ValueError` | Invalid `gated` value (not "auto", "manual", or False) |
| `ValueError` | Invalid `repo_type` |
| `ValueError` | No settings provided (empty payload) |
| `RepositoryNotFoundError` | Repo doesn't exist or no access |

---

### 5. `move_repo()` — Repository Rename & Transfer

Renames a repo or transfers it to another namespace. Supports all repo types.

```python
# Rename within same namespace
api.move_repo("user/old-name", "user/new-name")

# Transfer to another user/organization
api.move_repo("user/my-model", "other-user/my-model")
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `from_id` | `str` | required | Current `namespace/name` |
| `to_id` | `str` | required | Target `namespace/name` |
| `repo_type` | `str\|None` | `"model"` | Must be explicit for non-model repos |
| `token` | `str\|bool\|None` | cached | Auth token |

#### Limitations

- Cannot move to a namespace you don't own
- The `from_id` and `to_id` must both be in `namespace/name` format (with `/`)
- Redirections from old URL are set up automatically by the Hub
- Moving a repo does NOT affect downloads/forks — redirects are in place

#### REST Equivalent

```
POST https://huggingface.co/api/repos/move
Content-Type: application/json

{
  "fromRepo": "user/old-name",
  "toRepo": "user/new-name",
  "type": "model"
}
```

#### Error Handling

| Error | When |
|-------|------|
| `ValueError` | `from_id` or `to_id` missing `/` separator |
| `RepositoryNotFoundError` | Source repo doesn't exist |
| `HfHubHTTPError` (403) | No permission on source or target namespace |

---

### 6. `duplicate_repo()` — Server-Side Repository Cloning

Full server-side copy preserving complete git history and LFS objects. No local download/upload needed. Zero cost.

```python
from huggingface_hub import duplicate_repo, SpaceHardware

# Duplicate a model to your account (same name)
url = duplicate_repo("google/gemma-7b")
# → RepoUrl('https://huggingface.co/youruser/gemma-7b')

# Duplicate with custom name
url = duplicate_repo("google/gemma-7b", to_id="myorg/my-gemma-7b")

# Duplicate a dataset
url = duplicate_repo("openai/gdpval", to_id="myorg/my-gdpval", repo_type="dataset")

# Duplicate a Space with upgraded hardware
url = duplicate_repo(
    "multimodalart/dreambooth-training",
    repo_type="space",
    space_hardware="t4-medium",
)
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `from_id` | `str` | required | Source repo ID |
| `to_id` | `str\|None` | `None` | Target repo ID (`None` = same name under your account) |
| `repo_type` | `str\|None` | `"model"` | Repo type |
| `private` | `bool\|None` | `None` | Override privacy (default: same as source) |
| `visibility` | `str\|None` | `None` | Explicit visibility override |
| `token` | `str\|bool\|None` | cached | Auth token |
| `exist_ok` | `bool` | `False` | Don't error if target exists |
| `space_hardware` | `SpaceHardware\|None` | Same as source | **Space only** — override hardware |
| `space_storage` | `SpaceStorage\|None` | Same as source | **Deprecated** — use volumes |
| `space_sleep_time` | `int\|None` | Same as source | **Space only** — override sleep time |
| `space_secrets` | `list[dict]\|None` | Not copied | **Space only** — set new secrets |
| `space_variables` | `list[dict]\|None` | Not copied | **Space only** — set new variables |
| `space_volumes` | `list[Volume]\|None` | Same as source | **Space only** — override volumes |

**Critical note:** Secrets are NEVER copied from the source Space for security reasons. Set them explicitly via `space_secrets=`.

#### Free Tier Notes

| Aspect | Detail |
|--------|--------|
| **Cost** | Free — server-side operation |
| **Disk usage** | The duplicate is a new repo, so it uses separate storage quota |
| **Space hardware** | Free tier is limited to `CPU_BASIC` unless you have PRO |
| **Privacy** | Private repos can be duplicated to private repos only (unless you own both) |

---

### 7. `super_squash_history()` — Commit History Compaction

Collapses all commits on a branch into a single commit. Useful for repos with bloated git history from many small uploads.

```python
api.super_squash_history("user/my-model", commit_message="Initial release")

# Squash a specific branch
api.super_squash_history("user/my-model", branch="dev", commit_message="Squash dev")

# Works on all repo types
api.super_squash_history("user/my-dataset", repo_type="dataset")
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `repo_id` | `str` | required | `namespace/name` |
| `branch` | `str\|None` | `None` | Branch to squash (default: `main`) |
| `commit_message` | `str\|None` | `None` | Message for the squashed commit |
| `repo_type` | `str\|None` | `"model"` | Repo type |
| `token` | `str\|bool\|None` | cached | Auth token |

#### Warnings

- **IRREVERSIBLE** — history cannot be retrieved after squashing
- **Breaks merge compatibility** — once a branch is squashed, it cannot be merged into another branch (divergent history)
- **Only works from HEAD** — cannot squash from a non-tip revision
- **Cannot squash tags** — `BadRequestError` if you pass a tag as branch

#### When to Squash

1. **Before uploading large model files** — reduces LFS storage by removing old unreferenced LFS OIDs (see Topic #98, LFS deep-dive)
2. **After many small dataset updates** — cleans up hundreds of tiny commits
3. **Before making a repo public** — removes sensitive info accidentally committed and later removed

```python
# Typical workflow: upload → squash → upload more
api.upload_folder(folder_path="./checkpoints", repo_id="user/my-model")
api.super_squash_history("user/my-model", commit_message="Initial checkpoint")
api.upload_folder(folder_path="./final-model", repo_id="user/my-model")
```

---

### 8. REST API Reference (Raw Endpoints)

All `HfApi` methods map to specific REST endpoints. Here are the direct equivalents for scripting (e.g., with `curl` or `httpx`):

| Operation | Method | Endpoint | Auth Required |
|-----------|--------|----------|---------------|
| Create repo | `POST` | `/api/repos/create` | Yes (write scope) |
| Delete repo | `DELETE` | `/api/{repo_type}s/{repo_id}` | Yes (write scope) |
| Repo info | `GET` | `/api/{repo_type}s/{repo_id}` | No for public |
| Repo exists | `GET` | `/api/{repo_type}s/{repo_id}` | No for public |
| Update settings | `PUT` | `/api/{repo_type}s/{repo_id}/settings` | Yes (write scope) |
| Move repo | `POST` | `/api/repos/move` | Yes (admin on both) |
| Duplicate repo | `POST` | `/api/{repo_type}s/{from_id}/duplicate` | Yes (write scope) |
| Squash history | `POST` | `/api/{repo_type}s/{repo_id}/super-squash` | Yes (write scope) |

Repo type URL prefixes: `""` (model), `/datasets/`, `/spaces/`.

Example direct API call:
```bash
# Create a model repo
curl -X POST "https://huggingface.co/api/repos/create" \
  -H "Authorization: Bearer hf_..." \
  -H "Content-Type: application/json" \
  -d '{"name": "my-model", "organization": "myuser", "type": "model", "visibility": "public"}'

# Get repo info
curl "https://huggingface.co/api/models/meta-llama/Llama-3.2-1B"

# Update repo settings (make private)
curl -X PUT "https://huggingface.co/api/models/myuser/my-model/settings" \
  -H "Authorization: Bearer hf_..." \
  -H "Content-Type: application/json" \
  -d '{"visibility": "private"}'
```

---

### 9. Practical Patterns

#### Pattern A: Repository Bootstrap Blueprint

```python
from huggingface_hub import HfApi
from huggingface_hub.hf_api import SpaceHardware

api = HfApi()

def bootstrap_model_repo(repo_id, private=True, description=None):
    """Create a model repo with standard settings."""
    url = api.create_repo(repo_id, private=private, exist_ok=True)
    if description:
        api.update_repo_settings(repo_id, gated="auto" if private else False)
    print(f"✓ {repo_id} → {url}")
    return url

def bootstrap_space_repo(repo_id, sdk="gradio", secrets=None):
    """Create a Space repo with optional secrets."""
    url = api.create_repo(
        repo_id,
        repo_type="space",
        space_sdk=sdk,
        space_hardware=SpaceHardware.CPU_BASIC,
        exist_ok=True,
        space_secrets=secrets or [],
    )
    print(f"✓ Space {repo_id} → {url}")
    return url

# Usage
bootstrap_model_repo("beer-sakthai/new-model", private=False, description="My new model")
bootstrap_space_repo(
    "beer-sakthai/my-demo",
    sdk="gradio",
    secrets=[{"key": "API_KEY", "value": "sk-...", "description": "API key"}]
)
```

#### Pattern B: Safe Migration Workflow

```python
def migrate_repo(api, from_id, to_id, repo_type="model"):
    """Safely move a repo with verification."""
    # 1. Verify source exists
    src_info = api.repo_info(from_id, repo_type=repo_type)
    print(f"Source: {from_id} ({src_info.sha[:8]})")

    # 2. Check target doesn't already exist
    if api.repo_exists(to_id, repo_type=repo_type):
        raise ValueError(f"Target {to_id} already exists!")

    # 3. Move
    api.move_repo(from_id, to_id, repo_type=repo_type)
    print(f"Moved: {from_id} → {to_id}")

    # 4. Verify
    dst_info = api.repo_info(to_id, repo_type=repo_type)
    assert dst_info.sha == src_info.sha, "SHA mismatch after move!"
    print(f"✓ Verified: {to_id} ({dst_info.sha[:8]})")
```

#### Pattern C: Storage Optimization Workflow

```python
def optimize_repo_storage(api, repo_id, repo_type="model"):
    """Squash history and verify storage reduction."""
    info = api.repo_info(repo_id, repo_type=repo_type, files_metadata=True)
    before_count = len(info.siblings)
    print(f"Before: {before_count} files")

    api.super_squash_history(repo_id, repo_type=repo_type,
                             commit_message="Storage optimization")
    print("✓ History squashed")
```

#### Pattern D: List and Filter All Your Repos

```python
# List all repos for a user (uses the search API internally)
repos = api.list_repos("beer-sakthai", repo_type="model")
for repo in repos:
    print(f"{repo.repo_id} ({'private' if repo.private else 'public'}) "
          f"· {repo.downloads:,} downloads · {repo.likes:,} likes")
```

---

### 10. Data Models Reference

#### `RepoUrl` (returned by `create_repo()`, `duplicate_repo()`)

| Attribute | Type | Example |
|-----------|------|---------|
| `__str__` | `str` | `"https://huggingface.co/user/my-model"` |
| `endpoint` | `str` | `"https://huggingface.co"` |
| `repo_type` | `str` | `"model"` |
| `repo_id` | `str` | `"user/my-model"` |

#### `ModelInfo` (returned by `repo_info()`)

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | `"user/my-model"` |
| `sha` | `str` | Current commit OID |
| `private` | `bool` | Privacy status |
| `downloads` | `int` | Total downloads |
| `likes` | `int` | Total likes |
| `pipeline_tag` | `str\|None` | Task type (e.g. `"text-generation"`) |
| `library_name` | `str\|None` | Framework (e.g. `"transformers"`) |
| `tags` | `list[str]` | All tags (library, license, language, region, etc.) |
| `card_data` | `ModelCardData\|None` | Parsed YAML frontmatter |
| `siblings` | `list[RepoFile]` | File listing (when `files_metadata=True`) |
| `safetensors` | `dict\|None` | Safetensors weight metadata |
| `config` | `dict\|None` | Model config.json |
| `gated` | `str\|bool\|None` | Gated access mode |
| `disabled` | `bool` | Whether repo is disabled |

#### `DatasetInfo` (returned by `repo_info()` for datasets)

Same base fields as ModelInfo, plus:
- `dataset_info` — dataset-specific metadata (features, splits, etc.)
- `card_data` — includes dataset card YAML

#### `SpaceInfo` (returned by `repo_info()` for spaces)

Same base fields, plus:
- `sdk` — `"gradio"`, `"streamlit"`, `"docker"`, `"static"`
- `runtime` — `SpaceRuntime` with stage, hardware, etc.

#### `RepoFile` (`siblings` items)

| Field | Type | Description |
|-------|------|-------------|
| `rfilename` | `str` | File path in repo |
| `size` | `int\|None` | File size (bytes) |
| `blob_id` | `str\|None` | Git blob OID |
| `lfs` | `dict\|None` | LFS metadata: `sha256`, `size`, `oid`, `pointerSize` |
| `type` | `str\|None` | File type |

---

### Key Takeaways

1. **`create_repo()` is universal** — one method for models, datasets, and Spaces. The `space_*` parameters are silently ignored for non-Space repos.
2. **`exist_ok=True` is your friend** — makes creation idempotent. Use in all automation scripts.
3. **`update_repo_settings()` is for post-creation changes** — you can toggle visibility and gated access anytime.
4. **`duplicate_repo()` is zero-cost** — server-side copy, no local download/upload. Secrets are never copied.
5. **`move_repo()` has input validation** — both `from_id` and `to_id` must have a `/` separator.
6. **`super_squash_history()` is one-way** — plan your compaction before merging branches or sharing repos.
7. **`repo_info()` is the Swiss Army knife** — use `expand` for efficient partial data, `files_metadata=True` for full file listing.
8. **`delete_repo()` has no undo** — always pair with `repo_info()` for a safety check.

### Resources
- `hf_api.py` source (Repo CRUD): https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/hf_api.py
  - `create_repo`: line ~4504
  - `delete_repo`: line ~4717
  - `update_repo_settings`: line ~4767
  - `move_repo`: line ~4846
  - `repo_info`: line ~3567
  - `duplicate_repo`: line ~8707
  - `super_squash_history`: line ~4269
- Hub REST API docs: https://huggingface.co/docs/hub/en/api
- Repo settings docs: https://huggingface.co/docs/hub/en/repositories-settings

---
## 2026-07-24: hf-inference-client-provider-fallback-and-routing — Provider Discovery & Fallback Chains (Topic #143)

### Summary
Deep-dive into building practical provider fallback chains using Hugging Face `InferenceClient`. Covers programmatic provider discovery via `model_info(expand='inferenceProviderMapping')`, the `InferenceProviderMapping` data model, building multi-provider fallback chains with `AsyncInferenceClient`, Router API `/v1/models` for provider comparison, direct provider API key integration, and real provider availability patterns verified against `huggingface_hub` v1.24.0.

### Core Discovery API — inferenceProviderMapping

The Hub's `expand=inferenceProviderMapping` parameter reveals which providers serve a model and their status.

```python
from huggingface_hub import HfApi

api = HfApi()
info = api.model_info("microsoft/phi-4", expand="inferenceProviderMapping")
for pm in info.inference_provider_mapping:
    print(f"{pm.provider:25s} | status={pm.status:10s} | task={pm.task}")
# Output (verified live on 2026-07-24):
#   featherless-ai            | status=live       | task=conversational
#   deepinfra                 | status=live       | task=conversational
```

#### InferenceProviderMapping Data Model

| Field | Type | Description |
|-------|------|-------------|
| `provider` | `str` | Provider identifier (e.g. `"featherless-ai"`, `"deepinfra"`, `"together"`) |
| `hf_model_id` | `str` | The original Hugging Face model ID |
| `provider_id` | `str` | Provider's internal model name (may differ from HF ID) |
| `status` | `str` | `"live"` = available, other values = degraded/unavailable |
| `task` | `str` | Inference task (e.g. `"conversational"`, `"text-to-image"`) |
| `adapter` | `str\|None` | LoRA adapter if applicable |
| `adapter_weights_path` | `str\|None` | Path to adapter weights |
| `type` | `str\|None` | Model type |

**Key insight:** Not all models have providers. Models with no mapping must be run locally.

### Real Provider Availability Patterns

Testing against `huggingface_hub` v1.24.0 on 2026-07-24:

| Model | Live Providers | Total |
|-------|---------------|-------|
| `microsoft/phi-4` | featherless-ai, deepinfra | 2/2 |
| `Qwen/Qwen2.5-7B-Instruct` | featherless-ai, together | 2/2 |
| `Qwen/Qwen3-32B` | featherless-ai, deepinfra, nscale | 3/5 |
| `meta-llama/Meta-Llama-3.1-8B-Instruct` | novita, deepinfra, nscale | 3/4 |
| `google/gemma-2-2b-it` | featherless-ai | 1/1 |
| `NousResearch/Hermes-3-Llama-3.1-8B` | featherless-ai | 1/1 |
| `mistralai/Mistral-7B-Instruct-v0.3` | _(none live)_ | 0/1 |

**Patterns observed:**
- **featherless-ai** is the most common free provider
- **deepinfra** and **nscale** are frequent secondary providers
- **together** covers selective popular models
- Empty live-provider sets happen — always check before routing

### Provider Selection — Three-Layer System

#### Layer 1: Client-Level Default
```python
client = InferenceClient(provider="auto")     # fastest available (default)
client = InferenceClient(provider="deepinfra") # pin to specific provider
```

#### Layer 2: Per-Call Override via Model-ID Suffix
```python
result = client.chat_completion(
    model="Qwen/Qwen3-32B:fastest",  # :cheapest, :preferred, :provider-name
    messages=[...],
)
```

#### Layer 3: Runtime Provider Detection
```python
def get_live_providers(model_id: str) -> list[str]:
    info = HfApi().model_info(model_id, expand="inferenceProviderMapping")
    return [pm.provider for pm in info.inference_provider_mapping if pm.status == "live"]
```

### Fallback Chain Pattern
```python
async def chat_with_fallback(messages, model="microsoft/phi-4", providers=None, timeout=15.0):
    if providers is None:
        providers = get_live_providers(model) or ["auto"]
    for provider in providers:
        client = AsyncInferenceClient(provider=provider, timeout=timeout)
        try:
            result = await client.chat_completion(model=model, messages=messages, max_tokens=256)
            return result
        except Exception:
            continue
        finally:
            await client.close()
    raise RuntimeError(f"All providers failed for {model}")
```

### Full reference in main hf-learnings.md

### Resources
- [InferenceClient API reference](https://huggingface.co/docs/huggingface_hub/v1.24.0/en/package_reference/inference_client)
- [Inference Providers docs](https://huggingface.co/docs/inference-providers/en/index)
- [Router API](https://router.huggingface.co/v1/models)

### Skill
huggingface-hub — references/hf-learnings.md

---

## 2026-07-24: hf-huggingface-hub-download-lifecycle — `hf_hub_download()` Internals Deep Dive (Topic #147)

### Summary
Complete deep-dive into the internal working of `hf_hub_download()` — the primary entry-point for downloading files from the Hugging Face Hub. Covers the full download lifecycle: metadata HEAD call with redirect following, cache lookup via `try_to_load_from_cache()`, the `.no_exist` cache for known-missing files, concurrent download protection via `WeakFileLock`, HTTP streaming with resume/retry, Xet-accelerated downloads via `xet_get()`, atomic temp-file writes with `_download_to_tmp_and_move()`, symlink creation in the cache, the `local_dir` path (metadata + etag matching), and environment variable tuning. Source-verified against `huggingface_hub` v1.24.0 file_download.py (2026 lines).

### Architecture Overview

`hf_hub_download()` is the central function for all Hugging Face Hub downloads — used by Transformers, Diffusers, Datasets, and every other HF library. It manages two distinct paths:

```
hf_hub_download()
├── local_dir is set → _hf_hub_download_to_local_dir()
│   ├── File metadata stored in .cache/huggingface/ subfolder
│   ├── Etag matching to avoid redownloads
│   └── Fallback to cache_dir if file is cached
└── local_dir is None → _hf_hub_download_to_cache_dir()
    ├── Cache-first: try_to_load_from_cache()
    ├── Metadata HEAD call
    ├── Lock-based concurrent download protection
    └── Symlink-based deduplication
```

### 1. Cache-First Path: `try_to_load_from_cache()`

Before making any network call, the function checks the local cache:

```python
from huggingface_hub import try_to_load_from_cache, _CACHED_NO_EXIST

# Returns one of:
#   - str:        path to the cached file
#   - _CACHED_NO_EXIST:  special sentinel object if file's non-existence was cached
#   - None:       file is not cached at all
result = try_to_load_from_cache("bert-base-uncased", "config.json",
                                  revision="main", repo_type="model")
```

**Cache lookup algorithm:**
1. Resolve `revision` via `refs/` directory (e.g. `main` → `2439f60ef33a0d46d85da5001d52aeda5b00ce9f`)
2. Check `.no_exist/{revision}/{filename}` — if file is known to not exist, immediately return `_CACHED_NO_EXIST` (avoids repeated 404 HEAD calls)
3. Look for `snapshots/{commit_hash}/{filename}` — if the symlink exists, return its resolved path
4. Return `None` if not found

**Key insight:** The `.no_exist` cache is a silent efficiency hack. When a HEAD request returns 404, the fact is recorded in `.no_exist/{revision}/{filename}` as an empty file. Future calls skip the network entirely until the ref is updated.

### 2. Metadata HEAD Call: `get_hf_file_metadata()`

When the cache misses, the function issues a HEAD request to the Hub to get file metadata:

```python
from huggingface_hub.file_download import get_hf_file_metadata, HfFileMetadata

url = hf_hub_url("bert-base-uncased", "config.json", revision="main")
metadata = get_hf_file_metadata(url, ...)
# HfFileMetadata(
#     commit_hash="2439f60...",
#     etag="7cb18dc9bafbfcf74629a4b760af1b160957a83e",
#     location="https://huggingface.co/bert-base-uncased/resolve/main/config.json",
#     size=398,
#     xet_file_data=None  # or XetFileData if Xet-enabled repo
# )
```

**HEAD request flow:**
1. Build the URL: `https://huggingface.co/{repo_id}/resolve/{revision}/{filename}`
2. Send HEAD with `Accept-Encoding: identity` to get real file size (not compressed)
3. Follow redirects using `_httpx_follow_relative_redirects_with_backoff()` — handles CDN redirects to CloudFront
4. Parse response headers:
   - `X-Repo-Commit` → `commit_hash`
   - `X-Linked-Etag` (preferred) or `ETag` → `etag`
   - `X-Linked-Size` (preferred) or `Content-Length` → `size`
   - `X-Xet-*` headers → `xet_file_data` (via `parse_xet_file_data_from_response()`)
5. The `location` returned may be a CDN URL (CloudFront) for large files

**Tree cache optimization:** When `tree_cache_folder` is set (local_dir mode with a commit_hash), the metadata can be reconstructed from a cached tree listing, **skipping the HEAD call entirely**. This is a significant speedup for repos with many files.

**Error handling in `_get_metadata_or_catch_error()`:**
- `local_files_only=True` → immediately returns `OfflineModeIsEnabled` error
- Network errors (timeout, connection) → returns exception, triggers cache fallback
- HTTP 404 → returns exception, might cache as `.no_exist`
- HTTP 429/5xx → on first call returns error, on retry (60s timeout) retries once more

### 3. Concurrent Download Protection: `WeakFileLock`

Two concurrent processes downloading the same file simultaneously would corrupt the cache. The solution is file-based locking:

```python
from huggingface_hub.utils import WeakFileLock

lock_path = os.path.join(locks_dir, repo_folder_name(...), f"{etag}.lock")
with WeakFileLock(lock_path):
    # Only one process enters this section per unique file (identified by etag)
    _download_to_tmp_and_move(...)
    _create_symlink(blob_path, pointer_path, new_blob=True)
```

**Lock behavior:**
- Located at `{cache_dir}/.locks/{repo_type}s--{namespace}--{repo_name}/{etag}.lock`
- Uses `fcntl.flock()` on Linux/Mac, `msvcrt.locking()` on Windows
- **Best-effort only:** On some filesystems (Lustre, GPFS, NFS), `flock()` silently succeeds for all callers. In that case, the lock is broken but correctness is maintained by the per-process temp file (see §5).
- The lock protects both the download AND the symlink creation atomically

### 4. Download Methods: HTTP vs Xet

Once the lock is acquired, `_download_to_tmp_and_move()` decides the download method:

```python
if xet_file_data is not None and is_xet_available():
    # Xet-accelerated download
    xet_get(incomplete_path=tmp_path, xet_file_data=xet_file_data, ...)
else:
    # Standard HTTP streaming download
    http_get(url_to_download, temp_file, headers=headers, ...)
```

#### 4a. HTTP Download: `http_get()`

```python
from huggingface_hub.file_download import http_get

http_get(
    url,                          # URL to download from
    temp_file,                    # file-like object to write to
    resume_size=0,                # bytes already downloaded (for resume)
    headers=headers,
    expected_size=expected_size,  # used for progress bar and validation
    tqdm_class=tqdm_class,
)
```

**HTTP download flow:**
1. Set `Range` header if `resume_size > 0` (supports resume)
2. Files > 50GB (`MAX_HTTP_DOWNLOAD_SIZE`) raise ValueError — must use Xet
3. Stream with `http_stream_backoff()` (retry on 408, 429 status codes)
4. If requested Range but got HTTP 200 (server ignored Range), truncate and restart from 0
5. Read `Content-Range` or `Content-Length` to get total size
6. Fall back to `expected_size` if no size header (compressed responses)
7. Stream in chunks (`DOWNLOAD_CHUNK_SIZE`) with progress bar
8. **Auto-retry:** On `httpx.ConnectError`, `TimeoutException`, or `RemoteProtocolError`:
   - Log warning, `time.sleep(1)`, retry up to 5 times
   - Reuses the same progress bar across retries (no double-counting)
9. **Size validation:** After download, verifies `expected_size == temp_file.tell()`. Mismatch raises `OSError` with clear message.

#### 4b. Xet Download: `xet_get()`

For repos using Xet storage (the default since huggingface_hub v0.32.0):

```python
xet_get(
    incomplete_path=tmp_path,
    xet_file_data=xet_file_data,  # from HEAD response headers
    headers=headers,
    expected_size=expected_size,
)
```

**Xet download flow:**
1. Opens a `new_file_download_group()` session with:
   - `token_refresh_url` from xet_file_data (short-lived tokens)
   - `custom_headers` (without auth: Xet handles auth differently)
   - `progress_callback` for dual progress bars (transfer + reconstruction)
2. Calls `group.start_download_file(XetFileInfo(hash, size), path)`:
   - Registers download task → starts immediately in background
   - Queries CAS server: "how is this file split into chunks?"
   - Server responds with: chunk list + presigned S3 URLs
   - Downloads chunks in parallel (auto-caches for future reuse)
   - Reassembles chunks → writes file to disk
3. On `KeyboardInterrupt`: calls `abort_xet_session()` for clean shutdown

**Key advantage:** Chunk-based deduplication. If a model file changes only slightly between versions, only the changed chunks need to be re-downloaded. This is fundamentally different from LFS where the entire file must be re-downloaded.

### 5. Atomic Write: Per-Process Temp Files

The most subtle correctness mechanism in the download system:

```python
# NOT this (shared incomplete path would corrupt on broken locks):
# tmp_path = incomplete_path  # .incomplete file (shared across processes)

# This (process-unique temp file):
tmp_path = incomplete_path.with_name(
    f"{incomplete_path.stem}.{uuid.uuid4().hex[:8]}.incomplete"
)

# Download to unique temp
with tmp_path.open("wb") as f:
    http_get(url_to_download, f, ...)

# Atomic rename to final blob path
_chmod_and_move(tmp_path, destination_path)
```

**Why this matters:** On NFS/Lustre/GPFS filesystems, `flock()` is a no-op. Without per-process temp files, concurrent downloads would append to the same incomplete file, causing corruption. With unique temp files, a broken lock only wastes bandwidth — each process downloads independently and the last one to rename wins.

**The rename is atomic** on POSIX systems (`os.rename()` on same filesystem). After the move, `blobs/{etag}` is a complete file. Any subsequent process that loses the race will find the blob already exists and skip the download.

### 6. Symlink Creation: `_create_symlink()`

After the blob is written, the function creates a symlink from `snapshots/{commit_hash}/{filename}` → `blobs/{etag}`:

```python
from huggingface_hub.file_download import _create_symlink

_create_symlink(src=blob_path, dst=pointer_path, new_blob=True)
```

**Symlink logic:**
1. Remove existing symlink file at dst (if any)
2. Compute **relative** symlink source (e.g., `../../../blobs/{etag}`) — this is intentional! Relative paths survive cache directory moves and work better on Windows
3. Check symlink support on the volume (`are_symlinks_supported()`):
   - Test once per cache directory at first use, cache result
4. If symlinks supported: `os.symlink(relative_src, abs_dst)`
5. If symlinks NOT supported (Windows without Developer Mode):
   - `new_blob=True`: Move the blob file to the snapshot path (no symlink at all)
   - `new_blob=False`: Copy the blob (conservative — blob may be referenced elsewhere)

**Windows considerations:**
- If path > 255 chars, prefix with `\\?\`
- Symlink support requires Developer Mode or admin privileges
- If different volumes: `os.path.relpath()` raises `ValueError`, fallback to `shutil.copyfile()`

### 7. Ref Caching: `_cache_commit_hash_for_specific_revision()`

After a successful download, the mapping from revision (tag/branch) to commit_hash is cached:

```python
_cache_commit_hash_for_specific_revision(storage_folder, revision, commit_hash)
```

This writes a file at `refs/{revision}` containing the commit hash. Writing is **atomic** (tmp file + rename) so concurrent readers never see a partially written file. Only written if `revision != commit_hash` — commit hashes don't need mapping.

### 8. The `local_dir` Path

When `local_dir` is provided, the download goes through a different code path:

```python
local_path = _hf_hub_download_to_local_dir(
    local_dir="/path/to/local",
    repo_id="bert-base-uncased",
    filename="config.json",
    ...
)
```

**local_dir architecture:**
```
local_dir/
├── config.json                    # actual file
├── pytorch_model.bin              # actual file
└── .cache/huggingface/
    ├── download_metadata.json     # mapping filename → {commit_hash, etag}
    └── tree_cache/                # cached tree listings per commit_hash
```

**Optimization flow:**
1. **Quick return:** If file exists + metadata has matching commit_hash → return immediately (no HEAD call)
2. **HEAD call:** Get `etag`, `commit_hash`, `expected_size`
3. **Etag match:** If local file exists + etag matches → update metadata, return (no download)
4. **Etag = sha256 fallback:** If metadata is missing but etag is a SHA256 hash (LFS file), compute local file hash and compare → if match, update metadata, return (avoids re-downloading large LFS files!)
5. **Cache fallback:** Before downloading, check if file exists in main cache (`try_to_load_from_cache()`) → copy from cache instead of downloading
6. **Full download:** Download via temp file + atomic rename, then write metadata

**Key difference from cache mode:** local_dir uses `download_metadata.json` for state tracking instead of the full cache directory structure. Files are stored directly in `local_dir` without symlinks.

### 9. Environment Variables Tuning

| Variable | Default | Effect |
|----------|---------|--------|
| `HF_HOME` | `~/.cache/huggingface` | Base directory for all HF caches |
| `HF_HUB_CACHE` | `$HF_HOME/hub` | Cache directory for Hub downloads |
| `HF_HUB_DOWNLOAD_TIMEOUT` | `10` (seconds) | Timeout for HTTP download requests |
| `HF_HUB_ETAG_TIMEOUT` | `10` | Timeout for HEAD metadata requests (env var takes precedence over function arg) |
| `HF_HUB_DISABLE_SYMLINKS` | (not set) | Disable symlink usage; fall back to file copies |
| `HF_HUB_DISABLE_SYMLINKS_WARNING` | (not set) | Suppress the symlink warning on Windows |
| `HF_HUB_DISABLE_PROGRESS_BARS` | (not set) | Disable all progress bars |
| `HF_HUB_DISABLE_XET` | (not set) | Force legacy HTTP path instead of Xet |
| `HF_ENDPOINT` | `https://huggingface.co` | Override the Hub endpoint URL |
| `HF_TOKEN` | (not set) | Default authentication token |
| `HF_HUB_ENABLE_HF_TRANSFER` | (deprecated) | Old Rust download accelerator; use Xet instead |

### 10. Dry-Run Mode

Since huggingface_hub v1.24.0, `hf_hub_download()` supports dry runs:

```python
from huggingface_hub import hf_hub_download, DryRunFileInfo

info = hf_hub_download("bert-base-uncased", "pytorch_model.bin", dry_run=True)
# DryRunFileInfo(
#     commit_hash="2439f60ef33a0d46d85da5001d52aeda5b00ce9f",
#     file_size=440473133,
#     filename="pytorch_model.bin",
#     local_path="/.../snapshots/2439f60/.../pytorch_model.bin",
#     is_cached=True,
#     will_download=False
# )
```

Dry-run skips the actual download but performs:
1. Cache lookup (`try_to_load_from_cache`)
2. Metadata HEAD call (unless `local_files_only=True`)
3. Returns `DryRunFileInfo` with `is_cached` and `will_download` flags

### 11. Error Handling Reference

| Error | Raised When |
|-------|-------------|
| `RepositoryNotFoundError` | Repo doesn't exist or is private without access |
| `RevisionNotFoundError` | Branch/tag/commit doesn't exist |
| `RemoteEntryNotFoundError` | File doesn't exist in the repo |
| `LocalEntryNotFoundError` | `local_files_only=True` and file not in cache |
| `OfflineModeIsEnabled` | Network is disabled or unavailable |
| `ValueError` | File > 50GB without Xet installed |
| `OSError` | ETag can't be determined; file size mismatch |
| `EnvironmentError` | `token=True` but token file not found |

### Concurrency Model Summary

```
Process A: hf_hub_download("model", "weights.bin")
├── try_to_load_from_cache() → None (not cached)
├── get_hf_file_metadata() → HEAD request → {etag: "abc123", ...}
├── WeakFileLock(".locks/model/abc123.lock")
│   ├── tmp = blobs/abc123.{uuid}.incomplete (unique per process!)
│   ├── http_get(url, tmp) → stream chunks → tmp written
│   ├── os.replace(tmp → blobs/abc123) → atomic
│   └── _create_symlink(blobs/abc123 → snapshots/{hash}/weights.bin)
└── return snapshot_path

Process B (concurrent, same file):
├── try_to_load_from_cache() → None
├── get_hf_file_metadata() → same etag
├── WeakFileLock(".locks/model/abc123.lock") → blocks on A's lock
│   ├── (A releases lock → B acquires it)
│   ├── blobs/abc123 EXISTS NOW (A wrote it) → skip download
│   ├── pointer_path → symlink already exists → skip
│   └── return pointer_path
└── Returns immediately (no download)
```

This design means: **the first downloader pays the bandwidth cost; all concurrent waiters get the cached file for free.**

### Resources
- Source: `file_download.py` in `huggingface_hub` (2026 lines) — https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/file_download.py
- Download guide: https://huggingface.co/docs/huggingface_hub/en/guides/download
- Cache guide: https://huggingface.co/docs/huggingface_hub/en/guides/manage-cache
- Cache reference: https://huggingface.co/docs/huggingface_hub/en/package_reference/cache
- File download reference: https://huggingface.co/docs/huggingface_hub/v1.24.0/en/package_reference/file_download
- Xet storage docs: https://huggingface.co/docs/hub/en/xet
- `_CACHED_NO_EXIST`: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/file_download.py#L63

### Skill
huggingface-hub — references/hf-learnings.md
---

## 2026-07-24: hf-hub-sandboxes -- Sandboxes: Isolated Cloud VMs via Jobs (Topic #148)

### Summary
Complete deep-dive into the new **Sandbox** feature in `huggingface_hub` v1.22.0+ -- isolated cloud machines that spin up in seconds for running commands, transferring files, and serving ports. Covers both `Sandbox.create()` (dedicated VMs) and `SandboxPool` (shared CPU pool), the full API surface, CLI commands, background processes, port proxying, and cost-model implications. Plus bonus coverage of the simultaneously released **Space Templates** (v1.23.0), **Tree Cache** (v1.22.0), and **Named Jobs** (v1.24.0).

### Architecture Overview

Sandboxes are built on top of **Jobs**: under the hood a sandbox is a Job running a tiny static server that exposes command execution and file transfers over HTTP. This means any Docker image with `/bin/sh` works -- no Python, pip, or agent preinstalled needed (the server binary is injected at startup). Sandboxes inherit Jobs' billing, hardware flavors, namespace permissions, and 24h maximum lifetime.

**Two flavors:**

| Aspect | `Sandbox.create()` | `SandboxPool` |
|--------|-------------------|---------------|
| Allocation | 1 Job = 1 sandbox (whole VM) | 1 Job = many sandboxes (packed) |
| Isolation | Full VM | uid + Landlock (same-user trust) |
| Cold start | ~6s per sandbox | ~6s first host, then ~1 RTT each |
| Cost | 1 VM per sandbox | 1 VM amortized across many sandboxes |
| GPU | Yes | No (CPU only) |
| Best for | Single sandbox, GPU, untrusted code | Many cheap CPU sandboxes (RL, fan-out) |

### Core API: Sandbox.create()

```python
from huggingface_hub import Sandbox

# Context manager -- auto-terminates on exit
with Sandbox.create() as sbx:
    result = sbx.run("python -c 'print(40 + 2)'")
    print(result.stdout)  # 42

# With custom image and GPU flavor
sbx = Sandbox.create(
    image="pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel",
    flavor="a10g-small",
    idle_timeout=600,
    env={"MY_VAR": "hello"},
    secrets={"API_KEY": "sk-..."},
    volumes=[Volume(...)],
    forward_hf_token=False,
)
```

#### Sandbox.create() Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image` | `str` | `"python:3.12"` | Any Docker image with `/bin/sh` |
| `flavor` | `str` | `"cpu-basic"` | Hardware flavor (`cpu-basic`, `a10g-small`, etc.) |
| `idle_timeout` | `int\|float\|None` | `600` | Auto-shutdown after inactivity (s); None disables |
| `env` | `dict` | `None` | Environment variables |
| `secrets` | `dict` | `None` | Encrypted secret env vars |
| `volumes` | `list[Volume]` | `None` | HF repos/buckets to mount |
| `namespace` | `str` | `None` | User/org namespace (defaults to current user) |
| `forward_hf_token` | `bool` | `False` | Inject HF_TOKEN into sandbox |
| `start_timeout` | `float` | `120.0` | Max seconds to wait for readiness |

### Running Commands

```python
# Shell string -> runs through /bin/sh -c
sbx.run("pip install -q numpy && python -c 'import numpy; print(numpy.__version__)'")

# argv list -> exec'd directly (no shell)
sbx.run(["python", "-c", "import numpy; print(numpy.__version__)"])

# Explicit shell/argv mode
sbx.run("echo $HOME && ls | wc -l", shell=True)
sbx.run(["git", "commit", "-m", msg], shell=False)

# Live output streaming + env + cwd + timeout
sbx.run("make -j4", cwd="/app", env={"CC": "gcc"}, timeout=600,
    on_stdout=lambda line: print(f"[OUT] {line}"),
    on_stderr=lambda line: print(f"[ERR] {line}"),
)

# Non-zero exits -> SandboxCommandError
result = sbx.run("exit 1", check=False)
print(result.exit_code, result.stdout, result.stderr)

# Background processes
bg = sbx.run("python -m http.server 8080", background=True)
sbx.processes()
bg.kill()

# stdin
sbx.run("sort -n", input=b"3\n1\n2\n")
```

### File Operations

```python
sbx.files.write("/app/script.py", "print('hello')")
content = sbx.files.read("/app/script.py")
sbx.files.delete("/app/script.py")
sbx.files.write("/app/data/file.txt", b"...")
sbx.files.list("/app/")
```

### Port Proxying (proxy_url_for)

```python
sbx.run("python -m http.server 8080", background=True)
url = sbx.proxy_url_for(port=8080, path="/", scheme="https://")
# -> https://<job_id>--8080.hf.jobs/v1/.../proxy/8080/
```

Protocol-agnostic: use `scheme="wss://"` for WebSocket.

Pool sandbox caveat: Pool sandboxes cannot bind TCP ports (Landlock). Use Unix socket instead.

### Lifecycle & Reconnection

```python
with Sandbox.create() as sbx:
    ...

# Manual lifecycle
sbx = Sandbox.create()
sbx.run("python train.py")
sbx.close()       # release local HTTP client (no terminate)
sbx.kill()        # terminate

# Reconnect from anywhere
sbx = Sandbox.connect(sandbox_id="<id>", namespace="<user>")
```

### SandboxPool -- Shared CPU Sandboxes

```python
from huggingface_hub import SandboxPool

with SandboxPool(image="python:3.12", max_size=10) as pool:
    sbx = pool.get_sandbox()
    result = sbx.run("python task.py")
    sbx.return_to_pool()

    with pool.get_sandbox() as sbx:
        result = sbx.run("python task.py")

    results = pool.map(my_func, [1, 2, 3, 4, 5])
```

Pool characteristics:
- max_size: max concurrent sandboxes (default 10)
- CPU-only (cpu-basic flavor)
- uid + Landlock isolation
- First host ~6s, then ~1 RTT per sandbox
- Auto-scale hosts

### CLI Commands (hf sandbox)

```bash
hf sandbox create --image python:3.12 --flavor cpu-basic
hf sandbox exec <id> -- python -c "print('hi')"
hf sandbox cp data.csv <id>:/data/data.csv
hf sandbox cp <id>:/output/results.csv ./results.csv
hf sandbox ls
hf sandbox kill <id>
hf sandbox spawn <id> -- python server.py
hf sandbox logs <id>
```

### Cost & Zero-Cost

**Sandboxes require billing.** Built on Jobs which require HF Pro/billing:
- Free-tier accounts cannot create sandboxes
- `idle_timeout` (default 10 min) is primary cost control
- Zero-cost alt: Spaces persistent storage + Gradio/Streamlit; local VMs

### Bonus: Space Templates (v1.23.0)

Seed Spaces from templates:

```bash
hf spaces templates
# NAME        REPO_ID                             SDK     PREFERRED_PRIVATE
# Streamlit   streamlit/streamlit-template-space  docker
# JupyterLab  SpacesExamples/jupyterlab           docker  Yes

hf repos create my-jupyterlab --type space --template jupyterlab
```

```python
create_repo("my-jupyterlab", repo_type="space", space_template="jupyterlab")
```

- Templates: JupyterLab, Streamlit chatbot, Gradio chatbot, more
- SDK inferred from template
- PREFERRED_PRIVATE templates default private

### Bonus: Tree Cache (v1.22.0)

snapshot_download caches repo file listing in `trees/` folder:
- Cached commit costs 1 network call (branch->hash resolve)
- Skips per-file HEAD for Xet files
- Raises `IncompleteSnapshotError` on cache miss + network failure

### Bonus: Named Jobs (v1.24.0)

```bash
hf jobs run --name training-v2 python:3.12 python train.py
hf jobs labels <job_id> --name training-v2
hf jobs scheduled run @hourly --name hourly-task python:3.12 python -c 'print("hello")'
```

```python
run_job("python:3.12", command="python train.py", name="training-v2")
create_scheduled_job("@hourly", "python:3.12", "python task.py", name="hourly-task")
```

Names optional, stored as `name` label, shown in UI.

### Resources
- Sandbox guide: https://huggingface.co/docs/huggingface_hub/main/en/guides/sandbox
- Sandbox reference: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/sandbox
- Jobs reference: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/jobs
- v1.22.0 release (Sandboxes, Tree Cache, CLI rebuild): https://github.com/huggingface/huggingface_hub/releases/tag/v1.22.0
- v1.23.0 release (Space Templates): https://github.com/huggingface/huggingface_hub/releases/tag/v1.23.0
- v1.24.0 release (Named Jobs): https://github.com/huggingface/huggingface_hub/releases/tag/v1.24.0
- CLI guide: https://huggingface.co/docs/huggingface_hub/main/en/guides/cli
- Spaces docs: https://huggingface.co/docs/hub/en/spaces

### Skill
mlops/huggingface-hub -- references/hf-learnings.md

---

## 2026-07-24: hf-hub-organization-management-api — Managing Organizations, Members, Repos, and Teams (Topic #150)

### Summary
Comprehensive deep-dive into the Hugging Face Hub Organization Management ecosystem — covering the Python SDK (`huggingface_hub` `HfApi`) methods, REST API endpoints, data models (`Organization`, `User`), repo lifecycle under org namespaces, resource groups (Enterprise), and the web UI management interface. Built entirely from source code analysis of `huggingface_hub` v1.24.0.

### Core Architecture

Organizations on the Hugging Face Hub are **namespace containers** that own models, datasets, Spaces, and buckets. They provide:
- **Shared ownership** — repos belong to the org, not any individual
- **Role-based access** — members have reader/writer/admin roles
- **Resource groups** (Enterprise) — granular access control within an org
- **Team plan** — paid tier with additional features (private repos, higher rate limits)
- **Verification** — verified badge for official orgs

API endpoint base: `https://huggingface.co/api/organizations/{organization}`

### Python SDK Methods

| Method | Description | REST Endpoint |
|--------|-------------|---------------|
| `get_organization_overview(org)` | Org profile (name, members, counts) | `GET /api/organizations/{org}/overview` |
| `list_organization_members(org)` | Paginated member roster | `GET /api/organizations/{org}/members` |
| `list_organization_followers(org)` | Paginated follower list | `GET /api/organizations/{org}/followers` |
| `whoami()` | Auth user info including org roles | `GET /api/whoami-v2` |
| `create_repo("org/repo")` | Create repo under org | `POST /api/repos/create` |
| `move_repo(from_id, to_id)` | Transfer across namespaces | `POST /api/repos/move` |
| `duplicate_repo(from_id, to_id)` | Server-side copy | `POST /api/repos/duplicate` |
| `delete_repo("org/repo")` | Delete repo (irreversible) | `DELETE /api/repos/delete` |
| `update_repo_settings()` | Change visibility/gating | `POST /api/repos/{repo}/settings` |
| `list_user_repos(namespace=org)` | List all org repos with storage info | `GET /api/organizations/{org}/settings/repositories` |

### Key Takeaways

1. **Three org-read methods** exist in the SDK: `get_organization_overview()`, `list_organization_members()`, and `list_organization_followers()` — all pull from the `huggingface_hub` REST API
2. **No SDK for creating orgs or managing members** — these are web UI only (https://huggingface.co/settings/organizations)
3. **Repo management under orgs** uses the same SDK methods as user repos, just with `org/repo` notation — `create_repo`, `move_repo`, `duplicate_repo`, `delete_repo`, `update_repo_settings`
4. **`whoami()` with `cache=True`** is the way to check your role in an org — role info is not exposed via `get_organization_overview()`
5. **Resource groups** provide Enterprise-only fine-grained access control within orgs
6. **Org names must be globally unique** — they share the namespace with usernames
7. **Member roles** (admin/write/read) control what you can do with repo operations under an org namespace

### Data Models

**Organization** fields: avatar_url, name, fullname, details, is_verified, is_following, num_users, num_models, num_spaces, num_datasets, num_followers, num_papers, plan

**User** fields: username, fullname, avatar_url, details, is_following, is_pro, num_models, num_datasets, num_spaces, num_discussions, num_papers, num_upvotes, orgs

### Limitations
- No SDK for member invite/remove/role-change
- No API for creating orgs
- `num_users` can be stale
- Role info only via `whoami()`, not org overview
- Resource groups are Enterprise-only
- Creating repos under org requires write+ role

### Source
Direct from `huggingface_hub` v1.24.0 source code analysis:
- `/opt/data/.venv-sakthai/lib/python3.14/site-packages/huggingface_hub/hf_api.py`

### Resources
- [Hub Organizations Docs](https://huggingface.co/docs/hub/en/organizations)
- [Hugging Face Account Settings (Orgs)](https://huggingface.co/settings/organizations)
- [huggingface_hub API Reference: HfApi](https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api)
