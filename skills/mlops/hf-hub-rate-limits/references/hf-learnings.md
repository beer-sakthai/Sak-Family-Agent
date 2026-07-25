# HF Learnings Log

## 2026-07-25: hf-hub-rate-limits — Hugging Face Hub Rate Limit Policies, Tiers & Best Practices (Topic #249)

### Summary
Comprehensive deep-dive on Hugging Face Hub's rate limit system. Covers the three rate limit buckets (API, Resolver, Pages) and their distinct quotas, the official per-plan rate limit tiers (Anonymous → Enterprise Plus), the standardized `RateLimit` and `RateLimit-Policy` HTTP headers (IETF draft-ietf-httpapi-ratelimit-headers v9), how to monitor rate limit status via the billing dashboard, `huggingface_hub`'s built-in smart rate limit handling (v1.2.0+), practical strategies for avoiding throttling on free-tier accounts, and granular user-action limits for repos/commits/discussions.

### Source
- HF Hub Rate Limits doc: https://huggingface.co/docs/hub/en/rate-limits
- IETF draft: https://www.ietf.org/archive/id/draft-ietf-httpapi-ratelimit-headers-09.html
- huggingface_hub source: `huggingface_hub/utils/_http.py` — `RateLimitInfo`, `parse_ratelimit_headers()`
- huggingface_hub constants: `DEFAULT_ETAG_TIMEOUT=10`, `DEFAULT_DOWNLOAD_TIMEOUT=10`, `DEFAULT_REQUEST_TIMEOUT=10`
- Billing dashboard: https://huggingface.co/settings/billing

---

### 1. The Three Rate Limit Buckets

The HF Hub defines **three distinct rate limit buckets**, each with its own quota and characteristics:

| Bucket | Scope | Example Requests | Typical Quota Level |
|--------|-------|-----------------|---------------------|
| **API** | Hub REST API endpoints (search, repo CRUD, user mgmt) | `GET /api/models`, `POST /api/repos/create` | Lowest |
| **Resolvers** | `/resolve/` URLs serving user-generated content (model/dataset files) | `huggingface.co/google-bert/bert-base-uncased/resolve/main/config.json` | Highest |
| **Pages** | Web pages on `huggingface.co` | Browsing model cards, dataset pages | Medium |

**Key insight:** Resolver requests are heavily optimized by HF's infrastructure and have the highest rate limits because they serve the core download use case. API requests are more constrained.

**All quotas are calculated over 5-minute fixed windows**, which allows for some "burstiness" — you can use your entire 5-minute quota in a short burst rather than being limited per-second.

---

### 2. Rate Limit Tiers by Plan

Official rate limits (as documented September 2025):

| Plan | API | Resolvers | Pages |
|------|-----|-----------|-------|
| **Anonymous** (per IP) | 500 | 3,000 | 100 |
| **Free user** | 1,000 | 5,000 | 200 |
| **PRO user** | 2,500 | 12,000 | 400 |
| **Team organization** | 3,000 | 20,000 | 400 |
| **Enterprise organization** | 6,000 | 50,000 | 600 |
| **Enterprise Plus** | 10,000 | 100,000 | 1,000 |
| **Enterprise Plus (with Org IP Ranges)** | 100,000 | 500,000 | 10,000 |
| **Academia Hub** | 3,000 | 20,000 | 400 |

**Critical note for free-tier users:** Anonymous and Free user limits are subject to change over time depending on platform health. Always authenticate with `HF_TOKEN` to get Free user limits instead of Anonymous (which are 2× lower for API, ~1.7× lower for Resolvers).

**Organization behavior:** For organizations, rate limits are applied individually to each member, NOT shared across members. Each team member gets their own quota.

---

### 3. Standardized Rate Limit HTTP Headers

HF implements the IETF draft (v9) `RateLimit` HTTP header fields. When a request hits a rate limit, the response includes:

