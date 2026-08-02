# 2026-07-30 — Zero-Day Sibling in Health Check

## Scenario

`sakthai-context-1.5b-merged-v2` was created **the same day** as this health-check cron run (2026-07-30). It appeared in the sibling comparison with:

- **downloads: 0**
- **velocity: 0.0/day**
- **model-index: null** (no benchmarks published)
- **lastModified: null** (from author list API)
- **age_days: 0.5** (fresh upload)

## Impact on Scoring

### Popularity

Formula uses max sibling downloads as denominator:

```python
dl_score = min(100, round(downloads / max_sibling_downloads * 100))
```

A 0-download sibling doesn't shift `max_sibling_downloads` — the existing max (0.5B at 1370) remains. Result: **no scoring distortion**. The zero-day sibling is effectively invisible to the max-based formula.

### Momentum

Same logic for velocity ratio. The zero-day sibling's 0 velocity doesn't affect `max_sibling_velocity`. The blended rank score also ignores it naturally — it ranks at the bottom (#14 of 19).

### Benchmarks

`selection_accuracy: null` in sibling comparison section. No model-index means the `null` is correct and doesn't affect the target model's benchmark score.

## Lessons

1. **Zero-day siblings don't break scoring.** The max-based formulas naturally ignore them. No special-casing needed.
2. **`lastModified: null` is expected** for a model created the same day — the API hasn't populated it yet. Don't flag as an error.
3. **`selection_accuracy: null`** is correct when a sibling has no model-index. The YAML output should use literal `null`, not a sentinel like `0` or `unavailable`.
4. **Velocity rank** is unaffected — a 0-velocity model simply occupies the bottom ranks. The rank-based component (rank_score) correctly assigns it the minimum.
5. **Future runs will see this naturally** — as the v2 accumulates downloads and velocity, it'll eventually compete in the comparison. The scoring will smoothly transition.
