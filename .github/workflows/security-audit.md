---
name: Security Audit
emoji: "🛡️"
description: |
  Weekly security sweep. Runs the repository's own scanners — bandit under this repo's
  configuration, pip-audit over the locked dependency set, and the guardrail/sentinel
  regression suite — then triages what they report against the prevention table in
  docs/security-hardening.md and opens at most one issue when something is actionable.
  This replaces the retired continuous-security.yml, which invoked the agent through the
  Anthropic provider and therefore skipped every night on a repository that has no
  ANTHROPIC_API_KEY configured; this workflow runs on the same Gemini engine as the rest
  of the agentic workflows here. It audits and never edits: no pull requests, no writes.

on:
  schedule: weekly on thursday
  workflow_dispatch:

permissions:
  contents: read
  issues: read
  pull-requests: read

engine: gemini
strict: true

network:
  allowed:
    - defaults
    - python

steps:
  - name: Checkout repository
    uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
    with:
      persist-credentials: false

  - name: Set up Python
    uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97
    with:
      python-version: "3.12"

  - name: Install uv
    run: pipx install uv

  - name: Install the package
    run: uv sync --all-extras

  # Every scanner runs with `set +e` and its exit code recorded rather than
  # propagated: a finding is something for the agent to triage, not a reason for
  # the workflow itself to go red. ci.yml is the job that fails a build on bandit.
  - name: Collect scanner output
    run: |
      set +e
      mkdir -p /tmp/gh-aw/agent

      uv run bandit -c pyproject.toml -r personas/sakthai/sakthai \
        > /tmp/gh-aw/agent/bandit.txt 2>&1
      echo "exit_code=$?" >> /tmp/gh-aw/agent/bandit.txt

      # Same export/audit pair dependency-audit.yml runs, so the two jobs cannot
      # disagree about which packages are in scope. --all-groups matters: the
      # dependency groups are not extras, and --all-extras alone misses them.
      uv export --frozen --all-extras --all-groups --no-emit-project --no-hashes \
        -o /tmp/gh-aw/agent/requirements.txt 2>&1
      uvx pip-audit -r /tmp/gh-aw/agent/requirements.txt --disable-pip --no-deps \
        > /tmp/gh-aw/agent/pip-audit.txt 2>&1
      echo "exit_code=$?" >> /tmp/gh-aw/agent/pip-audit.txt

      uv run pytest tests/test_guardrails_hardened.py tests/test_security_hardening.py \
        tests/test_security_sentinel.py tests/test_persona_guardrails_parity.py \
        tests/test_giturl.py tests/test_web_auth.py -q \
        > /tmp/gh-aw/agent/guardrails.txt 2>&1
      echo "exit_code=$?" >> /tmp/gh-aw/agent/guardrails.txt

      echo "--- collected ---"
      wc -l /tmp/gh-aw/agent/bandit.txt /tmp/gh-aw/agent/pip-audit.txt \
        /tmp/gh-aw/agent/guardrails.txt

safe-outputs:
  create-issue:
    title-prefix: "[security] "
    labels: [security, automation]
    max: 1
    close-older-issues: true

tools:
  cache-memory: true
  bash:
    - "cat"
    - "find"
    - "grep"
    - "ls"
    - "wc"

timeout-minutes: 20
---

# Security Audit

This repository's security posture rests on four things running and being read: bandit
under `[tool.bandit]` in `pyproject.toml`, pip-audit over the locked dependency closure,
the guardrail layer in `personas/sakthai/sakthai/agent/guardrails*.py` with its regression
suite, and the parity rule that keeps every persona's copy of `guardrails.py` byte-identical
to the canonical one.

A step before this prompt has already run all four and captured the output. **You are
triaging that output, not re-scanning and not fixing anything.** Do not edit tracked files,
do not open a pull request, and do not propose changes to anything under `.github/` or to
the guardrail subsystem itself — those are deliberately outside what an automated agent
may touch here (see `docs/self-healing-ci.md` for the same boundary applied to the
self-healing agent).

## Inputs

| File | What it holds |
|---|---|
| `/tmp/gh-aw/agent/bandit.txt` | bandit over `personas/sakthai/sakthai`, with `-c pyproject.toml` so this repo's `skips` apply. Last line is `exit_code=`. |
| `/tmp/gh-aw/agent/pip-audit.txt` | pip-audit over the exported lock. Last line is `exit_code=`. |
| `/tmp/gh-aw/agent/guardrails.txt` | The guardrail, hardening, sentinel, persona-parity, git-URL and web-auth test files. Last line is `exit_code=`. |
| `/tmp/gh-aw/agent/requirements.txt` | The exact resolved dependency set pip-audit read. |

## What to do

1. Read each file's last line for its exit code, then read the body. Treat a non-zero exit
   as findings to report, never as a reason to fail this workflow.
2. **bandit** — for each finding, give the test id (`B###`), severity, confidence, file and
   line. `pyproject.toml` deliberately skips B101 and the subprocess rules the guardrail
   layer exists to police; if one of those appears anyway, that means the configuration was
   not applied and is itself the finding. Say so plainly.
3. **pip-audit** — for each advisory, name the package, the installed version, the fixed
   version if one exists, and whether the package is a direct dependency or transitive.
   `dependency-audit.yml` ignores `PYSEC-2026-1939` / `GHSA-g4r7-86gm-pgqc` (sqlitedict,
   no fixed version, reachable only through the `evals` group); if either shows up here,
   report it as known-and-accepted rather than as new.
4. **Guardrail suite** — a failure here is the most serious thing this workflow can find.
   Report the failing test's name and its assertion verbatim. A `test_persona_guardrails_parity`
   failure specifically means a persona's copy of `guardrails.py` has drifted from the
   canonical `personas/sakthai/sakthai/agent/guardrails.py`; name the persona and the file.
5. Cross-check anything you report against the prevention table in
   `docs/security-hardening.md`. If a finding matches a row that already documents it as
   accepted, mitigated, or structurally unreachable, say which row and do not re-raise it
   as new.

## Reporting

Open an issue **only if** there is something actionable: a bandit finding not covered by
the configuration, a new advisory with a fix available, or any guardrail/parity test
failure. A clean sweep creates nothing and simply says so in the run log — a weekly
"nothing found" issue is noise.

When you do open one:

- Title: `Security audit — <n> finding(s)`
- Lead with a one-line verdict, then one section per scanner, each a table of
  finding → location → the one-line next step.
- Quote each scanner's own output for a finding rather than restating it in your words —
  the exact string is what someone will grep for.
- Rank guardrail/parity failures above everything else, regardless of what the other
  scanners reported.
- Include the run URL:
  ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
