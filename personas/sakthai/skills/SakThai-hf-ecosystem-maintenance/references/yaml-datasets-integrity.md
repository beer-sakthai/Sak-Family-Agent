# YAML Datasets Integrity: Syncing Frontmatter With Body

> Documented 2026-07-29 — pitfall uncovered when TTS model card (69 dl) had 5 datasets in the README body table but only 2 in YAML frontmatter.

## The Gap

HF model cards have **two separate dataset representations** in the same file:

| Where | Purpose | Consumers |
|-------|---------|-----------|
| YAML `datasets:` list (frontmatter) | Machine-readable metadata | HF search index, API `cardData`, dataset-tag-based discovery |
| Body table (e.g. `## 📊 Sibling Datasets`) | Human-readable documentation | Visitors browsing the card |

These **can and do drift** independently. The YAML drives API-visible `cardData.datasets` and the auto-generated `dataset:` tags in the model's tag list. If the YAML is incomplete, the model won't appear in search results filtered by the missing datasets.

## Detection

### 1. Check YAML vs API

```bash
# Get the live YAML datasets from the API
curl -s "https://huggingface.co/api/models/<author>/<repo>" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('cardData',{}).get('datasets',[]))"
```

### 2. Expect 5 for SakThai ecosystem

All SakThai ecosystem model cards should list **all 6 datasets** in YAML:

```
sakthai-combined-v6
sakthai-kaggle-notebooks
SimpleToolCalling
food-penguin-v1
sakthai-combined-v7
sakthai-irrelevance-supplement
```

### 3. Batch check all models

```bash
MODELS="sakthai-context-1.5b-merged sakthai-context-0.5b-merged sakthai-context-7b-merged ..."
for m in $MODELS; do
  count=$(curl -s "https://huggingface.co/api/models/Nanthasit/$m" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('cardData',{}).get('datasets',[])))")
  echo "$m: $count datasets"
done
# Expected: all 6. Any <6 needs a YAML fix.
```

## Fix: Adding Missing Datasets to YAML

### Via git clone (safer — validates file structure)

```bash
git clone https://huggingface.co/<author>/<repo> /tmp/fix-repo
cd /tmp/fix-repo
# Edit README.md — add missing - entries under datasets:
git add README.md
git commit -m "Fix: add missing sibling datasets to YAML frontmatter"
git push
```

### Via hf upload (faster for single-file edits)

```bash
# Download current README, patch, upload
curl -sL "https://huggingface.co/<author>/<repo>/raw/main/README.md" -o /tmp/current.md
# ... edit /tmp/current.md to add missing datasets ...
hf upload <author>/<repo> /tmp/current.md README.md \
  --commit-message "Fix: add all 5 sibling datasets to YAML frontmatter"
```

## Verification: Confirm API Update

After push, verify the API reflects the change:

```bash
curl -s "https://huggingface.co/api/models/<author>/<repo>" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); ds=d.get('cardData',{}).get('datasets',[]); print(f'{len(ds)} datasets: {ds}'); assert len(ds)==6"
```

Also check the `tags` array for `dataset:` prefixed entries — each dataset should generate a `dataset:<author>/<name>` tag for search indexing.

## Root Cause

The YAML datasets list is easy to forget because:

1. The README body table is more visible during editing — it's right there in the rendered page
2. YAML is at the very top, often collapsed in HF's web editor
3. Enrichment cron jobs typically add the body table first, and if the YAML was already present (even incomplete), there's nothing visually "missing"

**Rule:** Every time you add or modify the Sibling Datasets body section, check and update the YAML `datasets:` list in the same commit.
