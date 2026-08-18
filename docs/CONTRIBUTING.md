# Contributing to sakthai-agent (v2)

Thanks for your interest in `sakthai-agent`. This document explains how the
project is organized, how to set up a development environment, and the bar that
changes must clear before they land on `main`.

## A note on licensing

This repository is the active, clean from-scratch rewrite of the core engine,
and is currently maintained as a **personal project**. As noted in the
[README](README.md), the source is provided for reading and learning. External
pull requests are not actively solicited, but if you have access to contribute,
the workflow and quality bar below apply to every change.

## Project layout

```
sakthai/     the package (memory, agent, mcp, cycle, skills, dashboard, cli)
tests/       unit tests (hermetic — no network, no GCP)
skills/      top-level skills (sakthai-personal, sakthai-cycle-*)
library/     curated library of SakThai's own skills, grouped by category
docs/        architecture and capabilities docs
scripts/     bootstrap.sh, setup-extensions.sh
data/        memory snapshot format + a sample export
```

See [`docs/architecture.md`](docs/architecture.md) for the full data-flow
diagram and [`CLAUDE.md`](CLAUDE.md) for the architectural ground rules.

## Development setup

Python **>= 3.11** is required (CI runs on 3.11 and 3.12).

This project uses `uv` for dependency management. See `skills/sakthai-coding-uv/SKILL.md` for the full workflow.

```bash
cp .env.example .env          # then fill in ANTHROPIC_API_KEY
uv sync --extra dev           # Install project and development dependencies
uv sync --all-extras          # Install all optional dependencies
```

Verify your environment with `sakthai doctor` and `sakthai setup`.

## The quality bar

CI runs a fixed sequence on every pull request, and **green CI is the bar for
`main`.** Run the same checks locally before pushing:

```bash
uv sync --all-extras                                         # see note below
uv run ruff check personas/sakthai/sakthai tests             # lint
uv run ruff format --check personas/sakthai/sakthai tests    # format (drop --check to apply)
uv run mypy personas/sakthai/sakthai                         # strict type-check
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai  # security scan
uv run pytest -m "not integration" -q                        # unit suite, as CI runs it
```

To run a single test file:

```bash
uv run pytest tests/test_memory_store.py -q
```

Notes:

- **The package lives at `personas/sakthai/sakthai/`.** There is no root-level
  `sakthai/` directory; `import sakthai` resolves there through the editable
  install.
- **`uv sync --all-extras`, not plain `uv sync`.** `hypothesis` lives in the
  `dev` extra, and `tests/test_store_properties.py` fails collection without
  it — which aborts the whole run.
- **`mypy` is `strict`** over the package, with one exemption:
  `sakthai.telegram.*`. Keep all other new code strict-clean.
- **`ruff` excludes `library/` and `scripts/`,** and `mypy` only covers
  `personas/sakthai/sakthai`. Don't "fix" lint or types in those trees.
- **Tests must stay hermetic** — no network calls and no GCP credentials. Inject
  clients and stores rather than reaching out.
- A **secret scan** (gitleaks) runs first in CI. Never commit secrets; `.env` is
  gitignored and only `.env.example` is committed.

## Architectural ground rules

These conventions keep the package small and strictly layered. Please respect
them:

- **The memory store is the seam.** Anything that touches SQLite goes through
  `MemoryStore` (`sakthai/memory/store.py`). Schema changes are additive
  migrations in `_migrate_schema()` (`ALTER TABLE` only, under
  `BEGIN IMMEDIATE`).
- **Tools are defined once.** Add a tool to `BUILTIN_TOOLS` in
  `sakthai/agent/tools.py` and it appears in both the agent loop and the MCP
  server via `agent/registry.py`. Don't bypass the registry.
- **Paths live in `config.py`.** Nothing else hard-codes a path; new paths go
  there.
- **Auth goes through `auth.py`.** Call `resolve_anthropic_client()` (and the
  matching resolvers) rather than constructing a client directly.
- **Sandbox defaults are deliberate.** `read_file` is restricted to cwd +
  `~/.sakthai` + `SAKTHAI_READ_ALLOW`; `run_command` is opt-in via
  `SAKTHAI_SHELL_ALLOW`. Don't widen these without a clear reason.

