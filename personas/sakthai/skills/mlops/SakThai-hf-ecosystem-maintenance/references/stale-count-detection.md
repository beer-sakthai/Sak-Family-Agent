# Stale Ecosystem Summary Count Detection

Documented 2026-07-29 — pattern for detecting and fixing stale ecosystem summary counts ("N models", "N datasets", "N Spaces") across model cards, dataset cards, and Space READMEs.

## The Problem

Ecosystem summary counts ("14 models", "4 datasets") embedded in cards are **manually maintained text** — unlike per-model download count badges, these have no dynamic update mechanism. They drift silently when:
- Models are added, deleted, or made private
- Datasets are created or removed
- Spaces are built or deprecated

A card claiming "14 models" when only 11 are downloadable undermines trust and confuses visitors.

## Detection: Scan All Cards for N-Count Patterns

Use `grep` with `\d+\s+models` / `\d+\s+datasets` / `\d+\s+spaces` patterns against every ecosystem card's raw README:

```bash
# Scan ALL repo types for stale counts
for repo_type in dataset model space; do
  case $repo_type in
    dataset) api="datasets" ;;
    model)   api="models" ;;
    space)   api="spaces" ;;
  esac
  
  for repo in $(curl -s "https://huggingface.co/api/$api?author=Nanthasit&page_size=50" \
    | python3 -c "import json,sys; [print(r['id']) for r in json.load(sys.stdin)]"); do
    
    id=$(echo $repo | cut -d/ -f2)
    # Skip profile and placeholder repos
    [[ "$id" == "Nanthasit" || "$id" == "food-penguin-v1" ]] && continue
    
    # Determine raw URL
    raw_url="https://huggingface.co"
    if [ "$repo_type" = "dataset" ]; then raw_url="$raw_url/datasets"; fi
    if [ "$repo_type" = "space" ]; then raw_url="$raw_url/spaces"; fi
    raw_url="$raw_url/$repo/raw/main/README.md"
    
    content=$(curl -sL "$raw_url" 2>/dev/null)
    if [ -z "$content" ]; then
      # Space may use index.html instead of README.md
      raw_url=$(echo "$raw_url" | sed 's|README.md|index.html|')
      content=$(curl -sL "$raw_url" 2>/dev/null)
    fi
    
    counts=$(echo "$content" | grep -oiP '\d+\s+(model|models|dataset|datasets|space|spaces)' | sort | uniq -c)
    if [ -n "$counts" ]; then
      echo "$repo_type/$id: $counts"
    fi
  done
done
```

### Cross-Reference Against Current API State

```bash
# Get actual counts from HF API
curl -s "https://huggingface.co/api/models?author=Nanthasit" \
  | python3 -c "import json,sys; data=json.load(sys.stdin); real=[r for r in data if r['id'] not in ['Nanthasit/Nanthasit','Nanthasit/food-penguin-v1']]; print(f'Models: {len(real)}')"

curl -s "https://huggingface.co/api/datasets?author=Nanthasit" \
  | python3 -c "import json,sys; print(f'Datasets: {len(json.load(sys.stdin))}')"

curl -s "https://huggingface.co/api/spaces?author=Nanthasit" \
  | python3 -c "import json,sys; print(f'Spaces: {len(json.load(sys.stdin))}')"
```

Any card reporting a count that differs from the API result needs fixing.

## Fix

### Python (huggingface_hub)

```python
import os
from huggingface_hub import HfApi

api = HfApi(token=os.environ.get('HF_TOKEN'))

# Fetch current card
path = api.hf_hub_download(
    repo_id='Nanthasit/<repo>',
    filename='README.md',
    repo_type='dataset'  # or 'model', 'space'
)
with open(path) as f:
    content = f.read()

# Replace stale count — verify before/after
old = '14 models'
new = '11 models'
count_before = content.count(old)
content = content.replace(old, new)
count_after = content.count(old)
print(f'Replaced {count_before - count_after} occurrences of {old} → {new}')

# Upload corrected card
api.upload_file(
    path_or_fileobj=content.encode(),
    path_in_repo='README.md',
    repo_id='Nanthasit/<repo>',
    repo_type='dataset',  # CRITICAL: default is 'model'
)
```

### Via `hf upload` CLI

```bash
# Save corrected file locally, then upload
curl -s "https://huggingface.co/datasets/Nanthasit/<repo>/raw/main/README.md" \
  -o /tmp/readme_fixed.md
sed -i 's/14 models/11 models/g' /tmp/readme_fixed.md
hf upload Nanthasit/<repo> /tmp/readme_fixed.md README.md \
  --repo-type dataset \
  --commit-message "docs: fix stale model count 14→11"
```

## Verification

