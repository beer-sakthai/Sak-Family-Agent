# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`sakthai-agent` **v2.0** — a personal learning agent with persistent memory. It
gives a Claude or Gemini agent a durable SQLite memory it can read and write
across sessions, plus a shared tool registry and an MCP stdio server so the same
memory is reachable from other runtimes.

This is a **clean, from-scratch rewrite** of the original `SakThai-Agent` (the
"OG"). The OG is a read-only blueprint: consult it for intent, but never copy its
code or layout into this repository — re-derive everything. The OG's Google
ADK / Vertex AI cloud agent is **not** part of v2: there is **no `app/` cloud
bundle, no `sync-app-package.sh` sync step, and no `sakthai/cloud/` module** here.
v2 is local-first — the CLI, the agent loop, and the MCP stdio server.

---

## Monorepo Structure

This repo is the shared source workspace for the whole Sak family, not just one
package. Only `personas/sakthai/sakthai/` is a build target; everything else is
personas, deployment config, training assets, or docs.

```
personas/          the six agents + the shared package (see below)
tests/             the one pytest suite (imports `sakthai`, 134 test files)
library/           31 curated skills across 11 categories (a live skill root)
docs/              architecture, security, plans/specs under docs/superpowers/
scripts/           dev + maintenance scripts (compose_persona, export_agent_repo, …)
infra/             hermes-agents profiles, vm-agents systemd/env, pw-poc (npm), servicequotebot
services/          servicequotebot, inference-endpoint, HF dataset publishing, teams-copilot-mcp
apps/              agent_workflow_framework, sak_agent_dashboard
training/          LoRA/model runs, HF jobs, serving configs
evaluation_tasks/  lm-evaluation-harness task YAML + datasets (run-evals.yml)
sakthai-chat-cli/  folded-in copy of the standalone chat-CLI repo (see below)
product/ security/ profiles/ data/ bin/ dataset-cards/
```

`assets/` still exists on disk (two large branding PNGs) but is untracked — see
[`docs/repo-audit-2026-08-08.md`](docs/repo-audit-2026-08-08.md). The orphaned
root `skills/` directory and `migrated-repos-archive/` were removed in that same
cleanup; git history still has them.

### The persona package copies (read this before editing `sakthai/`)

`personas/sakthai/sakthai/` is **the** package: it is what `pyproject.toml`
installs (`[tool.setuptools.packages.find] where = ["personas/sakthai"]`), what
`import sakthai` resolves to, and what mypy/ruff/bandit/pytest run against.
Treat it as the source of truth for anything you are actually running.

`personas/shared/sakthai/` is the canonical *shared* copy that the other
personas point at. The wiring is **not uniform**, and the difference matters:

| Persona | How it gets `sakthai/` |
|---|---|
| `sakthai` | real directory — **the installed package** |
| `sakjules`, `saktan` | `sakthai -> ../shared/sakthai` symlink |
| `sakking`, `saksee`, `saksit` | a **partial real directory** that shadows the shared copy, plus a `sakthai~origin_main -> ../shared/sakthai` symlink alongside it |

Those three partial directories contain only a handful of files —
`agent/guardrails.py` and `web/server.py` for all three, plus
`cli/__init__.py` and `cli/system.py` for SakSee and SakSit. They exist because
security syncs committed files *into* what used to be a symlink path. The
`agent/guardrails.py` **and `web/server.py`** copies are kept byte-identical to
the canonical ones, enforced by `tests/test_persona_guardrails_parity.py` across
all six personas (the list is derived from `config.PERSONA_NAMES`, so a new
persona is guarded automatically). That test also pins the *inventory* of
shadowed files: adding a new shadowing copy fails CI until it is either declared
security-synced or explicitly allowlisted as stale. The SakSee/SakSit `cli/`
files are those **stale snapshots** — they still register a `dashboard` command
the real CLI no longer has. Don't treat them as live code, and don't "fix" them
by deleting the shadowing files without checking the parity test first.

`personas/sakthai/sakthai/` has also genuinely diverged from
`personas/shared/sakthai/`: `config.py`, `auth.py`, `skills.py`,
`agent/loop.py`, `agent/tools.py`, `agent/chat.py`,
`agent/providers/__init__.py`, `cli/agent.py`, `cli/chat.py`,
`telegram/bot.py` all differ, and `agent/security_hardening.py` +
`agent/guardrails_hardened.py` exist only in the SakThai copy. Reconciling the
two is a known, tracked gap — not yet done.

That gap is now **inventoried**, by `tests/test_shared_package_divergence.py`.
The shared copy is what SakJules and SakTan execute, but it sits outside
`[tool.coverage.run] source` (which resolves to the *installed* package), so no
test imports it and its coverage is not low — it is absent. The new test does
not reconcile the two trees; it pins the difference so it cannot grow unnoticed:
every diverged file must be declared in `KNOWN_DIVERGENCES` with a reason, and
every SakThai-only module in `CANONICAL_ONLY`. **If you edit anything under
`personas/shared/sakthai/` or add a module to the canonical package, this test
fails until you either sync the file or declare it.** Entries are also checked
for staleness — syncing a declared-diverged file fails CI until its register
entry is removed, which is what makes the debt shrink rather than calcify.

### Personas

Six agents on disk (`config.PERSONA_NAMES`: sakking, sakthai, saksee, saksit,
sakjules, saktan); **SakThai is lead**. Each persona directory has:

- `SOUL.md` — identity, injected as a system-prompt prefix by `run/chat --persona`.
  Cross-persona consistency is CI-enforced by `tests/test_soul_consistency.py`.
- `skills/` — that persona's own skill overlay, one directory per skill directly
  under `skills/` (no category subdirectories, no duplicate-named skill folders).
  Counts on disk: SakThai 299, SakSee 182, SakJules 180, SakKing 106, SakSit 43,
  SakTan 13. `personas/sakthai/skills/.archive/` is an intentional exception —
  retired skills kept for history, excluded from discovery. A skill directory may
  itself contain a documented "umbrella" sub-skill (see
  `SakThai-environment-automation`'s `cron-watchdog-self-heal`) reached by direct
  file reads rather than the skill index.
- `config/` — `config.yaml` (default model/provider), `mcp.json`,
  `gateway_voice_mode.json`, and for some personas `workspace.yaml`.
- `agent-self-evolution` — symlink to `../shared/agent-self-evolution` for every
  persona except SakThai, whose copy is real and is the one CI builds.

Configured default models (`config/config.yaml`, consumed by
`config.persona_model_defaults()`): SakThai and SakSee `huggingface` /
`gemini-3.1-flash-lite`, SakKing `huggingface` /
`Qwen/Qwen3-Coder-30B-A3B-Instruct`, SakSit `huggingface` / `DeepSeek-V4-Flash`,
SakJules `huggingface` / `gemini-2.5-flash-lite`, SakTan `ollama` / `sakthai`.

**Shared resources:** `personas/shared/` holds `sakthai/` (the shared package
copy), `agent-self-evolution/` (template), `skills/` (3 `Sak-*` skills, identical
across all personas), and `model_roster`.

**Skill naming:** `Sak-` prefix for shared skills, `Sak<Name>-` for per-persona
skills — enforced by `sakthai skills validate --naming`.

### `sakthai-chat-cli/`

A self-contained folded-in copy of the standalone `sakthai-chat-cli` repo
(migrated 2026-08-01, see its `MIGRATION_NOTE.md`). It is deliberately **not**
merged into the canonical package: it has a Textual TUI redesign of `chat` the
canonical package lacks, while the canonical package has the `huggingface`
provider, guardrails hardening, and the dashboard subpackage it lacks. It has its
own `CLAUDE.md` and its own (stale) docs — notably it still describes a
five-persona roster. Don't sync the two trees casually, and don't treat its docs
as authoritative for this repo.

Everything below this point describes the SakThai agent package itself.

---

## Commands

```bash
# Setup (Python >=3.11)
cp .env.example .env      # then fill in ANTHROPIC_API_KEY
uv sync --all-extras      # install all project and optional dependencies

# Test / lint / type-check / security (mirrors .github/workflows/ci.yml)
uv run pytest tests/ -q                      # full unit suite (no network, no GCP)
uv run pytest tests/test_memory_store.py -q  # a single test file
uv run pytest -m "not integration" -q        # exclude network tests (default in CI)
uv run ruff check personas/sakthai/sakthai tests              # lint
uv run ruff format --check personas/sakthai/sakthai tests     # format check (drop --check to apply)
uv run mypy personas/sakthai/sakthai                          # strict type-check
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai   # security scan
make mutation                                # mutmut on core seam modules (slow, local-only, not in CI)
```

`uv sync --all-extras` (not plain `uv sync`) is required: `hypothesis` lives in
the `dev` extra and `tests/test_store_properties.py` fails collection without it,
which aborts the whole run.

Other `make` targets: `compose-personas` (rebuild full skill trees into
`build/personas/`), `export-agent-repos` / `export-agent-repo PERSONA=<name>`
(materialize standalone per-persona repo snapshots), `test`, `lint`.

`.githooks/` holds a `pre-commit` hook that fails if `uv.lock` is out of sync with
`pyproject.toml`, and a `pre-push` hook. Opt in with
`git config core.hooksPath .githooks`.

### CI

Twenty-nine hand-written workflows live in `.github/workflows/`, plus **eight**
gh-aw Markdown sources compiled to `.lock.yml` beside them — 37 `.yml` files in
all, plus `shared/opencode.md`, which is an import rather than a workflow of its
own. Seven of the eight run on `engine: gemini` and one on a vendored OpenCode
engine driving a Gemini model — see
[`docs/gh-aw-engines.md`](docs/gh-aw-engines.md) and the gh-aw note below.

That "seven on Gemini" was **aspirational until 2026-08-19**: four of the locks
(`ci-doctor`, `maintain-agents-md`, `maintain-docs`, `release`) were still
compiled from gh-aw v0.86.2 against **Copilot**, because their `.md` was
switched to `engine: gemini` and never recompiled. Actions executes the
`.lock.yml`, not the `.md`, so all four failed with `400 The requested model is
not supported` while the source claimed otherwise. **Editing a `.md` without
recompiling changes nothing** — the recompile procedure is in
`docs/gh-aw-engines.md`.

Every hand-written workflow that a pull request can trigger declares a top-level
`concurrency:` block, and every job in every hand-written workflow declares
`timeout-minutes`. Both are enforced by `tests/test_workflow_hygiene.py`
(`test_pull_request_workflows_serialise_per_ref`,
`test_every_job_declares_a_timeout`) — though only since 2026-08-19: the rules
were described in that file's docstring and asserted here for months while
**no test implemented either one**, and three workflows were violating them
(`auto-update-prs.yml`, `bandit.yml`, `codeql.yml`). The
convention for `cancel-in-progress` is
`${{ github.event_name == 'pull_request' }}` — cancel a superseded PR run, never
a run on `main`, because a cancelled analysis uploads no SARIF and an alert is
only ever closed by a newer analysis from the same tool. The `.lock.yml` files
are exempt from both rules: they are compiler output and gh-aw sets
`timeout-minutes` on only one of each workflow's generated jobs.

**Python setup is one composite action, and it caches.** Every workflow that
needs Python goes through `./.github/actions/setup-uv-python`, which installs a
SHA-pinned uv, provisions the interpreter, restores uv's dependency cache (keyed
on `**/uv.lock` + `**/pyproject.toml`, partitioned by `cache-suffix`) and runs
`uv sync --locked`. Before it, `ci.yml` and `subprojects.yml` ran
`pipx install uv` — an unpinned install — and no workflow in the repository
cached a single Python wheel. Pass `sync: "false"` for jobs that only need the
binary (`uv export`, `uvx <tool>`). `tests/test_workflow_hygiene.py` holds the
action to the same SHA-pinning rule as the workflows, since extracting it moved
those `uses:` lines out of the directory that check scans.

