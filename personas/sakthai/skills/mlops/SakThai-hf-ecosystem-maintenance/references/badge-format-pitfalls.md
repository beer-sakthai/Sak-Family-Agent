# Badge Format Pitfalls — shields.io/endpoint vs HF API

## The Problem

`shields.io/endpoint` badges (`https://img.shields.io/endpoint?url=...`) require the target URL to return JSON in the shields.io custom format:

```json
{"schemaVersion": 1, "label": "Downloads", "message": "34", "color": "blue"}
```

The Hugging Face model API endpoint (`GET /api/models/{user}/{repo}`) returns **model metadata** JSON — a completely different schema containing `id`, `downloads`, `likes`, `pipeline_tag`, etc. Using it as a shields.io endpoint produces **"Downloads: invalid"** — a broken badge.

## Correct Pattern

Use a static badge via `shields.io/badge`:

```markdown
<img src="https://img.shields.io/badge/downloads-{count}-blue" alt="Downloads"/>
```

This always renders correctly. The download count is also embedded in the sibling model table on the card, so the static badge is consistent with visible display.

## Also Affects Dataset Cards

The same `shields.io/endpoint` breaking pattern also appears on dataset READMEs. Dataset badges may use either of these broken forms:

**Pattern A — direct API URL (no query):**
```markdown
<img src="https://img.shields.io/endpoint?url=https://huggingface.co/api/datasets/Nanthasit/<dataset>&label=Downloads&color=blue" alt="Downloads"/>
```
URL-decoded: `endpoint?url=https://huggingface.co/api/datasets/Nanthasit/<dataset>&label=Downloads&color=blue`

**Pattern B — URL-encoded with `query` parameter:**
```markdown
<img src="https://img.shields.io/endpoint?url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fdatasets%2FNanthasit%2F<dataset>&query=%24.downloads&label=Downloads&color=blue" alt="Downloads"/>
```
URL-decoded: `endpoint?url=https://huggingface.co/api/datasets/Nanthasit/<dataset>&query=$.downloads&label=Downloads&color=blue`

Both produce **"Downloads: invalid"** because the HF API returns dataset metadata JSON, not the shields.io endpoint protocol (`{schemaVersion, label, message, color}`).

Fix both to the same static format:
```markdown
<img src="https://img.shields.io/badge/downloads-{count}-blue" alt="Downloads"/>
```

## Comprehensive Audit — Check ALL Repo Types

**Critical lesson (2026-07-30):** A badge fix that only audits one repo type will miss the others. Cron #026 fixed 11 model cards but left 2 dataset cards with broken badges. The fix is to search across ALL repo types at once:

```bash
# Check every model for broken endpoint badges
for model in $(curl -s "https://huggingface.co/api/models?author=Nanthasit" | python3 -c "
import sys,json; ms=json.load(sys.stdin)
for m in ms:
    if m['id'] != 'Nanthasit/Nanthasit': print(m['id'].split('/')[-1])
"); do
  README=$(curl -s "https://huggingface.co/Nanthasit/$model/raw/main/README.md" 2>/dev/null)
  if echo "$README" | grep -q 'shields.io/endpoint'; then
    echo "❌ model/$model — HAS endpoint badge"
  fi
done

# Check every dataset
for ds in $(curl -s "https://huggingface.co/api/datasets?author=Nanthasit" | python3 -c "
import sys,json; ds=json.load(sys.stdin)
for d in ds: print(d['id'].split('/')[-1])
"); do
  README=$(curl -s "https://huggingface.co/datasets/Nanthasit/$ds/raw/main/README.md" 2>/dev/null)
  if echo "$README" | grep -q 'shields.io/endpoint'; then
    echo "❌ dataset/$ds — HAS endpoint badge"
  fi
done

# Check every Space
for sp in $(curl -s "https://huggingface.co/api/spaces?author=Nanthasit" | python3 -c "
import sys,json; sp=json.load(sys.stdin)
for s in sp: print(s['id'].split('/')[-1])
"); do
  README=$(curl -s "https://huggingface.co/spaces/Nanthasit/$sp/raw/main/README.md" 2>/dev/null)
  if echo "$README" | grep -q 'shields.io/endpoint'; then
    echo "❌ space/$sp — HAS endpoint badge"
  fi
done

echo "✅ All repos checked."
```

