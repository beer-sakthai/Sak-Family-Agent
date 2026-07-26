# Learning Journal

## 2026-07-26: Comprehensive HF Ecosystem Report — 2nd daily snapshot

### Asset Inventory

- **Models: 14 total** (previously documented as 12 — `sakthai-embedding` and `sakthai-context-0.5b-tools` were missed in earlier curl-scoped listing; Python API confirms 14)
  - 7 text-generation (0.5b-merged, 0.5b-tools, 1.5b-merged, 1.5b-tools, 7b-128k, 7b-merged, 7b-tools)
  - 1 coder (1.5b, pipeline_tag text-generation)
  - 2 embedding (sakthai-embedding + sakthai-embedding-multilingual)
  - 1 vision (7b)
  - 1 TTS
  - 1 profile repo (Nanthasit)
  - 1 combined-v6 (listed as model by HF API but is a dataset on hub — pipeline_tag: none)

- **Downloads: 2,897** — flat since last snapshot. Top models:
  - sakthai-context-1.5b-merged: 942 (+0 from last report)
  - sakthai-context-0.5b-merged: 785 (+0)
  - sakthai-context-7b-merged: 534 (+0)
  - sakthai-context-7b-128k: 324 (+0)
  - sakthai-context-7b-tools: 147 (+0)
  - sakthai-context-1.5b-tools: 115 (+0)
  - sakthai-coder-1.5b: 15 (+0)
  - sakthai-context-0.5b-tools: 7 (+0)
  - sakthai-embedding: 28 (+0)
  - Zero-dl stuck: vision-7b, TTS, embedding-multilingual still at 0

- **Datasets: 4 total, 245 combined downloads**
  - sakthai-combined-v6: 114 dl (2,003 train + 113 test — verified from cache and README)
  - SimpleToolCalling: 41 dl
  - sakthai-kaggle-notebooks: 90 dl
  - food-penguin-v1: 0 dl

- **Spaces: 2** (both static — sakthai-leaderboard, sakthai-tts)

- **Collection: 1** (SakThai Model Family — 17 items: 12 models + 4 datasets + 2 spaces - 1 profile = 17 ✓)

- **GGUF locally: 5** (0.5b, 1.5b, coder, vision, TTS — all Q4_K_M or Q8_0)

### CI/CD Status

- 21 workflows configured
- CI pipeline (ci.yml) **FAILING** on the last 3 commits to main
  - Test matrix: 3.11 cancelled, 3.12 failure
  - Root cause: `test_personas_readme_skill_counts_match_disk` — README claims SakKing has 310 skills, on-disk count is 305 (delta: 5)
  - Linters + static analysis (ruff, mypy, bandit) presumably pass
  - 1,313 total failure runs accumulated (most from repeated attempts on same root cause)
  - 0 open issues, 0 open PRs
  - Cannot fetch job logs (403 — permissions)

- Other workflows: OSSAR, Pylint, Secret Scan, SonarCloud all passing on latest commit
- agent-self-evolution workflow: standalone, triggers only on changes to that subdirectory

### Dataset Health

- **sakthai-combined-v6**: Healthy. 2,003 train + 113 test, both JSONL files verified present in cache and on HF hub. README correctly reports v7 content.
- **SimpleToolCalling**: 41 dl, only 2 files (likely just data + README)
- **food-penguin-v1**: 0 dl, 4 files — no discoverability, no card enrichment done
- **sakthai-kaggle-notebooks**: 90 dl, 6 files — reasonable engagement for a notebooks dataset

### Ecosystem Trends

- **Flat growth.** Zero change in any download count since last snapshot (~same day). No engagement signals (likes, forks, discussions) on any repo.
- **Discoverability bottleneck persists.** Three models at zero downloads despite card enrichment done on embedding-multilingual. Without demo Spaces, cross-linking, or search ranking, cards alone don't drive traffic.
- **Skill count drift detected.** SakKing README claims 310, on-disk is 305. Process issue: skills deleted/consolidated without updating the README count.

