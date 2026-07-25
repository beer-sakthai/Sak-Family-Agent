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
|       └── DDUFExportError

## 2026-07-24: hf-hub-sandboxes-deep-dive — HF Sandboxes: Ephemeral Cloud Machines via `huggingface_hub` (Topic #148 Deepened)

### Summary
Deep-dive into **HF Sandboxes** — isolated cloud machines you spin up in seconds, run commands in with live-streamed output, and transfer files in/out of — all from Python (`huggingface_hub` v1.24.0+) or the CLI (`hf sandbox`). Sandboxes are built on top of HF Jobs: a sandbox is a Job running a small static binary (`sbx-server`) that exposes command execution and file transfer over HTTP. Available in two flavors: **dedicated** (one Job = one VM, supports GPU) and **pooled** (one Job hosts many sandboxes via uid + Landlock isolation, CPU only). Covered: architecture, API reference, CLI usage, pooling model, security model, file API, proxy/forwarding, and performance benchmarks.

### Key Concepts

**No dedicated sandbox backend.** A sandbox is just an HF Job (VM) running a single static Rust binary `sbx-server` (~640KB, zero deps) that speaks HTTP. The client talks to it through the Jobs proxy (`*.hf.jobs` URL). Everything — auth, discovery, packing — builds on existing Job primitives (labels, env vars, secrets).

### The Two Kinds of Sandbox

| Aspect | `Sandbox.create()` (dedicated) | `SandboxPool` (shared/pool) |
|--------|-------------------------------|-----------------------------|
| Mapping | 1 Job = 1 sandbox (whole VM) | 1 Job = many sandboxes (same VM, packed) |
| Isolation | Full VM | uid + Landlock (same-user trust) |
| Cold start | ~6s per sandbox | ~6s first host, then ~1 round-trip each |
| Cost | 1 VM per sandbox | 1 VM per host, amortized |
| GPU | ✅ | ❌ (CPU only) |
| Best for | Single sandbox, GPU workloads, untrusted code | Many cheap CPU sandboxes (RL rollouts, fan-out) |

### Quickstart (Python)

```python
from huggingface_hub import Sandbox

# Dedicated sandbox
with Sandbox.create() as sbx:
    result = sbx.run("python -c 'print(40 + 2)'")
    print(result.stdout)  # 42

# Custom image and GPU flavor
sbx = Sandbox.create(image="pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel", flavor="a10g-small")
```

### Running Commands: `Sandbox.run()`

