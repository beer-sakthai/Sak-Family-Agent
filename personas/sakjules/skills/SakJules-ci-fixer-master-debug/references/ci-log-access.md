# CI Log Access Patterns

GitHub log access is tricky. Here are the working patterns for `beer-sakthai/Sak-Family-Agent`.

## API Token Extraction

`~/.git-credentials` stores tokens in format: `https://x-access-token:TOKEN@github.com`

Extract with Python:
```python
import re
with open('/root/.git-credentials') as f:
    for line in f:
        m = re.search(r'x-access-token:([^@]+)@github\.com', line)
        if m:
            token = m.group(1)
```

## Getting Failure Details

### Check runs API (most reliable)
Shows ALL checks including CI, gitleaks, SonarCloud:
```
GET /repos/beer-sakthai/Sak-Family-Agent/commits/{sha}/check-runs
```

Response includes `status` (completed/in_progress) and `conclusion` (success/failure) for each check. No auth needed for public repos.

### Workflow runs API
```
GET /repos/beer-sakthai/Sak-Family-Agent/actions/runs?per_page=5&status=completed
```

### Job logs (requires token with actions:read scope)
```
GET /repos/beer-sakthai/Sak-Family-Agent/actions/jobs/{job_id}/logs
```
This returns a redirect (302) to a signed URL. The token must have `actions:read` scope. The `x-access-token` format from `~/.git-credentials` may NOT have this scope — test with `curl -I` first.

### Commit status API (less reliable)
```
GET /repos/beer-sakthai/Sak-Family-Agent/commits/{sha}/status
```
Returns "pending" when checks are still running. Empty `statuses` array means no checks reported — use check-runs API instead.

## Common Failure: "pending" with no statuses

If the commit status shows "pending" with an empty statuses array:
1. Check the check-runs API for in_progress checks
2. If all are completed but status is still "pending", it's a stale reference
3. The check-runs API is the SOURCE OF TRUTH — commit/status is often stale

## Reading CI test output without token auth

The GitHub web UI (Actions tab) shows step output without auth. The API log download requires token auth which may fail. When API log access fails:
1. Use check-runs API to identify WHICH step failed
2. Use the step name to match against known failure patterns
3. Re-run the test locally to reproduce the failure
