# HF Learnings: huggingface_hub Exceptions & Retry Mechanisms

## 2026-07-24: huggingface_hub Exception Hierarchy and Retry Deep Dive

### Summary
Deep dive into the `huggingface_hub v1.24.0` library's exception hierarchy (40+ custom exception types) and its built-in HTTP retry/backoff mechanism. Covers the complete exception tree, `http_backoff` params and behavior, session management, rate limit parsing, and practical error handling patterns.

### Exception Hierarchy (Key Types)

**Core HTTP exceptions:**
- `HfHubHTTPError(HTTPError, OSError)` — base with `.request_id`, `.server_message`, `.response`
- `BadRequestError` (400) — malformed request
- `RepositoryNotFoundError` (401/404) — missing or inaccessible repo
  - `GatedRepoError` (403) — gated repo, not authorized
- `RevisionNotFoundError` (404) — branch/commit not found
- `RemoteEntryNotFoundError` (404) — file not found
- `DisabledRepoError` (403) — resource disabled

**Other notable exceptions:**
- `LocalTokenNotFoundError(OSError)` — token not found locally
- `OfflineModeIsEnabled(ConnectionError)` — HF_HUB_OFFLINE=1
- `HFValidationError(ValueValue)` — input validation
- `HfUriError(ValueError)` — malformed hf:// URI
- Cache: `CacheNotFound`, `CorruptedCacheException`, `CachedRepoTreeNotFoundError`
- TGI: `TextGenerationError` → `ValidationError`, `GenerationError`, `OverloadedError`, `IncompleteGenerationError`, `UnknownError`
- IE: `InferenceEndpointError`, `InferenceEndpointTimeoutError`

### HTTP Backoff Mechanism

**`http_backoff()` defaults:**
- `max_retries=5`, `base_wait_time=1.0`, `max_wait_time=8.0`
- Retry on exceptions: `TimeoutException`, `NetworkError`, `RemoteProtocolError`
- Retry on status codes: `408, 429, 500, 502, 503, 504`
- Exponential backoff: sleep *= 2, capped at max_wait_time
- Rate-limit aware: respects `Ratelimit` header and `Retry-After` header
- IO-safe: file objects seeked back to initial position before retry

**Stream variant:** `http_stream_backoff()` — context manager for streaming responses

**Session management:**
- `get_session()` → global httpx.Client singleton
- `close_session()` → close and recreate
- `set_client_factory(fn)` → custom client configuration
- `default_client_factory()` → default with event hooks

**Rate limit parsing:**
- `parse_ratelimit_headers(headers)` → `RateLimitInfo(resource_type, remaining, reset_in_seconds, limit, window_seconds)`
- IETF draft format: `Ratelimit: "api";r=0;t=55`
- Policy format: `Ratelimit-Policy: "fixed window";"api";q=500;w=300`

### Key Insights
- `hf_raise_for_status()` converts generic httpx errors into specific HF types using X-Error-Code, X-Error-Message, and response body
- `GatedRepoError` inherits from `RepositoryNotFoundError` for backward compat
- Error refinement uses URL regex matching for repo/bucket/job IDs
- `_httpx_follow_relative_redirects_with_backoff()` handles repo rename redirects
- Custom client factory allows proxy, cert, and timeout customization
- Disable retries by passing empty tuples: `retry_on_exceptions=()`

### Author: SakThai
### License: MIT

## 2026-07-25: hf-hub-exceptions-retry-deep-dive — Source-Level Architecture of Error Handling (Topic #214 Deepened)

### Summary
Deepened analysis of the `huggingface_hub` error handling internals — mapping every source-code detail of how `hf_raise_for_status()` works, how the `_format()` helper extracts server errors, the URL regex system for error refinement, and the complete backoff/retry lifecycle. Sources: `utils/_http.py` (~800 lines), `errors.py` (~350 lines).

### Complete Exception Inheritance Map