- **String** → runs through `/bin/sh -c` (supports pipes, globs, `$VARS`)
- **List** → exec'd directly as argv (no quoting surprises)
- `shell=True/False` to force mode explicitly (avoids footgun of `["echo hi"]` being exec'd as a single program named "echo hi")
- Non-zero exit raises `SandboxCommandError` by default; pass `check=False` to get `SandboxCommandResult` instead
- `background=True` starts a process detached, returns `SandboxProcess` immediately (for servers/watchers)

```python
# Live streaming output
sbx.run("make -j4", cwd="/app", env={"CC": "gcc"}, timeout=600,
        on_stdout=print, on_stderr=print)

# Background server
proc = sbx.run("python -m http.server 8000", background=True)
# Later: sbx.processes() → list, proc.kill() → terminate
```

### File Transfer

```python
# Write/read
sbx.files.write("/app/script.py", "print('hi')")
text = sbx.files.read_text("/app/script.py")

# Upload/download (local ↔ sandbox)
sbx.files.upload("local_data.csv", "/data/data.csv")
sbx.files.download("/data/results.bin", "results.bin")

# List/stat
entries = sbx.files.list("/data")
# Also: stat, exists, mkdir, delete
```

### Proxy: Reaching an Inner Server

Start a server in the sandbox (background), then reach it from outside:

```python
import httpx
with Sandbox.create() as sbx:
    sbx.files.write("app.py", "...")
    sbx.run("uvicorn app:app --host 127.0.0.1 --port 8000", background=True)
    
    # Plain HTTP
    r = httpx.get(sbx.proxy_url_for(8000, "/hello"), headers=sbx.proxy_headers)
    
    # WebSocket
    ws_url = sbx.proxy_url_for(8000, "/ws", scheme="wss://")
```

**Pooled sandbox note:** Can't bind TCP (Landlock), so listen on unix socket at `$SBX_PROXY_DIR/<port>.sock`:
```python
# Inside sandbox: uvicorn app:app --uds $SBX_PROXY_DIR/8000.sock
# Client side (proxy_url_for / proxy_headers) is identical
```

### Lifecycle

- **Persistent:** outlives the creating process — reconnect from anywhere with `Sandbox.connect("687f911eaea852de79c4a50a")`
- **`idle_timeout`:** default 10 min auto-shutdown when no API calls or running processes; pass `None` to disable
- **24h hard limit:** maximum job lifetime (not configurable)
- **`forward_hf_token=True`:** opt-in to inject HF_TOKEN into the sandbox (never sent by default)

### Pooled Sandboxes: `SandboxPool`

For many parallel CPU sandboxes (RL rollouts, batch eval, fan-out):

```python
from huggingface_hub import SandboxPool
from concurrent.futures import ThreadPoolExecutor

with SandboxPool(image="python:3.12", flavor="cpu-basic", warm_up=4) as pool:
    boxes = [pool.create() for _ in tasks]
    with ThreadPoolExecutor(32) as ex:
        outputs = list(ex.map(lambda b, t: b.run(t.cmd).stdout, boxes, tasks))
```

Key pooling parameters:
- `sandboxes_per_host`: default 50 sandboxes per host VM
- `warm_up`: pre-provision N hosts (avoids cold start on first calls)
- `max_hosts`: cap on concurrent host VMs
- Per-sandbox `env`, `idle_timeout`, `forward_hf_token` — but `image`/`flavor`/`volumes` are pool-level (set once)

Pool reconnection: `SandboxPool.connect("pool-ae9f7efe0bc7")` from any machine.

### Security & Authentication (Stateless HMAC)

Two-layer auth:
1. **Jobs proxy gate:** requires HF token with read access to the job's namespace
2. **Application gate (`X-Sandbox-Token`):** per-sandbox token derived as:
   ```
   nonce = random 128-bit hex  (stored in job label "hf-sandbox-nonce")
   token = HMAC-SHA256(key=your_hf_token, msg="hf-sandbox:" + nonce)
   ```

This means: stateless reconnection from anywhere (read nonce from label, recompute token), HF token never enters the sandbox (unless explicitly forwarded), and each sandbox has a unique token scope.

### Pool Isolation: uid + Landlock

- Each pooled sandbox gets: dedicated uid (≥20000), private `0700` home, `NO_NEW_PRIVS`, per-process rlimits, per-sandbox Landlock ruleset
- ✅ Cannot read other sandboxes' environ, /proc/*/environ, signal/ptrace, read 0700 homes
- ✅ /tmp and /dev/shm access denied (each confined to own home, TMPDIR inside $HOME)
- ✅ Cannot bind TCP ports (no inter-sandbox localhost services)
- ✅ Abstract unix sockets blocked (via `LANDLOCK_SCOPED_ABSTRACT_UNIX_SOCKET`)
- ⚠️ No cgroup delegation — CPU/RAM/disk not partitioned (RLIMIT_NPROC/RLIMIT_AS bound per-process)
- ⚠️ Can see process list metadata via /proc (names, cmdlines) — cannot read or signal

Use `Sandbox.create()` (full VM) for mutually-hostile untrusted code or GPU workloads.

### CLI Reference

```bash
# Dedicated
hf sandbox create
hf sandbox exec <id> -- python -c "print('hi')"
hf sandbox cp data.csv <id>:/data/data.csv
hf sandbox kill <id>

# Background processes
hf sandbox spawn <id> -- python -m http.server 8000
hf sandbox process ls <id>
hf sandbox process kill <id> <pid>

# Pool
hf sandbox pool create python:3.12 --flavor cpu-basic
hf sandbox create --pool <pool-id> --env LOG_LEVEL=debug
hf sandbox pool ls
hf sandbox pool delete <pool-id>
```

### Performance Benchmarks

**Dedicated:** cold start ~5.8s median, run() round-trip p50 ~110ms (proxy RTT floor ~105ms), file transfer ~340 MiB/s down, ~441 MiB/s up (parallel ranged, >8 MiB).

**Pool (50 sandboxes/host):** 100 sandboxes in ~6.1s total, 1000 sandboxes in ~16s total. Server-side create/exec/delete ~1ms each — budget is entirely network round-trip.

**Cost example:** 1000 sandboxes (20 hosts × 50 each) ≈ $0.0009 total vs ~$0.06 for one Job per sandbox (1000 VMs).

### Source
- https://huggingface.co/docs/huggingface_hub/en/guides/sandbox
- https://huggingface.co/docs/huggingface_hub/en/concepts/sandbox
- https://huggingface.co/docs/huggingface_hub/en/package_reference/sandbox
- Server binary: https://github.com/huggingface/sandbox-server
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
|- Env vars: https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables

---

## 2026-07-24: hf-inference-client-image-input-pipeline-deep-dive — Image Input Handling in InferenceClient (Topic #187)

### Summary
Source-code deep-dive into the `huggingface_hub` InferenceClient's complete image input pipeline. Covers the `ContentT` type union (7 accepted formats), the `_open_as_mime_bytes` normalization engine, encoding utilities (`_b64_encode`, `_as_url`, `_bytes_to_image`), the 8 task-specific image methods, provider-specific binary vs. JSON handling, and the multimodal chat completion pattern via OpenAI-compatible data URLs. All findings verified against `huggingface_hub` source code at `/opt/data/.venv-sakthai/lib/python3.14/site-packages/huggingface_hub/inference/`.

### Source
- huggingface_hub inference/_common.py: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_common.py
- huggingface_hub inference/_client.py: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_client.py
- huggingface_hub inference/_providers/hf_inference.py: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_providers/hf_inference.py

### 1. The ContentT Type System

The core type alias `ContentT` (in `_common.py` line 48) defines all 7 accepted image input formats:

```python
ContentT = Union[bytes, BinaryIO, PathT, UrlT, "Image", bytearray, memoryview]
# Where:
PathT = Union[str, Path]
UrlT  = str  # Must start with http:// or https:// (checked at runtime)
```

| # | Type | Example | Use Case |
|---|------|---------|----------|
| 1 | `bytes` | `open("img.jpg","rb").read()` | Raw file bytes in memory |
| 2 | `bytearray` | `bytearray(data)` | Mutable byte buffer |
| 3 | `memoryview` | `memoryview(data)` | Zero-copy buffer view |
| 4 | `BinaryIO` (duck-typed via `.read()`) | `open("img.jpg","rb")` | File-like stream objects |
| 5 | `str` (URL) | `"https://example.com/img.jpg"` | Remote image (auto-downloaded) |
| 6 | `str`/`Path` (local path) | `"img.jpg"` or `Path("img.jpg")` | Local file (auto-opened) |
| 7 | `PIL.Image.Image` | `Image.open("img.jpg")` | In-memory PIL Image object |

**Key insight:** The `str` type is ambiguous — checked at runtime: if it starts with `http://` or `https://` it's treated as a URL and downloaded; otherwise treated as a local file path.

### 2. The Normalization Engine: `_open_as_mime_bytes()`

This function (lines 126–189 in `_common.py`) converts any `ContentT` input to `MimeBytes` (bytes subclass with `.mime_type` attribute). Processing order (first-match wins):

```
Input
├── None → return None
├── bytes → MimeBytes(content) [no mime type]
├── bytearray/memoryview → MimeBytes(bytes(content)) [no mime type]
├── duck-type .read() → MimeBytes(f.read(), mime=guess_type(f.name))
│   (raises TypeError if .read() returns str instead of bytes)
├── str starting with http:// or https:// → HTTP GET download
│   → MimeBytes(response.content, mime=Content-Type header or guess)
├── str (not URL) → treated as Path; raises FileNotFoundError if missing
├── Path → MimeBytes(path.read_bytes(), mime=guess_type(path))
├── PIL.Image.Image → save to BytesIO (format preserved, default PNG)
│   → MimeBytes(buffer.getvalue(), mime=f"image/{fmt.lower()}")
└── Any other type → TypeError
```

**MimeType detection priority:** BinaryIO→`.name` attribute guess, URL→HTTP Content-Type header, Path→file extension guess, PIL image→format metadata, raw bytes→None.

### 3. Encoding Utilities

| Function | Input | Output | Used By |
|----------|-------|--------|---------|
| `_b64_encode(content) → str` | Any ContentT | Base64 string (no prefix) | `document_qa()`, `visual_qa()` — embeds image in JSON body |
| `_as_url(content, default_mime) → str` | Any ContentT | `data:{mime};base64,{data}` data URL | Chat completion multimodal content parts |
| `_bytes_to_image(content) → Image` | Raw bytes | PIL.Image | `text_to_image()`, `image_to_image()`, `image_to_video()` |
| `_b64_to_image(str) → Image` | Base64 string | PIL.Image | Client-side post-processing |

**`_as_url` shortcut:** URLs starting with `http://`, `https://`, or `data:` pass through unchanged — no re-encoding.

### 4. Image Methods on InferenceClient

All 8 image methods in `_client.py` accept `image: ContentT`:

| Method | Line | Returns | API Task |
|--------|------|---------|----------|
| `image_classification()` | 1163 | `list[ImageClassificationOutputElement]` | image-classification |
| `image_segmentation()` | 1213 | `list[ImageSegmentationOutputElement]` | image-segmentation |
| `image_to_image()` | 1281 | `Image` (PIL) | image-to-image |
| `image_to_video()` | 1357 | `bytes` | image-to-video |
| `image_to_text()` | 1436 | `ImageToTextOutput` | image-to-text |
| `object_detection()` | 1482 | `list[ObjectDetectionOutputElement]` | object-detection |
| `text_to_image()` | 2439 | `Image` (PIL) | text-to-image (no image input) |
| `visual_question_answering()` | 3048 | `list[VisualQuestionAnsweringOutputElement]` | visual-question-answering |
| `zero_shot_image_classification()` | 3210 | `list[ZeroShotImageClassificationOutputElement]` | zero-shot-image-classification |

`document_question_answering()` (line 937) also accepts `image: ContentT` and always passes `{"question": ..., "image": _b64_encode(image)}`.

### 5. Provider-Specific Image Handling

**`HFInferenceTask`** (JSON-based): For text tasks — raises `ValueError` on binary inputs.

**`HFInferenceBinaryInputTask`** (binary-capable, lines 72–101):
- **No parameters** → raw bytes via `_open_as_mime_bytes(inputs)` with auto-detected MIME
- **With parameters** → base64 in JSON: `{"inputs": _b64_encode(inputs), "parameters": ...}`

### 6. Chat Completion Multimodal Pattern

`chat_completion()` does NOT accept `ContentT` for images — users provide pre-encoded URLs:
```python
messages = [{"role": "user", "content": [
    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
    {"type": "text", "text": "Describe this image."},
]}]
```

### 7. Key Architectural Insights

1. **Dual pathway:** Every image method supports raw binary (no parameters, minimal overhead) or b64 JSON (with parameters, +33% size).
2. **Lazy PIL import:** Only needed when passing PIL Image objects or receiving image output. Bytes/URLs/Paths work without PIL.
3. **String ambiguity risk:** A plain string is always treated as a path first — can cause confusing `FileNotFoundError`.
4. **Chat completion gap:** Unlike task methods, `chat_completion()` has no `ContentT` convenience — users must encode manually.
5. **BinaryIO duck-typing:** Matches any `.read()` object — including text streams (raises `TypeError` at runtime).

### 8. Zero-Cost Patterns

```python
from huggingface_hub import InferenceClient
client = InferenceClient()  # free tier

# Classification — auto-selects HF's recommended free model
result = client.image_classification("cat.jpg")

# Captioning — free via recommended model
caption = client.image_to_text("https://example.com/photo.jpg")

# VQA — specify a free model explicitly
answers = client.visual_question_answering(
    image="scene.jpg",
    question="How many people?",
    model="google/vit-base-patch16-224",
)
```

### References
- `_common.py`: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_common.py
- `_client.py`: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_client.py
- `hf_inference.py` provider: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_providers/hf_inference.py
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


---

## 2026-07-24: hf-hub-xet-storage-and-hf-xet — Xet Storage & hf_xet Rust Accelerator Deep Dive (Topic #154)

### Summary
Deep-dive into Xet storage, the Rust-based content-addressable storage system powering the Hugging Face Hub, and its Python client `hf_xet`. Covers the architecture (chunk-level deduplication, XORBs, CAS), the replacement of `hf_transfer` with `hf_xet`, the token refresh system, cache optimization via tree listing, and configuration via env vars. Sources: huggingface_hub v1.24.0 source code analysis and HF Hub Xet docs.

### Architecture Overview

Xet is a **content-addressable storage (CAS)** system built specifically for AI/ML development on the Hugging Face Hub. It replaces the older Git LFS-based storage backend.

**Key differences from Git LFS:**
- **Chunk-level deduplication** — identical chunks across different files stored only once (not possible with LFS's file-level storage)
- **Smaller uploads** — only new/changed chunks are transferred
- **Faster downloads** — parallel chunk retrieval with presigned URLs
- **Immutable chunks (XORBs)** — broken into blocks called xorbs, reassembled on request

### Architecture Flow

1. Files are broken into immutable chunks (xorbs)
2. Chunks are stored in the content-addressable service (CAS)
3. LFS SHA256 hash -> reconstruction metadata (ranges within xorbs + presigned URLs)
4. `hf_xet` downloads xorb ranges in parallel and writes files to disk
5. Short-lived Xet access tokens are refreshed automatically via the refresh API

### hf_xet Python Package

| Property | Value |
|----------|-------|
| Package name | hf-xet (pip), imported as hf_xet |
| Current version | 1.5.2 (installed in this env) |
| Purpose | Rust-based download/upload accelerator for the HF Hub |
| Relationship to hf_transfer | hf_transfer is DEPRECATED - use hf_xet instead |
| Bundled with | huggingface_hub >= 0.32.0 (automatically installed) |
| Summary | Fast transfer of large files with the Hugging Face Hub |

### How hf_xet Integrates with huggingface_hub

**Runtime detection** - `_runtime.py` checks for `hf_xet` package at import time via `is_xet_available()`.

**Download flow** - `file_download.py` contains the `xet_get()` function.

**XetFileData dataclass** - `utils/_xet.py`:
- `file_hash` (str): Xet content hash for file identification in CAS
- `refresh_route` (str): URL to refresh the short-lived Xet access token

**Token refresh URL format:**
```
{ENDPOINT}/api/{repo_type}s/{repo_id}/xet-{read|write}-token/{revision}
```

**XetTokenType enum:** READ / WRITE

**XetSessionHolder** - thread-safe session management for free-threaded Python (3.14t):
- Uses threading.Lock for thread safety
- Supports safe re-creation after sigint_abort() or fork
- Automatically refreshes tokens as needed

### Cache Optimization - Tree Listing

When Xet is enabled, the Hub API's /tree listing response includes Xet metadata (xet_hash, lfs_sha256, lfs_size). This allows hf_xet to skip the HEAD request that regular downloads need, since Xet downloads don't rely on the /resolve redirect.

### Configuration

| Env Variable | Purpose |
|-------------|---------|
| HF_HUB_DISABLE_XET | Set to disable Xet even if hf_xet is installed |
| (default) | Xet enabled by default when hf_xet package is available |

### Zero-Cost Relevance

Xet storage and hf_xet are free for all Hub users - no paid tier required. For Beer's zero-cost setup:
- hf_xet is already bundled with huggingface_hub v1.24.0
- Faster downloads save time on model/dataset downloads without any cost
- Chunk-level deduplication means the Hub stores less data overall

### Resources
- HF Hub Download Guide (https://huggingface.co/docs/huggingface_hub/en/guides/download)
- Xet Hub Documentation (https://huggingface.co/docs/hub/xet/index)
- huggingface_hub utils/_xet.py on GitHub
- hf_xet PyPI package: hf-xet

---

## 2026-07-24: hf-hub-webhooks-and-notifications-api-deep-dive — Webhooks, Notifications & User Settings API (Topic #163)

### Summary
Deep-dive into the Hugging Face Hub's user-facing API surface covering three areas: **Webhooks** (event-driven repo notifications to external URLs/Jobs), **Notifications** (in-Hub alerts for discussions, PRs, mentions), and **User Settings** (notification prefs, watch settings, MCP tools config, billing/usage, repository list, webhook CRUD). All accessible via the `huggingface_hub` Python library (v1.24.0) methods and the Hub REST API (documented in OpenAPI spec).

---

### 1. Webhooks API — Event-Driven Automation

Webhooks send HTTP POST requests to a specified URL (or trigger a Hub Job) when events happen on watched repos (pushes, discussion activity, PR merges). This is the Hub's primary automation mechanism — zero-cost, no server needed.

#### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/settings/webhooks` | List all webhooks |
| POST | `/api/settings/webhooks` | Create webhook |
| GET | `/api/settings/webhooks/{webhookId}` | Get webhook details |
| POST | `/api/settings/webhooks/{webhookId}` | Update webhook |
| DELETE | `/api/settings/webhooks/{webhookId}` | Delete webhook |
| POST | `/api/settings/webhooks/{webhookId}/{action}` | `enable` or `disable` |
| POST | `/api/settings/webhooks/{webhookId}/replay/{logId}` | Replay a webhook delivery |

#### Python API (`HfApi` methods)

```python
from huggingface_hub import HfApi

api = HfApi()

# List
webhooks: list[WebhookInfo] = api.list_webhooks()

# Create (URL-based)
api.create_webhook(
    url="https://my-server.example.com/hf-webhook",
    watched=[{"type": "user", "name": "beer-sakthai"}],
    domains=["repo", "discussions"],
    secret="my-webhook-secret",
)

# Create (Job-based) — triggers a Hub Job instead of HTTP POST
api.create_webhook(
    job_id="job-id-from-hf-jobs",
    watched=[{"type": "model", "name": "mistralai/Mistral-7B-v0.1"}],
    domains=["repo"],
)

# Update
api.update_webhook(
    webhook_id="abc123",
    url="https://new-url.example.com/hook",
    watched=[{"type": "org", "name": "huggingface"}],
)

# Enable/Disable
api.enable_webhook("abc123")
api.disable_webhook("abc123")

# Delete
api.delete_webhook("abc123")
```

#### Data Models

**`WebhookInfo`** (dataclass):
| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique webhook ID |
| `url` | `str | None` | HTTP endpoint URL (or None if Job-based) |
| `job` | `JobSpec | None` | Job specification (or None if URL-based) |
| `watched` | `list[WebhookWatchedItem]` | Repos/users/orgs being watched |
| `domains` | `list[WEBHOOK_DOMAIN_T]` | Event domains: `"repo"`, `"discussions"` |
| `secret` | `str | None` | HMAC secret for signature verification |
| `disabled` | `bool` | Whether webhook is inactive |

**`WebhookWatchedItem`** (dataclass):
| Field | Type | Description |
|-------|------|-------------|
| `type` | `Literal["dataset", "model", "org", "space", "user"]` | Entity type to watch |
| `name` | `str` | Entity name (repo ID, org name, username) |

**`WEBHOOK_DOMAIN_T`** = `Literal["repo", "discussions"]`
- `"repo"` — pushes, branch/tag changes, file modifications
- `"discussions"` — new comments, PR merges, discussion status changes

#### Webhook Secret Verification

When a secret is set, each webhook POST includes an `X-Webhook-Signature` header with an HMAC-SHA256 signature of the request body, using the secret as the key. Verify on your server:

```python
import hmac, hashlib

def verify_webhook_signature(body: bytes, secret: str, signature_header: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)
```

#### Best Practices
- **Use Job-based triggers** for Hub-native workflows (no external server needed).
- **Set a secret** to verify payload authenticity.
- **Watch org-level** to cover all repos in an org.
- **Use `domains=["repo"]`** for file-change automation (CI/CD pipelines).
- **Use `domains=["discussions"]`** for community/moderation bots.
- **Monitor webhook logs** via the Hub UI (`Settings > Webhooks > {hook} > Logs`).

---

### 2. Notifications API — In-Hub Alerts

The Notifications API manages the bell icon alerts on the Hub (discussion replies, PR merges, mentions, access requests).

#### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications` | List notifications (paginated, filterable) |
| POST | `/api/notifications/mark-as-read` | Mark notifications as read |
| DELETE | `/api/notifications` | Delete notifications |

#### GET `/api/notifications` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `p` | `int` | `0` | Page number (0-indexed) |
| `readStatus` | `"all" \| "unread"` | `"all"` | Filter by read status |
| `repoType` | enum | — | Filter by repo type (`dataset`, `model`, `space`, `bucket`, `kernel`) |
| `repoName` | `string` | — | Filter by repo name |
| `postAuthor` | `string` | — | Filter by notification author |
| `paperId` | `string` | — | Filter by paper |
| `articleId` | `string` | — | Filter by article |
| `mention` | `"all" \| "participating" \| "mentions"` | `"all"` | Filter by mention/participation type |
| `lastUpdate` | `datetime` (ISO 8601) | — | Filter by last update timestamp (regex-validated) |

#### DELETE Parameters (same as GET, plus:)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `applyToAll` | `bool` | `False` | If true, deletes all matching notifications instead of just the current page |

#### Usage Pattern (Python)

```python
import requests

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# List unread notifications
resp = requests.get(
    "https://huggingface.co/api/notifications",
    params={"readStatus": "unread", "p": 0},
    headers=headers,
)
notifications = resp.json()

# Mark as read
requests.post(
    "https://huggingface.co/api/notifications/mark-as-read",
    json={"ids": [n["id"] for n in notifications]},
    headers=headers,
)

# Delete all repo-type notifications
requests.delete(
    "https://huggingface.co/api/notifications",
    params={"repoType": "model", "applyToAll": True},
    headers=headers,
)
```

> **Note:** The `huggingface_hub` library does NOT yet expose notification-specific methods. Use direct `requests` or `HfApi._inner_whoami` for now.

---

### 3. User Settings API

Settings endpoints manage user preferences, billing/usage, webhooks, MCP tools, and repository listings.

#### Endpoint Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/whoami-v2` | Current user + auth info |
| GET | `/api/settings/repositories` | List user repos (with search, type filter, sort) |
| PATCH | `/api/settings/notifications` | Update notification preferences |
| PATCH | `/api/settings/watch` | Update auto-watch settings |
| GET | `/api/settings/mcp` | Get user's MCP tools configuration |
| GET | `/api/settings/webhooks` | List webhooks (also under Webhooks) |
| POST | `/api/settings/papers/claim` | Claim paper authorship |
| GET | `/api/settings/billing/usage` | Get usage stats |
| GET | `/api/settings/billing/usage-v2` | Get usage stats (v2) |
| GET | `/api/settings/billing/usage-by-inference-session` | Per-session usage |
| GET | `/api/settings/billing/usage/jobs` | Jobs usage |
| GET | `/api/settings/billing/usage/live` | Stream usage (SSE) |
| GET | `/api/settings/webhooks/{webhookId}/replay/{logId}` | Replay webhook delivery |

#### `GET /api/settings/repositories` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `search` | `string` | — | Case-insensitive substring match on repo name |
| `type` | enum | — | Filter by type: `dataset`, `model`, `space`, `bucket`, `kernel` |
| `limit` | `int` | — | Max results |
| `sort` | `"storage" \| "updatedAt"` | `"storage"` | Sort field |
| `direction` | `"asc" \| "desc"` | `"desc"` | Sort direction |

#### User Profile & Identity Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/whoami-v2` | Full user info + auth method + token details |
| GET | `/oauth/userinfo` | OAuth user info (OpenID Connect) |
| GET | `/api/users/{username}/overview` | Public user overview page data |
| GET | `/api/users/{username}/likes` | User's liked repos |
| GET | `/api/users/{username}/socials` | User's social links |
| GET | `/api/users/{username}/avatar` | User avatar URL |
| GET | `/api/avatars/{namespace}` | Generic avatar endpoint |

#### `whoami()` Python Method

```python
from huggingface_hub import HfApi

api = HfApi()
me = api.whoami()
# Returns dict with keys:
# - id: str (MongoDB ObjectId hex)
# - name: str
# - fullname: str
# - email: str
# - canPay: bool
# - isPro: bool
# - isStaff: bool
# - avatarUrl: str
# - orgs: list of org memberships
# - auth: dict (token info, role, fine-grained permissions)

# Cached variant (avoids redundant API calls in-session)
me_cached = api.whoami(cache=True)
```

#### `update_repo_settings()` — Repo-Level Settings

```python
# Change gated access, visibility, or privacy on a repo
api.update_repo_settings(
    repo_id="beer-sakthai/my-model",
    gated="auto",       # "auto" | "manual" | False
    private=False,      # bool
    visibility="public",  # "public" | "private"
)
```

---

### 4. Organization Settings API

Organizations have their own settings surface area, managed via the Hub REST API.

#### Endpoint Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/organizations/{name}/members` | List members |
| PUT | `/api/organizations/{name}/members/{username}/role` | Change member role |
| GET | `/api/organizations/{name}/settings/network-security` | Get network security rules |
| PATCH | `/api/organizations/{name}/settings/network-security` | Update network security |
| GET | `/api/organizations/{name}/settings/repositories` | List org repos |
| POST | `/api/organizations/{name}/settings/tokens/revoke` | Revoke member token |
| GET | `/api/organizations/{name}/audit-log/export` | Export audit log |
| GET | `/api/organizations/{name}/avatar` | Get avatar |
| POST | `/api/organizations/{name}/resource-groups` | Create resource group |
| GET/PATCH/DELETE | `/api/organizations/{name}/resource-groups/{id}` | Manage resource groups |
| POST | `/api/organizations/{name}/resource-groups/{id}/users` | Add users to resource group |
| PATCH/DELETE | `/api/organizations/{name}/resource-groups/{id}/users/{username}` | Manage user in resource group |
| GET | `/api/organizations/{name}/service-accounts` | List service accounts |
| POST | `/api/organizations/{name}/service-accounts` | Create service account |
| GET/DELETE | `/api/organizations/{name}/service-accounts/{id}` | Get/delete service account |
| POST | `/api/organizations/{name}/service-accounts/{id}/tokens` | Create SA token |
| PATCH/DELETE | `/api/organizations/{name}/service-accounts/{id}/tokens/{tokenId}` | Manage SA token |
| POST | `/api/organizations/{name}/service-accounts/{id}/tokens/{tokenId}/rotate` | Rotate SA token |
| GET | `/api/organizations/{name}/socials` | Get social handles |
| GET | `/api/organizations/{name}/billing/usage` | Get org usage |
| GET | `/api/organizations/{name}/billing/usage-v2` | Get org usage v2 |
| GET | `/api/organizations/{name}/billing/usage-by-inference-session` | Per-session usage |
| GET | `/api/organizations/{name}/billing/usage-by-resource-group` | Per-resource-group usage |
| GET | `/api/organizations/{name}/billing/usage/live` | Stream org usage |

---

### 5. Token & Auth Details

The `whoami-v2` response includes a detailed `auth` object:

```json
{
  "auth": {
    "type": "access-token",
    "accessToken": {
      "displayName": "my-token-name",
      "role": "write",
      "fineGrained": {
        "scoped": [{
          "entity": {
            "_id": "abc123def456...",
            "name": "beer-sakthai",
            "type": "user"
          },
          "permissions": ["write"]
        }]
      }
    }
  }
}
```

**Token roles:** `read`, `write`, `god`, `fineGrained`
- `fineGrained` tokens have scoped permissions with per-entity type (dataset, model, space, bucket, kernel, collection, org, user, resource-group, oauth app) and per-repo granularity.

---

### 6. Zero-Cost Relevance

- **Webhooks are free** — no paid tier required for webhook creation or delivery.
- **Notifications API is free** — accessible with any valid HF token.
- **Settings & whoami API is free** — no usage limits documented.
- **Org management API is free** for public orgs; some Enterprise features (SCIM, audit log, network security) may require Enterprise plan.
- **Usage/billing endpoints** are read-only and free — useful for monitoring consumption without cost.
- **Resource Groups** are an Enterprise feature (not zero-cost).

### Resources
- Hub Webhooks Guide: https://huggingface.co/docs/hub/en/webhooks
- huggingface_hub Webhooks API: `HfApi.list_webhooks()`, `create_webhook()`, etc.
- Hub OpenAPI spec: `/.well-known/openapi.json` (webhooks, notifications, settings sections)
- huggingface_hub `WebhookInfo`, `WebhookWatchedItem` dataclasses (v1.24.0+)
|- Hub Settings UI: https://huggingface.co/settings/webhooks

## 2026-07-24: hf-hub-api-rate-limiting-deep-dive — Complete Rate Limit System (Topic #167)

### Summary
Comprehensive guide to Hugging Face Hub rate limits — how the three-bucket system works, the IETF-standard RateLimit HTTP headers, per-plan quotas over 5-minute fixed windows, and best practices for avoiding 429 errors. Source: https://huggingface.co/docs/hub/en/rate-limits and live API response analysis.

### Three Rate Limit Buckets

The Hub enforces limits on three distinct classes of requests:

| Bucket | Description | Example Endpoints |
|--------|-------------|-------------------|
| **Hub APIs** | Programmatic API calls | `/api/models`, `/api/datasets`, repo creation, user management |
| **Resolvers** | File download URLs containing `/resolve/` | Model weight downloads via transformers, vLLM, llama.cpp, LM Studio |
| **Pages** | HTML web pages on huggingface.co | Human browsing traffic |

### Per-Plan Limits (all over 5-minute fixed windows)

| Plan | API | Resolvers | Pages |
|------|-----|-----------|-------|
| Anonymous (per IP) | 500* | 3,000* | 100* |
| Free user | 1,000* | 5,000* | 200* |
| PRO user | 2,500 | 12,000 | 400 |
| Team org | 3,000 | 20,000 | 400 |
| Enterprise org | 6,000 | 50,000 | 600 |
| Enterprise Plus org | 10,000 | 100,000 | 1,000 |
| Enterprise Plus (Org IP Ranges) | 100,000 | 500,000 | 10,000 |
| Academia Hub org | 3,000 | 20,000 | 400 |

*Anonymous and Free user limits are subject to change based on platform health.

**Important:** Organization limits apply to each member individually, not shared across members.

### HTTP Rate Limit Headers (IETF Draft Standard)

The HF Hub implements `draft-ietf-httpapi-ratelimit-headers` (Version 9). Two headers:

**`RateLimit`** — current status:
```
ratelimit: "api";r=499;t=37
```
- `"api"` (or `"resolvers"` / `"pages"`) — which bucket
- `r` — remaining requests in current window
- `t` — seconds until window reset

**`RateLimit-Policy`** — the policy definition:
```
ratelimit-policy: "fixed window";"api";q=500;w=300
```
- `"fixed window"` — algorithm type
- `q` — total allowed per window
- `w` — window duration in seconds (always 300 / 5 min)

### Live API Response Verified (this session)

```
HTTP/2 200
ratelimit: "api";r=499;t=37
ratelimit-policy: "fixed window";"api";q=500;w=300
```

Interpretation: 499 of 500 API calls remaining, 37s until next 5-minute window opens. This confirms the anonymous/free tier API limit of ~500/5min.

### Smart Retry in huggingface_hub (v1.2.0+)

The Python SDK includes automatic rate limit handling:
- On 429 error, SDK parses `RateLimit` header for the `t` (seconds remaining) value
- Waits exactly that duration before retrying
- Covers: file downloads (Resolvers) and paginated Hub API calls
- **Strongly recommended** over custom retry logic

```python
from huggingface_hub import HfApi
api = HfApi()
# SDK handles retries automatically on 429
models = api.list_models()  # paginated — auto-retried
```

### Billing Dashboard Monitoring

Rate limit status is visible in real-time at:
- https://huggingface.co/settings/billing

Three gauges (one per bucket) show:
- Current request count (last 5 minutes)
- Allowed request count
- Red bar when limit is exceeded

Context switcher lets you toggle between user account and orgs.

### What to Do When Rate-Limited (429)

1. **Pass a HF_TOKEN** — most common fix. Anonymous IP limits are lowest.
2. **Use Resolver endpoints instead of API calls** when possible (5x–10x higher limits)
3. **Spread requests** over longer periods (5-minute windows allow burstiness)
4. **Upgrade plan** to PRO (2.5x), Team (3x), or Enterprise (6x–200x)
5. **Use huggingface_hub** for automatic retry handling

### Granular User Action Limits

Separate from the three main buckets, specific actions have their own undocumented limits:
- Repo creation
- Repo commits/pushes
- Discussions and comments
- Moderation actions

These limits are not documented and change frequently. Contact support or upgrade for higher quotas.

### Key Differences: API vs Resolver

| Aspect | Hub API | Resolver |
|--------|---------|----------|
| Path pattern | `/api/...` | `/.../resolve/...` |
| Typical usage | Search, list, create repos | Download model files, tokenizer files |
| Free limit | 1,000/5min | 5,000/5min |
| Anonymous limit | 500/5min | 3,000/5min |
| Content served | JSON metadata | Binary blobs (safetensors, etc.) |

### Best Practices

- **Always authenticate** — anonymous limits are lowest and subject to change
- **Cache resolver results** — don't re-download model files repeatedly
- **Monitor billing dashboard** to catch approaching limits early
- **Use huggingface_hub** for all programmatic access to get free smart retry
- **Prefer Resolver over API** for high-throughput data access
- **Implement exponential backoff** as fallback if not using huggingface_hub
- **Check RateLimit header** on every response to anticipate window resets

### References
- Hub Rate Limits doc: https://huggingface.co/docs/hub/en/rate-limits
- Hub API Endpoints: https://huggingface.co/docs/hub/en/api
- OpenAPI spec: https://huggingface.co/.well-known/openapi.json
- Billing Dashboard: https://huggingface.co/settings/billing
- huggingface_hub: https://github.com/huggingface/huggingface_hub
- IETF RateLimit Headers: https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/

## 2026-07-24: hf-hub-hf_transfer-rust-download-accelerator-deep-dive — Topic #186

### Summary
Comprehensive deep-dive into `hf_transfer` — Hugging Face's Rust-based download/upload accelerator. Covers Rust implementation (PyO3+reqwest+tokio), parallel HTTP Range chunking, the `download()` and `multipart_upload()` functions, and — critically — its **deprecation** in favor of Xet (`HF_XET_HIGH_PERFORMANCE`). Research from source code at huggingface/hf_transfer and huggingface/huggingface_hub.

### Key Findings

1. **Architecture**: Rust native Python extension (PyO3 0.26), reqwest 0.12 HTTP/2, tokio 1.42 multi-threaded runtime, semaphore-based concurrency via `FuturesUnordered`.

2. **Download**: Splits files into configurable chunks, each fetched via HTTP `Range: bytes=start-stop`, writing directly to file with `seek`+`write_all`. Exponential backoff retry (base=300ms, jitter=random(0..500), cap=10s).

3. **Upload**: S3-style multipart upload with pre-signed URLs. Each chunk PUT with `FramedRead` streaming body. Returns part ETags for completion.

4. **⚠️ CRITICAL — Deprecated**: `hf_transfer` is no longer used in `huggingface_hub`. `HF_HUB_ENABLE_HF_TRANSFER` triggers `FutureWarning`. Replaced by `HF_XET_HIGH_PERFORMANCE=1` with the `hf_xet` package.

5. **Replacement (Xet)**: Content-addressed, deduplicated transfers via `hf_xet` Rust package. Provides `XetSession` for lifecycle management, fork-safe `XetSessionHolder`, and token-based auth at `/api/{repo_type}s/{repo_id}/xet-{read|write}-token/{revision}`.

6. **For zero-cost environments**: Standard `hf_hub_download()` handles caching, resumption, and progress bars transparently. The Rust accelerator is only relevant on very high-bandwidth (>500 MB/s) infrastructure.

### References
- hf_transfer: https://github.com/huggingface/hf_transfer
- huggingface_hub constants.py: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/constants.py
- huggingface_hub Xet utils: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/utils/_xet.py
- hf_transfer PyPI: https://pypi.org/pypi/hf_transfer/
- Xet docs: https://huggingface.co/docs/hub/en/xet
|- Env vars: https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables

---

## 2026-07-24: hf-inference-client-image-input-pipeline-deep-dive — Image Input Handling in InferenceClient (Topic #187)

### Summary
Source-code deep-dive into the `huggingface_hub` InferenceClient's complete image input pipeline. Covers the `ContentT` type union (7 accepted formats), the `_open_as_mime_bytes` normalization engine, encoding utilities (`_b64_encode`, `_as_url`, `_bytes_to_image`), the 8 task-specific image methods, provider-specific binary vs. JSON handling, and the multimodal chat completion pattern via OpenAI-compatible data URLs. All findings verified against `huggingface_hub` source code at `/opt/data/.venv-sakthai/lib/python3.14/site-packages/huggingface_hub/inference/`.

### Source
- huggingface_hub inference/_common.py: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_common.py
- huggingface_hub inference/_client.py: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_client.py
- huggingface_hub inference/_providers/hf_inference.py: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_providers/hf_inference.py

### 1. The ContentT Type System

The core type alias `ContentT` (in `_common.py` line 48) defines all 7 accepted image input formats:

```python
ContentT = Union[bytes, BinaryIO, PathT, UrlT, "Image", bytearray, memoryview]
# Where:
PathT = Union[str, Path]
UrlT  = str  # Must start with http:// or https:// (checked at runtime)
```

| # | Type | Example | Use Case |
|---|------|---------|----------|
| 1 | `bytes` | `open("img.jpg","rb").read()` | Raw file bytes in memory |
| 2 | `bytearray` | `bytearray(data)` | Mutable byte buffer |
| 3 | `memoryview` | `memoryview(data)` | Zero-copy buffer view |
| 4 | `BinaryIO` (duck-typed via `.read()`) | `open("img.jpg","rb")` | File-like stream objects |
| 5 | `str` (URL) | `"https://example.com/img.jpg"` | Remote image (auto-downloaded) |
| 6 | `str`/`Path` (local path) | `"img.jpg"` or `Path("img.jpg")` | Local file (auto-opened) |
| 7 | `PIL.Image.Image` | `Image.open("img.jpg")` | In-memory PIL Image object |

**Key insight:** The `str` type is ambiguous — checked at runtime: if it starts with `http://` or `https://` it's treated as a URL and downloaded; otherwise treated as a local file path.

### 2. The Normalization Engine: `_open_as_mime_bytes()`

This function (lines 126–189 in `_common.py`) converts any `ContentT` input to `MimeBytes` (bytes subclass with `.mime_type` attribute). Processing order (first-match wins):

```
Input
├── None → return None
├── bytes → MimeBytes(content) [no mime type]
├── bytearray/memoryview → MimeBytes(bytes(content)) [no mime type]
├── duck-type .read() → MimeBytes(f.read(), mime=guess_type(f.name))
│   (raises TypeError if .read() returns str instead of bytes)
├── str starting with http:// or https:// → HTTP GET download
│   → MimeBytes(response.content, mime=Content-Type header or guess)
├── str (not URL) → treated as Path; raises FileNotFoundError if missing
├── Path → MimeBytes(path.read_bytes(), mime=guess_type(path))
├── PIL.Image.Image → save to BytesIO (format preserved, default PNG)
│   → MimeBytes(buffer.getvalue(), mime=f"image/{fmt.lower()}")
└── Any other type → TypeError
```

**MimeType detection priority:** BinaryIO→`.name` attribute guess, URL→HTTP Content-Type header, Path→file extension guess, PIL image→format metadata, raw bytes→None.

### 3. Encoding Utilities

| Function | Input | Output | Used By |
|----------|-------|--------|---------|
| `_b64_encode(content) → str` | Any ContentT | Base64 string (no prefix) | `document_qa()`, `visual_qa()` — embeds image in JSON body |
| `_as_url(content, default_mime) → str` | Any ContentT | `data:{mime};base64,{data}` data URL | Chat completion multimodal content parts |
| `_bytes_to_image(content) → Image` | Raw bytes | PIL.Image | `text_to_image()`, `image_to_image()`, `image_to_video()` |
| `_b64_to_image(str) → Image` | Base64 string | PIL.Image | Client-side post-processing |

**`_as_url` shortcut:** URLs starting with `http://`, `https://`, or `data:` pass through unchanged — no re-encoding.

### 4. Image Methods on InferenceClient

All 8 image methods in `_client.py` accept `image: ContentT`:

| Method | Line | Returns | API Task |
|--------|------|---------|----------|
| `image_classification()` | 1163 | `list[ImageClassificationOutputElement]` | image-classification |
| `image_segmentation()` | 1213 | `list[ImageSegmentationOutputElement]` | image-segmentation |
| `image_to_image()` | 1281 | `Image` (PIL) | image-to-image |
| `image_to_video()` | 1357 | `bytes` | image-to-video |
| `image_to_text()` | 1436 | `ImageToTextOutput` | image-to-text |
| `object_detection()` | 1482 | `list[ObjectDetectionOutputElement]` | object-detection |
| `text_to_image()` | 2439 | `Image` (PIL) | text-to-image (no image input) |
| `visual_question_answering()` | 3048 | `list[VisualQuestionAnsweringOutputElement]` | visual-question-answering |
| `zero_shot_image_classification()` | 3210 | `list[ZeroShotImageClassificationOutputElement]` | zero-shot-image-classification |

`document_question_answering()` (line 937) also accepts `image: ContentT` and always passes `{"question": ..., "image": _b64_encode(image)}`.

### 5. Provider-Specific Image Handling

**`HFInferenceTask`** (JSON-based): For text tasks — raises `ValueError` on binary inputs.

**`HFInferenceBinaryInputTask`** (binary-capable, lines 72–101):
- **No parameters** → raw bytes via `_open_as_mime_bytes(inputs)` with auto-detected MIME
- **With parameters** → base64 in JSON: `{"inputs": _b64_encode(inputs), "parameters": ...}`

### 6. Chat Completion Multimodal Pattern

`chat_completion()` does NOT accept `ContentT` for images — users provide pre-encoded URLs:
```python
messages = [{"role": "user", "content": [
    {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}},
    {"type": "text", "text": "Describe this image."},
]}]
```

### 7. Key Architectural Insights

1. **Dual pathway:** Every image method supports raw binary (no parameters, minimal overhead) or b64 JSON (with parameters, +33% size).
2. **Lazy PIL import:** Only needed when passing PIL Image objects or receiving image output. Bytes/URLs/Paths work without PIL.
3. **String ambiguity risk:** A plain string is always treated as a path first — can cause confusing `FileNotFoundError`.
4. **Chat completion gap:** Unlike task methods, `chat_completion()` has no `ContentT` convenience — users must encode manually.
5. **BinaryIO duck-typing:** Matches any `.read()` object — including text streams (raises `TypeError` at runtime).

### 8. Zero-Cost Patterns

```python
from huggingface_hub import InferenceClient
client = InferenceClient()  # free tier

# Classification — auto-selects HF's recommended free model
result = client.image_classification("cat.jpg")

# Captioning — free via recommended model
caption = client.image_to_text("https://example.com/photo.jpg")

# VQA — specify a free model explicitly
answers = client.visual_question_answering(
    image="scene.jpg",
    question="How many people?",
    model="google/vit-base-patch16-224",
)
```

### References
- `_common.py`: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_common.py
- `_client.py`: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_client.py
- `hf_inference.py` provider: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/_providers/hf_inference.py

---
## 2026-07-24: hf-hub-sandboxes-deep-dive — HF Sandboxes (Topic #148)

### Summary
Deep-dive into HF Sandboxes — isolated cloud machines built on Jobs for remote code execution, with GPU/CPU options, volume mounts from Hub repos/buckets, secrets injection, and persistent reconnection from any machine. All zero-cost with cpu-basic.

### Architecture
| Mode | Description | Use Case | Cost |
|------|-------------|----------|------|
| Dedicated | One sandbox = one Job VM | GPU, untrusted code | Free cpu-basic |
| Pool | Shared host, landlock-isolated | Cheap CPU scale | Free tier eligible |

### CLI
```bash
# Create
hf sandbox create
hf sandbox create --flavor t4-small
hf sandbox create --pool pool-ab12 --env LOG=debug
hf sandbox create -v hf://buckets/ns/b:/mnt/data

# Exec / Spawn / Cp / Kill
hf sandbox exec <id> -- python -c "print(42)"
hf sandbox spawn <id> -- python -m http.server 8000
hf sandbox cp data.csv <id>:/data/
hf sandbox kill <id>
hf sandbox kill --all

# Pools
hf sandbox pool create --per-host 50
hf sandbox pool ls
```

### Python SDK
```python
from huggingface_hub import HfApi
api = HfApi()
s = api.create_sandbox(flavor="cpu-basic",
    volumes=["hf://datasets/org/ds:/data:ro"])
s.exec("python -c 'print(42)'")
s.cp("result.json", "/app/result.json")
api.get_sandbox("<id>")  # reattach
api.delete_sandbox("<id>")
```

### Key Points
1. Sandboxes outlive the client — create once, reconnect anywhere.
2. Volume mounts (hf:// URIs) avoid data downloads.
3. Secrets injection only for dedicated mode.
4. Zero-cost default: cpu-basic + pool mode.

## 2026-07-24: hf-hub-create-commit-atomic-operations-deep-dive — `create_commit` API with CommitOperationAdd/Copy/Delete (Topic #211)

### Summary
Deep-dive into the `create_commit` API — the core programmatic interface for atomic multi-file operations on the Hugging Face Hub. Covers the three `CommitOperation` types (`Add`, `Copy`, `Delete`), the full commit lifecycle (preupload → LFS batch → commit), no-op detection, cross-repo copies, Xet vs legacy LFS upload, the `preupload_lfs_files` power-user pattern, `CommitInfo` return type, and high-level wrappers (`upload_file`, `upload_folder`, `delete_file`, `delete_folder`). Source: `huggingface_hub/_commit_api.py` and `huggingface_hub/hf_api.py` (v1.24.0).

### Core Architecture

`create_commit` is the foundation that all Hub write operations build on. It accepts a list of `CommitOperation` objects (mutated in-place during processing — do NOT reuse objects across commits) and returns a `CommitInfo`.

#### Type Alias

```python
CommitOperation = Union[CommitOperationAdd, CommitOperationCopy, CommitOperationDelete]
```

### Three Operation Types

#### 1. `CommitOperationAdd` — Upload Files

```python
@dataclass
class CommitOperationAdd:
    path_in_repo: str                          # e.g. "checkpoints/weights.bin"
    path_or_fileobj: str | Path | bytes | BinaryIO  # Local path, bytes, or buffered IO
    # Internal (set during commit):
    _upload_mode: UploadMode | None = None     # "lfs" or "regular"
    _remote_oid: str | None = None             # SHA of existing file on Hub (for no-op detection)
    _local_oid: str | None = None              # SHA256 (LFS) or SHA1 (regular) of local content
    _is_uploaded: bool = False                 # True once LFS upload completes
    _is_committed: bool = False                # True once commit is sent
```

- `path_or_fileobj` accepts: `str` (file path), `Path`, `bytes` (in-memory content), or `io.BufferedIOBase` (must support `seek()` + `tell()`)
- `upload_info` (computed in `__post_init__`): stores SHA256, file size, etc. via `UploadInfo.from_path()`, `UploadInfo.from_bytes()`, or `UploadInfo.from_fileobj()`
- Use `.as_file()` context manager to read content regardless of input type:
  ```python
  with operation.as_file(with_tqdm=True) as f:
      content = f.read()
  ```
- `.b64content()` returns base64-encoded bytes for inline content

#### 2. `CommitOperationCopy` — Server-Side File Copy

```python
@dataclass
class CommitOperationCopy:
    src_path_in_repo: str                      # Source file path
    path_in_repo: str                          # Destination file path
    src_revision: str | None = None            # Git revision of source (default: current commit)
    src_repo_id: str | None = None             # Cross-repo source (e.g. "user/source-model")
    src_repo_type: str | None = None           # Required when src_repo_id set ("model"/"dataset"/"space")
    # Internal:
    _src_oid: str | None = None
    _dest_oid: str | None = None
    _is_duplicated: bool = False
```

- LFS files are copied **server-side** (no download/upload needed)
- Regular (non-LFS) files are downloaded and re-uploaded as part of the commit
- Cross-repo copies require same storage region (cross-region not supported)
- Combine with `CommitOperationDelete` to rename an LFS file on the Hub:
  ```python
  operations = [
      CommitOperationCopy(src_path_in_repo="old_name.bin", path_in_repo="new_name.bin"),
      CommitOperationDelete(path_in_repo="old_name.bin"),
  ]
  ```

#### 3. `CommitOperationDelete` — Delete Files or Folders

```python
@dataclass
class CommitOperationDelete:
    path_in_repo: str                          # File path or folder path (ending in "/")
    is_folder: bool | Literal["auto"] = "auto" # Auto-detects by trailing "/"
```

- `is_folder="auto"` (default): path ending in `/` treated as folder, otherwise file
- Explicit: `is_folder=True` or `is_folder=False`
- Deleting a folder removes all files inside it in a single operation

### The Commit Flow (Step by Step)

When you call `api.create_commit(operations=[...])`, here's the internal sequence:

```
1. VALIDATE INPUTS
   ├── parent_commit matches REGEX_COMMIT_OID (40 hex chars)
   ├── commit_message is non-empty
   ├── repo_type is one of: "model", "dataset", "space"
   ├── No reused CommitOperationAdd (checks _is_committed flag)
   └── Warn if .arrow/.parquet files uploaded to non-dataset repos

2. VALIDATE README (early fail)
   └── If any operation targets "README.md", validate YAML metadata before uploading anything

3. WARN ON OVERWRITES
   └── _warn_on_overwriting_operations(): warns if same file updated twice
       or updated and then deleted in the same commit

4. PREUPLOAD LFS FILES
   └── preupload_lfs_files() [see below]

5. FETCH FILES TO COPY
   └── _fetch_files_to_copy(): resolves source file info for CommitOperationCopy

6. DUPLICATE LFS FILES (cross-repo copies)
   └── _duplicate_lfs_files(): For cross-repo copies, duplicate LFS objects
       to destination repo before committing

7. REMOVE NO-OP OPERATIONS
   └── For CommitOperationAdd: skip if _remote_oid == _local_oid (file unchanged)
   └── For CommitOperationCopy: skip if _dest_oid == _src_oid (identical source/dest)
   └── If ALL operations are no-op: return early with latest commit info

8. SEND COMMIT
   └── _send_commit(): POST to /api/{repo_type}s/{repo_id}/commit with
       all operations serialized
```

### No-Op Detection (Empty Commit Prevention)

The library intelligently skips files that haven't changed:

- **For CommitOperationAdd**: `_remote_oid` (SHA of existing file on Hub) is compared to `_local_oid` (SHA256 for LFS, SHA1 for regular). Match → skipped.
- **For CommitOperationCopy**: `_src_oid` compared to `_dest_oid`. Match → skipped.
- If **all** operations are no-op: returns `CommitInfo` from the latest commit with a warning: "No files have been modified since last commit. Skipping to prevent empty commit."

### Preupload LFS Files Pattern (Power Users)

`preupload_lfs_files()` lets you upload LFS files one at a time, freeing memory between uploads — crucial when generating files on-the-fly:

```python
from huggingface_hub import CommitOperationAdd, preupload_lfs_files, create_commit

operations = []
for i in range(5):
    content = generate_large_binary()  # e.g. model shard
    addition = CommitOperationAdd(
        path_in_repo=f"shard_{i}_of_5.bin",
        path_or_fileobj=content        # bytes or file-like
    )
    preupload_lfs_files(repo_id, additions=[addition])  # Uploads + frees memory
    operations.append(addition)

create_commit(repo_id, operations=operations, commit_message="Commit all shards")
```

Key details:
- LFS files only (regular files < 5MB are committed inline)
- `free_memory=True` (default): `path_or_fileobj` replaced with `b""` after upload
- `gitignore_content`: optionally pass to check `.gitignore` rules before upload
- Parallel upload with `num_threads` (default: 5)
- Uses Xet protocol when available (`hf_xet`), falls back to legacy LFS HTTP

### LFS Upload: Xet vs Legacy

Two upload paths in `_upload_files()`:

| Aspect | Xet Protocol | Legacy LFS HTTP |
|--------|-------------|-----------------|
| Deps | `hf_xet` package installed | Always available |
| Buffered IO | ❌ not supported | ✅ supported |
| SHA256 | Computed inside `hf_xet` during chunking | Computed client-side first |
| Flow | Single pass read + upload | Two-pass: hash then upload |
| Binary IO buffers | Falls back to legacy | Handled natively |

When `hf_xet` is available and no `io.BufferedIOBase` operations exist → Xet path. Otherwise legacy.

### `CommitInfo` Return Type

```python
@dataclass
class CommitInfo(str):  # inherits str for backward compat
    commit_url: str           # URL to view commit on Hub
    commit_message: str       # First line
    commit_description: str   # Full description (can be empty)
    oid: str                  # Commit hash (e.g. "91c54ad1727ee830252e457677f467be0bfd8a57")
    _endpoint: str | None     # API endpoint used
    pr_url: str | None        # PR URL if create_pr=True
    repo_url: RepoUrl         # Computed from commit_url
    pr_revision: str | None   # Computed from pr_url, e.g. "refs/pr/1"
    pr_num: int | None        # Computed from pr_url, e.g. 42
```

### `parent_commit` for Concurrency Safety

Pass `parent_commit` (OID/SHA of expected parent) to prevent race conditions in concurrent workflows:

```python
# Ensure no one else committed before us
info = create_commit(
    repo_id="user/repo",
    operations=[...],
    commit_message="sensitive update",
    parent_commit=known_sha,
)
```

- If `revision` doesn't point to `parent_commit` → commit fails
- If `create_pr=True` → PR created from `parent_commit`

### PR Creation Flow

When `create_pr=True`:
1. LFS preupload uses `revision=None` (so read-access users can still preupload even without write perms)
2. Commit is created against the target branch, then a PR discussion is opened
3. `CommitInfo` returns `pr_url`, `pr_revision` (`refs/pr/N`), and `pr_num`

### High-Level Wrappers

These convenience methods all delegate to `create_commit`:

| Method | What it does |
|--------|-------------|
| `upload_file(path_in_repo, path_or_fileobj, repo_id, ...)` | Single file upload via `CommitOperationAdd` |
| `upload_folder(folder_path, repo_id, ...)` | Recursive folder upload with **parallel** uploads (thread pool), path stripping, allow/ignore patterns |
| `delete_file(path_in_repo, repo_id, ...)` | Single file delete via `CommitOperationDelete` |
| `delete_files(paths_in_repo, repo_id, ...)` | Batch file delete |
| `delete_folder(folder_path, repo_id, ...)` | Folder delete (path must end with `/`) |

### `upload_folder` Advanced Features

```python
api.upload_folder(
    folder_path="./local_checkpoints",
    repo_id="user/repo",
    path_in_repo="remote/checkpoints",      # strip local prefix
    allow_patterns=["*.bin", "*.safetensors"],  # only these files
    ignore_patterns=["*.tmp"],                   # skip these
    delete_patterns=["*.old"],                   # delete matching remote files first
    num_threads=10,                              # parallel upload
    create_pr=True,
)
```

- `allow_patterns` / `ignore_patterns`: glob-based file filtering
- `delete_patterns`: delete matching remote files in the same commit (atomic replacement)
- `num_threads`: parallelism for upload (default: 5, based on `UPLOAD_BATCH_MAX_NUM_FILES=256`)
- Path mapping: `os.path.relpath(local_path, folder_path)` → `path_in_repo/relative_path`

### Limits & Constraints

| Constraint | Value |
|-----------|-------|
| Max LFS files per commit | 25,000 |
| Max payload for regular files | 1 GB |
| LFS batch fetch size | 500 files (`FETCH_LFS_BATCH_SIZE`) |
| Upload batch chunk | 256 files (`UPLOAD_BATCH_MAX_NUM_FILES`) |
| Default upload threads | 5 |
| Cross-region copies | ❌ Not supported |
| IO buffer + Xet | ❌ Falls back to legacy HTTP |

### Best Practices

1. **Use `upload_folder` with `delete_patterns`** for atomic deployment updates (upload new, delete old in one commit)
2. **Preupload LFS files** when generating content on-the-fly to keep memory low
3. **Set `parent_commit`** in concurrent workflows to prevent conflicts
4. **Use `CommitOperationCopy` for renaming** large LFS files (server-side, no re-upload)
5. **Validate README metadata offline** before committing (early fail prevents wasted uploads)
6. **Don't reuse `CommitOperationAdd` objects** — they're mutated during the commit flow
7. **Check for `RepositoryNotFoundError`** if getting 404s — repo must exist before committing
8. **For large folders**, batch additions in groups and use `create_pr=True` for safe review

## 2026-07-24: hf-hub-repo-likes-engagement-api — Repo Like/Engagement System (Topic #213)

### Summary
Deep dive into the Hugging Face Hub's repository "like" engagement system — the social signal system for expressing interest in repos. Unlike GitHub's stars, HF uses a "like" (heart) model with a deliberate anti-spam asymmetry: users can unlike via API but can only like through the web UI. Covers the 3 API methods (`list_liked_repos`, `list_repo_likers`, `unlike`), the REST endpoints behind them, the `UserLikes` and `User` dataclasses, how likes integrate into user profiles, and the relationship between likes, engagement, and the trending/discovery system.

### Key API Surface

**`list_liked_repos(user=None)`** → `UserLikes`
- REST: `GET /api/users/{user}/likes`
- Returns all public repos a user has liked, categorized by type (models, datasets, spaces, kernels)
- If user is None, defaults to the authenticated user (requires token)
- No auth required when querying a public user's likes
- Returns `UserLikes(user, total, models, datasets, spaces, kernels)` with repo IDs as strings
- Response shape from API: Array of `{createdAt, repo: {name, type}}` objects

**`list_repo_likers(repo_id, repo_type=None)`** → `Iterable[User]`
- REST: `GET /api/{repo_type}s/{repo_id}/likers`
- Returns an iterable of `User` objects for all users who liked a given repo
- Paginated (uses the `paginate` helper internally)
- Works across model, dataset, and space repos
- Each `User` object provides: username, fullname, avatar_url

**`unlike(repo_id, repo_type=None)`** → `None`
- REST: `DELETE /api/{repo_type}s/{repo_id}/like`
- Removes the authenticated user's like from a repo
- Requires authentication (token)
- **No symmetric `like()` method exists** — anti-spam measure: "To prevent spam usage, it is not possible to like a repository from a script"

### User Profile Likes Integration

The `User` dataclass (`huggingface_hub.hf_api.User`) exposes engagement metrics:
| Field | Source | Description |
|-------|--------|-------------|
| `num_upvotes` | User profile API | Total upvotes the user has received across their repo contributions |
| `num_likes` | User profile API | Total number of likes the user has given to other repos |
| `num_followers` | User profile API | Number of users following this user |
| `num_following` | User profile API | Number of users this user follows |

These come from the user profile API and are resolved from camelCase Hub API fields (`numUpvotes`, `numLikes`, `numFollowers`, `numFollowing`).

### Anti-Spare Architecture

The like system has a deliberate read-write asymmetry:
- **Read:** Both `list_liked_repos` and `list_repo_likers` are public, no token required for public data
- **Write (unlike):** `DELETE` endpoint requires auth, but only removes — no ability to add
- **Write (like):** Only possible through the web UI at huggingface.co (button click on a repo page)
- This prevents scripted vote manipulation, bot-driven like campaigns, and engagement farming

### Like Count in Repo Info

The like count for a repo is visible via the web UI and can be obtained via:
- `api.repo_info(repo_id).likes` — the `RepoInfo` object's `likes` attribute (int)
- The Hub REST API returns like count in repo metadata: `GET /api/models/{repo_id}` or `/api/datasets/{repo_id}` or `/api/spaces/{repo_id}`
- Like count is part of `RepoInfo.likes` field (an integer)
- Likes are counted in the trending/ranking algorithms for discovery

### Relationship to Discussion Reactions

The Hub's discussion/PR system has a separate emoji reaction system (not the same as repo likes):
- Comments and discussion posts support emoji reactions (👍, ❤️, 🚀, 👀, 🎉, 😕, etc.)
- These are managed through different API endpoints under `/api/{repo_type}s/{repo_id}/discussions/{num}/reactions`
- The huggingface_hub library doesn't expose a direct reaction API — reactions are embedded in `DiscussionComment` objects returned by `get_discussion_details()`
- Each reaction has: `emoji` (string like "+1", "heart", "rocket") and list of users who reacted
- This is a separate system from the repo "like" system

### Key Insights
- HF uses "likes" (hearts) not "stars" — the REST endpoint paths use `/like` and `/likers`
- Unlike GitHub stars, HF's system is read-heavy with deliberate write restrictions
- The `list_liked_repos` API is useful for recommendation/discovery — "users who liked X also liked Y" patterns
- `list_repo_likers` can be used for community engagement analysis (who's interested in your repos)
- The `unlike` method exists primarily for cleanup (removing stale likes programmatically)
- Like count is a search/sortable field in Hub API queries (e.g., sorting by likes)
- Like events are not real-time streamed through webhooks (no webhook event for likes unlike GitHub stars)
- To get likes for your own repos, use `list_repo_likers()` in batches or read from `repo_info().likes`

### Sources
- Source code: `huggingface_hub/hf_api.py` — `HfApi.list_liked_repos`, `HfApi.list_repo_likers`, `HfApi.unlike`
- Source code: `huggingface_hub/hf_api.py` — `UserLikes` dataclass, `User` dataclass
- Hub API docs: https://huggingface.co/docs/hub/en/api
- huggingface_hub docs: https://huggingface.co/docs/huggingface_hub/package_reference/hf_api
- Discussion reactions documented in `endpoint_helpers.py` (`DiscussionComment.reactions`)

---

## 2026-07-24: hf-hub-repo-likes-engagement-api-deep-dive-v2 — Downloads, Trending Score, and Discovery API (Topic #213 Deepening)

**author:** SakThai
**license:** MIT

### Summary

Extension of the Hub Engagement API deep-dive covering the three remaining engagement dimensions beyond the likes system: **downloads metrics** (30-day + all-time, counting methodology), **trending score** (how repos rank on the Hub), and the **search/discovery API parameters** that surface engagement data. Together with the likes API from the previous deep-dive, this completes the full Hub engagement picture.

---

### 1. Downloads Metrics — `downloads` and `downloads_all_time`

Every repository exposes two download counters. These are **read-only** fields available through `repo_info()`, `model_info()`, and the search/list APIs.

| Field | huggingface_hub Attribute | API Field | Scope |
|-------|--------------------------|-----------|-------|
| 30-day downloads | `ModelInfo.downloads` / `DatasetInfo.downloads` / `SpaceInfo.downloads` | `downloads` | Last 30 days |
| All-time downloads | `ModelInfo.downloads_all_time` / `DatasetInfo.downloads_all_time` | `downloadsAllTime` | Cumulated since creation |

```python
from huggingface_hub import HfApi
api = HfApi()

info = api.model_info("bert-base-uncased")
print(f"30-day: {info.downloads}")          # int | None
print(f"All-time: {info.downloads_all_time}")  # int | None
```

**Key properties:**
- Both fields are integers (`int | None`)
- `downloads_all_time` is only present when `expand=True` is passed in `list_models()`/`list_datasets()` or when using `model_info()`/`dataset_info()` directly
- For model info, `downloads` and `downloads_all_time` are always included
- For search/list endpoints, they must be requested via `expand=["downloads", "downloadsAllTime"]`

#### How Downloads Are Counted (Server-Side Methodology)

Download counting is **server-side only** — no client-side instrumentation or analytics payloads. Every HTTP `GET` and `HEAD` request to designated "query files" increments the counter.

**Default query files** (when no library is specified):
- `config.json`, `config.yaml`, `hyperparams.yaml`, `params.json`, `meta.yaml`

**Library-specific overrides** — the Hub maintains open-source code (`/api/event` endpoint config) that maps libraries to custom download query patterns:

| Library | Query Files |
|---------|------------|
| Default (no library) | `config.json`, `config.yaml`, `hyperparams.yaml`, `params.json`, `meta.yaml` |
| nemo | All `.nemo` files |
| GGUF | All files (GGUF files are self-contained) |
| diffusers | Top-level `.safetensors` + files loaded by the diffusers library |
| Custom libraries | Add via PR to [huggingface/hub-internal-download-stats](https://github.com/huggingface/hub-internal-download-stats) |

**Double-counting rules:**
- **GGUF**: All GGUF files counted — cloning a whole repo double-counts each file, but most users download single GGUF files
- **Diffusers**: Special filter avoids double-counting nested safetensors/pickle weights loaded via the library vs. direct downloads (Auto1111, LoRA UIs)
- **General**: The `config.json` query file is the single counter by default to avoid counting one model download as N file downloads

#### Publisher Analytics for Granular Data

Organizations that need more detailed download data (distinguish config.json from weights, exclude CI/CD, count unique downloaders) can use **Publisher Analytics** — anonymized request-level access logs.

Features:
- Raw access logs for all models/datasets published by an organization
- Can distinguish file types, filter out CI/CD traffic
- Deduplicate by unique IPs for unique downloader counts
- Requires an organization account (not available for individual users)

---

### 2. Trending Score — `trending_score`

Every repository type (model, dataset, space) has a **`trending_score`** — an integer value computed server-side that measures recent engagement velocity.

```python
info = api.model_info("bert-base-uncased")
print(f"Trending score: {info.trending_score}")  # int | None
```

**Availability:**
- Exposed in `ModelInfo.trending_score`, `DatasetInfo.trending_score`, `SpaceInfo.trending_score`
- Only available when requesting with `expand=True` in list/search APIs or via `model_info()`/`dataset_info()`/`space_info()`
- The Hub API JSON field is `trendingScore` (camelCase)

**How it's used:**
- Sort parameter in `list_models()`, `list_datasets()`, `list_spaces()` — sort by `"trending_score"`
- Drives the default "Trending" sort on the Hub web UI
- Collections can also be sorted by `"trending"` (for `CollectionSort_T`)
- Daily Papers use `"trending"` as a sort option

**Known behavior:**
- Trending is recency-weighted — repos with spikes in likes/downloads get higher scores
- The exact formula is proprietary/server-side but correlates with: recent likes + recent downloads + velocity (change over short time window)
- Not documented publicly; the raw `trendingScore` is an opaque integer

**Type definition:**
```python
ModelSort_T = Literal["created_at", "downloads", "last_modified", "likes", "trending_score"]
DatasetSort_T = Literal["created_at", "downloads", "last_modified", "likes", "trending_score"]
SpaceSort_T = Literal["created_at", "last_modified", "likes", "trending_score"]
CollectionSort_T = Literal["lastModified", "trending", "upvotes"]
DailyPapersSort_T = Literal["publishedAt", "trending"]
```

---

### 3. Search & Discovery by Engagement — Sort and Expand Parameters

The list/search APIs (`list_models()`, `list_datasets()`, `list_spaces()`) support sorting by engagement metrics and expanding responses to include them.

#### Sort Options

```python
# Sort models by likes (descending)
api.list_models(sort="likes", direction=-1)

# Sort by trending score
api.list_models(sort="trending_score", direction=-1)

# Sort by downloads
api.list_models(sort="downloads", direction=-1)

# Sort by last_modified (for recently updated)
api.list_models(sort="last_modified", direction=-1)
```

| Sort Value | Sorts By | Available For |
|------------|----------|---------------|
| `"likes"` | Like count | models, datasets, spaces |
| `"downloads"` | 30-day download count | models, datasets |
| `"trending_score"` | Trending score | models, datasets, spaces |
| `"last_modified"` | Last commit date | models, datasets, spaces |
| `"created_at"` | Creation date | models, datasets |

**Direction:** `direction=1` (ascending) or `direction=-1` (descending, default).

#### Expand Parameters

The `expand` parameter controls which optional fields are included in list/search API responses. Engagement-related expand values:

```python
# Include all engagement metrics in search results
api.list_models(
    expand=["downloads", "downloadsAllTime", "likes", "trendingScore"],
    sort="likes",
    limit=10
)
```

| Expand Value | What It Adds |
|--------------|-------------|
| `"downloads"` | Include 30-day download count |
| `"downloadsAllTime"` | Include all-time download count |
| `"likes"` | Include like count |
| `"trendingScore"` | Include trending score |
| `"lastModified"` | Include last modification timestamp |
| `"createdAt"` | Include creation timestamp |

**Performance note:** Each expand value adds one sub-query server-side. Only request what you need. Without expand, list endpoints return minimal metadata only.

**Full expand options for models:**
```python
ExpandableModelFields = Literal[
    "author", "cardData", "config", "createdAt", "disabled",
    "downloads", "downloadsAllTime", "evalResults", "gated",
    "gguf", "inference", "inferenceProviderMapping", "lastModified",
    "library_name", "likes", "mask_token", "model-index",
    "pipeline_tag", "private", "safetensors", "sha", "siblings",
    "spaces", "tags", "transformersInfo", "trendingScore",
    "widgetData", "resourceGroup"
]
```

---

### 4. REST API Endpoints for Engagement

All engagement endpoints are available directly via REST without the Python library:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/models/{repo_id}` | GET | Full model info including likes, downloads, trendingScore (requires no auth for public repos) |
| `/api/models/{repo_id}/like` | POST | Like a repo (web UI only — blocked in scripts) |
| `/api/models/{repo_id}/like` | DELETE | Unlike a repo (requires auth, usable from API) |
| `/api/models/{repo_id}/likers` | GET | List users who liked a repo |
| `/api/users/{user}/likes` | GET | List repos liked by a user |
| `/api/models` | GET | List/search models with sort, expand, filter |
| `/api/datasets` | GET | List/search datasets with sort, expand, filter |
| `/api/spaces` | GET | List/search spaces with sort, expand, filter |

Replace `models` with `datasets` or `spaces` for dataset/space endpoints. The `/api/event` endpoint (not public) handles download counting internal logic.

---

### 5. Complete Engagement Data Model

The full engagement state of a repository can be read from `repo_info()` which returns `RepoInfo` (or `ModelInfo`/`DatasetInfo`/`SpaceInfo`):

```python
from huggingface_hub import HfApi

api = HfApi()
info = api.repo_info("bert-base-uncased", repo_type="model")

# Likes
print(f"Likes: {info.likes}")                              # int

# Downloads
print(f"Downloads (30d): {info.downloads}")                # int
print(f"Downloads (all time): {info.downloads_all_time}")  # int | None

# Trending
print(f"Trending score: {info.trending_score}")            # int | None

# Last modified timestamp
print(f"Last modified: {info.last_modified}")              # datetime | None

# Created timestamp
print(f"Created at: {info.created_at}")                    # datetime | None

# Is repo private/disabled/gated
print(f"Private: {info.private}")
print(f"Disabled: {info.disabled}")
print(f"Gated: {info.gated}")
```

For search results (bulk), use list endpoints with expand:

```python
# Top 100 most-liked models
for model in api.list_models(sort="likes", expand=["likes", "downloads"], limit=100):
    print(f"{model.modelId:50s} ❤️ {model.likes:>5}  ⬇️ {model.downloads:>8}")
```

---

### 6. Key Insights & Practical Patterns

1. **Likes + downloads are independent signals:** A model can have many downloads but few likes (utility usage) or many likes but few downloads (community buzz).

2. **Trending score is the composite signal:** It combines both dimensions with recency weighting. Use `sort="trending_score"` for "what's hot now" discovery.

3. **Expand is your friend for bulk queries:** Without expand, list endpoints return minimal data. Always pass `expand=["likes", "downloads"]` when you need engagement data in bulk.

4. **Downloads counting has edge cases:** GGUF counts all files (potential double-counting), diffusers has special filters. Use Publisher Analytics for definitive numbers.

5. **Unlike-only API is asymmetric by design:** Scripts can only unlike, never like. This prevents bot-driven engagement farming. Likes must come from real users through the web UI.

6. **Engagement feeds discovery:** The Hub's search ranking and "trending" views use these metrics. More engagement → more visibility → more engagement (compounding effect).

|7. **Zero-cost relevance:** All engagement APIs are free and public-readable. No token needed to read likes, downloads, or trending score for public repos. Perfect for Beer's analytics and discovery needs.

### Sources
- Source code: `huggingface_hub/hf_api.py` — `ModelInfo`, `DatasetInfo`, `SpaceInfo`, `RepoInfo` fields (`likes`, `downloads`, `downloadsAllTime`, `trendingScore`)
- Source code: `huggingface_hub/hf_api.py` — `list_models()` sort/expand parameters
- Source code: `huggingface_hub/hf_api.py` — `ModelSort_T`, `DatasetSort_T`, `SpaceSort_T` type definitions
- Hub API docs: https://huggingface.co/docs/hub/en/api
- Download stats methodology: https://huggingface.co/docs/hub/en/models-download-stats
- Hub docs: https://huggingface.co/docs/hub/en/repositories-getting-started

---

## 2026-07-25: hf-hub-user-and-org-profile-api — User and Organization Profile API (Topic #231)

### Summary
Comprehensive reference on the Hugging Face Hub's User and Organization profile API — the REST endpoints and `huggingface_hub` Python methods for reading public user/org profiles, managing repositories, navigating the social graph (followers/following), and understanding profile data models. Profile management (bio, avatar, settings) is web-UI only — there is no public API for updating profiles.

### REST API Endpoints

#### User Endpoints
| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/users/{username}/overview` | GET | No | Full public user profile |
| `/api/users/{username}/followers` | GET | No | Paginated list of followers (User objects) |
| `/api/users/{username}/following` | GET | No | Paginated list of users this user follows |

#### Organization Endpoints
| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/organizations/{name}/overview` | GET | No | Full public org profile |
| `/api/organizations/{name}/members` | GET | No | Paginated list of org members (User objects) |
| `/api/organizations/{name}/followers` | GET | No | Paginated list of org followers |

#### Authenticated Endpoints
| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/whoami-v2` | GET | Token | Current user's full profile + orgs + token info |
| `/api/settings/repositories` | GET | Token | Authed user's repos with storage info |
| `/api/organizations/{name}/settings/repositories` | GET | Token | Org's repos with storage info |

### huggingface_hub Python API

#### User/Org Profile Methods
All available as both `HfApi` instance methods and module-level functions:

| Method | Returns | Description |
|---|---|---|
| `get_user_overview(username)` | `User` | Fetch user profile (no auth needed for public users) |
| `get_organization_overview(org)` | `Organization` | Fetch org profile (no auth needed) |
| `whoami(token)` | `dict` | Current user's auth session + org membership |
| `list_user_repos(namespace=None)` | `Iterable[RepoStorageInfo]` | List repos with storage (authed); namespace=org name for org repos |

#### Social Graph Methods
| Method | Returns | Description |
|---|---|---|
| `list_user_followers(username)` | `Iterable[User]` | Paginated followers |
| `list_user_following(username)` | `Iterable[User]` | Paginated following list |
| `list_organization_members(org)` | `Iterable[User]` | Paginated org members |
| `list_organization_followers(org)` | `Iterable[User]` | Paginated org followers |

### Data Models

#### User Object
Returned by `get_user_overview()`, `list_user_followers()`, etc.

| Field | Type | Source Key | Description |
|---|---|---|---|
| `username` | `str` | `user` | Unique HF username |
| `fullname` | `str` | `fullname` | Display name |
| `avatar_url` | `str` | `avatarUrl` | CDN URL for avatar image |
| `details` | `str | None` | Bio/description from profile |
| `is_following` | `bool | None` | Whether authed user follows them |
| `is_pro` | `bool | None` | HF Pro subscriber? |
| `user_type` | `str | None` | `"user"` or `"org"` |
| `num_models` | `int | None` | Model count |
| `num_datasets` | `int | None` | Dataset count |
| `num_spaces` | `int | None` | Spaces count |
| `num_buckets` | `int | None` | Storage bucket count |
| `num_discussions` | `int | None` | Discussion count |
| `num_papers` | `int | None` | Paper count |
| `num_upvotes` | `int | None` | Received upvotes |
| `num_likes` | `int | None` | Likes given |
| `num_followers` | `int | None` | Follower count |
| `num_following` | `int | None` | Following count |
| `num_following_orgs` | `int | None` | Orgs following |
| `orgs` | `list[Organization]` | Organizations they belong to (minimal: id, name, fullname, avatarUrl) |
| `createdAt` | `str (ISO 8601)` | Account creation date |

#### Organization Object
Returned by `get_organization_overview()`, `list_organization_members()`, etc.

| Field | Type | Source Key | Description |
|---|---|---|---|
| `name` | `str` | `name` | Unique org name |
| `fullname` | `str` | `fullname` | Display name |
| `avatar_url` | `str` | `avatarUrl` | CDN URL for avatar |
| `details` | `str | None` | Org description |
| `is_verified` | `bool | None` | Verified badge? |
| `is_following` | `bool | None` | Whether authed user follows |
| `num_users` | `int | None` | Member count |
| `num_models` | `int | None` | Models owned |
| `num_spaces` | `int | None` | Spaces owned |
| `num_datasets` | `int | None` | Datasets owned |
| `num_buckets` | `int | None` | Buckets owned |
| `num_papers` | `int | None` | Papers authored |
| `num_followers` | `int | None` | Follower count |
| `plan` | `str | None` | Subscription plan (`"enterprise"`, `"team"`, `"pro"`, etc.) |

### Profile Management (Web UI Only, No API)

The following profile settings have **no public API** — they can only be changed through the web UI:
- **Avatar:** `https://huggingface.co/settings/profile` — upload/replace avatar image
- **Bio/Details:** Same settings page — text area for user description
- **Full name:** Same settings page
- **Social links:** Website URL in profile
- **Account settings:** Email, password, 2FA at `https://huggingface.co/settings/account`

There is no `follow_user()` or `unfollow_user()` method in `huggingface_hub`. Follow/unfollow actions also require the web UI.

### Practical Code Examples

#### Fetch and display a user profile
```python
from huggingface_hub import get_user_overview

user = get_user_overview("Nanthasit")
print(f"{user.fullname} (@{user.username})")
print(f"Bio: {user.details}")
print(f"Models: {user.num_models} | Datasets: {user.num_datasets} | Spaces: {user.num_spaces}")
print(f"Followers: {user.num_followers} | Following: {user.num_following}")
```

#### List all followers of a user
```python
from huggingface_hub import list_user_followers

for follower in list_user_followers("Nanthasit"):
    print(f"{follower.fullname} (@{follower.username}) — {follower.num_models} models")
```

#### List org members
```python
from huggingface_hub import list_organization_members

for member in list_organization_members("litert-community"):
    print(f"Member: {member.fullname} (@{member.username})")
```

#### Get authenticated user's repos with storage info
```python
from huggingface_hub import list_user_repos

for repo in list_user_repos():
    storage_mb = repo.storage / (1024 * 1024)
    print(f"{repo.type:8s} {repo.id:40s} {storage_mb:6.1f} MB ({repo.visibility})")
```

#### Check how many users are in an org
```python
from huggingface_hub import get_organization_overview

org = get_organization_overview("litert-community")
print(f"{org.fullname}: {org.num_users} members, {org.num_models} models, {org.num_followers} followers")
```

### Key Insights

1. **No write API for profiles:** Hugging Face intentionally does not expose profile-editing endpoints via the public API. All profile management goes through the web UI at `huggingface.co/settings/profile`. This prevents bot-driven profile manipulation.

2. **Public-by-default:** User overviews and org overviews are fully public (no token required). Great for analytics and discovery — you can scrape org membership, follower counts, and model counts without authentication.

3. **Paginated social graph:** `list_user_followers()`, `list_user_following()`, `list_organization_members()`, and `list_organization_followers()` all return `Iterable` — internally using Hugging Face's `paginate()` helper that yields items from cursor-based pagination. No manual page management needed.

4. **User vs Organization distinction:** The `type` field distinguishes `"user"` from `"org"` accounts. Org profiles have different field sets (`num_users` vs `num_following`, `plan` vs `is_pro`).

5. **Repo listing includes storage:** `list_user_repos()` returns `RepoStorageInfo` with `storage` (bytes) and `storage_percent` — useful for monitoring disk usage and staying within free tier limits. Requires authentication.

6. **whoami is rate-limited:** The `/api/whoami-v2` endpoint is heavily rate-limited for security. Use `whoami(cache=True)` to cache the result for the duration of the Python process.

### Zero-Cost Relevance
- All public endpoints require no token — 100% free for read-only access
- `list_user_repos()` with storage info helps Beer track his HF storage usage (16 models, 8 datasets, 2 Spaces, 2 buckets — within free tier)
- User/org profile data is useful for building analytics dashboards, discovering collaborators, and identifying popular model authors
- No API costs or rate limits for public reads — usable in cron jobs and automation

### Sources
- Source code: `huggingface_hub/hf_api.py` — `get_user_overview()`, `get_organization_overview()`, `whoami()`, `list_user_followers()`, `list_user_following()`, `list_organization_members()`, `list_organization_followers()`, `list_user_repos()`
- Source code: `huggingface_hub/hf_api.py` — `User` dataclass, `Organization` dataclass, `RepoStorageInfo` dataclass
- Hub API: https://huggingface.co/api/users/{username}/overview
- Hub API: https://huggingface.co/api/organizations/{name}/overview
- User settings: https://huggingface.co/settings/profile
- huggingface_hub docs: https://huggingface.co/docs/huggingface_hub/en/package_reference/community

---

## 2026-07-25: hf-hub-agent-harnesses-registry — HF Agent Harnesses Registry, MCP Server & Agent Ecosystem (Topic #233)

### Summary
Deep-dive into the Hugging Face Hub's new **Agent Ecosystem** — a dedicated docs section (Agents Overview, HF MCP Server, HF CLI for AI Agents, Agent Skills, SDK, Local Agents, Session Traces) plus a new **`/api/agent-harnesses`** REST endpoint that returns a registry of AI agents / harnesses known to the Hub. This is how `huggingface_hub` identifies which agent it's running inside (e.g., Claude Code, Codex, Cursor) and reports agent-attributed usage on Hub requests.

### Sources
- HF Hub Agents docs: https://huggingface.co/docs/hub/en/agents
- Agents Overview: https://huggingface.co/docs/hub/en/agents-overview
- HF MCP Server: https://huggingface.co/docs/hub/en/agents-mcp
- HF CLI for AI Agents: https://huggingface.co/docs/hub/en/agents-cli
- Agent Skills: https://huggingface.co/docs/hub/en/agents-skills
- SDK docs: https://huggingface.co/docs/hub/en/agents-sdk
- Local Agents: https://huggingface.co/docs/hub/en/agents-local
- Session Traces Format: https://huggingface.co/docs/hub/en/session-traces-format
- OpenAPI spec: https://huggingface.co/.well-known/openapi.md
- Agent harnesses source: `@huggingface/tasks` package — `agent-harnesses.ts`
- MCP Settings: https://huggingface.co/settings/mcp

### 1. Hub Agents Documentation (New Section)

The Hugging Face Hub now has a dedicated **Agents** section in its docs with 8 sub-pages:

| Page | URL | Purpose |
|------|-----|---------|
| Agents Overview | `/docs/hub/en/agents-overview` | Connecting chat & coding agents to the Hub |
| HF CLI for AI Agents | `/docs/hub/en/agents-cli` | Using `hf` CLI from coding agents |
| HF MCP Server | `/docs/hub/en/agents-mcp` | MCP protocol server for AI assistants |
| HF Agent Skills | `/docs/hub/en/agents-skills` | Pre-built skills (agentskills.io) |
| Building agents with HF SDK | `/docs/hub/en/agents-sdk` | Python/JS SDK for building agents |
| Local Agents with llama.cpp | `/docs/hub/en/agents-local` | Running agents locally |
| Agent Libraries | `/docs/hub/en/agents-libraries` | Catalog of agent libraries |
| Session Traces Format | `/docs/hub/en/session-traces-format` | Standard format for agent traces |

### 2. `/api/agent-harnesses` — The Agent Registry Endpoint

A new REST endpoint in the Hub API:

```
GET /api/agent-harnesses
```

Returns the registry of all AI agents / harnesses known to the Hub, along with the **standard environment variables used to detect them**. This is how the Hub knows what agent is making a request.

**How it works:**
- `huggingface_hub` detects which agent harness it's running inside by checking environment variables
- When making Hub API calls, it includes the harness name in the user-agent header
- Registered harnesses get attributed by name in Hub usage analytics and the public agent usage dataset
- Unregistered tools are only counted in the aggregate "unknown" share

**To register a harness:** Open a PR adding an entry to `agent-harnesses.ts` in the `@huggingface/tasks` package. Entry fields include: name, display label, environment variable detection patterns, docs URL, and repo URL.

### 3. HF MCP Server

The Hugging Face MCP Server connects MCP-compatible AI assistants to the Hub:

- **Configuration:** Generated at https://huggingface.co/settings/mcp — picks your client type and produces the exact snippet
- **Supported clients:** Cursor, VS Code, Zed, Claude Desktop, ChatGPT, Codex, and any MCP-compatible client
- **Built-in tools:** The `hf_fs` tool enables semantic searches of docs and Spaces
- **Community tools:** Gradio MCP-compatible Spaces expose their functions as tools with arguments and descriptions
- **Capabilities:** Search models/datasets/Spaces, read docs, schedule Jobs, use Sandboxes, run community tools

To connect: `claude mcp add hf-mcp-server -t http "https://huggingface.co/mcp?login"`

### 4. HF CLI for AI Agents

The `hf` CLI now has first-class agent support:

- **CLI Skill:** `hf skills add --global` installs the CLI skill so coding agents know every `hf` command
- **Claude Code integration:** `/plugin marketplace add huggingface/skills` then `/plugin install hf-cli@huggingface/skills`
- **Agent workflow:** Agents can search models, manage datasets/buckets, launch Spaces, run Jobs — all via the CLI

### 5. Agent Skills Platform (agentskills.io)

A new skill marketplace at agentskills.io allows agents to install task-specific capabilities:
- Skills work alongside MCP or standalone
- Published by Hugging Face as `huggingface/skills` on the plugin marketplace
- Skills provide guidance for AI/ML workflows (HF CLI, model handling, etc.)

### 6. Session Traces Format

Standardized JSON format for recording agent sessions interacting with the Hub. Enables traceability and reproducibility of agent actions.

### 7. Key Takeaways

1. **The agent ecosystem is a first-class Hub feature** — not an afterthought. Dedicated docs, API endpoint, and CLI integration.
2. **Attribution is opt-in via environment variable detection.** Registering your harness gives named attribution in Hub analytics.
3. **MCP is the primary integration protocol.** The HF MCP Server exposes Hub tools via MCP for any compatible assistant.
4. **Skills are a complementary layer** to MCP, providing task-specific procedural guidance for coding agents.
5. **The registry is open-source** — agent-harnesses.ts in the `@huggingface/tasks` package accepts PRs for new harnesses.

### Skill
mlops/huggingface-hub — Hub API, MCP Server, CLI, and agent integration

---

## 2026-07-25: hf-agent-skills-complete-reference — HF Agent Skills Platform: Complete Specification & Ecosystem (Deep-Dive of Topic #233)

### Summary
Complete deep-dive on the **Agent Skills** ecosystem — an open, lightweight format for extending AI agents with specialized knowledge and workflows. Covers the open specification (agentskills.io), the `SKILL.md` format with YAML frontmatter, progressive disclosure loading model, directory structure conventions, the Hugging Face curated skill catalog (11 official skills), the `hf skills add` CLI, installation patterns for all major coding agents, the validation tooling (`skills-ref`), and how this relates to the Sak Family Agents' own skill system.

### Sources
- Agent Skills Overview: https://agentskills.io/home.md
- Specification: https://agentskills.io/specification.md
- Quickstart: https://agentskills.io/skill-creation/quickstart.md
- HF Agent Skills (Hub docs): https://huggingface.co/docs/hub/en/agents-skills
- HF CLI for AI Agents: https://huggingface.co/docs/hub/en/agents-cli
- Validation tool: https://github.com/agentskills/agentskills/tree/main/skills-ref
- Best practices: https://agentskills.io/skill-creation/best-practices.md
- Client Showcase: https://agentskills.io/clients.md
- GitHub: https://github.com/agentskills/agentskills
- Discord: https://discord.gg/MKPE9g8aUy

### 1. What Are Agent Skills?

Agent Skills are an **open, lightweight format** (originally developed by Anthropic, now community-governed) for extending AI agent capabilities with specialized knowledge and repeatable workflows. A skill is a folder containing a `SKILL.md` file with metadata and instructions plus optional scripts, references, and assets.

```tree
my-skill/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
├── assets/           # Optional: templates, resources
└── ...               # Any additional files or directories
```

**Key properties:**
- **Portable** — version-controlled folders, shareable via git
- **Cross-product** — same skill works in Claude Code, VS Code, Cursor, OpenCode, Gemini CLI, Copilot, Codex, and 30+ more clients
- **Progressive disclosure** — agents load only metadata at startup, full instructions on activation, resources on demand

### 2. The `SKILL.md` Format (Specification)

#### Frontmatter Fields

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | Yes | 1-64 chars, lowercase alphanumeric + hyphens, must match directory name |
| `description` | Yes | 1-1024 chars, describes what + when to use |
| `license` | No | License name or reference to bundled file |
| `compatibility` | No | 1-500 chars, environment requirements |
| `metadata` | No | Arbitrary key-value map |
| `allowed-tools` | No | Space-separated pre-approved tools (experimental) |

**Minimal example:**
```yaml
---
name: skill-name
description: A description of what this skill does and when to use it.
---
```

**Full example with optional fields:**
```yaml
---
name: pdf-processing
description: Extract PDF text, fill forms, merge files. Use when handling PDFs.
license: Apache-2.0
compatibility: Requires Python 3.14+ and uv
metadata:
  author: example-org
  version: "1.0"
allowed-tools: Bash(git:*) Bash(jq:*) Read
---
```

#### Naming Rules
- Only lowercase letters (`a-z`), digits (`0-9`), and hyphens (`-`)
- Must not start or end with a hyphen
- No consecutive hyphens (`--`)
- Must match the parent directory name

#### Body Content
The Markdown body after frontmatter contains instructions. Recommended sections:
- Step-by-step instructions
- Examples of inputs and outputs
- Common edge cases

Agents load the body on activation. Keep under 500 lines; move reference material to separate files.

### 3. Progressive Disclosure Model

Agents load skills in three stages to minimize context usage:

| Stage | What's Loaded | Token Cost | When |
|-------|---------------|------------|------|
| Discovery | `name` + `description` | ~100 tokens | At startup for all skills |
| Activation | Full `SKILL.md` body | < 5000 tokens recommended | When task matches description |
| Execution | Referenced files (scripts/, references/, assets/) | Variable | Only when needed |

This means agents can have hundreds of skills available without filling their context window.

### 4. Hugging Face Curated Skills Catalog

HF publishes 11 official skills at `huggingface/skills` on the Claude Code plugin marketplace:

| Skill | What It Does |
|-------|-------------|
| `hf-cli` | Hub operations via the `hf` CLI: download, upload, manage repos, run jobs |
| `huggingface-datasets` | Explore datasets, paginate rows, search text, apply filters |
| `huggingface-llm-trainer` | Train or fine-tune LLMs with TRL (SFT, DPO, GRPO) on HF Jobs |
| `huggingface-vision-trainer` | Train object detection and image classification models |
| `huggingface-community-evals` | Run evaluations against models on the Hub on local hardware |
| `huggingface-trackio` | Track and visualize ML training experiments with Trackio |
| `huggingface-papers` | Look up and read HF paper pages in markdown |
| `huggingface-paper-publisher` | Publish and manage research papers on the Hub |
| `huggingface-tool-builder` | Build reusable scripts for HF API operations |
| `gradio` | Build Gradio web UIs and demos |
| `transformers-js` | Run ML models in JavaScript/TypeScript with WebGPU/WASM |

### 5. Installation Methods

#### Method 1: `hf skills add` (HF CLI — recommended)
```bash
# Global install (works with Codex, Cursor, OpenCode, anything loading from ~/.agents/skills)
hf skills add --global
# For Claude Code specifically
hf skills add --claude --global
# Project-local install
hf skills add
# Project-local for Claude Code
hf skills add --claude
```
The skill is generated from the locally installed CLI version — always up to date.

#### Method 2: Claude Code Plugin Marketplace
```
/plugin marketplace add huggingface/skills
/plugin install hf-cli@huggingface/skills
```

#### Method 3: Manual Directory
Create a `.agents/skills/<skill-name>/SKILL.md` file in your project (works with VS Code, Cursor, and other clients that scan `.agents/skills/`).

### 6. Compatible Clients (30+)

Major agents supporting the Agent Skills format:

| Client | Provider |
|--------|----------|
| Claude Code | Anthropic |
| GitHub Copilot | GitHub/Microsoft |
| VS Code | Microsoft |
| Cursor | Cursor |
| OpenAI Codex | OpenAI |
| Gemini CLI | Google |
| Junie | JetBrains |
| OpenCode | SST |
| OpenHands | OpenHands |
| Goose | Block |
| Roo Code | Roo Code |
| Factory | Factory AI |
| Letta | Letta AI |
| And 15+ more... | |

### 7. Validation Tooling

The `skills-ref` library validates skill format:

```bash
pip install skills-ref   # or equivalent
skills-ref validate ./my-skill
```

Checks: valid YAML frontmatter, name matches directory, correct field types, no naming violations.

### 8. Zero-Cost Relevance for Beer/SakThai

- **Skills are free** — no paid service required. Everything is file-based and open-source.
- **The Sak Family Agents already use a skill-based architecture** (Hermes skills at `~/.hermes/skills/`). The Agent Skills format provides a complementary, cross-product standard that SakThai agents could adopt for sharing skills with the wider ecosystem.
- **Beer can publish his own skills** on agentskills.io or distribute them via GitHub — no HF Pro needed.
- **The `hf-cli` skill** is directly useful: it teaches any agent how to use the `hf` CLI for Hub operations, complementing the HF MCP Server.
- **Cross-installable**: Sak skills written in Agent Skills format would work in Claude Code, Cursor, Copilot, etc. — making Beer's workflows portable.

### 9. Key Distinction: Hermes Skills vs. Agent Skills

| Aspect | Hermes Skills | Agent Skills |
|--------|--------------|--------------|
| Format | YAML frontmatter + body in a `SKILL.md` | YAML frontmatter + body in a `SKILL.md` |
| Name field | `name:` in YAML frontmatter | `name:` in YAML frontmatter |
| Author field | `author: SakThai` (required) | `metadata.author` (optional) |
| License field | `license: MIT` (required) | `license:` (optional) |
| Location | `~/.hermes/skills/` | `.agents/skills/` or plugin marketplace |
| Client | Hermes agent only | Any Agent Skills-compatible client (30+) |
| Load model | At startup via skill_view | Progressive disclosure |
| Extra dirs | `references/` only | `scripts/`, `references/`, `assets/` |
| Validation | Built into Hermes | `skills-ref` CLI |
| Publishing | Private git repo | agentskills.io, GitHub, plugin marketplaces |

The formats are structurally compatible — a Hermes SKILL.md with `author: SakThai` and `license: MIT` can serve as a valid Agent Skills SKILL.md with minimal adjustment.

### 10. Skill Creators' Resources

- **Quickstart**: Create a skill in 5 minutes — https://agentskills.io/skill-creation/quickstart.md
- **Best practices**: Well-scoped, calibrated skills — https://agentskills.io/skill-creation/best-practices.md
- **Optimizing descriptions**: Test and improve trigger reliability — https://agentskills.io/skill-creation/optimizing-descriptions.md
- **Evaluating skills**: Eval-driven quality iteration — https://agentskills.io/skill-creation/evaluating-skills.md
- **Using scripts**: Bundling executable code — https://agentskills.io/skill-creation/using-scripts.md

### Skill
mlops/huggingface-hub — Hub API, MCP Server, CLI, Agent Skills, and agent integration

---

## 2026-07-25: huggingface-hub-http-request-lifecycle-source-deep-dive — Internal HTTP Request Lifecycle of `huggingface_hub`

**Topic:** huggingface-hub-http-request-lifecycle-source-deep-dive  
**Learned:** 2026-07-25  
**Author:** SakThai  
**License:** MIT  
**Source:** Source code analysis of `huggingface_hub` v1.24.0 (`utils/_http.py`, `utils/_headers.py`, `utils/_auth.py`, `hf_api.py`, `hf_file_system.py`)

### Summary

Deep-dive into the internal HTTP request lifecycle of `huggingface_hub` v1.24.0 — from token resolution → header building → session management → retry/backoff → error refinement. Critical for debugging API failures, optimizing performance, and understanding the full stack of Hub interactions.

### Key Architectural Discovery: `httpx` (not `requests`)

The library uses **`httpx`** as its HTTP backend — not the more common `requests` library. This matters for several reasons:

- `httpx.Client` provides connection pooling, event hooks, and async support natively
- `timeout=None` by default (infinite), which means connection hangs won't auto-abort
- `follow_redirects=True` by default on the shared client
- The `httpx.HTTPStatusError` exception hierarchy differs from `requests`

```python
# The underlying client
import httpx
from huggingface_hub.utils import get_session

client = get_session()
assert isinstance(client, httpx.Client)  # True
```

### 1. Token Resolution Pipeline

`get_token()` (`utils/_auth.py`) resolves credentials in this priority order:

1. **OIDC token exchange** (if `HF_OIDC_RESOURCE` env var set) — used by Trusted Publishers in CI environments. Short-lived tokens via OIDC protocol. Failure here raises `OIDCError` (no silent fallback since opting into OIDC is explicit).
2. **`HF_TOKEN` environment variable** — direct string read. Most common in production/CI.
3. **Token file** (`~/.cache/huggingface/token`) — cached user token. OAuth tokens with refresh tokens are **transparently refreshed** when close to expiry (network call + file write) before being returned.
4. **Google Colab secrets vault** (`google.colab.userdata.get("HF_TOKEN")`) — read once per session with a lock to avoid thread-safety issues.

The `get_token_to_send()` function in `_headers.py` handles the decision logic for whether to actually send the token:

- `token=True` → must resolve token or raise `LocalTokenNotFoundError`
- `token=False` → suppress auth header entirely
- `token=None` → resolve unless `HF_HUB_DISABLE_IMPLICIT_TOKEN` is set (to avoid unnecessary file reads/OAuth refresh)
- `token="<explicit string>"` → use as-is

### 2. Header Building (`build_hf_headers`)

The `build_hf_headers()` function constructs:

- **User-Agent**: Composed as `{library_name}/{library_version}; hf_hub/{hf_hub_version}; python/{python_version}`. Optionally appends `torch/{version}` and agent info (detected via `detect_agent()`). Telemetry can be disabled with `HF_HUB_DISABLE_TELEMETRY`.
- **Authorization**: `Bearer {token}` if token is resolved.
- **Custom headers**: Additional headers passed via `headers` parameter (merged after default headers, overriding if keys collide).

User-agent origin can be extended via `HF_HUB_USER_AGENT_ORIGIN` environment variable.

### 3. Session Management (`utils/_http.py`)

**Single global client (sync)**: `get_session()` returns a module-level singleton `httpx.Client`:

```python
def get_session() -> httpx.Client:
    global _GLOBAL_CLIENT
    if _GLOBAL_CLIENT is None:
        with _CLIENT_LOCK:
            _GLOBAL_CLIENT = _GLOBAL_CLIENT_FACTORY()
    return _GLOBAL_CLIENT
```

Default client factory:
```python
def default_client_factory() -> httpx.Client:
    return httpx.Client(
        event_hooks={"request": [hf_request_event_hook]},
        follow_redirects=True,
        timeout=None,
    )
```

Key implications:
- **Thread-safe creation** via `_CLIENT_LOCK` (threading.Lock)
- **No timeout** (`timeout=None`) — requests can hang indefinitely
- Connection pool is shared across all requests
- `atexit.register(close_session)` ensures clean shutdown
- `os.register_at_fork(after_in_child=close_session)` reinitializes after `fork()` to avoid sharing SSL/connection state

**Custom factory**: `set_client_factory(factory)` replaces the factory, closing any existing client first.

**No shared async client**: `get_async_client()` creates a *new* client on every call (not shared). The async event hook (`async_hf_response_event_hook`) pre-reads response bodies for error handling.

### 4. Event Hooks

**`hf_request_event_hook`** runs before every request:

1. **Offline mode check**: If `HF_HUB_OFFLINE` is set, raises `OfflineModeIsEnabled` immediately.
2. **Request ID injection**: Adds `X-Amzn-Trace-Id` header (UUID4 if not already present). Also checks `X-Request-Id` first for backward compatibility.
3. **Debug logging**: Logs method, URL, and auth status. If `HF_DEBUG` is set, also logs a full curl command (with credentials redacted).

**`async_hf_response_event_hook`** (async only): pre-reads error response bodies for status >= 400 to ensure error info is available when the exception is raised, but only if `Content-Length < 1MB` (to avoid OOM).

### 5. Request Execution: Two Paths

#### 5a. Simple requests (most `HfApi` methods)
Most `HfApi` methods use the pattern:
```python
response = get_session().get(url, headers=self._build_hf_headers(token=token))
hf_raise_for_status(response)
```
This uses the shared client directly — no retry logic at this level. Examples: `whoami`, `list_models`, `repo_info`, `list_files`.

#### 5b. Backoff-protected requests (uploads, downloads)
For operations that need retry resilience (uploads, large downloads), `http_backoff()` is used:
```python
response = http_backoff("PUT", upload_url, data=data)
```

`http_backoff` is used in:
- Upload operations: `upload_file`, `upload_folder`, `create_commit`
- File downloads: via `hf_hub_download` / `snapshot_download` (through `_httpx_follow_relative_redirects_with_backoff`)
- Any `put`/`post` that could fail transiently

### 6. Retry/Backoff Internals (`_http_backoff_base`)

The custom backoff engine (no external `backoff` library dependency):

```
Default parameters:
  max_retries = 5
  base_wait_time = 1s
  max_wait_time = 8s
  retry_on_exceptions = (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError)
  retry_on_status_codes = (408, 429, 500, 502, 503, 504)
```

**Retry flow**:

1. On **exceptions** (timeout, network error, protocol error):
   - `ConnectError` triggers `close_session()` — invalidates the client to force SSL renegotiation
   - Exhausts max_retries → re-raises the original exception

2. On **status codes** (429, 5xx, 408):
   - Checks `ratelimit` header (IETF standard) for `r` (remaining) and `t` (reset-in-seconds)
   - Falls back to `Retry-After` header (delay-seconds format only, not HTTP-date)
   - Uses ratelimit reset time + 1s if available, otherwise exponential backoff: `sleep = min(max_wait_time, sleep * 2)`

3. **IO-aware data rewind**: If `data` is a file/IO object, `seek(initial_pos)` is called before each retry to rewind the stream — critical for upload retries.

### 7. Error Refinement (`hf_raise_for_status`)

The `hf_raise_for_status()` function is the single chokepoint for error handling. It:

1. First calls `_warn_on_warning_headers()` to parse `X-HF-Warning` headers (each topic warned once per process).

2. Then refines `HTTPStatusError` into specific exception types based on:
   - **`X-Error-Code`** header: `RepoNotFound`, `RevisionNotFound`, `EntryNotFound`, `GatedRepo`
   - **`X-Error-Message`** header: `"Access to this resource is disabled."` → `DisabledRepoError`
   - **URL patterns**: Parses repo type/ID from URL for richer error context
   - **Bucket API URLs**: Separate `BucketNotFoundError`
   - **Job API URLs**: Separate `JobNotFoundError`
   - **Status codes**: 400 → `BadRequestError`, 403 → `HfHubHTTPError`, 429 → rate-limit specific `HfHubHTTPError`, 416 → range error

3. **Server message extraction**: Tries to parse error body as JSON (`response.json()`), extracting from `error`, `error_description`, and `errors` fields. Falls back to raw text for non-HTML responses.

4. **Request ID enrichment**: Extracts `X-Request-Id`, `X-Amzn-Trace-Id`, or `x-amz-cf-id` and injects into the error message for easier debugging.

```python
# Exception mapping summary:
# 404 + X-Error-Code: RepoNotFound  → RepositoryNotFoundError
# 404 + bucket URL                  → BucketNotFoundError
# 404 + job URL                     → JobNotFoundError
# 401 + repo URL                    → RepositoryNotFoundError (ambiguous 401→404)
# X-Error-Code: RevisionNotFound    → RevisionNotFoundError
# X-Error-Code: EntryNotFound       → RemoteEntryNotFoundError
# X-Error-Code: GatedRepo           → GatedRepoError
# X-Error-Message: "disabled"       → DisabledRepoError
# 400                               → BadRequestError
# 403                               → HfHubHTTPError
# 429                               → HfHubHTTPError (with rate limit info)
# 416                               → HfHubHTTPError (with range info)
# All other errors                  → HfHubHTTPError
```

### 8. Rate Limit Header Parsing

The `parse_ratelimit_headers()` function implements the IETF draft standard (`draft-ietf-httpapi-ratelimit-headers-09`):

```
Header example:
  ratelimit: "api";r=0;t=55
  ratelimit-policy: "fixed window";"api";q=500;w=300

Parsed result:
  RateLimitInfo(resource_type="api", remaining=0, reset_in_seconds=55, limit=500, window_seconds=300)
```

The `resource_type` field distinguishes between different rate limit scopes (e.g., `"api"` for general API, `"upload"` for upload-specific limits).

### 9. Debug Facilities

**`HF_DEBUG` environment variable**: When set, every request is logged as a curl command via `_curlify()`, with:
- `authorization` header redacted (→ `<TOKEN>`)
- Sensitive body fields redacted (OAuth tokens, client secrets, device codes via `_redact_sensitive_body()`)
- Body truncated to 1000 chars
- Streaming bodies shown as `<streaming body>`

**`hf_request_event_hook`** logs every request at debug level with a unique request ID, making it possible to correlate client-side logs with server-side request traces.

### 10. Offline Mode

`HF_HUB_OFFLINE` environment variable → prevents all outgoing requests:
```python
if constants.is_offline_mode():
    raise OfflineModeIsEnabled(
        f"Cannot reach {request.url}: offline mode is enabled."
    )
```
This is checked in the request event hook — the earliest possible intercept point — before any connection attempt.

### 11. File Download Pipeline (`file_download.py`)

For model/dataset file downloads, an additional HTTP layer exists:

- `_httpx_follow_relative_redirects_with_backoff()` — wraps `http_backoff()` and follows relative `Location` redirects to handle renamed repos. Stops at absolute redirects (which go to CDN).
- `hf_hub_download` uses `http_backoff()` for metadata checks (HEAD requests) and raw `get_session().stream()` for the actual download, with `resume_size` and `Range` header support.
- The `hf_transfer` Rust accelerator (`HF_HUB_ENABLE_HF_TRANSFER=1`) bypasses Python entirely for downloads — using a separate native binary that speaks HTTP directly with multithreaded chunking.

### Key Takeaways

1. **`httpx` is the engine**, not `requests` — don't look for `requests.Session` or `requests.adapters` configuration.
2. **No default timeout** — the global client has `timeout=None`. Set via `set_client_factory` if needed.
3. **Retry is opt-in** — most read-only `HfApi` methods don't use `http_backoff`; only uploads and downloads do.
4. **Token resolution is layered** — OIDC → env → file → Colab, each with distinct error semantics.
5. **Error refinement is URL-aware** — the same 404 means different things depending on whether the URL is a repo, bucket, or job endpoint.
6. **Rate limit headers follow IETF draft** — parse both resource-specific limits and policy windows.

## 2026-07-25: hf-hub-hfuri-mount-volume-system — HfUri, HfMount, and Volume API for Spaces & Jobs

### Summary
Deep dive into the new Hugging Face Hub URI system (`hf://`), Mount specifications (`hf://...:<MOUNT_PATH>[:ro|:rw]`), and the Volume API for Space/Job resource mounting. Introduced in `huggingface_hub v1.24.0`. The `HfUri` dataclass provides a unified parser for identifying any Hub resource (model, dataset, space, kernel, or bucket) along with an optional revision and sub-path. `HfMount` extends this with a local mount path and read-only flag. The `Volume` dataclass (with `set_space_volumes`/`delete_space_volumes` API) replaces the deprecated `request_space_storage` for Spaces, while `sync_job_volume` enables local-to-bucket syncing for Job volumes.

### Key Components

**1. HfUri — Canonical Hub Resource Identifier**
- Grammar: `hf://[<TYPE>/]<ID>[@<REVISION>][/<PATH>]`
- Type prefixes (plural mandated): `models/`, `datasets/`, `spaces/`, `kernels/`, `buckets/`
- Default type (no prefix): `model`
- Special ref handling: `refs/pr/N` and `refs/convert/<name>` matched eagerly (contain `/`)
- Revisions with `/` not matching special refs are URL-encoded as `%2F`
- Bucket URIs never carry a revision
- Accepted URI types from source: `model`, `dataset`, `space`, `kernel`, `bucket`
- Properties: `.type`, `.id`, `.revision` (optional), `.path_in_repo` (default `""`), `.is_bucket`, `.is_repo`
- `.to_uri()` — renders canonical `hf://` string
- `.to_url(endpoint)` — renders Hugging Face web URL (e.g. `https://huggingface.co/org/model`)

**2. HfMount — Mount Specification**
- Grammar: `hf://[<TYPE>/]<ID>[@<REVISION>][/<PATH>]:<MOUNT_PATH>[:ro|:rw]`
- Fields: `source` (HfUri), `mount_path` (absolute, starts with `/`), `read_only` (optional bool)
- `.to_uri()` — renders mount URI
- Parsing: `parse_hf_mount(mount_str)` returns `HfMount`
- Mount path always starts with `:/` delimiter; uses rfind to handle edge cases

**3. Volume Class — API-facing mount descriptor**
```python
@dataclass
class Volume:
    type: Literal["bucket", "model", "dataset", "space"]
    source: str              # repo or bucket ID
    mount_path: str          # absolute path in container
    revision: str | None     # git revision (repos only)
    read_only: bool | None   # True for repos, default False for buckets
    path: str | None         # subfolder prefix inside resource
```
- `.to_dict()` — serializes to Hub API JSON payload (uses camelCase keys)
- `.to_uri()` — renders as `hf://` mount URI via `HfMount`

**4. set_space_volumes / delete_space_volumes — New Space Volume API**
- `api.set_space_volumes(repo_id, volumes)` — replaces ALL volumes on a Space; raises `BadRequestError` on static Spaces
- `api.delete_space_volumes(repo_id)` — removes ALL volumes from a Space; raises `BadRequestError` if none attached
- `api.get_space_runtime(repo_id)` — returns `SpaceRuntime` with `.volumes: list[Volume] | None`
- `request_space_storage` deprecated in v1.24.0, will be removed in v2.0

**5. sync_job_volume — Job Volume Sync**
- `api.sync_job_volume(source, mount_path, *, remote_name, read_only, namespace)` returns `Volume`
- Syncs local directory to `{namespace}/jobs-artifacts` bucket (auto-created private)
- Uses same sync logic as `sync_bucket` — re-syncing only uploads new/modified files
- Default subfolder name derived from directory path + hostname; pass `remote_name` for fixed name
- Read-only by default; pass `read_only=False` for Job output volumes
- Empty directories get `.keep` placeholder so volume mounts succeed
- Returns a `Volume` ready for `run_job`/`run_uv_job`/`create_scheduled_job`/`create_scheduled_uv_job`

**6. duplicate_repo with space_volumes**
- `api.duplicate_repo(from_id, to_id, *, repo_type, space_volumes=..., ...)` — new unified duplication API
- `duplicate_space()` deprecated in favor of `duplicate_repo(repo_type="space")`
- `space_volumes` parameter accepts `list[Volume]` for the duplicate

**7. Web URL to HF URI Parsing**
- `parse_hf_uri()` accepts both `hf://` URIs and Hugging Face web URLs (auto-detected)
- Supported URL routes: `blob`, `resolve`, `raw`, `tree`, `blame` (repos); `resolve`, `tree` (buckets)
- User/org pages, listing pages, and non-location routes (commit, discussions, settings, edit) rejected
- Self-hosted endpoints supported via `endpoint` parameter
- Constants: `HF_PROTOCOL="hf://"`, `HF_URI_TYPE_PREFIXES={models: model, datasets: dataset, spaces: space, kernels: kernel, buckets: bucket}`, `HF_URL_HOSTS={hf.co, huggingface.co, hub-ci.huggingface.co}`

### Key Design Decisions
- Singular type names rejected with helpful error
- `HfUri` is frozen/hashable — safe for caching and use as dict keys
- Mount paths use rfind(`:/`) to avoid splitting on `:` in Windows-style paths
- Bucket URIs explicitly reject revision markers (`@`)
- `Volume.to_uri()` uses HfMount internally for CLI compatibility
- Model URLs are at root; others under type prefix

### API Integration
- SpaceRuntime includes `volumes: list[Volume] | None` field populated from API response
- `SpaceRuntime` also tracks `dev_mode: bool`, `storage: SpaceStorage | None`, `hot_reloading: SpaceHotReloading | None`
- Volumes in SpaceRuntime are created via `Volume(**v)` from raw API dict

### Practical Usage
```python
from huggingface_hub import HfApi, Volume, parse_hf_uri, parse_hf_mount

# Parse URIs and web URLs
uri = parse_hf_uri("hf://datasets/my-org/my-dataset@v1/train.csv")
uri.to_url()  # full Hugging Face web URL

# Mount specification
mount = parse_hf_mount("hf://models/org/model:/models:ro")
mount.to_uri()  # canonical mount URI

# Volume for Spaces API
api = HfApi()
volumes = [
    Volume(type="bucket", source="my-org/my-bucket", mount_path="/data"),
    Volume(type="model", source="other-org/base-model", mount_path="/model", read_only=True),
]
api.set_space_volumes("my-org/my-space", volumes)
runtime = api.get_space_runtime("my-org/my-space")
for vol in runtime.volumes:
    print(f"{vol.type}: {vol.source} -> {vol.mount_path}")

# Volume for Jobs
vol = api.sync_job_volume("./inputs", mount_path="/inputs", remote_name="eval-data-v3")
job = api.run_uv_job("run_eval.py", volumes=[vol], flavor="cpu-upgrade")
```

### Zero-Cost Relevance
- Volumes for Spaces are available on free CPU Basic hardware (static Spaces not supported)
- `sync_job_volume` syncs to free `jobs-artifacts` bucket (public unlimited, private with limits)
- Mounting models/datasets as volumes costs nothing extra — read-only references to existing resources
- Bucket volumes may incur storage costs for large data; keep buckets public for free unlimited storage
- The `hf://` URI system itself is free — a standardized way to reference Hub resources

### Skill Updated
`mlops/huggingface-hub/` — added HfUri/HfMount/Volume reference to `references/hf-learnings.md`

---

## 2026-07-25: hf-spaces-hot-reload-architecture-deep-dive — Hot Reload & Dev Mode for Spaces

### Summary
Comprehensive source-code deep-dive into the Hugging Face Spaces Hot Reload system (`huggingface_hub._hot_reload`), which enables live code reloading on running Spaces without full container rebuilds. Built on top of **Dev Mode** (a PRO/Team feature that keeps the container alive between restarts), the Hot Reload infrastructure uses Server-Sent Events (SSE) to push incremental code changes to individual replicas. This is the first time the full internal architecture of this system has been documented from source.

### Architecture Overview

The Hot Reload system has three layers:

1. **Dev Mode** — Toggle on/off via `enable_space_dev_mode()`/`disable_space_dev_mode()`. Keeps the Space container running while the application restarts. Required before hot reloading can work. Available on PRO and Team & Enterprise plans.

2. **Commit with `_hot_reload=True`** — Pass the private `_hot_reload=True` parameter to `create_commit()` (or `upload_folder()` which wraps it). This adds `?hot_reload=1` as a query parameter to the commit API endpoint (`POST /api/{type}s/{repo_id}/commit/{revision}`), signalling the Hub to notify all running replicas.

3. **SSE-based Reload Client** — Each running Space replica runs a reload server on port **7887** (subdomain-based: `{space}--7887.hf.space`). The `ReloadClient` connects to this endpoint and streams reload events via SSE.

### Source Code Structure

All hot reload source lives under `huggingface_hub/_hot_reload/` (Copyright 2026, new in v1.24.0):

| File | Purpose |
|------|---------|
| `__init__.py` | Package marker (license only, no exports) |
| `types.py` | TypedDict definitions for all reload API request/response shapes |
| `sse_client.py` | Vendored SSE client (from `mpetazzoni/sseclient`, Apache-2.0) |
| `client.py` | `ReloadClient` and `multi_replica_reload_events()` — core Hot Reload logic |

### Types Reference (`types.py`)

**Operation Types** (the actual events streamed during reload):

| Type | Kind | Description |
|------|------|-------------|
| `ReloadOperationObject` | `"add"` / `"update"` / `"delete"` | File-level object change: `objectType`, `objectName`, `region` |
| `ReloadOperationRun` | `"run"` | Execute code block: `codeLines`, `stdout`, `stderr` |
| `ReloadOperationException` | `"exception"` | Runtime exception with `traceback` string |
| `ReloadOperationError` | `"error"` | Fatal reload error with `traceback` |
| `ReloadOperationUI` | `"ui"` | UI change notification: `updated: bool` |
| `ReloadOperationFile` | `"file"` | File creation notification: `created: bool` |

**API Request/Response Types:**

| TypedDict | Purpose |
|-----------|---------|
| `ApiCreateReloadRequest` | `{filepath, contents, reloadId?}` — trigger a reload on a specific file |
| `ApiCreateReloadResponseSuccess` | `{status: "created", reloadId: str}` |
| `ApiCreateReloadResponseError` | `{status: "alreadyReloading" | "fileNotFound"}` |
| `ApiGetReloadRequest` | `{reloadId: str}` — poll/pull reload events by ID |
| `ApiGetReloadEventSourceData` | Stream of `ReloadOperation*` events emitted during reload |
| `ApiGetStatusRequest` | `{revision: str}` — check if a revision has been reloaded |
| `ApiGetStatusResponse` | `{reloading: bool, uncommitted: list[str]}` |
| `ApiFetchContentsRequest` | `{filepath: str}` — fetch file contents from running Space |
| `ApiFetchContentsResponse` | `{status: "ok" | "fileNotFound", contents?: str}` |

### ReloadClient (`client.py`)

Key design:
- Each replica is addressed by its `replica_hash` via the `--replicas/+{hash}` URL path segment
- GET reload returns an SSE stream — events are parsed by the vendored `SSEClient`
- Non-200/204 status codes raise exceptions; 204 means "reloadId not found" (retryable)
- 20-second client timeout (`CLIENT_TIMEOUT`)

### Multi-Replica Coordination (`multi_replica_reload_events()`)

This function:
1. Creates one `ReloadClient` per replica hash
2. For each replica, calls `get_reload(commit_sha)` with up to `max_retries` retries
3. Tracks all events from the first replica as the reference (`first_client_events`)
4. For subsequent replicas, checks if their stream matches the first replica's events exactly
5. **Deduplication**: events that are identical across replicas are suppressed; only the first replica's events are yielded, plus a `fullMatch` marker for replicas that match exactly
6. **Partial match**: if a replica diverges mid-stream, replay backlog then yield fresh events

### SpaceRuntime Integration

The `SpaceRuntime` dataclass (in `_space_api.py`) exposes hot reload state:
- `dev_mode: bool` — is dev mode enabled?
- `hot_reloading: SpaceHotReloading | None` — active reload if any

`SpaceHotReloading.status` is `"created"` (reload initiated), `"canceled"` (reload aborted), or `None` (pending). The `replica_statuses` field contains per-replica status tuples.

### Dev Mode API
```python
api.enable_space_dev_mode("user/my-space")   # POST /api/spaces/{id}/dev-mode {"enabled": True}
api.disable_space_dev_mode("user/my-space")  # POST /api/spaces/{id}/dev-mode {"enabled": False}
```

### End-to-End Flow
1. Enable Dev Mode → keeps container alive
2. Commit with `_hot_reload=True` → `POST .../commit/main?hot_reload=1`
3. Hub notifies running replicas → each replica streams SSE events on port 7887
4. Events: object add/update/delete, code run, UI update, file create (or exception/error)
5. Poll `get_space_runtime()` → `hot_reloading.status` to verify completion

### Key Design Decisions
1. **SSE over WebSocket** — simpler, unidirectional, HTTP-based
2. **Per-replica port naming** — `--7887` subdomain avoids port conflicts
3. **First-replica dedup** — first replica's events are canonical; subsequent matching replicas yield `fullMatch`
4. **Private `_hot_reload`** — experimental/PRO-only, not in public docs
5. **10 retries** — 2s sleep on 204 (reloadId propagation delay)

### Zero-Cost Relevance
- Dev Mode requires PRO ($9/mo) — not on free tier
- Understanding the architecture helps with debugging Spaces and contributing to `huggingface_hub` open source
- The vendored `sse_client.py` (Apache-2.0) is reusable for any SSE integration

### Files Analyzed
| File | Lines |
|------|-------|
| `huggingface_hub/_hot_reload/types.py` | 121 |
| `huggingface_hub/_hot_reload/sse_client.py` | 144 |
| `huggingface_hub/_hot_reload/client.py` | 130 |
| `huggingface_hub/hf_api.py` (rel. sections) | ~120 |
| `huggingface_hub/_space_api.py` (rel. sections) | ~30 |
| `huggingface_hub/_commit_api.py` (rel. sections) | ~20 |
| **Total code analyzed** | **~565 lines** |

### Skill Updated
`mlops/huggingface-hub/` — added Hot Reload & Dev Mode reference to `references/hf-learnings.md`

---

