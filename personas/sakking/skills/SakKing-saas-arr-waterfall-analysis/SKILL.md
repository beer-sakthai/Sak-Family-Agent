---
name: SakKing-saas-arr-waterfall-analysis
version: 1.0.0
description: "Build monthly or quarterly ARR waterfalls showing exactly how ARR moved from period-open to period-close, decomposed into New, Reactivation, Expansion, Contraction, and Churn. Use when the board asks why ARR grew/lagged, when NRR looks wrong, or when building board-bridge slides."
trigger: "Board or investor asks for ARR bridge/waterfall; NRR off target and you need to find the leak; you need to decompose quarterly ARR movement into actionable buckets."
inputs: "Beginning ARR, Ending ARR, by-customer ARR snapshots."
outputs: "Waterfall table, bucket deltas with pct of beginning, and 60-second explain narrative."
---

## ARR Waterfall Definition

ARR Waterfall tracks absolute dollar movement between two ARR snapshots: "If we started at $X, what exactly happened to reach $Y?"

## Standard Buckets (Do Not Repurpose)

- **New**: ARR from net-new logos signed in period. SUM(ARR) where pre-ARR == 0 and post-ARR > 0.
- **Reactivation**: ARR won back from previously churned customers. SUM(ARR) where pre-ARR == 0 and prior-pre-ARR > 0.
- **Expansion**: Uptick from existing customers. SUM(delta) where pre-ARR > 0 and post-ARR > pre-ARR.
- **Contraction**: Downtick (still paying). SUM(abs(delta)) where pre-ARR > 0 and 0 < post-ARR < pre-ARR.
- **Churn**: Full ARR loss. SUM(pre-ARR) where pre-ARR > 0 and post-ARR == 0.

Net movement = New + Reactivation + Expansion - Contraction - Churn = Ending - Beginning.

## Step-by-Step Workflow

### 1. Snapshot ARR twice
Export ARR by customer at period-open and period-close. Calculate ARR as MRR * 12 (monthly) or committed contract value (multi-year). Snapshots must align to end-of-period convention -- pick one and stick to it.

### 2. Classify customer delta
Join snapshots on customer ID. Priority order:
1. `pre == 0 and post > 0 and pre-previous > 0` -> Reactivation
2. `pre == 0 and post > 0` -> New
3. `pre > 0 and post == 0` -> Churn
4. `post > pre` -> Expansion
5. `0 < post < pre` -> Contraction
6. `pre == post` -> No change (ignore)

### 3. Sum by bucket and verify identity
Hard check: `New + Reactivation + Expansion - Contraction - Churn` must equal `Ending - Beginning` within $0.01. If not:
- Orphaned records (customer in only one snapshot)
- Odd-churn edge-case (pro-rated months across boundary)
- Data-quality bug

Do not present unless it ties.

### 4. Compute derivatives
- New ARR % = New / Beginning
- Retention Rate = (Beginning - Churn) / Beginning
- Churn Rate = Churn / Beginning
- Expansion Rate = Expansion / Beginning
- Net ARR Growth Rate = (Ending - Beginning) / Beginning
- Gross Retention Rate = (Beginning - Churn + Expansion) / Beginning
- NDR proxy = (Ending - Beginning + Churn) / Beginning

### 5. Draft the 60-second narrative
"We opened at `$X`. Added `$Y` in new ARR `(+pct)`, reactivated `$Z`, expanded existing by `$E`. Lost `$F` to churn and `$G` to contractions. Net: `$End` (`+N/N pct`), driven by [New/Expansion] with churn at `X.x pct` -- [inline/above/below] plan."

## Visual Presentation

| Bucket | $M | pct Begin | Cumulative |
|---|---|---|---|
| Beginning ARR | -- | -- | $7.2 |
| New | +1.1 | +15.3 pct | $8.3 |
| Reactivation | +0.1 | +1.4 pct | $8.4 |
| Expansion | +0.6 | +8.3 pct | $9.0 |
| Contraction | (0.2) | (2.8 pct) | $8.8 |
| Churn | (0.5) | (6.9 pct) | $8.3 |
| Ending ARR | -- | -- | $8.3 |
| Net Growth | +1.1 | +15.3 pct | -- |

## Formulas and Edge Cases
- **Pro-rated churn**: Use full pre-churn ARR in Churn bucket if snapshot is end-of-month. Flag mid-period churns separately if you want to exclude honoring-month distortion.
- **Multi-year contracts**: Expansion mid-term is full delta in period of change. Multi-year churn goes to Churn at renewal.
- **Reactivations**: Do NOT double-count as both Churn and New. Use 3-month grace window.
- **Contract start timing**: Committed-value-as-signed captures in Month 1; earned-start captures in Month 2. Be consistent.

## Pitfalls
1. Deriving NRR without definition check. NRR = `(Ending - New) / Beginning` if you exclude new business. Label the lens.
2. Forgetting reactivations. Omitting reactivations distorts historic churn.
3. Comparing across months with cohort bias (enterprise deals vary; Q4 outpaces Q3 from comp cycles). Always annotate seasonality.
4. Percentages that do not sum constructively. Either use pct of Beginning or pct of Ending -- do not blender them.
5. Mixing billings and ARR. ARR is committed future revenue. Billings is cash. Keep them separate.

## Verification Step
Before sharing, run:
1. `ending == beginning + sum(all buckets)` -- exact match required.
2. `churn_rate` and `expansion_rate` vs. standardized metrics -- flag drift > 0.2 pct.
3. Anomaly sweep:
   - Single customer > 20 pct of any drift bucket? Flag as key account, investigate structural vs transient.
   - Any bucket > 50 pct of total net change? Verify data import vs real event.
   - Does `(beginning - churn + expansion) / beginning` match reported GRR within 0.1 pct? If not, definition mismatch -- fix before board deck.

## Example
Beginning ARR = $10.0M:
- New +1.2
- Reactivation +0.1
- Expansion +0.8
- Contraction (0.3)
- Churn (0.5)
- Ending $11.3

Net growth = 1.2 + 0.1 + 0.8 - 0.3 - 0.5 = 1.3 = $11.3 - $10.0. Verified.
NDR check = (10.0 - 0.5 + 0.8) / 10.0 = 103 pct.

## Related Skills
- Cohort-level retention curves: use `cohort-analysis-operational-framework`
- NRR decomposition by expansion type: use `saas-expansion-revenue-decomposition`
- Full board pack narrative: use `board-deck-kpi-narrative-framing`
