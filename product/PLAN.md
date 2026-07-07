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
| SakKing | [personas/sakking/SOUL.md](../personas/sakking/SOUL.md) | ✅ Done |
| SakSee | [personas/saksee/SOUL.md](../personas/saksee/SOUL.md) | ✅ Done |
| SakThai | [personas/sakthai/SOUL.md](../personas/sakthai/SOUL.md) | ✅ Done |
| SakSit | [personas/saksit/SOUL.md](../personas/saksit/SOUL.md) | ✅ Done |
| SakTan | [personas/saktan/SOUL.md](../personas/saktan/SOUL.md) | ✅ Done |
| SakJules | [personas/sakjules/SOUL.md](../personas/sakjules/SOUL.md) | ✅ Done |

### Shared files

| File | Status |
|---|---|
| [SOUL.md](../docs/SOUL.md) | ✅ Root — team roster synced, Charge, Principles, Operating Contract |
| [OPERATING_CONTRACT.md](../docs/OPERATING_CONTRACT.md) | ✅ Shared operating rules (one place) |

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

## 🚀 Phases — Repo Hygiene ✅ (Completed 2026-07-02)

All four phases completed — SOULs created/refactored for all 6 personas and root synced.

### Phase 1-4 Summary
- **Phase 1** — SakThai + SakSit SOUL fixes ✅
- **Phase 2** — SakTan full SOUL rewrite ✅
- **Phase 3** — SakJules SOUL.md created ✅
- **Phase 4** — Root SOUL.md roster synced ✅

---

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

### Phase 6 — Detailed Product & Market Analysis ✅ 2026-07-02

*Goal: To ensure the agent is ready for any business type, including digital marketing, we will perform a more detailed analysis before building.*

#### Part A: Market & Problem Discovery

- [x] Identify 3-5 target business archetypes. — 2026-07-02
  - 1. Digital Marketing Agency
  - 1. Local Service Business
  - 1. Student / Researcher
  - 1. E-commerce Store
  - 1. Content Creator / Solopreneur
- [x] For each archetype, list 5-10 common, repetitive, information-based problems they face. — 2026-07-02

#### Part B: Agent Capability & Gap Analysis

- [x] Audit the Sak-Family-Agent's current tools (`learn`, `recall`, `search`, etc.) and skills. — 2026-07-02
- [x] Create a map: which existing tools/skills can solve which problems from Part A?
  - **1. Digital Marketing Agency**
    - **Problem:** Repetitive Content Creation & Trend-Chasing.
      - **Capability:** SakSit (content) + SakSee (research).
      - **Gap:** Needs a reliable tool to programmatically identify trending audio/formats on platforms like TikTok.
    - **Problem:** Repetitive Reporting & Simple Analysis.
      - **Capability:** SakTan (ops) + SakSee (data gathering).
      - **Gap:** Direct API access to social media platforms (e.g., via Composio) would be more robust than screen-scraping.
    - **Problem:** Repetitive Client Communication.
      - **Capability:** SakTan (ops).
      - **Tools:** `send_telegram_message`, `learn`/`recall`.
      - **Gap:** Needs integration with email or a project management system to have real-time project status.
    - **Problem:** Repetitive Market & Influencer Research.
      - **Capability:** SakSee (web browsing).
      - **Gap:** Needs a more structured way to filter and score potential influencers beyond manual browsing.
  - **2. Local Service Business**
    - **Problem:** Repetitive Scheduling & Availability Inquiries.
      - **Capability:** SakTan (ops) + `send_telegram_message`.
      - **Gap:** Needs calendar integration (Google Calendar/Calendly) to check and book real-time availability.
    - **Problem:** Repetitive Pricing & Service Quotes.
      - **Capability:** SakThai (logic) + `recall` (pricing rules).
      - **Gap:** Needs a structured quoting engine or connection to an invoicing system (Stripe, QuickBooks).
    - **Problem:** Repetitive Follow-up & Review Requests.
      - **Capability:** SakTan.
      - **Gap:** Needs a trigger/webhook system when a job is marked 'done' to automatically send the request.
  - **3. Student / Researcher**
    - **Problem:** Repetitive Source Gathering & Citation Formatting.
      - **Capability:** SakSee (research) + SakSit (writing).
      - **Gap:** Direct integration with academic databases (PubMed, JSTOR) and reference managers (Zotero).
    - **Problem:** Repetitive Summarization of Long PDFs.
      - **Capability:** `read_file` or a custom PDF extraction tool.
      - **Gap:** Needs an efficient way to handle large token contexts or chunked RAG specifically optimized for academic papers.
  - **4. E-commerce Store**
    - **Problem:** Repetitive "Where is my order?" (WISMO) Inquiries.
      - **Capability:** SakTan (ops).
      - **Gap:** Direct API access to Shopify/WooCommerce and shipping providers (FedEx, UPS, USPS).
    - **Problem:** Repetitive Product Recommendation & Sizing.
      - **Capability:** `recall`, `learn` for product catalog.
      - **Gap:** Real-time inventory check and a dynamic recommendation engine based on visual fit or past purchases.
    - **Problem:** Repetitive Return Processing.
      - **Capability:** SakTan.
      - **Gap:** Ability to generate return labels programmatically and update order status in the e-commerce backend.
  - **5. Content Creator / Solopreneur**
    - **Problem:** Repetitive Content Repurposing (YouTube to Blog to Twitter).
      - **Capability:** SakSit (content) + SakJules (automation).
      - **Gap:** Ability to process long-form audio/video directly (whisper integration) to extract text, and integration with posting scheduling tools (Buffer, HootSuite).
    - **Problem:** Repetitive Email Triage & Fan Engagement.
      - **Capability:** SakTan.
      - **Gap:** Direct integration with Gmail/Outlook with read/write access and draft generation capabilities.

