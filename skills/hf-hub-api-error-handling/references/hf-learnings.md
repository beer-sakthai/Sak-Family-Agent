# HF Learnings — HF Hub API Error Handling (Source-Code Deep Dive)

## 2026-07-25: hf-hub-api-error-handling — Hugging Face Hub API Error Handling Complete Reference (Topic #325)

### Summary
Source-code-level deep dive into the Hugging Face Hub's error handling system across three layers: Python SDK (`huggingface_hub` v1.24.0), Hub REST API (X-Error-Code header system), and the retry/backoff mechanism. The previous learning file at this path was corrupted with wrong content (notification-system text) — this replaces it with the correct, comprehensive error handling reference. Covers the 40+ exception hierarchy, `hf_raise_for_status()` HTTP-to-exception mapping, `http_backoff()` retry engine, rate limit header parsing (IETF draft), offline mode enforcement, InferenceClient text generation errors, and production best practices.

### Source Files Analyzed

| File | Lines | Purpose |
|------|-------|---------|
| `huggingface_hub/errors.py` | 609 | All 40+ custom exception classes |
| `huggingface_hub/utils/_http.py` | 1161 | HTTP retry, raise_for_status, rate limit parsing, session management |
| `huggingface_hub/hf_api.py` | ~15K | API methods with additional error enrichment |
| Hub OpenAPI spec | N/A | `/.well-known/openapi.json` — X-Error-Code reference |

---

### 1. Exception Hierarchy (40+ Types)

The entire hierarchy lives in `huggingface_hub/errors.py` (~609 lines). Four major lineages:

```
Exception
├── EntryNotFoundError               # Abstract base for local + remote not-found
│   ├── RemoteEntryNotFoundError(HfHubHTTPError)
│   └── LocalEntryNotFoundError(FileNotFoundError)
│       └── IncompleteSnapshotError  # Cached snapshot known incomplete
├── CacheNotFound                    # Cache directory not found
├── CorruptedCacheException          # Unexpected cache structure
├── OIDCError                        # Trusted Publishers CI/CD auth failure
├── DeviceCodeError                  # OAuth Device Code flow failure
├── HfUriError(ValueError)           # Malformed hf:// URI
├── HFValidationError(ValueError)    # Repo ID / token validation
├── SafetensorsParsingError          # Corrupted safetensors metadata
├── NotASafetensorsRepoError         # Missing safetensors index
├── DryRunError(OSError)             # Dry run on invalid repo
├── FileMetadataError(OSError)       # Missing ETag or commit_hash
├── InferenceEndpointError           # Inference Endpoints base
│   └── InferenceEndpointTimeoutError(TimeoutError)
├── ConnectionError
│   └── OfflineModeIsEnabled         # HF_HUB_OFFLINE=1 set
├── HTTPError
│   ├── InferenceTimeoutError(TimeoutError)  # Model unavailable / TGI timeout
│   └── TextGenerationError          # Text Generation Inference base
│       ├── ValidationError          # Server-side validation
│       ├── GenerationError          # Generation failure
│       ├── OverloadedError          # Model overloaded
│       ├── IncompleteGenerationError # Partial generation
│       └── UnknownError             # Unexpected TGI error
├── HfHubHTTPError(HTTPError, OSError) # CORE: all HF API HTTP errors
│   ├── BadRequestError(ValueError)  # HTTP 400
│   ├── BucketNotFoundError          # Bucket API 404
│   ├── JobNotFoundError             # Job API 404
│   ├── RepositoryNotFoundError      # 401/404 on repo endpoints
│   │   └── GatedRepoError           # 403 on gated repo (backward compat)
│   ├── RevisionNotFoundError        # 404 on invalid revision
│   ├── RemoteEntryNotFoundError     # 404 on missing file (shared)
│   └── DisabledRepoError            # 403 when repo disabled by author
```

**Key design choices:**
- `GatedRepoError` extends `RepositoryNotFoundError` for backward compatibility — catching the parent catches both
- `RemoteEntryNotFoundError` has dual inheritance: `HfHubHTTPError` (for HTTP context) + `EntryNotFoundError` (for semantic "not found")
- `LocalEntryNotFoundError` extends `FileNotFoundError` + `EntryNotFoundError` — matches Python's built-in IO exception semantics
- All `HfHubHTTPError` subclasses carry `.request_id`, `.server_message`, `.response`, `.request` attributes

