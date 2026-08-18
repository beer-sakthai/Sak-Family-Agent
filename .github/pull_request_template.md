<!--
Keep this short. The diff is the record — this is for what the diff cannot say:
why the change exists, and what you did to convince yourself it works.
Delete any section that does not apply rather than filling it with "N/A".
-->

## What and why

<!-- What changed, and what problem it solves. Explain the *why*; the diff
     already shows the *what*. -->

## How it was verified

<!-- What you actually ran, and what it said. "Tests pass" is not verification;
     name the command and the result. If something is untested, say so here
     rather than leaving it to be discovered in review. -->

```bash
uv sync --all-extras                                        # --all-extras is required
uv run ruff check personas/sakthai/sakthai tests
uv run ruff format --check personas/sakthai/sakthai tests
uv run mypy personas/sakthai/sakthai
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai
uv run pytest -m "not integration" -q
```

## Checklist

- [ ] Local check sequence above passes (green CI is the bar for `main`)
- [ ] Coverage floor holds — `fail_under = 96`, branch coverage on
- [ ] New tests are hermetic: no network, no GCP credentials; injected
      `MemoryStore(":memory:")`, mocked provider clients, `tmp_path` for file I/O
- [ ] Docs updated where behavior or conventions changed (`README.md`, `docs/`,
      `CLAUDE.md`)
- [ ] `PLAN.md` updated if this completes a planned phase (targeted line edits
      only — never overwrite the file)

<!-- Only if you touched these: -->

- [ ] **Guardrails** — `personas/sakthai/sakthai/agent/guardrails.py` is copied
      per persona and pinned byte-identical by
      `tests/test_persona_guardrails_parity.py`. Every copy is synced, and each
      closed bypass has a regression test that pins `result.reason` (asserting
      only `action == DENY` can pass because a *different*, broader rule fired).
- [ ] **New built-in tool** — added once to `BUILTIN_TOOLS` in
      `agent/tools.py`, so it surfaces in both `sakthai run` and `sakthai mcp`;
      test added in `tests/test_tools.py`; checked whether `guardrails.py` needs
      a matching rule.
- [ ] **Schema migration** — additive only (`ALTER TABLE` under
      `BEGIN IMMEDIATE`). No dropped columns or tables.
- [ ] **Workflows** — each file is a real, loadable workflow: `.yml`/`.yaml`
      extension (GitHub silently ignores anything else, including `foo. yml`
      with a space), top-level `on:`, `jobs:` and `permissions:`, no duplicate
      keys, actions pinned by SHA. Do **not** add `.github/workflows/codeql.yml`
      — it collides with CodeQL default setup and every job fails.

## Review

Per [`docs/CONTRIBUTING.md`](../docs/CONTRIBUTING.md), every PR into `main`
needs an approving review from someone other than its author before it merges.
Green CI is not a substitute, and automating the approval is out of bounds — it
would satisfy branch protection and the OpenSSF Scorecard Code-Review check
while removing the only thing either one is for.
