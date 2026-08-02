# Social Growth Metrics Check

A **lightweight engagement-only** sub-workflow of the full ecosystem health check. Use this when the task is specifically "check social growth" — downloads, likes, followers, community signals — rather than the full 11-section health report (CI, crons, trending, gap analysis, etc.).

## When to Use

- Dedicated "social growth metrics" cron job (runs in 30-45 seconds vs 3-5 min for full health check)
- Quick check between full reports — track whether downloads/likes/followers are moving
- First-time baseline to establish starting numbers before the deep audit

## Step 0: Pre-Check — Is There Actually Something New?

Before making a single API call, read the journal to determine whether this cron cycle's data is already captured.

**Procedure:**

1. Open `LEARNING_JOURNAL.md` (use the profile path from `environment-automation` — typically `./LEARNING_JOURNAL.md` or `~/profiles/sakthai/LEARNING_JOURNAL.md`)
2. Search for today's date (`YYYY-MM-DD`) near the end of the file
3. Look for total download/like counts for models, datasets, spaces
4. **If all numbers match what the API would return** (you know the approximate totals from the last check), emit `[SILENT]` immediately — do NOT make any API calls, do NOT write to the journal
5. **If the data is stale or absent**, proceed with the data sources below

**Why this matters:** In a busy cron schedule, multiple jobs may capture the same metrics within hours of each other. The earlier job writes the numbers; later jobs should detect they're redundant before burning API calls. This beats the full delta-check script for the lightweight variant — it's a simple file read, not a cached snapshot comparison.

## Data Sources (Cron-Safe Pattern)

All use the two-step approach to avoid Tirith pipe-to-interpreter blocks. Two valid patterns:

**Preferred (curl + file + parse):** `curl -o <file>` followed by `python3 -c` reading the file. Batch all downloads first, then all parses — the terminal tool runs them sequentially within one call, but splitting downloads from processing makes each block independently verifiable.

**Alternative (urllib inline):** Use `python3 -c "import urllib.request; ..."` in a single call. This avoids temp files entirely and works when even `curl -o` is unreliable. Slightly slower (no parallel downloads) but zero cleanup needed. Useful for quick 1-2 endpoint checks.

### 1. Models — full portfolio sweep

**curl+file pattern:**
```bash
curl -s --connect-timeout 10 -o /tmp/hf_models.txt \
  'https://huggingface.co/api/models?author=Nanthasit&sort=downloads&direction=-1&limit=50'

python3 -c "
import json
data = json.load(open('/tmp/hf_models.txt'))
for m in sorted(data, key=lambda x: x.get('downloads',0), reverse=True):
    print(f'{m[\"modelId\"]:50s} dl={m.get(\"downloads\",0):>6} likes={m.get(\"likes\",0):>3}')
print(f'Total: {len(data)} models, {sum(m.get(\"downloads\",0) or 0 for m in data)} downloads')
"
```

**urllib inline pattern (alternative):**
```bash
python3 -c "
import urllib.request, json
req = urllib.request.Request('https://huggingface.co/api/models?author=Nanthasit&sort=downloads&direction=-1&limit=50')
with urllib.request.urlopen(req, timeout=15) as r:
    data = json.loads(r.read())
for m in sorted(data, key=lambda x: x.get('downloads',0), reverse=True):
    print(f'{m[\"modelId\"]:50s} dl={m.get(\"downloads\",0):>6} likes={m.get(\"likes\",0):>3}')
print(f'Total: {len(data)} models, {sum(m.get(\"downloads\",0) or 0 for m in data)} downloads')
"
```

**Note**: The HF API's `modelId` field is the repo identifier. Some model repos may not appear without an auth token — see `hf-rest-api-endpoints.md` pitfall section. For authenticated access, add `req.add_header('Authorization', f'Bearer {token}')`.

### 2. Datasets

