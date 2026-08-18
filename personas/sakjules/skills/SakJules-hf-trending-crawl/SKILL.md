---
name: SakJules-SakThai-hf-trending-crawl
description: 'Scheduled crawl of HF Hub trending models: fetch, select uncovered model, deep-dive,
  report, update tracker, sync to GitHub.'
---

# HF Trending Model Crawl

Recurring cron workflow: poll HF Hub's trending API, pick an uncovered model, research it, update tracker, and sync to the skills repo.

## Trigger

Scheduled cron job (`ticker_heartbeat` tracks last-run timestamp). Run each tick when:
- The job file at `~/profiles/sakthai/cron/jobs.json` has an active entry with `script` pointing to this workflow.
- Ticker state files at `~/profiles/sakthai/cron/ticker_*` indicate readiness.

## Step-by-step

### 1. Read tracker
```bash
cat ~/profiles/sakthai/cron/hf-trending-covered.json
```
The tracker is a JSON list of model IDs already covered.

### 2. Fetch trending models
Use Python with an HF token for authenticated access (avoids 401s on gated repos and returns richer data):

```python
import os, urllib.request, json
token = os.environ.get('HF_TOKEN', '')
headers = {'User-Agent': 'Mozilla/5.0'}
if token:
    headers['Authorization'] = f'Bearer {token}'

req = urllib.request.Request('https://huggingface.co/api/trending', headers=headers)
with urllib.request.urlopen(req, timeout=15) as r:
    data = json.loads(r.read())
trending = data['recentlyTrending']  # list of {repoData: {...}}
```

**Response structure:** `recentlyTrending[i].repoData.id` gives the item ID.

**Repo type detection — the `repoData` dict has different keys depending on type:**

| Type | Detecting keys | Description |
|------|---------------|-------------|
| Model | `safetensors`, `pipeline_tag`, `numParameters` | Has weight files — the target |
| Dataset | `datasetsServerInfo`, `isBenchmark`, `isTraces` | No weights, skip |
| Space | `runtime`, `title`, `emoji`, `sdk`, `shortDescription` | Gradio/Streamlit app, skip |

Check for these keys before fetching full model info to avoid wasted API calls:

```python
def is_weight_model(repo):
    return 'safetensors' in repo or 'numParameters' in repo and repo.get('numParameters', 0) > 0

def is_space(repo):
    return 'runtime' in repo or 'title' in repo

def is_dataset(repo):
    return 'datasetsServerInfo' in repo or repo.get('isBenchmark') or repo.get('isTraces')
```

Other useful fields: `downloads`, `likes`, `gated`, `lastModified`.

### 3. Pick one uncovered model
Pre-filter by repo type using the key-detection helpers from Step 2 — only keep weight models. Then intersect against the tracker list.