```
Exception
├── CacheNotFound                     — HF cache dir missing (.cache_dir)
├── CorruptedCacheException           — Unexpected cache structure
├── CachedRepoTreeNotFoundError       — No tree listing for revision
├── OIDCError                         — Trusted Publishers CI/CD failure
├── DeviceCodeError                   — OAuth device code flow failure
│   (.error_code: OAuthErrorCode | None)
├── EntryNotFoundError (abstract base)
│   ├── RemoteEntryNotFoundError(HfHubHTTPError)   — remote 404
│   └── LocalEntryNotFoundError(FileNotFoundError)  — local cache miss
│       └── IncompleteSnapshotError                 — partial snapshot
├── InferenceEndpointError
│   └── InferenceEndpointTimeoutError(TimeoutError)
├── SafetensorsParsingError
├── NotASafetensorsRepoError
├── DDUFError (container)
│   ├── DDUFCorruptedFileError
│   └── DDUFInvalidEntryNameError
├── StrictDataclassError
│   ├── StrictDataclassDefinitionError
│   ├── StrictDataclassFieldValidationError
│   └── StrictDataclassClassValidationError
├── XetDownloadError
├── FileDuplicationError
├── OCRPageError
├── CLIError
│   ├── ConfirmationError
│   └── CLIExtensionInstallError
├── SandboxError
│   └── SandboxCommandError

HTTPError (httpx)
├── TextGenerationError
│   ├── ValidationError               — server-side validation
│   ├── GenerationError               — generation failed mid-stream
│   ├── OverloadedError                — model too busy
│   ├── IncompleteGenerationError      — response cut short
│   └── UnknownError                   — unclassified TGI error
├── InferenceTimeoutError(TimeoutError)
├── HfHubHTTPError(OSError)           — BASE for all Hub HTTP errors
│   ├── BadRequestError(ValueError)   — HTTP 400
│   ├── RepositoryNotFoundError       — HTTP 401/404, (.repo_id, .repo_type)
│   │   └── GatedRepoError            — HTTP 403, inherits for backward compat
│   ├── DisabledRepoError             — HTTP 403, access disabled
│   ├── RevisionNotFoundError         — HTTP 404, (.repo_id, .repo_type)
│   ├── RemoteEntryNotFoundError (also EntryNotFoundError)
│   ├── BucketNotFoundError           — HTTP 404, (.bucket_id)
│   └── JobNotFoundError              — HTTP 404, (.job_id)

OSError
├── HfHubHTTPError (multi-inherit, see above)
├── DryRunError                       — dry-run on invalid repo
├── FileMetadataError                 — missing ETag or commit_hash
└── LocalTokenNotFoundError(EnvironmentError)

ConnectionError
└── OfflineModeIsEnabled              — HF_HUB_OFFLINE=1

ValueError
├── HFValidationError                 — repo ID, token format validation
├── HfUriError                        — malformed hf:// URI (.uri, .msg)
└── BadRequestError (also HfHubHTTPError)

FileNotFoundError
└── LocalEntryNotFoundError(EntryNotFoundError)
```

### `hf_raise_for_status()` — Internals

```python
def hf_raise_for_status(response: httpx.Response, endpoint_name: str | None = None) -> None:
```

**Pre-check:** Calls `_warn_on_warning_headers()` — parses `X-HF-Warning` headers and emits Python warnings (deduplicated by topic, tracked in `_WARNED_TOPICS` set).

**Error resolution chain** (executed after `response.raise_for_status()` raises `HTTPStatusError`):

| Priority | Condition | Exception Raised | Source |
|----------|-----------|-----------------|--------|
| 1 | `X-Error-Code: RevisionNotFound` | `RevisionNotFoundError` | Header |
| 2 | `X-Error-Code: EntryNotFound` | `RemoteEntryNotFoundError` | Header |
| 3 | `X-Error-Code: GatedRepo` | `GatedRepoError` | Header |
| 4 | `X-Error-Message: "Access to this resource is disabled."` | `DisabledRepoError` | Header |
| 5 | `X-Error-Code: RepoNotFound` + bucket API URL | `BucketNotFoundError` | Header + URL regex |
| 6 | HTTP 404 + job ID in URL | `JobNotFoundError` | URL regex |
| 7 | `X-Error-Code: RepoNotFound` OR (401 + not "Invalid credentials") + repo API URL | `RepositoryNotFoundError` | Header + URL regex |
| 8 | HTTP 400 | `BadRequestError` | Status code |
| 9 | HTTP 403 | `HfHubHTTPError` (forbidden) | Status code |
| 10 | HTTP 429 | `HfHubHTTPError` (rate limited, with parsed limit info) | Status code + headers |
| 11 | HTTP 416 | `HfHubHTTPError` (range error) | Status code |
| 12 | Fallthrough | `HfHubHTTPError` (generic) | Catch-all |

