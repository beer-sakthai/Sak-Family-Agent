# Platform Algorithms Monitor — Cron Pattern

Fetches trending data from GitHub, Hugging Face, and (where possible) Kaggle. Compares against our portfolio. Records findings.

## Quick Reference

| Platform | Endpoint / URL | Method | Limit |
|----------|---------------|--------|-------|
| GitHub daily trending | `https://github.com/trending?since=daily` | `browser_navigate` + snapshot | 25 articles |
| GitHub weekly trending | `https://github.com/trending?since=weekly` | `browser_navigate` + snapshot | 25 articles |
| HF trending (all types) | `https://huggingface.co/api/trending?limit=20` | `curl -s` | **max 20** — returns ALL types under `recentlyTrending` key; each item has `repoType` field (`model`/`dataset`/`space`). Use one call, filter by `repoType` in Python. ⚠️ The `type` filter param documented in older posts may not produce structured results — the API returns a unified `recentlyTrending` array regardless of `type` param. See §Response Structure below. **Also accepts `?scope=weekly` and `?scope=daily` to get different timeframes** — both return 30 items (more than the default 20). Returns different trending sets per scope. |
| HF trending via CLI (PREFERRED tirith-safe) | `hf models list --sort trending_score --limit 20` | `hf` CLI, single terminal() call | 20 models (models only, not datasets/spaces). Single call, no temp files, no pipe-to-interpreter risk. Use `2>&1` to merge stderr. Parse TSV output by column position. |
| Our HF models | `hf models list --author Nanthasit --sort downloads --limit 30` (tirith-safe) OR `https://huggingface.co/api/models?author=Nanthasit&sort=downloads&direction=-1` | `hf` CLI PREFERRED, `curl -s` fallback | — |
| Our HF datasets | `https://huggingface.co/api/datasets?author=Nanthasit&sort=downloads&direction=-1` | `curl -s` (⚠️ `hf datasets list` shows `downloads=0` for all — CLI bug) | — |
| Our HF spaces | `https://huggingface.co/api/spaces?author=Nanthasit&sort=downloads&direction=-1` | `curl -s` | — |
| Kaggle trending | `https://www.kaggle.com/trending` | `curl -sL` → empty React shell | N/A (JS-only) |
| Kaggle user profile | `https://www.kaggle.com/{username}` | `curl -sL` → empty React shell | N/A (JS-only) |
| Kaggle dataset listing (unauthenticated) | `https://www.kaggle.com/api/v1/datasets/list?sortBy=votes` | `curl -s` | 20 items/page. Fields: `voteCount`, `downloadCount` (not `totalVotes`/`totalDownloads`) |
| Our GitHub repos (ALL) | `https://api.github.com/users/beer-sakthai/repos?per_page=100&type=public&sort=updated` | `curl -s` with token from `git credential-store get` | — |
| Our GitHub repos (search) | `https://api.github.com/search/repositories?q=sakthai+OR+sak-family-agent+OR+sakthai-chat-cli&per_page=10` | `curl -s` | — |

## Execution Order

⚠️ **Step 0 is mandatory.** Sessions that skip it waste 5-15 API calls on redundant runs.

### 0. Pre-run delta check — skip if nothing changed

