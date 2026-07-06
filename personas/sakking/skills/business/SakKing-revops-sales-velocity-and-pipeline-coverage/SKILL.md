---
name: SakKing-revops-sales-velocity-and-pipeline-coverage
title: Sales Velocity & Pipeline Coverage
triggers:
  - Revenue forecasting and predictability gaps
  - Diagnosing why bookings are slipping despite "big pipeline"
  - Quota planning and SDR/AE activity targets
  - Weekly pipeline reviews and board revenue reads
  - Deciding whether to accelerate headcount or marketing spend
description: Measure and improve revenue predictability using sales velocity and pipeline coverage ratio. Use when forecasting revenue, diagnosing pipeline shortfalls, setting SDR/AE activity targets, or when leadership needs a defensible read on whether to accelerate hiring.
tags: [revops, sales, forecasting, pipeline]
related_skills: [SakKing-b2b-pipeline-math-mql-to-close, SakKing-gtm-channel-mix-economics]
---

# Sales Velocity & Pipeline Coverage

## Step-by-Step Workflow

### 1. Clean and segment the pipeline before any calculation
Garbage in, garbage out. Remove or downgrade:
- Opportunities with close dates older than 2× your average sales cycle.
- Duplicates and unqualified leads (no budget, authority, timeline, or pain).
- Discounted deals not yet approved (model them at list price unless approved).

**Action**: Segment pipeline by motion or ACV band (SMB / Mid-Market / Enterprise) and by CRM stage. Keep stage definitions consistent across the team.

### 2. Calculate sales velocity by segment
Sales velocity measures how fast a segment converts pipeline into revenue, expressed as revenue per day.

**Formula**:
```
Sales Velocity = (Number of Qualified Opportunities × Average Deal Size × Win Rate) / Sales Cycle Length (days)
```

**Example**:
- 50 qualified opps × $50K ACV × 25% win rate / 45-day cycle = $13,889/day
- Annualized run rate = $13,889 × 240 selling days = ~$3.3M ARR

**Benchmark**:
- B2B SaaS average: ~$8,200/day ($3M ARR equivalent).
- Sales-led motions usually 45–90 day cycles; PLG can be <14 days.

### 3. Calculate coverage ratio (standard and risk-adjusted)
Coverage tells you if your pipeline is big enough to hit quota given your conversion rate.

**Standard formula**:
```
Pipeline Coverage = Total Qualified Pipeline Value / Quota Target
```
- **Benchmark**: 3–4× for sales-led SaaS. If quota is $1M, you want $3–4M in qualified pipeline.

**Risk-adjusted formula** (more accurate for mixed win rates):
```
Required Raw Coverage = 1 / Win Rate
```
- If win rate = 20%, you need 5× quota in raw pipeline even if the "standard" rule says 3×.
- Use this when win rates are unusually low (<20%) or high (>40%).

**By-segment check**: If Enterprise win rate is 15% but SMB is 40%, don't blend them. Calculate coverage separately.

### 4. Diagnose the four levers of sales velocity
Velocity problems are rarely "sales is broken." They are usually one of four things:

| Lever | Formulaic driver | Common operational fix |
|-------|------------------|------------------------|
| **Opportunity count** | New opps/week per rep | Increase outbound, improve lead handoff, adjust prospecting quotas |
| **Average deal size** | ARPA of won deals | Repackage tiers, add enterprise modules, improve qualification (avoid small deals) |
| **Win rate** | Won / Closed-lost | Tighten MEDDIC/Champion checks, improve objection handling, focus on best-fit ICP |
| **Sales cycle** | Days from opp creation to close | Shorten legal/SOW cycles, compress proof-of-value steps, banish stalled deals sooner |

**Action**: Run a controller chart for each lever by rep and by segment for the trailing 6 months. The lever with the highest standard deviation or steepest decline is usually the one dragging velocity.

### 5. Forecast with stage-weighted reality
Don't confuse theoretical velocity with real forecasted revenue. The theoretical max assumes every opportunity closes at average deal size.

