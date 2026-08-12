# Code-scanning sweep — 2026-08-12

A full pass over everything that feeds
[the code-scanning dashboard](https://github.com/beer-sakthai/Sak-Family-Agent/security/code-scanning),
run against `main` at `b4cc123`.

**Result: every scanner that still runs on this repository reports zero
findings.** The alerts on the dashboard are orphans — they were uploaded by a
Codacy workflow that was deleted in July, and nothing that can be changed in
this repository will clear them. Clearing them takes one command against the
API with a token this repository's Actions do not have; see
[Remediation](#remediation).

## Why the dashboard was reproduced rather than read

Listing alerts needs the "Code scanning alerts" repository permission
(`security_events` on a classic PAT). The token available to Actions and to
agent sessions here does not carry it — `GET /code-scanning/alerts`,
`/code-scanning/analyses` and `/code-scanning/default-setup` all return
`403 Resource not accessible by integration`. So each contributing tool was
reproduced or read from its own run logs instead.

This is the second sweep to hit that wall; PR #599 hit it earlier the same day.
`scripts/code_scanning_analyses.py` exists so the next one does not have to
rediscover any of this.

## What actually uploads to the dashboard

Only two workflows call `github/codeql-action/upload-sarif`
(`ossar.yml`, `scorecard.yml`); CodeQL itself runs through default setup, which
is configured in repository settings and has no workflow file.

| Tool | Source | Findings | Evidence |
|---|---|---|---|
| **CodeQL** | default setup — `python`, `javascript-typescript`, `actions` | **0** | reproduced locally, below |
| **eslint** | `ossar.yml` → `microsoft/security-devops-action` | **0** | job 94034310166: `Active results: 0` |
| **Scorecard** | `scorecard.yml` | **1** (note) | artifact 9131513797: a single `BranchProtectionID` result |
| **gitleaks** | `secret-scan.yml` | **0** | artifact 9131504765 — and it uploads only as an artifact, never to the dashboard |
| **Codacy** | `codacy.yml`, **deleted 2026-07-03** | **~15k, all still open** | see below |

### CodeQL — reproduced at 0

Default setup pins CodeQL CLI **2.26.2** with query packs `python-queries`
1.8.7, `javascript-queries` 2.4.2 and `actions-queries` 0.6.32, running each
language's default `code-scanning` suite (45 queries for Python). Matching that
exactly matters: the `security-extended` suite would report findings the
dashboard does not have.

```bash
BUNDLE=https://github.com/github/codeql-action/releases/download/codeql-bundle-v2.26.2/codeql-bundle-linux64.tar.gz
curl -sSL "$BUNDLE" | tar xz            # unpacks ./codeql

for lang in python javascript-typescript actions; do
  ./codeql/codeql database create "db-$lang" --language="$lang" --source-root=. --overwrite
done

./codeql/codeql database analyze db-python               python-code-scanning.qls     --format=sarif-latest --output=python.sarif
./codeql/codeql database analyze db-javascript-typescript javascript-code-scanning.qls --format=sarif-latest --output=javascript.sarif
./codeql/codeql database analyze db-actions              actions-code-scanning.qls    --format=sarif-latest --output=actions.sarif

jq '.runs[0].results | length' python.sarif javascript.sarif actions.sarif   # → 0 0 0
```

Coverage matched the hosted run file for file — 755 of 756 Python files, 45 of
54 JavaScript/TypeScript files, 17 of 17 Actions files — so this is the same
analysis the dashboard sees, not a narrower one.

The four `py/clear-text-logging-sensitive-data` families and the
`actions/missing-workflow-permissions` finding that PR #599 fixed are all
confirmed still closed, and all 17 workflows carry a top-level `permissions`
block.

### Codacy — the orphaned alerts

`.github/workflows/codacy.yml` ran `codacy/codacy-analysis-cli-action` unscoped
over the whole monorepo. Run 28634356719 on `main` (2026-07-03) ends with
`Successfully uploaded results` / `Analysis upload status is complete`. The
workflow was removed hours later in `7224074c`, whose message records what it
had been uploading:

> Before it broke, it ran unscoped over the whole monorepo and uploaded ~15k
> style-level lint findings (Pylint, Remark-lint, Prospector, ...) to GitHub
> code scanning, duplicating coverage already provided by CodeQL, bandit, ruff,
> super-linter, and SonarCloud scoped in ci.yml.

An alert is only ever closed by a **newer analysis from the same tool** that no
longer reports it. With the workflow gone, no such analysis will ever arrive,
so all of those findings stay open permanently. They are style-level lint
results — `codacy-analysis-cli` emits one SARIF run per underlying linter, so
they are spread across several tool names on the dashboard rather than one.

Restoring the workflow is not the fix: it was deleted deliberately, for being
both broken (a bad merge left duplicate `pull_request` keys) and redundant with
CodeQL, bandit, ruff and SonarCloud. Deleting the analyses is the supported
remedy.

### The advanced/default setup collision

Partway through this sweep, `5648d3ab` ("[StepSecurity] Apply security best
practices", PR #603) added `.github/workflows/codeql.yml` — the stock GitHub
CodeQL starter template, matrix `["javascript", "python", "typescript"]`.

Default setup is enabled on this repository, and the two cannot coexist: every
job from that workflow uploaded its SARIF and then failed with

```
Code Scanning could not process the submitted SARIF file:
CodeQL analyses from advanced configurations cannot be processed when the
default setup is enabled
```

This broke `Analyze (javascript)`, `Analyze (python)` and
`Analyze (typescript)` on `main` and on every open PR, while the default-setup
jobs (`Analyze (javascript-typescript)`, `Analyze (python)`,
`Analyze (actions)`) passed alongside them. The workflow has been removed here,
restoring the state CLAUDE.md already documents:

> CodeQL runs via GitHub's *default setup* (repo settings), so there is
> deliberately no `codeql.yml` — adding one would conflict.

Nothing is lost by removing it. Default setup analyses `python`,
`javascript-typescript` and `actions`; `javascript-typescript` is exactly
`javascript` + `typescript`, so the template's matrix was a strict *subset* of
what already runs — it did not even cover `actions`.

The rest of #603 (the `harden-runner` steps across all workflows,
`dependency-review.yml`, `.pre-commit-config.yaml`, the expanded
`dependabot.yml`) is kept as-is.

### Scorecard — Branch-Protection

The one live finding, note-level, scoring 3:

- branch protection settings do not apply to administrators
- `main` does not require approvers
- CODEOWNERS review is not required
- PRs are not required to make changes

All four are repository settings — no diff can close them. Note also that
`scorecard.yml` leaves `repo_token` commented out, so Scorecard is reading only
what the public API exposes and may be under-reporting what is actually
configured.

Turning these on is a real trade-off, not an oversight: requiring approvers on
`main` blocks the agent-driven workflows this repository runs on (`SakJules`,
`claude/*` branches, the nightly `continuous-security.yml` patch pipeline),
each of which merges its own PRs.

## Remediation

Both remaining items need repository-owner access, not a pull request.

**1. Clear the orphaned Codacy alerts.** No personal access token is needed:
the permission involved is one the repository's own `GITHUB_TOKEN` can be
granted per job, so the cleanup runs as a workflow.

From the Actions tab, run **Code scanning cleanup**
(`.github/workflows/code-scanning-cleanup.yml`):

1. Run it with no inputs. It reports every open alert and analysis grouped by
   the tool that produced it. The orphans identify themselves — their
   `latest analysis` date is stuck in July, next to today's date on the tools
   that still run.
2. Re-run with `tool` set to one of those names, leaving `apply` unchecked, to
   see exactly which analyses would go.
3. Re-run with `apply` ticked to delete them. Repeat per tool name.

Deleting an analysis also deletes the alerts derived from it and cannot be
undone — which is what is wanted here, since no producer remains to re-report
them.

The same script runs locally if preferred, with a PAT carrying the
"Code scanning alerts" permission:

```bash
export GITHUB_TOKEN=<pat with code-scanning write>
python scripts/code_scanning_analyses.py list
python scripts/code_scanning_analyses.py delete --tool <name>          # dry run
python scripts/code_scanning_analyses.py delete --tool <name> --apply  # delete
```

**2. Branch-Protection** — a settings change on `main`, weighed against the
agent workflows above.

## Also worth knowing

- The **`github-advanced-security` check ("Code scanning AI findings")** fails
  on this repository's PRs at the `Processing Request` step. It is a
  GitHub-side `dynamic/agents/github-advanced-security` workflow, not something
  in this repository; PR #602 merged with it red. Treat it as non-blocking.
- **`mobsf.yml`** was added and removed the same day and never registered a
  workflow run, so unlike Codacy it left nothing behind.
- **Dependabot alerts** (`PYSEC-2026-1939`, `sqlitedict` via `lm-eval`) live on
  a different tab and are unaffected by any of the above.