**`RateLimit` header:**
```
RateLimit: "api";r=0;t=55
```
- `r` = remaining requests in current window
- `t` = seconds remaining until window reset

**`RateLimit-Policy` header:**
```
RateLimit-Policy: "fixed window";"api";q=500;w=300
```
- `q` = total requests allowed per window
- `w` = window duration in seconds (always 300 = 5 minutes)

**`429 Too Many Requests` response:**
When a rate limit is exceeded, the server returns HTTP 429 with these headers.

**`Retry-After` header:**
Fallback header in delay-seconds format for older/legacy clients.

---

### 4. Monitoring Rate Limit Status

**Billing dashboard gauges:**
Visit https://huggingface.co/settings/billing to see real-time gauges for all three buckets:
- Each gauge shows requests in the last 5 minutes vs. the plan limit
- Gauges turn RED when the limit is exceeded
- Use the context switcher to toggle between user account and org views

---

### 5. Smart Rate Limit Handling in huggingface_hub (v1.2.0+)

The `huggingface_hub` Python library includes built-in support:

**Automatic 429 retry:**
When a 429 is received, the SDK automatically:
1. Parses the `RateLimit` header to extract `t` (seconds until reset)
2. Waits exactly that duration before retrying
3. Applies to file downloads (Resolvers) AND paginated Hub API calls (`list_models`, `list_datasets`, `list_spaces`)

**`parse_ratelimit_headers()` utility:**
```python
from huggingface_hub.utils import parse_ratelimit_headers

headers = {
    "ratelimit": '"api";r=0;t=55',
    "ratelimit-policy": '"fixed window";"api";q=500;w=300',
}
info = parse_ratelimit_headers(headers)
# info.reset_in_seconds → 55
# info.resource_type → "api"
```

**`RateLimitInfo` named tuple:**
- `resource_type`: Which bucket was limited (api, resolvers, pages)
- `reset_in_seconds`: Seconds until the window resets

**SRC reference:** The implementation lives in `huggingface_hub/utils/_http.py` and uses two regex patterns:
- `_RATELIMIT_REGEX`: Parses `"resource_type";r=N;t=N` from the `RateLimit` header
- `_RATELIMIT_POLICY_REGEX`: Parses `q=N;w=N` from the `RateLimit-Policy` header

---

### 6. Granular User Action Rate Limits

Beyond the three main buckets, HF enforces limits on **specific user actions**:
- Repository creation
- Repository commits/pushes
- Discussions and comments
- Moderation actions

**These granular limits are not publicly documented** (they change more frequently). If you get quota errors on these actions, HF recommends upgrading to PRO/Team/Enterprise or contacting support.

---

### 7. Strategies to Avoid Rate Limiting (Free Tier)

#### 7.1 Always Authenticate
```bash
export HF_TOKEN=hf_your_token_here
```
This is the #1 reason users get rate limited — making requests anonymously when they could be authenticated. Free tier is 2× the anonymous limit.

#### 7.2 Use Resolvers Instead of API When Possible
- Resolver limits (5,000 for Free) are 5× higher than API limits (1,000 for Free)
- Use `hf_hub_download()` or `snapshot_download()` instead of `model_info()` for file access
- Use `requests.get()` directly on `/resolve/` URLs for simple downloads

#### 7.3 Spread Requests Over Time
- Batch paginated listing calls with delays between pages
- Use `huggingface_hub`'s built-in pagination (it handles rate limits automatically)
- For bulk operations, add `time.sleep(1)` between requests

#### 7.4 Cache Aggressively
```bash
export HF_HUB_CACHE=/path/to/cache  # Default: ~/.cache/huggingface/hub
```
- huggingface_hub caches downloads by default → subsequent reads are free
- Increase cache size to avoid re-downloading
- Set `HF_HUB_DOWNLOAD_TIMEOUT` higher on slow connections

