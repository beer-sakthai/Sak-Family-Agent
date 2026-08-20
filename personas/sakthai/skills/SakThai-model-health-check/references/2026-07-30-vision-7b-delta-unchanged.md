# Vision-7b Health Check — Delta Unchanged (2026-07-30)

**Previous check:** `health-check-vision-7b-2026-07-30-v3.yaml` (from earlier same day)
**Current check:** `health-check-sakthai-vision-7b-2026-07-30-v4.yaml`

## Delta

| Field | Before | After | Δ |
|-------|--------|-------|---|
| downloads | 186 | 186 | — |
| likes | 1 | 1 | — |
| lastModified | 2026-07-30T21:46:34Z | 2026-07-30T21:54:38Z | +8 min (artifact upload) |
| author_model_count | 21 | 21 | — |
| velocity_rank | 4/21 | 4/21 | — |
| download_rank | 8/21 | 8/21 | — |
| health_score | 70 | 70 | — |
| demo_space | 404 | 404 | still broken |

## Changes Noticed

Tags grew from 21 → 29. New tags observed:
- `eval-results`, `endpoints_compatible`, `region:us`, `conversational`
- `arxiv:2310.03744` (LLaVA paper)
- `license:other`

These were likely added by a card-edit session or automated tag inference, not a model update.

## Notes

- No real change to model since last check — stable but idle.
- 5 health-check YAML artifacts in `.eval_results/` — consolidation candidate.
- Demo Space (`sakthai-vision-demo`) remains 404 across all 4 checks. This is the single highest-impact fix available.
