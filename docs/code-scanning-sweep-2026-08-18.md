# Code-scanning sweep — 2026-08-18

A read of [the code-scanning dashboard](https://github.com/beer-sakthai/Sak-Family-Agent/security/code-scanning)
and the changes it prompted. `main` at `67e85f5`.

**Result: 5,832 open alerts, and 5,000 of them are one misconfigured workflow
reporting `assert` statements in the test suite.** The previous sweep
([2026-08-12](code-scanning-sweep-2026-08-12.md)) left the dashboard at 6.

## The measurement

Read from the dashboard itself, by dispatching **Code scanning cleanup** with no
inputs — run
[32088928144](https://github.com/beer-sakthai/Sak-Family-Agent/actions/runs/32088928144).
Nothing in this document is inferred from a workflow's source; the counts below
are the API's own, which is the standing lesson of the previous sweep's two
recorded corrections.

```
Open code-scanning alerts on beer-sakthai/Sak-Family-Agent: 5832

tool         open alerts  analyses  latest analysis
-----------  -----------  --------  --------------------
Bandit       5000         425       2026-08-18T01:37:51Z
BinSkim      0            412       2026-07-06T05:01:03Z
CodeQL       788          7891      2026-08-18T01:38:25Z
ESLint       0            2310      2026-08-18T01:38:12Z
Scorecard    21           920       2026-08-18T01:37:33Z
github-repo  23           1         2026-08-17T09:47:23Z
mobsfscan    0            14        2026-08-12T04:14:21Z
```

## Bandit — 5,000, and the number is a cap, not a count

By rule:

| Count | Rule | What it is |
|---:|---|---|
| 4,525 | `B101` | `assert_used` |
| 105 | `B603` | `subprocess_without_shell_equals_true` |
| 86 | `B404` | `import subprocess` |
| 55 | `B310` | `urllib.urlopen` audit |
| 47 | `B108` | hardcoded `/tmp` |
| 37 | `B105` | hardcoded password string |
| 37 | `B615` | unpinned Hugging Face download |
| … | | 17 rules in total |

By tree: `sakthai-chat-cli` 2,944, `personas` 1,272, `tests` 640, `services` 44,
`scripts` 37, `training` 22, `apps` 20, `fuzz` 11.

**5,000 is exactly GitHub's per-upload SARIF cap.** The real figure is higher and
the overflow was discarded silently; a local run of the same scan over the same
tree produces 7,960 results outside `.venv`.

### Root cause

`.github/workflows/bandit.yml` was a stock starter template driving
`shundor/python-bandit-scan` with every optional input left commented out — no
`path`, no `ini_path`, no `skips`. Two consequences, and the first is the one
that matters:

1. **The repository's own Bandit configuration was never loaded.** Bandit reads
   `[tool.bandit]` from `pyproject.toml` only when that file is passed with
   `-c`. Without it, `skips = ["B101", "B404", "B603", "B606", "B607"]` and
   `exclude_dirs = ["tests"]` were both ignored — so the scan reported, as
   security findings, precisely the rules this repository had already decided
   were not findings. 4,525 of the 5,000 are assertions in `tests/`.
2. **The scan walked three trees that are not first-party code**: `tests/`, the
   folded-in `sakthai-chat-cli/` copy of a separate repository, and the ~900
   skill directories under `personas/*/skills/`.

None of this ever failed a build — the action ran with `exit_zero: true` — so
the only symptom was the dashboard.

Worth naming: `ci.yml` has run `uv run bandit -c pyproject.toml -r
personas/sakthai/sakthai` on every push and PR the whole time, and it reports
zero. The gate was never broken. What was broken was the thing publishing to the
Security tab beside it, and the two disagreed by five thousand.

### The fix

`bandit.yml` now runs Bandit directly — `bandit -c pyproject.toml -r .` with an
`--exclude` list for the non-first-party trees — and uploads the SARIF with
`github/codeql-action/upload-sarif`. In scope: the package, the shared package
copy, `scripts/`, `services/`, `infra/`, `training/`, `apps/`, `fuzz/`. Out of
scope: `tests/`, `library/`, `sakthai-chat-cli/`, `personas/*/skills/`, and
build/dependency output. New first-party code is covered without editing the
file again.

Measured against the same tree, the same command the workflow now runs:

```
5,000 results  ->  63 results,  0 HIGH severity
```

The 63 break down as 23 × `B615` (Hugging Face `from_pretrained` /
`load_dataset` without a pinned revision, in `training/` and `scripts/`),
13 × `B311` (`random` for non-crypto use), 11 × `B108` (hardcoded `/tmp`),
6 × `B110`, 4 × `B310`, 3 × `B105`, 3 × `B112`. Those are a real backlog, small
enough to read in one sitting, and none of them are in
`personas/sakthai/sakthai` or `personas/shared/sakthai` — both scan clean.

Bandit writes `Bandit` as the tool name in its SARIF, unchanged from before, so
a run of the new workflow supersedes the old analyses. **This is the part to
verify rather than assume**: an alert is only closed by a newer analysis from
the same tool *and category*. If the 5,000 are still open after this lands on
`main` and the workflow has run, they are orphaned under the old category, and
the remedy is the documented one — dispatch **Code scanning cleanup** with
`tool: Bandit` and `apply` ticked, which deletes every Bandit analysis and lets
the next run repopulate the 63. That deletion is irreversible and is the
repository owner's call.

## CodeQL — 788, up from 0 on 2026-08-13

| Count | Rule | Severity |
|---:|---|---|
| 707 | `py/path-injection` | high |
| 28 | `js/path-injection` | high |
| 25 | `py/polynomial-redos` | high |
| 22 | `py/command-line-injection` | critical |
| 3 | `js/resource-exhaustion` | high |
| 2 | `js/request-forgery` | critical |
| 1 | `py/full-ssrf` | critical |

Where they land: 545 of the 788 are in trees this repository does not author —
~235 in vendored `personas/*/skills/` scripts (the same handful of upstream
files re-reported once per persona that carries a copy: three `clean.py` copies
account for 108 alerts between them), 236 in the folded-in `sakthai-chat-cli/`
duplicate, 74 in `tests/`. The remaining ~243 are first-party: 99 in
`personas/sakthai/sakthai`, 99 in its `personas/shared/sakthai` duplicate, and
the rest across `apps/`, `scripts/` and `infra/`.

### What the first-party findings actually are

The 99 in the canonical package are 88 `py/path-injection`, 10
`py/polynomial-redos` and 1 `py/command-line-injection`, spread over
`extensions/install.py` (11), `selfheal/ingest.py` (10), `agent/tools.py` (9),
`memory/sync.py` (9), `mcp/servers.py` (7) and fifteen other modules.

They were not taken at face value. The one critical — `py/command-line-injection`
in `sandbox.py:166` — was read line by line: the call is `subprocess.run(cmd,
shell=False)` against a list, with the task string appended after a `--`
separator specifically so a task beginning with `-` cannot be parsed as an
option, and it is already annotated `# nosec B603` with that reasoning. CodeQL
flags it because a CLI argument reaches a subprocess. That is what
`sakthai run --sandbox` *is*: a local CLI running the task its own operator
typed. No privilege boundary is crossed, and there is nothing to fix.

The bulk of the `py/path-injection` set has the same shape — `SAKTHAI_HOME`,
`--db`, `--persona` and similar operator-supplied values reaching `Path()` and
`open()`. The two places where a path really does cross a trust boundary are
already guarded and already tested: the `read_file` tool is confined to cwd +
`~/.sakthai` + `SAKTHAI_READ_ALLOW`, and `agent/guardrails.py` runs
`_is_sensitive_path` over every tool argument. Rewriting 88 call sites to
satisfy a taint tracker whose source is the operator would be a large,
regression-prone change that improves nothing.

**So none of the 788 is being "fixed" by editing code, and no attempt is made to
claim otherwise.** What the change below does is make the first-party 243
visible by removing the 545 that are not.

### `.github/codeql/codeql-config.yml` — added, and inert until a property is set

CodeQL runs here through default setup, so there is no workflow to add
`paths-ignore` to, and adding one is the failure this repository has already hit
twice. Default setup does support a merged config file, but only via a custom
repository property:

> Settings → Custom properties → `codeql-config-file` = `.github/codeql/codeql-config.yml`

The file is committed with the exclusions and the reasoning. **Until an
administrator sets that property it does nothing at all**, and this document
does not count its alerts as closed. Setting it requires admin rights on the
repository, which no agent here has.

## Scorecard — 21, one of them a real vulnerability

`DangerousWorkflowID` #15541, severity **critical**, at
`.github/workflows/self-healing-ci.yml:65`: *untrusted code checkout
`${{ github.event.workflow_run.head_sha || github.sha }}`*.

This one is genuine and was fixed. The mechanism:

- The workflow triggers on `workflow_run` for CI completions, so it runs in the
  **base** repository's context, with this job's `contents: write` /
  `pull-requests: write` token and the `ANTHROPIC_API_KEY` secret.
- It then checks out `workflow_run.head_sha` and executes it — `uv sync
  --all-extras` alone runs arbitrary build hooks from the checked-out tree.
- The `branches: [main]` filter on the trigger is not a defence. It matches the
  triggering run's head branch **name**, and a pull request opened from a fork's
  own `main` branch produces a CI run whose `head_branch` is `main` and whose
  `head_sha` is the contributor's commit.

The job's `if:` now additionally requires
`github.event.workflow_run.head_repository.full_name == github.repository`, so
the workflow can only ever heal a commit already in this repository.
`workflow_dispatch` is unaffected.

Expect the alert to stay open regardless. Scorecard's check is syntactic — it
looks for a checkout whose `ref` is an untrusted expression and does not
evaluate the guarding `if:`. The alternative, resolving the SHA in an earlier
step so the expression is no longer visible at the checkout, would close the
alert without changing the behaviour by one bit. That is gaming the check and it
was not done.

The other 20:

| Count | Rule | Sev | Disposition |
|---:|---|---|---|
| 15 | `TokenPermissionsID` | high | 14 accepted, 1 stale |
| 2 | `PinnedDependenciesID` | medium | both stale |
| 1 | `BranchProtectionID` | high | repository settings, owner-only |
| 1 | `CodeReviewID` | high | 0/12 approved changesets — the 2026-08-13 review policy, climbing as reviewed merges enter the window |
| 1 | `CIIBestPracticesID` | low | badge is `InProgress` on bestpractices.dev |

The accepted `TokenPermissionsID` set is job-scoped `contents: write` /
`security-events: write` / `actions: write` in workflows that push branches,
cut releases or upload SARIF — 10 of them in the gh-aw–generated `*.lock.yml`
files. A workflow that pushes needs `contents: write` somewhere and job scope is
already the tighter of the two options; this is the same accepted risk the
2026-08-12 sweep recorded, unchanged.

Three are stale rather than accepted, all three verified against the tree
rather than assumed: `PinnedDependenciesID` #21379 cites
`datadog-synthetics.yml:30`, and that file is not on `main` at all;
`PinnedDependenciesID` #16372 and `TokenPermissionsID` #16371 cite
`bandit.yml:32` and `bandit.yml:1`, but the version of `bandit.yml` on `main`
before this change already pinned `actions/checkout` by SHA and already carried
a top-level `permissions:` block (line 23). All three should close on the next
Scorecard run.

## OSPS baseline (`github-repo`) — 23, of which 21 are passes

This tool uploads one SARIF result per control it evaluated, including the ones
that **passed**: "Repository is public", "Issues are enabled for the
repository", "License was found in a well known location", "This control is
enforced by GitHub for all projects". Those are not findings, and no diff will
make them go away — the alert count for this tool is its control count.

Two are `error` severity and both say the same thing: `OSPS-DO-01.01` ("User
guide was NOT specified in Security Insights data") and `OSPS-QA-04.01`
("Insights does not contain a list of repositories"). Five more —
`OSPS-AC-03.01`, `OSPS-BR-03.02`, `OSPS-BR-07.01`, `OSPS-DO-02.01`,
`OSPS-GV-03.01` — reduce to "no Security Insights declaration was found".

All seven would close together with an OpenSSF **Security Insights v2.0.0**
manifest (`SECURITY-INSIGHTS.yml`) at the repository root. It is deliberately
**not** added here: the manifest asserts facts about the project — vulnerability
reporting process, official distribution points, project lifecycle status,
named security contacts, the repository list — that are the owner's to state and
would otherwise be invented. Writing a plausible-looking security manifest is
exactly the failure mode the previous sweep's two Corrections are about. The
facts needed are listed above; the file is a short one once they exist.

Two more will not close by any diff:

- `OSPS-LE-02.01` / `OSPS-LE-02.02` (warning) — "License file `LICENSE` is
  present but its SPDX identity could not be determined". Correct: `LICENSE` is
  a bespoke "House of Sak — Intellectual Property License, All Rights
  Reserved". It is not OSI- or FSF-approved and is not meant to be. Permanent
  by design.
- `OSPS-BR-01.01` (warning) — "Unable to evaluate 4 of 31 workflow files":
  `ci-doctor.lock.yml` and its siblings use `concurrency.queue`, which the
  baseline scanner's workflow parser does not recognise. The workflows are
  valid; the parser is behind.

## Where this leaves the dashboard

| Tool | Before | Expected after | By what |
|---|---:|---:|---|
| Bandit | 5,000 | 63 | the rewritten workflow's next run (or an analysis delete, if the category orphans them) |
| CodeQL | 788 | 788, or ~243 | unchanged unless an admin sets `codeql-config-file` |
| Scorecard | 21 | 18 | 3 stale alerts closing; the critical one stays open by design |
| github-repo | 23 | 23, or 16 | unchanged unless `SECURITY-INSIGHTS.yml` is written |
| **Total** | **5,832** | **~892** | |

One real vulnerability was found and fixed (`DangerousWorkflowID` #15541). The
other 5,831 alerts were, in descending order: a scanner configured to ignore the
repository's own configuration, a scanner scoped to trees the repository does
not own, and a scanner reporting its passes.
