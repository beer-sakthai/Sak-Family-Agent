---
name: b2b-pipeline-math-mql-to-close
description: Build a B2B SaaS conversion model from MQL to SQL to Close with benchmarks, formulas, and variance checks. Use when forecasting revenue, diagnosing funnel bottlenecks, or setting conversion targets.
tags: pipeline, mql, sql, conversion, b2b-saas, metrics, forecasting
---

# B2B Pipeline Math: MQL → SQL → Close

## Trigger
When asked to:
- Model revenue from marketing and sales pipeline inputs
- Diagnose where deals leak in the funnel
- Set realistic conversion targets by channel
- Benchmark funnel health
- Build bottom-up budgets or Quota attainment plans

## Workflow
1. **Define stage criteria.** Agree on Marketing Qualified Lead (MQL) and Sales Qualified Lead (SQL) definitions with sales. Document what counts as a qualified opportunity and what counts as a win.
2. **Collect inputs.**
   - MQL volume by source (paid search, organic, webinars, outbound, etc.)
   - Historical conversion rates by stage
   - Average Contract Value (ACV) or deal size
   - Sales cycle length
   - Quota / revenue target
3. **Build the stage-to-stage model.**
   - Compute MQL→SQL rate
   - Compute SQL→Opportunity rate
   - Compute Opportunity→Close rate
   - Overall yield = MQL volume × product of stage rates = projected wins
   - Revenue projection = projected wins × ACV
4. **Layer in pipeline velocity.** Estimate how long leads sit in each stage to align timing with revenue recognition.
5. **Set targets.** Use recent benchmarks to set aggressive but plausible goals. Disaggregate by source because conversion varies.
6. **Validate monthly.** Backcast actuals to see if predicted MQL volume matches observed volume. Adjust stage rates and re-run.

## Formulas
```text
MQL → SQL rate   = SQLs / MQLs
SQL → Opp rate    = Opportunities / SQLs
Opp → Close rate  = Wins / Opportunities

Projected Wins    = MQLs × (MQL→SQL) × (SQL→Opp) × (Opp→Close)
Projected Revenue = Projected Wins × ACV

Pipeline Coverage = (SQL Value + Opportunity Value) / Quota
Recreation MQLs   = (Wins) / [(MQL→SQL) × (SQL→Opp) × (Opp→Close)]
```

## Benchmarks (2025–2026 approximate, from industry reports)
- **MQL → SQL:** 13–35% overall. Best-in-class target 15–20% with fast follow-up and clear criteria. By source: webinars ~25%, paid search ~18%, email outreach ~46%, organic ~51%. *Source snippets from Understory/Prospeo/Zeliq (2025–2026).*
- **SQL → Opportunity:** 30–50% when discovery is high quality.
- **Opportunity → Close:** 20–30%.
- **Pipeline coverage:** 3–4× quota for healthy SaaS businesses.

> **Caveat:** Benchmarks vary with ACV, sales motion (self-serve vs PLG vs high-touch), and follow-up speed. Use them to sanity-check, not as strict standards.

## Pitfalls
- **Aggregating all sources.** A 20% blended MQL→SQL hides that webinars may convert 25% while paid search converts 5%. Disaggregate by source to allocate budget rationally.
- **Ignoring lag.** MQLs convert to SQLs in days or weeks; SQLs to wins can take months. Model timing separately.
- **No sales-marketing SLA.** If marketing owns MQL quantity but not quality, and sales owns SQL→Close but not MQL→SQL, finger-pointing follows. Jointly own stage rates.
- **Moving MQLs without cleaning.** Duplicate or recycled leads inflate MQL counts and distort rates.
- **Static ACV.** Applying a single ACV across segments masks high-value and low-value deal differences. Segment by plan or channel when possible.
- **Target creep.** Raising MQL volume targets without fixing SQL→Close conversion just creates a bigger top-of-funnel burden.

## Verification Step
**Backcast test:** Take last month's sales results (wins, opportunity volume, SQL volume, MQL volume). Multiply backwards using your assumed stage rates from the current model. If the model predicts a materially different MQL volume than actually entered the pipeline, your model is missing leakage (e.g., leads going stale, duplicate recycling, or fast disqualification). Adjust rates or add a "stale" bucket until the backcast aligns within ~10%.

## Example
- **Inputs:** 1,000 MQLs, SQL→Opp 40%, Opp→Close 25%, ACV $10,000
- **MQL→SQL:** Let's assume 20% = 200 SQLs
- **SQL→Opp:** 200 × 40% = 80 Opps
- **Opp→Close:** 80 × 25% = 20 Wins
- **Revenue:** 20 × $10k = $200k
- **Pipeline coverage check:** If quota = $100k, need $300–400k in open SQL+Opp value. That's 30–40 open opportunities of $10k each.
