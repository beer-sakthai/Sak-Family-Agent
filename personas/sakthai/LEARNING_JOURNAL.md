# SakThai Learning Journal

## 2026-07-30 — HF Ecosystem Report & Plan (Scheduled Cron #007)

### Executive Summary
Beer's HF account **Nanthasit** holds 11 public models (8 text-gen, 1 image-to-text, 1 TTS, 1 embedding), 8 datasets, 3 static Spaces, and 2 collections. Total model downloads hit **4,086** (+438 from 3,648 on 07-26). All previously zero-download models have broken through — embedding-multilingual leads at 188 dl. **CI is FAILING** (both test matrix jobs exit with code 1). The collection description says "12 models" but has 11. Four new datasets (irrelevance-supplement, combined-v7, bench-v1, bench-v2) have 0 downloads.

### Models (11 public — 4,086 total downloads, +438 since 07-26)

Growth by model, sorted by downloads:
- **sakthai-context-1.5b-merged** — 1,269 dl (+72 from 1,197) — Top performer, steady growth
- **sakthai-context-0.5b-merged** — 1,030 dl (+36 from 994) — Strong second, approaching 1K
- **sakthai-context-7b-merged** — 585 dl (+23 from 562) — Steady growth
- **sakthai-context-7b-128k** — 382 dl (+31 from 351) — Consistent
- **sakthai-context-7b-tools** — 219 dl (+34 from 185) — Tool variant gaining
- **sakthai-embedding-multilingual** — 188 dl (+84 from 104) — **Star performer**, organic explosion
- **sakthai-context-1.5b-tools** — 163 dl (+20 from 143) — Steady
- **sakthai-vision-7b** — 104 dl (+59 from 45) — Strong growth despite missing mmproj
- **sakthai-coder-1.5b** — 70 dl (+36 from 34) — Doubled since last report
- **sakthai-tts-model** — 69 dl (+36 from 33) — More than doubled
- **sakthai-context-0.5b-tools** — 7 dl (flat, unchanged from 7) — **Stuck**

**Key insight:** All models grew. The zero-download victory from 07-26 is now a comfortable growth phase. Embedding-multilingual (0→188 in 5 days) is the standout. TTS-model and coder both doubled. The only stalled model is 0.5b-tools at 7 dl — the adapter-only variant that requires merging.

### Datasets (8 total — 381 total downloads, +81 since 07-26)

- **sakthai-combined-v6** — 175 dl (+25 from 150) — Best performer, solid growth
- **sakthai-kaggle-notebooks** — 103 dl (+11 from 92) — Steady
- **SimpleToolCalling** — 52 dl (+9 from 43) — Still gaining despite deprecation tag
- **food-penguin-v1** — 51 dl (+36 from 15) — Strong growth, more than tripled
- **sakthai-irrelevance-supplement** — 0 dl (new, no traction yet)
- **sakthai-combined-v7** — 0 dl (new, 2,309 examples, no traction yet)
- **sakthai-bench-v1** — 0 dl (new, no traction yet)
- **sakthai-bench-v2** — 0 dl (new, no traction yet)

**License fix verified:** All 8 datasets now have license metadata in cardData (mit or apache-2.0), plus license tags. The 07-26 report called this out as a gap — it's been resolved.

**"v7" tag issue:** RESOLVED. Combined-v6 no longer has v7 in its tags. Combined-v7 exists as its own separate repo. The tag confusion from earlier reports has been cleaned up.

### Spaces (3 total — all static)

- **sakthai-tts** — static HTML, no usage metrics
- **sakthai-leaderboard** — static HTML, no usage metrics
- **sakthai-vision-demo** — static HTML (new since 07-26 report)

All three are pure static HTML Spaces. No functional Gradio or interactive demos. This remains the biggest ecosystem gap.

### Collections

**1. SakThai Model Family** (active)
- 22 items: 11 models + 8 datasets + 3 spaces
- No duplicates ✅
- **Description still says "12 models"** but has 11 — needs patch

**2. SakThai Context Models** (slug from listing, but API returns "Collection not found" — may have been deleted or slug changed)

### CI Status — FAILING ❌

