# HF Download Tracker — cron snapshot pattern

Reusable pattern for tracking download/like counts across all of a user's
Hugging Face repos (models + datasets). Designed for cron-mode execution.

> **Ready-to-run:** `scripts/hf-download-tracker.py` — the verified standalone
> implementation (self-fetching `urllib`, dedupes models/datasets by ID,
> prints `SILENT` on no change, saves snapshot). Copy it, change `AUTHOR`,
> drop into the profile's cron dir. Verified 2026-07-31 (idempotent run →
> SILENT; perturbation → +1 GAIN detected; snapshot restore intact).

> **Install state (2026-07-31):** the script IS now installed at
> `~/profiles/sakthai/cron/hf-download-tracker.py` (copied verbatim from the
> skill copy). To run: `python3 ~/profiles/sakthai/cron/hf-download-tracker.py`
> — no retrieve/write step needed. If it's missing (fresh machine/profile),
> re-install: `skill_view(name='cron-tool-workarounds',
> file_path='scripts/hf-download-tracker.py')` to retrieve the source, then
> `write_file` it to the cron dir and execute. Do not hand-type the logic — it
> is long and the skill copy is the verified one.
>
> **Verified run (2026-07-31):** installed script ran end-to-end → `SILENT`
> (no changes); post-save live-coverage check (section 5) → `PASS: 30 repos,
> 6746 downloads, 30/30 live-verified`; ad-hoc verification → py_compile ok,
> perturbation test correctly detected `+1 GAIN`, real snapshot untouched.
> Snapshot universe is 30 repos (dedupe of the repo that appears in both
> endpoints: 17 models + 13 datasets → 30).

## Pattern overview

```
curl HF API for all models by author  ─┐
curl HF API for all datasets by author ─┤
                                         ├──→ compare with saved snapshot JSON
write new snapshot                      ─┘
                                         └──→ report deltas or [SILENT]
```

## Step-by-step

### 1. Fetch current stats

Use `curl` (not `execute_code` — blocked in cron mode). Two calls, independent,
so fire them in parallel:

```bash
curl -s 'https://huggingface.co/api/models?author=USERNAME'
curl -s 'https://huggingface.co/api/datasets?author=USERNAME'
```

Each returns a JSON array. Models carry `"downloads"` and `"likes"` fields.
Datasets carry `"downloads"`.

### 2. Read previous snapshot

```bash
cat ~/profiles/<profile>/cron/hf-download-snapshot.json
```

Snapshot format:
```json
{
  "Nanthasit/sakthai-context-1.5b-merged": {
    "downloads": 1599,
    "likes": 0,
    "type": "model"
  },
  "Nanthasit/sakthai-combined-v6": {
    "downloads": 246,
    "likes": 0,
    "type": "dataset"
  }
}
```

### 3. Compare (inline Python)

Write a comparison script to the working directory with `write_file`, or use
a python3 heredoc if you want zero files on disk. Example comparison logic:

```python
old = json.load(open("snapshot.json"))
new = {}  # built from API responses

# New assets
added = set(new) - set(old)

# Download/like changes
for rid in set(old) & set(new):
    dl_diff = new[rid]["downloads"] - old[rid]["downloads"]
    like_diff = new[rid]["likes"] - old[rid]["likes"]
    # report >0 as gainers, <0 as losers
```

### 4. Save new snapshot

Write to `~/profiles/<profile>/cron/hf-download-snapshot.json`.

### 5. Report or stay silent

If no changes across all repos → reply `[SILENT]` (suppresses delivery).
If changes exist → summarize gainers, losers, new/removed assets.

## 5. Post-save verification

Snapshot saved. Now verify integrity against the live API — without `execute_code`
(blocked in cron mode) and without `/tmp/` files (also blocked).

Inline `python3 -c` with `urllib.request` does both checks in one shot:

```python
python3 -c "
import json, os, urllib.request

# Read saved snapshot
data = json.load(open('SNAPSHOT_PATH'))

# Fetch live API — models and datasets
api_all = set()
for url, name in [
    ('https://huggingface.co/api/models?author=USERNAME', 'models'),
    ('https://huggingface.co/api/datasets?author=USERNAME', 'datasets'),
]:
    with urllib.request.urlopen(url, timeout=10) as r:
        for item in json.loads(r.read()):
            api_all.add(item['id'])

# Schema check
errors = []
for name, info in data.items():
    if info.get('type') not in ('model', 'dataset'):
        errors.append(f'{name}: invalid type')
    if not isinstance(info.get('downloads'), int):
        errors.append(f'{name}: downloads not int')

# Coverage check — every snapshot entry is a real HF repo
snap_keys = set(data.keys())
missing = api_all - snap_keys
extra = snap_keys - api_all
if missing:
    errors.append(f'Missing from snapshot: {sorted(missing)}')
if extra:
    errors.append(f'Extra in snapshot (removed?): {sorted(extra)}')

if errors:
    for e in errors:
        print(f'FAIL: {e}')
    exit(1)
else:
    total = sum(v['downloads'] for v in data.values())
    matched = sum(1 for k in snap_keys if k in api_all)
    print(f'PASS: {len(data)} repos, {total} downloads, {matched}/{len(data)} live-verified')
"
```

Substitute `SNAPSHOT_PATH` and `USERNAME` before running.

## What to track

| Field | Source | Notes |
|-------|--------|-------|
| `downloads` | models & datasets API | Primary metric — proxy for adoption |
| `likes` | models API only | Proxy for community appreciation |
| `trendingScore` | models API | Can indicate organic discovery |
| `pipeline_tag` | models API | Useful for categorising changes |

## Pitfalls

- A repo can exist as BOTH a model and a dataset (`sakthai-coder-browser` is
  an example). Store it as a model (primary type) with `"also_dataset": true`
  rather than duplicating entries.
- The API doesn't dedupe `sakthai-coder-browser` across endpoints — you must
  handle the collision manually. Symptom: live fetch reports 19 models + 11
  datasets but the union is only 29 repos because one ID appears in both
  lists. **Never assert `len(models) + len(datasets)` — build a dict keyed by
  repo ID so dedupe is automatic.**
- HF API rate-limits: generous but avoid hammering. One call per endpoint per
  run is fine.
- The snapshot file is small (~3KB for 30 assets). No pagination needed.
- New models/datasets with 0 downloads are still worth reporting — they tell
  the user their publishing pipeline worked.

## Verifying the tracker (perturbation test)

To prove a no-change cron tracker actually detects changes, perturb the
snapshot and re-run — then restore. Direction matters:

- **Decrement a snapshot download count by 1** → tracker must report a **+1
  GAIN** (previous was lower than live).
- **Increment a snapshot download count by 1** → tracker must report a **-1
  LOSS** (previous was higher than live).

First-timers often assert the wrong direction (bumped the *previous* value up
and expected a gain). Wrap the perturbation in try/finally to restore the real
snapshot, and assert the snapshot file matches the live API universe after
restore. Verified 2026-07-31 on `scripts/hf-download-tracker.py`.
