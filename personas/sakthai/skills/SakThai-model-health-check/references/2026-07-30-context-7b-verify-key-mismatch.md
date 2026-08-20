# Verify script `llm_cron` key mismatch — context-7b session

**Date:** 2026-07-30
**Models:** `sakthai-context-7b-merged`, siblings 0.5B and 1.5B
**Schema:** `llm_cron` (text-generation cron health-check)

## The problem

The `verify-health-check.py` script's `_get_identity_and_score` for `llm_cron` schema looked for `health_score.final_score`, but the generated YAML and the documented schema use `health_score.overall`. Result: the score printed as `assessment=0/100` even though the YAML had a correct overall score.

Similarly, `_get_metrics` read `target_model.downloads` exclusively, but the natural place for downloads is `repo_summary.downloads`. If `target_model.downloads` was absent (as in v1 of the YAML generator), the script got dl=0 and failed `DL_MISMATCH` when `expected_downloads` was passed.

## Fix applied

1. **`_get_identity_and_score`:** now checks `hs.get('overall')` first, falls back to `hs.get('final_score', 0)`
2. **`_get_metrics`:** now reads `dl = tm.get('downloads', 0) or rs.get('downloads', 0)` — checks target_model first, falls back to repo_summary

## YAML authoring lesson

When writing a health-check YAML for `llm_cron` schema, ensure:

- `target_model.id` — model identity string
- `target_model.downloads` — verified by `_get_metrics` (or at least `repo_summary.downloads` as fallback)
- `repo_summary.total_gb` — single source for file-size extraction (`_get_metrics` computes `int(total_gb * 1024**3)`)
- `health_score.overall` — used by `_get_identity_and_score` (preferred over `final_score`)

## Scenario

The 7B model had the largest weight file (15.23 GB) among the three context-model siblings but the fewest downloads (744 vs 1,370 for 0.5B and 1,599 for 1.5B). The YAML generator originally omitted `target_model.downloads` and `repo_summary.total_gb`, causing the verify script to return dl=0, size=0 and fail at step 4. Both keys had to be added in v2.