```bash
curl -s --connect-timeout 10 -o /tmp/hf_datasets.txt \
  'https://huggingface.co/api/datasets?author=Nanthasit&sort=downloads&direction=-1&limit=10'

python3 -c "
import json
data = json.load(open('/tmp/hf_datasets.txt'))
for d in data:
    print(f'{d[\"id\"]:50s} dl={d.get(\"downloads\",0):>6} likes={d.get(\"likes\",0):>3} modified={d.get(\"lastModified\",\"?\")[:10]}')
print(f'Total: {len(data)} datasets, {sum(d.get(\"downloads\",0) or 0 for d in data)} downloads')
"
```

### 3. Spaces

```bash
curl -s --connect-timeout 10 -o /tmp/hf_spaces.txt \
  'https://huggingface.co/api/spaces?author=Nanthasit&sort=likes&direction=-1&limit=10'

python3 -c "
import json
data = json.load(open('/tmp/hf_spaces.txt'))
for s in data:
    print(f'{s[\"id\"]:50s} likes={s.get(\"likes\",0):>3} sdk={s.get(\"sdk\",\"?\")}')
print(f'Total: {len(data)} spaces')
"
```

### 4. Collection (bundled view)

```bash
curl -s --connect-timeout 10 -o /tmp/hf_collection.txt \
  'https://huggingface.co/api/collections/Nanthasit/sakthai-model-family'

python3 -c "
import json
data = json.load(open('/tmp/hf_collection.txt'))
items = data.get('items', [])
print(f'Collection: {data[\"title\"]}')
print(f'Items: {len(items)}')
types = {}
for i in items:
    t = i.get('repoType','?')
    types[t] = types.get(t,0)+1
print(f'By type: {types}')
sorted_items = sorted(items, key=lambda x: x.get('downloads',0), reverse=True)
for i in sorted_items[:5]:
    print(f'  {i[\"id\"]}: {i.get(\"downloads\",0)} dl, {i.get(\"likes\",0)} likes')
"
```

### 5. User Followers & Profile

The `/api/users/{username}` endpoint may not work (returns "page not found" — observed for Nanthasit 2026-07-26). Instead, follower count is available from the collection's `owner.followerCount` field when you fetch the collection.

```bash
# Follower count lives in collection owner data
python3 -c "
import json
data = json.load(open('/tmp/hf_collection.txt'))
owner = data.get('owner', {})
print(f'Followers: {owner.get(\"followerCount\",\"?\")}')
print(f'PRO user: {owner.get(\"isPro\",\"?\")}')
"
```

### 6. GitHub Social Metrics (Stars, Forks, Followers)

GitHub social growth is a separate dimension from HF — 0 stars means zero algorithmic search ranking regardless of repo quality. Check each cron cycle alongside HF metrics.

#### 6a. User Profile

```bash
curl -s --connect-timeout 10 -o /tmp/gh_user.txt \
  'https://api.github.com/users/beer-sakthai'

python3 -c "
import json
d = json.load(open('/tmp/gh_user.txt'))
print(f'User: {d.get(\"login\",\"?\")}')
print(f'Followers: {d.get(\"followers\",0)}')
print(f'Following: {d.get(\"following\",0)}')
print(f'Public repos: {d.get(\"public_repos\",0)}')
"
```

**Note**: GitHub API's user endpoint does NOT include `total_stars`. To compute total stars, sum `stargazers_count` across all repos in 6b.

#### 6b. Repo Listing (Stars, Forks per Repo)

```bash
curl -s --connect-timeout 10 -o /tmp/gh_repos.txt \
  'https://api.github.com/users/beer-sakthai/repos?per_page=20&sort=pushed'

python3 -c "
import json
data = json.load(open('/tmp/gh_repos.txt'))
total_stars = 0
total_forks = 0
for r in data:
    s = r.get('stargazers_count', 0)
    f = r.get('forks_count', 0)
    w = r.get('watchers_count', 0)
    total_stars += s
    total_forks += f
    print(f'{r[\"name\"]:30s} stars={s:3d} forks={f:3d} watchers={w:3d}')
print(f'---')
print(f'Total: {len(data)} repos, {total_stars} stars, {total_forks} forks')
"
```

