---
name: customer-health-score-operational-framework
title: Customer Health Score Operational Framework
description: Build, validate, and operationalize a customer health score that predicts churn and expansion. Covers signal selection, weighted scoring, threshold playbooks, and CSM action triggers.
tags:
  - customer-success
  - churn-prevention
  - retention
  - metrics
  - csm
---

# Customer Health Score Operational Framework

## Trigger
- CSM team lacks a data-driven way to prioritize at-risk accounts
- Churn is rising but aggregate retention metrics still look healthy → need a leading indicator
- Product usage data exists but isn’t tied to retention outcomes
- Want to automate QBR prep and proactive outreach
- Board/investor asks for churn prevention metrics beyond lagging churn rate

---

## Step-by-Step Workflow

### 1. Map Outcomes to Signals
Pick signals that correlate with renewal, churn, or expansion in your historical data.

**Signal categories:**
- **Product engagement:** logins/week, active seats, feature adoption, API events, sessions per day
- **Financial health:** days to payment, invoice disputes, downgrade history, discount depth
- **Support health:** ticket volume, severity, CSAT/NPS/CSM score, response/resolution time
- **Contractual timing:** days to renewal, contract value, change in billing frequency

**Rule:** Cap at 8–10 signals. More than that collapses signal-to-noise and makes weighting impossible.

### 2. Define the Scoring Model
Two proven approaches:
- **Weighted sum:** score = Σ(weight_i × normalized_signal_i) — fast to launch, easy to explain.
- **Churn probability (logistic):** outputs 0–1 risk probability — more accurate once you have labeled churn data.

Start with weighted sum; migrate to probability once you have 12+ months of churn labels.

**Normalization:**
- **Min-max:** `(x - x_min) / (x_max - x_min)`
- **Z-score** if distribution is roughly normal
- **Inverse ratio** for "closer to bad" metrics (e.g., days to renewal: `1 - min_max(days)`)

Cap outliers at the 95th percentile to prevent a single abnormal week from tanking a score.

**Weights:** Derive from historical churn correlation, or initialize with equal weights and calibrate monthly. Example default weighting:
- Product engagement: 40%
- Support health: 25%
- Financial: 20%
- Contract timing: 15%

### 3. Set Thresholds and Buckets
Score range: 0–100.
- **Red (0–39):** High risk → escalate to CSM lead within 48h
- **Yellow (40–69):** At risk → CSM action plan within 7 days
- **Green (70–100):** Healthy → standard nurture, expansion outreach

Calibrate thresholds by overlaying historical churn rates. If the green bucket churns at >5%, raise the threshold. If red bucket churn is <2× baseline, lower it.

### 4. Build the Automation Pipeline
- **Ingest:** CRM (Salesforce/HubSpot), product analytics (Amplitude/Mixpanel), support (Zendesk), billing (Stripe/Chargebee)
- **Compute:** Weekly batch for most SaaS; daily for high-touch enterprise
- **Outputs:** per-account score, trend (Δ from prior period), top contributing risk factors, recommended CSM play

### 5. Tie to CSM Playbooks
**Red account:**
- Auto-create task: "Executive health review call within 48h"
- Highlight top 2–3 risk factors
- Suggest stack-ranked plays: onboarding refresher, usage training, executive business review, discount/payment review

**Yellow account:**
- Automated best-practice email or in-app guidance
- Flag for next QBR agenda

**Green account:**
- Expansion playbook: new feature trial, seat expansion offer, case-study invitation

### 6. Validate and Calibrate
**Monthly:**
- Precision = (# churned or downgraded in Red) / (# total in Red)
- Lift = (Churn rate in Red) / (Baseline churn rate)
- Target: precision ≥ 60%, lift ≥ 3×

**Quarterly:**
- Re-evaluate weights based on new correlation data
- Add or drop signals if predictive power drops
- Check for data drift (e.g., a feature launch changes engagement patterns)

---

## Formulas

### Weighted Sum Health Score
```
Score = [ Σ (w_i × norm(s_i)) ] × 100
```
Where:
- `w_i` = weight for signal i (sum of weights = 1)
- `norm(s_i)` = normalized value 0–1
- Result scaled to 0–100

### Min-Max Normalization
```
norm(x) = (x - x_min) / (x_max - x_min)
```
Use capped percentiles: set `x_min` to 1st percentile and `x_max` to 99th percentile to reduce outlier influence.

### Churn Probability (Logistic Regression)
```
p(churn) = 1 / (1 + e^( - (β₀ + β₁·x₁ + β₂·x₂ + ... ) ))
Health = (1 - p(churn)) × 100
```

### Precision and Lift
```
Precision = (# churned in Red bucket) / (# total in Red bucket)
Lift = Churn rate in Red bucket / Baseline churn rate
```

---

## Worked Example

**Company:** PLG SaaS, $50/mo, 5,000 customers.

**Signals & weights:**
| Signal | Weight | Direction |
|--------|--------|-----------|
| logins_last_14d | 0.25 | Higher = better |
| core_feature_used_last_7d | 0.20 | Higher = better |
| support_tickets_last_30d | 0.20 | Higher = worse (invert) |
| nps_score | 0.15 | Higher = better |
| days_past_due_invoice | 0.10 | Higher = worse (invert) |
| days_to_renewal | 0.10 | Closer = worse (inverse) |

**Customer values:**
- logins: 2 (min=0, max=20) → norm = 0.10
- core_feature: 0 → norm = 0.00
- tickets: 2 (min=0, max=5, cap) → invert: (5-2)/5 = 0.60 → norm = 0.60
- nps: 5 (min=0, max=10) → norm = 0.50
- days_past_due: 0 → norm = 0.00 (inverted = 1.00)
- days_to_renewal: 45 (min=0, max=90) → inverse norm = 0.50

Score = (0.25×0.10) + (0.20×0) + (0.20×0.60) + (0.15×0.50) + (0.10×1.00) + (0.10×0.50)
= 0.025 + 0 + 0.12 + 0.075 + 0.10 + 0.05 = **0.370 → 37.0 → Red**

---

## Pitfalls

| Pitfall | Why It Hurts | Fix |
|---------|--------------|-----|
| **Metric gaming** | Support or CSMs manipulate signal data to avoid "red" flags | Keep score internal; tie to process, not individual performance only |
| **Tenure blindness** | New accounts look identical to mature ones; zero usage may be expected early | Add tenure as a factor or segment weights by account age |
| **Seasonal usage mismatch** | Monthly-reporting customers look dead in weekly metrics | Align signal windows to actual customer usage cadence |
| **Ignoring nulls** | Missing NPS treated as zero scores healthy accounts down | Impute missing values with segment median, or exclude signal per account |
| **Static weights** | Product expansion or pricing changes shift drivers of churn | Revalidate weights quarterly using latest churn labels |
| **Threshold drift** | Changing customer mix makes original 0–39 red band inaccurate | Recalibrate buckets monthly based on actual churn distribution |

---

## Verification Step

1. **Backtest precision and lift:** Run the current model against the last 6 months. If precision < 50% or lift < 2×, recalibrate before wide rollout.
2. **Sanity check top-risk list:** The top 10% highest-risk accounts should contain ≥ 80% of accounts that churned in the last 30 days.
3. **Data reconciliation:** Sum of accounts in score output must equal total active customer count. Verify no duplicate account IDs and no missing billing-status fields.
