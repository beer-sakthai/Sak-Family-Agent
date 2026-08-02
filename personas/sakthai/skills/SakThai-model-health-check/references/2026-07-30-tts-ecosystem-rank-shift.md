# Ecosystem Rank Shift: Score Changes Without Actual Growth

## Observed: 2026-07-30 TTS Cron Run

**Model:** `Nanthasit/sakthai-tts-model` (Kokoro TTS)
**Score change:** 38 → 43 (+5)
**Actual downloads/likes:** Unchanged (150/0)
**Cause:** Momentum rank shifted #12 → #6

## Mechanism

The momentum score is a blended average of:

```python
ratio_score = min(100, round(velocity / max_sibling_velocity * 100))  # speed vs fastest
rank_score = max(0, 100 - (velocity_rank - 1) * 10)                    # position
mom_score = round((ratio_score + rank_score) / 2)
```

Both inputs are relative to the author ecosystem, not absolute:

- **`max_sibling_velocity`** — when new models with 0 downloads/day enter, the max stays stable, so ratio_score is unchanged.
- **`velocity_rank`** — when new zero-download models enter, the active list grows. A model at rank #12 can become rank #6 simply because 6 models with 0 dl/day are now sorted below it.

## When This Happens

New models batch-pushed to HF arrive with 0 downloads. If a cron run lands between batch pushes, the rank shifts purely from a larger denominator of zero-velocity siblings.

## Impact Example

| Before (11 active siblings) | After (12 active + 6 new zeros) |
|---|---|
| rank #12 → rank_score = 0 | rank #6 → rank_score = 50 |
| mom = (41 + 0)/2 = 20 | mom = (41 + 50)/2 = 46 |

Overall score: +5 (20% weight on momentum improvement).

## Detection

Compare `delta.score_change` against `delta.downloads_change` in the YAML:

- Score up + downloads up → real growth
- Score up + downloads flat → ecosystem shift (neutral)
- Score up + downloads down → score masks decline (worst)
- Score flat + downloads flat → stable (normal)
