---
name: saas-pricing-conjoint-analysis
description: >
  Design, field, and interpret a choice-based conjoint (CBC) study to
  quantify feature value, willingness-to-pay, and price elasticity for
  SaaS pricing decisions. Use when redesigning tiers, validating WTP for
  a premium feature, choosing between per-seat vs. usage-based pricing,
  segmenting customers by price sensitivity, or when Van Westendorp gives
  an acceptable price range but you need feature-level trade-off data.
  This skill produces part-worth utilities, attribute importance scores,
  WTP estimates, and market-share simulations to support data-driven
  pricing.
triggers:
  - "pricing research beyond Van Westendorp"
  - "feature valuation for SaaS"
  - "price elasticity by segment"
  - "how to design a pricing survey"
  - "choice-based conjoint for subscription pricing"
tags:
  - pricing
  - saas
  - market-research
  - monetization
  - pricing-research
---

# SaaS Pricing Conjoint Analysis — Operational Skill

## When to Use This Skill

- Launching or redesigning a tiered pricing structure where feature trade-offs matter (e.g., "Do buyers value SSO more than 5 additional users?")
- Quantifying WTP for a specific premium module, add-on, or consumption cap
- Choosing between fundamentally different value metrics (per-seat vs. usage-based vs. flat fee)
- Segmenting target audiences by price sensitivity to inform packaging (e.g., SMB vs. mid-market vs. enterprise)
- Validating whether an intended price increase is supportable by product features
- Building a pricing business case for investors who demand feature-level value evidence

Do NOT use this when:
- You only need an initial price range and don't care about feature trade-offs (use `van-westendorp-price-research` instead)
- You are testing a minor price tweak in production (use `saas-pricing-experiment-design`)
- You are optimizing usage-based metering or B2B deal structures (see `usage-based-pricing-bill-shock-prevention` or `b2b-deal-packaging-and-pro-pricing`)

## Core Concept

Choice-Based Conjoint (CBC) asks respondents to choose between multiple product concepts, each defined by a specific combination of **attributes** (features, limits, support level) at different **levels**, with price as one of the attributes.

Statistical modeling (typically Hierarchical Bayes or multinomial logit) estimates **part-worth utilities** — the relative value buyers assign to each attribute level. From these utilities, you can compute:

| Output | What It Answers |
|--------|-----------------|
| **Attribute Importance** | Which features actually drive choice? (e.g., "SSO is 2× more important than 100 extra seats") |
| **Willingness-to-Pay (WTP)** | How much will buyers pay to add feature X or switch from Basic to Pro? |
| **Price Elasticity** | How does simulated market share change if price moves ±20%? |
| **Market Simulation** | What share of demand would a candidate tier structure capture vs. the current offering? |

---

## Step 1 — Scope the Study

### Define the research objective
Write a single sentence: *"We need to know which tier structure and price points maximize revenue for mid-market project-management buyers without eroding conversion."* Keep the scope narrow. Redesigning five tiers and four add-ons in one study is too much; split it.

### Define the target segment
- Recruit **actual buyers or power users** in the segment, not random consumers.
- If studying multiple segments, ensure minimum **200 respondents per segment** for stable utility estimates. If segmenting post-hoc, aim for ≥100 per segment; factor this into overall sample size.
- Screen by role, company size, industry, or geography depending on relevance.

### Set success criteria
- Hit rate on holdout (unseen) choice tasks ≥ 50%
- Standard error of price coefficient < 5% of coefficient magnitude
- Segment differences in WTP > 20% (otherwise merging segments may be simpler)

---

## Step 2 — Select Attributes and Levels

### Rules of thumb
- **4–6 attributes** max. More than 6 causes cognitive overload and data quality collapse.
- Include **price** as one attribute. It should have **3–5 levels** spanning your acceptable price range.
- Each non-price attribute should have **2–4 levels**.
- All attributes must be **independent and realistic** (no impossible bundles).

### Good vs. bad examples for a project-management SaaS
| Attribute | Levels | Notes |
|-----------|--------|-------|
| User seats | 5 / 15 / 50 / Unlimited | Clear increments, testable |
| Admin controls | Basic / Advanced / Enterprise | Real packaging lever |
| Integrations | 3 / 10 / 50 / Custom | Quantifiable |
| Support | Email / 9×5 chat / 24×7 phone | Common enterprise differentiator |
| Price | $15 / $29 / $49 / $79 per user/mo | Span realistic range |

### Avoid
- Correlated attributes (e.g., "Unlimited seats" and "$5/user" — conceptually impossible together)
- Too many "plus/minus" binary flips that produce 2^n expansion before any design efficiency
- Price levels that are too close together (<10% apart) — respondents can't detect differences

