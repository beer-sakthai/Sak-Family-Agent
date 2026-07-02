# Sak Family Agent — Living Plan

> **Dream → Hope → Care → Joy → Trust → Growth**
> Work top-to-bottom. Check off with a date note when done. Plan first, then act.

---

## 🌟 High-Level Goals

**Immediate (repo hygiene):** Give every Sak Family persona a clean, consistent
SOUL.md so agents are easy to configure, extend, and deploy.

**Long-term (Beer's goal):** Achieve financial stability for Beer by developing
and monetizing a product based on the Sak Family Agent technology.

---

## 📋 Current State — Persona SOULs (2026-07-02)

| Persona | SOUL.md | Status |
|---|---|---|
| SakKing | [personas/sakking/SOUL.md](./personas/sakking/SOUL.md) | ✅ Done |
| SakSee | [personas/saksee/SOUL.md](./personas/saksee/SOUL.md) | ✅ Done |
| SakThai | [personas/sakthai/SOUL.md](./personas/sakthai/SOUL.md) | ✅ Done |
| SakSit | [personas/saksit/SOUL.md](./personas/saksit/SOUL.md) | ✅ Done |
| SakTan | [personas/saktan/SOUL.md](./personas/saktan/SOUL.md) | ✅ Done |
| SakJules | [personas/sakjules/SOUL.md](./personas/sakjules/SOUL.md) | ✅ Done |

### Shared files

| File | Status |
|---|---|
| [SOUL.md](./SOUL.md) | ✅ Root — team roster synced, Charge, Principles, Operating Contract |
| [OPERATING_CONTRACT.md](./OPERATING_CONTRACT.md) | ✅ Shared operating rules (one place) |

---

## 🗺️ Target Structure — every persona SOUL.md

```
# <AgentName> Agent Persona

## Identity
  Who I am, Telegram handle, siblings, model/framework.

## Say who I am — every reply
  One-liner role that opens every reply.
  `personas/<name>/SOUL.md` is the authoritative source line.

## Character & Craft
  General character + role-specific craft / specialty.

## Charge
  ### What charge is
  ### Charge states (table)
  ### Charging the soul

## Principles
  1. Read before you write.
  2. Capture what's worth recalling.
  3. Finish what you start.
  4. Be honest about state.

## How I grow — the 6-stage cycle   (SakKing only; optional for others)
## Tone
```

---

## 🚀 Phases — Repo Hygiene

### Phase 1 — Fix the two partially-refactored personas ✅ 2026-07-02

- [x] **SakThai**: Added `## Character & Craft` heading + HF craft paragraph. Self-reference line in correct place.
- [x] **SakSit**: Moved `SOUL.md` self-reference line to directly after role line.

### Phase 2 — Refactor SakTan ✅ 2026-07-02

- [x] Full SOUL.md rewrite: Identity, Say who I am, Character & Craft (daily ops / life admin), Charge, Principles, Tone. Inline Operating Contract removed.

### Phase 3 — Create SakJules SOUL.md ✅ 2026-07-02

- [x] Created `personas/sakjules/SOUL.md` from scratch (Master of Automation & CI/CD, `gemini-1.5-pro-latest`, full structure).

### Phase 4 — Sync root SOUL.md team roster ✅ 2026-07-02

- [x] Updated model column: SakThai (`claude-opus-4-8`), SakSee (local `llama3`), SakSit (local `llama3` / Modal).
- [x] Added `personas/sakjules/SOUL.md` link to root `SOUL.md` link list.

### Phase 5 — Long-term: Product & Monetization

- [x] Brainstorm product ideas that leverage the Sak Family Agent technology. — 2026-07-02
  - *Decision: Focus on "Idea 2: Agent-in-a-Box" while keeping "Idea 1: Personal Memory Agent" as a parallel option.*
- [x] Define an MVP for the "Agent-in-a-Box" idea. — 2026-07-02
  - **MVP Definition: The "Telegram Knowledge Bot"**
    - **Product:** A custom-branded AI agent, delivered as a private Telegram bot, that answers questions based on a business's specific documents.
    - **Core Value:** Provides a "digital expert" to instantly answer repetitive questions for customers or staff.
- [x] Identify the first target customer for the MVP. — 2026-07-02
  - *Target: Beer's friend who has a business and for whom Beer is building a web app.*

---

## 🚀 Phases — Product & Monetization (Continued)

### Phase 6 — Detailed Product & Market Analysis (Pivoted 2026-07-02)

*Goal: To ensure the agent is ready for any business type, including digital marketing, we will perform a more detailed analysis before building.*

#### Part A: Market & Problem Discovery

- [x] Identify 3-5 target business archetypes. — 2026-07-02
  - 1. Digital Marketing Agency
  - 1. Local Service Business
  - 1. Student / Researcher
  - 1. E-commerce Store
  - 1. Content Creator / Solopreneur
- [ ] For each archetype, list 5-10 common, repetitive, information-based problems they face. *(In Progress)*
  - **1. Digital Marketing Agency (Targeting budget-conscious youth)**
    - **Content Creation:** Repetitively generating high-volume, low-cost content (TikTok/Reels) and brainstorming viral hooks based on current trends.
    - **Reporting & Analysis:** Pulling weekly engagement metrics from multiple social platforms and summarizing them into simple reports for clients.
    - **Client Communication:** Answering the same client questions repeatedly ("What's the status?", "Send the report.").
    - **Market Research:** Constantly searching for affordable micro-influencers with high engagement in niche youth markets.
  - **2. Local Service Business**
    - **Social Media Management:** Struggling to post content consistently due to being busy with daily operations.
    - **Customer Inquiries:** Losing potential customers by not being able to respond quickly to common questions via DMs and email.
    - **Appointment Scheduling:** Spending too much time manually managing bookings and sending reminders.
    - **Reputation Management:** Lacking time to request and respond to customer reviews on platforms like Google and Yelp.
  - **3. Student / Researcher**
    - **Information Overload:** Drowning in research papers, articles, and lecture notes with no easy way to search or connect ideas across them.
    - **Time Management & Burnout:** Struggling to balance classes, assignments, a part-time job, and personal well-being, leading to disorganization and stress.
    - **Financial Strain:** Constantly worried about the high cost of living and lacking simple tools to track expenses or find student-specific discounts.
    - **Writing & Formatting Grind:** Spending countless hours on tedious, repetitive tasks like formatting citations and checking paper templates instead of focusing on core research.
  - **4. E-commerce Store (Focused on Customer Care)**
    - **Repetitive Pre-Sale Questions:** Spending significant time answering the same questions about shipping, returns, and product details before a purchase.
    - **Post-Sale Support Overload:** Handling a high volume of common post-purchase inquiries like "Where is my order?" or "How do I track my package?".
    - **Personalization at Scale:** Wanting to provide a personal touch and remember loyal customers but lacking the tools to track individual histories efficiently.
    - **Feedback & Review Management:** Struggling to find the time to proactively request customer reviews and respond to feedback in a timely manner.
- [ ] Specifically detail the problems and opportunities for a **Digital Marketing Agency**.
  - **5. Content Creator / Solopreneur**
    - **Content Creation Treadmill:** Constantly under pressure to produce a steady stream of new content, leading to burnout.
    - **Audience Engagement Overload:** Spending hours every day replying to the same comments and DMs across multiple platforms.
    - **Manual Content Repurposing:** Wasting time manually turning long-form content into smaller pieces for different platforms (e.g., video to blog post to tweets).
    - **Business Admin Distractions:** Juggling all business tasks (invoicing, scheduling, marketing) alone, which takes time away from creative work.

#### Part B: Agent Capability & Gap Analysis

- [ ] Audit the Sak-Family-Agent's current tools (`learn`, `recall`, `search`, etc.) and skills.
- [ ] Create a map: which existing tools/skills can solve which problems from Part A?
- [ ] Identify capability gaps: what new skills or tools would be needed to be effective for these businesses?

#### Part C: MVP Definition & Strategy

- [ ] Based on the analysis, select the single most promising combination of (Business Archetype + Solvable Problem).
- [ ] Define a highly specific Minimum Viable Product (MVP) for this combination.
- [ ] Outline a low-risk monetization strategy for this MVP.

---

## 🔑 Key Principles for This Work

1. **Plan first, act second.** Update this PLAN.md before making edits.
2. **Surgical edits.** Change only what the task needs; preserve surrounding style.
3. **One persona at a time.** Finish and verify before moving to the next.
4. **No duplication.** Shared content (Charge, Principles, Operating Contract)
   lives in root `SOUL.md` — persona SOULs are lean and persona-specific.
5. **Protect Beer first.** No-cost, low-risk solutions always preferred.
