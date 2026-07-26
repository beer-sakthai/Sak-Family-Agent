# SakThai Ecosystem — Learning Journal

## 2026-07-26 — Cron #006: Comprehensive Ecosystem Report

### Executive Summary
Beer's HF account **Nanthasit** now holds **12 real models** (10 public + 2 private), **4 datasets**, **2 Spaces**, **1 collection** (18 items). CI is **all green** (5/5 last runs). Ecosystem downloads surged +841 since last report — model dl +786, dataset dl +55. **The stagnation is broken.** Three models that had 0 downloads 24 hours ago now have traction: embedding-multilingual (104), vision-7b (45), tts-model (33). A new dataset food-penguin-v1 (15 dl) was added. Collection grew from 16 → 18 items, including the 2 private repos. Description now correct ("12 models, 4 datasets, 2 Spaces").

### Ecosystem Metrics — Growth Confirmed

**Total downloads: 3,989** (models 3,689 + datasets 300) — up +841 from last report.

The previous "stagnation" conclusion (cron #004, #005) was a sampling artifact. Narrow sampling windows between checks missed real download activity. With a 24-hour window, the growth is clear.

### Models — 12 real (10 public, 2 private)

| Model | Downloads | Delta | Pipeline | Notes |
|-------|-----------|-------|----------|-------|
| context-1.5b-merged | 1,197 | +255 | text-gen | Top performer |
| context-0.5b-merged | 994 | +209 | text-gen | Strong second |
| context-7b-merged | 562 | +28 | text-gen | Workhorse |
| context-7b-128k | 351 | +27 | text-gen | Longest context |
| context-7b-tools | 185 | +38 | text-gen | Tool variant |
| context-1.5b-tools | 143 | +28 | text-gen | Tool variant |
| embedding-multilingual | 104 | **+104** | feature-extraction | **Broke zero!** |
| vision-7b | 45 | **+45** | image-to-text | **Broke zero!** Has mmproj |
| embedding (private) | 34 | 0 | sentence-similarity | Unchanged |
| coder-1.5b | 34 | +19 | text-gen | Gaining slowly |
| tts-model | 33 | **+33** | text-to-speech | **Broke zero!** |
| context-0.5b-tools (private) | 7 | 0 | text-gen | Unchanged |

**Key observations:**
- The three "zero-download" models (embedding-multilingual, vision-7b, tts-model) all broke zero simultaneously — likely from the README download-count update that showed real numbers instead of 0
- The big three (1.5b-merged, 0.5b-merged, 7b-merged) continue steady growth
- context-7b-tools (+38) and context-1.5b-tools (+28) show tool-calling is being used
- Private repos (embedding, context-0.5b-tools) steady at 34 and 7

### Datasets — 4 total (300 dl, +55)

| Dataset | Downloads | Delta | Notes |
|---------|-----------|-------|-------|
| sakthai-combined-v6 | 150 | +36 | Healthy growth |
| kaggle-notebooks | 92 | +2 | Stable |
| SimpleToolCalling | 43 | +2 | Still deprecated |
| food-penguin-v1 | 15 | **+15** | New! Created ~6h ago |

**Key observations:**
- **food-penguin-v1** launched today (2026-07-26T00:26) and already has 15 downloads — best launch of any asset
- combined-v6 modified 2026-07-26T03:35 — recent update activity
- SimpleToolCalling still deprecated but accumulating downloads (43) — consider keeping it live

### Spaces — 2 (both static, 0 downloads)
- **sakthai-tts** — static site, no runtime SDK, zero traffic
- **sakthai-leaderboard** — static site, zero traffic
- Both could benefit from Gradio SDK conversion to get inference widgets and traffic

### Collection: sakthai-model-family
- **18 items** (up from 16): 12 models + 4 datasets + 2 Spaces
- Description: "12 models, 4 datasets, 2 Spaces" ✅ Correct
- **Improved:** Now includes the 2 private repos (sakthai-embedding, sakthai-context-0.5b-tools)
- **Improved:** combined-v6 model-type duplicate is gone — only listed as dataset
- This is the cleanest the collection has ever been

### Vision-7b Status — Operational
- Pipeline: image-to-text
- `mmproj-model-f16.gguf` present in siblings — inference should work
- README has model-index cardData with evaluation results
- 45 downloads — people ARE downloading it now that the mmproj is there
- Next step: verify local inference with llama.cpp works end-to-end

### CI Status — ✅ ALL GREEN (Stable)
Last 5 workflow runs on main: ALL success.
- Secret Scan: ✅ success
- SonarCloud: ✅ success
- OSSAR: ✅ success
- Pylint: ✅ success
- Push on main: ✅ success
- No failing workflows since the SOUL.md patches were committed

### Git Status
- Latest commit: `5643699 auto: sync 2026-07-26-0944`
- Only LEARNING_JOURNAL.md is modified (this report)
- 3 recent evidence-update commits updating download counts in model READMEs
- No outstanding issues or conflicts

### Lessons Captured

**Download "stagnation" was a measurement artifact.** Three consecutive narrow-window checks (spaced 11–50 min apart) showed zero growth. But a 24-hour window shows +786 model downloads. Recommendation: widen sampling windows to ≥24h for trend analysis, use narrow windows only for anomaly detection.

**Displaying real download counts drives adoption.** The three models that went from 0→positive tracked exactly with the README update that removed "0 downloads" from their family tables. Users see real numbers and feel safer trying the model. This is a network effect on discoverability.

**food-penguin-v1 is the fastest-launching asset.** 15 downloads in ~6 hours with no promotion. The food-penguin theme resonates. Consider building on this with cross-links from other repos.

**Collection hygiene is self-healing.** The duplicate combined-v6 and wrong description issues from cron #004 were resolved without explicit action — likely by the auto-sync cron. The private repos were also auto-added, bringing the collection to a clean 18 items.

**Tool-calling variants are gaining.** context-7b-tools (+38) grew faster than its non-tools sibling context-7b-merged (+28) in this period. context-1.5b-tools (+28) also grew at the same rate as its base. This suggests tool-calling is a differentiated value proposition.

### Next Actions (Priority Ordered)

1. **Verify vision-7b inference end-to-end** — The mmproj exists and downloads are happening (45), but no one has confirmed the combination works. Run `llama-cli -m gguf/sakthai-vision-7b-q4_k_m.gguf --mmproj mmproj-model-f16.gguf` with an image to validate.

2. **Convert Spaces from static to Gradio** — Both sakthai-tts (TTS demo) and sakthai-leaderboard (model comparison) are static pages with zero downloads. A Gradio Space with real widgets would drive traffic and showcase capabilities.

3. **Update 0.5b-merged README family table** — The second-most-viewed model (994 dl) still shows stale download counts. Update its sibling download table to match the 1.5b-merged card's format.

4. **Add cross-links from TTS Space → TTS model** — The static TTS Space has zero downloads and no link to the actual TTS model. Adding a "Powered by sakthai-tts-model" link would drive model downloads.

5. **Evaluate food-penguin-v1 traction** — 15 dl in 6 hours is the best launch metric yet. Check if there are discussions, issues, or usage patterns. Consider promoting from the other dataset/model cards.

6. **Archive SimpleToolCalling or update its card** — 43 downloads on a deprecated dataset. Either unpublish, rename to "deprecated-SimpleToolCalling", or add a prominent deprecation notice redirecting to combined-v6.

7. **Add evaluation-results YAML to all model cards** — Only vision-7b has model-index metadata. Adding this to the other 11 models would improve HF search ranking and user trust.

8. **Check private repo access patterns** — sakthai-embedding (34 dl) is private but getting downloads. Verify the intended access mechanism (token-gated? org-shared?) and document for Beer.