Before ANY API call, run the pre-report delta check (see `pre-report-delta-check.md` in this skill's references):

1. Read the last "Platform Algorithms" entry from LEARNING_JOURNAL.md — extract date and total model download count
2. Fetch ONE HF API call to get current total download count
3. If same-day entry exists AND totals match -> emit `[SILENT]` immediately, skip all remaining steps

This is a local grep + one curl call (~0.5s total). It saves the full 5-15 call pipeline when metrics haven't budged since the last scan.

**Quick gate script:**

```bash
python3 << 'PYEOF'
import re, json, urllib.request, datetime

with open('/opt/data/LEARNING_JOURNAL.md') as f:
    content = f.read()

sections = re.split(r'^## ', content, flags=re.MULTILINE)
relevant = [s for s in sections if 'Platform Algorithms' in s]
if not relevant:
    print('NEED_FULL_SCAN')
    exit(0)

last = relevant[-1]
date_m = re.search(r'(\d{4}-\d{2}-\d{2})', last)
last_date = date_m.group(1) if date_m else ''

req = urllib.request.Request(
    'https://huggingface.co/api/models?author=Nanthasit&limit=30',
    headers={'User-Agent': 'sakthai-cron/1.0'}
)
with urllib.request.urlopen(req, timeout=10) as r:
    models = json.loads(r.read())
current_total = sum(m.get('downloads', 0) for m in models if not m.get('private'))

prev_m = re.search(r'(\d+)\s*downloads?(?:\s*across|\s*models|\s*\[)', last, re.IGNORECASE)
prev_total = int(prev_m.group(1)) if prev_m else -1

today = datetime.date.today().isoformat()
if last_date == today and current_total == prev_total:
    print('SAME_DAY_SAME_TOTAL')
else:
    print(f'NEED_FULL_SCAN prev={prev_total} current={current_total} date={last_date}')
PYEOF
```

If the script outputs `SAME_DAY_SAME_TOTAL`, emit `[SILENT]` and exit — no API calls wasted.

### 1. Fetch all platform data (skip this if step 0 said SAME_DAY_SAME_TOTAL)

```bash
# One API call — returns all types under `recentlyTrending` key
curl -s 'https://huggingface.co/api/trending?limit=20' -o /tmp/hf_trending.json
# Our assets
curl -s 'https://huggingface.co/api/models?author=Nanthasit&sort=downloads&direction=-1' -o /tmp/hf_our_models.json
curl -s 'https://huggingface.co/api/datasets?author=Nanthasit&sort=downloads&direction=-1' -o /tmp/hf_our_datasets.json
curl -s 'https://huggingface.co/api/spaces?author=Nanthasit&sort=downloads&direction=-1' -o /tmp/hf_our_spaces.json
curl -s 'https://api.github.com/search/repositories?q=sakthai+OR+sak-family-agent+OR+sakthai-chat-cli&per_page=10' -o /tmp/gh_sak_repos.json
browser_navigate('https://github.com/trending?since=daily')
```

2. **Parse data**:
   - For HF JSON files: use `python3 -c` with file reads. Filter trending items by `repoType` field.
   - For GitHub trending: **prefer `browser_console` JS extraction** (Option B under §GitHub Trending Extraction) for structured data in one call. Fall back to `browser_snapshot` accessibility tree parsing when JS extraction fails (e.g., the expression returns empty or the page hasn't fully rendered).

3. **Extract key metrics**:
   - Top N trending repos/models (name, stars/likes, one-line description, theme)
   - Our assets' current downloads + likes
   - Compare our assets against trending themes (are we in a trending category?)
   - Any new social engagement signals (0→1 like, 0→1 star)

4. **Identify algorithmic insights** — common themes, velocity patterns, platform-specific ranking factors.

5. **Append to LEARNING_JOURNAL.md** — use the two-step snippet workflow.

## GitHub Trending Extraction (browser_navigate)

### Option A — browser_snapshot accessibility tree (comprehensive, slower)

The accessibility tree renders trending articles as `<article>` elements with:
- `heading` with repo name (e.g., `"opengeos / GeoLibre"`)
- `link` accessible via snapshot's `ref=eNN` for the repo URL
- `StaticText` for description, language, stars count, stars-today count
- Contributor avatars in a `Built by ` container

**Extraction pattern:** Scan for heading level=2 entries whose text matches `"owner / repo"` pattern. Below each heading, find the paragraph (description) and the stars/fork counts. The final `StaticText` in each article element is the "X stars today" count.

Example from snapshot:
```
- link "star 4,335" [ref=e65]
- StaticText " 671 stars today"
```

The star total is in the link text (e.g. "4,335" from "star 4,335"). The daily velocity is in the trailing StaticText.

**Limitation:** browser_navigate shows 25 articles on first load. Scrolling only reveals the same articles — it's not infinite scroll.

### Option B — browser_console JS extraction (preferred, faster, structured)

After `browser_navigate('https://github.com/trending')`, use `browser_console` with JavaScript expressions to extract structured data directly:

**Get repo names (returns array of "owner / repo" strings):**
```javascript
Array.from(document.querySelectorAll('article h2 a')).map(a => a.textContent.trim())
```

**Get full details for each repo (name, description, stars, daily velocity):**
```javascript
Array.from(document.querySelectorAll('article')).map(article => {
  const title = article.querySelector('h2')?.textContent?.trim()?.replace(/\n\s+/g, ' ') || '?';
  const desc = article.querySelector('p')?.textContent?.trim() || '';
  const stars = article.querySelector('[href*="star"]')?.textContent?.trim() || '?';
  const today = article.textContent.match(/([\d,]+)\s*stars\s*today/);
  return `${title} | ⭐${stars} | ${today ? today[1]+' today' : ''} | ${desc.substring(0,80)}`;
}).join('\n')
```

**Estimated vs actual stars today (from all page text for cross-verification):**
The `([\d,]+)\s*stars\s*today` regex extracts the daily velocity from each article's textContent. Verify against the total star count from the `[href*="star"]` link to catch stale data.

**Advantages over snapshot parsing:**
- No need to parse deep accessibility tree (25 articles × ~15 elements each)
- Returns structured data in one expression, not spread across 50+ snapshot lines
- ~3x faster (one browser_console call vs 3+ browser_snapshot calls)
- Easy to filter, sort, or reformat within JS before returning

**Limitation:** `browser_console` returns strings. For complex transformations, pair with a `python3 -c` script on the extracted data using a temp file.

## HF Trending Response Structure

The `/api/trending?limit=20` endpoint returns a single JSON object — NOT separate arrays per type:

```json
{
  "recentlyTrending": [
    {"repoType": "model", "repoData": {"id": "author/model", "downloads": 99214, "likes": 8805, "pipeline_tag": "text-generation", ...}},
    {"repoType": "dataset", "repoData": {"id": "author/dataset", "downloads": 76867, "likes": 235, ...}},
    {"repoType": "space", "repoData": {"id": "author/space", "likes": 928, ...}}
  ]
}
```

**Key facts:**
- The `type` query parameter (e.g., `?type=model`) is **ignored** — the API always returns all types mixed together
- Each item's `repoType` field distinguishes type (`model` / `dataset` / `space`)
- Items are ordered by recency + activity blend, not pure download velocity
- Large orgs dominate: MoonshotAI, Baidu, Microsoft, zai-org with 100k+ downloads and 1k+ likes
- Only outliers (like DavidAU's 736k-download GGUF quantization) break in from small creators

**Extraction in Python:**
```python
with open('/tmp/hf_trending.json') as f:
    td = json.load(f)
items = td.get('recentlyTrending', [])
models = [i for i in items if i.get('repoType') == 'model']
datasets = [i for i in items if i.get('repoType') == 'dataset']
spaces = [i for i in items if i.get('repoType') == 'space']

for m in models[:10]:
    rd = m.get('repoData', {})
    print(f"{rd['id']:50s} dls:{rd.get('downloads',0):8d} likes:{rd.get('likes',0):4d}")
```

## Known Kaggle Limitation

Both `/trending` and user profile pages render empty React shells (`<div id="root">`) with no server-side content. The title reflects the page (`"Trending | Kaggle"` or `"{Username} | Kaggle"`) but the body has nothing. Tools like Puppeteer/Playwright (not available in cron mode) or the official Kaggle API (`kaggle` CLI with API key) are required for programmatic access.

**Kaggle REST API (`/api/v1/users/{username}`)** — can check profile existence without auth:
- **Existing user** (e.g., `Nanthasit`): returns valid JSON with `displayName`, `userName`, `publicNotebookCount`, `publicDatasetCount`, etc.
- **Non-existent user** (e.g., `beersakthai`): returns empty/invalid body — `json.load()` raises `JSONDecodeError` ("Expecting value"). Use `<title>` tag check as secondary verification (curl the profile page, grep for `"| Kaggle"`).

**Kaggle dataset listing API fields (verified 2026-07-30):** The `/api/v1/datasets/list` response uses `voteCount` and `downloadCount` (not `totalVotes`/`totalDownloads`). Some fields have `Nullable` variants (`titleNullable`, `subtitleNullable`) — use the non-nullable versions (`title`, `subtitle`) which are `null` when absent. Response also includes `hasTitle`, `hasSubtitle` boolean guards. Example: `d.get('voteCount', 0)` returns the vote count. Top datasets have 50K+ votes and 100K+ downloads.

**Profile existence verification pattern:**
```bash
# Method 1 — API (fast, but errors on non-existent users)
curl -s "https://www.kaggle.com/api/v1/users/{username}" -o /tmp/kaggle_user.json
python3 -c "import json; json.load(open('/tmp/kaggle_user.json')); print('EXISTS')" 2>/dev/null || echo "NOT FOUND"

# Method 2 — Page title (slower, but works for both cases)
curl -sL "https://www.kaggle.com/{username}" 2>/dev/null | grep -o '<title>[^<]*</title>'
# Existing: "<title>Nanthasit | Kaggle</title>"
# Missing: "<title>Kaggle: Your Home for Data Science</title>"
```

## Trend Themes Observed (2026-07-30)

| Theme | GitHub | HF Models | HF Datasets | HF Spaces |
|-------|--------|-----------|-------------|-----------|
| Agent ecosystems | 6/8 weekly trending | 2/10 | 3/15 | 0/10 |
| Voice/speech AI | 2/8 daily | 1/10 (TTS) | 0/15 | 1/10 |
| Video generation | 0/8 | 0/10 | 0/15 | 4/10 |
| GGUF quantization | 0/8 | 5/20 | 0/15 | 0/10 |
| Multimodal | 0/8 | 8/20 | 0/15 | 2/10 |

## Trending Thresholds (quantified 2026-07-30)

Live API data from `GET /api/trending` produced these ranges:

| Metric | Min | Max | Median | Our best | Gap |
|--------|-----|-----|--------|----------|-----|
| Likes to trend | 28 | 8,822 | ~500 | 1 (vision-7b) | 27× |
| Downloads to trend | 0 | 2,598,659 | ~15,000 | 1,599 (1.5b) | 9× |
| **`hf trending_score`** (from CLI) | 113 | 8,029 | ~250 | 1 (vision-7b) | **112×** |

**Key insight:** Likes are the binding constraint. A model can have 0 downloads and still trend if it has 28+ likes. Our models have downloads but zero community engagement signal.

**`trending_score` column note (2026-07-30):** The `hf models list --sort trending_score` CLI flag exposes a separate numeric column not available via the REST API's `/trending` endpoint. This column appears to measure a different velocity blend than the trending page itself — the top item scores 8,029 (Kimi-K3) vs the API trending's top model (same Kimi-K3 at 8,822 likes). The CLI's score is likely a normalized rank, while the API returns raw metrics. Threshold to break top 50 CLI: ~113.

**Ranking factors (inferred):**
1. **Like velocity** — likes accumulated in the trending window (24h or 7d)
2. **Download-to-like ratio** — high ratio (many downloads, few likes) suppresses trending score
3. **Novelty** — newly published or recently-updated repos rank higher than stable older ones
4. **Author reputation** — org accounts (MoonshotAI, Baidu, Microsoft) dominate, likely weighted

**To trend, a model needs:** ≥28 likes OR ≥15k downloads AND positive velocity in both. Likes are ~10× more influential than downloads per unit.

### GitHub Star Threshold (2026-07-30)

GitHub trending in the last 24h: **226,619 repos** created. Top 25 cutoff: **★8** in a single day.

Our 8 repos have **0 stars across all time** — no single-day burst, no discoverability. The algorithm measures star *velocity* in a ~24h window, not total accumulation. A repo needs ~8 stars in one day to appear; our total lifetime is 0.

### Cross-Platform Algorithm Insight (2026-07-30)

All three platforms (HF, GitHub, Kaggle) share the same cold-start structure:

| Property | HF Trending | GitHub Trending | Kaggle Trending |
|----------|-----------|----------------|-----------------|
| Trigger metric | `trending_score` (≥113) | Star velocity (≥★8/day) | Vote velocity |
| Time window | Hours–days | ~24 hours | ~7 days |
| Our status | score=1 (vision-7b) | 0 stars total | Unindexed |
| Gap to floor | 112× | 1 burst of ★8 | 1 published+upvoted dataset |

**The shared architecture:** All three rank content by *velocity in a tight time window*, not by accumulated quality. Slow organic accumulation across 9 weeks (5,875 dl) is invisible to every algorithmic surface. The cold-start gateway is identical on all three: a coordinated burst push on at least one platform.

**Practical implication:** Until we ship a catalyst event (cross-post, social share, Colab badge) that triggers a download/star/like burst, no algorithmic surface will surface our work. Detection of any burst (a single like, a single star) is the first milestone — not trending itself.