- [x] Identify capability gaps: what new skills or tools would be needed to be effective for these businesses?
  - **Summary of Gaps:** Across all archetypes, the core missing link is **third-party integration tools**. The Sak Family Agent handles text/logic beautifully via its personas, but needs standard APIs (Calendly, Shopify, Gmail, social media platforms) to execute actions. Additionally, handling rich media (audio/video transcription, large PDFs) is a recurring bottleneck.

#### Part C: MVP Definition & Strategy

- [x] Based on the analysis, select the single most promising combination of (Business Archetype + Solvable Problem).
  - **Selection:** Local Service Business (e.g., Plumbers, Cleaners) + Repetitive Pricing & Service Quotes. This provides immediate value and requires minimal custom integrations (mostly Q&A from a price book).
- [x] Define a highly specific Minimum Viable Product (MVP) for this combination.
  - **MVP Definition: "ServiceQuoteBot"** A Telegram-based agent (leveraging SakTan and SakThai) that ingests a local service business's price book and FAQs. It provides instant, accurate quotes or service info to customers 24/7, capturing leads in the process.
- [x] Outline a low-risk monetization strategy for this MVP.
  - **Monetization:** A "Done-for-you" one-time setup fee ($200 - $500) plus a flat monthly hosting/maintenance fee ($50 - $100/month). Low risk as it relies on existing platforms (Telegram) and requires no custom app development.

---

### Phase 7 — ServiceQuoteBot Execution ✅ (2026-07-02 → ongoing)

- [x] **ServiceQuoteBot scaffold** built — quoting engine structure created at `services/servicequotebot/`
- [x] **Pricing templates** defined per archetype (local service, digital marketing, e-commerce)
- [x] **Integration with Composio** for Google Sheets-based price book ingestion
- [x] **Target customer identified** — Beer's friend's business (web app project)
- [ ] **Customer outreach** — pending first deployment
- [ ] **Revenue tracking** — metrics dashboard setup

---

## 🔑 Key Principles for This Work

1. **Plan first, act second.** Update this PLAN.md before making edits.
2. **Surgical edits.** Change only what the task needs; preserve surrounding style.
3. **One persona at a time.** Finish and verify before moving to the next.
4. **No duplication.** Shared content (Charge, Principles, Operating Contract)
   lives in root `SOUL.md` — persona SOULs are lean and persona-specific.
5. **Protect Beer first.** No-cost, low-risk solutions always preferred.
