# Dataset JSONL Integrity — Detection, Fix, and Verification

Captured 2026-07-29 during a cron run that fixed `sakthai-irrelevance-supplement` (0 dl) — a dataset whose `.jsonl` file was actually a JSON array.

## The Problem

A `.jsonl` file stored as a JSON array (`[{...}, ...]`) instead of one JSON object per line is the most common data-integrity bug in Hugging Face datasets. Libraries expecting line-delimited JSON silently produce zero rows. Training scripts (TRL, Axolotl, llama-factory) load the dataset and train on nothing.

Zero-download datasets often have this bug — nobody has tried to load them yet.

## Detection: Quick check via curl (single dataset)

```bash
auth_header="Authorization: Bearer $(cat ~/.cache/huggingface/token)"
for file in data/train.jsonl data/test.jsonl; do
  first_byte=$(curl -s -H "$auth_header" \
    "https://huggingface.co/datasets/Nanthasit/dataset-name/raw/main/$file" | head -c 1)
  if [ "$first_byte" = "[" ]; then
    echo "$file: JSON array (starts with [) — broken JSONL"
  elif [ "$first_byte" = "{" ]; then
    echo "$file: valid JSONL"
  else
    echo "$file: starts with '$first_byte'"
  fi
done
```

## Detection: Scan all sibling datasets

```python
from huggingface_hub import HfApi
import json

api = HfApi()
author = "Nanthasit"

for ds in api.list_datasets(author=author):
    try:
        siblings = api.get_repo_info(ds.id, repo_type="dataset").siblings
    except Exception:
        continue

    jsonl_files = [s.rfilename for s in siblings if s.rfilename.endswith(".jsonl")]
    if not jsonl_files:
        continue

    print(f"\n{ds.id.split('/')[1]}:")
    for filepath in jsonl_files:
        try:
            local = api.hf_hub_download(ds.id, filepath, repo_type="dataset")
            with open(local) as f:
                first_char = f.read(1)
                f.seek(0)
                content = f.read()

            if first_char == "[":
                try:
                    parsed = json.loads(content)
                    print(f"  {filepath}: JSON ARRAY ({len(parsed)} items) — should be JSONL")
                except json.JSONDecodeError:
                    print(f"  {filepath}: invalid JSON")
            elif first_char == "{":
                lines = content.strip().split("\n")
                valid = sum(1 for line in lines if json.loads(line.strip()) or True)
                print(f"  {filepath}: JSONL ({valid} valid lines, {len(content)} bytes)")
            else:
                print(f"  ? {filepath}: starts with {repr(first_char)}")
        except Exception as e:
            print(f"  ? {filepath}: {e}")
```

## Fix: Convert JSON array to JSONL

```python
import json

with open("broken.jsonl") as f:
    data = json.load(f)

with open("fixed.jsonl", "w") as f:
    for item in data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
```

## Fix: Upload to HF

```python
from huggingface_hub import HfApi, CommitOperationAdd

api = HfApi()

# Option A: file on disk
api.upload_file(
    path_or_fileobj="/tmp/fixed.jsonl",
    path_in_repo="data/train.jsonl",
    repo_id="Nanthasit/dataset-name",
    repo_type="dataset",
    commit_message="fix: convert JSON array to proper JSONL (one object per line)"
)

# Option B: in-memory (cron-safe, no temp file)
with open("/tmp/fixed.jsonl") as f:
    content = f.read()
api.create_commit(
    repo_id="Nanthasit/dataset-name",
    repo_type="dataset",
    operations=[CommitOperationAdd(
        path_in_repo="data/train.jsonl",
        path_or_fileobj=content.encode()
    )],
    commit_message="fix: convert JSON array to proper JSONL"
)
```

## Fix: Update README with integrity notice

Add to the dataset card's README:

```markdown
> **2026-07-29 integrity fix:** Converted from JSON array to proper JSONL.
> Previously stored as `[{...},...]` in a `.jsonl` file, which broke standard
> parsers. Now each line is a standalone JSON object — compatible with
> `datasets`, TRL, and all training pipelines.
```

This builds trust and explains why the dataset had low downloads.

## Verification

```python
import urllib.request, json

url = "https://huggingface.co/datasets/Nanthasit/dataset-name/raw/main/data/train.jsonl"
resp = urllib.request.urlopen(url)
lines = resp.read().decode().strip().split("\n")

all_valid = True
for i, line in enumerate(lines):
    try:
        obj = json.loads(line)
        assert "messages" in obj, f"Line {i}: missing 'messages'"
        assert "tools" in obj, f"Line {i}: missing 'tools'"
    except (json.JSONDecodeError, AssertionError) as e:
        print(f"Line {i}: {e}")
        all_valid = False

print(f"{'OK' if all_valid else 'FAIL'} {len(lines)} lines, all valid JSONL")
```

## Real-world example (2026-07-29)

**Target:** `Nanthasit/sakthai-irrelevance-supplement` (0 dl)
**Bug found:** `data/train.jsonl` was a JSON array — 10 items in a single JSON document stored with `.jsonl` extension.
**Impact:** Libraries expecting line-delimited JSON would silently produce zero rows. This likely contributed to 0 downloads — the dataset was structurally broken.
**Fix:** Converted to proper JSONL (10 lines, each independently parseable). Updated README with integrity notice, accurate schema docs, corrected stale counts (11 to 14 models).
**Verification:** All 10 lines valid JSONL with expected keys. README fix notice present.

## Related skills

- `hf-ecosystem-maintenance` — parent skill for this reference
- `hf-datasets-data-validation-quality` skill section 7.4 — programmatic JSONL format validation
- `references/cron-mode-workarounds.md` — for handling cron restrictions during upload
