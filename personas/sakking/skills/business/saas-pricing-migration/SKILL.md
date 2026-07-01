---
name: saas-pricing-migration
description: Execute a staged pricing migration for existing SaaS customers when restructuring plans, tiers, or billing models. Covers pre-migration segmentation, grandfathering strategy, communication cadence, cohort sequencing, churn modeling, and post-rollout monitoring. Use when redesigning SaaS pricing, consolidating tiers, shifting from per-seat to usage-based, or when leadership decides to end grandfathering.
---

# SaaS Pricing Migration Playbook

## Trigger

Use this when:
- Redesigning pricing architecture (new tiers, value metrics, or billing units).
- Consolidating or sunsetting legacy plans/SKUs.
- Shifting existing customers from one billing model to another (e.g., per-seat → usage-based, flat-rate → tiered).
- Ending grandfathering for early adopters.
- Merging acquired customers into the parent company’s pricing stack.

Do NOT use for simple price increases on existing plans — use `saas-price-increase-execution-playbook` instead. Do NOT use for testing prices on new customers — use `saas-pricing-experiment-design`.

## Workflow

### 1. Audit and Segment Existing Customers
Pull a full customer list with:
- Current plan / SKU
- MRR/ARR
- Contract end date
- Usage depth (if applicable)
- Tenure (months since signup)
- Lifetime value to date

Segment into buckets:
- **Loyalists**: Low usage, high tenure, below-market ACV (will churn if moved).
- **Power users**: High usage, high value, likely to be price-sensitive but sticky.
- **Ghosts**: Very low engagement, easy to lose or cheap to keep.
- **Expansion-ready**: Undersized plan, headroom to grow into a higher tier.

### 2. Design Target Mapping Rules
For each legacy plan, define a target plan. Avoid “one-size-fits-all” mapping:
- Seat-based → Usage-based: map by historical average consumption + 20% buffer.
- Flat-rate → Tiered: map by feature usage signals, not just revenue.
- Consolidating SKUs: map to closest functional equivalent; if none exists, flag for human review.

Output: A mapping table with `from_plan → to_plan`, `price_delta`, and `features_delta`.

### 3. Choose Grandfathering Policy
Options:
- **Grandfather forever**: Safest, cleanest, but sacrifices margin expansion.
- **Grandfather + sunset**: Keep at renewal, 12–18 months before forced migration.
- **No grandfathering**: Highest risk, highest reward; requires exceptional communication.

Recommendation: Use **grandfather + sunset** for cohorts with >2 years tenure or >$50K ACV. Use **no grandfathering** for new cohorts and low-touch, low-ACV segments.

### 4. Model Revenue and Churn Impact
Compute before committing:

```
Migration Revenue Impact = Σ(Customer_Target_Price − Customer_Current_Price)
Churn Risk Uplift = Historical_Churn_Rate × Sensitivity_Multiplier
```

- **Sensitivity_Multiplier**: 1.0 for low-touch tiers, 1.5 for mid-market, 2.0+ for enterprise.
- **Expected Net Change** = Migration Revenue Impact − (Churn_Risk_Uplift × ARR_at_Risk)

Run a scatter sensitivity: 5% / 10% / 15% / 20% incremental churn on the at-risk cohort.

### 5. Build Communication Cadence
Sequence:
- **90 days before migration effective date**: High-value customers receive executive-level briefing.
- **60 days**: Product announcement + migration estimator tool shipped in-app.
- **30 days**: In-app prompts + email reminders + self-service migration path.
- **14 days**: Final notice + CSM outreach to at-risk accounts.
- **Effective date**: Auto-migration completes; billing adjusts on next invoice.

Copy principles:
- Lead with value (“You now get X feature included”).
- Never lead with cost increase.
- Show exactly what the new bill looks like.

### 6. Execute Staged Migration
Cohort sequencing (pick one primary axis):
- **By contract renewal date**: Migrate at renewal to avoid mid-term churn spikes.
- **By ACV**: Low ACV first, high ACV last (learn from small mistakes).
- **By product line**: Migrate one product at a time to contain support load.

Technical requirements:
- Create new plans/entitlements in the billing system *before* migration day.
- Build a “preview your new plan” sandbox in the product.
- Maintain a rollback window (7–14 days) for customers who hit errors.

### 7. Monitor Post-Rollout (30/60/90 Days)
Track:
- Migration completion rate by cohort.
- 30-day churn by pre-migration segment.
- Support ticket volume + topic clustering (billing confusion, missing features).
- ARPU migration gap: actual vs modeled.

### 8. Handle Exceptions and Appeals
Set guardrails:
- CS managers get a 10% discount authority for 30 days post-migration.
- Escalation path for >20% ACV customers.
- Pause migration if 30-day churn exceeds modeled upside by >50%.

---

## Formulas

- **Gross Migration Impact**: Total ARR uplift if zero customers churned.
- **Risk-Adjusted Impact**: Migration Impact × (1 − Projected_Churn_Uplift).
- **Migration Velocity**: `% of target accounts migrated / number of weeks since launch`.
- **Time-to-Migrate**: If staged by renewal, = weighted average days-to-renewal for unmigrated cohort.

## Pitfalls

- **Ripping the band-aid** on enterprise accounts: Churn risk outweighs margin gain.
- **Ignoring feature parity**: Customers forced into a cheaper-looking plan that lacks features they depend on will churn with prejudice.
- **Bad timing**: Migrating during budget season or a support crunch amplifies negative sentiment.
- **No self-service preview**: Customers flee when their first notice is an invoice they didn’t expect.
- **Cutting support capacity after launch**: The first 14 days determine whether the migration is an operational event or a PR problem.

## Verification

- **Pre-req check**: Mapping table signed off by Product, Finance, and Legal.
- **Run a pilot**: Migrate 1% of unmapped, low-ACV customers first; measure 14-day churn.
- **Acceptance criterion**: 30-day post-migration churn ≤ modeled upside (risk-adjusted) + 3 percentage points.
- **Business outcome**: If risk-adjusted upside is negative, abort or slide sunset date.