**Caches are warmed on `main` and evicted at PR close.** Actions scopes caches so
a branch reads only its own ref, its base, and the default branch — an entry
first written by a PR run is invisible to every other branch, which for a
short-lived agent branch means it never hits. `cache-warm.yml` therefore
populates the uv, pnpm and `.next/cache` entries on `main` (on lockfile changes,
weekly Monday, and on demand), and `cache-cleanup.yml` deletes a PR's caches when
it closes so dead entries do not push the warm baseline out of the repository's
10 GB budget by LRU. Neither gates anything.

**`ci.yml` can run on a self-hosted runner, opt-in.** Its `runs-on` is
`${{ vars.CI_RUNNER_LABEL || 'ubuntu-latest' }}` — set that repository variable
to move CI onto your own hardware, delete it to move back, no workflow edit
either way. The fallback is load-bearing and pinned by a test: a job dispatched
to a label with no online runner does not fail, it *queues* for 24 hours and then
expires, so the repository would stop reporting with nothing red to point at.
Setup lives in [`infra/self-hosted-runner/`](infra/self-hosted-runner/README.md);
read its first section before setting the variable, since a self-hosted runner
must not be reachable by a fork's pull request. Only `ci.yml` is wired this way —
the security scanners stay on GitHub-hosted runners on purpose.

The ones that gate a change:

