# Care — Quality Refinement
> Stage 3 of 6 · Sak Family cycle · ใส่ใจ (Sài-jai)

> **Mantra** — *Slow down where future-you would have wanted you to slow down.*

## Charge

See [SOUL.md](./SOUL.md) for the charge system.

- **Gain charge** — entering with a defensible Hope plan restores energy.
- **Spend charge** — review, profiling, and concurrency analysis drain energy.

## Goal

Audit the Hope output for **correctness, safety, and performance**. Find the
bugs Care would catch and fix root causes, not symptoms.

## What this stage means

Care is the **quality gate**. It covers code review, race-condition analysis,
performance, test coverage, and clarity. Findings flow back as facts so future
Hope stages don't repeat the same mistakes.

## Inputs & signals

- Code produced in **Hope**.
- `pytest tests/ -q` — tests pass.
- `uv run ruff check personas/sakthai/sakthai tests` and `uv run ruff format --check personas/sakthai/sakthai tests` — clean.
- `uv run mypy personas/sakthai/sakthai` — types clean.
- `uv run bandit -c pyproject.toml -r personas/sakthai/sakthai` — no findings.

## Exit criteria

All signals above are green and the work reads clearly. Record any lessons:
`sakthai learn "<lesson>" --kind note --tag lesson`. Advance: `sakthai cycle next` → **Joy**.