```bash
# Confirm ALL occurrences now show correct count
curl -sL "https://huggingface.co/datasets/Nanthasit/<repo>/raw/main/README.md" \
  | grep -oiP '\d+\s+models' | sort | uniq -c
# Expected: "3 11 models" with no "14 models" remaining
```

## Pitfalls

- **Only check the raw README, never the rendered page.** The rendered page may show a stale cached version. Always use `/raw/main/README.md`.
- **Spaces may use `index.html` instead of `README.md`** for landing content. Check both URLs.
- **Some repos have no README at all** (data-only repos, bare scaffold). Skip them — they don't expose stale counts to visitors.
- **String replacement is a silent no-op if text doesn't match exactly.** Always verify `count_before > 0` before uploading, and re-grep-live after upload.
- **`repo_type` defaults to `'model'`.** Uploading to a dataset or Space without setting the correct type causes a confusing 404.
- **`HF_TOKEN` is an env var, not a file.** In cron context, it's already set. Do not rely on a token file — it may not exist on all runners.
- **Count the right number of "real" models.** Exclude profile repos and redirect/placeholder repos from your count. What the API returns as a "model" may include items users shouldn't download.

---

## Dataset Row Count Drift

A **separate stale-count class**: the number of training examples documented in a dataset README drifts from the actual row count in the data files. Unlike ecosystem summary counts (which change when assets are added), dataset row counts change when examples are appended between versions.

### Detection: Compare README counts against actual JSONL/Parquet row counts

```python
from huggingface_hub import hf_hub_download
import json

# 1. Extract all digit sequences from the README near row-count context
readme = hf_hub_download("Nanthasit/<dataset>", "README.md", repo_type="dataset")
with open(readme) as f:
    content = f.read()

# Look for numbers near row-count keywords — these are likely stale
import re
suspicious = []
for match in re.finditer(r'(\d[\d,]*)\s*(example|row|line|sample|record|entry)', content, re.IGNORECASE):
    suspicious.append(match.group(1).replace(',', ''))

# 2. Count actual lines in data files
train_path = hf_hub_download("Nanthasit/<dataset>", "data/train.jsonl", repo_type="dataset")
with open(train_path) as f:
    actual = len(f.readlines())

# 3. Compare
for claimed in suspicious:
    if int(claimed) != actual:
        print(f"STALE: README says {claimed} but actual is {actual}")
```

### Fix: Replace all stale occurrences across both formats

```python
# From detection step: `suspicious` has claimed counts, `actual` is real count
stale_comma = f"{actual:,}"  # The comma-formatted string to match in prose
stale_plain = str(actual)    # Bare number to match in code comments

# Find the ACTUAL stale values from the suspicious list (not the correct one)
for claimed_str in suspicious:
    if int(claimed_str) == actual:
        continue  # skip — this number is already correct
    # Replace both formats: "2,294" (prose) and "2294" (code comments)
    content = content.replace(claimed_str, f"{actual:,}")

# Upload corrected README
from huggingface_hub import upload_file
upload_file(
    path_or_fileobj=content.encode(),
    path_in_repo="README.md",
    repo_id="Nanthasit/<dataset>",
    repo_type="dataset",
    commit_message="Fix stale training count (actual row count)"
)
```

### Real-world example

`sakthai-combined-v7` README documented **2,294 training examples** across 7 locations (header, code comments, data quality table, evolution table, limitations, growth log). Actual `train.jsonl` contained **2,309 lines** — a 15-row delta from incremental augmentation runs between v7.3 and v7.4. Fixed via commit `f233580dd`.

### Pitfalls

- **Multiple number formats.** The count may appear as both `2,294` (comma-formatted, in prose) and `2294` (bare, in code comments). Both must be replaced.
- **Code comment drift is the most deceptive.** Users who copy-paste the Quick Start code get `print(len(ds))  # 2309` returning a different number than the surrounding text says. This erodes trust faster than just a prose mismatch.
- **Not all numbers in a README are row counts.** A dataset might reference 115 test examples, 86 tool schemas, or 10 augment rounds — those are legitimate and should not be touched. Only replace numbers explicitly labeled as total row/example counts.
- **Row count can legitimately change between versions.** If the README says "v7.3: 2,294 rows" and the current data is v7.4 with 2,309, the version history section is correct and the top-of-file summary is stale. Fix both to match current state.
- **Train/test row counts must be verified independently.** A README might correctly document test rows (115) while being stale on train rows (2,294→2,309).

## Relevant Skill Sections

- `hf-ecosystem-maintenance` → `references/verification-patterns.md` (grep-live checks for content markers, dead links)
- `hf-ecosystem-maintenance` → `references/space-card-enrichment.md` (stale data detection in Space READMEs)
- `hf-ecosystem-maintenance` → `references/cron-execution-patterns.md` (safe cron workflow for HF operations)
