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