The original `SakThai-Agent` (v1) is a read-only blueprint: consult it for
intent, but never copy its code or layout into this repo — re-derive everything.

## Commit and pull-request guidelines

- Write clear, descriptive commit messages explaining the *why*, not just the
  *what*.
- Keep each change focused; prefer small, reviewable PRs.
- Make sure the full local check sequence above passes before you open a PR.
- Update relevant docs (`README.md`, `docs/`, `CLAUDE.md`) when behavior or
  conventions change.

## Review policy for `main`

**Every pull request into `main` gets an approving review from someone other
than its author before it merges.** Most PRs here are opened by an agent —
`claude/*` branches, Sentinel security fixes, Dependabot bumps — and the
repository owner is the reviewer for those: read the diff, then leave a GitHub
**Approve** review before merging, rather than merging straight from the
mergeable state.

This is one extra click and it is not bookkeeping. It is the only thing that
distinguishes "an agent changed `main`" from "a change to `main` was seen by a
second party", and an agent-opened PR is exactly the case where that
distinction matters most.

Two consequences worth knowing:

- **Self-authored PRs cannot satisfy it.** GitHub does not let you approve your
  own pull request. A change you author yourself either waits for a second
  reviewer or merges unreviewed — and merges unreviewed should be the rare,
  deliberate case, not the default.
- **It is measured.** OpenSSF Scorecard's Code-Review check counts, over a
  window of recent changesets on the default branch, how many carried a review
  with state `APPROVED` from a login other than the author's. Nothing else
  counts: not a comment, not a passing CI run, not the merge itself. The score
  moves only as reviewed changesets enter that window, so it responds to the
  habit, not to any one PR. See
  [`code-scanning-sweep-2026-08-12.md`](code-scanning-sweep-2026-08-12.md) for
  the full mechanism and the standing alert this policy answers.

Do **not** automate the approval. A workflow that has a bot approve every PR
would satisfy both the branch-protection setting and the Scorecard check while
removing the only thing either one is for.

## Automatic merge

`.github/workflows/auto-merge.yml` lets a pull request merge itself once it is
*allowed* to — it never changes what "allowed" means.

Apply the **`automerge`** label to a PR and the workflow turns on GitHub's
native auto-merge for it (squash). GitHub holds the PR until every
branch-protection requirement on `main` is met — required checks green **and**
the non-author approving review described above — then merges it. Remove the
label to turn auto-merge back off. A draft PR is skipped and picked up
automatically when it is marked ready for review.

What this does *not* do, deliberately:

- It does not approve anything. The review above still has to happen, by a
  person, before the merge fires. The label says "merge this once it is allowed
  to merge"; it does not say "merge this".
- It does not apply itself. The label is a per-PR opt-in — nothing merges
  because it matched a branch pattern or an author.
- It is not for dependency bumps. `auto-dependency-update.yml` opens those as
  drafts on purpose: a freshly published malicious version passes tests as
  happily as a good one, so a person reads the diff. Labelling one is a
  deliberate override, not the default.

Prerequisites, all in repository settings:

- **Allow auto-merge** must be on (Settings → General → Pull Requests). Without
  it the workflow fails with "Auto-merge is not allowed for this repository".
- **Allow squash merging** must be on, or change `MERGE_METHOD` in the workflow
  to `--merge`.
- `main` must have branch protection with required checks and a required
  approving review — that protection *is* the gate; auto-merge only waits on it.
- The `automerge` label must exist: `gh label create automerge -c 0E8A16 -d
  "Merge once checks pass and the PR is approved"`.
- `GH_PAT_FOR_ACTIONS` is optional but preferred. A merge attributed to the
  ambient `GITHUB_TOKEN` does not trigger the `push: main` workflows (CI,
  SonarCloud, Scorecard), and `self-healing-ci.yml` keys off CI completing on
  `main`.

To do the same thing by hand on a single PR, without the label:

```bash
gh pr merge <number> --auto --squash
```

## Reporting security issues

Please do **not** open public issues for security vulnerabilities. Follow the
process in [`SECURITY.md`](SECURITY.md) instead.
