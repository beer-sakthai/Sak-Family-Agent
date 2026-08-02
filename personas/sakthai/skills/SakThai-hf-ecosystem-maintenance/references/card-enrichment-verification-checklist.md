# Model Card Enrichment — Verification Checklist

Generic 20-point checklist for verifying a model card enrichment pass. Checks proceed top-to-bottom through the card's structure.

## Pre-flight

| # | Check | How | Example |
|---|-------|-----|---------|
| 0 | Commit landed | `api.list_repo_commits()` or curl the commit URL | `curl -s "https://huggingface.co/api/models/author/repo" \| python3 -c "import json,sys; print(json.load(sys.stdin).get('cardData',{}).get('latest_commit',''))"` |
| 1 | YAML: irrelevance-supplement | grep `irrelevance-supplement` in the YAML frontmatter block | `content.split('---')[1]` if YAML present |
| 2 | YAML: model-index entries present | At least one `model-index:` → `results:` → `metrics:` chain | Check all 3 of `name`, `dataset.type`, `metrics[].value` |

## Tables: Variants / Selection / Pipeline

| # | Check | How | Example |
|---|-------|-----|---------|
| 3 | Variants: all counts match API | For each row with a download column, extract the number and compare | `grep -E '\| (0\.5B\|1\.5B\|7B) ' content` and verify count |
| 4 | Variants: no stale pre-update values | Old numbers should be absent | `'1,197' not in content`, `'994' not in content`, `'562' not in content` |
| 5 | Variants: self/card download is correct | The card's own count is usually the last row or bolded | `'382' in content` for a 382-dl card |
| 6 | Pipeline / Companion tables: model links resolve | Each URL in the table is a valid HF repo | Spot-check 2-3 links |

## Family / Sibling Model Table

| # | Check | How | Example |
|---|-------|-----|---------|
| 7 | All 11 public siblings present | Count rows in the family table | 11 rows = 11 public models (excluding profile card and deprecated placeholder) |
| 8 | 0.5B-Tools shows actual count (not lock) | `| 7 |` not `| 🔒 |` | `'| 7 |' in content` |
| 9 | No stale pre-update values | Old counts absent | Check all: `'1,197'`, `'994'`, `'562'`, `'351'`, `'185'`, `'143'`, `'34'`, `'45'`, `'33'` |
| 10 | No dead private-model link | If a private model row was removed, no orphaned URL | `'author/private-model' not in content` |
| 11 | Coder count matches API | `| 70 |` (not 34) | |
| 12 | Vision count matches API | `| 104 |` (not 45) | |
| 13 | TTS count matches API | `| 69 |` (not 33) | |
| 14 | Embedding-Multilingual count matches API | `| 188 |` (not 104) | |

## Low-Download Gems / Rising Stars Section

| # | Check | How | Example |
|---|-------|-----|---------|
| 15 | Section heading present | `'Low-Download Hidden Gems' in content` or `'Rising Stars' in content` |
| 16 | Promotes 0.5B-Tools | `'0.5B-Tools' in content` within the Gems section boundaries |
| 17 | Promotes irrelevance-supplement | `'irrelevance-supplement' in content` within the Gems section |

## Training Details & Narrative

| # | Check | How | Example |
|---|-------|-----|---------|
| 18 | Training links both datasets | `'sakthai-combined-v6' in content and 'irrelevance-supplement' in content` in the Training Details section |
| 19 | Footer / ecosystem counts correct | `'12 models'` or whatever the current functional count is | Verify from live API first |

## Structural Integrity

| # | Check | How | Example |
|---|-------|-----|---------|
| 20 | No lock emoji | `'🔒' not in content` | If present, a private-model row still exists |
| 21 | Card size increased | Newer card is larger after enrichment | `len(new) > len(old)` — enrichment adds content |
| 22 | No truncated tables | Each table has consistent column counts | Split on `\n`, for lines matching `|.*|.*|`, check same number of `|` per section |

## Structural Overhaul Verification (Reusable Script)

For **structural overhauls** (adding datasets table, spaces table, growing-ecosystem section, expanding grouped family rows) — the 22-point numeric checklist above isn't the right tool. Instead, run the reusable verification script:

```bash
python3 scripts/verify-card-structure.py <repo_id> --type model --counts "13 6 3"
```

The script checks for:
- Ecosystem count (models/datasets/Spaces) in card body
- Collection link present
- "Growing the ecosystem" section with low-download gems CTAs
- Sibling datasets table (combined-v6, combined-v7, irrelevance-supplement)
- All 13 sibling models individually listed (no grouped rows)
- v2 tool models present (0.5b-tools-v2, 1.5b-tools-v2)
- All 3 Spaces cross-linked (TTS, Leaderboard, Vision Demo)
- YAML frontmatter integrity (pipeline_tag, license, model-index)
- Dataset variant works with `--type dataset` flag

Exit code 0 = all checks pass. Output includes PASS/FAIL per check for easy debugging.

Example:
```bash
# After enriching a model card:
python3 scripts/verify-card-structure.py Nanthasit/sakthai-context-7b-merged
# After enriching a dataset card:
python3 scripts/verify-card-structure.py Nanthasit/sakthai-combined-v7 --type dataset
```

Use the `--counts` flag to override expected ecosystem size (run `hf-ecosystem-health-check` first to get live counts).

## Custom One-Off Verification

After any README enrichment, run custom checks against the **live** (post-commit) content:

```python
import urllib.request

url = "https://huggingface.co/author/repo/raw/main/README.md"
resp = urllib.request.urlopen(url)
content = resp.read().decode()

checks = {
    "irrelevance-supplement in YAML": 'irrelevance-supplement' in content,
    "Variants: 1,030": '1,030' in content,
    "No stale 1,197": '1,197' not in content,
    # ... adapt for the specific card
}
for name, ok in checks.items():
    print(f"  {'PASS' if ok else 'FAIL'}: {name}")
print(f"All pass: {all(checks.values())}")
```

Adapt the expected numbers to the card you enriched. The key principle: **check for presence of correct new values + absence of stale old values** for every table that was touched.
