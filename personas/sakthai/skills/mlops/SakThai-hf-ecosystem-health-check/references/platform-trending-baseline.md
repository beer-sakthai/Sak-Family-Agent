# Platform Trending Baseline — 2026-07-26

Captured during the first comprehensive multi-platform trending analysis. Future
crons comparing against trending thresholds should reference this baseline and
note any deltas.

## 1. GitHub Trending

### How it works
Ranks repos by star acquisition velocity over time windows (today / week /
month). Higher stars per window = higher rank. No secret sauce — it's a simple
rate sort.

**Access method:** The unauthenticated `github.com/trending` page returns login
redirects (no repo data). Use the Search API instead:
```
https://api.github.com/search/repositories?q=created:>YYYY-MM-DD+stars:>0&sort=stars&order=desc&per_page=50
```
This returns repos created after a given date with stars > 0, sorted by stars
descending. It's not the official trending algorithm but approximates it well.

### Trending repos (today, 2026-07-26)

Python repos only:
| Rank | Repo | Stars today | Description |
|:----:|:----:|:----------:|:------------|
| 1 | ComposioHQ/awesome-claude-skills | 577 | Claude skills integration |
| 2 | shiyu-coder/Kronos | 319 | Code generation tool |
| 3 | anthropics/claude-cookbooks | 132 | Official Claude examples |

All-languages top:
| Rank | Repo | Stars today | Language |
|:----:|:----:|:----------:|:--------:|
| 1 | block/buzz | 2,491 | Rust |
| 2 | citrolabs/ego-lite | 986 | JavaScript |
| 3 | Automattic/harper | 503 | Rust |

**Threshold for Python trending (top 10):** ~300+ stars/day.
**Threshold for all-languages top 10:** ~100+ stars/day.

### Our presence
- **Owner:** `beer-sakthai` — 2 repos (Sak-Family-Agent, sakthai-chat-cli), all 0 stars, 0 forks
- **Topics:** None set — invisible to `topic:ai` or `topic:agent` search filters
- **Appearing?** ❌ Not on any trending page
- **Gap:** 3+ orders of magnitude

## 2. Hugging Face Trending

### How it works
HF exposes a dedicated trending API at `/api/trending` returning a
`recentlyTrending` array (60 items). Each item has `{repoData: {id, downloads,
likes, pipeline_tag, numParameters...}}`. The related Models API also accepts
`sort=trendingScore&direction=-1` for ranking models by trending score.

**NOTE: This baseline originally claimed `/api/trending` returned 404. That was
incorrect — the endpoint works and returns structured data. The earlier 404
may have been a transient API glitch or a request header issue.**

### Top trending models (from /api/trending, 2026-07-26)

| Rank | Model | Downloads | Likes | Pipeline | Params |
|:----:|:-----:|:---------:|:-----:|:--------:|:------:|
| 1 | baidu/Unlimited-OCR | 2,564,264 | 3,130 | image-text-to-text | 3.3B |
| 2 | poolside/Laguna-S-2.1 | 45,260 | 668 | text-generation | 118B |
| 3 | upstage/Solar-Open2-250B | 2,784 | 575 | text-generation | 250B |
| 4 | DavidAU/Qwen3.6-27B-Fable-... | 483,845 | 565 | image-text-to-text | 27B |
| 5 | thinkingmachines/Inkling | 31,575 | 1,573 | image-text-to-text | 952B |
| 6 | Nanbeige/Nanbeige4.2-3B | 11,573 | 413 | text-generation | 3B |
| 7 | microsoft/Mage-Flow | 1,156 | 291 | text-to-image | 4B |
| 8 | prism-ml/Ternary-Bonsai-27B-gguf | 611,685 | 1,033 | text-generation | 27B |
| 9 | zai-org/GLM-5.2 | 707,029 | 4,451 | text-generation | ? |

**Smallest trending model (today):** upstage/Solar-Open2-250B (2,784 dl, 575 likes).
**Smallest trending dataset (separate endpoint):** HuggingFaceCode/stack-v3-train (35,376 dl, 147 likes).

**Threshold for trending list:** ~1,000+ downloads minimum with at least ~300 likes.
**Threshold for prominent trending (top 3):** 30K+ downloads, 1K+ likes.

**Upload trends observed:**
- Image-text-to-text and text-generation pipeline tags dominate
- Large models (27B-952B) and merged/GGUF quantized variants
- Community-driven models (DavidAU-style Franken-merges) appear alongside enterprise releases

### Our presence
- **Models:** 12, top download = context-1.5b-merged (942) — 3x below minimum trending threshold
- **Likes:** 0 on all models (only 1 total across entire author profile)
- **Datasets:** 4, top = 114 downloads
- **Spaces:** 2, both 0 likes
- **Appearing?** ❌ None
- **Gap:** ~3x in downloads, literally 0 in likes — the like gap is more severe than the download gap