---

### 2. HfHubHTTPError Core Class

```python
class HfHubHTTPError(HTTPError, OSError):
    def __init__(
        self,
        message: str,
        *,
        response: Response,
        server_message: str | None = None,
    ):
        # Request ID from headers: X-Request-Id > X-Amzn-Trace-Id > x-amz-cf-id
        self.request_id = (
            response.headers.get("x-request-id")
            or response.headers.get("X-Amzn-Trace-Id")
            or response.headers.get("x-amz-cf-id")
        )
        self.server_message = server_message
        self.response = response
        self.request = response.request
        super().__init__(message)

    def append_to_message(self, additional_message: str) -> None:
        """Append additional info after the exception is raised."""
        self.args = (self.args[0] + additional_message,) + self.args[1:]
```

**Instance attributes available on all HfHubHTTPError instances:**

| Attribute | Source | Example |
|-----------|--------|---------|
| `.request_id` | X-Request-Id / X-Amzn-Trace-Id / x-amz-cf-id | `Root=1-6a64adab-29889d51374587b826d03dc1` |
| `.server_message` | X-Error-Message header or JSON body | `"Invalid username or password."` |
| `.response` | The full httpx.Response object | `status_code`, `.headers`, `.json()` |
| `.request` | The httpx.Request object | `.url`, `.method`, `.headers` |

**Subclass-specific attributes:**

| Exception | Extra Attrs | Populated From |
|-----------|-------------|----------------|
| `RepositoryNotFoundError` | `repo_id`, `repo_type` | URL regex parsing |
| `RevisionNotFoundError` | `repo_id`, `repo_type` | URL regex parsing |
| `RemoteEntryNotFoundError` | `repo_id`, `repo_type` | URL regex parsing |
| `GatedRepoError` | `repo_id`, `repo_type` | URL regex parsing |
| `BucketNotFoundError` | `bucket_id` | URL regex parsing |
| `JobNotFoundError` | `job_id` | URL regex parsing |

---

### 3. hf_raise_for_status() — HTTP to Exception Mapping

The central function in `_http.py` (lines 755-924) that refines generic HTTP errors into typed exceptions. Called by every Hub API method.

**Mapping logic (in order of evaluation):**

| Condition | Status Code | Exception Raised | Headers Checked |
|-----------|-------------|-------------------|-----------------|
| `X-Error-Code: RevisionNotFound` | 404 | `RevisionNotFoundError` | + repo info from URL |
| `X-Error-Code: EntryNotFound` | 404 | `RemoteEntryNotFoundError` | + repo info from URL |
| `X-Error-Code: GatedRepo` | 403 | `GatedRepoError` | + repo info from URL |
| `X-Error-Message: "Access to this resource is disabled."` | 403 | `DisabledRepoError` | None |
| `X-Error-Code: RepoNotFound` + bucket URL | 404 | `BucketNotFoundError` | + bucket_id from URL |
| 404 + job URL pattern | 404 | `JobNotFoundError` | + job_id from URL |
| `X-Error-Code: RepoNotFound` | 401/404 | `RepositoryNotFoundError` | + repo info from URL |
| 401 + not "Invalid credentials" + repo URL | 401 | `RepositoryNotFoundError` | URL regex |
| 400 | 400 | `BadRequestError` | + endpoint_name |
| 403 | 403 | `HfHubHTTPError` (generic) | + error_message |
| 429 | 429 | `HfHubHTTPError` | + rate limit info from headers |
| 416 (Range Not Satisfiable) | 416 | `HfHubHTTPError` | + Range header |
| Everything else | Any | `HfHubHTTPError` (generic) | + server message extraction |

**Confirmed X-Error-Code values (verified via live Hub API):**

| X-Error-Code | Meaning | Example |
|--------------|---------|---------|
| `RepoNotFound` | Repository doesn't exist or no access | `GET /api/models/fake/repo` |
| `RevisionNotFound` | Revision/branch/tag doesn't exist | `GET /repo/resolve/bad-rev/file` |
| `EntryNotFound` | File/path not found in repo | `GET /repo/resolve/main/nonexistent.xyz` |
| `GatedRepo` | User not authorized for gated repo | `GET /api/models/gated-org/model` |

