---
name: SakTan-business-research-deep-dive
description: "Multi-angle deep-dive research workflow for House of Sak scouting. Scout markets, profile leads, discover digital gaps, and produce structured reports with ranked picks, pricing intel, and actionable opportunity maps."
version: 1.0.0
author: Beer + SakTan
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [business, research, scouting, lead-generation, house-of-sak]
    related_skills: [house-of-sak-qa-shield, service-quoting]

---

# Business Research — Deep Dive Scout

## Overview

A repeatable six-phase process for scouting businesses, markets, and
opportunities — born from Beer's methodology during the Cork 118-business
scan (July 2026). This is NOT a shallow summary skill. Every research
pass produces **structured tables, ranked picks, specific URLs, pricing
intel, and a clear opportunity map** for House of Sak.

## When to Use

- Beer says "research [category] in [area]" or "scout [industry]"
- A multi-angle deep-dive is expected (not a one-source summary)
- Finding leads for House of Sak outreach
- Analysing competitors in a market
- Building case studies from real businesses

## Workflow

### Phase 0: Understand the Brief

Before running anything, confirm the scope:

| Question | Why |
|----------|-----|
| What category/industry? | Restaurants, barbers, trades, ecommerce? |
| What location? | City, neighbourhood, radius? |
| What's the goal? | Lead gen, competitor analysis, case study? |
| Any exclusions? | Chain brands to skip, known contacts? |

One clarifying question is enough. If Beer says "process" — skip this
phase and go.

---

### Phase 1: Market Recon — Find the Players

Use **parallel** tools for maximum speed. Run these simultaneously:

#### 1a — Google Maps sweep (via Composio)

Query the category in the target location. Batch similar categories
together:

```
"barbers in Cork City Ireland"
"hair salons in Cork City Ireland"
"restaurants in Cork City Ireland"
```

Capture for each result: name, rating, review count, phone, address,
website URL, category.

#### 1b — Web search for context

```
site:linkedin.com "[industry]" "[city]"
"[business]" pricing OR packages OR menu
"[business]" review OR "case study"
```

#### 1c — Check multiple map/directory platforms

When available, cross-reference Google Maps with:
- Yelp (yelp.com/search?find_loc=[city]&find_nl=[category])
- Trustpilot (trustpilot.com/review/[domain])
- Industry-specific directories

---

### Phase 2: Classify Web Presence

For every business found, classify their website field:

| Classification | Meaning | Priority |
|---------------|---------|----------|
| **none** | No website field at all | 🔴 High |
| **facebook_only** | Website is a Facebook page URL | 🟡 Medium |
| **instagram_only** | Website is an Instagram URL | 🟡 Medium |
| **booking_app** | Square, Booksy, Nearcut, Fresha, etc. | 🟡 Medium |
| **booking_site** | Booking.com, Hotels.com, OpenTable | 🟡 Medium |
| **url_shortener** | shorturl.at, bit.ly (suspect) | 🟡 Medium |
| **google_site** | sites.google.com | 🟡 Medium |
| **chain_brand** | National chain (Tesco, McDonalds) | 🟢 Ignore |
| **proper_site** | Real custom domain with content | ✅ Skip |

**Key insight from Beer's Cork scan:** Barbershops are the most
underserved category — 13 of 19 zero-website businesses in the scan
were barbershops. Average rating 4.7★.

---

### Phase 3: Deep Dive — Per Lead

For high-priority leads (none / facebook_only / booking_app), dig deeper:

#### 3a — Social presence check

Search each lead's name + city on:
- Facebook → check if they have a page, last post date, follower count
- Instagram → check handle, content quality, engagement rate
- Google Business Profile → response rate to reviews

#### 3b — Pricing intelligence

Search for their pricing, packages, or menu:
```
"[business name]" "[city]" price OR menu OR packages OR rates
```

Scrape menu/pricing pages when found — they reveal the budget tier.

#### 3c — Review sentiment scan

Check their top reviews (Google, Yelp, Trustpilot):
- What do customers love?
- What do they complain about?
- Are complaints addressable by House of Sak services?
  (Slow booking? No online presence? Hard to find info?)

---

### Phase 4: Build the Lead Table

Produce a structured markdown table with ALL findings:

| # | Business | Category | ★ | Reviews | Phone | Address | Web Presence | Pricing Tier | Social | Opportunity |
|---|----------|----------|---|---------|-------|---------|-------------|-------------|--------|------------|
| 1 | Name | Type | 4.5 | 87 | 021-X | Street | none / FB-only / booking_app | €€ or N/A | IG: N, FB: Y | 🔴 High |

