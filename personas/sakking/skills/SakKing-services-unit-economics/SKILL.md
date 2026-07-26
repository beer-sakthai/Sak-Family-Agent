---
name: SakKing-services-unit-economics
title: Services & Agency Unit Economics
description: Analyze profitability for labor-driven businesses (agencies, consultancies, law, accounting, MSPs, studios) using utilization, realization, billable-rate multipliers, and a contribution-margin ladder. Use when pricing projects, sizing team capacity, diagnosing why revenue grows but margin shrinks, or benchmarking against professional-services peers.
---

# Services & Agency Unit Economics

## Trigger
- Pricing a new service line or retainer
- Diagnosing why revenue is up but net profit is down
- Setting annual billable targets for teams
- Evaluating an acquisition target or a potential acquisition
- Deciding whether to hire additional capacity vs. subcontract
- Budgeting headcount and overhead for the year

---

## Step-by-Step Workflow

1. **Define the unit** — Choose the atomic revenue unit (e.g., billable hour, project, retainer month, managed contract). Hour-based is most common for services.

2. **Map the margin ladder** — Build three contribution layers (CM1, CM2, CM3) to see where margin leaks. Do this at the service-line level, not company-level aggregates.

3. **Calculate productivity metrics** — Utilization, realization, and multiplier tell you whether margins are bleeding from capacity waste, discounting, or poor pricing.

4. **Benchmark against segment norms** — Compare against the right peer set (e.g., management consulting vs. creative agency vs. MSP).

5. **Model decisions** — Use the framework to pressure-test hiring, firing, pricing, and automation investments.

---

## Core Formulas

### 1. Billable Utilization Rate
`Utilization = (Billable Hours / Total Paid Hours) × 100`

- **Total Paid Hours** = salaried hours (typically 1,920–2,080 hrs per FTE/year)
- Not all firms bill 100%; bench time, sales support, and admin reduce this.
- Benchmarks:
  - Consulting / law: 65–80%
  - Creative / digital agency: 60–75%
  - MSP / implementation: 55–70%
  - Productized services (retainers): 70–85%

### 2. Realization Rate
`Realization = (Billed Revenue / Standard Revenue) × 100`

- **Standard Revenue** = `(Standard Rate × Billable Hours)`
- **Billed Revenue** = What actually hit the invoice after discounts, write-offs, or unbilled work.
- Benchmarks:
  - High-performing firms: 90–100%
  - Average firms: 75–90%
  - Below 70% means systemic discounting or scope creep.

### 3. Revenue per Billable Hour
`Effective Rate = Revenue / Billable Hours`

### 4. Loaded Cost per Billable Hour
`Loaded Cost = (Total Direct Labor Cost + Benefits + Payroll Tax) / (Total Paid Hours × Utilization %)`

### 5. Gross Margin (CM1)
`CM1 = Revenue - Direct Labor Cost - Subcontractor Cost - Delivery Tools/COGS`

`CM1 % = CM1 / Revenue`

- Benchmarks by type:
  - Software implementation: 40–55%
  - Strategy consulting: 50–65%
  - Creative agency: 35–50%
  - Managed services (MSP): 45–60%

### 6. Contribution Margin Ladder

| Layer | Formula | What It Captures |
|---|---|---|
| **CM1** | Revenue - Direct labor + subcontractors + delivery COGS | Purely delivery profitability |
| **CM2** | CM1 - Variable sales/marketing - implementation commissions - client onboarding | Profit after customer acquisition |
| **CM3** | CM2 - Allocated fixed overhead (rent, leadership, admin) | Profit before tax (EBITDA proxy) |

### 7. Salary Multiplier (Multiple on Cost)
`Multiplier = Billing Rate / Loaded Cost Rate`

- The number of times a client pays your direct cost.
- Benchmarks:
  - Management consulting: 3.0–5.0x
  - Law firms: 3.0–6.0x (equity partners see higher)
  - Digital agencies: 2.0–3.5x
  - Low-margin commoditized services: 1.2–1.8x

### 8. Break-Even Hours per Client
`Break-Even Hours = (Account Management Hours + Sales Cost + Onboarding Cost) / (Effective Rate × CM1 % - Hourly Delivery Cost)`

### 9. Profitability per Client (or Project)
`Profit = (Effective Hours × Effective Rate × CM1 %) - (Sales Cost + Onboarding Cost + CS/AM Cost)`

- Always calculate at the client/project level, not aggregate. Medium clients often hide margin destroyers.

---

## Pitfalls

- **Confusing utilization with profitability** — A 90% utilized team can still lose money if realization is 65% or rates are too low.
- **Ignoring non-billable selling time** — New-business development and relationship management hours should be allocated to a customer’s true economics.
- **Treating salary as fixed** — In services, direct labor *is* variable cost (it scales with delivery). Framing it as fixed overhead leads to bad expansion decisions.
- **Hidden COGS** — Forgetting delivery tools, licenses, subcontractors, overtime rates, and client travel. These kill CM1.
- **One client, one model** — A single large client with steep discounting can distort blended rates. Segment by price tier.
- **Overlooking realization** — Discounts at the invoice stage (not just rate card) are the #1 reason high-utilization firms have low margins.
- **Including overhead in CM1** — CM1 should only strip *direct* delivery costs. Overhead allocation belongs in CM2/CM3.

---

## Verification Step

Pick the most recent completed quarter. Build a **client-level P&L** with these columns:

1. Client revenue
2. Direct labor hours × loaded rate
3. Subcontractor spend
4. Delivery tools/COGS
5. CM1
6. Sales / onboarding amortization
7. CS/AM hours × loaded rate
8. CM2
9. Allocated overhead
10. CM3

Reconcile the sum of client-level CM3 to the company’s actual EBITDA before tax for that quarter. If the numbers don’t tie, a cost is either double-counted or sits in the wrong layer.
