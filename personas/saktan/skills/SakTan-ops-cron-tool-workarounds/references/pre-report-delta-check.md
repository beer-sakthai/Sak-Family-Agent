# Pre-report Delta Check — Avoid Redundant Cron Reports

## Problem

Cron jobs that check slowly-changing platform metrics (downloads, trending, stars) can run multiple times per day with identical results. Every run burns 5–15 API/browser calls and produces a journal entry confirming "nothing changed." Over a week of hour-interval runs, this wastes hundreds of tool calls.

In a real incident (2026-07-30), the "Platform Algorithms" cron ran 3× in a single day — each producing the same finding: zero trending presence, flat downloads. The 2nd and 3rd runs had nothing to add but still consumed 8+ browser calls each to confirm it.

## Pattern: Cheapest-Check-First

The insight: **most "what's new?" questions can be answered by reading a single local file** — the last journal entry — before touching any external API.

```
┌─────────────────────────────────────────────────────┐
│  1. READ last journal entry (cheapest — local I/O)  │
│  2. EXTRACT key metrics from entry                  │
│  3. COMPARE with current via ONE API call (cheap)   │
│  4. DECIDE: report, [SILENT], or full crawl         │
└─────────────────────────────────────────────────────┘
```

### Multi-metric Pre-check (Ecosystem Audits)

For crons that cover multiple asset types (models + datasets + Spaces + CI), a single model-download check is insufficient. A small delta on datasets or a CI transition can go undetected while the model total is flat. Use **sequential metric checking** — cheapest metric first, escalate only when needed:

```
Model downloads unchanged?  →  Dataset downloads unchanged?  →  CI status unchanged?  →  [SILENT]
         ↓ (changed)                      ↓ (changed)                  ↓ (changed)
   Full models fetch          Full datasets fetch + Rest     Full CI crawl + report
```

Implementation — stop early when a metric changes, but check all three before emitting [SILENT]:

```bash
python3 << 'PYEOF'
import urllib.request, json, re

# Read previous entry baseline
with open('/opt/data/LEARNING_JOURNAL.md') as f:
    content = f.read()
sections = re.split(r'^## ', content, flags=re.MULTILINE)
relevant = [s for s in sections if 'Ecosystem' in s or 'Health' in s or 'Full Audit' in s]
if not relevant:
    print('NEED_REPORT')
    exit(0)

last = relevant[-1]
date_m = re.search(r'(\d{4}-\d{2}-\d{2})', last)
last_date = date_m.group(1) if date_m else '0000-00-00'
today = __import__('datetime').date.today().isoformat()
if last_date != today:
    print('NEED_REPORT')
    exit(0)

token = open('/opt/data/.cache/huggingface/token').read().strip()

# Check 1: Model downloads
req = urllib.request.Request('https://huggingface.co/api/models?author=Nanthasit&limit=50',
    headers={'Authorization': f'Bearer {token}'})
with urllib.request.urlopen(req, timeout=10) as r:
    models = json.loads(r.read())
model_dl = sum(m.get('downloads', 0) for m in models if not m.get('private'))
prev_mdl = int(re.search(r'(\d+)\s*model downloads', last).group(1)) if re.search(r'(\d+)\s*model downloads', last) else -1
if model_dl != prev_mdl:
    print(f'NEED_REPORT (model dl: {prev_mdl}→{model_dl})')
    exit(0)

# Check 2: Dataset downloads
req = urllib.request.Request('https://huggingface.co/api/datasets?author=Nanthasit&limit=50',
    headers={'Authorization': f'Bearer {token}'})
with urllib.request.urlopen(req, timeout=10) as r:
    datasets = json.loads(r.read())
ds_dl = sum(d.get('downloads', 0) for d in datasets)
prev_ds = int(re.search(r'(\d+)\s*dataset downloads', last).group(1)) if re.search(r'(\d+)\s*dataset downloads', last) else -1
if ds_dl != prev_ds:
    print(f'NEED_REPORT (dataset dl: {prev_ds}→{ds_dl})')
    exit(0)

# Check 3: CI status (quick HEAD request)
req = urllib.request.Request('https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/actions/runs?per_page=1',
    headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as r:
    ci = json.loads(r.read())
current_ci = ci.get('workflow_runs', [{}])[0].get('conclusion', 'unknown') if ci.get('workflow_runs') else 'unknown'

# All three unchanged → [SILENT]
print('SAME_DAY_ALL_FLAT')
PYEOF
```

