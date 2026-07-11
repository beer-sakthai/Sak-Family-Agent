# Repository Security Audit — 2026-07-11

Full-repo security review covering GitHub Actions workflows, secret handling,
dependency management, and the `sakthai` package's own sandbox controls.
Fixes applied in the same change are marked **[fixed]**; items left for a
human decision are marked **[recommendation]**.

## Summary

The code-level security posture is strong: the agent's shell tool is opt-in,
file reads are allowlisted, the web server binds to localhost, migrations are
additive, and no hardcoded credentials were found in the working tree. The
gaps were almost entirely in the CI/automation layer — controls that were
*documented* but not actually *wired up*, plus a few supply-chain hygiene
issues in the workflows.

## Findings and actions

### 1. Secret scanning was documented but never ran — **[fixed]**

`SECURITY.md` claimed a gitleaks workflow (`secret-scan.yml`) runs "on every
push and pull request". No such workflow existed; `.gitleaks.toml` was inert
configuration. Added `.github/workflows/secret-scan.yml`: full-history
gitleaks scan on pushes to `main`, all PRs, and manual dispatch, using the
existing `.gitleaks.toml` allowlist.

### 2. The "Continuous Security Scan" workflow is dormant — **[recommendation]**

`continuous-security.yml` sits at the **repository root**, not in
`.github/workflows/`, so GitHub never schedules it. The nightly
"digital immune system" described in `SECURITY.md` has therefore never run.
Not moved automatically because activating it is a cost/credential decision:
it spends Anthropic API credits nightly and needs the `ANTHROPIC_API_KEY` and
`GH_PAT_FOR_ACTIONS` secrets, and it runs the agent with
`SAKTHAI_SHELL_ALLOW=1` and `contents: write`. If you want it live, move the
file into `.github/workflows/` — and consider restricting it to
`workflow_dispatch` first to trial it. `SECURITY.md` now states this honestly.

### 3. Unpinned third-party action (`@latest`) — **[fixed]**

`ossar.yml` used `microsoft/security-devops-action@latest` — a floating tag
that would silently pick up any future (including compromised) release of a
third-party action that gets `security-events: write`. Pinned to `v1.12.0`;
Dependabot's `github-actions` ecosystem keeps it current.

### 4. No vulnerability audit of *current* dependencies — **[fixed]**

Dependabot proposes version bumps, but nothing failed when an existing pin in
`uv.lock` had a published CVE. Added `.github/workflows/dependency-audit.yml`:
`pip-audit` over the exported lock (weekly, on dependency-file changes, and on
demand).

### 5. Dead Dependabot npm target — **[fixed]**

The npm ecosystem entry pointed at `/dashboard`, which no longer exists, so
npm dependencies were silently unmonitored. Repointed to `/infra/pw-poc`, the
only npm project in the repo with real dependencies.

### 6. Secret interpolated into a shell script body — **[fixed]**

`run-evals.yml` did `export HF_TOKEN=${{ secrets.HF_TOKEN }}` inside the
`run:` block. GitHub masks secrets in logs, but interpolating them into the
rendered script is fragile (quoting bugs can leak them). Moved to the step's
`env:` block.

### 7. Stale security documentation — **[fixed]**

`SECURITY.md` and `CLAUDE.md` described gates that didn't exist and omitted
ones that do. Both now list the actual enforced controls, including that
CodeQL runs via GitHub's *default setup* (repo settings — so no `codeql.yml`
must ever be added; it would conflict).

## Verified as sound (no action needed)

- **Agent tool sandbox** (`agent/tools.py`): `run_command` is disabled unless
  `SAKTHAI_SHELL_ALLOW` is set and runs with `shell=False`; `read_file` is
  restricted to cwd + `~/.sakthai` + `SAKTHAI_READ_ALLOW` with resolved-path
  containment checks.
- **Web server** (`web/server.py`): binds `127.0.0.1` by default; static-path
  canonicalisation was already hardened in PR #344.
- **Workflow permissions**: every workflow declares least-privilege
  `permissions:` (top-level `contents: read`, job-level escalation only where
  needed).
- **`pull_request_target` usage** (`greetings.yml`, `labeler.yml`): neither
  checks out or executes PR-controlled code — the safe pattern.
- **Prompt-injection handling** (`summary.yml`): untrusted issue text goes
  into the AI-inference `prompt:` input (not a shell), with an explicit
  injection warning, and the reply step passes outputs via `env:`.
- **Secrets sweep**: no hardcoded credentials in `personas/sakthai/sakthai`,
  `scripts`, `infra`, or `.github`; `.env` is gitignored and `.env.example`
  contains only empty placeholders.
- **CodeQL** default setup and **Dependabot** (uv + actions) are active on the
  repository.

## Remaining recommendations (human decisions)

1. **Branch protection on `main`** (repo settings): require the CI, Secret
   Scan, and CodeQL checks to pass before merge, and require PRs for all
   changes. Workflow gates only bite if merges are blocked on them.
2. **Pin actions to commit SHAs** rather than tags for the workflows holding
   write permissions (`auto-dependency-update.yml`, `continuous-security.yml`
   if activated). Dependabot updates SHA pins too. Tag pinning is acceptable
   for the rest.
3. **Scope `GH_PAT_FOR_ACTIONS`**: if it's a classic PAT, replace it with a
   fine-grained PAT limited to this repository with `contents` and
   `pull-requests` read/write only.
4. **Repo hygiene**: `coverage.xml` (215 KB) and `sakking-dashboard.tar.gz`
   (28 KB) are committed build artifacts. Opaque archives are exactly where
   secret scanners are weakest — prefer deleting them from the tree and
   gitignoring the patterns.
5. **Enable GitHub push protection** (Settings → Code security → Secret
   scanning → Push protection) as a second, server-side layer in front of the
   gitleaks CI gate.
