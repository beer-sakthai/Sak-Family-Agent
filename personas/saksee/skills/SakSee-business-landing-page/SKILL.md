---
name: SakSee-business-landing-page
version: 1.0.0
description: Transform a business repo (README, services, pricing, docs) into a polished,
  story-driven single-page HTML landing site with nav, animations, trust signals,
  and CTA.
category: web-browser
tags:
- browser
- business
- landing
- page
---

# Business Landing Page

## Overview

Use this skill when the user wants to turn a business/info repo — README, services docs, pricing table, crisis/info docs — into a **single, polished, production-ready HTML landing page**. This is NOT a throwaway mockup (use `sketch` for that). This is the page you put live.

## When to Use

- The user says "polish the house of sak page" or "make a landing page for my business"
- You have a repo full of markdown docs (README, SERVICES.md, pricing, crisis info)
- The user needs a single HTML file they can deploy immediately
- Content exists but needs to become a cohesive web presence

## When NOT to Use

- User wants 2-3 variants to compare — use `sketch`
- User wants a design-only artifact without production concerns — use `claude-design`
- User wants a diagram or infographic — use `excalidraw` or `architecture-diagram`
- User wants a full multi-page site with backend — this is single-page only

## Core Method

### 1. Intake — Read the Source Material

Read every relevant file in the business repo:

```
read_file("path/to/README.md")
read_file("path/to/SERVICES.md")   # pricing, packages
read_file("path/to/PLAN.md")       # business strategy
read_file("path/to/CRISIS.md")     # emergency info
read_file("path/to/ABOUT.md")      # founder story
```

Extract:
- **Brand identity**: name, tagline, tone, colors if specified
- **Origin story**: the founder's narrative — this is your emotional hook
- **The team/agents**: who delivers — each needs a name, role, emoji
- **Services**: package name, description, price range, delivery time, what's included/not
- **Process**: how clients engage (inquiry → quote → build → deliver → pay)
- **Trust signals**: crisis info, testimonials, social proof
- **CTA channels**: Telegram, Instagram, LinkedIn, email — how clients reach you

### 2. Structure the Page Sections

Standard structure (adjust based on what the repo has). When services carry significant detail (features, use cases, deliverables), prefer the expanded pattern:

```
1. NAV          — Sticky bar: links to each section + CTA button
2. HERO         — Tagline, headline, badge ("X agents online"), CTA buttons
3. STORY        — Origin narrative with stat cards (numbers that impress)
4. AGENTS/TEAM  — Grid of who delivers (name, role, emoji, description)
5. PROCESS      — "How It Works" steps (3-4 steps)
6. WHY US       — Optional trust section: 6 cards about values (pay-after-delivery, no jargon, etc.)
7. SERVICES     — Pricing grid with price ranges, agent attribution, feature lists
8. FAQ          — Optional accordion: common questions about process, pricing, trust
9. TESTIMONIAL  — Quote section (founder quote or client placeholder)
10. CTA/CONTACT — Channel cards (Telegram, Instagram, LinkedIn)
11. FOOTER      — Attribution + crisis/emergency numbers (if applicable)
```

### 3. Design Patterns

**Color scheme:**
- Dark theme (`#0a0a0b` bg, `#e8e8ed` text) works for tech/agent stories
- Use a single accent color (purple `#8b5cf6`, cyan `#06b6d4`, green `#22c55e`)
- Subtle grid background via `body::before` with 3% opacity accent lines
- Surface/raised cards at `#121214` and `#1a1a1e`

**Typography:**
- Headings: `Inter` at 800 weight, tight tracking (`letter-spacing: -3px`)
- Body: `Inter` at 400 weight
- Prices/metrics: `JetBrains Mono` monospace for credibility
- Import: `@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');`

**Animations:**
- Scroll-reveal with IntersectionObserver (0-dependency, lightweight)
- Card hover lifts (`translateY(-4px)`) + border accent
- Hero badge pulsing dot
- Scroll hint at bottom of hero (optional)

**Responsive breakpoints:**
- `@media (max-width: 768px)`: single-column grids, smaller headings, hamburger nav
- `@media (max-width: 480px)`: stacked CTAs, single-column stats

**Content Strategy:**
- Showcase authentic origin stories to build emotional connection
- Feature case studies and reports for social proof
- Link to detailed documentation for transparency
- Include methodology explanations to build trust

### 4. Polish Checklist

- [ ] **Sticky nav** with smooth scroll (`html { scroll-behavior: smooth }`), closed on mobile link click
- [ ] **Hamburger menu** for mobile (toggle class `open` on nav-links)
- [ ] **OG meta tags** (og:title, og:description, og:type, og:url) + Twitter card
- [ ] **Favicon** via SVG data URI (`data:image/svg+xml,...`)
- [ ] **Scroll-reveal** — every section gets `class="reveal"`, IntersectionObserver adds `class="visible"`
- [ ] **Stat cards** with auto-calculated day counter (e.g. "82 Days Since April 15")
- [ ] **Service cards** with "powered by AgentName" attribution line
- [ ] **Bundle/highlight card** with accent border and gradient background
- [ ] **Expanded service cards** (Pattern B): feature lists, use-case box, deliverable line, per-service CTA
- [ ] **"Why Us" trust section** — 6 cards covering: pay-after-delivery, AI+human, no jargon, small biz focus, fast iteration, pricing for people who struggle
- [ ] **FAQ accordion** with toggle function — 6-8 questions covering pay process, revisions, agents, communication, examples, international, custom projects, origin story
- [ ] **CTA section** with clickable channel cards (Telegram, Instagram, LinkedIn)
- [ ] **"No upfront payment" badge** — repeated in process step 4, services section footer, and CTA
- [ ] **Crisis footer** (optional, for mental-health-adjacent businesses): emergency numbers in red-bordered container

## Extended Pricing Patterns & HTML/CSS Templates

For complete pricing display grids, FAQ accordion components, transparent pricing breakdown sections, and full single-page CSS/JS templates, see [`references/pricing_and_css_templates.md`](./references/pricing_and_css_templates.md).

## Verification

- Ensure all HTML tags close cleanly.
- Open in browser to confirm responsive design across 320px, 768px, and 1200px breakpoints.
- Verify 0 console errors.