| Workflow | Trigger | What it does |
|---|---|---|
| `ci.yml` | push/PR to `main` | ruff check + format → mypy + bandit → pytest with coverage, on Python **3.11 and 3.12** |
| `pylint.yml` | push/PR to `main` | pylint over `personas/sakthai/sakthai` + `tests` |
| `secret-scan.yml` | push to `main`, all PRs, manual | gitleaks (config `.gitleaks.toml`, which allowlists persona docs) |
| `dependency-audit.yml` | PRs touching `pyproject.toml`/`uv.lock`, weekly Monday, manual | pip-audit over `uv.lock` |
| `dependency-review.yml` | all PRs | GitHub dependency-review on the PR's diff |
| `subprojects.yml` | push/PR touching `apps/agent_workflow_framework/**`, `apps/sak_agent_dashboard/**`, or `services/teams-copilot-mcp/**` | the two out-of-tree pytest suites + the dashboard's lint/typecheck/test/build chain |
| `quality-flywheel-gate.yml` | push/PR touching `apps/sak_agent_dashboard/**` or `personas/**`, manual | runs `apps/sak_agent_dashboard/scripts/run_eval_quality_gate.sh` — the eval-engine/API/component vitest files, then `tsc --noEmit`, then `pnpm build`. Runs on pnpm/Node 22, `working-directory: apps/sak_agent_dashboard` |
| `mutation-self-healing-gate.yml` | push/PR touching `apps/sak_agent_dashboard/**` or `personas/**`, manual | runs `apps/sak_agent_dashboard/scripts/run_mutation_gate.sh` — the five `mutation_*` vitest files, then `tsc --noEmit`, then `pnpm build`. Same runner shape as the flywheel gate |
| `agent-self-evolution.yml` | push/PR touching `personas/sakthai/agent-self-evolution/**`, manual | that subproject's own suite |
| `labeler.yml` | `pull_request_target` | PR labelling |
| `scorecard.yml` | push to `main`, weekly Thursday, `branch_protection_rule` | OpenSSF Scorecard → SARIF to code scanning |
| `codeql.yml` | push/PR to `main`, weekly Sunday | CodeQL **advanced** setup over `actions`, `javascript-typescript`, `python`; scope from `.github/codeql/codeql-config.yml` via `config-file:`. Query suites are per language (set on `matrix.include`, since a config file's `queries:` applies to every language at once): `actions` runs `security-extended` — the workflow-security rules — and the other two stay on the default suite until the ~243 first-party alerts are triaged. See [`.github/codeql/README.md`](.github/codeql/README.md), and `scripts/codeql_local.sh` to run the same scoped analysis locally |
| `sonarcloud.yml` | push/PR to `main`, manual | SonarCloud analysis (skipped on a fork's PR, which has no `SONAR_TOKEN`) |
| `bandit.yml` | push/PR to `main`, weekly Wednesday | bandit with `-c pyproject.toml` over first-party Python → SARIF to code scanning. Publishes, does not gate — `ci.yml` is the gate |
| `eslint.yml` | push/PR touching `apps/sak_agent_dashboard/**`, weekly Sunday | `eslint src` with the app's own flat config → SARIF (`category: eslint-dashboard`). Publishes, does not gate — `subprojects.yml` is the gate |
| `innersource-advisories.yml` | daily 01:00 UTC, manual | reads the open Dependabot alert list and rewrites one standing issue with it. **Needs `DEPENDABOT_ALERTS_TOKEN`** — `GITHUB_TOKEN` cannot read Dependabot alerts, and `security-events: read` does not grant it (the Actions app lacks the permission entirely). Gates nothing |
| `self-healing-ci.yml` | `workflow_run` completion of `CI` on `main` (failure only), or manual | runs `sakthai heal run` over the failed job's log and opens a `selfheal/` fix PR when the patch is safe and locally verified. Gates nothing — it only ever adds a PR |
| `auto-merge.yml` | `pull_request_target` labeled/unlabeled/ready_for_review | turns GitHub's **native** auto-merge on for a PR carrying the `automerge` label (squash), off when the label is removed. Gates nothing and waives nothing — GitHub still holds the merge until branch protection is satisfied, including the non-author approval. Uses no checkout, so the `pull_request_target` token never meets PR code |
| `ossar.yml` | push/PR to `main`, weekly Monday | open-source static analysis on `windows-latest` → SARIF. Retired 2026-08-18, re-added 2026-08-19 as the stock starter template and repaired the same day — **read the callout below before editing it** |
| `auto-update-prs.yml` | push to `main` | walks every open PR targeting `main` and calls the update-branch API on each, so a merge does not leave the queue stale. Holds `contents: write` + `pull-requests: write` and pushes to *contributor* branches, which is why its `concurrency:` group uses `cancel-in-progress: false` — a run cancelled mid-loop leaves some branches rebased onto the new `main` and the rest on the old one. Gates nothing; a PR it cannot update (conflicts) is logged and skipped |

**`ossar.yml` was re-added on 2026-08-19 and needed two separate repairs.**
It was retired on 2026-08-18 for the reasons in the removal note below, then
re-added by commit `52be3a6` as GitHub's stock OSSAR starter template,
unmodified, which turned `main` red. Both defects are fixed now, but the shape
of them is worth keeping:

1. **It could not check this repository out.** The stock template runs
   `runs-on: windows-latest` (`github/ossar-action` supports no other runner),
   and the repo contained eight skill directories with `::` in their names —
   `SakJules-stitch::code-to-design` and seven `SakSee-stitch::*`. `::` is not a
   legal NTFS path character, so `actions/checkout` exited 128 with
   `invalid path '.../SakJules-stitch::code-to-design/SKILL.md'` before OSSAR
   started. **Those directories are now `stitch-*` rather than `stitch::*`.**
   Note the retired version of this workflow ran MSDO on `ubuntu-latest` and so
   never hit this; the constraint arrived with the Windows-only action.
2. **It violated three invariants `tests/test_workflow_hygiene.py` enforces**,
   so it failed `ci.yml` as well as its own job: unpinned action tags, no
   top-level `concurrency:`, and no `timeout-minutes`. All three are pinned and
   declared now.

3. **It still could not check out after the rename**, for an unrelated Windows
   reason: three vendored paths under
   `apps/sak_agent_dashboard/microsoft_agents_m365copilot/` are 274-278
   characters, past Windows' 260-character `MAX_PATH`. Git wrote all 6,250
   files and then exited 1 with no message naming a file. The workflow now runs
   `git config --global core.longpaths true` before `actions/checkout`.

The trap here is that (2) is mechanical while (1) and (3) are not. Pinning the
SHAs alone would have turned `ci.yml` green while leaving a workflow that still
could not check the repository out — a quieter failure, not a fixed one, and
each layer only became visible once the one above it was cleared.

**Two standing constraints follow from this, and they bind any future
Windows-runner workflow, not just OSSAR:** a `::` in a path makes checkout fail
immediately with `invalid path`, and a path over 260 characters makes it fail
at the end with a bare exit 1. Both are properties of this repository's tree —
the `stitch-*` skill names and the vendored M365 SDK — rather than of the
workflow that trips over them.

Note that the two `*-gate.yml` dashboard workflows are triggered by `personas/**`
as well as `apps/sak_agent_dashboard/**`, but both run entirely inside
`apps/sak_agent_dashboard` — a persona-only change fires them and they still only
exercise the dashboard.

Scheduled, manual, or event-driven only, so they never block a PR:
`verify-assets.yml` (daily HF asset check), `run-evals.yml` (weekly Sunday
lm-eval, installs the `evals` dependency group), `summary.yml` (on new issues),
`OSPS.yml` (weekly Monday security-baseline assessment),
`code-scanning-cleanup.yml` (manual, retires orphaned code-scanning alerts),
`cache-warm.yml` (weekly Monday and on lockfile changes to `main`, primes the
dependency caches), `cache-cleanup.yml` (on a pull request closing, evicts that
PR's caches), and `self-hosted-runner-health.yml` (daily, skipped entirely unless
`CI_RUNNER_LABEL` is set; probes the runner and its toolchain).

`opencode.yml` is also in that group but is worth its own paragraph, because it is
the one workflow a *comment* can start. A `/oc` or `/opencode` comment on an issue
or PR-review thread runs an OpenCode agent on the **OpenCode Go** subscription
(`opencode-go/deepseek-v4-flash`, one `OPENCODE_API_KEY` secret). Properties that
hold it in place, none to be relaxed casually:

- **It comments back, and `contents: read` is the real ceiling.** It is *not*
  read-only, despite what this file said until 2026-08-19: the action posts a
  reaction on the triggering comment and then a reply, so it needs
  `issues: write` (issue threads and PR conversation comments) and
  `pull-requests: write` (the `pull_request_review_comment` trigger, a different
  endpoint). With read-only scopes both calls returned
  `403 Resource not accessible by integration` and the step exited 1 having done
  nothing. What it still cannot do is push, branch, or open a pull request.
  Those scopes bind at all only because of `use_github_token: true`: the
  action's default is to exchange an OIDC token for an *OpenCode GitHub App*
  installation token whose permissions come from the app install and ignore this
  workflow's `permissions:` block entirely.
- **It has tools, and shell.** The job runs `./.github/actions/setup-uv-python`
  so `opencode.json`'s `mcp.sakthai` entry can actually start — without it the
  MCP server failed silently and the agent lost all 14 builtin tools. Shell
  comes from `.github/opencode-ci.json`, pointed at by `OPENCODE_CONFIG`: the
  root `opencode.json` sets `permission.bash: "ask"`, which cannot be answered
  headlessly, and is pinned by `tests/test_agent_cli_configs.py`, so CI
  overrides it rather than loosening it. That config also sets `edit: deny` —
  with `contents: read` an edit could never be pushed. Note this widens the
  blast radius of a prompt injection reaching the agent through a comment or
  diff: the trusted-commenter gate below is what contains it.
- **Only trusted commenters, and no session link.** It fires only for an
  `OWNER`/`MEMBER`/`COLLABORATOR` commenter, and passes `share: false` because
  the action defaults `share` to **true for public repositories** — which this
  one is — publishing a session link with the agent's reasoning trace on every
  run. Its `concurrency:` group is per issue/PR thread with
  `cancel-in-progress: false`, which serialises rather than cancels and so also
  caps how fast it can spend a budget shared with interactive use.

Setup and rationale in
[`docs/multi-agent-cli-setup.md`](docs/multi-agent-cli-setup.md). Note this is a
**separate** OpenCode integration from the vendored gh-aw engine below: they share
a name and nothing else.

The eight agentic gh-aw workflows also never block a PR, but **they do not all
merely report** — check the `safe-outputs:` block before assuming one is
read-only:

| Source | Trigger | Output |
|---|---|---|
| `security-audit.md` | weekly Thursday | triages bandit + pip-audit + the guardrail suite; issue only |
| `shared-package-drift.md` | weekly Tuesday | audits the `personas/shared/sakthai/` divergence register; one issue, `close-older-issues` |
| `skills-hygiene.md` | weekly Wednesday | runs `sakthai skills validate --naming`; issue only |
| `opencode-smoke.md` | weekly Monday | proves the vendored OpenCode engine still runs; one issue, `close-older-issues` |
| `ci-doctor.md` | `workflow_run` completion of **`CI`, `Pylint`, `Subproject tests`** on `main`, failure only | root-causes the failure; opens a `[ci-doctor] ` issue and may `add-comment` |
| `maintain-docs.md` | daily on weekdays | **opens a draft PR** (`[docs] `, max 1) for docs out of sync with recent commits |
| `maintain-agents-md.md` | weekly Monday | **opens a draft PR** (`[agents-md] `, max 1) keeping `AGENTS.md` current with merged PRs |
| `release.md` | `workflow_dispatch` only, `roles: [admin, maintainer]` | builds/tests/publishes a release for a `patch`/`minor`/`major` input; `safe-outputs: update-release` |

So four report by issue only, `ci-doctor.md` reports by issue and comment, two
open draft pull requests, and `release.md` writes a GitHub release. The
`ci-doctor.md` `workflows:` list matches on `name:` values exactly — verify a new
entry against `grep -h '^name:' .github/workflows/*.yml` before adding it, as the
file's own comment records an entry that matched nothing for as long as it was
there.

**Five workflows were removed on 2026-08-18** after their run history was read
rather than their files: `auto-dependency-update.yml` (22 runs, 22 failures — it
died at *Create Pull Request* with `Input 'token' not supplied`, because no
`GH_PAT_FOR_ACTIONS` secret exists here, and Dependabot already covers pip / npm /
Docker / Actions), `continuous-security.yml` (nightly, but every run skipped its
agent step because there is no `ANTHROPIC_API_KEY` — `security-audit.md` replaces
it on the Gemini engine the rest of the agentic workflows already use),
`ossar.yml` (MSDO with `tools: eslint` at a repository root that has no
`package.json`, duplicating what `eslint.yml` does properly — **note it was
re-added on 2026-08-19 as the stock OSSAR template and repaired rather than
re-retired; see the callout above**), `stale.yml` (still
carrying the starter template's literal `'Stale issue message'` placeholder), and
`manual.yml` (a greeting echo). Before adding a workflow back, check the Actions
tab for what it actually did.

CodeQL used to run via GitHub's *default setup*, and the rule was "never add
`codeql.yml`" — an advanced analysis cannot upload while default setup is
enabled, so remediation bots that added the file twice failed every job with
`CodeQL analyses from advanced configurations cannot be processed when the
default setup is enabled`. **That is no longer the state of the repository.**
Default setup is off and `codeql.yml` is the live producer: its three `Analyze`
jobs upload successfully, which is only possible with default setup disabled.
Do not delete it, and do not re-enable default setup without deleting it — the
two cannot coexist. The payoff is `config-file:`, which default setup could not
be given by path: `.github/codeql/codeql-config.yml` was inert for exactly that
reason and now applies, excluding the vendored trees that produced 545 of the
788 open CodeQL alerts. See `docs/code-scanning-sweep-2026-08-18.md`.

**No smoke-test job is wired into any workflow**, despite
`.claude/skills/run-sakthai-agent-v2/driver.py` existing — treat that as
available tooling, not an enforced gate.

Workflow files are expected to be real, loadable workflows: a `.yml`/`.yaml`
extension (GitHub silently ignores anything else, including a name like
`foo. yml` with a space), a top-level `on:` and `jobs:`, no duplicate keys, and
a top-level `permissions:` block. A batch of pasted starter templates that met
none of this was removed on 2026-08-13, and three more (`bandit.yml`,
`codeql.yml`, `eslint.yml`) arrived on 2026-08-18.

**`tests/test_workflow_hygiene.py` now enforces all of it in CI**, plus SHA
pinning on every `uses:`, the `self-healing-ci.yml` fork guard, `codeql.yml`'s
`config-file:` reference, and `.bandit` being parseable configuration. It exists
because a bot commit reverted a merged critical security fix — 446 deletions
under a message about something else — and nothing failed. If you are adding a
workflow, run it: `uv run pytest tests/test_workflow_hygiene.py -q`.

Coverage floor is **96%** (`fail_under = 96`, branch coverage on) over the
`sakthai` package. Nothing is omitted from measurement any more — `omit = []`;
`telegram/bot.py` used to be excluded, which did not make it tested, only
invisible (it sat at 38% while the reported total stayed above the floor). It is
measured now and covered at 98%. The suite currently sits at **97.92%**. Run the
lint→pytest sequence locally before
pushing; green CI is the bar for `main`.

---

## Runtime entry points

One package, four ways in — all sharing `~/.sakthai/memory.db` by default
(override the root with `SAKTHAI_HOME`). On the VM deployment, each persona's
process sets its own `SAKTHAI_HOME=$HOME/.sakthai/$AGENT`, so each persona
naturally gets its own memory shard at `~/.sakthai/<persona>/memory.db`. For
local dev, pass `--persona <name>` to `learn`/`recall`/`run`/`chat`/`memory` to
get the same per-persona shard without setting `SAKTHAI_HOME` yourself — see
"Per-persona memory sharding" below.

1. **CLI** — `sakthai <cmd>` (entry point `sakthai.cli:main`, wired in
   `cli/__init__.py`). Commands:
   - Memory: `learn`, `recall`, and the `memory` group —
     `show|stats|search|forget|forget-obs|backup|healthcheck|export|import|consolidate|consolidate-sessions|deduplicate|family|sync|pull`.
     `--persona <name>` is a **group-level** option on `memory` (and a plain
     option on `learn`/`recall`); `sync` and `pull` explicitly reject it (git/HTTP
     sync always targets the unscoped `memory.db`), and `family` merges across
     every persona's shard (or a `--personas a,b,c` subset) into one read-only view.
   - Agent: `run "<task>"` — `--provider`/`-p`
     (anthropic/google/openai/ollama/gateway/huggingface), `--model`,
     `--max-tokens`, `--max-iterations`, `--max-seconds`, `--with-skills <name>`
     (repeatable), `--no-mcp`, `--dry-run` (validate config, no API call),
     `--stream`, `--fast` (skip the 6-stage cycle), `--stateless` (don't
     load/append memory), `--caveman lite|full|ultra|wenyan-*` (token-compression
     skill), `--sandbox` (run inside the `Dockerfile.sandbox` container; only
     `memory.db` is bind-mounted; not combinable with `--persona`),
     `--persona <name>`, `-v/--verbose`.
   - Chat: `chat` — interactive multi-turn REPL over the same loop and memory.
   - Server: `mcp` (start the MCP stdio server).
   - Web: `web setup` (print/create the API bearer token), `web regen-token`.
   - Cycle: `cycle status|next|set|list`
   - Skills: `skills list|show|validate|create|sync-sakking`
   - Extensions: `extensions install|list|remove`
   - Sessions: `sessions list|show|clean`
   - Eval: `eval summary [--limit N] [--json]`
   - Heal: `heal inspect|run` — the self-healing CI agent. `inspect` parses a
     failed job's log and prints the failures (no model call, no writes); `run`
     walks the full diagnose → gate → patch → verify → publish pipeline. Its
     exit code reports whether the *pipeline* ran, not whether a fix was found —
     read the status from `--json`. See "Self-healing CI" below.
   - Hugging Face: `hf info|download <repo_id>`
   - System: `doctor`, `setup`, `status`, `tools`
   - There is **no `dashboard` command** — the CLI wiring was removed (a stale
     copy still registering it survives under `personas/saksee|saksit/sakthai/cli/`),
     but `dashboard/data.py` was later re-added as the KPI module behind the web
     API. See the dashboard note under "Other subsystems".

2. **Agent loop** — `sakthai run` drives a provider-agnostic tool-using loop
   (Claude, Gemini, or any OpenAI-compatible/Ollama/gateway/HF endpoint).

3. **Chat REPL** — `sakthai chat` drives the same loop turn by turn.

4. **MCP server** — `sakthai mcp` serves the same tools over JSON-RPC stdio.

`sakthai run` can also reach *out* to external MCP servers: tools discovered from
them are merged into the registry (namespaced `<server>__<tool>`) for that run.

A task starting with `/plugin:command` is treated as a **slash command**:
`_parse_slash_command()` in `agent/loop.py` resolves
`<root>/<plugin>/commands/<command>.md` across the skill roots, strips its
frontmatter, substitutes `$ARGUMENTS`/`$FEATURE`, and injects the body as a
system-prompt block.

---

## Architecture (the big picture)

A small, strictly layered package — each layer has one job. Data flows
CLI/MCP → agent loop → guardrails → tool registry → MemoryStore → SQLite. See
[`docs/architecture.md`](docs/architecture.md) for the full diagram.

### Core modules

- **`config.py`** — single source of truth for paths and env-var names
  (`sakthai_home`, `memory_db_path`, `persona_memory_db_path`, `sessions_dir`,
  `eval_log_path`, `persona_skills_dir`, `persona_mcp_config_path`,
  `persona_model_defaults`, `check_env`). Also owns secret handling:
  `SECRET_PATTERN`, `register_secret()`, `redact_secrets()` — used by the loop,
  the eval log, and the guardrails' output filter. Nothing else hard-codes a
  path; new paths and env-var names go here.
- **`auth.py`** — credential resolution. Always call `resolve_anthropic_client()`
  rather than constructing a client. Anthropic chain: `ANTHROPIC_API_KEY` →
  `ANTHROPIC_AUTH_TOKEN` → Claude CLI OAuth token. Google uses the Gemini CLI
  OAuth token. OpenAI/Ollama uses `resolve_openai_credentials` to locate the base
  URL and API key. Raises `AuthError` when no credentials are found.
- **`sandbox.py`** — backs `sakthai run --sandbox`. Builds/reuses a Docker image
  from `Dockerfile.sandbox` (layer-cached) and re-executes the task inside it;
  only `memory.db` is bind-mounted from the host. Egress is on by default (the
  model provider needs it) — set `SAKTHAI_SANDBOX_NETWORK` (e.g. `none`) to
  restrict it. Raises `SandboxError` if Docker isn't on `PATH`.
- **`giturl.py`** — `validate_git_url()`. Every user-supplied URL handed to a git
  subprocess (memory sync remotes, extension clone URLs) goes through it: it
  rejects `-`-leading values (option smuggling), remote-helper transports
  (`ext::…` runs arbitrary commands), and schemes outside http(s)/ssh/git/file.
- **`hf.py`** — Hugging Face Hub info/download; `huggingface_hub` is imported
  lazily so the package and test suite work without it installed.
- **`sakking_skills.py`** — idempotent import of SakKing's *learned* skills from
  `~/.sakking` into this repo as `SakKing-` prefixed skills (`skills sync-sakking`).

### Memory subsystem (`memory/`)

- **`memory/store.py`** — `MemoryStore` is the **only** code that touches SQLite.
  It holds *facts* (`Fact` dataclass: `id`, kind, key, value, source_session,
  created_at, updated_at, tags) and *observations* (`Observation` dataclass: `id`,
  summary, evidence_session_id, weight, confidence, created_at). Features:
  WAL concurrency, additive migrations in `_migrate_schema()` (ALTER TABLE only,
  under `BEGIN IMMEDIATE`), snapshot export/import (JSONL/CSV), deduplicate, and
  consolidate. `render_prompt_block()` injects memory into the system prompt.
- **`memory/provider.py`** — `SakThaiMemoryProvider` adapts the store to
  system-prompt blocks with context-window limiting.
- **`memory/backup.py`** — timestamped copy of `memory.db`, or of an explicit
  `db_path` (used to back up a persona's own shard).
- **`memory/sync.py`** — git-based JSONL export/import (multi-agent sync) and
  HTTP backup to a configured endpoint.
- **`memory/merged.py`** — `FamilyMemoryView`, a read-only view across every
  persona's memory shard plus the legacy unscoped `memory.db`, deduplicated and
  grouped by persona. Backs `sakthai memory family`.
- **`memory/cache.py`** — in-process caching and provider isolation. `MemoryLRUCache`
  (TTL+capacity LRU: `get`/`set`/`delete`/`stats`) and `DistributedMemoryCache`
  (client-backed, for the planned distributed memory mesh) serve read-side caching;
  `CircuitBreaker` (`failure_threshold` + recovery window; `allow_request`/
  `record_success`/`record_failure`) is the breaker the `healing/` supervisor
  attaches per persona to isolate a degraded provider.

### Per-persona memory sharding

Each of the six personas gets its own memory shard, `~/.sakthai/<persona>/memory.db`,
distinct from the legacy unscoped `~/.sakthai/memory.db`. This isn't a new
mechanism: it's the same convention already used in production by
`infra/vm-agents/sakthai-agent-run.sh`, which runs each deployed persona with
`SAKTHAI_HOME=$HOME/.sakthai/$AGENT` — `memory_db_path()` (which does honor
`SAKTHAI_HOME`) already resolved to that persona's shard for any process running
that way. What's new is `config.persona_memory_db_path(persona)`, which computes
the same `~/.sakthai/<persona>/memory.db` path directly from `Path.home()`,
**independent of the current process's own `SAKTHAI_HOME`**. That's what makes
two things possible that weren't before:

- **Local CLI parity** — `learn`/`recall`/`run`/`chat`/`memory <subcommand>` all
  accept `--persona <name>` so a local dev shell (which isn't running with a
  persona-scoped `SAKTHAI_HOME`) can still read/write a specific persona's shard.
  `run`/`chat --persona` additionally inject that persona's `SOUL.md` as a
  system-prompt prefix, resolve `--with-skills`/caveman/slash-commands against
  that persona's own skill overlay instead of SakThai's, auto-load its own
  `config/mcp.json` when `SAKTHAI_MCP_CONFIG` isn't already set, and default
  `--model`/`--provider` from its own `config/config.yaml` when those flags are
  left at their CLI defaults. `memory sync`/`memory pull` reject `--persona`
  (they always target the unscoped `memory.db` — no per-persona git/HTTP sync
  exists). `run --persona` can't combine with `--sandbox` (the sandbox only
  bind-mounts the unscoped `memory.db`).
- **The merged family view** — `FamilyMemoryView` (`memory/merged.py`) opens
  every persona's shard (skipping ones that don't exist yet) plus the legacy
  `memory.db` at once, regardless of which single persona the current process
  would otherwise be scoped to, and merges/dedups facts and observations across
  them. `sakthai memory family [--personas a,b,c] [--limit N] [--json]` is the
  CLI surface for it.

A persona's shard file only comes into existence on first write (`learn
--persona X`, or any `run`/`chat --persona X` that calls a memory-writing
tool) — an unwritten-to persona is simply absent from `memory family` output,
not an error.

### Agent subsystem (`agent/`)

- **`agent/tools.py`** — defines `BUILTIN_TOOLS` (14 tools, one schema + handler
  each): `learn`, `ingest_document`, `capture_lead`, `recall`, `search`, `forget`,
  `read_file`, `run_command`, `send_telegram_message`, `send_outlook_mail`,
  `read_outlook_mail`, `list_calendar_events`, `create_calendar_event`,
  `run_agent_loop`. Add a tool here and it appears in both the agent loop and
  the MCP server automatically. Note: `run_agent_loop` is filtered out of the
  in-loop tool set (it's MCP-only) and additionally guards on the
  `SAKTHAI_AGENT_ACTIVE` env var to block indirect recursion. The four Graph
  tools share `_graph_access_token()` / `_graph_request()` / `_graph_safe()`
  helpers: a refresh token (env `MS_GRAPH_REFRESH_TOKEN` or cached at
  `~/.sakthai/graph_token.json`, seeded via `scripts/graph_device_login.py`) is
  exchanged for a short-lived access token on every call.
- **`agent/registry.py`** — `ToolRegistry` keys tools by name; `with_tools()`
  merges sets (later tool wins on name clash, so plugins can shadow built-ins).
- **`agent/loop.py`** — `run_agent()` is the main orchestration loop. Injects
  `store.render_prompt_block()` into the system prompt, resolves slash commands,
  applies the context filter, dispatches every tool call through the guardrail
  policy, appends an `EvalRecord` per run, and writes session logs to
  `~/.sakthai/sessions/`. Returns `AgentResult` (iterations, stop_reason,
  tool_calls, usage). `client`, `store`, `guardrail_policy`, and `context_filter`
  are all injectable for testing. Defaults live here: `DEFAULT_MODEL =
  "claude-opus-4-8"`, `DEFAULT_MAX_TOKENS = 16000`, `DEFAULT_MAX_ITERATIONS = 12`.
- **`agent/chat.py`** — the interactive REPL behind `sakthai chat`. Keeps
  `rich`/`prompt_toolkit` I/O at the module edges (renderers take an injected
  `Console`, the loop takes an injected `read_input`) so conversation flow is
  testable without a terminal.
- **`agent/eval.py`** — local model-eval / MLOps logging. Every `run_agent` call
  appends one `EvalRecord` (model, provider, latency, usage, outcome) to
  `eval_log_path()` (default `~/.sakthai/eval.jsonl`); `summarize_evals()` backs
  `sakthai eval summary`. No cloud dependency.
- **`agent/usage.py`** — `UsageTracker` / `extract_usage()` for token counting.
- **`agent/context_filter.py`** — the `ContextFilter` protocol plus
  `TurnSummarizationFilter` and `DEFAULT_CONTEXT_FILTER`, wired into
  `run_agent`. The filter compacts every turn but the last two, and it takes an
  optional `summarizer` callable — the injected seam for a smaller, faster
  model. `DEFAULT_CONTEXT_FILTER` passes none, so the default behaviour is
  still deterministic truncation; a summarizer that raises, returns a
  non-string, or fails to shorten the text falls back to that truncation.
  Compaction covers plain string content, `text` blocks, and `tool_result`
  blocks — the last of those is where a tool-using run's tokens actually
  accumulate, since `read_file`/`run_command` output only ever reaches history
  as a block. Provider `Block` objects on an assistant turn are passed through
  untouched (rewriting them would mutate objects the caller still holds), and
  the filter never mutates its input.
- **`agent/prompt_builder.py`** / **`agent/context_manager.py`** — an extracted
  prompt-assembly seam (`build_system_prompt`, `render_skills_prompt_block`,
  `ContextManager`). Both are tested (`tests/test_prompt_builder.py`,
  `tests/test_context_manager.py`), but note that `agent/loop.py` still imports
  `render_skills_prompt_block` straight from `skills.py` — the loop has not been
  migrated onto `ContextManager` yet.
- **`agent/providers/`** — provider abstraction:
  - `base.py` — shared types (`Block`, `Response`), retry logic via `tenacity`
  - `anthropic_provider.py` — Claude via the `anthropic` SDK
  - `gemini_provider.py` — Gemini via `google-genai`
  - `openai_provider.py` — OpenAI-compatible APIs, Ollama, the `gateway`
    provider (OpenRouter/LiteLLM/Vercel/Cloudflare AI gateways), and the
    `huggingface` provider (HF Inference Providers router, via `HF_TOKEN`) — all via `httpx`
  - `__init__.py` — provider detection and client factory

### Healing subsystem (`healing/`)

Runtime resilience and recovery — **not** the same as `selfheal/`. `selfheal/`
is the CI agent that reads a *failed GitHub Actions job's log* and opens a fix
PR; `healing/` intercepts *live* agent-loop exceptions, rolls back memory, and
isolates providers. Different triggers, different surfaces — don't conflate them.

- **`healing/supervisor.py`** — `SelfHealingSupervisor` is the orchestration point.
  `classify_error()` maps an exception to `ErrorSeverity` (`TRANSIENT` /
  `STATE_CORRUPT` / `FATAL`); `handle_execution_failure()` runs the recovery flow
  (classify → snapshot rollback for state-corrupting failures → DLQ enqueue →
  circuit-breaker update); `get_circuit_breaker(persona)` returns a per-persona
  `CircuitBreaker` (from `memory/cache.py`) so one degraded provider is isolated
  without grounding the others; `replay_dlq_item(item_id, executor_fn)` re-runs a
  buffered payload; `get_health_status(persona)` reports breaker state and DLQ
  depth. `RecoveryResult` is the return shape. `ErrorSeverity` and `RecoveryResult`
  live here on `main` (the feature branch relocates them into `healing/models.py`).
- **`healing/dlq.py`** — `DeadLetterQueue` / `DeadLetterItem`: a persistent
  SQLite-backed buffer (`_recovery_db_path()`) for failed task payloads —
  `enqueue` / `list_pending` / `get_item` / `record_retry_failure` /
  `mark_replayed` / `mark_purged` / `stats`.
- **`healing/snapshot.py`** — `MemorySnapshotManager`: point-in-time checkpoint +
  atomic rollback of a `MemoryStore` (`create_checkpoint(store, label)` →
  checkpoint id; `rollback(store, checkpoint_id)` → bool; `release_checkpoint`;
  `active_checkpoints_count`). It takes the `MemoryStore`, not a raw db path —
  consistent with the memory-store-is-the-seam rule.

The package is mirrored under `personas/shared/sakthai/healing/` and follows the
same parity rule as `guardrails.py`: keep the two copies in sync or
`tests/test_shared_package_divergence.py` fails CI.

### Security subsystem (`agent/guardrails*.py`, `agent/security_hardening.py`)

This is the largest single body of code in the package and the most actively
attacked surface — several rounds of Sentinel audits landed here.

- **`agent/guardrails.py`** (~1,400 lines) — `GuardrailPolicy` with pre- and
  post-execution checks around every tool call; `DEFAULT_POLICY` is what
  `run_agent` uses. Enforces: `run_command` blocked unless `SAKTHAI_SHELL_ALLOW`
  is set, dangerous/destructive shell commands, sensitive-path arguments
  (`_is_sensitive_path` over `_SENSITIVE_BASENAMES` / `_SENSITIVE_DIRS` /
  `_SENSITIVE_KEY_STEMS` / `_CRITICAL_ROOTS`, matched case-insensitively, across
  separators, for relative as well as absolute paths, including `make` recipe
  and `-C`/`-f` resolution), and secret-bearing tool output. A `GuardrailResult`
  carries a `GuardrailAction` (`ALLOW`/`DENY`) plus possibly-rewritten args.
- **`agent/security_hardening.py`** — defense-in-depth primitives: environment
  pinning/verification, MCP server validation and allowlisting,
  `EnhancedPathValidator`, `SymlinkDetector`, `ConfigFileIntegrity`, TOCTOU
  prevention, `ShellCommandHardener`, and an audit logger.
- **`agent/guardrails_hardened.py`** — wires those primitives on top of the base
  policy.

**When you change guardrails, you must sync the file.** `guardrails.py` is
copied per persona and `tests/test_persona_guardrails_parity.py` fails CI the
moment any copy drifts from `personas/sakthai/sakthai/agent/guardrails.py`
(it checks sakthai, sakjules, sakking, saksee, saksit). Roughly 15 test files
(`test_guardrails_*.py`, `test_sentinel_*.py`, `test_security_*.py`) cover this
area; add a regression test for every new bypass you close.

### MCP subsystem (`mcp/`)

- **`mcp/server.py`** — **inbound** JSON-RPC 2.0 stdio server. `handle_request`
  is a **pure function**, testable without a process. Reuses `BUILTIN_TOOLS` so
  behavior matches the agent loop exactly. Advertises protocol version
  `"2024-11-05"`.
- **`mcp/client.py`** — **outbound** stdio client. Launches external MCP servers,
  wraps their tools as local `Tool` objects, auto-namespaces as `<server>__<tool>`.
  Dependency-free; uses `select`-based timeouts (no asyncio).
- **`mcp/manager.py`** — `connect_servers()` context manager starts all configured
  servers, fails soft on errors, merges tools, cleans up on exit.
- **`mcp/servers.py`** — `MCPServerSpec` dataclass + `load_server_specs()`:
  discovers external server specs from `~/.sakthai/mcp.json` (or
  `SAKTHAI_MCP_CONFIG`, or the persona's own `config/mcp.json`) and extensions.

External MCP server config format:

```json
{
  "servers": [
    { "name": "my-server", "command": "npx", "args": ["-y", "my-mcp-pkg"] }
  ]
}
```

### CLI subsystem (`cli/`)

Click commands split by area; all sub-files imported by `cli/__init__.py`, which
binds groups under `*_cmd` aliases on purpose so `sakthai.cli.<name>` keeps
resolving to the *module* rather than the command object:

- `agent.py` — `run`, `mcp`
- `chat.py` — `chat`
- `memory.py` — `learn`, `recall`, `memory` group
- `system.py` — `doctor`, `setup`, `status`, `tools`, `web` group
- `skills.py` — `skills` group
- `cycle.py` — `cycle` group
- `extensions.py` — `extensions` group
- `eval.py` — `eval` group
- `heal.py` — `heal` group
- `sessions.py` — `sessions` group
- `hf.py` — `hf` group

There is no `dashboard.py` here — see the dashboard note below.

### Other subsystems

- **`cycle/`** — six-stage Dream → Hope → Care → Joy → Trust → Growth state
  machine. `stages.py` defines the `Stage` StrEnum plus a `StageInfo` table
  (goal, commands, guidance per stage); `state.py` persists the current stage as
  a single fact in the store (kind=`cycle`, key=`current_stage`).
- **`skills.py` + `library/` + `personas/*/skills/`** — parse/catalog/validate
  `SKILL.md` files. `default_skill_roots(persona=None)` returns, in order:
  the persona's own overlay (`persona_skills_dir(persona)`, else `SKILLS_DIR` =
  `personas/sakthai/skills/`), `personas/shared/skills/`
  (`SHARED_SKILLS_DIR`/`LIBRARY_DIR`, 3 skills identical across personas), root
  `library/` (`CURATED_LIBRARY_DIR`, 31 curated skills across 11 categories,
  pre-dating the `Sak-`/`SakThai-` convention), `~/.sakthai/extensions`, and the
  Gemini extensions dir if it exists. The **root-level `skills/` directory is not
  a root** — it's orphaned content. Skills reach the system prompt via
  `render_skills_prompt_block()`.
- **Dashboard — backend only.** The CLI's `dashboard` command and the frontend
  (both the old in-package bundle and the repo-root Vite project) are gone, but
  `personas/sakthai/sakthai/dashboard/data.py` was re-added: it collects
  KPI/lead/revenue metrics from the memory store and is served by
  `web/server.py`'s `/api/stages` endpoint (covered by
  `tests/test_dashboard_data.py`). `_STATIC_ROOT` resolves to
  `personas/sakthai/sakthai/dashboard/dist/`, which does not exist, so the web
  server runs API-only and static requests fall through to 404.
- **`web/server.py`** — HTTP API server exposing `/health`, `/api/stages`, and
  `/api/ecosystem`. Refuses non-loopback binds unless `SAKTHAI_WEB_ALLOW_PUBLIC`
  is set. **Every path except `/health` now requires the bearer token** —
  `/api/*` answers 401/403 as JSON, and static paths get a plaintext 401, closing
  the gap described in
  `docs/superpowers/specs/2026-08-03-sakthai-web-auth-design.md`. The token comes
  from `_get_or_create_bearer_token()` (stored as a `web_auth` fact in
  `memory.db`, managed with `sakthai web setup` / `web regen-token`). Static
  serving additionally canonicalises the request path against `_STATIC_ROOT`
  before delegating.
- **`selfheal/`** — the self-healing CI agent behind `sakthai heal` and
  `.github/workflows/self-healing-ci.yml`. `pipeline.heal()` is the whole flow in
  one injectable function: `ingest.py` parses a failed job's log into
  `FailureSignal`s (pytest/ruff/mypy/bandit), `inspector.py` resolves the
  implicated files against the checkout and reads bounded, containment-checked
  windows, `diagnose.py` asks a model for **JSON only** (root cause, confidence,
  exact-string edits — never commands), `safety.py` gates those edits
  deterministically, `patch.py` applies them all-or-nothing with a byte-exact
  rollback, `verify.py` re-runs the failing test then the whole suite,
  `publish.py` pushes a `selfheal/` branch and opens the PR, and
  `walkthrough.py` renders the report. **The safety gate has the final word: a
  violation is a hard stop that no confidence score overrides**, and its
  protected-path list includes `.github/`, dependency pins, the security
  subsystem, and the `selfheal` package itself — the agent cannot edit its own
  gate, its own workflow, or its own tests. Rationale and the full status table
  are in [`docs/self-healing-ci.md`](docs/self-healing-ci.md). Note this module
  exists only in the SakThai copy of the package, not in
  `personas/shared/sakthai/` — the same known divergence described above.
- **`extensions/install.py`** — clones skill/MCP bundles from git into
  `~/.sakthai/extensions` (URLs validated via `giturl.py`, removal containment-
  checked); `list`/`remove` manage installed bundles.
- **`learn/capture.py`** — `learn()` one-shot fact capture used by `sakthai learn`.
  **`learn/ingest.py`** — `ingest_document`, splitting Markdown/text/CSV into facts.
  **`lead/capture.py`** — `capture_lead()`, storing a structured lead fact.
- **`telegram/`** — a standalone `python-telegram-bot` polling bot (`bot.py`,
  `config.py`, `workflow_executor.py`). `bot.py`'s `/workflow <name>` handler
  runs `run_agent()` **in-process** via `asyncio.to_thread` — it does not shell
  out. `workflow_executor.py`'s `run_workflow()`/`_workflow_command()` (which
  *do* shell out to `python -m sakthai run ... --with-skills <name> --fast
  --stateless`) are unit-tested but currently unused by `bot.py` (only
  `get_available_workflows()` is called from there). `telegram/config.py`
  re-exports `ALLOWED_USER_IDS`/`TELEGRAM_BOT_TOKEN` from the central
  `config.py`. `workflow_executor.py`'s skill discovery is persona-aware: it uses
  `config.persona_skills_dir(config.sakthai_persona())` when `SAKTHAI_PERSONA` is
  set (see `infra/vm-agents/env-templates/*.env.example`), falling back to
  `config.SKILLS_DIR`. This subpackage is the one part of the package held to a
  lower bar: mypy skips it and coverage omits `bot.py`.

---

## Tests

Tests live in `tests/` (134 test files, ~32,358 lines) and are the suite for the
`sakthai` package — there is no per-persona test tree. All tests are hermetic:
no network, no GCP credentials. Integration tests that may hit real endpoints
(Ollama, Anthropic) are marked `@pytest.mark.integration` and self-skip when
credentials/endpoints are absent; `ci.yml` also excludes them by marker with
`-m "not integration"`, so a test that forgets its `skipif` guard still cannot
make CI network-dependent.

Three suites live **outside** `tests/` and are not covered by `testpaths`:
`apps/agent_workflow_framework/tests/` (127 tests, no `pyproject.toml` — run
in-place with `uv run --with pyyaml python -m pytest tests/`),
`services/teams-copilot-mcp/tests/` (37 tests, its own `pyproject.toml`/`uv.lock`
— `uv run --project . --extra dev python -m pytest tests/`), and
`apps/sak_agent_dashboard/` (the repo's only Node subproject — 172 vitest tests,
run with `pnpm test`; see the dashboard gates below). All three are run by
`.github/workflows/subprojects.yml`, path-filtered to their own directories.

**The dashboard's CI job runs more than tests, and lint gates the rest.** The
`sak_agent_dashboard` job runs `pnpm lint` → `pnpm typecheck` → `pnpm test` →
`pnpm build` in that order, each `needs`-free but sequential, so a lint error
silently skips the three steps behind it (they report as skipped, not failed —
read the *first* red step, not the last). `pnpm lint` is stock
`eslint-config-next` v16, which enables the **React Compiler** rules
(`react-hooks/immutability`, `react-hooks/set-state-in-effect`, …). These are
stricter than the classic `exhaustive-deps` set and catch things a passing
vitest run will not: a `useCallback` that references itself, or an effect body
that calls `setState` synchronously. Run the full sequence locally before
pushing any change under `apps/sak_agent_dashboard/`:

```bash
cd apps/sak_agent_dashboard
pnpm install --frozen-lockfile
pnpm lint && pnpm typecheck && pnpm test && pnpm build
```

**Assert on the rule, not just the outcome.** Several guardrail rules overlap,
so a test that asserts only `action == DENY` can pass because a *different*,
broader rule fired — which is exactly how the container-escape battery in
`tests/test_guardrails_containers.py` stayed green while the container-specific
logic it was named after (`guardrails.py` rule 6) never executed once. New
guardrail tests must pin `result.reason` so the intended defense is what gets
verified.

That anti-pattern is not hypothetical and was **not** confined to the container
battery — a 2026-08-16 sweep found four more live instances in
`tests/test_guardrails_hardened.py` alone, all since fixed: two path tests
(`test_glob_pattern_denied`, `test_case_sensitivity_trick_denied`) whose inputs
were caught by the earlier sensitive-path branch so the rules they were named
for never ran; one that asserted `action in (ALLOW, DENY)`, which no behavior
can fail; and one that pinned the environment *before* setting
`SAKTHAI_SHELL_ALLOW`, so it denied at env-tampering two checks earlier than the
branch it claimed to cover. When writing a test for a specific rule, confirm the
rule actually fires — run it and read `result.reason` — rather than trusting a
green `DENY`.

Two guardrail branches are **structurally unreachable**, both shadowed by an
earlier, broader check, and both pinned by characterization tests rather than
deleted: `guardrails.py` rule 6 (container mounts/`cp`, shadowed by rule 2's
destructive-binary scan) and `check_enhanced_path_safety`'s case-trick branch
(shadowed by `_is_sensitive_path`, which already matches case-insensitively).
Rule 6 is extracted as `_check_container_tokens` and tested directly in
`tests/test_guardrails_container_rule.py`, so the backstop is verified before it
could ever become load-bearing. If you change rule 2's binary list or the rule
ordering, expect those characterization tests to fail — that is them working.

Key test areas:

- **Memory** — `test_memory_store.py`, `test_memory_sync.py`, `test_memory_aux.py`,
  `test_memory_concurrent.py`, `test_memory_merged.py`,
  `test_memory_secrets_redaction.py`, `test_store_migrations.py`,
  `test_store_properties.py` (hypothesis)
- **Agent** — `test_agent_loop.py`, `test_agent_loop_failure_seams.py`,
  `test_tools.py`, `test_tools_overrides.py`, `test_registry.py`, `test_usage.py`,
  `test_chat.py`, `test_eval*.py`, `test_context_filter.py`,
  `test_context_manager.py`, `test_prompt_builder.py`, `test_providers*.py`,
  `test_provider_contracts.py`, `test_provider_resilience.py`
- **Security** — `test_guardrails*.py` (12 files, incl.
  `test_guardrails_container_rule.py`), `test_sentinel_*.py` (6 files),
  `test_security_hardening.py`, `test_security_sentinel.py`,
  `test_persona_guardrails_parity.py`, `test_sakking_skill_security.py`,
  `test_giturl.py`, `test_web_auth.py`
- **MCP** — `test_mcp_server.py`, `test_mcp_client.py`,
  `test_mcp_client_resilience.py`, `test_mcp_manager.py`, `test_mcp_servers.py`,
  `test_mcp_main.py`
- **CLI** — `test_cli.py`, `test_cli_system.py`, `test_cli_eval.py`,
  `test_cli_heal.py`, `test_cli_consolidate_sessions.py`, `test_sessions_cli.py`,
  `test_entrypoint.py`
- **Healing** — `test_healing_circuit_breaker.py`, `test_healing_dlq.py`,
  `test_healing_integration.py`, `test_healing_models.py`,
  `test_healing_snapshot.py`, `test_healing_supervisor.py`
- **Self-healing CI** — `test_selfheal_ingest.py`, `test_selfheal_inspector.py`,
  `test_selfheal_safety.py`, `test_selfheal_patch.py`, `test_selfheal_verify.py`,
  `test_selfheal_diagnose.py`, `test_selfheal_walkthrough.py`,
  `test_selfheal_publish.py`, `test_selfheal_completion.py`,
  `test_selfheal_pipeline.py`
- **Repo/CI invariants** — `test_workflow_hygiene.py` (every workflow loadable,
  top-level `permissions:`, SHA-pinned actions, the `self-healing-ci.yml` fork
  guard, `codeql.yml`'s `config-file:`, `.bandit` parseable),
  `test_dependabot_config.py` (every `dependabot.yml` directory exists, is not a
  symlink, and holds a manifest of its declared ecosystem; no globs; no
  `target-branch`; bounded open-PR budget; and a completeness sweep that fails
  when a manifest has no entry and is not in `UNCOVERED_BY_DESIGN`)
- **Repo/persona invariants** — `test_soul_consistency.py`,
  `test_shared_package_divergence.py`,
  `test_compose_persona.py`, `test_export_agent_repo.py`,
  `test_persona_workspace_workflows.py`, `test_train_configs.py`
- `conftest.py` — shared fixtures: in-memory `MemoryStore`, temp dirs,
  mock Anthropic clients

**Pattern for new tests:** inject a fresh `MemoryStore(":memory:")` (SQLite
in-memory); mock the Anthropic/Gemini/OpenAI client at the boundary; never
reach out to a real endpoint. Use `tmp_path` fixtures for file I/O.

---

## Conventions specific to this repository

- **The memory store is the seam.** Anything touching SQLite goes through
  `MemoryStore`; anything an agent or MCP client can do goes through the
  `agent/tools.py` registry. Don't bypass either.
- **Config centralization.** No module hard-codes a path — everything goes through
  `config.py`. New paths and env-var names belong there.
- **Dependency injection over global state.** `run_agent()` and `handle_request()`
  accept injectable client, store, policy, and filter arguments; this is what
  makes them testable. Don't use module-level globals for these.
- **Tests assume no network and no GCP credentials.** Keep them hermetic; inject
  clients/stores instead of reaching out.
- **Sandbox defaults are deliberate.** `read_file` is restricted to cwd +
  `~/.sakthai` + `SAKTHAI_READ_ALLOW`; `run_command` is **opt-in** via
  `SAKTHAI_SHELL_ALLOW`. Don't widen these without reason.
- **Guardrail changes must be synced across personas.** Copy the canonical
  `personas/sakthai/sakthai/agent/guardrails.py` to every persona copy, or
  `tests/test_persona_guardrails_parity.py` fails CI.
- **Not linted / not type-checked:** ruff excludes `library/` and `scripts/`;
  mypy covers only `personas/sakthai/sakthai`. Don't "fix" lint/types in the
  other trees.
- **mypy is `strict`** over the package, with exactly one exemption:
  `sakthai.telegram.*` is `ignore_errors = true` (an early-stage standalone
  prototype). Keep all other new code strict-clean.
- **Schema migrations are additive.** Use `ALTER TABLE` only, under
  `BEGIN IMMEDIATE`. Never drop columns or tables in a migration.
- **Tool registry is the MCP server.** `BUILTIN_TOOLS` in `agent/tools.py` is
  the single definition; `mcp/server.py` reuses it directly. Add a tool once and
  it appears in both surfaces.
- **Later tool wins on name clash.** In `ToolRegistry.with_tools()`, a plugin or
  external MCP server tool can shadow a built-in by registering under the same
  name.
- **Ollama uses 127.0.0.1, not localhost.** IPv6 resolution for `localhost` breaks
  some environments; the OpenAI provider explicitly connects to `127.0.0.1`.
- **Scripts must fix up `sys.path`.** There is no root-level `sakthai/` package;
  `import sakthai` only works because of the editable install. Any script under
  `scripts/` that must run outside the installed env has to
  `sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))` first.
- **PRs into `main` need a non-author approval before merging.** Agent-opened
  PRs are reviewed by the repository owner; green CI is not a substitute, and a
  bot that auto-approves is explicitly out of bounds. Policy in
  `docs/CONTRIBUTING.md`, rationale and the Scorecard mechanism behind it in
  `docs/code-scanning-sweep-2026-08-12.md`.

---

## Workflow: Plan First

- **Always read and update `PLAN.md` before starting any work** in this repository.
  - Mark tasks `[ ]` → `[/]` (in progress) at the start of a phase.
  - Mark `[/]` → `[x] YYYY-MM-DD` (done with date) once the work is verified.
- **Never start coding a phase until it is checked off in PLAN.md** as in-progress.
- Terse one-word or short user approvals like `process`, `go`, `do it`, `run` after a plan summary = explicit approval to execute all queued plan steps.

### PLAN.md Safety

- **Never overwrite `PLAN.md` entirely.** Use targeted chunk replacements only.
- When marking tasks complete, find and replace only the specific `- [ ]` or `- [/]` line(s) — not whole sections.
- After any edit to `PLAN.md`, immediately re-read it to verify the surrounding content is intact before continuing.

`PLAN.md` is the master index; sub-plans live in `product/PLAN.md`,
`security/SECURITY_FIXES_PLAN.md`, `personas/*/PLAN.md`, and
`docs/superpowers/plans/`. Link, don't duplicate.

---

## Key environment variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Anthropic auth for `sakthai run` / `mcp` (or `ANTHROPIC_AUTH_TOKEN`, or Claude CLI OAuth) |
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Gemini auth (or Gemini CLI OAuth token) |
| `OPENAI_API_KEY` | Key for OpenAI-compatible gateway (defaults to `nokey`) |
| `OPENAI_API_BASE` / `OPENAI_BASE_URL` | Base URL for OpenAI-compatible endpoint |
| `OLLAMA_HOST` | Ollama server address (default: `http://127.0.0.1:11434`) |
| `SAKTHAI_GATEWAY_URL` | Base URL of an OpenAI-compatible AI gateway (OpenRouter/LiteLLM/Vercel/Cloudflare) — enables the `gateway` provider |
| `SAKTHAI_GATEWAY_API_KEY` | Bearer token for the AI gateway (defaults to `nokey`) |
| `HF_TOKEN` | Hugging Face access token — used by `sakthai hf` and the `huggingface` provider |
| `SAKTHAI_HF_API_BASE` | HF Inference Providers router base URL (default: `https://router.huggingface.co/v1`) |
| `SAKTHAI_HOME` | Override the `~/.sakthai` root (memory db, sessions, extensions, eval log) |
| `SAKTHAI_PERSONA` | Persona identity for systemd/Telegram launches — scopes skill discovery |
| `SAKTHAI_MODEL` / `SAKTHAI_PROVIDER` | Default model/provider for non-interactive launches |
| `SAKTHAI_FAST` / `SAKTHAI_STATELESS` / `SAKTHAI_NO_MCP` | Env equivalents of `--fast` / `--stateless` / `--no-mcp` |
| `SAKTHAI_WITH_SKILLS` | Comma-separated skill names injected into the system prompt |
| `SAKTHAI_SYSTEM_PROMPT` / `SAKTHAI_SYSTEM_PROMPT_FILE` | Inline or file-backed system-prompt prefix |
| `SAKTHAI_READ_ALLOW` | `os.pathsep`-separated extra paths the `read_file` tool may read |
| `SAKTHAI_SHELL_ALLOW` | Any non-empty value enables the `run_command` tool |
| `SAKTHAI_SANDBOX_NETWORK` | Docker `--network` value for `run --sandbox` (e.g. `none` to cut egress) |
| `SAKTHAI_MCP_CONFIG` | Override the external MCP server config path |
| `SAKTHAI_MCP_TIMEOUT` | Seconds to wait for an external MCP server reply (default: 30) |
| `SAKTHAI_MCP_ENV_PASSTHROUGH` | Env vars forwarded to spawned MCP servers |
| `SAKTHAI_EVAL_LOG` | Override the eval/MLOps JSONL log path (default `SAKTHAI_HOME/eval.jsonl`) |
| `SAKTHAI_WEB_ALLOW_PUBLIC` | Opt-in to non-loopback binds for the web server (default: refused — loopback-only) |
| `SAKTHAI_AGENT_ACTIVE` | Set by the loop itself; the `run_agent_loop` recursion guard reads it |
| `SAKKING_HOME` | Override the SakKing data dir (default `~/.sakking`) for `skills sync-sakking` |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` / `TELEGRAM_ALLOWED_USER_IDS` | Telegram gateway and the `send_telegram_message` tool |
| `MS_GRAPH_CLIENT_ID` / `MS_GRAPH_TENANT_ID` / `MS_GRAPH_REFRESH_TOKEN` | Microsoft Graph mail + calendar tools (seed via `scripts/graph_device_login.py`) |

---

## Local skills for this repo

- `run-sakthai-agent-v2` — use when asked to build, run, drive, or smoke-test the SakThai CLI/agent loop/MCP server/web API in this monorepo.
- `Sak-family-auto-cycle` — use when asked to run the six-persona (SakKing/SakThai/SakSee/SakSit/SakTan/SakJules) auto-cycle or dispatch them as a team.

## Skills format

A skill is a directory containing a `SKILL.md` with a YAML frontmatter block:

```yaml
---
name: my-skill
category: coding
description: One-line summary of what this skill does
version: "1.0"
platforms: [linux, macos, windows]   # host OSes the skill supports
metadata:
  sakthai:
    tags: [python, testing]
    related_skills: [other-skill]
---

Skill body goes here. This is injected into the agent system prompt when the
skill is active.
```

Note: `tags`/`related_skills` must be nested under `metadata.sakthai` — a flat
top-level `tags:`/`related_skills:` is silently ignored by the parser in
`skills.py`.

Discovery roots are listed under "Other subsystems" above. Run
`sakthai skills list` to see everything discovered, and `sakthai skills validate
--naming` to check the `Sak-`/`Sak<Name>-` prefix convention.
`sakthai run --dry-run` validates `--with-skills` names and fails on
unresolved ones; a live run warns and skips them.

A skill directory may also carry `commands/<name>.md` files, which become
`/skill:command` slash commands for `sakthai run` (see "Runtime entry points").

---

## Adding a new built-in tool

1. Add a `Tool(name=..., description=..., input_schema=..., handler=...)` to
   `BUILTIN_TOOLS` in `personas/sakthai/sakthai/agent/tools.py`.
2. The tool automatically appears in both `sakthai run` (agent loop) and
   `sakthai mcp` (MCP server) — no other wiring needed.
3. Write a test in `tests/test_tools.py` using an injected `MemoryStore(":memory:")`.
4. If the tool touches the filesystem or network, sandbox it appropriately
   (follow the `read_file` / `run_command` patterns) and check whether
   `agent/guardrails.py` needs a matching rule.

---

## Docs

| File | Contents |
|------|---------|
| `docs/architecture.md` | Full layer diagram and SQLite schema |
| `docs/capabilities.md` | Feature list |
| `docs/plugins.md` | Skills and MCP extensibility |
| `docs/replication.md` | Multi-agent memory sync |
| `docs/runtimes.md` | CLI / agent loop / MCP server |
| `docs/workspace.md` | Dev environment setup |
| `docs/og_parity_audit.md` | Comparison with original SakThai |
| `docs/integrations.md` | Composio and cross-agent communication recipes |
| `docs/skill-naming.md` | The `Sak-` / `Sak<Name>-` naming convention |
| `docs/agent-diagnosis.md` | Standalone run checklist and runtime notes |
| `docs/self-healing-ci.md` | The `sakthai heal` pipeline, its safety model, and the workflow that drives it |
| `.github/codeql/README.md` | Why CodeQL runs as an advanced setup, how the scope config reaches it, the per-language query suites, and `scripts/codeql_local.sh` |
| `infra/self-hosted-runner/README.md` | Installing and operating a self-hosted Actions runner, and the `CI_RUNNER_LABEL` opt-in that keeps it reversible |
| `docs/configuring-multi-ecosystem-updates.md` · `docs/dependabot-setup.md` | The five-ecosystem Dependabot config and why it is shaped that way · enabling the repository settings the config cannot |
| `.github/INNERSOURCE.md` | Advisory ownership, severity SLAs, and how accepted-risk advisories are recorded |
| `docs/SOUL.md` · `docs/USER.md` · `docs/OPERATING_CONTRACT.md` | Team identity · Beer's profile · agent operating rules |
| `docs/SECURITY.md` · `docs/security-hardening.md` · `docs/SECURITY_HARDENING_IMPLEMENTATION.md` | Security policy/architecture · audit findings and the prevention pattern + regression test for each · implementation notes |
| `docs/security_audit_2026-07-11.md` · `docs/security_audit_2026-07-12.md` | Point-in-time audit reports |
| `docs/superpowers/plans/` · `docs/superpowers/specs/` | Dated feature plans and design specs |
| `AGENTS.md` | Repo guidelines + the SakJules PR protocol |
