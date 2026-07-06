---
name: SakKing-saas-growth-efficiency
title: SaaS Growth Efficiency Metrics — Burn Multiple, Magic Number, Rule of 40
description: |
  Diagnose capital efficiency and sales productivity using Burn Multiple, Magic Number, Efficiency Score, 
  Rule of 40, and ROSE. Use when fundraising, setting budgets, reallocating headcount spend, 
  diagnosing growth stalls, or benchmarking against public/private SaaS peers.
triggers:
  - "growth efficiency"
  - "burn multiple"
  - "magic number"
  - "Rule of 40"
  - "capital efficiency"
  - "sales efficiency"
  - "efficiency score"
  - "ROSE"
inputs:
  - Current and prior period ARR (or NRR)
  - Net burn (operating cash outflow) for same period
  - Sales and marketing spend (S&M)
  - Gross margin % (or CM1% for DTC but use gross margin for SaaS)
  - Prior period S&M for Magic Number back-calculation
  - Headcount and opex breakdown by function (R&D, G&A, S&M)
outputs:
  - Burn Multiple
  - Magic Number
  - Bessemer Efficiency Score
  - Rule of 40 %
  - ROSE (Revenue Operating Spend Efficiency)
  - Efficiency verdict (efficient, balanced, or burn-heavy)
  - Action list: trim, reinvest, or restructure
---

# SaaS Growth Efficiency Metrics

## Why this skill
Growth at any cost leaves cash on the table and scares investors. These metrics compress growth, spend, and profitability into single scores that force trade-off clarity. They work as a quarterly board report and as an operational warning system.

---

## Core Metrics and Formulas

### 1. Burn Multiple
Measures how much cash you burn to generate $1 of ARR growth.

```
Burn Multiple = Net Burn (period) / Net New ARR (period)
```

**Net Burn** = Total cash operating outflow (sum of S&M, R&D, G&A) minus any net cash from operations. Use the "Net Burn" from your P&L or cash flow statement.

**Net New ARR** = Ending ARR − Starting ARR (includes new, expansion, and churn-adjusted movement).

**What it means:**
- < 1.0: Elite efficiency (Bessemer standard)
- 1.0–1.5: Efficient growth, healthy
- 1.5–2.0: Acceptable if outperforming on retention/operating leverage
- > 2.0: Danger zone; capital is being converted to growth at an expensive rate

**Time window:** quarterly or annual. Always match Net Burn and ARR change to the same period.

---

### 2. Magic Number (Sales Efficiency)
Measures how efficiently S&M spend generates ARR, with a lag for customer decision cycles.

```
Magic Number = Net New ARR (quarter) / S&M Spend (prior quarter)
```

Use prior-quarter S&M because revenue from that spend often closes in the following quarter.

**Benchmarks:**
- < 0.7: Poor sales efficiency; rethink channel mix, ICP, or ICP fit
- 0.7–1.0: Below median; improve conversion or raise ACV
- > 1.0: Efficient; good ARR generation per dollar invested

Do NOT use if ARR growth is >50% quarter-over-quarter because the denominator is stale; discount the number.

---

### 3. Bessemer Efficiency Score
A normalized scoring system from 0–25+ that combines Margin Score (based on FCF margin or Rule of 40) and Growth Score (ARR growth %).

```
Efficiency Score = (FCF Margin × 1.5) + ARR Growth %

where FCF Margin = FCF / ARR
```

Simplified variant if you don’t have clean FCF:

```
Efficiency Score = (Gross Margin % × 1.5) + ARR Growth %
```

**Benchmarks (Bessemer):**
- 0–4: Struggling
- 4–16: On the fence
- 16–24: Good
- 25+: Elite

The ×1.5 weight on margin reflects the capital-efficiency premium investors place on profitability over pure growth.

---

### 4. Rule of 40
The classic SaaS health check: growth rate + profit margin should sum to ≥ 40%.

```
Rule of 40 % = ARR Growth % + EBITDA Margin %
```

If EBITDA margin is negative, use `+ (FCF Margin %)` or `+ (Gross Margin % − Opex % of ARR)`.

**Benchmarks:**
- 40–60: Healthy mid-growth
- 60–80: Strong, private flagship
- 80+: Exceptional (rare, often PE-backed or dominated)
- < 40 at scale (> $50M ARR): Warning sign; debate whether growth or margin is the constraint

Use this as the **board North Star** because it is intuitive and investor-standard.

---

### 5. ROSE — Revenue Operating Spend Efficiency
A forward-looking efficiency metric that compares net new ARR to total operating spend (not just sales).

```
ROSE = Net New ARR (quarter) / Total Opex (quarter)
```

Total Opex = S&M + R&D + G&A (all operating expenses).

**Benchmarks:**
- 0.15–0.25: Typical for growth-stage SaaS
- > 0.25: Exceptional
- < 0.10: Heavy burn relative to growth

ROSE is most useful when tracking whether each incremental hire or office expansion translates into proportional ARR growth.

---

## Step-by-Step Diagnostic Workflow

### 1. Pull aligned quarterly data
Collect:
- Starting ARR, Ending ARR, Net New ARR
- Net Burn (or total Opex)
- Prior-quarter S&M
- Gross Margin %, FCF (if available)
- R&D and G&A split