#### 7.5 Timeout Configuration
```python
# Environment variables for timeout control
HF_HUB_DOWNLOAD_TIMEOUT=30   # Default 10s — increase on slow connections
HF_HUB_ETAG_TIMEOUT=30       # Default 10s — etag check timeout
```

#### 7.6 Offline Mode for Development
```bash
export HF_HUB_OFFLINE=1
```
When developing/testing: use offline mode to avoid accidental API calls. Only cached files will be accessible.

#### 7.7 Pagination Best Practices
```python
from huggingface_hub import HfApi

api = HfApi()
# huggingface_hub handles pagination with rate-limit awareness
for model in api.list_models(task="text-classification", limit=50):
    process(model)
```
Always use the library's pagination instead of manual page-by-page requests.

---

### 8. Rate Limit Architecture Diagram

```
Client Request
     │
     ▼
┌─────────────────────┐
│  HF Load Balancer   │
└─────────────────────┘
     │
     ▼
┌──────────────────────────────────────────┐
│  Rate Limit Middleware                   │
│  ┌─────────────────────────────────────┐ │
│  │  API Bucket    │  500/5min (anon)  │ │
│  │  Resolver Bucket│ 3,000/5min (anon) │ │
│  │  Pages Bucket   │   100/5min (anon) │ │
│  └─────────────────────────────────────┘ │
│  Returns 429 + RateLimit headers          │
└──────────────────────────────────────────┘
     │
     ▼
┌─────────────────────┐
│  Application Logic  │
│  (huggingface_hub   │
│   auto-retry on 429)│
└─────────────────────┘
```

---

### 9. Comparison: hf-hub-rate-limits vs hf-hub-exceptions-retry

| Aspect | Rate Limits (this doc) | Exceptions & Retry |
|--------|----------------------|-------------------|
| **Focus** | Server-side policies, tiers, quotas | Client-side retry mechanisms |
| **Covers** | Three buckets, per-plan limits, RateLimit headers, billing dashboard | `http_backoff()`, `parse_ratelimit_headers()`, error hierarchy |
| **Audience** | All Hub users managing API usage | Developers implementing retry logic |
| **Key info** | Free tier = 1,000 API/5,000 Resolvers per 5min | Exponential backoff: wait = min(max, base × 2^n) |

---

### 10. Quick Reference

| Need | What to Do |
|------|-----------|
| Check current usage | Visit https://huggingface.co/settings/billing |
| Avoid anonymous limits | Set `export HF_TOKEN=...` |
| Fastest download path | Use `/resolve/` URLs instead of API |
| Handle 429 in code | Use `huggingface_hub` (auto-retry) |
| Parse rate limit headers | `from huggingface_hub.utils import parse_ratelimit_headers` |
| Increase timeout | `export HF_HUB_DOWNLOAD_TIMEOUT=30` |
| Offline development | `export HF_HUB_OFFLINE=1` |
| Cache location | `~/.cache/huggingface/hub` or `$HF_HUB_CACHE` |
| Free API quota | 1,000 requests per 5 minutes |
| Free Resolver quota | 5,000 requests per 5 minutes |

---

## 2026-07-25: hf-hub-rate-limits-deep-dive-v2 — Source Code Internals & Advanced Patterns (Deeper on Topic #249)

### Summary
Deep-dive into the actual `huggingface_hub v1.24.0` source code implementing rate limit handling. Covers the `_http_backoff_base()` internal function, the precise regex patterns for parsing IETF RateLimit headers, how `http_backoff()` integrates rate-limit-aware waiting with exponential backoff, `hf_raise_for_status()` 429 error message construction, `HfApi` pagination internals, Storage Buckets rate limits, and practical code patterns for custom handling.

### Source Code Reference
- huggingface_hub v1.24.0 source: `huggingface_hub/utils/_http.py` (lines 55–920)
- Rate limit regex + parser: lines 75–135
- `_http_backoff_base()`: lines 430–527
- `http_backoff()` wrapper: lines 530–610
- `hf_raise_for_status()` 429 handling: lines 895–914