---

## Step 3 — Choose the Experimental Design

Use an **efficient fractional factorial design** optimized for D-efficiency. You do not need a full factorial.

| Design Type | When to Use | Trade-off |
|-------------|-------------|-----------|
| **Random design** | N < 150 | Simple, but lower statistical efficiency |
| **Efficient design (D-optimal / A-optimal)** | N ≥ 150 | Standard for professional CBC; maximizes information per respondent |
| **Adaptive / Bayesian efficient** | N ≥ 300 | Slight uplift in precision; more complex to field |

Most survey platforms (Qualtrics, SurveyMonkey) and specialized tools (Sawtooth, Conjointly) offer CBC modules with built-in efficient designs.

### Number of tasks per respondent
Typical CBC surveys present **10–15 choice tasks** per respondent. Each task shows 2–3 concepts plus a "None / Not Buy" option. Keeping tasks under 20 prevents fatigue and straight-lining.

---

## Step 4 — Calculate Minimum Sample Size

A workable sample-size guide:

| Scenario | Minimum Respondents | Reason |
|----------|---------------------|--------|
| Single segment, directional insight | 150 | Stable main effects |
| Single segment, confident results | 200–300 | Robust part-worths and simulations |
| Segmented analysis (2–3 segments) | 200 per segment | Each segment needs cell counts; this is the common ceiling |
| 4+ segments or niche sub-segments | Consider redefining segments or using HB with priors | Sample cost grows linearly with segments |

**Rule of thumb for internal cell counts:** With 5 attributes and 3 levels each, the design has ~40 unique cells. Aim for **≥30 respondents per cell**. This is why 200 is a practical minimum.

---

## Step 5 — Build the Survey

### Survey skeleton
1. **Qualification screener** (role, company size, industry, budget authority)
2. **Context-setting description** of the product concept (specific enough that respondents understand exactly what they are choosing between)
3. **CBC tasks** (10–15 choice sets, randomized order, 2–3 concepts + None)
4. **Optional classification questions** (usage patterns, current vendor, budget range)
5. **Optional holdout tasks** (unseen choice sets used to validate model fit)

### Critical design details
- **Randomize concept order** within each task and task order across respondents.
- Include a **"None / Would not choose any"** option in every task to capture real opt-outs and approximate price elasticity more accurately.
- Specifying **B2B context**: State whether the price is per seat/month, annual, or flat fee. B2B respondents ignore the pricing block if billing terms are ambiguous.
- Avoid **"Would you buy?" yes/no questions** after every task; they create anchoring.

---

## Step 6 — Field and Clean

### Recruitment channels (fastest to slowest)
| Channel | Signal Quality | Cost | Typical N |
|---------|---------------|------|-----------|
| Existing customer panel | Highest | Low | 200–500 depending on base |
| Warm prospects / pipeline | High | Low | 50–200 |
| B2B panel vendor (Cint, Respondi, Lucid) | Medium-High | Medium | 200–1,000 |
| Paid LinkedIn / industry newsletters | Medium | Medium | Variable |

### Cleaning thresholds
| Check | Action if failed |
|-------|------------------|
| **Speeders**: < 15 seconds per task | Exclude respondent |
| **Straight-lining**: identical answer pattern across ≥ 8 tasks | Exclude |
| **Inconsistency**: choosing a concept with all "worst" attribute levels | Exclude if pattern repeats |
| **Screener failures**: role or company size mismatch | Exclude from start |
| **"None" always chosen**: may be realistic (price too high) or lazy; check average price levels and exclude if task completion time is absurdly low |

---

## Step 7 — Analyze and Generate Utilities

Most practitioners use Hierarchical Bayes (HB) estimation provided by conjoint platforms. If running from scratch in Python/R:

**Analytical steps**
1. Estimate part-worths for each attribute level per respondent.
2. Aggregate to population level (mean + std dev).
3. Calculate **relative attribute importance**:
   ```
   Importance(attr) = (max(utility) - min(utility)) / Σ[max-min] × 100
   ```
4. Calculate **WTP for each level vs. baseline**:
   ```
   WTP(feature) = - (utility(feature) - utility(baseline)) / price_coefficient
   ```
   Ensure price_coefficient is negative; flip sign to get positive dollar WTP.

### Example output
| Attribute | Importance | Key WTP Insights |
|-----------|-----------|------------------|
| Integrations | 34% | Moving 3 → 10 integrations adds $11/user/mo WTP |
| Support | 28% | 24×7 phone adds $18/user/mo over email |
| Seats | 22% | 5 → 15 seats is baseline; unlimited adds $6 |
| Price | 16% | Buyers are moderately price-sensitive |