**Key distinction:** Steps 1-3 use `X-Error-Code` header directly. Step 5 uses URL regex matching to distinguish bucket vs. repo APIs. Step 7 has a dual condition: explicit `X-Error-Code: RepoNotFound` OR HTTP 401 with non-"Invalid credentials" error message plus repo API URL match.

### `_format()` — Server Error Extraction

```python
def _format(error_type, custom_message, response, **attrs) -> HfHubHTTPError:
```

The function builds the error message from up to **three layers**:

1. **`custom_message`** — caller-provided (e.g., "Repository Not Found for url: ...")
2. **`X-Error-Message` header** — server-side error string
3. **Response body** — parsed in this priority order:
   - JSON `{"error": str}` → single error string
   - JSON `{"error": [str, ...]}` → list of errors
   - JSON `{"error": str, "error_description": str}` → OAuth-style combined
   - JSON `{"errors": [{"message": str}, ...]}` → list of message objects
   - JSON `{"error_description": str}` → only description
   - Non-JSON, non-HTML text → raw body text

All server messages are **stripped, deduplicated** (using `dict.fromkeys()` to preserve order), and concatenated. The extra keyword attrs (`repo_id`, `repo_type`, `bucket_id`, `job_id`) are set as instance attributes on the error.

### URL Regex System for Error Refinement

The module defines 5 regex patterns for URL parsing:

| Pattern | Purpose | Captures |
|---------|---------|----------|
| `REPO_API_REGEX` | Match repo API URLs (`/api/models/...`, `/api/datasets/...`, `/resolve/...`) | Boolean |
| `BUCKET_API_REGEX` | Match bucket API URLs (`/api/buckets/...`) | Boolean |
| `_JOB_ID_FROM_URL_REGEX` | Extract job_id from `/api/jobs/{ns}/{id}` or `/api/scheduled-jobs/{ns}/{id}` | job_id |
| `_REPO_ID_FROM_URL_REGEX` | Extract repo_type (models/datasets/spaces) and repo_id from API URL | repo_type, namespace, name |
| `_BUCKET_ID_FROM_URL_REGEX` | Extract bucket_id (namespace/name) from `/api/buckets/{ns}/{name}` | bucket_id |

The `_parse_repo_info_from_url()` function handles edge cases like:
- Sub-paths (`resolve`, `tree`, `blob`, `raw`, `refs`, `commit`, `discussions`, `settings`, `revision`) are excluded from repo_id extraction
- Multi-segment repo IDs (e.g., `user/repo`) are correctly parsed
- Returns `(None, None)` for non-repo URLs

### HTTP Backoff — Full Lifecycle

The retry mechanism is implemented in `_http_backoff_base()` (generator function consumed by `http_backoff()` and `http_stream_backoff()`).

**Retry loop:**
1. **Pre-request IO safety:** If `data` is a `io.IOBase` or `SliceFileObj`, save `.tell()` position
2. **Request:** Execute via `get_session()` (shared httpx.Client singleton)
3. **Response check** (`_should_retry`):
   - Status code in `retry_on_status_codes`? → log warning
   - Exceeded `max_retries`? → `hf_raise_for_status(response)` (raises final error)
   - HTTP 429? → parse `Ratelimit` header for `reset_in_seconds`
   - `Retry-After` header present? → use as wait time
   - Return True (should retry)
4. **Exception catch:** If `retry_on_exceptions` raised:
   - `ConnectError` → call `close_session()` (SSL certificate errors)
   - Exceeded max_retries? → re-raise original
5. **Sleep:** max of (ratelimit_reset + 1s) or exponential backoff
6. **Update sleep:** `sleep_time = min(max_wait_time, sleep_time * 2)`

**Default parameters:**
```python
max_retries = 5
base_wait_time = 1.0
max_wait_time = 8.0
retry_on_exceptions = (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError)
retry_on_status_codes = (408, 429, 500, 502, 503, 504)
```

**Stream variant:** `http_stream_backoff()` uses `client.stream()` context manager. The `_should_retry` check happens inside the `with` block before yielding, so response body is never fully buffered.