---

### 1. Exact Regex Patterns for Rate Limit Header Parsing

The library uses two compiled regex patterns:

**`_RATELIMIT_REGEX`** — Parses the `RateLimit` response header:
```python
_RATELIMIT_REGEX = re.compile(
    r'\"(?P<resource_type>\w+)\"\s*;\s*r\s*=\s*(?P<r>\d+)\s*;\s*t\s*=\s*(?P<t>\d+)'
)
```
Matches patterns like: `"api";r=0;t=55`
- `resource_type` → `"api"`, `"resolvers"`, or `"pages"`
- `r` → remaining requests in current window
- `t` → seconds until window reset

**`_RATELIMIT_POLICY_REGEX`** — Parses the `RateLimit-Policy` response header:
```python
_RATELIMIT_POLICY_REGEX = re.compile(
    r'q\s*=\s*(?P<q>\d+).*?w\s*=\s*(?P<w>\d+)'
)
```
Matches patterns like: `"fixed window";"api";q=500;w=300`
- `q` → quota per window
- `w` → window duration in seconds (always 300 = 5 min)

These regexes are CASE-INSENSITIVE for header key lookup (lowercased in `parse_ratelimit_headers()`), but case-sensitive for the header value matching.

---

### 2. The `RateLimitInfo` Data Class

```python
@dataclass(frozen=True)
class RateLimitInfo:
    resource_type: str
    remaining: int
    reset_in_seconds: int
    limit: int | None = None
    window_seconds: int | None = None
```
- Frozen (immutable) dataclass returned by `parse_ratelimit_headers()`
- `limit` and `window_seconds` are `Optional` because they come from the `RateLimit-Policy` header which may not always be present
- Used both for logging/display AND for the automatic retry delay calculation

---

### 3. The Full Auto-Retry Flow in `_http_backoff_base()`

This is the core function shared by both `http_backoff()` (regular requests) and `http_stream_backoff()` (streaming). Here's the complete retry lifecycle:

```python
def _http_backoff_base(
    method, url, *,
    max_retries=5,            # Max attempts before giving up
    base_wait_time=1,         # Initial sleep (seconds)
    max_wait_time=8,          # Cap on exponential backoff
    retry_on_exceptions,      # Default: TimeoutException, NetworkError, RemoteProtocolError
    retry_on_status_codes,    # Default: (408, 429, 500, 502, 503, 504)
    stream=False,
    **kwargs,
):
```

**The loop:**

1. **Attempt request** via `client.request()` or `client.stream()`
2. **`_should_retry(response)`** closure checks:
   - If status code NOT in `retry_on_status_codes` → stop (success)
   - If `nb_tries > max_retries` → call `hf_raise_for_status()` (will raise, or return)
   - If status is **429** → parse `RateLimit` header via `parse_ratelimit_headers()` to get `reset_in_seconds`
   - If `Retry-After` header present → fallback to `_parse_retry_after()`
   - Return `True` (should retry) for all other retryable status codes
3. **Wait logic:**
   - If rate limited → `actual_sleep = float(ratelimit_reset) + 1` (adds +1s safety margin)
   - Otherwise → `actual_sleep = sleep_time` (exponential: 1s, 2s, 4s, 8s... capped at `max_wait_time=8s`)
4. **Exponential backoff:** `sleep_time = min(max_wait_time, sleep_time * 2)`
5. **File-object cursor reset:** If `data` kwarg is a file/IO object, saves and restores `.tell()` position between retries to allow re-sending upload bodies.

**Key insight:** When rate limited, the huggingface_hub library respects the server's precise reset time (+1s safety margin), rather than using exponential backoff. This is much more efficient than blindly backing off.

---

### 4. `hf_raise_for_status()` — The 429 Error Message Generator