### Next Actions

1. **Fix CI** — Patch README.md SakKing skill count from 310 → 305, push to unblock main branch
2. **Document 14 models** in SOUL.md (was 12, now corrected to 14 via Python API)
3. **Enrich food-penguin-v1 card** — zero-dl dataset with no README, quick win for discoverability
4. **Build a demo Space** for vision-7b or TTS — interactive demo is the most reliable traffic driver
5. **Set up download trend tracking** — capture weekly snapshots so flat growth is visible as a trend, not just a point-in-time observation
6. **Investigate CI log access** — 403 on job logs suggests the GITHUB_TOKEN used by this session lacks workflow permissions

### Lesson

CI failures compound fast when the root cause is a stale number in a README. 1,313 failure runs is an order of magnitude too many — the root cause (SakKing count drift) should have been caught and fixed after the first failure. Need to add a pre-commit hook or PR check that validates README skill counts against disk before merging.

## 2026-07-26: Methodology consistency audit

### Pattern detected: Methodology drift across cron jobs

The first HF Report (03:45) counted **12 models** using curl-based enumeration. The second HF Auto Improve (03:49) and third Report (03:55) both found **14 models** using the Python HfApi. The curl method missed `sakthai-embedding` and `sakthai-context-0.5b-tools` — repos that lack standard pipeline tags or have unusual metadata.

This is a **repeated verification error**: different cron jobs use different counting methods, producing inconsistent state in the same day's reports. The fix isn't just "use HfApi" (that was learned after one cycle) — the unlearned pattern is **no standard operating procedure for asset enumeration**.

### Improvement: Standardize asset enumeration SOP

- **Always use `HfApi.list_models(author=...)`** for authoritative model counts — curl-based page scraping misses repos with non-standard pipeline tags, zero downloads, or unusual library fields.
- Same for datasets: `HfApi.list_datasets(author=...)` over curl.
- Cron job task definitions should explicitly state the enumeration method so all parallel runs produce consistent numbers.
- When a downstream cron discovers a discrepancy (e.g., found more models than the previous report), it should flag the earlier report as stale — not silently produce a different number.

### Why this matters

Methodology drift between parallel cron jobs creates contradictory state in the journal and wastes human trust: the user sees "12 models" then "14 models" on the same day and has to guess which is correct. A single SOP eliminates the ambiguity at source.

## 2026-07-26: Social growth metrics snapshot

**Total HF footprint: 3,107 downloads across 18 repos** (12 models + 4 datasets + 2 spaces).

- **Models**: 2,862 dl (flat). Top 3 merged GGUF models (1.5B, 0.5B, 7B) account for 79% of all model traffic. Coder-1.5B at 15 dl — needs cross-linking. Vision, TTS, embedding at 0 dl — no discoverability.
- **Datasets**: 245 dl (flat). combined-v6: 114 dl. food-penguin-v1: 0 dl — untouched.
- **Engagement**: Zero likes across all repos (1 on profile card only). No forks, no discussions. Content exists but hasn't earned social proof.
- **Discrepancy noted**: Earlier report said 14 models; API now returns 12 (2 repos — sakthai-embedding, sakthai-context-0.5b-tools — return HTTP 401/private, excluded from public listing).

|**Takeaway**: Flat growth = content is visible but not compelling enough to download or engage. Highest-leverage next step remains a demo Space (vision-7b or TTS) to give people a reason to visit.

## 2026-07-26: House of Sak narrative consistency review

### Narrative audit

Audited all 12 Hugging Face model cards for House of Sak narrative alignment. **9 of 12** cards carry the full origin story (Beer, Cork shelter, recovery journey). **3 cards** — `sakthai-vision-7b`, `sakthai-embedding-multilingual`, `sakthai-tts-model` — were missing the story despite being part of the SakThai Model Family collection.