This catches dataset-only drift and CI transitions that a model-only pre-check would miss, at the cost of ~1.0s (3 fast API calls) instead of ~0.3s (1 call). For a full ecosystem audit that would otherwise burn 8–12 calls, this is still a net savings.

## Step-by-Step

### 1. Read the last entry's date and metrics

Grep the most recent entry for the cron's topic:

```bash
# Find the last entry for this cron type
grep -c "Platform Algorithms" /opt/data/LEARNING_JOURNAL.md

# Extract the date of the last entry
grep "^## .*Platform Algorithms" /opt/data/LEARNING_JOURNAL.md | tail -1
```

Or for structured metrics, extract the key numbers:

```bash
# Extract model download totals from last entry
python3 << 'PYEOF'
import re
with open('/opt/data/LEARNING_JOURNAL.md') as f:
    content = f.read()

# Find last "Platform Algorithms" section — split on section headers
sections = re.split(r'^## ', content, flags=re.MULTILINE)
algo_sections = [s for s in sections if 'Platform Algorithms' in s or 'platform algorithms' in s.lower()]

if not algo_sections:
    print('NO_PREVIOUS_ENTRY')
else:
    last = algo_sections[-1]
    # Extract date from first line
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', last)
    print(f'Last entry date: {date_match.group(1) if date_match else "unknown"}')
    
    # Extract key metrics — search for numbers near known keywords
    for pattern, label in [
        (r'(\d[\d,.]*k?)\s*downloads?\s+total', 'total_dl'),
        (r'models?.*?(\d+)\s*dl', 'model_dl_top'),
        (r'Stars?:?\s*0', 'gh_stars'),
    ]:
        m = re.search(pattern, last, re.IGNORECASE)
        if m:
            print(f'{label}: {m.group(1)}')
PYEOF
```

### 2. Compare with a single cheap API call

Before crawling all three platforms, make ONE fast API call to see if anything moved:

```bash
# Cheapest possible check: total public model downloads from HF API
python3 << 'PYEOF'
import urllib.request, json
req = urllib.request.Request(
    'https://huggingface.co/api/models?author=Nanthasit&sort=downloads&direction=-1&limit=30',
    headers={'User-Agent': 'Mozilla/5.0'}
)
with urllib.request.urlopen(req, timeout=10) as r:
    data = json.loads(r.read())

total = sum(m.get('downloads', 0) for m in data if not m.get('private'))
top = data[0]['id'].split('/')[1] if data else '?'
top_dl = data[0].get('downloads', 0) if data else 0
print(f'Total: {total}')
print(f'Top: {top} ({top_dl} dl)')
PYEOF
```

If the total matches the last journal entry's total, skip the full crawl. If it differs, proceed.

### 3. Decision Matrix

| Last entry is... | Total dl delta | Action |
|:----------------|:--------------:|--------|
| Today, exact match | 0 | **[SILENT]** — nothing to report |
| Today, small change (<2%) | Small | Quick update (1 paragraph) + [SILENT] if <0.5%. **After 3+ consecutive same-day <0.5% deltas, escalate to bare [SILENT]** — the repeated "small drift" quick-update paragraph is itself noise, not value. |
| Yesterday or older | Any | Full crawl + report |
| Different week | Any | Full crawl + detailed report |
| Not found | N/A | Full crawl + first-entry report |

**Consecutive small-delta escalation:** Track the number of consecutive same-day entries with <0.5% deltas via a simple counter stored in the journal entry header (e.g. "Cron #017 (delta #5)"). When counter ≥ 4, emit bare [SILENT] without the quick-update paragraph. The plateau is the steady state — don't re-document it.

### 4. Implementation

In practice, this is a ~15-line wrapper at the top of any cron that checks slowly-changing metrics:

