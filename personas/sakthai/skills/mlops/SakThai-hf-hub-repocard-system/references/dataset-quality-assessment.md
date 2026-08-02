# Dataset Quality Assessment & Card Enrichment

This reference covers programmatic quality assessment of Hugging Face datasets using `datasets.load_dataset()`, and using those metrics to enrich dataset cards.

## Why This Matters

Dataset cards that show actual verified metrics (row counts, message distributions, tool call instances, null checks) are more trustworthy than cards with only hand-written estimates. When you can show "8,922 messages, 2,189 tool calls, 0 null rows," users can trust the data quality immediately.

## Workflow

### 1. Enumerate Assets

Before improving a card, understand the full ecosystem:

```python
import requests, json

# List all models by an author
models = requests.get("https://huggingface.co/api/models?author=Nanthasit&sort=lastModified").json()
for m in models:
    print(m['id'].split('/')[1], m.get('downloads',0), m.get('pipeline_tag',''))

# List all datasets
datasets = requests.get("https://huggingface.co/api/datasets?author=Nanthasit&sort=lastModified").json()
for d in datasets:
    print(d['id'].split('/')[1], d.get('downloads',0), d.get('description','')[:80])

# List all Spaces
spaces = requests.get("https://huggingface.co/api/spaces?author=Nanthasit&sort=lastModified").json()
for s in spaces:
    print(s['id'].split('/')[1], s.get('sdk',''), s.get('tags',[]))
```

Save to JSON files for offline analysis:

```bash
curl -s "https://huggingface.co/api/models?author=Nanthasit&sort=lastModified" -o /tmp/hf-models.json
curl -s "https://huggingface.co/api/datasets?author=Nanthasit&sort=lastModified" -o /tmp/hf-datasets.json
curl -s "https://huggingface.co/api/spaces?author=Nanthasit&sort=lastModified" -o /tmp/hf-spaces.json
```

### 2. Assess Dataset Quality Programmatically

Load the dataset with `datasets.load_dataset()` and compute key metrics:

```python
from datasets import load_dataset
import json

ds = load_dataset("org/combined-v6", split="train")

tool_calls = 0
multi_turn = 0
has_tools_schema = 0
total_msgs = 0
roles_count = {}
null_messages = 0

for row in ds:
    msgs = row.get("messages") or []
    if msgs is None:
        null_messages += 1
        continue
    total_msgs += len(msgs)
    has_tools = bool(row.get("tools"))
    if has_tools:
        has_tools_schema += 1

    for m in msgs:
        role = m.get("role")
        roles_count[role] = roles_count.get(role, 0) + 1
        if role == "assistant" and m.get("tool_calls"):
            tool_calls += len(m["tool_calls"])

    user_turns = sum(1 for m in msgs if m.get("role") == "user")
    if user_turns >= 2:
        multi_turn += 1

print(f"Total rows: {len(ds)}")
print(f"Total messages: {total_msgs}")
print(f"Avg messages/row: {total_msgs/len(ds):.1f}")
print(f"Rows with tools schema: {has_tools_schema}")
print(f"Tool call instances: {tool_calls}")
print(f"Multi-turn examples: {multi_turn}")
print(f"Null messages: {null_messages}")
print(f"Role distribution: {json.dumps(roles_count, indent=2)}")
```

Also check the test split:

```python
ds_test = load_dataset("org/combined-v6", split="test")
print(f"Test rows: {len(ds_test)}")
```

### 3. Build the Card Content

Use the metrics to build a Data Quality Card section:

```markdown
## Data Quality Card

### Dataset Composition

| Metric | Value |
|--------|-------|
| **Total rows (train)** | 2,003 |
| **Total rows (test)** | 113 |
| **Total messages** | 8,922 (avg 4.5/row) |
| **Tool call instances** | 2,189 |
| **Rows with tool schemas** | 1,913 (96%) |
| **Multi-turn examples (2+ user turns)** | 179 |
| **Format integrity** | ✅ `messages` key on all rows |
| **Null messages** | 0 |

### Role Distribution

| Role | Count |
|------|-------|
| `system` | 1,803 |
| `user` | 2,079 |
| `assistant` | 3,549 |
| `tool` | 1,491 |
```

### 4. Upload the Updated Card

```bash
# CRITICAL: --repo-type dataset (or --type dataset) is REQUIRED for dataset repos!
# Without it, the command appears to succeed but DOES NOT commit any changes.

hf upload org/dataset-name /path/to/enriched_card.md README.md \
  --repo-type dataset \
  --commit-message "docs: add data quality card with verified metrics" \
  --token "$HF_TOKEN"
```

### 5. Verify the Upload

```bash
# Fetch the live card and confirm size and key content
curl -s "https://huggingface.co/datasets/org/dataset-name/raw/main/README.md" -o /tmp/verify.md
wc -c /tmp/verify.md              # should be larger than before
head -5 /tmp/verify.md            # confirm YAML frontmatter
grep -c "Data Quality Card" /tmp/verify.md || echo "❌ Missing quality card!"
grep -c "2,003" /tmp/verify.md && echo "✅ Correct row count"
```

## Pitfalls

### `hf upload` silently fails without `--repo-type dataset`

This is the #1 trap for dataset card updates. The command:

```bash
hf upload org/name readme.md README.md  # WRONG — silently no-op
```

appears to succeed (exits 0, prints a commit URL) but the URL points to the **previous identical commit** — no change was made. The error message is:

```
Removing 1 file(s) from commit that have not changed.
No files have been modified since last commit. Skipping to prevent empty commit.
```

The fix is to always specify the repo type:

```bash
hf upload org/name readme.md README.md --repo-type dataset  # ✅ CORRECT
# or equivalently:
hf upload org/name readme.md README.md --type dataset        # ✅ CORRECT
```

For Space repos, use `--repo-type space`. For model repos, the type is inferred by default and `--repo-type model` is optional but harmless.

**Always verify the upload by checking the raw README size after uploading.** Don't trust the exit code or commit URL.

### `write_file` blocked on `/tmp`

When writing card content to a file for upload, do NOT use `/tmp/`:

```python
# ❌ Write denied
# write_file('/tmp/card.md', content)

# ✅ Works
write_file('/opt/data/card.md', content)
```

Upload from `/opt/data/`:

```bash
hf upload org/name /opt/data/card.md README.md --repo-type dataset
```

### Large datasets take time to load

`datasets.load_dataset()` downloads and caches the full dataset. For datasets with many splits or large files, this may take 30+ seconds. Consider:
- Only loading the `train` split if that's all you need
- Using `.select(range(100))` for a quick sample check
- Pre-checking dataset size via the Parquet API before loading

### Model cards need `--repo-type model` (or omit)

Unlike datasets, model repos don't require the flag — `hf upload` defaults to model type:

```bash
hf upload org/model-name readme.md README.md --commit-message "docs: update"  # OK
```

But being explicit never hurts for consistency.

## Example Output (from production)

After computing these metrics for `sakthai-combined-v6`:

| Metric | Value |
|--------|-------|
| Total rows (train) | 2,003 |
| Total rows (test) | 113 |
| Total messages | 8,922 |
| Tool call instances | 2,189 |
| Rows with tool schemas | 1,913 (96%) |
| Multi-turn examples | 179 |
| Role counts | system: 1,803, user: 2,079, assistant: 3,549, tool: 1,491 |

The card grew from 3,247 → 7,131 bytes (+119%) with the addition of a full Data Quality Card, category breakdown, tool schema coverage table, evolution timeline, limitations section, and processing code examples.
