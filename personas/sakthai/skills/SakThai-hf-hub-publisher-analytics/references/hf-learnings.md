# HF Hub Publisher Analytics — Complete Deep-Dive

## Topic: hf-hub-publisher-analytics (#397)
**Date:** 2026-07-26
**Author:** SakThai
**License:** MIT

---

## 1. Overview

**Publisher Analytics** is an Enterprise-tier feature on the Hugging Face Hub that gives organizations detailed visibility into download activity across all their Models and Datasets. It solves the problem of understanding aggregate usage when you manage multiple repositories as an organization.

### Who needs it
- **Organizations** managing 10+ models/datasets who need aggregate dashboards
- **Enterprise teams** needing per-repo drill-down with time-series trends
- **Compliance teams** requiring per-request audit logs (Enterprise Plus add-on)
- **Model publishers** wanting to track download growth over time

### What it provides
| Feature | Availability |
|---------|-------------|
| Dashboard (All Time / Last Month) | Team & Enterprise |
| Per-repo breakdown with time-series | Team & Enterprise |
| CSV Export via UI & API | Team & Enterprise |
| Unique downloader detection | Enterprise Plus add-on |
| Request-level access logs | Enterprise Plus add-on |

---

## 2. Publisher Analytics Dashboard

The dashboard is accessible from the organization settings page:
`https://huggingface.co/organizations/YOUR_ORG_NAME/settings/publisher-analytics`

### Key dashboard features

**Aggregate view:** Shows total downloads for ALL Models and Datasets published by your organization. This is the first number you see — your org's overall download footprint.

**Time range toggle:** Switch between "All Time" and "Last Month" to understand recent momentum vs. lifetime impact.

**Use case:** Quickly answer "How many total downloads did our org get last month?" or "Which repos are driving the most traffic?"

---

## 3. Per-Repo Breakdown

The drill-down table beneath the aggregate view provides per-repository analytics:

- **Repository search** — Find specific repos by name
- **Row per repo** — Each Model or Dataset gets its own row
- **Time-series graph** — Every row includes a mini sparkline showing download trend over time
- **Sort/Filter** — Sort by total downloads, name, or repository type

This is where you identify which of your models are gaining traction and which ones are stagnant.

---

## 4. CSV Export API

The most powerful programmatic access is via the CSV export endpoint:

### Endpoint
```
GET https://huggingface.co/organizations/YOUR_ORG_NAME/settings/publisher-analytics/download-breakdown
Authorization: Bearer YOUR_HF_TOKEN
```

### cURL example
```bash
curl -H "Authorization: Bearer YOUR_HF_TOKEN" \
  "https://huggingface.co/organizations/YOUR_ORG_NAME/settings/publisher-analytics/download-breakdown" \
  --output breakdown.csv
```

### CSV Response Structure
Each record represents one day of downloads for one repository:

```csv
repoType,repoName,total,timestamp,downloads
model,huggingface/CodeBERTa-small-v1,4362460,2021-01-22T00:00:00.000Z,4
model,huggingface/CodeBERTa-small-v1,4362460,2021-01-23T00:00:00.000Z,7
dataset,huggingface/documentation-images,2167284,2021-11-27T00:00:00.000Z,3
dataset,huggingface/documentation-images,2167284,2021-11-28T00:00:00.000Z,18
```

### Field Reference
| Field | Type | Description |
|-------|------|-------------|
| `repoType` | string | `"model"`, `"dataset"`, or `"space"` |
| `repoName` | string | Full repository name including org (e.g. `huggingface/CodeBERTa-small-v1`) |
| `total` | integer | Cumulative total downloads for this repository (as of export time) |
| `timestamp` | ISO 8601 | Date in UTC (`YYYY-MM-DDTHH:MM:SS.sssZ`) |
| `downloads` | integer | Number of downloads on that specific day |

### Important notes
- Records are ordered **chronologically** (ascending by timestamp)
- Provides **daily granularity** — one row per repo per day
- Download figures are **NOT deduplicated by user** — if the same user downloads the same file 5 times, that counts as 5 downloads
- For deduplicated counts, use the Enterprise Plus add-on

