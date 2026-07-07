---
name: SakKing-coding-uv
category: coding
description: Manage sakthai-agent-v2's dependencies and environment with uv — the Rust-based installer/resolver this repo standardizes on. Use when adding/upgrading deps, syncing the venv, locking, or running the CI sequence locally.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - coding
      - python
      - uv
      - dependencies
      - tooling
    related_skills:
      - sakthai-coding-type-safety
      - sakthai-coding-testing
      - sakthai-coding-skill-authoring
---

# sakthai-coding-uv

`sakthai-agent-v2` standardizes on **uv** (Astral's Rust package manager) with a
committed **`uv.lock`** for reproducible builds. uv resolves and installs 10–100×
faster than pip and replaces pip / pip-tools / poetry for this repo. The OG used
`pip install -e`; **v2 does not** — defer to uv here.

## When to use this skill

- Adding, upgrading, or removing a dependency in `pyproject.toml`
- Recreating or syncing the project virtualenv (`.venv/`)
- Regenerating or verifying `uv.lock`
- Running the lint → format → mypy → bandit → pytest CI sequence locally
- Reproducing a CI failure that only happens with locked deps

## Core workflow

```bash
uv sync                       # create .venv + install from uv.lock (reproducible)
uv sync --extra dev           # include the dev extra (ruff, mypy, pytest, bandit)
uv sync --all-extras          # dev + dashboard + cloud
uv run <cmd>                  # run a tool inside the project env (no manual activate)
```

`uv sync` is the workhorse: it makes the environment exactly match the lockfile.
Use `uv run` to invoke tools — it guarantees the project env without sourcing
`.venv/bin/activate`.

## Managing dependencies

```bash
uv add httpx                  # add a runtime dep, update pyproject + uv.lock
uv add --dev mypy             # add to the dev extra
uv add 'anthropic>=0.40'      # version constraint
uv remove httpx               # drop a dep
uv lock                       # re-resolve and rewrite uv.lock (no install)
uv lock --upgrade-package ruff  # bump one package within constraints
```

**Always commit `pyproject.toml` and `uv.lock` together.** A drifted lockfile is
the uv analog of the OG's `app/` sync failures — CI resolves against the lock, so
an out-of-date lock means non-reproducible builds.

## Running the CI sequence locally

Mirror `.github/workflows/ci.yml` before pushing — green CI is the bar for `main`:

```bash
uv run ruff check sakthai tests
uv run ruff format --check sakthai tests
uv run mypy sakthai
uv run bandit -c pyproject.toml -r sakthai
uv run pytest tests/ -q
```

CI runs this on Python **3.11 and 3.12**. To check another interpreter locally:

```bash
uv python install 3.12        # fetch an interpreter uv manages
uv run --python 3.12 pytest tests/ -q
```

## Lockfile hygiene

```bash
uv lock --check               # fail if uv.lock is stale vs pyproject (CI-style gate)
uv sync --frozen              # install strictly from lock; error if lock is stale
uv tree                       # inspect the resolved dependency graph
```

Use `--frozen` in CI/containers to guarantee no implicit re-resolution. Use
`--check` as a pre-commit gate so a forgotten `uv lock` never reaches review.

## Common pitfalls

1. **Don't mix pip into the uv env.** `pip install` into `.venv` bypasses the
   lock and creates drift uv can't see. Use `uv add`.
2. **Don't hand-edit `uv.lock`.** It's generated — change `pyproject.toml` and
   run `uv lock`.
3. **Don't forget to commit the lock.** Dependency PRs that touch only
   `pyproject.toml` leave the build unreproducible.
4. **Don't `activate` then run global tools.** Prefer `uv run` so the tool
   version always matches the lock, not whatever is on `PATH`.
5. **`ruff`/`scripts` are excluded from lint, `library/` too** — adding deps for
   those trees still belongs in `pyproject.toml`, but don't chase lint there.
