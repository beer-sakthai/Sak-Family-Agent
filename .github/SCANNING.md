# Code Scanning Ecosystem

This repository uses **eight security and code quality scanners** running independently in CI/CD. This guide explains each scanner's purpose, scope, and configuration.

---

## Scanning Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│              GitHub Code Scanning Dashboard                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  CodeQL         SonarCloud        Scorecard                 │
│  (Advanced)     (SQ analysis)     (Supply-chain)             │
│  ✓ Python       ✓ Python          ✓ Security policy         │
│  ✓ JavaScript   ✓ JavaScript      ✓ Branch protection       │
│  ✓ Actions      ✓ Node.js         ✓ Token permissions       │
│                 ✓ CSS/YAML        ✓ Signed releases         │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│  Bandit      ESLint      Pylint      OSSAR                   │
│  (Python     (JS/TS      (Python     (MSDO)                  │
│   security)  linting)    quality)                            │
│  • Runs in   • Dashboard • Runs in   • Runs on              │
│    CI only     only      CI only      Windows               │
│  • Config in • Config in • Config in • Config via           │
│    tool.bandit eslint    tool.pylint  default               │
│              config.mjs  in pyproject |                      │
│                          .toml        │                      │
│                                       └─ Does NOT upload    │
│                                          to code scanning    │
└─────────────────────────────────────────────────────────────┘
```

---

## Scanner Details

### 1. **CodeQL** — GitHub's Semantic Analysis (Advanced Setup)

**Purpose:** Semantic code analysis catching logic errors, security vulnerabilities, and data-flow issues.

**Languages Analyzed:**
- Python (comprehensive)
- JavaScript/TypeScript (apps/sak_agent_dashboard)
- GitHub Actions (workflow files in .github/)

**Configuration:**
- **Workflow:** `.github/workflows/codeql.yml`
- **Config File:** `.github/codeql/codeql-config.yml`
- **Documentation:** `.github/codeql/README.md`
- **Local Testing:** `scripts/codeql_local.sh`

**Query Suites:**
- `actions`: `security-extended` (workflow-security rules)
- `python`: `default` suite (240+ first-party alerts backlog)
- `javascript-typescript`: `default` suite

**Scope (Excluded Paths):**
- `personas/*/skills/**` — Vendored skill reference scripts
- `library/**` — Curated third-party skill library
- `sakthai-chat-cli/**` — Folded-in separate repository copy
- `tests/**` — Test suite (injection patterns are intentional)
- Build output: `**/node_modules`, `**/dist`, `**/build`, `**/.venv`

**When It Runs:** Push & PR to `main`, weekly Sunday  
**Upload To:** GitHub Code Scanning dashboard  
**Setup Type:** Advanced (default setup is OFF — required for `config-file:`)

**Key Insight:** This repository deliberately uses *advanced setup* (not default setup) so that `.github/codeql/codeql-config.yml` can be loaded by path. Without this, 545 of 788 alerts would be in vendored trees this repository doesn't own.

---

### 2. **SonarCloud** — SonarSource Code Quality Analysis

**Purpose:** Comprehensive code quality, security hotspots, and maintainability metrics. Integrates with GitHub PR decoration.

**Languages Analyzed:**
- Python
- JavaScript/TypeScript
- CSS, YAML, and 25+ others

**Configuration:**
- **Workflow:** `.github/workflows/sonarcloud.yml`
- **Project Config:** `sonar-project.properties` (repository root)
- **Key:** `beer-sakthai_Sak-Family-Agent`
- **Organization:** `beer-sakthai`
- **Token Required:** `SONAR_TOKEN` (GitHub secret)

**Scope (Excluded Paths):** Matches CodeQL for consistency
- Vendored skill directories
- `library/`, `sakthai-chat-cli/`, `tests/`
- Build output

**When It Runs:** Push & PR to `main`, manual dispatch  
**Upload To:** GitHub Code Scanning dashboard  
**PR Integration:** Automatically decorates PR diffs with quality issues

**Note:** Requires `SONAR_TOKEN` secret in repository settings to run. Without it, the job skips silently (by design — SonarCloud is optional for forks).

---

### 3. **Scorecard** — OSSF Supply-Chain Security Assessment

**Purpose:** Measures repository security best practices (branch protection, signed releases, token permissions, etc.). Results push to the OpenSSF REST API.

**Configuration:**
- **Workflow:** `.github/workflows/scorecard.yml`
- **Config File:** `.scorecard.yml` (repository root)
- **Publishes Badge:** Yes (public repository)
- **Publishing:** Enabled for scorecard.dev ranking

**Checks Performed:**
- Branch Protection (rule enforcement)
- Signed Releases (cryptographic verification)
- Token Permissions (least-privilege principle)
- Dependency Management (pinned versions)
- Binary Artifacts (no untraceable binaries)
- Dangerous Workflows (expression injection, secrets exposure)
- License Detection
- Maintained Status

**When It Runs:**
- On branch protection rule changes
- Weekly Thursday
- Push to `main`

**Upload To:** GitHub Code Scanning dashboard + OpenSSF API  
**Scope:** Repository-wide (no exclusions) — assesses org practices, not code

---

### 4. **Bandit** — Python Security Linter

**Purpose:** Static security analysis for Python code. Identifies hardcoded credentials, insecure function calls, SQL injection patterns, etc.

**Configuration:**
- **Workflow:** `.github/workflows/bandit.yml`
- **Tool Config:** `pyproject.toml` → `[tool.bandit]`
- **Configuration File:** `.github/bandit-requirements.lock` (transitive deps)
- **Lock File:** `uv.lock`

**Excluded Issues:**
- `B101` (assert_used — testing-specific)
- `B404`, `B603`, `B607` (subprocess — intentional in agent design)
- Tests: Bandit runs only over `personas/sakthai/sakthai` and `tests/`, skipping test utility functions

**When It Runs:** Push & PR to `main`, weekly Wednesday  
**Upload To:** GitHub Code Scanning dashboard  
**Publish:** Yes (does not gate CI — CodeQL is the gate)

**Note:** Uses the same scope as CodeQL where applicable, but focuses on Python-specific patterns.

---

### 5. **ESLint** — JavaScript/TypeScript Linting

**Purpose:** JavaScript code quality, style consistency, and best-practice enforcement.

**Configuration:**
- **Workflow:** `.github/workflows/eslint.yml`
- **Config File:** `apps/sak_agent_dashboard/eslint.config.mjs` (flat config)
- **Includes:** React Compiler rules (`react-hooks/*`)
- **Triggered By:** Changes under `apps/sak_agent_dashboard/`, weekly Sunday

**When It Runs:** Push & PR touching dashboard, weekly Sunday  
**Upload To:** GitHub Code Scanning dashboard  
**Category:** `eslint-dashboard` (SARIF)  
**Note:** Dashboard is the only Node.js subproject; ESLint is scoped to it.

---

### 6. **Pylint** — Python Code Quality Analyzer

**Purpose:** Python code quality, style, and potential bugs. More conservative than Bandit, less semantic than CodeQL.

**Configuration:**
- **Workflow:** `.github/workflows/pylint.yml`
- **Tool Config:** `pyproject.toml` (implicit; no explicit `[tool.pylint]` section yet)
- **Scope:** `personas/sakthai/sakthai` + `tests`

**When It Runs:** Push & PR to `main`  
**Upload To:** GitHub Code Scanning (via SARIF) — *does not gate CI*  
**Note:** Runs alongside `ci.yml` for broader coverage.

---

### 7. **OSSAR** — Microsoft Security DevOps Analysis

**Purpose:** Microsoft's multi-tool security analysis (MSDO). Wraps multiple Microsoft security scanners.

**Configuration:**
- **Workflow:** `.github/workflows/ossar.yml`
- **Platform:** `windows-latest` (required by `github/ossar-action`)
- **Tools Included:** Multiple Microsoft security linters and scanners
- **Long Paths:** Configured with `git config --global core.longpaths true` (required for vendored M365 SDK paths > 260 chars)
- **Directory Renames:** Skill directories renamed from `stitch::*` to `stitch-*` to avoid invalid NTFS path characters

**When It Runs:** Push & PR to `main`, weekly Monday  
**Upload To:** GitHub Code Scanning dashboard  
**Note:** Windows-only constraints required repository-level path length management (see CLAUDE.md).

---

### 8. **Continuous Security / Security Audit** (Gemini-based Agent)

**Purpose:** Nightly security posture assessment combining Bandit findings, pip-audit results, and guardrail suite checks.

**Configuration:**
- **Workflow:** `.github/workflows/continuous-security.yml` (hollow — missing `ANTHROPIC_API_KEY`)
- **Replacement:** `.github/workflows/security-audit.md` (gh-aw Gemini workflow)
- **Actual Runs:** Weekly Thursday via `security-audit.md`

**When It Runs:**
- Weekly Thursday (via `security-audit.md`, which compiles to `.lock.yml`)
- Manual dispatch

**Output:** Issue (triages findings, no PR)  
**Note:** `continuous-security.yml` is a skeleton that was re-added but never revived — `security-audit.md` is the live agent.

---

## Configuration Files Summary

| File | Purpose | Required? | Location |
|------|---------|-----------|----------|
| `.github/codeql/codeql-config.yml` | CodeQL scope (Python, JS, Actions) | ✅ Yes | Path referenced in workflow |
| `.github/codeql/README.md` | CodeQL documentation & local setup | ✅ Yes | Explains advanced setup rationale |
| `sonar-project.properties` | SonarCloud project configuration | ✅ Yes | Repository root |
| `.scorecard.yml` | Scorecard checks configuration | ✅ Yes | Repository root |
| `pyproject.toml` → `[tool.bandit]` | Bandit Python security config | ✅ Yes | Project config file |
| `pyproject.toml` → `[tool.pylint]` | Pylint config (can be extended) | ⚠️  Optional | Project config file |
| `apps/sak_agent_dashboard/eslint.config.mjs` | ESLint JS/TS config | ✅ Yes | Dashboard directory |
| `.github/bandit-requirements.lock` | Bandit transitive dependencies | ✅ Yes | Referenced by workflow |

---

## Scope Alignment

All scanners exclude the same tree categories for consistency:

**Always Excluded:**
- `personas/*/skills/**` — Vendored skill reference scripts (not owned by this repo)
- `library/**` — Curated third-party skill library (pre-dating `Sak-` naming convention)
- `sakthai-chat-cli/**` — Folded-in copy of separate repository (its own CI/CD history)
- `tests/**` — Test suite (path injection patterns, subprocess calls, etc. are intentional)

**Why:** ~545 of the 788 CodeQL alerts on 2026-08-18 lived in these trees. Excluding them makes the remaining ~243 first-party findings legible.

---

## Running Scanners Locally

### CodeQL
```bash
scripts/codeql_local.sh                # All three languages
scripts/codeql_local.sh python         # Single language
scripts/codeql_local.sh --check        # Is CLI usable?
scripts/codeql_local.sh --rebuild      # Clear caches, rebuild
```

See `.github/codeql/README.md` for full details and bundle requirements.

### Bandit
```bash
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai
```

### Pylint
```bash
uv run pylint personas/sakthai/sakthai tests
```

### ESLint (Dashboard)
```bash
cd apps/sak_agent_dashboard
pnpm lint
```

### Mypy (Type Checking)
```bash
uv run mypy personas/sakthai/sakthai  # Strict mode
```

### Ruff (Format + Lint)
```bash
uv run ruff check personas/sakthai/sakthai tests
uv run ruff format --check personas/sakthai/sakthai tests
```

---

## CI Gate vs. Publish

### Gates CI (Required to Pass)
- **CodeQL** (via `codeql.yml` → `ci.yml` dependency, implicitly)
- **Ruff Lint** (via `ci.yml`)
- **Mypy Type Check** (via `ci.yml`)
- **Pytest** (via `ci.yml`, includes coverage floor at 96%)

### Does NOT Gate (Report Only)
- SonarCloud — Decorates PR, reports on `main`, but doesn't block merge
- Scorecard — Publishes to OpenSSF, updates badge
- Bandit — Uploads to code scanning, does not gate
- Pylint — Uploads to code scanning, does not gate
- ESLint — Uploads to code scanning, does not gate
- OSSAR — Uploads to code scanning, does not gate

**Rationale:** Multiple independent tools provide breadth; one strict gate (`ci.yml` with CodeQL, ruff, mypy) ensures the core pipeline stays green.

---

## Troubleshooting

### "Configuration not found" in Code Scanning

This appears when a scanner cannot locate its config file:
- **SonarCloud:** Check `SONAR_TOKEN` secret exists and `sonar-project.properties` is in repository root
- **Scorecard:** Check `.scorecard.yml` is in repository root and valid YAML
- **CodeQL:** Check `.github/codeql/codeql-config.yml` path matches workflow `config-file:` value

### Workflow Skipped

- **SonarCloud:** Runs only if `SONAR_TOKEN` is set (skips silently otherwise)
- **Scorecard:** Runs only on `main` branch for publish, or scheduled events
- **ESLint:** Runs only when changes touch `apps/sak_agent_dashboard/**`

### Local CodeQL Fails

- Requires CodeQL **bundle**, not just CLI (bundle includes query packs)
- Download from [codeql-action releases](https://github.com/github/codeql-action/releases)
- Pass `--codescanning-config` to honor `paths-ignore` (else see all 545 vendored alerts)

---

## Related Documentation

- **Security Architecture:** [`docs/SECURITY.md`](../docs/SECURITY.md)
- **Security Hardening:** [`docs/security-hardening.md`](../docs/security-hardening.md)
- **CodeQL Details:** [`.github/codeql/README.md`](./codeql/README.md)
- **GitHub Settings:** [`.github/GITHUB_SETTINGS.md`](.github/GITHUB_SETTINGS.md) (if present)
- **Workflow Hygiene:** [`tests/test_workflow_hygiene.py`](../tests/test_workflow_hygiene.py)

---

## Key Takeaways

1. **CodeQL is the gate** — uses advanced setup with explicit scope configuration
2. **Scope is consistent** — all scanners exclude vendored/test/library trees
3. **Configuration is explicit** — no "found nothing" defaults; each tool has a real config file
4. **Breadth over depth** — 8 independent tools provide coverage; one gate keeps the pipeline stable
5. **Documentation is the defense** — this file explains *why* each scanner exists and what it does
