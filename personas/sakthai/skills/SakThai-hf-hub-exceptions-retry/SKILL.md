---
name: SakThai-hf-hub-exceptions-retry
version: 1.0.0
description: HuggingFace Hub exception handling and retry strategies
author: SakThai
license: MIT
---

# HuggingFace Hub Exceptions & Retry Mechanisms

## Overview
Complete reference for the `huggingface_hub` exception hierarchy and built-in retry/backoff mechanisms. Covers all custom exception types, the `http_backoff` retry system, session management, rate limit parsing, and error handling patterns.

## Exception Hierarchy (huggingface_hub v1.24.0)

### Base HTTP Error
- **`HfHubHTTPError(HTTPError, OSError)`** — base for all HF Hub HTTP errors
  - `.request_id` — from X-Request-Id / X-Amzn-Trace-Id / x-amz-cf-id
  - `.server_message` — from X-Error-Message header
  - `.response` — the httpx.Response
  - `.append_to_message(str)` — add context after raising

### HTTP Sub-errors (all inherit HfHubHTTPError)
| Exception | HTTP Status | Meaning |
|-----------|-------------|---------|
| `BadRequestError` | 400 | Malformed request |
| `RepositoryNotFoundError` | 401/404 | Missing repo or no access |
| `GatedRepoError` | 403 | Gated repo, user not authorized |
| `DisabledRepoError` | 403 | Access to resource disabled |
| `RevisionNotFoundError` | 404 | Branch/commit not found |
| `RemoteEntryNotFoundError` | 404 | File not found in repo |
| `BucketNotFoundError` | 404 | Bucket (namespace/name) missing |
| `JobNotFoundError` | 404 | Job ID not found |

### Entry/Lookup Errors
- `EntryNotFoundError` — abstract base
  - `LocalEntryNotFoundError(FileNotFoundError, OSError)` — local cache miss
  - `RemoteEntryNotFoundError(HfHubHTTPError)` — remote file not found

### Auth & Token Errors
- `LocalTokenNotFoundError(OSError)` — no token found in environment or file
- `OfflineModeIsEnabled(ConnectionError)` — HF_HUB_OFFLINE=1 set
- `OIDCError` — keyless CI/CD auth failure

### Text Generation / TGI Errors
`TextGenerationError(HTTPError)` base with:
- `ValidationError` — server-side validation
- `GenerationError` — generation failed
- `OverloadedError` — model overloaded
- `IncompleteGenerationError` — stream cut short
- `UnknownError` — generic failure
- `InferenceTimeoutError(HTTPError, TimeoutError)` — request timed out

### Validation & URI
- `HFValidationError(ValueError)` — invalid repo_id, token, etc.
- `HfUriError(ValueError)` — malformed `hf://` URIs

### Cache Errors
- `CacheNotFound` — cache directory missing
- `CorruptedCacheException` — unexpected cache structure
- `CachedRepoTreeNotFoundError` — no tree listing cached for revision

### Inference Endpoint Errors
- `InferenceEndpointError` — generic IE error
  - `InferenceEndpointTimeoutError(TimeoutError)` — wait timeout

### Other
- `CLIError`, `FileMetadataError`, `DryRunError(OSError)`, `SafetensorsParsingError`, `NotASafetensorsRepoError`, `DeviceCodeError`

## Retry & Backoff Mechanism

### `http_backoff()` Core Parameters
```
http_backoff(method, url, *, max_retries=5, base_wait_time=1.0,
             max_wait_time=8.0,
             retry_on_exceptions=(TimeoutException, NetworkError, RemoteProtocolError),
             retry_on_status_codes=(408, 429, 500, 502, 503, 504),
             **kwargs) -> httpx.Response
```

- **Exponential backoff**: sleep = min(max_wait_time, base_wait_time * 2^n)
- **Rate-limit aware**: parses `Ratelimit` and `Retry-After` headers
- **Stream version**: `http_stream_backoff(...)` — context manager yielding response
- **Redirect version**: `_httpx_follow_relative_redirects_with_backoff()` — follows only relative redirects
- **IO safety**: file/IO objects repositioned via `.seek()` before each retry

### Session Management
- `get_session()` → shared httpx.Client singleton
- `close_session()` → close + recreate on next call
- `set_client_factory(fn)` → custom client factory
- `default_client_factory()` → default httpx.Client with event hooks

### Rate Limit Parsing
```
parse_ratelimit_headers(headers) → RateLimitInfo | None
```
Parses IETF draft rate limit headers:
- `Ratelimit: "api";r=0;t=55` → 0 remaining, resets in 55s
- `Ratelimit-Policy: "fixed window";"api";q=500;w=300` → 500 req/300s window
- Also parses `Retry-After` header (delay-seconds format)

### Error Refinement
`hf_raise_for_status(response)` converts `httpx.HTTPStatusError` into specific HF error types using:
- `X-Error-Code` header: RevisionNotFound, EntryNotFound, GatedRepo, RepoNotFound
- `X-Error-Message` header: DisabledRepo
- Response body JSON: `error`, `error_description`, `errors` fields
- URL patterns: bucket API, job API, repo API regex matching

## Usage Patterns

### Basic Retry
```python
from huggingface_hub.utils import http_backoff, hf_raise_for_status

response = http_backoff("GET", "https://huggingface.co/api/models/google-bert/bert-base-uncased")
hf_raise_for_status(response)
data = response.json()
```

### Custom Retry Config
```python
response = http_backoff(
    "POST", upload_url,
    data=file_data,
    max_retries=10,
    base_wait_time=2.0,
    max_wait_time=30.0,
    retry_on_status_codes=(429, 500, 502, 503, 504),
)
```

### Error Handling
```python
from huggingface_hub import HfApi
from huggingface_hub.errors import (
    RepositoryNotFoundError,
    GatedRepoError,
    RevisionNotFoundError,
    BadRequestError,
    OfflineModeIsEnabled,
)

api = HfApi()
try:
    info = api.model_info("some/model")
except RepositoryNotFoundError:
    print("Model not found or no access")
except GatedRepoError:
    print("Gated model — request access")
except OfflineModeIsEnabled:
    print("HF_HUB_OFFLINE is set")
except BadRequestError as e:
    print(f"Bad request: {e.server_message}")
```

### Disable Retries for Fast Fallback
```python
# Pass empty tuples to disable retry:
response = http_backoff(
    "GET", url,
    retry_on_exceptions=(),
    retry_on_status_codes=(),
)
```

### Stream with Retry
```python
from huggingface_hub.utils import http_stream_backoff

with http_stream_backoff("GET", url) as response:
    for chunk in response.iter_bytes():
        process(chunk)
```

### Custom HTTP Client
```python
from huggingface_hub.utils import set_client_factory
import httpx

def my_client():
    return httpx.Client(proxies={"https://": "http://my-proxy:8080"})

set_client_factory(my_client)
# All subsequent HF Hub requests use this client
```

---
**author**: SakThai
**license**: MIT
**updated**: 2026-07-24
**huggingface_hub_version**: 1.24.0