When a 429 response would not be retried (n_tries exhausted), `hf_raise_for_status()` constructs a detailed error message:

```python
elif response.status_code == 429:
    ratelimit_info = parse_ratelimit_headers(response.headers)
    if ratelimit_info is not None:
        message = (
            f"\n\n429 Too Many Requests: you have reached your "
            f"'{ratelimit_info.resource_type}' rate limit."
        )
        message += f"\nRetry after {ratelimit_info.reset_in_seconds} seconds"
        if ratelimit_info.limit is not None and ratelimit_info.window_seconds is not None:
            message += (
                f" ({ratelimit_info.remaining}/{ratelimit_info.limit} requests remaining"
                f" in current {ratelimit_info.window_seconds}s window)."
            )
    else:
        message = f"\n\n429 Too Many Requests for url: {response.url}."
```

This produces user-friendly messages like:
```
429 Too Many Requests: you have reached your 'api' rate limit.
Retry after 55 seconds (0/500 requests remaining in current 300s window).
```

---

### 5. How `HfApi` Iteration Methods Handle Rate Limits

The `HfApi.list_models()`, `list_datasets()`, `list_spaces()` methods all return **lazy iterators** (`Iterator[Model]`) rather than lists. Internally, they call:

```python
items: Iterator = api_iterate(  # or _fetch_with_pagination
    endpoint,                # e.g., "/api/models"
    params=params,
    headers=headers,
    ...
)
items = islice(items, limit)  # truncate to requested limit
```

The `api_iterate` function paginates automatically through the Hub API, using `http_backoff()` internally so rate limits are handled transparently. This means:
- You don't need to manage pagination yourself
- Rate limits are automatically respected between page fetches
- The iterator is lazy — it only fetches pages as you iterate

**Practical implication:** When using `list_models()`, you can safely iterate through thousands of items. The library handles backoff between pages automatically. The old pattern of manually calling `next_page()` is obsolete.

---

### 6. Storage Buckets Rate Limits

As of July 2026, HF's **Storage Buckets** feature has its own rate limit handling via a dedicated regex:

```python
BUCKET_API_REGEX = re.compile(
    r"""
        ^https?://[^/]+
        /api/buckets/
    """,
    flags=re.VERBOSE,
)
```

This regex identifies bucket API URLs (`/api/buckets/...`) separately from repo URLs. Bucket API calls fall under the general `api` rate limit bucket, but the library tracks the URL pattern to provide accurate error messages. The `_parse_bucket_id_from_url()` function extracts `namespace/name` from bucket URLs for better error context.

**Rate limit environment variables for downloads:**

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_HUB_DOWNLOAD_TIMEOUT` | 10s | Per-request timeout for file downloads |
| `HF_HUB_ETAG_TIMEOUT` | 10s | Timeout for HEAD requests checking file freshness |
| `HF_HUB_DEFAULT_TIMEOUT` | 10s | General request timeout |
| `HF_HUB_OFFLINE` | unset | When set to `1`, no network calls made (uses cache only) |

---

### 7. Custom Rate Limit Handling Patterns

#### 7.1 Manual Rate Limit Header Parsing

```python
from huggingface_hub.utils import parse_ratelimit_headers

# After receiving a response with rate limit headers
info = parse_ratelimit_headers(response.headers)
if info and info.remaining < 10:
    print(f"Approaching rate limit: {info.remaining}/{info.limit} remaining")
    time.sleep(info.reset_in_seconds)  # Wait for window reset
```

#### 7.2 Disabling Auto-Retry (for custom handling)

```python
from huggingface_hub.utils import http_backoff