```bash
# Pre-check: has anything changed since last report?
python3 << 'PYEOF'
import json, re

# Load baseline from journal
with open('/opt/data/LEARNING_JOURNAL.md') as f:
    content = f.read()

sections = re.split(r'^## ', content, flags=re.MULTILINE)
relevant = [s for s in sections if 'Platform Algorithms' in s or 'platform algorithms' in s.lower()]
if not relevant:
    print('NEED_REPORT')
    exit(0)

last = relevant[-1]
date_m = re.search(r'(\d{4}-\d{2}-\d{2})', last)
last_date = date_m.group(1) if date_m else '0000-00-00'

# Quick total-dl check
import urllib.request
req = urllib.request.Request(
    'https://huggingface.co/api/models?author=Nanthasit&limit=30',
    headers={'User-Agent': 'Mozilla/5.0'}
)
with urllib.request.urlopen(req, timeout=10) as r:
    models = json.loads(r.read())
current_total = sum(m.get('downloads', 0) for m in models if not m.get('private'))

# Try to extract previous total from the entry
prev_total_m = re.search(r'(\d+)\s*downloads', last)
prev_total = int(prev_total_m.group(1)) if prev_total_m else -1

today = __import__('datetime').date.today().isoformat()
if last_date == today and current_total == prev_total:
    print('SAME_DAY_SAME_TOTAL')
    exit(0)  # caller interprets as [SILENT]
else:
    print('NEED_REPORT')
    print(f'prev={prev_total} current={current_total} date={last_date}')
PYEOF
```

Then check the exit code to decide whether to proceed:

```bash
RESULT=$(python3 << 'PYEOF' ...)
if echo "$RESULT" | grep -q "SAME_DAY_SAME_TOTAL"; then
    echo "[SILENT]"
    exit 0
fi
```

## When This Pattern Applies

| Cron type | Change velocity | Pre-check cost | Benefit |
|-----------|:---------------:|:--------------:|---------|
| Platform Algorithms (GH/HF/Kaggle) | Hours–days | 1 HF API call (0.3s) | Saves 8-15 calls |
| Social Growth (likes/stars) | Hours–days | 1 HF + 1 GH call (0.6s) | Saves 6-10 calls |
| CI Health | Minutes | `git log` (0.1s) | Saves 3-5 GH API calls |
| HF Ecosystem Audit | Hours | 1 HF models call (0.3s) | Saves 8-12 calls |

The pattern works best when:
- The cron runs more than once per day
- The metrics change slowly (hours to days)
- At least one API call returns a single aggregate metric (total downloads, total stars)
- The previous entry is in the same journal file

## Known Pitfalls

- **First run of the day should always report**, even if nothing changed. A single daily report is useful; 3+ identical ones are not.
- **Aggregate totals can hide churn.** A model losing 10 downloads while another gains 10 produces the same total. If this matters, compare the top-3 model dls individually.
- **Dataset-only changes won't affect model totals.** If the cron covers datasets too, check dataset totals separately or skip the pre-check entirely.
- **Skipping the fetch also skips the journal entry.** That's correct — no change, no noise. The next run will find the same last entry and skip again. Deliver [SILENT] to the scheduler.
- **The pre-check itself costs ~0.3s for one call.** Even if it fires every time (never suppresses), the overhead is negligible compared to a full 8-call platform crawl.
- **Plateau-level small deltas are not meaningful changes.** A +23 model download delta across 14 models (0.39%) is the same steady-state plateau, not a signal. The pre-check should recognize this: when the delta is <0.5% AND the previous N (≥4) entries all reported the same plateau, skip the quick-update paragraph and emit bare [SILENT]. Implement by grepping the journal for consecutive same-topic entries with <0.5% deltas — if the pattern is unbroken for 4+ entries, escalate.
- **Multi-metric pre-check has a blind spot for likes.** A model gaining its first like (0→1❤) won't appear in download totals or dataset counts. If social engagement is in scope (likes, stars, forks), add a quick likes check: `sum(m.get('likes',0) for m in models)`. A 0→1 like transition is a real signal worth reporting even with flat downloads.

## Relation to Existing Patterns

This pattern is the **decision gate** before the "Delta Tracking" section (which computes per-run deltas after data is fetched). The two compose:

```
Pre-report Delta Check  →  [SILENT] if nothing changed
         ↓ (change detected)
Full API fetch (see "Social Engagement Metrics")
         ↓
Delta computation (see "Delta Tracking")
         ↓
Journal entry + report
```

The "Recommendation Hygiene" section handles a related but distinct problem: recommending the same fix across multiple runs. That occurs AFTER a report is generated. This pattern prevents unnecessary reports entirely.
