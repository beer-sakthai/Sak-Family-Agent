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

## Open Tasks (Consolidated in [`/PLAN.md`](../PLAN.md))

*(All 16 cards — 11 model + 4 dataset + profile — were rewritten and pushed on 2026-07-29, and `food-penguin-v1` model redirect stub was deleted.)*

- [ ] **Long-term call on private `Nanthasit/sakthai-embedding` (English)** — Keep private permanently (superseded by `sakthai-embedding-multilingual`) or publish a deprecation notice redirecting to `sakthai-embedding-multilingual`.
- [ ] **Automated promotion cron check** — Ensure no external promotion script overwrites the lean 11-model / 8-dataset / 3-Space card template on `sakthai-combined-v6`.