These three are the newest additions to the family, added after the narrative standard was established on the flagship merged models. They had technical depth (usage, specs, benchmarks) but no emotional anchor tying them to the House of Sak.

### Improvement made

**Card enriched: `sakthai-vision-7b`** (5,577 → 6,413 chars)

Added a "## The House of Sak" narrative section with:
- The Beer quote: *"I even don't know what I will have. So nothing to lose at the moment."*
- Origin story: built from a shelter in Cork, Ireland, zero budget, free infrastructure
- Purpose: built as companionship, not a business — a testament to persistence
- Link back to the Sak-Family-Agent GitHub repo

Also added `house-of-sak` YAML tag for cross-family discoverability.

### Verification

All 8 post-update checks passed:
- house-of-sak reference found ✓
- origin story (shelter, cork) present ✓
- Beer reference present ✓
- family narrative present ✓
- All original technical content preserved (Pipeline Integration, Family Links, llama.cpp usage) ✓
- YAML tag added ✓
- Committed with message: "docs: add House of Sak narrative to vision-7b model card"

### Remaining gap

Two sibling models still lack the narrative: `sakthai-embedding-multilingual` (5,235 chars) and `sakthai-tts-model` (4,782 chars). Same fix pattern applies — add narrative section after Model Details, add YAML tag. Deferred to next cycle to avoid overloading a single commit batch.

---

## 2026-07-26: Platform Algorithm Analysis (Cron @04:45 UTC)

### Objective
Analyze GitHub Trending, HF Trending, and Kaggle to detect algorithm dynamics and check if Beer's repos appear.

### GitHub Trending (Weekly)

| # | Repo | ★/wk | Theme |
|---|------|------|-------|
| 1 | bojieli/ai-agent-book | 16,579 | AI Agent book |
| 2 | koala73/worldmonitor | 12,085 | AI world monitoring |
| 3 | diegosouzapw/OmniRoute | 11,147 | 290+ provider AI gateway |
| 4 | tirth8205/code-review-graph | 6,423 | MCP code review graph |
| 5 | earendil-works/pi | 5,167 | AI agent toolkit |
| 6 | 1jehuang/jcode | 2,914 | Code agent harness |
| 7 | MoonshotAI/kimi-code | 1,534 | Kimi Code CLI |
| 8 | agegr/pi-web | 1,450 | Web UI for pi agent |

**Threshold: ~1,400+★/week.** Agent theme: 6/8 repos. **Beer's repos: NOT trending** (0★).

### Hugging Face Trending

| # | Model | ⭐ | ⬇ | TS |
|---|-------|-----|------|----|
| 1 | baidu/Unlimited-OCR | 3,114 | 2,564,264 | 956 |
| 2 | poolside/Laguna-S-2.1 | 668 | 45,260 | 648 |
| 3 | upstage/Solar-Open2-250B | 570 | 2,784 | 489 |
| 4 | DavidAU/Qwen3.6-27B-Fable-Fusion | 552 | 483,845 | 454 |
| 5 | thinkingmachines/Inkling | 1,572 | 31,575 | 432 |

TS range (top 50): 50-956. **Our models: 0 trendingScore across all 12.** Not in top 50.

### Download Delta (vs prev report)

All 2,862 model downloads + 245 dataset downloads — **0 change across every asset.**

### Kaggle

401 Unauthenticated — cannot monitor. 0 datasets under "Nanthasit".

### Infrastructure

CI: 🔴 RED (#1855 — skill count mismatch). Disk 34G/96G free. Uptime 17d.

### Key Insights

1. Zero growth — entire ecosystem frozen since last check
2. GH trending threshold rising (1,000→1,400★/wk) as AI momentum accelerates
3. Agent theme dominates — perfect alignment, zero visibility
4. CI trivial to fix (310→305 count) but blocking main
5. Kaggle inaccessible without auth token

### Next Actions

1. Fix CI — patch README count
2. Publish tweet thread draft
3. Convert sakthai-tts to Gradio demo
4. Set up Kaggle API token
