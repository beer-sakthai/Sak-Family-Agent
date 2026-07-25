# HF Learnings Log — hf-hub-api-error-handling

## 2026-07-25: hf-hub-api-error-handling — Hugging Face Hub API Error Handling Complete Reference

### Summary
Comprehensive deep-dive into error handling across the Hugging Face Hub REST API and the `huggingface_hub` Python library. Researched live API responses, library source code (`errors.py`, `utils/_http.py`), HTTP error headers, rate limiting (IETF draft), exception hierarchy, and retry patterns. Created authoritative reference for diagnosing and handling errors programmatically.

### Key Findings

#### 1. HF Hub API Error Response Format

The Hub REST API returns errors in two layers simultaneously:

**JSON Body** (media type `application/json`):
```json
{"error": "Invalid username or password."}
```
Variants observed:
- `{"error": "string error"}` — simple string error (most common)
- `{"error": ["error 1", "error 2"]}` — list of errors (multi-field validation)
- `{"error": "invalid_grant", "error_description": "..."}` — OAuth-style errors (RFC 6749)
- `{"error_description": "..."}` — description-only, no error code
- `{"errors": [{"message": "error 1"}, {"message": "error 2"}]}` — structured errors array
- Non-JSON plain text for certain endpoints (e.g. `"Entry not found"` for missing files)

**HTTP Headers** (richer, structured error signalling):

| Header | Example | Purpose |
|--------|---------|---------|
| `X-Error-Code` | `RepoNotFound`, `RevisionNotFound`, `EntryNotFound`, `GatedRepo` | Machine-readable error classification |
| `X-Error-Message` | `"Invalid username or password."` | Human-readable error description |
| `X-Request-Id` | `PvMw_VjBMjVdMz53WKIzP` | Unique request identifier for debugging |
| `X-HF-Warning` | `topic; message` | Deprecation/notice warnings (non-fatal) |
| `RateLimit` | `"api";r=0;t=55` | Current rate limit status (IETF draft) |
| `RateLimit-Policy` | `"fixed window";"api";q=500;w=300` | Rate limit window definition |

The `X-Error-Code` header is the primary machine-readable signal used by `hf_raise_for_status()` to dispatch to the correct exception type.

#### 2. HTTP Status Code → Exception Mapping

| Code | Meaning | X-Error-Code | Python Exception | Notes |
|------|---------|-------------|-------------------|-------|
| **400** | Bad Request | (none) | `BadRequestError` | Validation failure in request body/params |
| **401** | Unauthorized | `RepoNotFound` (or absent) | `RepositoryNotFoundError` | Ambiguous — also maps to missing/private repos without auth |
| **403** | Forbidden | `GatedRepo` | `GatedRepoError` | Gated repo without access |
| **403** | Forbidden | (none, msg=`"Access to this resource is disabled."`) | `DisabledRepoError` | Repo disabled by author |
| **403** | Forbidden | (other) | `HfHubHTTPError` | General forbidden (wrong token scope) |
| **404** | Not Found | `RevisionNotFound` | `RevisionNotFoundError` | Invalid revision |
| **404** | Not Found | `EntryNotFound` | `RemoteEntryNotFoundError` | Invalid file path in repo |
| **404** | Not Found | `RepoNotFound` (bucket API) | `BucketNotFoundError` | Storage bucket not found |
| **404** | Not Found | `RepoNotFound` (or absent, 401-style) | `RepositoryNotFoundError` | Repo doesn't exist |
| **404** | Not Found | (none, job API) | `JobNotFoundError` | Job ID not found |
| **416** | Range Not Satisfiable | (none) | `HfHubHTTPError` | Invalid byte range for resume download |
| **429** | Too Many Requests | (none) | `HfHubHTTPError` | Rate limited (parse `RateLimit` headers) |
| **5xx** | Server Error | (none) | `HfHubHTTPError` | Server-side failure, retryable |

**Critical nuance**: 401 is treated as `RepositoryNotFoundError` even when it's actually a credentials issue. This is a known design choice by HF:
```python
# From huggingface_hub source:
# 401 is misleading as it is returned for:
#    - private and gated repos if user is not authenticated
#    - missing repos
# => for now, we process them as `RepoNotFound` anyway.
```

#### 3. huggingface_hub Exception Hierarchy

