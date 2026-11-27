---
name: SakThai-hf-journey-narratives
version: 1.6.0
description: Create narrative content about your Hugging Face ecosystem journey —
  tweet threads, blog posts, HF forum posts, retrospectives, and collection notes
  — for self-improvement crons, social sharing, and community engagement
category: mlops
tags:
- branding
- content-creation
- ecosystem
- hf
- huggingface
- journey
- narrative
- narratives
- storytelling
author: SakThai
license: MIT
trigger: On cron-based self-improvement tasks that create "one piece of content about
  our HF journey", when writing about the ecosystem story for social platforms, when
  composing collection notes or retrospective entries, when running "Brand Storytelling"
  or "Content Creation" cron jobs
---

# HF Journey Narratives

**Area:** Hugging Face / Content & Brand
**Tags:** `brand-storytelling`, `content-creation`, `journey-documentation`, `tweet-threads`, `cron-self-improvement`

## Purpose

Create narrative content about the SakThai HF ecosystem journey for recurring self-improvement crons, social sharing, and community engagement. This skill covers one specific class of work: **telling the story of our HF ecosystem** — not reporting its health, but crafting the narrative around it.

This is distinct from:
- `hf-ecosystem-health-check` — quantitative data gathering and gap analysis
- `hf-model-card-yaml-widgets` — YAML metadata for individual model cards
- `hf-hub-collections` — programmatic collection management

## When to Use

- Cron job fires for "create one piece of content about our HF journey"
- Running "Brand Storytelling" or "Content Creation" cron jobs
- Drafting a tweet thread, blog post, or HF forum post about the ecosystem
- Writing a retrospective or "state of the ecosystem" narrative
- Updating the collection description or cross-platform bio

## Content Types

### Canonical Narrative Document

Before creating any content below, ensure a **canonical narrative document** exists at the repo root (e.g., `HOUSE_OF_SAK.md`). This single source of truth for the origin story, agent roster, and ecosystem inventory prevents narrative drift across model cards, dataset cards, and collection descriptions. See [`references/canonical-narrative-document.md`](./references/canonical-narrative-document.md) for the full pattern with templates and maintenance schedule.

Rotate between these types across runs — never repeat the same type consecutively:

| Type | Length | Best For | Frequency |
|------|--------|----------|-----------|
| **Tweet thread** | 6–10 tweets | Quick narrative, shareable, low barrier | Every 3–4 runs |
| **Model card improvement** | Full card | SEO, discoverability, thin cards | Every 2–3 runs |
| **Collection note** | 1–2 paragraphs | Summarizing the collection's purpose | Every 5–6 runs |
| **HF forum post** | 300–500 words | Community engagement, feedback | Every 4–5 runs |
| **Blog / LinkedIn draft** | 1000–1500 words | Long-form authority building, dev.to / HF Community / Hashnode cross-posting, SEO | Every 6–8 runs |
| **Ecosystem retrospective** | Structured sections | Milestone documentation | Every 10 runs |
| **Multi-purpose narrative essay** | 6-chapter origin story (3K-4K words) | Collection README + tweet thread blueprint + journal milestone | Every 6-8 runs |
| **Collection description** | <150 chars | Profile visibility, SEO | As needed |
| **Dataset card improvement** | Full card | Zero-download dataset rescue, SEO, discoverability | Every 4–5 runs |

## Workflow

### 1. Gather Current Ecosystem Data

**Light mode for content creation.** Unlike health-check crons that need full 25-API-call scans, narrative pieces only need a handful of data points. Gather these with minimal API calls:

```python
from huggingface_hub import HfApi
api = HfApi()

# One-shot: get all models sorted by downloads
models = list(api.list_models(author="Nanthasit"))
models.sort(key=lambda m: m.downloads or 0, reverse=True)
total_dl = sum(m.downloads or 0 for m in models)
zero_dl = [m.modelId for m in models if (m.downloads or 0) == 0]
top3 = models[:3]
```

**Key data points to collect (content creation only):**
- Total model downloads (across all 12+ models)
- Top 3 most-downloaded models with exact counts
- Zero-download count and names (honesty metric)
- Days since project started (from git log or memory)
- One notable delta since last content piece (if any)
- **Collection README status** — if the collection has no readme, that's a discoverability gap worth filling with narrative

Skip dataset stats, Spaces likes, CI status, collection counts, and trending analysis unless they directly support the narrative angle chosen in step 3. These are health-check concerns, not narrative inputs — every extra stat dilutes the story.

**Full mode** (for health-check reports or retrospective pieces that catalog everything): use the full scanning pattern documented in `hf-ecosystem-health-check`. Only reach for this when the content type is "Ecosystem retrospective" or the audience is technical and expects completeness.

### 2. Read Previous Content

Always read the end of `LEARNING_JOURNAL.md` first to understand:
- What was covered in the last 3–5 entries (avoid repetition)
- The formatting conventions used
- The "Next Run Target" from the last entry — it may suggest what type to do next

```bash
tail -100 /opt/data/LEARNING_JOURNAL.md
```

### 3. Choose the Right Angle

Map content type to current ecosystem state, and check the journal's "Next Run Target" from the last entry — that field is designed to guide the next choice:

| If ecosystem is... | Best angle | Content type |
|--------------------|------------|--------------|
| Stagnant (no growth) | Honest about struggles, what's being tried | Tweet thread |
| Growing (new downloads) | Success signal, celebrate small wins | Tweet thread or blog draft |
| CI broken | Transparent about fixing it, technical deep-dive | Forum post |
| New asset published | Showcase the new asset, explain why it matters | Model card update |
| Milestone reached | Retrospective, lessons learned | Blog draft or retrospective |
| Collection has no README | Fill gap with origin story | Multi-purpose narrative essay |