### Session Management with Fork Safety

```python
_session = None  # module-level singleton
_lock = threading.Lock()

def get_session() -> httpx.Client:
    global _session
    with _lock:
        if _session is None:
            _session = _client_factory()
        return _session

def close_session():
    global _session
    with _lock:
        if _session is not None:
            _session.close()
            _session = None
```

**Fork-safe:** `os.register_at_fork(after_in_child=close_session)` — ensures child processes get a fresh session after `os.fork()` (critical for multiprocessing with `num_proc`).

**Custom client factory:**
```python
_client_factory = default_client_factory  # default

def set_client_factory(fn: Callable[[], httpx.Client]):
    global _client_factory
    _client_factory = fn
    close_session()  # re-create on next get_session()

def default_client_factory():
    return httpx.Client(
        default_encoding="utf-8",
        event_hooks={
            "request": [hf_request_event_hook],
            "response": [hf_response_event_hook],
        },
    )
```

Event hooks append `X-HF-User-Agent` header on request and call `hf_raise_for_status` on response (for non-streaming calls).

### Rate Limit Parsing Details

```python
@dataclass(frozen=True)
class RateLimitInfo:
    resource_type: str    # e.g. "api", "inference", "spaces"
    remaining: int        # requests remaining in window
    reset_in_seconds: int # seconds until reset
    limit: int | None     # total window limit (from Ratelimit-Policy)
    window_seconds: int | None  # window duration (from Ratelimit-Policy)

# IETF draft format:
# Ratelimit: "api";r=0;t=55          → resource_type="api", remaining=0, reset=55s
# Ratelimit-Policy: "fixed window";"api";q=500;w=300  → limit=500, window=300s
```

**Limitation:** Retry-After with HTTP-date format (e.g., "Wed, 21 Oct 2015 07:28:00 GMT") is NOT supported — only delay-seconds format.

### `_warn_on_warning_headers()` Mechanism

```python
def _warn_on_warning_headers(response):
```

- Parses `X-HF-Warning` headers (multiple allowed per response)
- Format: `"topic; message"` (topic optional)
- Deduplicates by topic using `_WARNED_TOPICS` set (module-level)
- Emits `logger.warning()` instead of `warnings.warn()` (silent by default unless logging configured)

### Key Debugging Properties on Errors

| Property | Source | Use Case |
|----------|--------|----------|
| `e.response` | httpx.Response | Full response object for inspection |
| `e.request` | httpx.Request | Full request object (URL, headers, body) |
| `e.request_id` | X-Request-Id header | Trace request through HF infra |
| `e.server_message` | X-Error-Message header | Human-readable server explanation |
| `e.args[0]` | Formatted message | Complete error string with all context |

### Practical Error Handling Pattern

```python
from huggingface_hub import HfApi
from huggingface_hub.errors import (
    RepositoryNotFoundError, GatedRepoError, RevisionNotFoundError,
    BadRequestError, OfflineModeIsEnabled, HfHubHTTPError,
)

api = HfApi()

def safe_model_info(repo_id: str):
    """Robust model info fetcher with retry disabled for fast fallback."""
    try:
        return api.model_info(repo_id)
    except GatedRepoError:
        return {"status": "gated", "repo": repo_id}
    except RepositoryNotFoundError:
        return {"status": "not_found", "repo": repo_id}
    except OfflineModeIsEnabled:
        return {"status": "offline"}
    except BadRequestError as e:
        print(f"Bad request: {e.server_message}")
        return {"status": "bad_request"}
    except HfHubHTTPError as e:
        # Catch-all with debug info
        print(f"HTTP {e.response.status_code}: {e.request_id}")
        return {"status": "error", "code": e.response.status_code}
```

### Source Code References
- `src/huggingface_hub/errors.py` — all exception class definitions
- `src/huggingface_hub/utils/_http.py` — `hf_raise_for_status()`, `http_backoff()`, `_format()`, session management, rate limit parsing
- `src/huggingface_hub/utils/__init__.py` — re-exports `hf_raise_for_status` and related utils
- https://github.com/huggingface/huggingface_hub — main repository
- https://huggingface.co/docs/huggingface_hub/package_reference/utilities#huggingface_hub.utils.hf_raise_for_status