Skip:
- Items whose `repoData` lacks `safetensors` / `numParameters` (Spaces, datasets, traces)
- Models already in tracker
- Gated models
- Items whose `/api/models/{id}` 404s (non-canonical IDs that don't resolve)
- Items that canonicalize to an already-covered model ID (e.g. `openbmb/UltraX-Preview` → `openbmb/UltraX-0.6B-Preview`)

**⚠ All-covered handling**: If after filtering no uncovered weight model remains, output exactly `[SILENT]` (nothing else) and **stop** — do not proceed to steps 4–6. This is the correct response when the trending feed has no new weight models.

### 4. Deep dive

Two approaches — use whichever fits the available tooling.

#### 4a. Via HF API (raw HTTP)
```python
import urllib.request, json

# Model info
req = urllib.request.Request(f'https://huggingface.co/api/models/{model_id}',
    headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15) as r:
    info = json.loads(r.read())

# Card data (YAML frontmatter parsed to JSON)
card = info.get('cardData', {})

# README
req = urllib.request.Request(f'https://huggingface.co/{model_id}/raw/main/README.md',
    headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=15) as r:
    readme = r.read().decode('utf-8')
```

**Gotchas:**
- Gated models raise `HTTP 401` on both info and README — wrap in try/except.
- `numParameters` may be missing for LoRAs, datasets, or non-weight repos.
- `safetensors` field structure varies — check keys before accessing.
- Some trending IDs don't match canonical IDs — if `/api/models/{id}` 404s, drop it.
- **Composio unavailable fallback** — `references/hf-api-fallbacks.md` documents `curl` + `read_file` patterns when EXA_SEARCH is blocked (Enhanced Controls, 4300). Never pipe `curl` to `python3` (tirith blocks it); save to file first. Use HF Models/Spaces APIs directly:
  ```bash
  curl -s "https://huggingface.co/api/models?search=<term>&sort=downloads&direction=-1&limit=20" -o /tmp/models.json
  curl -s "https://huggingface.co/api/spaces?search=<term>&sort=likes&direction=-1&limit=10" -o /tmp/spaces.json
  ```
  Read via `read_file` tool — no pipe needed.

#### 4b. Via EXA_SEARCH / Composio (for HF doc/skill research)

When researching HF documentation (not a specific model's README) or when building a new skill about an HF topic, use `EXA_SEARCH` through `COMPOSIO_MULTI_EXECUTE_TOOL`:

```json
{
  "tool_slug": "EXA_SEARCH",
  "arguments": {
    "query": "Hugging Face <topic> documentation feature 2026",
    "includeDomains": ["huggingface.co"],
    "numResults": 10,
    "contents": { "text": { "maxCharacters": 5000, "verbosity": "compact" } },
    "type": "auto"
  }
}
```

**Why this is better than raw HTTP for research:**
- Searches across ALL HF docs (hub, huggingface_hub, API, etc.) simultaneously
- Returns semantic content — no need to parse HTML or guess which page to fetch
- `includeDomains: ["huggingface.co"]` scopes results to official HF docs
- Works for topics, features, APIs, best practices — anything documented on the Hub

**Processing results:** The `response.data.results[]` array contains `text` (extracted page content), `title`, `url`. Extract key facts from the text and build your skill content. No need to fetch each URL separately — EXA returns the text inline.

#### 4c. Report content

Write 2–3 paragraphs covering: architecture, use case, specifications, benchmarks (from README and card data). Include key numbers (param count, license, downloads, likes). For skill-building sessions, deliver the full skill content as the report body instead of generic paragraphs.

### 5. Update tracker
Append the new model ID to the JSON list:
```python
import json
with open('~/profiles/sakthai/cron/hf-trending-covered.json', 'r') as f:
    covered = json.load(f)
covered.append(new_model_id)
with open('~/profiles/sakthai/cron/hf-trending-covered.json', 'w') as f:
    json.dump(covered, f, indent=2)
```

### 6. Sync to GitHub
```bash
# Copy profile skills into the skills repo
cp -a ~/profiles/sakthai/skills/. /opt/data/sakthai-skills-repo/
cp -a ~/profiles/sakthai/cron/. /opt/data/sakthai-skills-repo/cron/

cd /opt/data/sakthai-skills-repo
git add -A
git commit -m "trending: <model-id>"
git push origin main
```

**Gotchas:**
- `git commit` may say "nothing to commit" if the files are already in HEAD from a previous cycle — this is fine, `git push` will say "Everything up-to-date".
- `git push` may fail if the local branch has diverged — run `git pull --rebase` first.
- Only push if there's actually a new commit (check `git status --short` first for efficiency).

## Pitfalls

| Pitfall | Symptom | Mitigation |
|---------|---------|------------|
| `sort=trending` on `/api/models` | 400 Bad Request | Use `/api/trending` endpoint instead — they are different |
| UltraX-Preview vs UltraX-0.6B-Preview | Trending API returns different ID than canonical | Cross-check by fetching `/api/models/{trending_id}` |
| Gated models 401 | `HTTP Error 401: Unauthorized` | Try/except, move to next candidate |
| `hf` CLI not installed | `hf: command not found` | Use raw API via Python urllib — don't depend on CLI |
| Repo has no new files | "nothing to commit" | Check `git diff HEAD` before giving up; it's fine to skip commit |
| All trending items non-models (Spaces/Datasets/traces) | No uncovered weight models after filtering | Check `repoData` keys — `runtime` = Space, `datasetsServerInfo` = dataset, `isTraces` = traces. Output `[SILENT]`. |
| Model info 404 on trending item | `HTTP Error 404: Not Found` | Item is a Space/dataset exposed in trending's model list. Skip it — it's not a weight model. |
| `openbmb/UltraX-Preview` resolves to `UltraX-0.6B-Preview` | Canonical ID differs from trending ID | Always fetch `/api/models/{trending_id}` and compare the returned `id` to catch redirects. |
| Unauthenticated API call returns sparse data | Missing `safetensors`, `cardData`, params fields | Set `HF_TOKEN` env var and pass `Authorization: Bearer {token}` header. Without auth, the API silently omits fields. |
