---
name: saas-sales-comp-plan-design
title: SaaS Sales Compensation Plan Design
description: >
  Design, audit, or optimize sales compensation plans for SaaS roles (SDR, AE, AM, CSM).
  Covers OTE setting, pay-mix benchmarks, back-calculated quota design, ramp schedules,
  accelerators/caps, and quota attainment realism checks. Use when hiring quota-carrying
  roles, designing a new comp plan, diagnosing over/under-spend on sales headcount,
  or aligning incentives with GTM motion.
triggers:
  - "design sales comp plan"
  - "SDR quota"
  - "AE OTE"
  - "sales compensation"
  - "on-target earnings"
  - "ramp plan"
  - "commission accelerator"
  - "quota setting formula"
  - "pay mix"
tags:
  - business
  - sales
  - compensation
  - GTM
  - SaaS
  - operations
---

# SaaS Sales Compensation Plan Design

## Core Precept

**Comp is a system, not a spreadsheet.** If you set quotas without back-calculating from realistic funnel math, you get turnover, sandbagging, and misaligned incentives. A well-designed plan links activity quotas to revenue outcomes, respects ramp time, and protects margin while motivating top performers.

---

## Step 1 — Lock the Role, OTE, and Pay Mix

### Role Definitions
| Role | Primary Metric | Typical ACV Band | Typical Ramp to Full Quota |
|------|---------------|------------------|----------------------------|
| **SDR** | Pipeline/SQLs created | Any | 90–150 days |
| **AE** (inside) | Closed ARR | <$25K | 90–180 days |
| **AE** (enterprise) | Closed ARR | >$50K | 180–270 days |
| **AM** | Expansion/retention ARR | Any | 90–120 days |
| **CSM** | Renewal/NRR | Any | 60–90 days |

### OTE Benchmarks (US, 2025–2026)
| Role | Median OTE Range |
|------|------------------|
| SDR (B2B SaaS) | $50K–$80K |
| Inside AE | $80K–$120K |
| Enterprise AE | $150K–$300K+ |
| AM | $70K–$110K |
| CSM | $60K–$90K |

### Pay Mix (Base : Variable)
- **SDR**: 70/30 to 80/20 (higher base because activity-based; variable often tied to meetings/SQLs)
- **AE**: 50/50 to 60/40 (higher variable because quota-carrying)
- **AM**: 60/40 to 70/30 (retention-focused, lower variable)
- **CSM**: 70/30 to 75/25 (retention/NRR variable)

**Rule**: If more than 30% of SDRs are hitting accelerator thresholds, your quotas are likely too low.

---

## Step 2 — Back-Calculate Quota from Funnel Math

Never set quota top-down without verifying the activity funnel supports it.

### The Backward Chain
```
Annual Revenue Target
    ÷ ACV (Average Contract Value)
    = Number of Closed/Won Deals
    ÷ Close Rate (Opportunity → Win)
    = Number of Qualified Opportunities Needed
    ÷ SQL Rate (Sourced → SQL)
    = Number of SQLs Needed
    ÷ Meeting/Activity Conversion Rate
    = Total Activities Required (calls, emails, touches)
```

### Worked Example: SDR Quota Design
- **Revenue target**: $1.2M new ARR (SDR team of 4)
- **ACV**: $15K
- **Close rate**: 10% (industry typical for SDR-sourced pipeline)
- **SDR opportunity quota**: $300K per SDR annually

```
$300,000 quota / $15,000 ACV = 20 deals
20 deals ÷ 10% close rate = 200 opportunities needed
200 opportunities ÷ 5% activity-to-opportunity rate = 4,000 activities/year
4,000 ÷ 250 working days ≈ 16 activities/day (calls + emails + touches)
```

**Validation check**: If 16 activities/day is unrealistic for your ICP and channel, the quota is too high.

### SDR Quota Formats
1. **Revenue quota**: $300K pipeline generated
2. **Opportunity quota**: 200 qualified opportunities/year
3. **Meeting quota**: 160 qualified meetings/year (if SDR owns scheduling)

**Best practice**: Attach variable pay to the metric the rep controls. SDRs can't guarantee revenue—they can guarantee meetings or pipelines.

---

## Step 3 — Design Accelerators and Caps

### Standard Accelerator Structure
| Performance Tier | Commission Rate | Rationale |
|------------------|-----------------|-----------|
| 0%–99% of quota | 1x rate | Standard earnings at target |
| 100%–125% of quota | 1.5x rate | Incentivize overachievement |
| >125% of quota | 2x rate or uncapped | Rewards top performers; prevents sandbagging |

### Cap Policy
- **Cap AEs at 150% commission** unless they are strategic key accounts (unlimited on named logos).
- **Never cap SDRs**—they are bounded by their activity funnel anyway, and caps discourage high performers from closing extra deals.

### Bonus Types by Role
| Role | Typical Bonus Metric | Frequency |
|------|---------------------|-----------|
| SDR | Meetings booked, SQLs delivered, pipeline generated | Monthly or Quarterly |
| AE | Closed ARR | Quarterly |
| AM | Expansion ARR, retention rate | Quarterly or Semi-annual |
| CSM | NRR/GRR, churn rate | Quarterly or Semi-annual |

---

## Step 4 — Build the Ramp Plan