**Server message extraction (`_format()` function, lines 957-1059):**

The `_format()` function extracts error details from three sources in priority order:

1. **`X-Error-Message` header** — simplest, most authoritative
2. **JSON response body** — several formats supported:
   - `{"error": "string"}` — simple
   - `{"error": ["error1", "error2"]}` — array
   - `{"error": "code", "error_description": "detail"}` — OAuth-style
   - `{"errors": [{"message": "..."}, ...]}` — GraphQL-like
   - `{"error_description": "..."}` — no error field
3. **Raw response text** — only if not HTML and not JSON

Request ID is extracted from headers and injected into the error message for traceability.

---

### 4. Retry / Backoff Mechanism

Two public functions: `http_backoff()` (for regular requests) and `http_stream_backoff()` (context manager for streaming). Both delegate to `_http_backoff_base()` (lines 431-529).

**Configuration:**

```python
def http_backoff(
    method: HTTP_METHOD_T,
    url: str,
    *,
    max_retries: int = 5,
    base_wait_time: float = 1,      # Initial wait (seconds)
    max_wait_time: float = 8,        # Cap after exponential growth
    retry_on_exceptions: tuple = (
        httpx.TimeoutException,
        httpx.NetworkError,
        httpx.RemoteProtocolError,
    ),
    retry_on_status_codes: tuple = (408, 429, 500, 502, 503, 504),
    **kwargs,
) -> httpx.Response:
```

**Retry decision flowchart:**

```
Request → exception or response
  ├── Exception in retry_on_exceptions?
  │     ├── Yes → nb_tries > max_retries? → Yes: re-raise
  │     │                                    No: wait and retry
  │     └── No → re-raise immediately
  └── Response received?
        ├── Status in retry_on_status_codes?
        │     ├── Yes → nb_tries > max_retries? → Yes: hf_raise_for_status()
        │     │                                    No: wait and retry
        │     └── No → return response (success)
        └── No → return response
```

**Exponential backoff with rate limit awareness:**

```python
# After each failed attempt:
if ratelimit_reset is not None:
    actual_sleep = float(ratelimit_reset) + 1  # +1s safety margin
else:
    actual_sleep = sleep_time                   # Current backoff value

time.sleep(actual_sleep)
sleep_time = min(max_wait_time, sleep_time * 2)  # Double wait, capped
```

**Important behaviors:**
- On `httpx.ConnectError`, the global shared client is closed via `close_session()` — this forces recreation on the next call, clearing potential SSL session issues
- File/IO objects in `data` parameter are saved by position and seeked back before each retry — prevents "consumed stream" errors
- Setting `retry_on_exceptions=()` or `retry_on_status_codes=()` disables retries entirely (used by `_httpx_follow_relative_redirects_with_backoff()` for fast fallback to local cache)
- Rate limit reset takes priority over exponential backoff — respects server's `Retry-After` and `Ratelimit` headers

---

### 5. Rate Limit Header Parsing

Two independent rate limit response header specs are supported:

**IETF draft header (`Ratelimit` + `Ratelimit-Policy`):**

```http
ratelimit: "api";r=497;t=174
ratelimit-policy: "fixed window";"api";q=500;w=300
```

Parsed by `parse_ratelimit_headers()` → `RateLimitInfo` dataclass:

| Field | Source | Example |
|-------|--------|---------|
| `resource_type` | `ratelimit` header group name | `"api"` |
| `remaining` | `r=` parameter | 497 |
| `reset_in_seconds` | `t=` parameter | 174 |
| `limit` | `q=` in `ratelimit-policy` | 500 |
| `window_seconds` | `w=` in `ratelimit-policy` | 300 |

**RFC 9110 `Retry-After` header:**

```http
Retry-After: 120  # delay-seconds format
# OR
Retry-After: Wed, 21 Oct 2015 07:28:00 GMT  # HTTP-date (NOT supported)
```

Parsed by `_parse_retry_after()` — only the delay-seconds format is handled. HTTP-date format returns `None` (falls back to exponential backoff).

**When both are present:** The `ratelimit` header's `t=` takes priority over `Retry-After`.