**CI workflow (run #1978)** — Failure on commit e3e02b6 (main)
- `test (3.11)`: Process completed with exit code 1
- `test (3.12)`: Process completed with exit code 1
- Warnings: Node.js 20 deprecated (actions/checkout@v4, actions/setup-python@v5 being forced to Node.js 24)

Other workflows all green:
- Pylint (#1863) ✅
- Secret Scan (#718) ✅
- SonarCloud (#1142) ✅
- OSSAR (#1249) ✅

The CI failure is recent. Earlier commits (from the 07-26 report era) had all-green CI. The failure appears correlated with the Node.js 20→24 deprecation or a test assertion break caused by a recent commit.

### Recent Git Activity (last 4 hours)
- 20+ commits on main, including:
  - Skill fixes: version fields added to 40 SKILL.md files
  - Skill count updates (SakThai 342→360, total 917→935)
  - CodeQL alert fixes (clear-text logging)
  - Colab notebook for bench-v2 evaluation
  - Greetings.yml disabled (deprecated action)
  - README count syncs

### Issues Log

| # | Issue | Severity | Since |
|---|-------|----------|-------|
| 1 | **CI failing** — both test matrix jobs exit with code 1 | CRITICAL | Today |
| 2 | **Collection description wrong** — says "12 models" but has 11 | LOW | 07-26 |
| 3 | **4 new datasets with 0 downloads** — irrelevance-supplement, combined-v7, bench-v1, bench-v2 | MEDIUM | Today |
| 4 | **sakthai-context-0.5b-tools stuck at 7 dl** — flat for 5+ days | LOW | 07-26 |
| 5 | **No functional demo Spaces** — all 3 are static HTML | MEDIUM | 07-25 |
| 6 | **vision-7b missing mmproj** — GGUF unusable without multimodal projector | MEDIUM | 07-25 |
| 7 | **Model license tags present but cardData YAML missing license** — 11/11 models have license:NONE in cardData | LOW | 07-26 |
| 8 | **SimpleToolCalling deprecated but still published** — still gaining downloads, should be handled | LOW | 07-25 |
| 9 | **Node.js 20 deprecation in CI** — actions forced to Node.js 24, may cause failures | MEDIUM | Today |

### Resolved Issues (since 07-26)
- ✅ All datasets now have license metadata (mit or apache-2.0)
- ✅ Combined-v6 no longer has "v7" tag confusion
- ✅ All previously zero-download models now have traction
- ✅ Collection description updated from old "14 models" to accurate counts
- ✅ sakthai-combined-v6 collection duplicate removed

### Next Actions (Priority Ordered)

1. **Fix CI failure (CRITICAL)** — Diagnose why test (3.11) and test (3.12) both fail with exit code 1. Check if Node.js 20→24 forced migration broke the setup, or if a test assertion changed. This blocks all other improvements — no green CI.

2. **Update Node.js action versions in CI** — Pin to Node.js 24-compatible versions of actions/checkout and actions/setup-python, or upgrade to v4→v5 and v5→v6 if available. The "Node.js 20 is deprecated" warning may eventually break builds.

3. **Fix collection description** — "12 models" → "11 models" in sakthai-model-family description (quick 2-minute fix via HF API).

4. **Promote 4 zero-download datasets** — Cross-link combined-v7, irrelevance-supplement, bench-v1, bench-v2 from model cards and collection description. Add Rising Stars sections.

5. **Investigate SakThai Context Models collection** — Slug exists in listing but API returns "Collection not found". Verify if it was deleted intentionally or broken.

6. **Build one functional demo Space** — Convert sakthai-vision-demo from static HTML to a real Gradio app using vision-7b. High-leverage: drives downloads to all sibling models.

7. **Resolve 0.5b-tools stall** — At 7 dl for 5+ days. Consider publishing a merged GGUF variant if the adapter-only format limits reach.

8. **Add cardData license to all 11 models** — Even though tag-level license is present, cardData YAML is needed for modern HF search filtering.

### Lessons Captured
- **All-models-growth is a first** — For the first time since tracking began, every single model gained downloads between reports. The zero-download drought is over.
- **Embedding models can explode** — Multilingual embedding went 0→104→188 in 5 days with no marketing. Embedding models seem to have viral discovery potential on HF.
- **Static Spaces don't drive downloads** — TTS model doubled (33→69) despite no functional demo, so card enrichment alone works. But a functional demo would likely accelerate further.
- **CI health is brittle** — Node.js deprecation or test drift can silently break the matrix. Need a CI health cron that alerts on status changes (this cron job is well-positioned to do that).
- **Dataset ecosystem is expanding fast** — 4 datasets created since last report (8 total, up from 4). Need to actively promote the new ones to prevent them from being invisible orphans.

---