```
Exception
├── CacheNotFound (cache dir missing)
├── CorruptedCacheException (corrupt cache structure)
├── CachedRepoTreeNotFoundError (no cached tree listing)
├── OIDCError (keyless CI/CD auth failure)
├── DeviceCodeError (OAuth Device Code flow failure)
│   └── .error_code: OAuthErrorCode enum (authorization_pending, slow_down, etc.)
├── HTTPError (from httpx)
│   ├── HfHubHTTPError (base HF HTTP error)
│   │   ├── .request_id (str | None)
│   │   ├── .server_message (str | None)  
│   │   ├── .response (httpx.Response)
│   │   ├── .request (httpx.Request)
│   │   ├── RepositoryNotFoundError
│   │   │   ├── .repo_id, .repo_type
│   │   │   └── GatedRepoError
│   │   ├── DisabledRepoError
│   │   ├── RevisionNotFoundError
│   │   │   └── .repo_id, .repo_type
│   │   ├── RemoteEntryNotFoundError (EntryNotFoundError also)
│   │   │   └── .repo_id, .repo_type
│   │   ├── BadRequestError (ValueError also)
│   │   ├── BucketNotFoundError
│   │   │   └── .bucket_id
│   │   └── JobNotFoundError
│   │       └── .job_id
│   ├── InferenceTimeoutError (TimeoutError also)
│   └── TextGenerationError
│       ├── ValidationError
│       ├── GenerationError
│       ├── OverloadedError
│       ├── IncompleteGenerationError
│       └── UnknownError
├── OfflineModeIsEnabled (ConnectionError)
├── HFValidationError (ValueError)
│   └── HfUriError (malformed hf:// URIs)
├── EntryNotFoundError
│   ├── RemoteEntryNotFoundError (HfHubHTTPError also)
│   └── LocalEntryNotFoundError (FileNotFoundError)
│       └── IncompleteSnapshotError (.snapshot_path)
├── SafetensorsParsingError
├── NotASafetensorsRepoError
├── FileMetadataError (OSError)
├── DryRunError (OSError)
├── FileDuplicationError
├── DDUFError
│   ├── DDUFCorruptedFileError
│   └── DDUFExportError
│       └── DDUFInvalidEntryNameError
├── StrictDataclassError
│   ├── StrictDataclassDefinitionError
│   ├── StrictDataclassFieldValidationError
│   └── StrictDataclassClassValidationError
├── XetDownloadError
├── InferenceEndpointError
│   └── InferenceEndpointTimeoutError (TimeoutError also)
├── SandboxError (.status_code)
│   └── SandboxCommandError (.cmd, .result)
├── CLIError
│   ├── ConfirmationError
│   └── CLIExtensionInstallError
└── LocalTokenNotFoundError (EnvironmentError)
```

#### 4. Rate Limiting — Headers (IETF Draft)

