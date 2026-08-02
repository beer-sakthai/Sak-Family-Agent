# New Asset Discovery via API-Journal Comparison

Documented 2026-07-29 — how to detect newly appeared HF repos that aren't yet tracked in the learning journal or baseline cache.

## Why This Matters

New models, datasets, or Spaces can appear in the HF API without any journal entry recording their creation. They silently become part of the ecosystem with:
- No promotion on existing cards (missing from family tables)
- Stale summary counts ("N models" vs actual count)
- Potential 0-byte data files (empty scaffold)
- No record of their purpose or provenance

Without active API-journal comparison, these assets drift unnoticed for multiple cron cycles.

## Detection: API vs Last-Known-Baseline

### Step 1: Fetch current API state

```bash
# WARNING: HF author parameter is CASE-SENSITIVE — "Nanthasit" not "nanthasit"
# Using lowercase returns an empty result silently
curl -s -o /tmp/models.json "https://huggingface.co/api/models?author=Nanthasit"
curl -s -o /tmp/datasets.json "https://huggingface.co/api/datasets?author=Nanthasit"
curl -s -o /tmp/spaces.json "https://huggingface.co/api/spaces?author=Nanthasit"
```

### Step 2: Cross-reference with journal snapshot

The last journal entry's "State at End of Cron" table records baseline counts. Any repo present in the API but absent from the journal is a new discovery.

```bash
python3 << 'DISCOVERY'
import json, re

# Load current API state
with open('/tmp/models.json') as f:
    models = json.load(f)
with open('/tmp/datasets.json') as f:
    datasets = json.load(f)

# Known baseline repos from last journal entry
KNOWN = {
    "sakthai-context-1.5b-merged", "sakthai-context-0.5b-merged",
    "sakthai-context-7b-merged", "sakthai-context-7b-128k",
    "sakthai-context-7b-tools", "sakthai-context-1.5b-tools",
    "sakthai-embedding-multilingual", "sakthai-context-0.5b-tools",
    "sakthai-coder-1.5b", "sakthai-vision-7b", "sakthai-tts-model",
    # Add v2 once discovered
}

# Find API models not in KNOWN
for m in models:
    name = m['id'].split('/')[-1]
    if name not in KNOWN and name != 'Nanthasit':  # skip profile
        print(f"🆕 NEW MODEL: {m['id']} ({m.get('downloads',0)} dl) — {m.get('pipeline_tag','?')}")

# Find API datasets not tracked
known_ds = {"sakthai-combined-v6", "sakthai-kaggle-notebooks",
            "SimpleToolCalling", "food-penguin-v1", "sakthai-irrelevance-supplement"}
for d in datasets:
    name = d['id'].split('/')[-1]
    if name not in known_ds:
        print(f"🆕 NEW DATASET: {d['id']} ({d.get('downloads',0)} dl)")
DISCOVERY
```

### Step 3: Check for empty scaffolds

New datasets often appear with all 0-byte files (created by API scaffold but never populated):

```bash
python3 << 'CHECK'
import json
with open('/tmp/datasets.json') as f:
    datasets = json.load(f)

# Check all datasets for file sizes
# Use HF API to inspect siblings
import urllib.request
for d in datasets:
    repo_id = d['id']
    url = f"https://huggingface.co/api/datasets/{repo_id}"
    req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    
    empty_files = []
    for sib in data.get('siblings', []):
        if sib['rfilename'] != '.gitattributes' and sib.get('size', -1) == 0:
            empty_files.append(sib['rfilename'])
    
    if empty_files:
        print(f"⚠️  {repo_id}: {len(empty_files)} empty file(s): {', '.join(empty_files)}")
CHECK
```

## HF API Author Quirk

The HF API `author` parameter is **case-sensitive**. This is a known HF API behavior that differs from many other platforms:

- `?author=Nanthasit` → returns all repos ✅
- `?author=nanthasit` → returns empty array `[]` ❌
- `?author=NANTHASIT` → returns empty array ❌

This affects both `huggingface.co/api/models?author=...` and `huggingface.co/api/datasets?author=...`. The `hf` CLI's `--author` parameter has the same sensitivity.

**If you get an empty result, the first thing to check is the case of the author name.**

## What To Do With Discovered Assets

| Asset State | Action |
|-------------|--------|
| New model with card | Add to Family table on high-traffic cards, promote in Low-Download Gems |
| New model without card | Write comprehensive README with YAML frontmatter |
| New dataset with 0-byte files | Flag as "empty scaffold — needs data" in journal |
| New dataset with card | Add to Datasets tables across model cards |
| New Space | Add to Spaces tables across ecosystem |

## Pitfalls

- **Profile repos look like models** — `Nanthasit/Nanthasit` appears as a model in the API but is just a profile card. Always exclude it from your count.
- **`hf models ls --author` uses different pagination than the REST API** — the CLI defaults to `--limit 30` and may not return all repos. Use the REST API (`curl`) for complete results.
- **Models can disappear between scans** — private repos returning 401, deleted repos, or repos moved to a different namespace. If a baseline asset returns 404, it was removed — update the baseline, don't treat it as a bug.
- **`huggingface-cli` is deprecated** (since July 2026) — use `hf` CLI instead. Running `huggingface-cli` prints a deprecation warning and exits non-zero.

## Relation to Other References

- `stale-count-detection.md` — for fixing the count drift after discovering new assets
- `card-enrichment-patterns.md` — for adding missing content to thin cards
- `cron-execution-patterns.md` — for safe cron workflows to upload fixes
