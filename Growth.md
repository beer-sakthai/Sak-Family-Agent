# Growth — Evolution
> Stage 6 of 6 · SakThai cycle · เติบโต (Dtə̀əp-dtoo)

> **Mantra** — *The cycle ends by teaching the agent to start the next one smarter.*

## Charge

See [SOUL.md](./SOUL.md) for the charge system.

- **Gain charge** — entering Growth with a trusted system restores energy.
- **Spend charge** — curating memory and skills takes cognitive effort.
- After Growth, charge resets as you re-enter **Dream** with a refreshed agent.

## Goal

Capture what this cycle taught you and fold it back into the agent's long-term
memory and skills. Growth **closes the cycle** and feeds directly into the next
Dream — every Dream after the first starts with a better-equipped agent.

## What this stage means

Growth is where lessons become durable. Promote scattered facts into a clean,
consolidated memory and codify reusable instructions as skills.

## Inputs

- A stable, trusted system from **Trust**.
- Accumulated facts and observations in `~/.sakthai/memory.db`.
- The skills under `skills/`.

## Do

- `sakthai learn "<lesson>" --kind lesson --tag growth` — record what you learned.
- `sakthai memory consolidate` — fold older facts into observations.
- `sakthai skills create <name>` — codify a reusable instruction, if one emerged.

## Exit criteria

The cycle's lessons live in memory/skills and charge is reset. Advance:
`sakthai cycle next` → back to **Dream**, smarter than before.
