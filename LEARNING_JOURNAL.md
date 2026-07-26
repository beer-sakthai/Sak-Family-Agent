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