### 2. Compute the scorecard
Use the formulas above. Put all five metrics in a single table for trend analysis (rolling 4 quarters).

### 3. Classify the business phase
Use Burn Multiple + Rule of 40 to label the stage:

| Label | Burn Multiple | Rule of 40 | Typical ARR | Action |
|---|---|---|---|---|
| Efficient Growth | < 1.0 | 40–60+ | $1M–$30M | Accelerate top-of-funnel and expansion |
| Balanced Growth | 1.0–1.8 | 30–50 | $5M–$50M | Optimize CAC payback; avoid headcount bloat |
| Burn-Heavy Growth | > 1.8 | < 30 | < $10M or restructuring | Rationalize S&M, tighten hiring, fix pricing |
| Profitability Turn | Deteriorating | > 60+ | > $30M | Harvest value, prepare exit or strong balance sheet |

### 4. Drill into levers
If Burn Multiple > 1.5:
- Diagnose whether the problem is S&M efficiency (low Magic Number) or unit economics (low Gross Margin).
- If Magic Number is also low: renegotiate channel contracts, refine ICP, increase price, reduce free trial length, or cut low-converting campaigns.
- If Magic Number is fine but Gross Margin is low: fix hosting costs, support costs, or packaging to raise Gross Margin.

If Rule of 40 < 30 but ARR growth > 50%:
- You are in "growth at all costs." Decide explicitly whether investors support this profile or if you must raise Gross Margin to ≥ 70%+.

### 5. Set rolling targets
For the next quarter, assign one primary efficiency target per metric:
- "Cut Burn Multiple from 1.9 to 1.4 by reducing S&M spend by 15% and raising Average ACV by 10%"
- "Raise Magic Number from 0.8 to 1.0 by shifting $100K from LinkedIn to SEO/content"
- "Increase Gross Margin from 72% to 78% by migrating 60% of workloads to reserved infrastructure"

---

## Formulas cheat sheet

```
Burn Multiple            = Net Burn / Net New ARR
Magic Number             = Net New ARR (this quarter) / S&M (prior quarter)
Bessemer Efficiency      = (FCF Margin % × 1.5) + ARR Growth %
Rule of 40               = ARR Growth % + EBITDA Margin %
ROSE                     = Net New ARR / Total Opex
LTV:CAC                  = (CM3 or Gross Margin contribution per customer × expected lifetime) / CAC
CAC Payback (months)     = CAC / (CM3 per customer per month)
```

---

## Pitfalls

1. **Mixing time windows.** Burn Multiple requires Net Burn and Net New ARR from the same period. Magic Number intentionally uses prior-quarter S&M; do not confuse the two.
2. **Ignoring FCF vs. net burn.** Magic Number should use cash-basis S&M, not accrual. If S&M spend is paid out over time, use actual cash paid.
3. **Using ARR growth in hypergrowth.** If ARR growth is >60% quarterly, Magic Number and Burn Multiple are noisy. Shift focus to ROSE and Gross Margin trajectory.
4. **Treating Rule of 40 as a ceiling.** It is a floor. Strong private companies aim for 60+ during growth and 80+ before exit or IPO.
5. **Using blended Gross Margin.** If you sell to SMB, Mid-Market, and Enterprise, compute Gross Margin by segment. A 70% blended margin with 85% Enterprise and 60% SMB hides SMB margin problems.
6. **Leveraging ROSE without segmenting.** Moving headcount from R&D to S&M can improve ROSE temporarily while degrading product quality and long-term retention.
7. **Confusing CAC with S&M.** CAC includes sales compensation, tools, and overhead. S&M alone is a proxy, not the truth, especially in channel-led motions.

---

## Verification step

**The Quarterly Scorecard Reconciliation:**
For each metric, compute it two ways:
- **Top-down from P&L/CMS billing data** (ARR, Net Burn)
- **Bottom-up from campaign + headcount + cost data** (S&M, R&D, G&A)

If top-down and bottom-up differ by > 10%, find the reconciling item. Common culprits: capitalized S&M, refunds, contra-revenue, or deferred revenue timing. Fix the data model before using the metric for a decision.

**The Absurdity Check:**
If your Burn Multiple is < 0.5 while ARR growth is > 30%, verify that Net Burn is truly net (include stock-based expense and cash tied up in inventory or receivables if applicable). An unrealistically low Burn Multiple usually means SBC or working capital is being hidden.

---

## Integration with other skills

- **gtm-channel-mix-economics** — Use Magic Number to validate channel-mix decisions and force-budget high-efficiency channels.
- **saas-retention-metrics** — Pair NRR with Burn Multiple; a 110%+ NRR with a 1.8+ Burn Multiple may still be efficient if the company is pre-product-market-fit.
- **ecommerce-unit-economics** — Convert S&M to CAC and use CM3% instead of Gross Margin for blended DTC/PLG models.
- **b2b-pipeline-math-mql-to-close** — Use pipeline conversion data to forecast Net New ARR with confidence intervals before committing to S&M burn multiples.
- **saas-pricing-architecture** — Raise ACV immediately impacts Magic Number and Burn Multiple by increasing Net New ARR without new channel spend.
