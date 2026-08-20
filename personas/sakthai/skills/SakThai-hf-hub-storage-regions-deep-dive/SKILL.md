---
name: SakThai-hf-hub-storage-regions-deep-dive
description: "Complete deep-dive on Hugging Face Hub Storage Regions \u2014 data residency controls\
  \ for Team & Enterprise organizations, region selection (US/EU/coming Asia-Pacific),\
  \ GDPR compliance, performance optimization, Repository tags, Spaces region binding,\
  \ and practical workflows for multi-region ML teams."
---

# Hugging Face Hub — Storage Regions Deep Dive

## Overview

Storage Regions allow Team & Enterprise organizations to control **where their ML assets are physically stored** — models, datasets, Spaces, and buckets. This is a **Team/Enterprise plan feature** ($20/user/month for Team). For Free and PRO users, all repos are stored in the **US**.

**Why storage regions matter:**

- **Regulatory compliance** — GDPR, data sovereignty laws, industry regulations (finance, healthcare, government)
- **Performance** — models/datasets stored closer to compute infrastructure = dramatically faster upload/download
- **Latency reduction** — EU users see ~4–5× faster speeds when repos are stored in EU vs US

## Available Regions

| Region | Code | Status | Use Case |
|--------|------|--------|----------|
| **United States** 🇺🇸 | `us` | **Default for all plans** | Global default, best for NA-based teams |
| **European Union** 🇪🇺 | `eu` | **Active** (Team/Enterprise) | GDPR compliance, EU-based teams |
| **Asia-Pacific** 🌏 | — | **Coming soon** | APAC teams, latency optimization |
| **GCC (KSA)** 🇸🇦 | — | **Coming soon** | Middle East data residency |

## Key Concepts

### How It Works

Organizations on Team/Enterprise plans access a **Regions settings page** in their organization dashboard. This page provides:

1. **Audit view** — shows where every repository is currently stored
2. **Default region selector** — sets where new repos will be created
3. **Per-repo migration** — move existing repos between regions

### Repository Region Tag

Any repository stored in a **non-default** region displays a **region badge** on its page:

- `EU` tag on model/dataset/space cards stored in the European Union
- Tags appear in search results, collections, and the repo page header
- Helps organization members quickly identify data locations

### Spaces Region Binding

When an organization selects a storage region, Spaces **both store and run** in that region:

- **Storage** — the Space's code, data, and persistent files live in the chosen region
- **Runtime** — the Space's compute (CPU/GPU) also runs in data centers within that region
- **Limitation:** Some advanced compute options (e.g., ZeroGPU) may not be available in all regions
- Hardware configuration options vary by region — contact HF account team for specific requests

### GDPR Compliance

For EU companies, using Storage Regions provides:

- Models, datasets, and inference endpoints stored in EU data centers
- Full GDPR-compliant ML development workflow on the Hub
- Audit trail showing data location for regulatory reporting
- Supports data processing agreements (DPA) with Hugging Face

## Performance Impact

The performance difference between regions is **substantial** due to model weight file sizes (GBs to hundreds of GBs):

| Scenario | US Region (from EU) | EU Region (from EU) | Improvement |
|----------|-------------------|-------------------|-------------|
| Upload 7B model (~14 GB) | ~45–60s | ~10–15s | ~4× faster |
| Download 70B model (~140 GB) | ~8–12 min | ~2–3 min | ~4–5× faster |
| Dataset streaming (large CSV) | Higher latency | Lower latency | ~3–5× faster |

The improvement comes from:
- **Shorter network distance** — data doesn't cross the Atlantic
- **Better peering** — within-region routes are more direct
- **CDN optimization** — regional edge caches serve closer locations

## Practical Workflows

### Workflow 1: Select a Storage Region (Org Admin)

1. Navigate to your organization's **Settings → Regions**
2. View the current repository location audit
3. Select the default region for new repos (e.g., `EU`)
4. Optionally migrate existing repos to the new region
5. All new models, datasets, Spaces, and buckets will now be stored in the chosen region

### Workflow 2: Verify Region Placement