**Ranking columns:**
- **Opportunity:** 🔴 High / 🟡 Medium / 🟢 Low
- **Pricing tier:** € (budget), €€ (mid), €€€ (premium) — helps target service offer
- **Social:** Quick snapshot of social presence quality

At the bottom, add a **Ranked Picks** section:
> **Top 3 by opportunity:**
> 1. [Business A] — why (high rating + zero web presence + good location)
> 2. [Business B] — why (booking-app-only + strong reviews + no custom site)
> 3. [Business C] — why (Facebook-only + high foot traffic area)

---

### Phase 5: Opportunity Map

For each high-priority lead, map which House of Sak service fits:

| House of Sak Service | Best For This Lead? | Notes |
|---------------------|-------------------|-------|
| **Web Development** | If no website or FB-only | ~€1,500–€3,000 |
| **Local API Prototyping** | If they need booking/scheduling | ~$150–$400/prototype |
| **QA Automation** | If they have a site but issues | ~$200–$500/project |
| **SEO / Digital Presence** | If they exist but invisible online | Quote-based |
| **Student Starter Kit** | If student-facing business | €500 flat |

Also flag **quick wins** — things they could fix in <1 hour:
- Claim/update Google Business Profile
- Add social links to existing site
- Update hours/contact info
- Respond to pending reviews

---

### Phase 6: Save & Handoff

Always close the loop:

1. **Save findings** — Write the full report to `house-of-sak-report/` directory
   as `scout-report-[category]-[location]-[date].md`
2. **Memory update** — Save key facts:
   - Total leads found, by category
   - Number of high/medium/low priority
   - Notable patterns (e.g. "13/19 no-website were barbershops")
   - Best opportunity pick with reasoning
3. **Cross-agent handoff** — If another agent needs context:
   - Compile a summary file: `house-of-sak-report/master-report-for-[agent].md`
   - Tell Beer the file is ready for forwarding

---

## Format Rules

### Structured Tables

Every research output MUST use proper markdown tables. No bullet-point
substitutes. Tables give Beer scannable data at a glance.

### Ranked Picks

Always end with a ranked picks section (top 3). Each pick needs:
- Business name
- One-line why it's the best opportunity
- Specific service recommendation

### Source URLs

Every claim should trace to a source. Include:
- Google Maps URL or place ID
- Website URL (or "no website found")
- Social profile URLs
- Review page URLs

---

## Pitfalls

1. **Don't stop at one source** — always cross-reference Maps + web search + social
2. **Don't assume "no website" means "no business"** — many strong local businesses run on word-of-mouth only
3. **Don't skip pricing intel** — it's the single best signal for budget tier
4. **Don't hallucinate contact details** — if Google Maps doesn't have a phone number, say "not listed" not "N/A"
5. **Don't re-rank based on personal preference** — ranking is about opportunity for House of Sak, not how cool the business is
6. **Chain brands are not leads** — skip Starbucks, Tesco, McDonalds, Boots
7. **"Process" means execute** — when Beer says "yes process" or "process", go immediately without confirmation loop

---

## Verification Checklist

- [ ] Phase 1: Market recon done (Maps + web search + directory cross-ref)
- [ ] Phase 2: Web presence classified for every lead
- [ ] Phase 3: Deep dive on top leads (social + pricing + reviews)
- [ ] Phase 4: Structured lead table with ranked picks
- [ ] Phase 5: Opportunity map with service recommendations
- [ ] Phase 6: Report saved + memory updated + handoff ready
- [ ] Sources have traceable URLs
- [ ] No hallucinated contact details

---

## Reference: Pricing Tiers from Beer's Services

| Service | Price Range |
|---------|------------|
| Local API Prototyping | $150–$400 (prototype + dashboard + JSON endpoints) |
| Hosting/Maintenance (add-on) | $40/month |
| QA Automation | $200–$500 per project (48h turnaround) |
| Web Development | ~€1,500–€3,000 (estimate, quote-based) |
| Student Starter Kit | €500 flat |

---

## Reference: Cross-Agent Handoff Pattern

When compiling for another agent (SakSee, SakSit, SakJules):

```
house-of-sak-report/master-report-for-[agent].md
├── Executive summary of the session
├── Each case study: 5-line summary, critical findings, quick wins
├── Market scan data (totals, breakdowns)
├── Reusable assets created (skills, templates)
└── Suggested next actions
```

No cross-agent messaging tools exist — file handoff via the shared
`house-of-sak-report/` directory is the pattern. Signal completion to Beer,
who forwards to the target agent.