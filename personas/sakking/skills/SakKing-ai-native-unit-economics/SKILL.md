---
name: SakKing-ai-native-unit-economics
title: AI-Native SaaS Unit Economics
description: >
  Analyze and design unit economics for AI-native SaaS, API products, and
  agentic software where inference costs, token consumption, and model routing
  replace traditional human-seat economics. Covers the AI-Gross-Margin ladder,
  CPQ math, per-seat vs per-token vs credit-based pricing, deflation hedging,
  and margin guardrails. Use when launching an AI feature, evaluating AI-native
  monetization, diagnosing why AI features destroy margin, or when your
  product uses LLMs/embeddings as a core cost center.
triggers:
  - launching or repricing AI features
  - evaluating AI-native monetization models
  - diagnosing margin collapse in LLM-powered products
  - modeling inference cost impact on LTV:CAC
  - comparing per-seat, per-token, and credit-based pricing
  - optimizing model routing for cost efficiency
---

# AI-Native SaaS Unit Economics

## 1. Vocabulary: The AI-Gross-Margin Ladder

Traditional SaaS has COGS dominated by hosting. AI-native products have a
**third layer of variable cost**: inference + embedding + retrieval. Use this
three-step ladder:

| Layer | What it captures | Formula |
|---|---|---|
| **CM1** (Gross AI Margin) | Revenue minus AI compute & API costs | Revenue − AI-COGS |
| **CM2** (AI-Contribution Margin) | CM1 minus support, tooling, retrieval infra | CM1 − (Support % + Vector DB / RAG infra) |
| **CM3** (AI-Operating Margin) | CM2 minus downstream CAC amortized to AI | CM2 − (AI-acquisition spend / AI-active-customers) |

> **Pitfall:** Traditional "hosting COGS" understates AI delivery cost by 2-10x.
> Many AI-native startups show 85-90% gross margins like SaaS but actually
> operate at 40-60% when AI-COGS is explicit.

## 2. Core Formulas

### Cost Per Query (CPQ)

```
CPQ = Total Monthly AI Inference Spend / Total Monthly AI-Powered Queries
```

Break down inference spend into:
- **Input tokens** (prompt + context)
- **Output tokens** (completion)
- **Embeddings spend** (if RAG / memory is used)
- **Fine-tuning / training amortization** (optional)

### Token Economics for Per-Unit Pricing

If priced per-token or per-query:

```
Unit Price = f(CPQ, target_gross_margin, model_upgrade_buffer)

Target Unit Price = CPQ / (1 − Target_AI_Gross_Margin%)

Example:
  CPQ = $0.008
  Target AI-Gross-Margin = 70%
  Minimum Unit Price = $0.008 / (1 − 0.70) = $0.0267
```

But **per-seat** pricing decouples revenue from usage:

```
Effective Price Per Query = Per-Seat ARR / (Seats × Avg Monthly Queries Per Seat)

Example:
  $1,200/seat/year ARR
  3 seats / account
  Avg 500 AI queries / user / month
  = $1,200 / (3 × 500 × 12) = $0.067 per query
```

### AI-COGS Model (Hybrid)

For products mixing AI and non-AI features:

```
AI-COGS = Σ [Query_Count_i × Token_Input_i × $/Input_Token_i
              + Query_Count_i × Token_Output_i × $/Output_Token_i
              + Embedding_Count × $/Embedding_Token]
```

Track by **feature** (summarization, generation, classification) because
quality upgrades change unit economics per feature.

## 3. Pricing Model Comparison

| Model | Alignment | Margin Risk | Buyer Preference | Best For |
|---|---|---|---|---|
| **Per-seat** | Low (heavy users subsidize light users) | High (power users can run CPQ > price) | Strong (familiar, easy to budget) | Traditional B2B, low-variance usage |
| **Per-token / per-query** | Perfect (direct 1:1) | Low if priced with margin buffer | Medium (sticker shock on big queries) | API-first, developer tools |
| **Credit-based** | High (pool covers variance) | Medium (breakage vs overage) | High (predictable bill) | Agents, hybrid workflows |
| **Outcome-based** | Highest (pay for value, not spend) | High (cost overruns land on vendor) | Growing (aligned incentives) | High-value vertical AI (legal, medical) |

### Hybrid Fallback Rule

If you must start per-seat (for sales motion), **cap or meter** power-user
usage:

```
Per-Seat Gross Margin = [Per-Seat Price − (Avg Queries × CPQ)] / Per-Seat Price

If margin < threshold (e.g., 50%), introduce:
  - Tiered caps (Pro: 1k queries/mo, Business: 5k, Enterprise: unlimited)
  - Overage fees at 2× marginal cost
```

## 4. Deflation Hedging

AI inference costs are dropping ~10x annually. Fixed per-token pricing becomes
a race to zero. Hedge with:

| Hedge | Mechanism |
|---|---|
| **Margin floors** | Contractual minimum price per token or minimum monthly spend |
| **Model routing** | Auto-route queries to cheapest model that passes quality gate |
| **Cost passthrough** | Index your price to a model-cost index (e.g., OpenAI 4o-mini cost) |
| **Bundling** | Package tokens into credits that devalue over time like airline miles |

## 5. AI-COGS Watchdog Dashboard

Track weekly:

1. **CPQ by feature**
2. **AI-Gross-Margin by segment** (SMB vs Enterprise)
3. **Model mix** (% on GPT-4o vs Sonnet vs Haiku vs on-prem)
4. **Inference cost trend** (month-over-month per 1k tokens)
5. **Break-even query volume** for enterprise custom models

### Red Flags

- AI-COGS > 40% of AI revenue → pricing is too low or volume too high
- Any single customer > 10% of monthly query volume → concentration risk
- CPQ rising despite cheaper models → context bloat or bad caching
- Credit redemption < 60% → "breakage" masking real unit economics

## 6. Verification Step

Build a **shadow model** for your pricing:

1. Export last 30 days of AI API usage (tokens in/out, by feature, by customer).
2. Compute actual CPQ.
3. Compute actual revenue received per query / per user.
4. Compare: **(Revenue − AI-COGS) / Revenue** vs. your target AI gross margin.
5. Run scenarios: *What if model costs drop 30%? What if usage doubles?*

If variance > 10 percentage points from target, pricing is decoupled from
real cost structure.