### Ramp Structure (Standard 30/60/90/120-Day Model)
| Period | Quota Setting | Acceleration / Protection |
|--------|---------------|---------------------------|
| Days 1–30 | 0% quota (training only) | Base salary only |
| Days 31–60 | 25% of full quota | Base + partial commission |
| Days 61–90 | 50% of full quota | Base + partial commission |
| Days 91–120 | 75% of full quota | Full commission |
| Day 121+ | 100% of full quota | Full commission + accelerators |

**Key ramp benchmarks**:
- Time to first deal: ≤60 days
- Time to full quota: ≤120–150 days (SDR), ≤180–210 days (AE)
- SDRs need ~7,000 activities before the first deal (training + ramp combined)

### Ramp Design Rules
1. **Extend ramp for enterprise AEs** (>$50K ACV): 180–270 days is normal.
2. **Include a draw** for AEs in ramp: guarantee base + partial commission if they're hitting activity targets but close rates are low.
3. **Track ramp attainment monthly**: If a rep hits <50% of their ramp quota at day 90, evaluate performance plan.

---

## Step 5 — Validate Plan Feasibility

### The "Kill Test" for Overly Aggressive Quotas
For any new quota:
1. Compute required activities per day.
2. Benchmark against industry averages (SDR: 50–100 touches/day in high-velocity motions; AEs: 8–15 meaningful conversations/week in enterprise).
3. If the activity number exceeds realistic capacity by >20%, lower ACV, improve conversion, or add headcount before hiring.

### Pipeline Coverage Reality Check
- **Target**: 3x–5x pipeline in the rep's territory/segment at the start of each quarter.
- If pipeline coverage <3x, the quota is unattainable regardless of rep performance.

### Comp Plan Cost as % of Revenue
| Role | Typical Comp as % of New ARR |
|------|------------------------------|
| SDR | 8%–12% |
| AE | 15%–25% |
| AM | 5%–10% |
| CSM | 5%–8% |

**Total S&M cost** (including tools, management, overhead) should be 35%–50% of new ARR for Series A+ SaaS.

---

## Step 6 — Common Pitfalls and Fixes

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| **Quota set from revenue top-down without funnel check** | 90% of reps miss quota despite working hard. | Back-calculate quota from realistic activity/close rates. |
| **No accelerators** | Top 20% of reps leave within 12 months. | Add 1.5x at 100%+ and 2x at 125%+. |
| **Variable pay too high for SDRs** | 40%+ churn in first 90 days. | Increase base to 75–80% of OTE. |
| **Ignoring ramp in annual budget** | Q1 pipeline misses, leadership panics. | Budget 50% of ramp-quota for Q1 new hires. |
| **Single metric quota** | Reps game the metric (e.g., SDRs book bad meetings). | Blend 2–3 metrics (meetings × SQL quality score). |
| **Caps on hunters** | Reps close deals early and coast. | Uncap AEs or raise cap to 150%+. |
| **Same plan across segments** | Enterprise AEs struggle, inside AEs are overpaid. | Segment comp plans by ACV tier and motion. |

---

## Formulas Cheat Sheet

```
Backward Quota Chain:
  Revenue Target
    ÷ ACV = Deals Needed
    ÷ Win Rate = Opportunities Needed
    ÷ SQL Rate = SQLs Needed
    ÷ Activity Conversion Rate = Activities Needed

OTE = Base Salary + (Variable Target × Achievement %)
  Variable Target = Annual Quota × Commission Rate

Pipeline Coverage = Quarter-Begin Pipeline / Quarterly Quota
  Target: 3x–5x

Comp as % of New ARR = (Base + Variable Paid) / New ARR

Draw Amount = (Base + Expected Variable) × Draw % (for ramp support)
```

### Commission Rate Benchmarks
| Role | Typical Variable Rate |
|------|----------------------|
| SDR | 5%–8% of pipeline generated |
| Inside AE | 8%–12% of closed ARR |
| Enterprise AE | 5%–8% of closed ARR |
| AM | 3%–5% of expansion ARR |
| CSM | 5%–10% of retention/upsell ARR |

---

## Step 7 — One-Page Plan Card Template

Build this for every role in the plan:

```
Role: SDR
OTE: $65,000 | Base: $52,000 (80%) | Variable: $13,000 (20%)
Quota: $300,000 pipeline / 200 opportunities / 160 meetings
Accelerator: 1.5x at 100%, 2x at 125%
Ramp: Days 1-30 0%, D31-60 25%, D61-90 50%, D91-120 75%, Day121+ 100%
Minimum KPI for HR review: <80% of ramp quota at Day 90
```

---

## Verification Step

Before launching a new comp plan, run these checks:
- [ ] **Funnel math passes**: Required activities/day is within realistic range for the role and channel.
- [ ] **Coverage check**: Team pipeline >3x quarterly quota.
- [ ] **Margin check**: Total comp cost + S&M overhead < 50% of new ARR.
- [ ] **Ramp check**: Budget accounts for 50% ramp load in Q1 of hiring.
- [ ] **Accelerator check**: Top 20% of reps can earn ≥150% of OTE at 150% attainment.
- [ ] **Cap check**: Cap is noted only where explicitly required (rare).

If any check fails, revise before hiring.

---

## Integration with Other Skills

- Use **revops-sales-velocity-and-pipeline-coverage** to size pipeline and check coverage.
- Use **b2b-pipeline-math-mql-to-close** to set conversion rates in back-calculations.
- Use **land-and-expand-playbook** to design AM/CSM expansion incentives.
- Use **board-deck-kpi-narrative-framing** when presenting comp plan changes to the board.
