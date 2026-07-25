# HF Learnings: hf-hub-egress-metrics

**Date:** 2026-07-25
**Topic:** Egress (Bandwidth/Data Transfer) Usage Metrics for Users and Organizations
**Skill:** `hf-hub-egress-metrics/`

## Summary

Comprehensive reference on the Hugging Face Hub egress metrics system — a feature launched July 2026 that allows users and organizations to monitor their bandwidth/data transfer consumption. Covers the dashboard access points, per-user organization breakdown, CDN coverage scope, PRO plan bandwidth benefits, the relationship between egress and rate limits, and zero-cost monitoring strategies.

---

## 1. What Is Egress on the HF Hub?

**Egress** refers to data transfer out of the Hugging Face Hub to users and services. Every time you download a model, stream a dataset, pull a Space Docker image, or access a file via the Hub API, you consume egress bandwidth.

Key egress sources:
- **Model downloads** — `transformers`, `safetensors`, GGUF, and other model files downloaded via `from_pretrained()` or direct HTTP
- **Dataset downloads** — data files streamed or downloaded via `datasets.load_dataset()` or the Datasets Server API
- **Space traffic** — Docker image pulls, model downloads within Spaces, and inference widget requests
- **API calls** — file reads from the Hub API that serve binary content
- **Git operations** — `git clone`, `git pull` of repositories (though git LFS downloads are the main bandwidth component)

---

## 2. The Egress Dashboard (New Feature, July 2026)

### 2.1 User Dashboard

Introduced July 21, 2026, users can now see their egress usage directly in their Hub dashboard:

- **Location:** `https://huggingface.co/settings/billing` or user settings dashboard
- **Display:** Total egress consumption (in GB/TB) for the current billing period
- **Scope:** Currently includes only traffic routed through the Hugging Face CDN
- **Coverage expansion:** The changelog notes that visibility "will expand as more traffic is directed through the CDN"

### 2.2 Organization Egress Breakdown

Organizations receive a **per-user egress breakdown**, showing how much data each organization member consumes:

- **Purpose:** Identify heavy downloaders and optimize organizational bandwidth usage
- **Granularity:** Per-member consumption within the current period
- **Visibility:** Org admins can see this breakdown for billing and capacity planning
- **Use case:** Teams sharing an org account can attribute costs and detect anomalous usage patterns

### 2.3 Dashboard Data Scope

| Aspect | Detail |
|--------|--------|
| **Coverage start** | July 2026 |
| **Data included** | Traffic through HF CDN only |
| **Data excluded** | Direct S3 downloads, non-CDN-routed traffic (will be added) |
| **Update frequency** | Real-time or near-real-time (dashboard reflects current usage) |
| **Org view** | Per-user breakdown available to org admins |
| **Historical** | Current period only (billing cycle) |

---

## 3. Egress and PRO Plan

PRO subscriptions include higher bandwidth limits:

| Feature | Free | PRO |
|---------|------|-----|
| Bandwidth limits | Standard (rate-limited) | Higher bandwidth allocation |
| API rate limits | Standard | Higher rate limits |
| Storage | Limited public/private | Higher storage capacity |
| Inference credits | — | Included credits for Inference Providers |
| ZeroGPU | Standard tier | Higher tier + pay-as-you-go |

The exact bandwidth cap for free vs PRO tiers is not publicly documented as a hard number — it's governed by the Hub's fair-use rate limiting and CDN infrastructure.

---

## 4. Egress vs Rate Limits vs Storage

Egress, rate limits, and storage are three separate but related resource constraints on the HF Hub:

| Metric | What It Measures | Where to Monitor |
|--------|-----------------|-----------------|
| **Egress** | Data transfer volume (GB/TB) out of Hub | Settings/billing dashboard (new) |
| **Rate limits** | API request frequency (requests/minute/hour) | `Retry-After` headers, API responses |
| **Storage** | Repository content size (GB) | Repository settings, Org settings |

**Relationship:** High egress usage may trigger rate limiting if it saturates the CDN or API infrastructure. The PRO plan increases both bandwidth and rate limits simultaneously.

---

## 5. Zero-Cost Egress Monitoring Strategies