---

## Step 8 — Simulate Market Scenarios

Using the aggregated utilities, compute simulated choice share for candidate offerings:

```
Utility(choice) = β_0 + Σ β_price × Price + Σ β_attr × Level_dummies
Share(choice) = exp(Utility(choice)) / Σ exp(Utility(all_choices))
```

Build a simulation matrix:
- Current offering vs. new tier structure
- "Good / Better / Best" configurations at different price points
- Enterprise add-on bundles at varying price points

**Revenue simulation** = Σ (Share × Segment Size × Price × Expected conversion)

Identify the revenue-maximizing configuration, not just the utility-maximizing one.

---

## Step 9 — Validate with Real-World Checks

- **Holdout hit rate**: ≥ 50% correct predictions for unseen choice tasks indicates acceptable model fit. <40% suggests poor attribute selection or respondent fatigue.
- **Price coefficient sanity**: Price coefficient should be negative and its magnitude should place the implied margin at or above target (e.g., >70% gross margin).
- **Managerial reasonableness**: If simulation says enterprise buyers demand 24×7 phone support at $8/user/mo, cross-check against known competitor pricing and implementation costs.
- **Segment behavior**: If SMB and Enterprise have effectively identical utilities, your attributes are not capturing real segmentation; redefine attributes.

---

## Pitfalls

| Pitfall | Why It Happens | Fix |
|---------|----------------|-----|
| **Too many attributes** | Team can't agree what to test | Force rank; drop bottom-vote attributes outside scope or test in a follow-up study |
| **Price levels too narrow** | No price elasticity signal | Span at least 30% of your price range (e.g., test $20, $35, $50, $70, $90) |
| **Ignoring "None"** | Overstated WTP | Always include "Would not choose any" |
| **Hypothetical bias** | Stated WTP ≠ real purchase | Add a validation question: "If this were your actual vendor, would you buy at the price shown?" Correlate with stated choice |
| **Running with N<150** | Unstable part-worths | Stick to 200+ per segment; if sample is scarce, focus on main effects only |
| **Over-interpreting small segments** | High variance in utilities | Require ≥100 respondents per segment; else merge or run a separate study |
| **Forgetting implementation cost** | WTP looks great but margin is thin | Subtract delivery cost (support, onboarding, infrastructure) from WTP before approving tier economics |

---

## Verification Checklist

Before using conjoint outputs to finalize pricing, packaging, or tier structures:

- [ ] Research objective is narrow and actionable (e.g., "pick tier 2 structure," not "design all packaging")
- [ ] 4–6 attributes selected; no correlated or impossible levels
- [ ] Efficient fractional factorial design applied (D-optimal or better)
- [ ] Minimum 200 respondents in the population of interest (≥200 per key segment)
- [ ] Each respondent completed 10–15 randomized choice tasks with a None option
- [ ] Data cleaning removed speeders, straight-liners, and inconsistent responders
- [ ] Model validation: holdout hit rate ≥ 50% and price coefficient is negative and sizable
- [ ] Attribute importance computed from max–min utility ranges
- [ ] WTP estimates derived relative to a clean baseline level and not raw dollar units
- [ ] Market simulation compared current vs. at least three candidate configurations
- [ ] Simulated revenue checked against gross margin, CAC payback, and LTV:CAC targets
- [ ] Results segmented by at least one material cut (persona, company size, or geography) if expected to differ
- [ ] A stakeholder reviewed the concepts for clarity and realism

---

## What This Skill Does NOT Cover

- Designing the tier architecture, value metric, or psychological levers (see `saas-pricing-architecture`)
- Testing price changes statistically in production (see `saas-pricing-experiment-design`)
- Usage-based metering and per-unit cost modeling (see `usage-based-pricing-bill-shock-prevention`)
- B2B enterprise deal packaging, discount governance, and CPQ mechanics (see `b2b-deal-packaging-and-pro-pricing` and `saas-pricing-governance-and-exception-management`)
- Van Westendorp price range research (see `van-westendorp-price-research`)
- Customer-side churn or retention diagnostics (see `saas-churn-root-cause-diagnosis`)

---

## Related Skills

- `van-westendorp-price-research` — complementary WTP research; use Van Westendorp first to define a price corridor, then conjoint to optimize features within it
- `saas-pricing-architecture` — translates conjoint outputs into tier structures and psychological pricing
- `saas-pricing-experiment-design` — validates conjoint-derived prices in production after launch
- `saas-cac-payback-optimization` — ensures derived WTP and tier structure support efficient growth economics
- `gtm-channel-mix-economics` — links segment-specific WTP differences to channel budget allocation