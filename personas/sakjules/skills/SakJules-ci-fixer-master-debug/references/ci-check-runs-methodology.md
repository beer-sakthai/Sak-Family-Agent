# CI Status — Proper Check Methodology

## The trap

Querying only `actions/runs?status=completed` misses in-progress runs. A commit that shows "pending" status is NOT necessarily broken — workflows may still be running.

## Wrong way (guessed this session)

```
# Only checked completed runs — missed that CI was still running
curl "...actions/runs?status=completed&per_page=5"
# → ALL GREEN (false — didn't see the in-progress CI runs)
```

## Correct way

1. First, check the **check-runs API** (not commit status, not actions/runs):

```
GET /repos/{owner}/{repo}/commits/{sha}/check-runs
```

This returns ALL checks with their current `status` and `conclusion`, including running ones.

2. Separate by status:

```
in_progress  → still running, normal
completed/success → green
completed/failure → red — diagnose
```

3. Only if ALL are completed AND all are success, report ALL GREEN.

## Why "pending" means nothing by itself

The commit status API (`/commits/{sha}/status`) returns `pending` when ANY check hasn't reported yet. It's a summary field, not a diagnostic. To diagnose, you need the raw check list.

## Quick check command

```bash
curl -sL "https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/commits/{SHA}/check-runs" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
for c in d.get('check_runs', []):
    icon = '🟢' if c.get('conclusion') == 'success' else '🔴' if c.get('conclusion') == 'failure' else '⏳'
    print(f'{icon} {c[\"name\"]:30s} {c[\"status\"]:12s} {c.get(\"conclusion\",\"-\")}')
"
```

## Lesson learned (2026-07-25)

Beer said: **"If I said it not check, dont guess"** — when he says "check CI", don't assume the state from partial data. Actually query the right API, read the raw list, and report only what the raw output confirms. "Pending" does NOT mean "failing" or "okay" — it means "incomplete". Go deeper.