---

## 5. Enterprise Plus: Unique Downloader Detection

### Granular access logs
The Enterprise Plus add-on provides **anonymized, request-level access logs** for all Models and Datasets published by your organization. Each line represents a single download-related HTTP request.

### Log column reference
| Column | Description |
|--------|-------------|
| `timestamp` | Request timestamp |
| `status` | HTTP status code (200, 206, 302, 307, 304, etc.) |
| `method` | HTTP method (GET, HEAD, etc.) |
| `repoName` | Full repo name (e.g. `nvidia/segformer-b0`) |
| `repoType` | `model`, `dataset`, or `space` |
| `hashedUserId` | Non-reversible hash of authenticated user ID |
| `hashedIp` | Non-reversible hash of IP (for unauthenticated requests) |
| `country` | ISO country code |
| `region` | Region or city name |
| `userAgent` | HTTP User-Agent header value |

### Key capabilities
- **Deduplicate by user**: Group by `hashedUserId` to count unique downloaders
- **Geographic analysis**: Filter by `country` / `region` to understand where your users are
- **Request patterns**: Classify by `status` and `method` to separate HEAD probes from actual downloads
- **HTTP status classification**: 200/206 = successful download, 302 = redirect to CDN, 307 = temporary redirect, 304 = Not Modified (cache hit)

### Implementation responsibility
> "Your team is responsible for ingesting these logs and running computations on them."

The export includes raw HTTP status codes and methods so you can classify patterns based on your own analytics needs.

### Availability
This is a **custom add-on to Enterprise Plus** requiring setup of a custom data export pipeline (Elastic index, etc.) on Hugging Face's side. Not self-serve.

---

## 6. Comparison: Public Download Stats vs. Publisher Analytics

| Aspect | Public Download Stats | Publisher Analytics |
|--------|---------------------|-------------------|
| **Who can see** | Everyone (on model page) | Organization admins only |
| **Granularity** | Per-repo total only | Per-repo daily breakdown |
| **Aggregate** | Single repo only | All repos at once |
| **Export** | No CSV export | CSV export via API |
| **Unique downloaders** | No | Enterprise Plus add-on |
| **Geographic data** | No | Enterprise Plus add-on |
| **Historical trend** | Current total only | Daily time series |
| **Cost** | Free | Team/Enterprise plan |
| **API access** | `huggingface_hub` model stats | Dedicated endpoint |

### Public download stats API (free alternative)
For individual publishers without an Enterprise plan:
```python
from huggingface_hub import HfApi
api = HfApi()
# Get downloads for a specific model
model_info = api.model_info("username/model-name")
print(f"Downloads: {model_info.downloads}")
```

---

## 7. How Hub Download Counting Works

Understanding what Publisher Analytics actually counts:

### Counting rules
- Downloads are counted **server-side** as the Hub serves files
- Every HTTP request (GET and HEAD) to counted files increments the counter
- No client-side tracking, no JavaScript, no cookies

### Query files by library
The Hub uses specific files to count downloads (to avoid double-counting sharded/split models):

| Library | Query File(s) |
|---------|--------------|
| Default (no library) | `config.json` |
| transformers | `config.json` |
| diffusers | Custom filter (top-level `.safetensors` + library-loaded files) |
| GGUF | All `.gguf` files |
| nemo | All `.nemo` files |
| Custom libraries | Configurable via PR to HF internal codebase |

### GGUF handling
GGUF files are self-contained and not tied to a single library — **all GGUF downloads are counted**. This may double-count if someone clones an entire repo, but most users download a single GGUF file per repo.

