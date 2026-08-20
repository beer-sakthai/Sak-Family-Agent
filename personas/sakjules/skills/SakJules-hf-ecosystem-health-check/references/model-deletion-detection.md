# Model Deletion Detection

## When to use

A delta check reports models disappeared from the API model list between the baseline and the current snapshot. This reference covers how to distinguish deletions from API artifacts (auth-gating, pagination glitches, caching).

## Detection workflow

### 1. Find the missing models

Compare `baseline["models"].keys()` against the current API response. Any baselined model not in the current set is a candidate.

### 2. Verify with HTTP status

```bash
curl -s -o /dev/null -w "%{http_code}" "https://huggingface.co/api/models/<author>/<model-name>"
```

| Code | Meaning | Action |
|------|---------|--------|
| **404** | Model deleted / never existed | Confirm with page title check |
| **401** | Model exists but auth-gated | NOT deleted — check if it's private or your token is stale |
| **200** | Model exists (API caching artifact) | Re-run list, likely pagination issue |
| **000 / timeout** | Network error | Retry |

### 3. Confirm with page title

A 404 can be confirmed by fetching the web page and checking the HTML title:

```bash
curl -s "https://huggingface.co/<author>/<model-name>" | grep -o '<title>[^<]*</title>'
```

- `"<title>404 – Hugging Face</title>"` → confirmed deleted
- Any other title (model name, description) → page exists, model data may be partitioned across API pages

### 4. Check all siblings

If one model is deleted, scan siblings for the same pattern. In our case both `sakthai-embedding` and `sakthai-context-0.5b-tools` were missing from the API and both returned 404.

### 5. Update baseline

After confirming deletion:

1. Remove the deleted model(s) from `hf_baseline.json` (`models` dict, decrement `model_count`, subtract their downloads from `model_downloads`)
2. Record the deletion in `LEARNING_JOURNAL.md` with model name, previous download count, and timestamp of detection
3. Note the cause if known (user action, HF cleanup, expiry). If unknown, flag as "cause unknown."

## Interpretation

**Why would a public model disappear?**
- **Creator deletion** — the owner deleted the repo from HF. This is the most common cause.
- **HF policy action** — models violating terms may be removed by HF. Unlikely for small personal repos.
- **Account change** — the model was moved to another account or made private.
- **API drift** — rare; the API may not return all repos on every query even with auth. Always confirm with a direct URL check (step 3) before concluding deletion.

If the model was visible for weeks then disappeared, and the creator has no record of deletion, it's worth re-checking via authenticated curl (with `Authorization: Bearer $TOKEN`) — some public models don't appear in unauthenticated `list_models` results.

## Example (from 2026-07-27)

```bash
# Two models vanished between baseline snapshots
# Check 1: API response
$ curl -s "https://huggingface.co/api/models?author=Nanthasit" | python3 -c "..."  # 12 models, baseline had 14

# Check 2: HTTP status
$ curl -s -o /dev/null -w "%{http_code}" "https://huggingface.co/Nanthasit/sakthai-embedding"
# → 404
$ curl -s -o /dev/null -w "%{http_code}" "https://huggingface.co/Nanthasit/sakthai-context-0.5b-tools"
# → 404

# Check 3: Page title confirmation
$ curl -s "https://huggingface.co/Nanthasit/sakthai-embedding" | grep -o '<title>[^<]*</title>'
# → <title>404 – Hugging Face</title>

# Conclusion: Both models deleted. Cause unknown.
# Result: Baseline updated from 14→12 models, -41 total downloads.
```