# Disable all retries — handle 429 yourself
response = http_backoff(
    "GET", url,
    retry_on_exceptions=(),
    retry_on_status_codes=()
)
```

#### 7.3 Custom Retry Configuration

```python
# Aggressive retry for critical operations
response = http_backoff(
    "POST", url,
    max_retries=10,
    base_wait_time=0.5,
    max_wait_time=30,
    retry_on_status_codes=(429, 500, 502, 503, 504)
)
```

#### 7.4 Using `_httpx_follow_relative_redirects_with_backoff`

For scenarios where you need to follow redirects AND handle rate limits:

```python
# Internal helper that follows relative redirects with auto-backoff
from huggingface_hub.utils._http import _httpx_follow_relative_redirects_with_backoff

response = _httpx_follow_relative_redirects_with_backoff(
    "GET", url,
    retry_on_errors=True,  # enables 429/5xx/timeout retry
)
```

This is used internally by the Hub for download flows that may redirect to CDN endpoints.

#### 7.5 Proactive Rate Limit Monitoring in Long-Running Jobs

```python
import os
import time
from huggingface_hub import HfApi, RateLimitInfo

api = HfApi()

# Monitor rate limit consumption during pagination
consumed = 0
for model in api.list_models(task="text-classification", limit=1000):
    process(model)
    consumed += 1
    if consumed % 100 == 0:
        # Check billing dashboard to see real-time usage
        # Or use the RateLimit headers from the last response
        print(f"Processed {consumed} models...")
        # Optional: pace yourself
        time.sleep(0.5)
```

---

### 8. Rate Limit Handling Architecture (Complete Flow)

```
User Code (HfApi.list_models)
    │
    ▼
api_iterate() / _fetch_with_pagination()
    │  Uses http_backoff() internally
    ▼
http_backoff(method, url, ...)
    │
    ▼
_http_backoff_base(method, url, ...)
    │
    ├──► client.request(method, url)  ──► HTTP Response
    │         │                              │
    │         │                         ┌────▼────┐
    │         │                    ┌─────┤ 429?    ├─────┐
    │         │                    │     └─────────┘     │
    │         │                    │  No                 │ Yes
    │         │                    ▼                     ▼
    │         │             return response     parse_ratelimit_headers()
    │         │                                      │
    │         │                               ┌──────▼──────┐
    │         │                               │ reset_in_sec│
    │         │                               │   = 55s     │
    │         │                               └──────┬──────┘
    │         │                                      │
    │         │                               sleep(55 + 1)
    │         │                                      │
    │         │                               retry ──► back to top
    │         │
    │    If Exception (network error):
    │         sleep(exponential: 1s, 2s, 4s... max 8s)
    │         retry ──► back to top
    │
    ▼
Returned to caller as lazy iterator
```

---

### 9. Key Differences from the Exceptions & Retry Skill

| Aspect | Rate Limits Source Code (this section) | hf-hub-exceptions-retry |
|--------|----------------------------------------|------------------------|
| **Focus** | Code-level implementation details | Documentation-level error hierarchy |
| **Covers** | `_http_backoff_base()` internals, regex patterns, 429 error messages, pagination integration | `HfHubHTTPError` subclasses, `http_backoff()` public API, retry parameters |
| **Regex** | `_RATELIMIT_REGEX` and `_RATELIMIT_POLICY_REGEX` patterns explained | Not covered |
| **Rate limit flow** | Rate-limit-aware sleep vs exponential backoff branching logic | General backoff formula |
| **Error messages** | Exact 429 message construction from `hf_raise_for_status()` | Exception class hierarchy |

---

### Sources
- huggingface_hub v1.24.0 source: `/usr/lib/python*/site-packages/huggingface_hub/utils/_http.py` (lines 55–914)
- IETF RateLimit Header Fields draft v9: https://www.ietf.org/archive/id/draft-ietf-httpapi-ratelimit-headers-09.html
- HF Hub Rate Limits doc: https://huggingface.co/docs/hub/rate-limits
- HF Pricing page: https://huggingface.co/pricing

---

**author**: SakThai
**license**: MIT
**updated**: 2026-07-25
**huggingface_hub_version**: 1.24.0+
**topic_id**: 249