#### 6c. GitHub Social Signals to Monitor

| Signal | What it means | Next action |
|--------|--------------|-------------|
| **0 stars across all repos** | Algorithmic invisibility on GitHub search | Needs external seeding (social, cross-platform links) |
| **1+ stars on any repo** | Breakthrough signal — someone found it worthwhile | Star is organic traffic seed; add Star link to sibling repos |
| **1+ forks** | Someone is actively using/customizing the code | Watch for PRs, consider adding CONTRIBUTING.md |
| **Followers growing** | Organic interest in the org/profile | Create release notes to build on interest |
| **Watchers on a repo** | Passive interest — people watching for updates | Push regular commits to convert watchers to users |

**Key finding observed (2026-07-26)**: All 4 repos at 0 stars, 0 forks, 0 watchers, 1 follower. The follower is likely self-follow or a mirror bot. The GitHub social graph is empty — no cross-network signals exist. This is the same cold-start bottleneck as HF (0 likes).

### 7. Cross-Platform Cold-Start Snapshot

When reporting social metrics, compile all platforms into a single compact table for a one-look health view:

```markdown
| Platform | Metric | Our value | Entry threshold | Gap |
|----------|--------|:---------:|:---------------:|:---:|
| HF | Model likes | 0 (all 10 public) | ~1 for trendingScore | Active blocker |
| HF | Trending presence | None | 1+ likes + recent dl | Functional |
| GitHub | Stars (all repos) | 0 | ~100/week for trending | Extreme |
| GitHub | Followers | 1 | N/A | Negligible |
| Kaggle | Notebooks/Votes | 11/0 | Not checked | No account |
```

Use this table to answer: **"Which platform needs the most help?"** — typically the one where the gap between current value and entry threshold is smallest. As of 2026-07-26 that is HF likes (gap: 1 like), making it the single highest-leverage action across all platforms.

## Summary Table Format

Compile the results into a compact table in LEARNING_JOURNAL.md. For cross-platform checks, include GitHub rows:

```markdown
| Asset | Count | Total Downloads | Likes/Stars |
|---|---|---|---|
| HF Models | 12 | 3,648 | 0 likes |
| HF Datasets | 4 | 300 | 0 likes |
| HF Spaces | 2 | — | 0 likes |
| Collection | 1 (18 items) | — | — |
| GitHub Repos | 4 | — | 0 stars |
| GitHub Followers | 1 | — | — |
```

## Insight Extraction Framework

After gathering raw numbers, extract **3 signals** — no more, no less. Each insight should be a distinct, actionable observation from the data:

| Dimension | What to look for | Example |
|-----------|-----------------|---------|
| **Engagement gap** | Downloads vs likes/followers ratio | "3K downloads but 0 likes — repos are used but don't drive engagement" |
| **Cross-platform consistency** | Likes vs stars vs votes | "0 across ALL platforms — not just a HF problem, systemic cold start" |
| **Model concentration** | Which models carry the weight | "Small models (1.5B+0.5B) = 55% of all downloads" |
| **New asset coverage** | Items with 0 or near-0 downloads | "vision-7b, food-penguin at 0 — too fresh to judge" |
| **Growth trend** | Change since last check | "from 2,100 to 2,862 models (up 36%)" |
| **Community void** | Lack of forks, discussions, PRs | "No community forks, discussions, or PRs" |

## From Insight to Action

Each insight pattern maps to a concrete fix. After extracting your 3 signals, connect them to remediation:

