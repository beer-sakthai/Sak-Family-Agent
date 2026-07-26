---
name: SakKing-b2b-pipeline-math-mql-to-close
title: B2B Pipeline Math MQL to Close
description: >
  Model the full B2B funnel from marketing-qualified lead to closed-won
  ARR. Covers conversion rates, required pipeline coverage, sales cycle
  length, ASP, and quota capacity. Use for go-to-market planning, budget
  setting, and board narrative.
triggers:
  - GTM planning
  - board metrics
  - quota and headcount planning
  - pipeline coverage reviews
  - marketing budget justification
---

# B2B Pipeline Math MQL to Close

## 1. The funnel identity

Every B2B company has a funnel identity. Know yours:

```
MQL → SQL → Opportunity → Demo/Pilot → Proposal → Closed-Won
```

Typical benchmarks (SaaS, mid-market):

| Metric | Median | Top quartile |
|---|---|---|
| MQL → SQL | 20-25% | 35%+ |
| SQL → Opp | 30-40% | 50%+ |
| Opp → Close | 15-25% | 30%+ |
| MQL → Close | 1-3% | 5%+ |
| Sales cycle | 60-120 days | <90 days |

## 2. Pipeline coverage

Pipeline coverage = **Total qualified pipeline / New ARR target**

| Stage of quarter | Minimum coverage |
|---|---|
| Start of quarter | 3.0-4.0× |
| Week 5 | 2.5× |
| Week 10 | 1.5× |

Use **segmented coverage** by stage for accuracy:

```
Coverage = (Commit × 0.85 + Best Case × 0.60 + Upside × 0.30) / Quota
```

## 3. Reverse-engineering the plan

If the target is $1M new ARR with a 20% win rate and $20k ASP:

```
Opportunities needed = $1M / ($20k × 0.20) = 250 opps
SQLs needed = 250 / 0.40 = 625 SQLs
MQLs needed = 625 / 0.25 = 2,500 MQLs
```

## 4. Capacity math

```
Reps needed = New ARR target / (Quota per rep × quota attainment %)

Example:
  Target = $1M
  Quota = $600k
  Attainment = 70%
  Reps needed = $1M / ($600k × 0.70) ≈ 2.4 → 3 reps
```

## 5. Lengthening sales cycle warning

If sales cycle increases by 30%, pipeline coverage needs to increase
proportionally because the same capital is tied up longer.

## 6. Common pitfalls

- Using one global conversion rate across segments.
- Counting unqualified pipeline to hit coverage targets.
- Ignoring churn when calculating net pipeline need.
- Treating pipeline as a marketing-only metric.

## 7. Board-ready output

| Metric | This quarter | Next quarter | Plan |
|---|---|---|---|
| New ARR target | $X | $Y | $Z |
| Qualified pipeline | $A | $B | $C |
| Coverage | A/X | B/Y | C/Z |
| Win rate | % | % | % |
| ASP | $ | $ | $ |
| Sales cycle | days | days | days |
| MQLs needed | # | # | # |

## 8. Verification

- Compare planned vs actual conversion rates monthly.
- Flag any stage with >20% month-over-month degradation.
- Validate coverage by AE, not just aggregate.
