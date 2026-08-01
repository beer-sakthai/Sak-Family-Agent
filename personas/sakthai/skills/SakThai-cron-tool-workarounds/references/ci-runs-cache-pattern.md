# CI Runs Cache (`ci_runs.json`) — Local CI Status Before Hitting GitHub API

## What It Is

`/opt/data/ci_runs.json` is a local snapshot of the GitHub Actions workflow runs endpoint. It stores the raw API response for `GET /repos/beer-sakthai/Sak-Family-Agent/actions/runs?per_page=50` (or similar), saved as JSON.

**Structure** (from the GitHub API response):

```json
{
  "total_count": 10182,
  "workflow_runs": [
    {
      "id": 30452569439,
      "name": "SonarCloud analysis",
      "head_branch": "main",
      "conclusion": "success",
      "status": "completed",
      "created_at": "2026-07-29T12:40:21Z",
      "updated_at": "2026-07-29T12:40:39Z",
      "run_number": 1114,
      "html_url": "https://github.com/beer-sakthai/Sak-Family-Agent/actions/runs/30452569439",
      "display_title": "Merge pull request #437 ..."
    }
  ]
}
```

Key fields per run: `name`, `conclusion` (`"success"`/`"failure"`/`null`), `status` (`"completed"`/`"in_progress"`), `display_title` (commit message), `created_at`.

## Why Use It

- **Zero API calls** — it's a local file. No rate-limit impact, no network latency.
- **Cron-safe** — reading JSON from disk doesn't trigger any tirith scanner.
- **Cheapest possible CI check** — ~5ms local read vs ~500ms GitHub API call.
- **Covers the full workflow surface** — all 10 workflow types (CI, Pylint, OSSAR, Secret Scan, SonarCloud, Stale, Labeler, Auto-Dependency-Update, Verify-Assets, Run-Evals).

## Pattern: Cache-First CI Check

```python
import json, time

CACHE_PATH = "/opt/data/ci_runs.json"
CACHE_MAX_AGE = 3600  # seconds — refresh API after 1h

def check_ci_from_cache():
    try:
        with open(CACHE_PATH) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return ("NO_CACHE", None)
    
    runs = data.get("workflow_runs", [])
    if not runs:
        return ("EMPTY_CACHE", None)
    
    latest = runs[0]
    age = time.time() - __import__('datetime').datetime.fromisoformat(
        latest["updated_at"].replace("Z", "+00:00")
    ).timestamp()
    
    if age > CACHE_MAX_AGE:
        return ("STALE", runs)  # callers should refresh
    
    # Check all recent runs for failures
    failures = [r for r in runs[:10] if r.get("conclusion") == "failure"]
    
    return ("FRESH", {
        "latest": latest["name"],
        "conclusion": latest["conclusion"],
        "updated_at": latest["updated_at"][:16],
        "total_runs": data.get("total_count", "?"),
        "failures": failures,
        "all_green": len(failures) == 0 and all(
            r.get("conclusion") == "success" 
            for r in runs[:10] 
            if r.get("status") == "completed"
        )
    })
```

## When to Hit the API vs When to Use Cache

| Situation | Use Cache | Use API |
|-----------|:---------:|:-------:|
| Quick check before full ecosystem report | ✅ | — |
| Checking if CI is still green (1-min polling) | ✅ | — |
| Delta check (was CI green last time? still green?) | ✅ | — |
| Detecting a NEW failure (need latest data) | — | ✅ |
| Cache is >1h old | — | ✅ |
| First run of the day | — | ✅ (then save to cache) |

## Writing to the Cache

When you do hit the GitHub API, save the response to `ci_runs.json` so the next cron tick reads from cache instead:

```bash
curl -s -H "Accept: application/vnd.github+json" \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "User-Agent: sakthai-cron/1.0" \
  "https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/actions/runs?per_page=10&status=completed" \
  -o /opt/data/ci_runs.json
```

For the token extraction method (since `gh` CLI is not installed), see the main `cron-tool-workarounds` skill's §4 (GitHub API) and `references/git-credentials-extraction.md`.

## Quick Terminal Check (bash)

```bash
python3 << 'PYEOF'
import json
try:
    with open('/opt/data/ci_runs.json') as f:
        d = json.load(f)
    runs = d.get('workflow_runs', [])
    if runs:
        r = runs[0]
        print(f"Latest: {r['name']} | conclusion: {r.get('conclusion','?')} | {r['updated_at'][:16]}")
        fails = [x for x in runs[:10] if x.get('conclusion') == 'failure']
        if fails:
            print(f"FAILURES: {len(fails)}")
            for f in fails:
                print(f"  {f['name']} | {f['display_title'][:60]}")
        else:
            print("All green (last 10 runs)")
    else:
        print("Empty cache")
except FileNotFoundError:
    print("No cache file — hit the GitHub API")
PYEOF
```

## Pitfalls

- **Cache can be stale.** The file might be from yesterday if no cron has hit the GH API recently. Check `updated_at` of the first run before relying on it.
- **Cache can be incomplete.** If only `per_page=5` was saved, you only see 5 runs. The `total_count` tells you total but not the content.
- **Cache doesn't auto-refresh.** It's only updated when a cron job explicitly writes to it. If multiple crons could update it, consider adding a timestamp marker so you don't overwrite with a stale snapshot.
- **The file path is `/opt/data/ci_runs.json`** — it's at workspace root, not in a subdirectory.