## Batch Fix Script — All Repo Types

```python
import re, os
from huggingface_hub import HfApi

api = HfApi(token=os.environ["HF_TOKEN"])

# (repo_suffix, repo_type, count)
ASSETS = [
    # Models
    ("sakthai-context-1.5b-merged", "model", 1269),
    ("sakthai-context-0.5b-merged", "model", 1030),
    # ... add all models
    # Datasets
    ("sakthai-combined-v7", "dataset", 0),
    ("sakthai-irrelevance-supplement", "dataset", 0),
    # ... add all datasets
]

for repo_suffix, repo_type, count in ASSETS:
    repo_id = f"Nanthasit/{repo_suffix}"
    readme = api.hf_hub_download(repo_id=repo_id, filename="README.md", repo_type=repo_type)
    with open(readme) as f:
        content = f.read()

    original = content

    # Pattern: shields.io/endpoint with any query params (URL-encoded or not)
    # Matches: endpoint?url=...<anything>&label=downloads...
    content = re.sub(
        r'<img\s+src="https://img\.shields\.io/endpoint\?url='
        r'https?%3A%2F%2F[^"]*'
        r'huggingface\.co%2Fapi%2F[^"]+'
        r'&[^"]*label=[Dd]ownloads[^"]*'
        r'"\s+alt="[Dd]ownloads"\s*/>',
        f'<img src="https://img.shields.io/badge/downloads-{count}-blue" alt="Downloads"/>',
        content,
    )
    # Also catch non-URL-encoded form
    content = re.sub(
        r'<img\s+src="https://img\.shields\.io/endpoint\?url='
        r'https://huggingface\.co/api/(models|datasets|spaces)/Nanthasit/'
        + re.escape(repo_suffix)
        + r'[^"]*label=[Dd]ownloads[^"]*'
        + r'"\s+alt="[Dd]ownloads"\s*/>',
        f'<img src="https://img.shields.io/badge/downloads-{count}-blue" alt="Downloads"/>',
        content,
    )
    # <a> wrapping <img> pattern
    content = re.sub(
        r'<a\s+href="https://img\.shields\.io/endpoint\?url='
        r'https://huggingface\.co/api/(models|datasets|spaces)/Nanthasit/'
        + re.escape(repo_suffix)
        + r'[^"]*label=[Dd]ownloads[^"]*">\s*\n?\s*'
        r'<img\s+src="https://img\.shields\.io/endpoint\?url='
        r'https://huggingface\.co/api/(models|datasets|spaces)/Nanthasit/'
        + re.escape(repo_suffix)
        + r'[^"]*label=[Dd]ownloads[^"]*"\s+alt="[Dd]ownloads"\s*/>\s*\n?\s*</a>',
        f'<img src="https://img.shields.io/badge/downloads-{count}-blue" alt="Downloads"/>',
        content,
    )

    if content != original:
        api.upload_file(
            path_or_fileobj=content.encode(),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type=repo_type,
            commit_message=f"fix: replace broken endpoint badge ({count} dl)",
        )
```

## Verification

After patching, verify by fetching each README across ALL repo types and checking:

```bash
curl -s -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/Nanthasit/{model}/raw/main/README.md" \
  | grep 'shields.io/badge' | grep download
```

Expected output for each model: `shields.io/badge/downloads-{count}-blue`

## Affected Assets (last fixed 2026-07-30)

### Models (11 fixed in cron #026)
All 11 production model cards had broken badges and were fixed:
- context-1.5b-merged, context-0.5b-merged, context-7b-merged
- context-7b-tools, context-1.5b-tools, context-0.5b-tools
- embedding-multilingual, embedding (private)
- vision-7b, coder-1.5b, tts-model

### Datasets (2 fixed in cron #030)
Two dataset cards were retrospectively fixed after the comprehensive audit caught them:
- sakthai-combined-v7 (0 dl) — used Pattern A (direct API URL)
- sakthai-irrelevance-supplement (0 dl) — used Pattern B (URL-encoded with `query=$.downloads`)

### Remaining
- All Spaces use `index.html` (not `README.md`) or static HTML — no badge badges found
- No `shields.io/endpoint` patterns remain anywhere in the ecosystem ✅