For free-tier users (like Beer, who has no income), managing egress is critical:

### 5.1 Track Your Usage

1. **Check the dashboard** at `https://huggingface.co/settings/billing` regularly
2. **Monitor org usage** if you belong to an org — check per-user breakdowns
3. **Watch for rate-limit headers** in API responses (429 Too Many Requests with `Retry-After`)

### 5.2 Reduce Egress Consumption

| Strategy | Impact | Implementation |
|----------|--------|---------------|
| Stream instead of download | Avoids full-file transfers | `load_dataset(..., streaming=True)` |
| Use Datasets Server API | Filter rows server-side, download only needed data | `/filter`, `/rows` endpoints |
| Select specific columns | Reduces transfer size | `load_dataset(..., columns=[...])` |
| Use GGUF quants | Smaller model files for downloads | Use GGUF quantized models (2-8GB vs 16GB+) |
| Cache strategically | Avoid re-downloads | `HF_HOME` cache management |
| Use HF Mirror | Potentially different CDN path | `HF_ENDPOINT` for regional mirrors |
| Batch downloads | Reduce connection overhead | Sequential vs parallel download tuning |

### 5.3 Cache Management

The Hugging Face Hub cache system (`~/.cache/huggingface/hub/`) stores previously downloaded models and datasets. Proper cache management:

- **Prevents re-downloads** of large model files across sessions
- **Store cache on large disk** if processing many models
- **Monitor cache size** with `huggingface_hub` utilities:
  ```python
  from huggingface_hub import scan_cache_dir
  cache_info = scan_cache_dir()
  print(f"Total cache size: {cache_info.size_on_disk / 1e9:.2f} GB")
  ```

---

## 6. API and Rate Limit Integration

### 6.1 Rate Limit Headers

The HF Hub returns rate limit information in HTTP response headers:

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Requests allowed per window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Timestamp when the window resets |
| `Retry-After` | Seconds to wait before retrying (on 429) |

### 6.2 Egress-Aware Usage Patterns

```python
from huggingface_hub import HfApi
import time

api = HfApi()

# Check remaining rate limit before large downloads
model_info = api.model_info("meta-llama/llama-2-7b")
file_size_gb = sum(f.size for f in model_info.siblings) / 1e9
print(f"Model download size: {file_size_gb:.1f} GB")

# Cache-aware model loading
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/llama-2-7b",
    cache_dir="/path/to/large/disk/cache",  # Prevent re-downloads
    local_files_only=False  # Use cache when available
)
```

---

## 7. Practical Dashboard Walkthrough (Expected Flow)

While the dashboard requires authentication, the expected flow is:

1. Navigate to `https://huggingface.co/settings/billing`
2. View current billing period's egress usage (displayed in GB)
3. For org admins: switch to org context to see per-user breakdown
4. Compare against plan limits (free vs PRO)
5. Plan upgrades if regularly exceeding free-tier bandwidth

---

## 8. Key Insights

- **Egress monitoring is new (July 2026):** Previously there was no visibility into individual bandwidth consumption — only rate limits were visible. The dashboard now provides transparency.
- **CDN-only scope (for now):** The current dashboard only counts traffic routed through the HF CDN. As more traffic is directed through the CDN, the dashboard will become more comprehensive.
- **Org per-user breakdown is unique:** Many platforms only show org-level totals. HF's per-user breakdown enables precise attribution and cost management for teams.
- **PRO = bandwidth upgrade:** For heavy downloaders, PRO's higher bandwidth allocation directly improves the experience beyond just rate limit increases.
- **Zero-cost planning:** Free-tier users should stream datasets, cache models, and select only needed data to minimize egress consumption.

---

## Skill Created
`hf-hub-egress-metrics/` — complete reference with dashboard access, org breakdown, CDN coverage, PRO plan bandwidth benefits, and zero-cost monitoring strategies.

## Sources
- HF Hub Changelog: `https://huggingface.co/changelog/egress` (Jul 21, 2026)
- HF Hub Billing Docs: `https://huggingface.co/docs/hub/en/billing`
- HF Hub Rate Limits: `https://huggingface.co/docs/hub/en/rate-limits`
- HF Hub PRO Plan: `https://huggingface.co/pro`
