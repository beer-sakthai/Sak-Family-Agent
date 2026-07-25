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

**author**: SakThai
**license**: MIT
**updated**: 2026-07-25
**huggingface_hub_version**: 1.24.0+
**topic_id**: 249
