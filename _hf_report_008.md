
---

## 2026-07-30 (weekly cron — Comprehensive HF Ecosystem Report #008)

**SakThai · Main Lead of the House & Master of Hugging Face**

### Executive Summary
Ecosystem is **growing steadily** with all key metrics trending up. Models gained +397 downloads since Jul 26. Dataset count doubled (4→8) with 4 new additions. CI was stabilised (greetings.yml deleted, Node.js versions updated). Critical discovery: **cron file is 0 bytes** — no cron jobs are registered, meaning all scheduled self-improvement, health checks, and maintenance cycles have never fired.

### Current Ecosystem Metrics (2026-07-30, HF API verified)

**Models — 11 public (4,086 total downloads)**
- text-generation: 8 models (3,625 dl)
- feature-extraction: 1 model (188 dl)
- image-to-text: 1 model (104 dl)
- text-to-speech: 1 model (69 dl)
- Top performer: context-1.5b-merged (1,269 dl — +72 since Jul 26)
- Bottom: context-0.5b-tools (7 dl — flat for 5+ days)

**Datasets — 8 public (381 total downloads)**
- Established (4): combined-v6 (175), kaggle-notebooks (103), SimpleToolCalling (52), food-penguin (51)
- New orphans (4): irrelevance-supplement (0), combined-v7 (0), bench-v1 (0), bench-v2 (0)
- All 4 new datasets have YAML-only cards — no README, no badges, no cross-links

**Spaces — 3 (all static HTML, 0 likes)**
- sakthai-tts, sakthai-leaderboard, sakthai-vision-demo
- No inference widgets, no try-before-download path

**Collection — SakThai Model Family (22 items)**
- 11 models + 8 datasets + 3 Spaces — correctly described

**Local GGUF — 5 files**
- sakthai-1.5b-Q4_K_M, sakthai-0.5b-Q4_K_M, qwen2.5-coder-1.5b, llava-1.5-7b, kokoro-82m-q8_0

### Growth Trends (since Jul 26 report, ~4 days)
- Model downloads: 3,689 to 4,086 = +397 (+10.8%)
- Dataset downloads: 300 to 381 = +81 (+27%)
- Total ecosystem: 3,989 to 4,467 = +478 (+12%)
- Datasets: 4 to 8 (+100%)
- Daily download rate: ~120/day — stable

### CI Status — Resolving
- greetings.yml DELETED (committed 08:57 today) — was consistently failing
- Node.js action versions updated (checkout v4 to v5, setup-python v5 to v6)
- Recent commits show focused CI fix activity
- gh CLI unavailable from cron (no GH_TOKEN)
- Pylint, SonarCloud, Secret Scan, OSSAR historically green on main

### CRITICAL: Cron File is 0 Bytes
The sakthai profile cron file is completely empty — 0 bytes, created Jul 23. This means:
- All 10+ self-improvement crons described in previous reports never existed
- The nightly learning loop has never run
- No scheduled asset sync, CI health check, or ecosystem monitor has fired
- P0 blocker — every automated improvement cycle is blocked until crons are registered

### Active Issues Log
1. P0: Cron file empty — no scheduled jobs (since Jul 23)
2. P1: 4 datasets at 0 dl — no READMEs, no discoverability
3. P1: All 3 Spaces are static HTML — no inference path
4. P2: context-0.5b-tools stuck at 7 dl (flat for 5+ days)
5. P2: No community engagement — 1 like across 22 assets
6. P2: SimpleToolCalling deprecated but still published (52 dl)

### Resolved Since Last Report
- greetings.yml deleted (CI failure fixed)
- Node.js action versions upgraded
- Collection description corrected to accurate counts
- All model cards updated with accurate sibling references
- HOUSE_OF_SAK.md ecosystem counts fixed

### Next Actions (Priority Order)
1. **P0: Register cron jobs** — Write a valid cron.yaml with: hf-quick-check (2h), hf-report-plan (weekly), ci-health-check (6h), nightly-learning-loop (daily 02:00)
2. **P1: Add READMEs to 4 zero-download datasets** — combined-v7 (2003 examples), irrelevance-supplement, bench-v1, bench-v2
3. **P1: Convert one Space to Gradio** — sakthai-vision-demo for interactive demo
4. **P1: Promote 0.5b-tools** — add badge, cross-link from combined-v7
5. **P2: Set up GH_TOKEN** — enable CI checks from cron
6. **P2: Properly deprecate SimpleToolCalling** — banner + redirect to combined-v7

### Lessons Captured
- Cron file was never populated — Always verify cron file contents, not just its existence. A 0-byte cron file equals no jobs registered.
- Dataset ecosystem expanded 2x (4 to 8) — New datasets need active promotion within the first week or they orphan at 0 dl.
- Downloads grow at ~120/day regardless of card changes — Card enrichment alone doesn't move the needle.
- CI fixes are working — But need GH_TOKEN to verify from cron.
