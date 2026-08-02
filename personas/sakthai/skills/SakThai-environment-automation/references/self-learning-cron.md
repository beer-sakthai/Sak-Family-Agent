# Self-Learning Cron Pattern

A reusable cron pattern where an agent autonomously learns new things in a domain, tracks what's been covered to avoid repeats, and improves its own skills based on each discovery.

## When to use

- User asks you to "learn about X every N minutes" or "continuously improve knowledge about Y"
- You need a recurring research + skill-improvement loop
- Any scenario where an agent should autonomously expand its domain expertise over time

## Components

| Component | Purpose |
|-----------|---------|
| **Tracker file** | JSON array at `~/profiles/sakthai/cron/<domain>-topics-covered.json` — stores topics already learned to prevent repeats |
| **Cron job** | Runs on a schedule (e.g. `1m`, `5m`, `30m`) with a self-contained prompt |
| **Agent prompt** | Self-directed: read tracker → pick new topic → research → improve skill(s) → update tracker → report |
| **Skill updates** | Each tick either patches an existing skill (`skill_manage action='patch'`), creates new reference files, or creates a new umbrella skill |

## Topic tracker format

```json
[
  "Inference Endpoints scale-to-zero configuration",
  "Datasets Parquet SQL queries via hf datasets sql",
  "Spaces ZeroGPU idle timeout settings"
]
```

The cron agent reads this first, picks a topic NOT in the list, researches it, then appends it.

## Key prompt elements

1. **Read the tracker** — always check before picking a topic
2. **Pick something new** — scan the domain broadly, don't narrow too fast
3. **Research** — use `web_search` for real, non-trivial information
4. **Improve a skill** — patch existing, create new, or add reference files
5. **Update the tracker** — write the full updated JSON back

## No-repeat enforcement

The JSON tracker is the source of truth. The agent:
1. Reads the full list
2. Selects a topic not in it
3. After completion, writes back `[...existing..., "new topic"]`

Simpler than hash-based or date-based dedup and works well for 50-200 topics.

## Pitfalls

- **Overspecified topic names** — a topic like "Spaces" is too broad; one tick covers it and blocks all future Spaces learning. Prefer narrow, specific topics.
- **Running out of topics** — ensure the domain has enough depth (HF has 200+ subtopics). For smaller domains, use `5m` or `10m` instead of `1m`.
- **Empty tracker on first run** — the prompt must handle `[]` as a valid state. Never let the job fail on missing file.
- **Skill_manage in cron** — IS available as a core agent tool. Use it to patch/create skills from within the cron prompt.

## Deployment reference

The HF continuous learning job (`HF Learn & Improve Skills`, job_id: `85e01dd6da53`) runs every 1 minute with tracker at `~/profiles/sakthai/cron/hf-topics-covered.json`. Each tick researches a new HF topic and updates an existing skill, creates a new one, or appends to a cumulative reference.
