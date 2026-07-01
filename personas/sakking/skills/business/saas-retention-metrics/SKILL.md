---
name: saas-retention-metrics
title: SaaS Retention Metrics
description: Calculate and interpret NRR, GRR, logo churn, and expansion revenue for SaaS/ subscription businesses. Use when diagnosing growth quality, sizing expansion pipeline, building board KPI decks, or benchmarking against peers.
---

# SaaS Retention Metrics

## Trigger
- Board/investor reporting on revenue health
- Diagnosing why ARR is growing/shrinking despite same customer count
- Sizing expansion pipeline or upsell targets
- Benchmarking retention health (early-stage, Series A-D, bootstrapped)

---

## Step-by-Step Workflow

1. **Define cohort and period** — Choose a starting book-of-business (e.g., MRR at start of quarter). Use a consistent rolling or fixed cohort; rolling Standard SaaS cohort is easier for weekly reporting.
2. **Calculate Gross Retention (GRR / GDR)** — Revenue from the cohort excluding expansion, upsells, or add-ons.
3. **Calculate Expansion Revenue** — New revenue from that cohort during the period (upsells, add-ons, overages).
4. **Calculate Net Retention (NRR / NDR)** — GRR plus expansion, normalized to starting cohort revenue.
5. **Calculate Logo Churn** — Percentage of customers lost, independent of revenue changes.
6. **Segment** — Break all metrics by plan tier, ACV band, region, or acquisition channel to localize leaks and expansion pockets.

---

## Formulas

### Gross Revenue Retention (GRR)
`GRR = (Starting MRR - churned MRR - contraction MRR) / Starting MRR`

- Churned MRR = lost customers
- Contraction MRR = downgraded customers
- Does NOT include expansion

### Net Revenue Retention (NRR)
`NRR = (Starting MRR - churned MRR - contraction MRR + expansion MRR) / Starting MRR`

- Expansion MRR = upsells, add-ons, usage overages from the same cohort
- Also called NDR (Net Dollar Retention)

### Expansion Rate
`Expansion Rate = Expansion MRR / Starting MRR`

### Logo Churn
`Logo Churn = Count of lost customers / Count of customers at start`

### Quick sanity expansion ratio
`Expansion Ratio = Expansion MRR / churned MRR`  
Target > 1; healthy SaaS typically 1.3–4x.

---

## Benchmarks (Use as directional, not absolute)

| Stage / Type | GRR | NRR | Typical Expansion Ratio |
|---|---|---|---|
| Early-stage SaaS | 80–90% | 100–115% | 1.2–2.5x |
| Growth SaaS | 90–95% | 115–130% | 2.5–6x |
| Enterprise SaaS | 92–97% | 120–150%+ | 4–12x |
| Bootstrapped ($3M–$20M ARR) | 85–92% | ~104% median | 1.2–2x |

If NRR < 100%, growth is entirely dependent on new sales. If GRR < 85%, churn/loss is severe.

---

## Pitfalls

- **Cohort mismatch**: Mixing new-book and old-book customers in the same denominator inflates NRR.
- **Ignoring contraction**: GRR is often miscalculated by omitting downgrades.
- **Expansion recognition timing**: Record expansion in the period it bills, not when sold.
- **Logo churn lies**: Logo churn can look flat while revenue churn spikes if large accounts leave; always pair with dollar metrics.
- **Multi-product confusion**: If a customer buys a new product line, decide if it counts as expansion or new acquisition; be consistent.

---

## Verification Step

Reconcile the cohort formula to actual ARR movement in the billing system:

`Starting Cohort MRR`
`+ New MRR from cohort (expansion)`
`- Churned MRR`
`- Contraction MRR`
`= Ending Cohort MRR`

The Ending Cohort MRR must match what the billing system reports for that exact customer set. If not, classification errors exist.