When the "Next Run Target" lists specific options, pick the highest-priority one that hasn't been done yet and isn't blocked by external factors. If it suggests a content type not in the rotation table (e.g. "collection description"), it overrides the table for this run — the target field is authored with full context of what's most needed.

#### Narrative Framing: Tier Analysis for Growth Content

When the ecosystem shows real download growth (models moving from 0 to non-zero, total downloads increasing), the most compelling narrative structure is **tier analysis** — grouping models by download volume into tiers that tell a layered story:

**Tier 1 — Breaking 1K (the leaders)**
Models approaching or exceeding 1,000 downloads. These are the flagship assets — they validate the project's core value proposition. Name them specifically with exact counts and percentage growth since last check.

**Tier 2 — Steady Growth (the core family)**  
Models with 100+ downloads growing consistently. These show the ecosystem has depth — it's not just one-hit-wonder. Percentage growth (+X%) matters more here than raw numbers.

**Tier 3 — Zero-to-Hero (the breakout story)**
Models that had 0 downloads in the last journal entry but now have real traction. This is the most emotionally compelling tier — it proves the ecosystem is reaching new users. Always call out the "from 0!" framing explicitly.

**Tier 4 — Unchanged / Stalled (honesty slot)**
Models still at 0 or unchanged since last check. Include at least one line about these — honesty about what isn't working builds more credibility than omitting them.

**Template for a growth narrative:**

```
**Tier 1 — Breaking 1K (the leaders)**
- [Model A]: X dl (+Y% from Z) ← our flagship
- [Model B]: X dl (+Y% from Z) ← closing in on 1K

**Tier 2 — Steady growth (core family)**
- [Model C]: X dl (+Y% from Z)
- [Model D]: X dl (+Y% from Z)

**Tier 3 — From 0 to real traction (the breakout story)**
- [Model E]: X dl (from 0!) ← first traction in category
- [Model F]: X dl (from 0!) ← people testing new modality

**Total ecosystem downloads:** ~X (up from Y baseline)

**Key insight:** [One-sentence pattern or observation about the data]
```

This structure works across multiple output formats:
- **Journal entries**: Use the template as-is with full model names and exact counts
- **Tweet threads**: One tier per tweet, with the Zero-to-Hero tier as the hook
- **Collection descriptions**: Condense to "X models breaking 1K, Y growing steadily, Z went from 0 to real traction"
- **Blog posts**: Each tier becomes a section with a short narrative paragraph

The tier pattern also naturally produces the **"honest constraint"** element — naming the stalled models in Tier 4 prevents the piece from reading like pure self-promotion.

#### Origin Story Framing (for static or milestone-based content)

When the ecosystem has **no growth to report** — downloads unchanged, no new assets — use **origin story framing** instead of tier analysis. Origin stories turn a "nothing changed" report into evergreen content that never expires.

**When to use:**
- All download counts identical to last snapshot
- Commemorating a milestone (ecosystem birthday, N downloads crossed, first N models)
- The collection has no README and needs narrative context
- The content type is a narrative essay, retrospective, or collection description

**Structure — The 6-Chapter Arc:**

| Chapter | Focus | Content |
|---------|-------|---------|
| **1. The First Model** | Origin | When and why it started, the constraints, the first asset |
| **2. The Family Grows** | Inventory | Current ecosystem: models, datasets, Spaces — names and counts |
| **3. The Economics of Zero** | Credibility | Every component's cost ($0), the budget constraint as a feature |
| **4. The Architecture** | Design | How it fits together — agent family, shared memory, interconnected models |
| **5. The Distribution** | Metrics | Download tiers, what's working, top vs long-tail |
| **6. What We Learned** | Depth | Honest lessons from the journey |
| **Coda: The Next Frontier** | Forward | What's next, even without growth |

**Key properties of origin story framing:**
- **Timeless** — the content is valid regardless of download growth
- **Multi-purpose** — one piece serves as collection README, tweet thread, and journal entry simultaneously
- **Emotion-first** — lead with the constraints (shelter, $0, one person) before the numbers
- **Honest constraint included** — always name what's NOT working (zero likes, stalled models, no demos)
- **No fake growth** — if downloads haven't moved, don't pretend they have. The story IS the content.

**Template for the opening hook (stakes technique):**

```
*Six agents. Twelve models. Four datasets. Two Spaces. One home. Zero budget.*

**How we built an AI ecosystem from a shelter.**

In [month year], the [name] crossed [N] downloads on Hugging Face. That number is small by platform standards. But every single one of those downloads represents [brief: constraints + defiance].
```

**Reference** See `references/multi-purpose-narrative-pattern.md` for the full 6-chapter template with word counts and per-section writing techniques.

### 4. Compose with SakThai Voice

Essential tone rules:

- **Honest first**: If downloads grew by 0, say so. If CI is red, say so. Never fabricate metrics.
- **Specific over generic**: "942 downloads on the 1.5B model" not "our models have been downloaded"
- **Human-scale**: Include $0 budget, one-person team, homeless situation context when relevant
- **Forward-looking**: End every piece with what's next — it implies momentum
- **No AI-isms**: Strip "I'm excited to share", "I'm thrilled to announce", "without further ado" — see `creative/humanizer` skill
- **Short sentences**: Concise builds credibility. Favor sentence fragments over compound sentences.
- **One narrative thread**: Each piece tells ONE story (e.g., "smaller models beat bigger ones" not "we have 14 models and also CI is broken")

### 5. Format the Output

**For LEARNING_JOURNAL.md entries**, use standard format:

````markdown

---

## Deep Dive Reference

For exhaustive reference specifications, cookbook snippets, and extended documentation, see [Journey Narrative Log Templates & Historical Entries](./references/narrative-log-templates.md).