---

### 6. Session Management

The `huggingface_hub` SDK uses a shared global `httpx.Client`:

```python
# Get the global shared client
client = get_session()    # httpx.Client — shared, do NOT close manually
client = get_async_session()  # httpx.AsyncClient — NOT shared, use as context manager
```

**Key characteristics:**
- Default client: `httpx.Client(event_hooks={"request": [hf_request_event_hook]}, follow_redirects=True, timeout=None)`
- `timeout=None` means NO default timeout — timeouts are controlled per-call or by the transport layer
- `follow_redirects=True` handles most redirects automatically
- Custom client factories: `set_client_factory(fn)` replaces the factory for custom proxies/TLS
- Automatic cleanup: `atexit.register(close_session)` + `os.register_at_fork(after_in_child=close_session)`

**Request event hook (`hf_request_event_hook`)** performs:
1. Offline mode check — raises `OfflineModeIsEnabled` if `HF_HUB_OFFLINE=1`
2. Request ID injection — adds `X-Amzn-Trace-Id` (UUID) if not already present
3. Debug logging — if `HF_DEBUG=1`, logs curl-equivalent command

**Async response event hook (`async_hf_response_event_hook`):**
- For streaming responses that will return HTTP 4xx/5xx, pre-reads the body (if Content-Length < 1MB) so error details are available when the exception is raised

---

### 7. Offline Mode Enforcement

The offline mode check happens at the HTTP transport layer, not at the application level:

```python
# In hf_request_event_hook:
if constants.is_offline_mode():
    raise OfflineModeIsEnabled(
        f"Cannot reach {request.url}: offline mode is enabled. "
        "To disable it, please unset the `HF_HUB_OFFLINE` "
        "environment variable."
    )
```

**Activation:** `HF_HUB_OFFLINE=1` environment variable (any truthy value)
**Effect:** Every single HTTP request through `get_session()` immediately raises `OfflineModeIsEnabled(ConnectionError)` before any network I/O
**Catch pattern:** `except (OfflineModeIsEnabled, ...)` since it's a `ConnectionError` subclass

---

### 8. X-HF-Warning Header System

Deprecation and non-critical warnings are communicated via `X-HF-Warning` headers:

```python
def _warn_on_warning_headers(response: httpx.Response) -> None:
    """Emit warnings from X-HF-Warning headers. Format: 'topic; message'"""
    server_warnings = response.headers.get_list("X-HF-Warning")
    for server_warning in server_warnings:
        topic, message = server_warning.split(";", 1) if ";" in server_warning else ("", server_warning)
        topic = topic.strip()
        if topic not in _WARNED_TOPICS:   # Each topic warned only once
            message = message.strip()
            if message:
                _WARNED_TOPICS.add(topic)
                logger.warning(message)
```

**Format:** `X-HF-Warning: topic; message` (topic is optional)
**Deduplication:** Each unique topic is warned only once per process (stored in module-level `_WARNED_TOPICS` set)

---

### 9. Inference Client Error Patterns

The `InferenceClient` uses TGI-specific error classes:

```python
TextGenerationError(HTTPError)           # Base for all TGI errors
├── ValidationError                      # Bad request parameters
├── GenerationError                      # Generation failed mid-stream
├── OverloadedError                      # Model at capacity
├── IncompleteGenerationError            # Response truncated
└── UnknownError                         # Unclassified server error
```

Additionally, `InferenceTimeoutError(HTTPError, TimeoutError)` is raised when a model is unavailable or the request times out — it has dual inheritance from both `HTTPError` and `TimeoutError` for flexible catching.

---

### 10. URL Parsing for Error Enrichment

The error system uses regex-based URL parsing to extract `repo_id`, `repo_type`, `bucket_id`, and `job_id` from request URLs — enriching error messages with contextual identifiers:

```python
# From _http.py:
_REPO_ID_FROM_URL_REGEX = re.compile(
    r"^https?://[^/]+/api/(models|datasets|spaces)/([^/]+)(?:/([^/]+))?"
)
_BUCKET_ID_FROM_URL_REGEX = re.compile(
    r"^https?://[^/]+/api/buckets/([^/]+/[^/]+)"
)
_JOB_ID_FROM_URL_REGEX = re.compile(
    r"^https?://[^/]+/api/(?:scheduled-jobs|jobs)/[^/]+/([^/?]+)"
)
_REPO_URL_SUBPATHS = {"resolve", "tree", "blob", "raw", "refs", "commit", 
                       "discussions", "settings", "revision"}
```