## 3. Kaggle Trending

### How it works
Notebooks ranked by "hotness" = combination of votes, views, and recency of last
run. Old notebooks with high votes can stay on trending. Fresh runs help for
discovery but votes are the dominant signal.

**Auth method — Bearer token (NOT Basic auth):** The Kaggle API v1 requires
`Authorization: Bearer $TOKEN` where the token is the `KGAT_` key from
`~/.kaggle/kaggle.json`. The older `curl -u user:key` (Basic auth) returns 401
even with valid credentials. Always use:
```bash
curl -sL -H "Authorization: Bearer $KGAT_KEY" \
  "https://www.kaggle.com/api/v1/kernels/list?page=1&pageSize=10"
```

### Trending notebooks (top 10 by hotness, 2026-07-26)

| Rank | Notebook | Votes | Views | Last run |
|:----:|:---------|:----:|:-----:|:--------:|
| 1 | demand-forecasting-eda | 5 | 0 | 2026-07-26 |
| 2 | ROGII Public Frontier Blend Research | 58 | 0 | 2026-07-25 |
| 3 | BioHub Cell Tracking | 49 | 0 | 2026-07-25 |
| 4 | Data Analisis Superstore | 17 | 0 | 2026-07-26 |
| 5 | Dental X-Ray Quadrant Detection | 5 | 0 | 2026-07-25 |
| 6+ | QM8 Electronic Spectra via GNN | 4 | 0 | ? |
| 7+ | Cockroach Janta Party Pyvis Networkx | 11 | 0 | ? |

**Threshold for top 20:** 4-5+ votes minimum.

### Our presence
- **Owner:** `nanthasitburankum`
- **Notebooks:** 4 total (SakThai Training, SakThai v9 Fix, SakThai v7 1.5B, SakThai v7 1dot5B)
- **Votes:** 0 on all
- **Views:** 0 on all
- **Last run:** 2026-07-23 to 2026-07-24 (2-3 days stale)
- **GPU:** None enabled
- **Private:** All public
- **Appearing?** ❌ None
- **Gap:** Need 5+ votes, ideally with fresh runs within hours

## Summary Matrix

| Platform | Our top asset | Trend threshold | Gap magnitude | Priority |
|:---------|:-------------|:---------------:|:-------------:|:--------:|
| GitHub Trending | 0 stars | ~300 stars/day (Python) | Extreme | Low |
| HF Trending | 942 dl, 0 likes | **ANY trendingScore**: ~1 like + recent downloads | Extreme (no likes) | Medium |
| | | **Top 10**: ~1K+ dl + ~300 likes | | |
| Kaggle Trending | 0 votes, 0 views | **Any visibility**: ~5 votes + recent run | High | **High** |
| | | **Top 20**: 4-5+ votes | | |

**Critical nuance — two HF thresholds:** The table distinguishes between _entering_ (non-zero trendingScore) and _ranking_ (top 10). A single like on any model gives non-zero trendingScore — this is the lowest algorithmic barrier across all three platforms. The "top 10" threshold (~300 likes) is a separate, much higher bar. Future scans should report both: (a) is trendingScore still 0? (b) if non-zero, what's the rank?

**Cold-start bottleneck:** All three platforms share the same structural problem — zero engagement signals (likes, stars, votes) produce zero algorithmic distribution, which produces zero engagement. This is self-reinforcing. Card enrichment helps convert visitors but does not generate them. Breaking the loop requires external traffic seeding (X/Twitter, Reddit, HN) — not in-platform improvements alone.

## Action Recommendations

1. **Kaggle (highest ROI):** Re-run notebooks weekly to keep them fresh. Add
   GPU for at least one run to make the notebook more compelling. The gap is
   smallest here but still requires external action (cannot be solved by
   in-platform improvements alone).
2. **HF (medium ROI):** No likes anywhere is the real problem — even a single
   like on a model would help. External promotion (tweet thread) is the only
   realistic path to generate likes. Card improvements have been exhausted.
3. **GitHub (lowest ROI):** Add repository topics (ai, agent, llm, huggingface,
   tool-calling) to improve search discoverability — zero-effort fix but
   requires `GITHUB_TOKEN` with `repo` scope (not available in cron env).
4. **Cross-platform synergy:** A tweet thread about the HF ecosystem could
   simultaneously drive stars (GitHub), likes (HF), and visits (Kaggle).
   This is the only action that can move all three needles at once.

---

*Baseline captured 2026-07-26. Updated 2026-07-26 with corrected Kaggle auth
method, confirmed /api/trending response structure, and refined trending
thresholds from cross-platform scan. Compare against this on subsequent
visibility scans to detect changes.*