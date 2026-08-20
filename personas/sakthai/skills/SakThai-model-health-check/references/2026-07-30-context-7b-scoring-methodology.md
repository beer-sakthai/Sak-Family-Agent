# Context 7B Scoring Methodology Refinement — 2026-07-30

## What changed

The Health Score Breakdown section was updated with concrete Python formulas for each component. Previously it only listed components and weights without specifying HOW to compute each score. This session validated the formulas on `sakthai-context-7b-merged`.

## Key decisions in formula design

### Popularity: downloads vs likes weighting
Downloads (70%) dominate over likes (30%). Rationale: likes are rare for new models — zero likes after 24 days is common, not a signal of poor quality. The max-sibling baseline for downloads keeps scoring relative rather than absolute.

### Momentum: blended ratio + rank
Pure ratio (`velocity / max_sibling_velocity * 100`) unfairly penalizes the slowest model in a fast-growing family. Pure rank (`100 - (rank-1)*10`) over-rewards models in small families. The arithmetic mean of both is more stable and produces intuitively reasonable scores (~54 for #5/19 at 30.3/d).

Velocity rank uses ALL author models, not just siblings. Compute fresh each run since new models shift ranks.

### Benchmark scoring tiers
- 0: no model-index at all
- 40: 1-2 unverified metrics (most common for new models)
- 60: 3+ unverified metrics
- 100: all verified (on leaderboard)
- +20 bonus for Open LLM Leaderboard submission

## Session results

| Model | Score | Pop | Mom | Bench | Card | Hyg |
|-------|:----:|:---:|:---:|:-----:|:----:|:---:|
| context-7b-merged | **58** | 33 | 54 | 40 | 80 | 100 |

## Scoring script template

```python
# After loading all data:
max_sib_dl = max(s['downloads'] for s in siblings_data.values())
max_sib_vel = max(s['velocity'] for s in siblings_data.values())

dl_score = min(100, round(downloads / max_sib_dl * 100))
likes_score = min(100, likes * 10)
pop_score = round(dl_score * 0.7 + likes_score * 0.3)

ratio_score = min(100, round(velocity / max_sib_vel * 100))
rank_score = max(0, 100 - (vel_rank - 1) * 10)
mom_score = round((ratio_score + rank_score) / 2)

# Benchmarks
bch_score = 40 if has_model_index else 0
if all_verified: bch_score = 100
elif metric_count >= 3: bch_score = 60

# Card quality
card_score = 100
# ... apply deductions ...

# Repo hygiene
hyg_score = 100
# ... apply deductions ...

overall = min(100, round(pop_score*0.20 + mom_score*0.20 + bch_score*0.25 + card_score*0.20 + hyg_score*0.15))
```