HF Hub implements the [IETF HTTP RateLimit headers draft](https://www.ietf.org/archive/id/draft-ietf-httpapi-ratelimit-headers-09.html). Confirmed via live API response:

```
ratelimit: "api";r=496;t=246
ratelimit-policy: "fixed window";"api";q=500;w=300
```

The Python library parses this into a `RateLimitInfo` dataclass:
```python
@dataclass(frozen=True)
class RateLimitInfo:
    resource_type: str         # e.g. "api"
    remaining: int             # requests remaining this window (e.g. 496)
    reset_in_seconds: int      # seconds until reset (e.g. 246)
    limit: int | None = None   # max per window (e.g. 500)
    window_seconds: int | None = None  # window size (e.g. 300)
```

Usage in `hf_raise_for_status` for 429 responses:
```python
ratelimit_info = parse_ratelimit_headers(response.headers)
if ratelimit_info is not None:
    message = f"429 Too Many Requests: you have reached your '{ratelimit_info.resource_type}' rate limit."
    message += f"\nRetry after {ratelimit_info.reset_in_seconds} seconds"
    # Includes remaining/limit counts and window info
```

**Rate Limit Detection Pattern:**
```python
from huggingface_hub.utils import parse_ratelimit_headers

def check_rate_limit(response):
    info = parse_ratelimit_headers(response.headers)
    if info and info.remaining == 0:
        return info.reset_in_seconds  # seconds to wait
    return None
```

#### 5. X-HF-Warning Header — Deprecation/Notice System

HF Hub can return non-fatal warnings via `X-HF-Warning` headers:
```
X-HF-Warning: topic; message text
```

The library logs a warning per unique topic (first occurrence only):
```python
topic, message = server_warning.split(";", 1) if ";" in server_warning else ("", server_warning)
if topic not in _WARNED_TOPICS:
    _WARNED_TOPICS.add(topic)
    logger.warning(message)
```

Multiple `X-HF-Warning` headers can appear in a single response.

#### 6. hf_raise_for_status() Error Dispatch Logic

The core error routing function `hf_raise_for_status(response, endpoint_name)` in `utils/_http.py` follows this decision tree:

1. Check `X-HF-Warning` headers (log warnings, never raise)
2. Try `response.raise_for_status()` (httpx built-in)
3. On `HTTPStatusError`:
   - 3xx → silent return (no redirect error)
   - Check `X-Error-Code` header:
     - `"RevisionNotFound"` → `RevisionNotFoundError`
     - `"EntryNotFound"` → `RemoteEntryNotFoundError`
     - `"GatedRepo"` → `GatedRepoError`
     - `"RepoNotFound"` + bucket URL → `BucketNotFoundError`
     - `"RepoNotFound"` or (401 + repo URL) → `RepositoryNotFoundError`
   - Check `X-Error-Message` == `"Access to this resource is disabled."` → `DisabledRepoError`
   - 400 → `BadRequestError`
   - 403 → `HfHubHTTPError` with permission guidance
   - 429 → `HfHubHTTPError` with rate limit details (parsed from headers)
   - 416 → `HfHubHTTPError` with Range/Content-Range info
   - Fallback → `HfHubHTTPError` with generic message

The `X-Request-Id` header is extracted from every error response (tries `x-request-id`, `X-Amzn-Trace-Id`, `x-amz-cf-id` in order).

#### 7. Server Error Message Extraction Priority

The `_format()` helper in `_http.py` builds error messages using this priority:
1. `X-Error-Message` header (highest priority)
2. JSON body: `error` field (string or list), `error_description`, `errors[].message`
3. Plain text body (if not HTML)
4. Deduplicates and joins all messages

#### 8. Retry Strategies & Best Practices

**Retryable errors (safe to retry with backoff):**
- 429 Too Many Requests (respect `reset_in_seconds`)
- 5xx Server Errors (transient infrastructure issues)
- 503 Service Unavailable (temporary)
- Connection errors (network blips, DNS issues)
- `InferenceTimeoutError` (model loading/scheduling delays)

**Non-retryable errors (fix before retrying):**
- 400 Bad Request (fix request body/params)
- 401/403 Authentication/Authorization (fix token or permissions)
- 404 Not Found (fix repo/file/revision path)
- `OfflineModeIsEnabled` (set `HF_HUB_OFFLINE=0`)
- `HFValidationError` (fix repo_id format)
- `LocalTokenNotFoundError` (login first)

**Recommended retry pattern:**
```python
import time
from huggingface_hub.utils import HfHubHTTPError, parse_ratelimit_headers

def hf_request_with_retry(fn, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            return fn()
        except HfHubHTTPError as e:
            status = e.response.status_code
            if status == 429:
                info = parse_ratelimit_headers(e.response.headers)
                wait = info.reset_in_seconds if info else base_delay * (2 ** attempt)
            elif status >= 500:
                wait = base_delay * (2 ** attempt)  # exponential backoff
            else:
                raise  # non-retryable
            time.sleep(min(wait, 60))  # cap at 60s
    raise  # exhausted retries
```

#### 9. Offline Mode Detection

`HF_HUB_OFFLINE=1` environment variable causes all network operations to raise `OfflineModeIsEnabled(ConnectionError)` immediately, before any HTTP call:

```python
from huggingface_hub import offline
if offline.is_offline_mode_enabled():
    print("Hub is offline — cannot make network requests")
```

The offline check is performed at the session level before every request.

#### 10. Auth Error Patterns

| Issue | HTTP | Exception | Key Signal |
|-------|------|-----------|------------|
| No token set | 401 | `RepositoryNotFoundError` | `LocalTokenNotFoundError` if `token=False` passed explicitly |
| Invalid token | 401 | `RepositoryNotFoundError` | `X-Error-Message: "Invalid username or password."` |
| Wrong token scope | 403 | `HfHubHTTPError` | `X-Error-Message: "...does not have the required permissions"` |
| Gated repo not authorized | 403 | `GatedRepoError` | `X-Error-Code: GatedRepo` |
| Token expired | 401 | `RepositoryNotFoundError` | (no specific X-Error-Code) |
| OIDC trusted publisher | — | `OIDCError` | No valid id token available |
| OAuth Device Code | — | `DeviceCodeError` | `.error_code` attribute with OAuth error codes |

#### 11. Request ID Tracking

Every HF Hub API error response includes a `X-Request-Id` header, accessible via:
```python
try:
    model_info("nonexistent/repo")
except HfHubHTTPError as e:
    print(f"Request ID: {e.request_id}")  # e.g. "PvMw_VjBMjVdMz53WKIzP"
    print(f"Server message: {e.server_message}")
    print(f"HTTP status: {e.response.status_code}")
```

This request ID is critical for HF support debug — always include it in bug reports.

#### 12. Validation Errors

`HFValidationError` (ValueError subclass) is raised for:
- Invalid repo_id format (special characters, wrong casing)
- Invalid revision format
- Invalid token format
- `HfUriError` for malformed `hf://` URIs (with `.uri` and `.msg` attributes)

### Impact & Use Cases
- **Debugging:** Map any HTTP error to the correct exception type and structured error fields
- **Resilience:** Build robust retry logic with proper retryable/non-retryable classification
- **Monitoring:** Track request IDs for HF support escalation
- **Zero-cost operations:** Avoid unnecessary retries on non-retryable errors (4xx) saves token/bandwidth
- **Rate limit awareness:** Parse `RateLimit` headers to pace API calls within free tier limits

### Skill Created
`hf-hub-api-error-handling/` — new skill with SKILL.md (author: SakThai, license: MIT) and this learnings reference. Covers the full error handling lifecycle from API response to Python exception to retry strategy.

### Sources
- huggingface_hub source: `errors.py` (exception hierarchy, 609 lines)
- huggingface_hub source: `utils/_http.py` (hf_raise_for_status, _format, parse_ratelimit_headers, _warn_on_warning_headers)
- Live API queries against hub endpoints (models, datasets, files, revisions)
- IETF RateLimit Headers draft: https://www.ietf.org/archive/id/draft-ietf-httpapi-ratelimit-headers-09.html
