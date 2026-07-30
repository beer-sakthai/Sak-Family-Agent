# Baseline Cache & Delta Detection Pattern

**Problem:** Every cron cycle re-scans all HF assets (25+ API calls) even when nothing changed. This wastes API budget, adds latency, and bloats journal entries with identical data.

**Solution:** Maintain a baseline cache file and compare against it on each run. Only report deltas.

## Implementation

The `hf_delta_check.py` script at `~/.hermes/profiles/sakthai/scripts/hf_delta_check.py` implements this pattern. **Single-run API — no subcommands:**

```bash
# Run delta check (only command needed)
python3 ~/.hermes/profiles/sakthai/scripts/hf_delta_check.py
```

| Exit code | stdout  | Meaning |
|-----------|---------|---------|
| 0         | `UNCHANGED` | No deltas — emit `[SILENT]` |
| 1         | `CHANGED: {structured JSON diff}` | Deltas found — proceed with report |

**No separate snapshot/delta/check subcommands.** The script is idempotent: on every run it compares current API state against the cached baseline. If UNCHANGED, it self-refreshes the full snapshot data (models, datasets, spaces, counts, totals) so the baseline always reflects the latest state without manual intervention. If CHANGED, it outputs a structured JSON diff with per-model download deltas, per-dataset deltas, and space/collection changes — then exits 1.

**Updated 2026-07-27:** Rebuilt from aggregate-only to per-asset tracking. The v1 script only checked total download sums (`model_downloads: 2897 → ...`). The v2 script tracks individual model deltas (`Nanthasit/sakthai-embedding: dl=34 (+6)`), per-dataset deltas, and space changes. This catches changes that were invisible before (e.g., the embedding model gaining +6 while the total stayed flat).

**Updated 2026-07-30 (baseline refresh bug fix):** Discovered that the v2 script only refreshed `baseline_timestamp` on each check, not the actual per-asset snapshot data. This created a subtle staleness: the first real change was detected correctly, but the baseline never absorbed it — every subsequent run compared against the original stale baseline and reported "CHANGED" forever with identical diffs. Fixed by adding a full-snapshot refresh loop in `main()` that copies all asset keys from `current` into `baseline` on every check. Detection: run twice in quick succession — if both return CHANGED with the same diff, the baseline is stale.

**To update the baseline to current state** (after verifying changes are real and the baseline is stale): fetch fresh API data and write a new baseline JSON. There is no dedicated "snapshot" subcommand — use Python one-liners:

```python
# Fetch fresh snapshot and write to baseline
import json, os, urllib.request
TOKEN = open(os.expanduser("~/.cache/huggingface/token")).read().strip()
req = urllib.request.Request("https://huggingface.co/api/models?author=Nanthasit&limit=50",
    headers={"Authorization": f"Bearer {TOKEN}"})
models = json.loads(urllib.request.urlopen(req, timeout=15).read().decode())
baseline = {"models": {m["id"]: {"downloads": m.get("downloads",0)} for m in models if m.get("id")},
            "model_count": len(models), "model_downloads": sum(m.get("downloads",0) for m in models)}
with open(os.expanduser("~/.hermes/profiles/sakthai/cache/hf_baseline.json"), "w") as f:
    json.dump(baseline, f, indent=2)
```

Cache stored at: `~/.hermes/profiles/sakthai/cache/hf_baseline.json`

Copies exist at:
- `~/.hermes/profiles/sakthai/cache/hf_baseline.json` (hermes profile path)
- `/opt/data/profiles/sakthai/cache/hf_baseline.json` (fallback)

Both copies are kept in sync.

## Delta Types Detected

| Change | Example Output |
|--------|---------------|
| New model | `"models_changed": {"Nanthasit/sakthai-new": "NEW (34 dl, 0 likes)"}` |
| Removed model | `"models_changed": {"Nanthasit/sakthai-old": "REMOVED"}` |
| Downloads changed | `"models_changed": {"Nanthasit/sakthai-context-1.5b-merged": "dl=1197 (+255)"}` |
| Likes changed | `"models_changed": {"Nanthasit/sakthai-model": "dl=34 (+6) | likes=1 (+1)"}` |
| Count changed | `"model_count": "12 → 14"` |
| Dataset change | `"dataset_downloads": "245 → 250 (+5)"` |
| Space change | `"space_count": "2 → 3"` |

## Workflow Integration

For cron jobs running every 10-30min:

1. Call `hf_delta_check.py` first (no args). This is now wired into the SKILL.md Step 0.
2. If exit 0 (no changes): emit `[SILENT]` — no report needed, do NOT make any API calls
3. If exit 1 (changes found): the script already output the structured diff. Proceed with a focused delta-only report. The JSON output can be parsed by downstream scripts.
4. If exit 1 but diff is noise (API variance, not real changes): run the baseline-update one-liner above.

This saves ~85% of API calls on typical days with zero organic movement.

## Verification

```bash
# Should exit 0 with "UNCHANGED" if baseline matches current API state
python3 ~/.hermes/profiles/sakthai/scripts/hf_delta_check.py
echo "EXIT: $?"  # Should be 0
```

## Meta-Lesson: Talking About the Fix vs. Building It

This script was the **second** time the delta-cache approach was mentioned in LEARNING_JOURNAL.md. The first entry (2026-07-27) described the problem and proposed the fix in detail — but never built it. The second entry (also 2026-07-27) built it.

**Pattern:** Journal entries can create the illusion of progress. A described fix is not a fixed problem. The actual work (writing the script, creating the cache dir, taking the first snapshot) happened 370 lines and 2 journal entries after the problem was first documented.

**Rule:** Every improvement entry in LEARNING_JOURNAL.md must reference a committed artifact (script, config change, tool update) — not just an intention. If the fix hasn't been built, the entry belongs in a "proposed" section, not "improvements made."

**Recursive check:** This pattern itself was identified and documented in the v1 reference file, but the v1 delta-check script still had an issue: it only tracked aggregate totals (missing per-model changes). The pattern of "documented but incomplete" applied to the fix for the fix. Closing the loop required rebuilding the script (v2) to actually detect the changes it claimed to detect. The lesson recurses: a documented improvement must be verified to actually produce the outcome described. A reference file saying "we catch per-model changes" when the script only checks sums is the same class of fix-illusion.
