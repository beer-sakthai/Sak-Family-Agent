---
title: Economic Moat Diagnosis and Strengthening
name: economic-moat-diagnosis-and-strengthening
description: Diagnose whether a business has a durable competitive advantage (economic moat), identify which structural source drives it, and decide how to reinforce it or close gaps. Use when evaluating a market opportunity, pricing power, M&A targets, go-to-market defensibility, product expansion risk, or when building a 3-year strategy that must outlast competitors.
triggers:
  - pricing pressure is eroding margins faster than expected
  - leaders ask whether the advantage is structural or temporary
  - entering a new segment or launching a new product line
  - evaluating an acquisition or partnership target
  - board or investor asks about competitive durability
  - GTM motion is being copied faster than anticipated
---

# Economic Moat Diagnosis and Strengthening

## What this skill does

Moves economic moat analysis from investor-style "wide/narrow/none" ratings into an operator's decision tool. Outputs: moat source assessment, durability score, gap map, and a 3–5 action plan to reinforce or build moat.

## Framework: Five Sources + Durability

A moat is a **structural advantage** (not a feature or a great team) that lets a firm earn superior returns for years while competitors try to copy. The durable sources, grounded in Morningstar/Morgan Stanley research, are:

| Source | What it is | Diagnostic signal |
|---|---|---|
| **Intangible Assets** | Brand, patents, regulatory licenses, data exclusivity | Customers pay more for the same widget; copying requires legal/brand investment measured in years |
| **Switching Costs** | Data migration, retraining, process integration, ecosystem lock-in | Churn/loss rate stays below industry average despite price increases |
| **Network Effect** | Value rises as more users join a marketplace, platform, or workflow | Growth begets growth; new entrants must replicate the entire network |
| **Cost Advantage** | Scale, proprietary input, unique location, or process | Can sustain structurally lower cost per unit than any new entrants |
| **Efficient Scale** | Natural monopolies or limited capacity in a niche | Market size barely fits existing players; new entrants destroy economics |

## Step-by-step workflow

### 1. Define the advantage to test
Pick a specific business, product, or GTM motion. Ask: What do we believe we have that competitors cannot easily replicate?

### 2. Force-rank the five sources
Score each source **0–5** for this business/product:
- 0 = absent
- 3 = contributing
- 5 = dominant structural driver

Do NOT give points for temporary advantages (first-mover without switching costs, temporary pricing, better sales team, superior engineering execution).

### 3. Assign the moat rating
- **Wide Moat** (score ≥ 15, at least one source scored 5, expected durability ≥ 20 years): structural and heavily reinforced.
- **Narrow Moat** (score 8–14, at least one source scored 3+): defensible but contestable.
- **No Moat** (score < 8 or all sources ≤ 2): advantage is fleeting.

Adjust rating downward if:
- Regulatory protection expires within 5 years
- Technology vectors are shifting against the source (e.g., switching costs collapse via open standards)
- A well-funded competitor has explicitly targeted the same source

### 4. Identify the dominant source
Pick the single strongest source. All 3–5 actions below should reinforce it.

### 5. Diagnosis by source (operator-specific)

**Intangible Assets**
- Test: Do customers mention brand/trust as a reason they choose us? Can they switch without reputational or compliance risk?
- Actions: Expand patent estate, protect trademark/regulatory exclusivity, invest in brand-adjacent content (market research, thought leadership, certifications).

**Switching Costs**
- Test: What does a customer have to do to leave us today? Is that work product impossible to move or simply annoying?
- Actions: Increase data depth (rich history/no export), embed workflows into customer ops (API calls, cron jobs, procurement process), build multi-year contracts with renewal friction.

**Network Effects**
- Test: Does the product improve for every user as user count rises? Can a new entrant replicate the network starting from zero users?
- Actions: Design liquidity programs (matching, incentives), lower friction for match/transaction creation, create subgroups or workspaces that increase stickiness.