### Custom query files
You can register your own library's query files by opening a PR to the Hugging Face Hub's internal codebase. See the [integration guide](https://huggingface.co/docs/hub/en/models-uploading) for details.

---

## 8. Practical Use Cases for Sak-Family-Agent

### Tracking Beer's model family downloads
Since Beer owns 11 models (6 text-gen, 1 embedding, 1 code GGUF, 1 vision, 1 TTS, 1 multilingual) across account `Nanthasit`, Publisher Analytics would provide:

- **Aggregate view**: Total downloads across all 11 models
- **Per-model time series**: Which model variants are trending
- **Export for reporting**: CSV data for monthly reports or grant applications

### Implementation plan (if Enterprise)
```python
import pandas as pd
import requests

# Export CSV
resp = requests.get(
    "https://huggingface.co/organizations/Nanthasit/settings/publisher-analytics/download-breakdown",
    headers={"Authorization": f"Bearer {HF_TOKEN}"}
)
df = pd.read_csv(resp.content)

# Per-model summary
summary = df.groupby("repoName").agg(
    total_downloads=("total", "max"),
    last_month=("downloads", "sum")
).sort_values("total_downloads", ascending=False)
```

### Zero-cost alternative
Since Beer's account is individual (not Enterprise), use the public API:
```python
from huggingface_hub import HfApi
api = HfApi()

models = api.list_models(author="Nanthasit")
for model in models:
    info = api.model_info(model.id)
    print(f"{model.id}: {info.downloads} downloads")
```

---

## 9. Model Release Checklist Integration

The **Model Release Checklist** (new Hub docs page) provides a complementary framework for before and after releasing a model — Publisher Analytics helps with the "after" phase.

### Key checklist items related to analytics
- ✅ **Usage Metrics**: Track downloads and likes to understand reach and adoption
- ✅ **Review Community Contributions**: Check for PRs and discussions
- ✅ **Add Evaluation Results**: Use `.eval_results/` folder with Hub benchmark datasets
- ✅ **Enterprise Features**: Publisher Analytics for deeper insights

### Model release best practices (summary)
1. **Use separate repos** per model variant (not directory listing)
2. **Prefer safetensors** over pickle
3. **Write comprehensive model cards** with proper YAML metadata
4. **Register a library** for automatic download tracking
5. **Link related models** via `base_model` and `new_version` metadata
6. **Create a Space demo** linked from the model card
7. **Add quantized variants** (GGUF) in separate repos with `base_model_relation: quantized`

### Evaluation results format
```yaml
# .eval_results/gpqa.yaml
- dataset:
    id: Idavidrein/gpqa
    task_id: diamond
  value: 76.1
  date: "2026-03-19"
  source:
    url: https://huggingface.co/your-org/your-model
    name: Model Card
```

---

## 10. API Reference Summary

### Publisher Analytics CSV Export
```
GET /organizations/{org_name}/settings/publisher-analytics/download-breakdown
Authorization: Bearer {token}
```

### Related public API methods
```python
# huggingface_hub methods
HfApi.get_model_downloads(model_id)  # Total downloads
HfApi.list_models(author=org)        # List org's models with download counts
HfApi.model_info(model_id).downloads # Per-model download count
```

### Granular log export (Enterprise Plus)
Setup via custom pipeline (contact HF Enterprise Sales).

---

## 11. Zero-Cost Analysis

| Need | Free Solution | Paid Solution |
|------|-------------|--------------|
| Single model download count | `HfApi().model_info()` | Publisher Analytics dashboard |
| All org models' download counts | `HfApi().list_models()` + loop | CSV export API |
| Daily breakdown chart | Manual tracking over time | Automatic time-series |
| Unique downloaders | Not available | Enterprise Plus logs |
| Geographic analysis | Not available | Enterprise Plus logs |
| Export to CSV | Build custom scraper | One-click CSV download |

**Recommendation for Beer:** Use `huggingface_hub` API to track downloads across all 11 models. Store snapshots in memory for trend analysis. Publisher Analytics is valuable only if/when the account upgrades to Team/Enterprise.

---

## Sources
- Official HF Hub docs: https://huggingface.co/docs/hub/en/publisher-analytics
- Official HF Hub docs — Model Release Checklist: https://huggingface.co/docs/hub/en/model-release-checklist
- Official HF Hub docs — Models Download Stats: https://huggingface.co/docs/hub/en/models-download-stats
- huggingface_hub Python library: https://huggingface.co/docs/hub/en/models-downloading
- Enterprise plans: https://huggingface.co/pricing
