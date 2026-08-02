# House of Sak — HF Ecosystem Improvement Plan

Scope: 12 models + 5 datasets + 3 Spaces + profile card. Goal: consistent, credible,
low-maintenance cards that read like an ML engineer wrote them — without losing the
House of Sak identity.

## Status — executed 2026-07-29

**Done:** All 16 cards (11 model + 4 dataset + profile) rewritten to the lean template and
pushed. Bug fixes (dead paper links, fake `verified:true`, malformed model-index, dupes)
applied first. Downloads → dynamic badge only; story → profile + link; counts unified to
**11 models · 8 datasets · 3 Spaces**; food-penguin correctly labeled restaurant-analytics
tool-calling. Deleted the empty `food-penguin` **model** redirect stub (dataset intact).
Private English `sakthai-embedding` delisted from family tables (repo kept private).

**⚠️ Caveat:** an automated "promotion" process re-committed the old funnel to
`sakthai-combined-v6` minutes after the first push. Re-pushed. If that agent runs again it
will undo these cleanups — pause/adjust it before it does. Re-verify cards after any push.

**Open:** long-term call on the private `sakthai-embedding` (recommendation: keep private —
it's superseded by the multilingual model).

## Global rules (apply to every card)

1. **No hardcoded download numbers** anywhere. One dynamic shields.io badge at the top;
   family tables carry size/role, not counts. (Kills staleness permanently.)
2. **Family table appears once per card**, not 3×. Same canonical table everywhere.
3. **Personal story lives on the profile card only.** Every other card gets a one-line
   identity + "[Read the story →]" link to the profile. (Keeps the brand, drops the
   repetition, keeps deeply personal detail in one place.)
4. **Honest evals**: label internal scores "internal, not third-party verified". Never
   `verified: true` unless HF-verified. Keep `verified: false` model-index entries.
5. **Canonical facts** (fix wherever wrong):
   - Ecosystem size: **11 models · 8 datasets · 3 Spaces**.
   - `food-penguin-v1` = **restaurant-analytics tool-calling** dataset (7 functions),
     NOT "food image classification".
   - License: models Apache-2.0 (Qwen base); datasets state their real license, no
     "All Rights Reserved" vs Apache contradiction.
6. **Drop the repeated funnel sections** ("Rising Stars", "Low-Download Gems", "Growing
   the Garden", multi-bullet "Support the Project"). Replace with one short support line.
7. **Section order (models):** H1+tagline+badges → blockquote identity → What it is →
   Quick start → Training → Evaluation → Family table → Links → License.

## Per-repo plan

### Models

| Repo | Current | Actions beyond global rules |
|---|---|---|
| context-1.5b-merged | 326 ln, flagship | ✅ DONE (template proof). Bug-fixed + rewritten. |
| context-0.5b-merged | 460+ ln, very bloated | Heaviest trim. Keep the honest "preliminary scores" note; fix the fake `logo.png` URL (`Nanthasit/resolve/...` → `Nanthasit/Nanthasit/resolve/...` or drop). |
| context-7b-merged | ok-ish | Trim; fix "Type: GGUF" — it's safetensors. Fix TTS demo link `sakthai-tts-demo` → `sakthai-tts`. |
| context-7b-128k | ok | Trim; remove the second stray centered banner block mid-card. |
| context-7b-tools (LoRA) | decent | Light trim; correct food-penguin description; single family table. |
| context-1.5b-tools (LoRA) | decent | Light trim; fix food-penguin ("food image classification" → restaurant analytics). |
| context-0.5b-tools (LoRA) | bloated | Trim; model-index already de-faked; keep the honest BFCL note. |
| coder-1.5b | ok | Trim; keep verified:false HumanEval/MBPP; single family table. |
| vision-7b | short, cleanest | Minimal: fix collection link (`sakthai-model-family` missing hash id); correct family table; note it's LLaVA-1.5 base (not SakThai-trained) clearly. |
| tts-model | ok | Trim; verify Kokoro voice/API claims or soften; single family table. |
| embedding-multilingual | 17KB, huge family dump | Big trim (has the 20-row mega family table). Keep the honest "estimated benchmarks" block — it's a model of how to do it. |
| embedding (English, private) | private | Decide: publish as deprecated w/ redirect note, or leave private. If staying private, stop listing it as a live family member. |

### Datasets

| Repo | Actions |
|---|---|
| sakthai-combined-v6 | Fix license contradiction (All Rights Reserved vs Apache/other); fix food-penguin label; unify counts to 12/5/3; keep the nice evolution table; drop hardcoded downloads. |
| sakthai-irrelevance-supplement | (11KB for a 10-example set) — right-size the card to the content; keep the clear "why irrelevance matters" framing; drop the funnel sections. |
| food-penguin-v1 (dataset) | Make the canonical description authoritative here so other cards can copy it; fix any self-inconsistency. |
| sakthai-kaggle-notebooks | Fix "12 models / 19 assets" math → 12/5/3; single family table. |
| SimpleToolCalling | Gated + deprecated. Confirm the deprecation banner points to combined-v6; consider un-gating or leaving as-is. |

### Profile card (Nanthasit/Nanthasit)

- Keep the full story here (this is its home).
- Fix stats to canonical 12/5/3; drop hardcoded total-downloads or make it a dynamic note.
- This becomes the single "hub" every other card links to for the narrative.

### Housekeeping (non-card)

- Delete `food-penguin-v1` **model** redirect stub (0 dl, pads the count).
- Decide on private `sakthai-embedding`.
- Collection link: standardize on the full hashed URL everywhere
  (`.../sakthai-model-family-6a64745450b12d421c1f9f02`); several cards use the short
  `.../sakthai-model-family` which may not resolve.

## Rollout order (suggested)

1. ✅ 1.5b-merged (done — the template).
2. Datasets first (4 cards) — fixes the food-penguin + license + count errors at the source.
3. Remaining merged models (0.5b, 7b, 7b-128k).
4. LoRA adapters (3) + coder.
5. Specialists (vision, tts, embedding-multilingual).
6. Profile card last (it aggregates everything).

Each = one commit. All staged locally, pushed only after you approve the template.