The second path segment heuristic: if it's NOT a known subpath keyword, it's part of a namespaced repo_id (e.g., `user/repo`).

---

### 11. Production Best Practices

**Catch specific exceptions first:**

```python
from huggingface_hub.utils import (
    RepositoryNotFoundError, GatedRepoError, RevisionNotFoundError,
    BadRequestError, HfHubHTTPError, OfflineModeIsEnabled,
)

try:
    info = hf_api.model_info("my-model")
except GatedRepoError:
    # Handle gated repo (extends RepositoryNotFoundError, must check first!)
    request_access()
except RepositoryNotFoundError:
    # Repo doesn't exist or no access
    create_repo()
except BadRequestError as e:
    # 400 — malformed request
    print(f"Bad request: {e.server_message}")
except HfHubHTTPError as e:
    # Any other HTTP error — request_id available
    print(f"HTTP {e.response.status_code}: {e}")
except OfflineModeIsEnabled:
    # Offline mode — fall back to local cache
    load_local()
```

**Retry configuration strategies:**

```python
from huggingface_hub.utils import http_backoff

# Default: retry up to 5 times on transient errors
response = http_backoff("GET", url)

# Aggressive retry for spotty connections
response = http_backoff("GET", url, max_retries=10, max_wait_time=30)

# No retry — fail fast (e.g., user-facing API)
response = http_backoff("GET", url, retry_on_exceptions=(), retry_on_status_codes=())

# Custom retry set
response = http_backoff("PUT", url, data=data, retry_on_status_codes=(429, 503))
```

**Enrich errors using `append_to_message()`:**

```python
try:
    hf_api.create_repo("my-model", exist_ok=True)
    hf_api.upload_file(...)
except HfHubHTTPError as e:
    e.append_to_message("\n`create_repo` or `upload_file` failed — check permissions.")
    raise
```

**Disable retries for fast local-cache fallback:**

The internal `_httpx_follow_relative_redirects_with_backoff()` function uses this pattern — when `retry_on_errors=False`, it passes empty tuples to disable all retry behavior, enabling fast fallback to cached content when the network is unreliable.

---

### 12. Complete HTTP Error Flow

```
User code → hf_api.model_info("repo")
  → HfApi._api_call() → http_backoff()
    → _http_backoff_base()
      → get_session() → httpx.Client()
        → event hook: hf_request_event_hook()
          → checks HF_HUB_OFFLINE → raises OfflineModeIsEnabled if set
          → adds X-Amzn-Trace-Id header
      → client.request() over network
    → Response received
      → Status code check
        → Success (not in retry set) → return response
        → Failure (in retry set)
          → nb_tries > max_retries? → hf_raise_for_status(response)
          → Not yet → parse ratelimit headers, exponential backoff, retry
  → hf_raise_for_status(response)
    → _warn_on_warning_headers(response) — X-HF-Warning log
    → response.raise_for_status() — may raise httpx.HTTPStatusError
    → Catch HTTPStatusError → check X-Error-Code
      → Map to typed exception (RepositoryNotFoundError, etc.)
      → _format() extracts server message from header + body + JSON
      → Raise typed HfHubHTTPError subclass
```

### Bug Fix Note
This file previously contained notification-and-watching-system content (a copy-paste error from a previous learning run). This has been replaced with the correct HF Hub API Error Handling deep-dive.

### Sources
- Source: `huggingface_hub/errors.py` (609 lines, v1.24.0) — all 40+ exception types
- Source: `huggingface_hub/utils/_http.py` (1161 lines) — `hf_raise_for_status()`, `http_backoff()`, rate limit parsing, session management
- Hub OpenAPI spec: `https://huggingface.co/.well-known/openapi.json`
- Live API verification: tested `/api/models`, `/resolve` endpoints for X-Error-Code responses
- Rate limit IETF draft: https://www.ietf.org/archive/id/draft-ietf-httpapi-ratelimit-headers-09.html