**Cost Advantage**
- Test: What is our unit cost vs. the best-funded potential entrant? Can we sustain that gap if volumes normalize?
- Actions: Vertical integration or long-term supply contracts, proprietary automation, geographic or asset-based advantages that competitors cannot lease.

**Efficient Scale**
- Test: Is the physical/economic capacity we occupy already near the size of the addressable market? Is entry by a new player uneconomic?
- Actions: Secure channel/real-estate/logistics capacity first, build reserve capacity to block entrants, keep pricing disciplined to avoid inviting entry.

### 6. Moat gap plan
For each source not already a 5, pick one action that changes the score by +1 within 12 months, and one that changes it by +1 within 3 years. Do not spread across all five—concentrate on the dominant source and one secondary.

### 7. Red team the moat
Assign someone to argue why the moat rating is wrong. Specific failure modes to probe:
- Brand advantage that exists only because we are older (not because we are better)
- Switching cost built on a non-standard format that eventually standardizes
- Network effect where negative network effects appear at scale (congestion, moderation, quality decline)
- Cost advantage built on a single-source labor or material that can be arbitraged
- Efficient scale in a market that is about to expand (bringing in new entrants)

## Formulas and metrics

### Moat durability estimate
`Durability (years) = (structural reinforcement score × 4) + (regulatory tailwind years) - (technology disruption risk in years)`

- Structural reinforcement score = 1 if switching cost, network effect, or efficient scale; 0.5 if cost advantage or intangibles.
- Regulatory tailwind years = years remaining on patents/licenses/locked-in channels.
- Technology disruption risk = 0 if none, 3 if mid-range risk (5G replacing proprietary transport, open formats, regulatory antitrust), 7 if high (AI rendering moat irrelevant).

**Example**: Narrow moat in regulated data analytics (switching costs 3, regulatory tailwind 15, tech disruption risk 3)
Durability = (3 × 4) + 15 - 3 = 24 years.

### Pricing power test
Compare price elasticity to market: if you can raise prices ≥ 5% annually with churn < 2% per year and win rate on deals > 80%, moat is real.

### Moat coverage risk
If CAC is growing faster than LTV, switching cost or brand may be weaker than assumed. Treat CAGR of CAC > CAGR of LTV as a moat-erosion signal for SaaS/subscription businesses.

## Pitfalls

1. **Feature masquerades as moat**: A better UX or faster release cycle is not a moat; it is execution. If the feature can be copied in months, it does not belong here.
2. **Brand without reason**: Brand is a moat only if it changes willingness-to-pay or trust economics. "Famous" is not a moat unless famous converts to higher price, lower churn, or regulatory favor.
3. **First-mover illusion**: Being first creates distribution, not a moat. Unless that distribution turned into switching costs or network effects, it is not structural.
4. **Size ≠ efficient scale**: Revenue leadership in a large market is not efficient scale. Efficient scale requires the addressable market to be smaller than optimal serving capacity.
5. **Regulatory moat without vigilance**: Regulatory licenses can be revoked or opened to competition. Treat them as time-boxed unless coupled with high switching costs.

## Verification step

Before finalizing a moat rating:
- Show evidence for each source in writing (e.g., "Switching cost = 4 because customers lose 8 weeks of workflow history on exit").
- Ask: "Would a well-funded, patient competitor still fail to copy this in 3 years?" If yes, it is structural. If no, it is execution.
- Test durability formula: if durability < 5 years, downgrade rating by one tier.

## Use cases

- **Pricing decisions**: Wide moat → firm pricing power; No moat → avoid premium pricing until you build structural advantage.
- **M&A evaluation**: If target has no moat, acquisition premium is mostly goodwill; demand structural provisions or earn-outs tied to moat-building KPIs.
- **GTM strategy**: Network-effect businesses need liquidity first; switching-cost businesses need depth of embed; intangible-asset businesses need brand scale.
- **Funding narrative**: Board/investor decks should state moat source, durability estimate, and 3 actions extending it.