Via the web UI, check the repository page for the region tag (e.g., `EU` badge).

Via the Hugging Face API:

```python
import requests
token = open("/path/to/token").read().strip()

# Check a model's storage metadata
resp = requests.get(
    "https://huggingface.co/api/models/org-name/model-name",
    headers={"Authorization": f"Bearer {token}"}
)
data = resp.json()
# Look for storage-related fields
storage = data.get("storage", {})
print(f"Region: {storage.get('region', 'us (default)')}")
```

### Workflow 3: Cross-Region Team Setup

- **US-based team** → store repos in US (default)
- **EU-based team** → create EU org or use org-level EU region
- **Multi-region teams** → use separate organizations per region, or contact HF for custom setups
- **Compliance requirements** → ensure all repos + inference endpoints + Spaces are in the required region

## Relation to Other HF Features

| Feature | Relationship to Storage Regions |
|---------|--------------------------------|
| **Storage Limits** | Region-agnostic — limits apply regardless of storage location |
| **Xet Storage Backend** | Works within any region; Xet deduplication/acceleration is transparent to region |
| **Storage Buckets** | Buckets can also be region-pinned under org settings |
| **Spaces Dev Mode** | Dev mode runs in the Space's chosen region |
| **Inference Endpoints** | Can be deployed in the same region as model storage for optimal performance |
| **Audit Logs** | Log repo region changes for compliance tracking |
| **Resource Groups** | Control which teams can access repos in specific regions |
| **CDN & Egress** | Regional CDN edges serve cached content; egress is included at no extra cost |

## Limitations & Considerations

- **Team/Enterprise only** — not available on Free or PRO individual accounts
- **No per-repo region selection** — region is org-level, set globally or migrated individually through the settings page
- **Feature parity varies** — ZeroGPU and certain hardware tiers may not be available in all regions
- **Migration time** — moving large repos between regions takes time proportional to repo size
- **Coming regions** — Asia-Pacific and GCC regions are announced but not yet available
- **No programmatic API** — region configuration is done via the web UI settings page; there is no dedicated REST API or `huggingface_hub` Python method for storage regions
- **Authentication** — only org admins can view or change storage region settings

## Verification

### Check if a model/dataset is stored in EU vs US

```bash
# Using the HF API (requires org token)
curl -s "https://huggingface.co/api/models/org-name/model-name" \
  -H "Authorization: Bearer $HF_TOKEN" | python3 -c "
import json,sys
d = json.load(sys.stdin)
# Check if the model has a storage region indicator
region = d.get('storage', {}).get('region', 'us')
print(f'Storage region: {region}')
# Check for custom metadata indicating region
card_data = d.get('cardData', {})
if card_data.get('region'):
    print(f'Card-declared region: {card_data[\"region\"]}')
"
```

### Verify Team Plan Access

```bash
# Check if your org has Team plan (required for Storage Regions)
curl -s "https://huggingface.co/api/organizations/org-name" \
  -H "Authorization: Bearer $HF_TOKEN" | python3 -c "
import json,sys
d = json.load(sys.stdin)
plan = d.get('plan', 'free')
print(f'Org plan: {plan}')
print(f'Storage Regions available: {plan in (\"team\", \"enterprise\")}')
"
```

## References

- [Official Docs: Storage Regions on the Hub](https://huggingface.co/docs/hub/en/storage-regions)
- [Pricing Page](https://huggingface.co/pricing) — Team plan details ($20/user/month)
- [Storage Limits Docs](https://huggingface.co/docs/hub/en/storage-limits)
- [Spaces Disk Usage & Storage](https://huggingface.co/docs/hub/en/spaces-storage)
- [Resource Groups Access Control](https://huggingface.co/docs/hub/en/resource-groups)
- [Audit Logs](https://huggingface.co/docs/hub/en/audit-logs)
- [Hub API Endpoints](https://huggingface.co/docs/hub/en/api)
- [Xet Storage Backend](https://huggingface.co/docs/hub/en/xet-storage)
- [Storage Buckets Access Patterns](https://huggingface.co/docs/hub/en/storage-buckets-access)
