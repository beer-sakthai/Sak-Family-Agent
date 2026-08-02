# GitHub Topics PATCH Quirk

> Verified 2026-07-30 with fine-grained PAT (`github_pat_...`).

## The quirk

`PATCH /repos/{owner}/{repo}` **silently ignores the `topics` field**. It returns HTTP 200 with a repo object whose `topics` is `[]` — no error, no warning. The description and homepage fields set in the same PATCH body are applied correctly; topics are silently dropped.

## The fix

Use the dedicated topics endpoint:

```
PUT /repos/{owner}/{repo}/topics
Accept: application/vnd.github.mercy-preview+json
```

### Two-step pattern (description + homepage + topics all set in one session)

**Step 1 — PATCH repo metadata:**
```bash
curl -s -X PATCH "https://api.github.com/repos/owner/repo" \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/json" \
  -d '{"description":"Six AI agent personas sharing one home...",
       "homepage":"https://huggingface.co/collections/..."}'
```

**Step 2 — PUT topics separately:**
```bash
curl -s -X PUT "https://api.github.com/repos/owner/repo/topics" \
  -H "Authorization: Bearer $GH_TOKEN" \
  -H "Accept: application/vnd.github.mercy-preview+json" \
  -H "Content-Type: application/json" \
  -d '{"names":["ai-agents","huggingface","open-source","llm"]}'
```

Or both in Python:
```python
import urllib.request, json

# Step 1
data = json.dumps({'description': '...', 'homepage': '...'}).encode('utf-8')
req = urllib.request.Request(f'https://api.github.com/repos/{owner}/{repo}',
    data=data, headers={'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github+json'}, method='PATCH')
urllib.request.urlopen(req)

# Step 2
data = json.dumps({'names': ['tag1', 'tag2']}).encode('utf-8')
req = urllib.request.Request(f'https://api.github.com/repos/{owner}/{repo}/topics',
    data=data, headers={'Authorization': f'Bearer {token}',
    'Accept': 'application/vnd.github.mercy-preview+json',
    'Content-Type': 'application/json'}, method='PUT')
urllib.request.urlopen(req)
```

## Why it happens

GitHub's REST API treats `topics` as a write-once field on the repo object. The `PATCH /repos/{owner}/{repo}` endpoint does accept `topics` in the schema but routes it to a different internal handler that doesn't persist the change. The topics-specific endpoint (`/topics` with `mercy-preview`) is the only one that actually commits topic changes.
