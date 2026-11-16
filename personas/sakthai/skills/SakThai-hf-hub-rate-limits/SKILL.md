---
name: SakThai-hf-hub-rate-limits
version: 1.0.0
description: Complete reference for Hugging Face Hub rate limit policies, the three
  quota buckets (API, Resolvers, Pages), plan tiers, and standardized IETF rate limit
  headers.
category: mlops
tags:
- api
- headers
- hf
- hub
- huggingface
- limits
- quotas
- rate
- rate-limits
- throttling
author: SakThai
license: MIT
---

# HF Hub Rate Limit Policies, Tiers & Handling

Manage and adhere to Hugging Face Hub rate limits, quota buckets, and standardized HTTP headers.

## Overview

The Hugging Face Hub calculates rate limits over **5-minute fixed windows** across three independent quota buckets:

1. **API Bucket**: REST endpoints for repo management, model search, and metadata updates (`/api/models`, `/api/repos`).
2. **Resolver Bucket**: File downloads and artifact resolution (`/resolve/` URLs) — highest quota.
3. **Pages Bucket**: Web UI browsing requests on `huggingface.co`.

## Quota Tiers by Account Type

| Plan / Tier | API (per 5 min) | Resolvers (per 5 min) | Pages (per 5 min) |
|:---|:---|:---|:---|
| **Anonymous** (IP-based) | 500 | 3,000 | 100 |
| **Free User** (Authenticated) | 1,000 | 5,000 | 200 |
| **PRO User** | 2,500 | 12,000 | 400 |
| **Team / Org** | 3,000 | 20,000 | 400 |
| **Enterprise** | 6,000 | 50,000 | 600 |

> [!IMPORTANT]
> Always authenticate requests with `HF_TOKEN`. Authenticated free users receive 2× the API quota of anonymous IPs.

## Rate Limit Headers (IETF Draft v9)

When receiving responses from the Hub, inspect these headers:
```http
RateLimit: "api";r=980;t=240
RateLimit-Policy: 1000;w=300
```
- `r`: Remaining requests in current window.
- `t`: Seconds until quota reset.
- `w`: Window duration in seconds (typically 300s = 5 minutes).

## Handling HTTP 429 in Python

```python
import time
from huggingface_hub.utils import HfHubHTTPError

def call_with_rate_limit_guard(api_call, *args, **kwargs):
    try:
        return api_call(*args, **kwargs)
    except HfHubHTTPError as err:
        if err.response is not None and err.response.status_code == 429:
            retry_after = int(err.response.headers.get("Retry-After", 60))
            time.sleep(retry_after)
            return api_call(*args, **kwargs)
        raise
```

## References
- Comprehensive deep-dive on rate limit headers and burst handling: [`references/hf-learnings.md`](./references/hf-learnings.md).
