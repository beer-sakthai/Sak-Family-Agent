# Canonical Narrative Document Pattern

## What

A **canonical narrative document** is a single markdown file at the repo root that serves as the definitive origin story, family roster, ecosystem inventory, and operating principles for a multi-asset AI ecosystem. Every model card, dataset README, Space description, and collection note references it rather than re-telling its own version of the story.

This eliminates narrative drift between assets — the single most common consistency failure in growing ecosystems.

## File

`HOUSE_OF_SAK.md` at the repository root (`Sak-Family-Agent/HOUSE_OF_SAK.md`).

Example structure used in the House of Sak:

```markdown
# House of Sak 🏠

> *"We are one family — and becoming more."* — **Beer (beer-sakthai)**

[One-paragraph elevator pitch: who, where, budget, mission]

## The Story

[Origin narrative — creator's journey, pivotal moment, motivation]

## The Agent Family

[Agent table: name, role, status (active/retired)]

## The Ecosystem

[Asset table: models, datasets, Spaces, with counts and descriptions]

## Key Links

[HF collection, GitHub, leaderboard, demos]

## Operating Principles

[Zero-cost, energy cycle, shared memory, self-improving]

## License
```

## Benefits

| Why | What it prevents |
|-----|-----------------|
| Single origin story | Cards drifting to different angles on the same story |
| One agent roster | "6 AI agents" vs "4 active" confusion across cards |
| Stale ecosystem counts | Model/dataset counts derived from API, not narrative |
| Consistent tagline | "one shared mind" vs "one shared memory" across 5 surfaces |
| New card onboarding | New model cards just link to the canonical doc instead of rewriting the story |

## How to use with model cards

Every model card should carry the following in its body (after technical content):

```markdown
## The House of Sak

Part of the **House of Sak** — [brief one-liner].

[Learn more about the House of Sak →](https://github.com/beer-sakthai/Sak-Family-Agent/blob/main/HOUSE_OF_SAK.md)
```

Plus the YAML tag: `- house-of-sak`

## How to use with dataset cards

Same pattern — add a `🏠 The House of Sak` section after the dataset description, before technical sections:

```markdown
## 🏠 The House of Sak

This dataset is part of the **House of Sak** — [one-liner]. Created by Beer from a shelter in Cork, Ireland with $0 budget.
```

Plus YAML tag: `- house-of-sak`

## How to use with collection descriptions

The collection is the most-visited entry point (every model card links to it). Description is capped at **150 characters**. Reference the canonical doc's key themes:

```
Six AI agents, one shared mind. 12 models, 4 datasets, 2 Spaces built from a shelter with $0 budget. One family, one home.
```

Key: lead with the **family/people** (agents) before the **stuff** (models/datasets).

## Maintenance

- **Update the canonical doc first** when the family changes (new agent, milestone, agent retirement). Propagate to cards second.
- **Re-check collection descriptions quarterly** — they have the most visibility and the tightest char limit, so they drift fastest.
- **Re-check model cards every 3-4 enrichment cycles** — new cards added since the canonical doc was created may lack references to it.
- **Cross-source audit** every month: compare canonical doc agent roster against model card taglines, collection description, and GitHub README. Flag any that diverge.