| Signal | Root Cause | Fix (see parent SKILL.md) |
|--------|-----------|---------------------------|
| **High downloads, 0 likes/discussions** | No community CTA or engagement hooks | Add "Leave a ♥ if useful" to model card YAML footer; embed collection badge; open a Discussion for questions |
| **Flat growth across consecutive checks** | Discoverability ceiling reached | Build a demo Space (ZeroGPU Tier 2 for $0); cross-post to HF forum or Twitter/Bluesky |
| **Zero-engagement Space** | No discoverability path from sibling models | Add Space badges to every sibling model card; pin the Space in the collection |
| **No forks or PRs** | No contributor onboarding | Add CONTRIBUTING.md stub; tag good-first-issue Discussions; add "Built with SakThai" section |
| **Zero-likes across 2+ weeks (persistent)** | Structural algorithmic invisibility | Break the cold-start loop — one like on any model changes its trendingScore from 0 to non-zero |

**Rule of thumb**: If the same signal fires 3+ reports in a row without the fix being applied, the fix needs to be automated (scripted cron step) rather than documented. Manual action items that never execute are aspirational — see the meta-pitfall in the parent SKILL.md.

### Ready-to-Paste CTA Badge Patterns

When the "high downloads, 0 likes" signal fires, add these to model card READMEs (after the frontmatter `---`, before the main content):

```markdown
<div align="center">

[![Star on HF](https://img.shields.io/badge/⭐-Star_on_HF-yellow?style=social)](https://huggingface.co/Nanthasit/<model-name>)
[![Report Issue](https://img.shields.io/badge/💬-Open_Discussion-8A2BE2?style=social)](https://huggingface.co/Nanthasit/<model-name>/discussions)
[![Collection](https://img.shields.io/badge/🤗-SakThai_Family-blue)](https://huggingface.co/collections/Nanthasit/sakthai-model-family-<slug>)

</div>
```

**Why this works**: The `?style=social` parameter renders HF/GitHub-style buttons (not raw badges), and the `⭐ Star on HF` text is an explicit call to action — users know exactly what to click. Place at the top of the card so it's the first interactive element new visitors see.

## Pitfalls

- **Models endpoint may miss repos without auth** — some public repos don't appear in unauthenticated `?author=` query results. For authoritative counts, pass `Authorization: Bearer $HF_TOKEN`. See `hf-rest-api-endpoints.md` for details.
- **Downloads fluctuate** — API-reported download counts can decrease between checks. This is a caching artifact, not data loss. Flag negative deltas as "API variance" unless they persist across 3+ consecutive checks.
- **Repo visibility changes inflate/deflate delta totals** — If the set of repos visible to the API changes between runs (a repo was private/deleted then re-appears, or vice versa), the total download count delta is contaminated. A "+35" looks like growth but may be two previously-hidden repos (28+7) simply appearing in the listing with unchanged counts. **Always decompose deltas into organic growth (from repos present in both runs) vs. visibility artifact (from repos appearing/disappearing between runs).** The formula: `real_growth = total_delta - sum(repo_deltas_only_from_newly_visible_or_hidden_repos)`. If all deltas are on newly-visible repos and none on the stable set, report "zero organic growth."
- **Collection may return 0 items on stale cache** — query a second time with a `?_=<timestamp>` cache-buster if surprised by a zero-item result.
- **Clean up temp files one at a time** — `rm /tmp/hf_*.txt` triggers Tirith's mass-deletion block. Use individual `rm` commands or skip cleanup.
- **Memory tool may be unavailable in cron mode** — save all findings to files (LEARNING_JOURNAL.md, reference docs), not to the memory store.
- **Pre-check only works when the journal's numbers are trustworthy.** If the previous cron emitted `[SILENT]` without verifying the API first, the journal may be stale. The pre-check assumes the last full check was correct — if in doubt, skip the pre-check and hit the API.
- **GitHub rate limit (unauthenticated): 60/hour** — For cron workflows running every 10min, that's fine for small repos, but a single user+repos query consumes 2 requests. Authenticated requests get 5,000/hour if a GitHub token is available.
- **urllib endpoint quirks** — The HF `/api/trending` endpoint with `limit=N` only accepts certain values (observed: limit=20 works, limit=40 and limit=100 return 400 Bad Request). Use the default (no limit param) or limit=20 when using urllib directly.