**Step**:
1. Assign close probabilities by stage (e.g., Discovery 10%, Demo 25%, Proposal 50%, Negotiation 75%, Closed-Won 100%).
2. Calculate **Weighted Pipeline** = Σ(Stage Value × Stage Probability).
3. Apply coverage logic: If Weighted Pipeline / Quota < 1, the gap is real.

**Quick sanity check**:
```
Forecast Coverage = Weighted Pipeline / Quota
```
- Target ≥ 1.0× (i.e., weighted pipeline meets or exceeds quota).
- If Forecast Coverage is 0.8× but raw coverage is 4×, your deals are stuck in early stages.

### 6. Set activity and hiring targets from the math
Use the operational math to translate revenue goals into field behavior.

**Example translation**:
- A rep needs $1M quota.
- Win rate = 25%, avg deal = $25K, cycle = 60 days.
- Required pipeline = $1M / 0.25 = $4M.
- Reps typically have 200 selling days/year.
- Deals needed per year = $4M / $25K = 160 deals.
- With 25% win rate, opps needed = 640 per year = 3.2 opps per selling day.
- If each rep can realistically create 1.5 opps/day, you need ~2.1 FTE per $1M quota, or adjust the model (larger deals, faster cycles, better win rate).

**Hiring trigger**: If required rep FTE > current headcount + planned attrition by >10%, start recruiting or increase marketing-sourced pipeline immediately.

## Formulas Cheat Sheet

| Metric | Formula | Benchmark / Usage |
|--------|---------|-------------------|
| Sales Velocity | (Opps × Avg Deal × Win Rate) / Sales Cycle (days) | $/day; compare across segments |
| Pipeline Coverage | Qualified Pipeline / Quota | 3–4× for sales-led |
| Risk-adjusted coverage | 1 / Win Rate | Use when win rate < 20% or > 40% |
| Weighted Pipeline | Σ(Stage Value × Stage Probability) | Forecast reality check |
| Forecast Coverage | Weighted Pipeline / Quota | ≥ 1.0× target |
| Opps needed per rep | (Quota / Avg Deal) / Win Rate | Top-of-funnel sourcing target |
| Deals needed per rep | Quota / Avg Deal | Activity planning baseline |

## Pitfalls

- **Inflated pipeline**: Counting every CRM stage as a dollar. A $500K pipeline with 80% of value in Discovery is not the same as $500K in Negotiation. Always blend stage-weighted probability.
- **Blended-segment blindness**: A 20% blended win rate hides that Enterprise is 12% and SMB is 45%. Run velocity and coverage by segment.
- **Ignoring new-rep ramp**: Reps hired in Q2 won't contribute full velocity until Q3/Q4. Don't divide annual quota evenly by headcount in year-one models.
- **Static cycle length**: Deals get longer in December and January, shorter in September/October. Use trailing-3-month average for cycle length, not annual.
- **Vanity metrics**: "We have $10M pipeline" means nothing if win rate is 10% and coverage is 1.5×. The math exposes this quickly; don't override it with anecdotes.
- **Discount creep**: If win rate improves because discounts rose, average deal size is falling. Track net deal size (ARPU after discount) separately.
- **Stage inflation**: Reps pushing deals to "Proposal" to show progress. Audit stage migration times weekly.

## Verification Step

**Weekly "Pipeline Health Check" — 5 minutes**

1. **Coverage sanity**: Is qualified pipeline ≥ 3× quota AND weighted pipeline ≥ 1.0× quota? If not, what is the dollar gap?
2. **Stale-deal scan**: Flag any opportunity with close date > 2× current average cycle and no activity in 14 days. Require recertification or archive.
3. **Stage migration audit**: Sample 10 deals that moved stages last week. Did the stage change reflect real buyer behavior or rep action? If >20% are "ghost stage pushes," retrain on stage definitions.
4. **Lever balance**: For any segment where velocity dropped >15% month-over-month, identify which of the four levers moved and by how much.
5. **Forecast lock**: Once per week, lock a forecast based on weighted pipeline, not rep "commitments." Variance analysis = last week's forecast vs. actual won pipeline movement.

If two or more segments fail Coverage + Weighted Pipeline checks in the same month, pause new hires and audit the top-of-funnel machine before adding more weight.
