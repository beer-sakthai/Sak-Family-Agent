# Dataset Version Comparison

Quick methodology for comparing two versions of a training dataset (v5 vs v6, etc.) — used to audit what changed and whether an upgrade is worth retraining.

## When to Use

- User asks "what's different between vX and vY?"
- Deciding whether to retrain with a newer dataset version
- Auditing data quality regression between releases
- Checking if upload to HF succeeded correctly

## Step 1: Load both datasets

```python
import json

def load_jsonl(path):
    return [json.loads(l) for l in open(path).read().splitlines() if l.strip()]

v5 = load_jsonl("data/train.jsonl")     # Path varies by version — find with `find /tmp -name "train.jsonl" -path "*v5*"`
v6 = load_jsonl("data/train.jsonl")     # Path varies by version — find with `find /tmp -name "train.jsonl" -path "*v6*"`
```

## Step 2: Count key metrics

```python
tool_call_examples = sum(1 for ex in examples if any(
    m.get("tool_calls") for m in ex.get("messages", [])
))
filler = len(examples) - tool_call_examples
has_schemas = sum(1 for ex in examples if ex.get("tools"))
```

## Step 3: Schema comparison (set diff)

```python
def get_schemas(examples):
    schemas = set()
    for ex in examples:
        for t in ex.get("tools", []):
            schemas.add(t.get("function", {}).get("name", ""))
    return schemas

v5_s = get_schemas(v5)
v6_s = get_schemas(v6)

added = v6_s - v5_s
removed = v5_s - v6_s
common = v5_s & v6_s

print(f"v5: {len(v5_s)} schemas, v6: {len(v6_s)}")
print(f"Common: {len(common)}")
print(f"Added in v6: {sorted(added)}")
print(f"Removed from v5: {sorted(removed)}")
```

## Step 4: Categorize new schemas

Group added schemas by domain to show what the new version brings:

- **HF Hub tools** — start with `hf_` prefix
- **Growth Cycle** — assess_energy, log_transition, capture_lesson, close_cycle
- **Real agent tools** — terminal, write_file, web_search, delegate_task, cronjob, etc.
- **Other** — remaining

## Step 5: Density and quality metrics

| Metric | Formula | What it reveals |
|--------|---------|-----------------|
| Tool-calling ratio | tool_call_examples / total | How much signal per example. v5 was 54%, v6 should be 99%+ |
| Avg tool calls/ex | total_tool_calls / total | Density of multi-call patterns. Higher = richer |
| Parallel call sets | examples with ≥2 calls in one turn | Multi-tasking ability taught |
| Error patterns | examples with error-like content in tool responses | Recovery behavior taught |

## Step 6: Verify HF repo status

Check if the dataset exists on HF and whether it's public or private:

```bash
# Check HTTP status — 200 = public, 401 = private/requires auth, 404 = doesn't exist
curl -s -o /dev/null -w "%{http_code}" "https://huggingface.co/datasets/ORG/REPO_NAME"

# Get full metadata
curl -s "https://huggingface.co/api/datasets/ORG/REPO_NAME" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('id:', d.get('id'))
print('siblings:', len(d.get('siblings', [])))
print('private:', d.get('private'))
print('downloads:', d.get('downloads'))
"
```

Common status codes:
- **200 OK** — public repo, metadata loads
- **401 Unauthorized** — private repo (exists but needs auth token)
- **404 Not Found** — repo doesn't exist (different name or never uploaded)

## Step 7: Build comparison table

```markdown
| Metric | v5 | v6 (improved) | Δ |
|--------|----|----|---|
| Total examples | 659 | **789** | +130 |
| Tool-calling ratio | 54% | **100%** | +46pp |
| Unique schemas | 53 | **81** | +28 |
| Avg tool calls/ex | 0.92 | **1.41** | +0.49 |
| Error patterns | 44 | **55** | +11 |

> Numbers from the latest v6 improvement (Jul 12). Regenerate from live data when comparing newer versions.
```

## Pitfalls

- **Shell `&` in heredocs**: The `&` character in Python strings (e.g., `v5_s & v6_s`) causes shell errors in heredocs. Use `v5_s.__and__(v6_s)` or write to a `.py` file and execute it instead.
- **`content` may not be a string**: Tool messages may have `content` as a dict or None. Always guard: `isinstance(c, str)` before `.lower()` or `len()`.
- **Private repos return 401, not 404**: Don't conclude a dataset doesn't exist just from a non-200 code. Check if the repo name/org is correct.
- **v5 vs v6 can live on different paths**: The local copies may be under different directories. Use `find /tmp -name "train.jsonl" -path "*v5*"` etc. to locate them.
- **HF API may return null for private repos**: `cardData` and `siblings` are null when unauthenticated, even if the repo has files.
- **Dataset card `configs` YAML format**: Bare key-value pairs in `configs` cause HF to reject the README. Wrong: `- train: data/train.jsonl`. Correct: `- config_name: train\n  data_files: data/train.jsonl`.
- **Local paths drift between versions**: `/tmp/sakthai-v6-expanded` was the first upload; `/tmp/v6-improved` was the improved version. Always `find /tmp -name "train.jsonl" -path "*v6*"` to locate the actual working copy rather than assuming a stale path.
