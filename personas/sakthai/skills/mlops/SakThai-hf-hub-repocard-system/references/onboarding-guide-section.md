# Onboarding Guide Section for Model Cards

**File:** `references/onboarding-guide-section.md`
**Skill:** `hf-hub-repocard-system`
**Purpose:** Document the pattern for adding a "Not Sure Which Model to Use?" decision-table onboarding section to any model card in a multi-model ecosystem.

## When to Add

- The ecosystem has 5+ sibling models across different sizes/modalities
- New visitors land on a single model page and have no way to discover siblings
- The model card already has technical documentation but lacks orientation for newcomers
- Download counts show a wide gap (flagship has 1K+, niche models have <50) — cross-promotion is needed

## Anatomy of an Onboarding Guide

### Section Heading

Use a clear, inviting heading that signals **orientation, not promotion**:

```
## 🎯 Not Sure Which Model to Use?
```

### Table Structure

| Column | Content | Example |
|--------|---------|---------|
| **You want…** | Use case description — short, human, goal-oriented | "A capable everyday assistant" |
| **Use this** | Model name + link + optional emphasis | [`sakthai-context-1.5b-merged`](link) 🏆 *flagship* |
| **Hardware** | Minimum viable hardware | CPU (1 GB) / GPU (4-6 GB) |
| **Downloads** | Current download count | 1,197 ⬇️ |

**Key rules for the "Use this" column:**
- Always embed a direct HF link to the sibling model
- Always mark the current model page with a clear **"You are here"** indicator (bold + emoji)
- Optionally mark the flagship/best-seller with a trophy or badge
- Include at least one tool-calling variant if available

### Placement

Place the onboarding guide **early in the card** — after the origin story / narrative section but before technical sections (specs, benchmarks, usage):

```
# Title + Badge row
## House of Sak (narrative)
## 🎯 Not Sure Which Model to Use?   ← HERE
## Pipeline Integration
## Model Details
## Quick Start
...
```

**Why here:** A visitor arrives, reads who built the model (narrative), then the very next thing they see is a table that says "if you're looking for X, use this model instead" — before they've invested time in technical details. This is the most effective moment for cross-discovery because the visitor is still orienting themselves.

**Do NOT place it:**
- At the bottom (visitors never scroll that far before deciding)
- After technical benchmarks (the decision is already made)
- Before the model name/badges (visitor needs to know what page they're on first)

### Model Coverage

Include ALL major sibling models, organized by use case. Grouping by scenario (not by size or download count) makes the table scannable:

- General-purpose: at least 2-3 size options (small/medium/large)
- Specialized: tool-calling variants, code model, vision, embeddings, TTS
- If a sibling is auth-gated (private), mark it as `(private)` instead of linking — don't create 401 dead ends

### "You Are Here" Marker

The current model's row should be visually distinct:
- Bold text
- Emoji (🖼️ for vision, 💻 for coder, 🗣️ for TTS, 🌐 for embeddings)
- Text: **"You are here"** or **"← you are here"**

### Pro-Tip CTA

After the table, add a one-liner that points to more context:

```
**Pro tip:** The real power is combining models — see the Pipeline Integration section below.
```

This gives the visitor a natural next step after orientation.

## Pitfalls

### 1. Stale download counts

The download column contains **static numbers**. These go stale within days/weeks. Mitigations:
- Prefer a note above the table: `(downloads as of <date>)`
- Update the entire table when any count changes significantly
- Accept that dynamic badges aren't practical inside a markdown table — static counts are a trade-off for scannability

### 2. Missing sibling coverage

It's tempting to list only the top 3-4 models, but that means visitors with niche needs (code, vision, TTS, embeddings) never discover those models. Cover all distinct modalities/use cases, even if the table is long. A long table that covers everything is better than a short table that sends visitors to dead pages.

### 3. Hardware column oversimplification

"CPU" or "GPU" is not enough — be specific about RAM/VRAM:
- `CPU (512 MB)` vs `CPU (1 GB)` vs `GPU (4+ GB)`
- This helps visitors self-qualify and prevents frustration from trying to run a 7B model on a phone

### 4. Forgetting to mark the current model

Without a "You are here" marker, the visitor doesn't know where they are in the table. This wastes the orientation value — they see a list of models but can't map it to the page they're on.

### 5. Over-promotion tone

The table should feel helpful, not promotional. Avoid:
- Excessive emoji or exclamation points
- Overhyping one model ("BEST MODEL EVER")
- Marketing language ("limited time", "amazing")
- Favor functional descriptions: "Long document analysis" not "Super-powered long-context AI"

### 6. Breadth vs. depth on "You want…" column

Too vague: `"Need text generation?"` — every model does text generation.
Too narrow: `"Need to analyze a 128K token financial document?"` — only fits one model.
Just right: `"Long document analysis"` — describes the use case without over-specifying.

## Real Examples

### Vision-7B Onboarding Table (added 2026-07-26)

The `sakthai-vision-7b` card (45 dl) received this addition after the "House of Sak" section:

```
| You want… | Use this | Hardware | Downloads |
|-----------|----------|:--------:|:---------:|
| A general chatbot on a laptop | sakthai-context-0.5b-merged | CPU (any) | 994 ⬇️ |
| A capable everyday assistant | sakthai-context-1.5b-merged 🏆 flagship | CPU/GPU | 1,197 ⬇️ |
| Production-quality responses | sakthai-context-7b-merged | GPU (4-6 GB) | 562 ⬇️ |
| ... | ... | ... | ... |
| **Image understanding** | **🖼️ sakthai-vision-7b** ← you are here | **GPU (4+ GB)** | **45 ⬇️** |
| ... | ... | ... | ... |
```

**Context:** The vision-7b was the highest-download under-50 model. Its card had comprehensive technical docs but no way for visitors to discover sibling models. The onboarding table doubled as a cross-promotion hub.

## When to Skip This Section

- **Single-model ecosystem:** If there's only one model, no onboarding needed.
- **Highly specialized page:** A model card for a niche fine-tune where visitors arrive with a clear goal (e.g., "I need a Thai tokenizer") doesn't benefit from a general-purpose table.
- **Already has equivalent section:** Some cards may have "Family Links" or "Sibling Models" tables that serve a similar function — don't duplicate if orientation is already covered.
