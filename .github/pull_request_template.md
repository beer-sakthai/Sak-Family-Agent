<!--
  Keep this short. The diff says what changed; this says what a reviewer cannot
  read off the diff — why, what could break, and how you would know.
  Delete any section that genuinely does not apply.
-->

## What and why

<!-- One paragraph. What this changes, and the problem it solves. -->

## Blast radius

<!-- Delete the lines that do not apply. -->

- **Package** (`personas/sakthai/sakthai/`) — changes what `import sakthai` does.
- **Guardrails / security** — touches `agent/guardrails*.py` or `web/server.py`.
  Both are copied per persona; see the sync rules in `CLAUDE.md`.
- **Workflows / CI** — changes `.github/`.
- **Personas** — touches `SOUL.md`, a skill overlay, or `personas/*/config/`.
- **Docs / tests only** — no runtime behaviour changes.

## How this was validated

<!-- Delete what does not apply; say what you actually ran, not what you could have. -->

- `uv run pytest tests/ -q --cov=sakthai --cov-branch --cov-fail-under=96`
- `uv run ruff check` / `ruff format --check` / `mypy` / `bandit`
- Ran the affected command or workflow by hand — say which.
- Relying on CI alone.

## If this is wrong, how does it surface?

<!--
  A failing test is the easy case. Say what happens if it passes CI and is still
  wrong: a silently skipped check, a workflow that goes red daily, a guardrail
  that stops denying. If the answer is "nothing would surface", say that.
-->

## Checklist

- [ ] Guardrail changes are synced across every persona copy (`tests/test_persona_guardrails_parity.py` enforces this; `web/server.py` has **no** such test — diff it by hand).
- [ ] `PLAN.md` (or the relevant sub-plan) is updated if this completes a planned item.
- [ ] No `.lock` file was hand-edited — regenerate with `scripts/gen_hash_lock.py`.
