# health_score Key Divergence Across Schema Variants

Detected: 2026-07-30 (Health check on `sakthai-context-7b-merged`, suffix -4)
Repository: `sakthai-model-health-check`

## Problem

The `health_score` block uses **different key names** for the overall score depending on which schema variant generated the YAML. When a recurring cron job computes a delta against a previous file that used a different variant, the score extraction returns `None` (or 0), producing a misleading `score_change: 0` or a NaN in the report.

## The Two Key Names

| Variant | Score key | Component structure |
|---------|-----------|-------------------|
| **llm_cron** (canonical) | `health_score.final_score` | `health_score.components.{name}.{raw,weight,contribution}` |
| **Flat generator** (observed this session) | `health_score.overall` | `health_score.{popularity,momentum,...}` (flat values, no sub-objects) |

## Delta-Resilient Extraction Pattern

```python
def extract_score(data: dict) -> int | None:
    """Extract the overall health score from any schema variant."""
    hs = data.get('health_score', {}) or {}

    # Try both llm_cron and flat-generator key names
    score = hs.get('final_score') or hs.get('overall')
    if score is not None:
        return int(score)

    # Fall through to other schema variants
    score = data.get('assessment', {}).get('score')
    if score is not None:
        return int(score)

    score = data.get('health_check', {}).get('score')
    if score is not None:
        return int(score)

    # Raw weighted average (last resort)
    rw = hs.get('raw_weighted')
    if rw is not None:
        return round(rw)

    return None
```

## Detective Tips

When examining a previous health-check YAML, check which variant it uses:

```bash
grep -E "final_score|overall|raw_weighted" previous-health-check.yaml
```

- `final_score` → llm_cron variant (componentized)
- `overall` → flat generator variant
- `raw_weighted` → either; part of componentized structure
- None of the above → need to check `assessment.score` or `health_check.score`

## How to Prevent

When generating a new health-check for an llm_cron-schema model:

1. **Download the most recent previous health-check** for the same model
2. **Inspect its `health_score` structure** — uses `final_score` or `overall`?
3. **Match that structure** in the new YAML, don't invent a different one
4. If the model has NO prior health-check, use the canonical llm_cron structure (`final_score` + `components.*`)
