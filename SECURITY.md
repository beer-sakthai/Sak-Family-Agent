# Security Policy

This document outlines the security posture of the Sak-Family-Agent project, including our automated security measures and how to report vulnerabilities.

## 🚨 Report a Vulnerability

**Do not report security vulnerabilities through public GitHub issues.**

⚡ **Send an email directly to:** **[beer-sakthai@users.noreply.github.com](mailto:beer-sakthai@users.noreply.github.com)**

Include:
- Description of the vulnerability and its potential impact
- Steps to reproduce (with code snippets if relevant)
- Any mitigations you've considered

**Response time:** We will acknowledge your report within **48 hours** and work with you to resolve it as quickly as possible.

---

## 🔒 Quick Reference: Security Checks

Before submitting code or opening a PR, run these local verification commands:

```bash
# Full quality bar (runs in CI)
uv sync --all-extras                                          # Install all deps
uv run ruff check personas/sakthai/sakthai tests               # ✨ Lint
uv run ruff format --check personas/sakthai/sakthai tests      # 🎨 Format
uv run mypy personas/sakthai/sakthai                           # 🔤 Type safety (strict)
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai    # 🛡️ Security scan
uv run pytest tests/ -m "not integration" -q                   # 🧪 Tests (coverage ≥96%)
```

**Red run in CI?** See [docs/self-healing-ci.md](docs/self-healing-ci.md) for how the automated healing workflow diagnoses and patches failures.

---

## Enforced security gates (GitHub Actions)

These run automatically and are the controls actually enforced on this repository:

| Gate | Where it's defined | What it covers |
|---|---|---|
| Lint + static analysis | `ci.yml` | `ruff`, strict `mypy`, and `bandit` over the core `sakthai` package on every push/PR to `main` |
| Secret scanning | `secret-scan.yml` | `gitleaks` over the full git history (config: `.gitleaks.toml`) on pushes to `main` and every pull request |
| Dependency vulnerability audit | `dependency-audit.yml` | `pip-audit` over the locked dependency set (`uv.lock`) — weekly, on dependency changes, and on demand |
| Code scanning (SAST) | `codeql.yml` | GitHub CodeQL **advanced** setup over `actions`, `javascript-typescript` and `python`, scoped by `.github/codeql/codeql-config.yml` via `config-file:`. Default setup is **off**: the two cannot coexist, so do not re-enable it without deleting the workflow. See `docs/code-scanning-sweep-2026-08-18.md` |
| Multi-tool SAST | `ossar.yml` | Microsoft Security DevOps (MSDO), results uploaded to the Security tab |
| Dependency updates | `.github/dependabot.yml` | Daily, grouped update PRs across five ecosystems (`uv`, `pip`, `npm`, `docker`, `github-actions`) covering 22 directories. The **only** source of automated dependency bumps — `auto-dependency-update.yml` duplicated it and was removed on 2026-08-18 after failing all 22 of its runs — then restored by a `[StepSecurity]` commit, still failing, and removed again on 2026-08-20. `tests/test_workflow_hygiene.py` now fails CI if it returns. Shape and rationale in `docs/configuring-multi-ecosystem-updates.md`; `tests/test_dependabot_config.py` fails CI if a manifest goes uncovered |
| Dependency alerts | Repository settings | Dependabot alerts + security updates, enabled per `docs/dependabot-setup.md` (or `scripts/enable_dependabot.sh`). Not configurable from `dependabot.yml` |
| Internal advisory report | `innersource-advisories.yml` | Daily read of the open Dependabot alert list into a standing issue, so consumers see exposure without Security-tab access. Policy in `.github/INNERSOURCE.md` |
| SARIF publishers | `bandit.yml`, `eslint.yml` | Bandit over first-party Python and ESLint over `apps/sak_agent_dashboard`, each uploading to the Security tab under its own category. Neither gates — `ci.yml` and `subprojects.yml` are the gates |
| Quality/security hotspots | `sonarcloud.yml`, `pylint.yml` | SonarCloud analysis and pylint |
| Supply-chain posture | `scorecard.yml`, `OSPS.yml` | OpenSSF Scorecard and the Open Source Project Security baseline, both → SARIF / artifacts |
| Workflow Action Pinning | All `.github/workflows/*.yml` | StepSecurity immutable commit SHA pinning with least-privilege permissions and top-level concurrency isolation |

## Runtime Defense & Deterministic Guardrails

In addition to CI/CD gating, the core runtime implements zero-tolerance deterministic security controls:

1. **Path Traversal & Control Character Rejection**:
   - `_resolve_and_validate_path` evaluates all filesystem queries and tool arguments across CLI commands, MCP tools, and workflow executors.
   - Any path string containing ASCII control characters (`\x00-\x1f\x7f`) is immediately rejected with a `ValueError`.
   - Redundant or malformed prefix traversal schemes (e.g. `@@`) are normalized and sanitized before root resolution.

2. **Cryptographic Key Hashing & PBKDF2**:
   - API keys and tokens are hashed using PBKDF2-HMAC-SHA256 with cryptographically secure random salts.
   - Plaintext keys are never stored in durable memory (`memory.db`) or logs.

3. **Command Injection & Execution Sandboxing**:
   - Shell command execution is subject to an AST denylist and strict token parsing (`personas/sakthai/sakthai/agent/guardrails.py`).
   - Untrusted agent sessions can be executed inside isolated Docker containers (`sandbox.py`) with zero host network access.


## Intelligent Digital Immune System

Beyond the enforced gates above, the project's longer-term security concept is an "intelligent digital immune system" — a proactive, self-healing approach to vulnerability management, designed to find and fix issues automatically and continuously.

This system is orchestrated by `.github/workflows/security-audit.md`, a weekly gh-aw agentic workflow running on `engine: gemini`. A pre-agent step runs the repository's own scanners — bandit under `[tool.bandit]`, pip-audit over the exported lock, and the guardrail/sentinel/persona-parity test files — and the agent triages that output against the prevention table in [`docs/security-hardening.md`](docs/security-hardening.md), opening at most one issue and only when something is actionable. It audits and never edits: no writes, no pull requests, and nothing under `.github/` or the guardrail subsystem.

**Why it is not the nightly Anthropic-driven scan this section used to describe.** That workflow (`continuous-security.yml`) was removed on 2026-08-18, **restored by a `[StepSecurity]` commit, and is on `main` again as of 2026-08-20 — still hollow.** It had been running nightly and doing nothing: the repository has no `ANTHROPIC_API_KEY` configured, so its agent step was skipped on every run while the job still reported success — verified in run `32093238703`, where *Run DevSecOps Skill* is `skipped` and *Explain why the scan was skipped* is `success`. Two earlier corrections to this same paragraph — about where the file lived, and about a `--with-skills` name that never resolved — are the reason the replacement runs on the engine this repository's other agentic workflows already have credentials for, and reports through an issue rather than a run log nobody reads.

### The Automated Security Workflow

The workflow currently covers the first of three intended stages:

1. **Proactive Scanning** (implemented):
    - The agent runs a suite of static analysis tools, including `ruff` for code quality and `bandit` for security vulnerabilities, across the codebase.
    - This process identifies potential bugs, security hotspots, and style issues.
    - A dedicated `gitleaks` workflow (`.github/workflows/secret-scan.yml`) runs on pushes to `main` and every pull request to detect and prevent hardcoded secrets from being committed to the repository.

2. **Automated Triage** (implemented for CI failures, not for vulnerabilities):
    - `security-audit.md` triages scanner output into a single issue, cross-checked against the prevention table in `docs/security-hardening.md` so a known-and-accepted finding is not re-raised as new. It proposes; it does not patch.
    - The one place automated patching does run is `self-healing-ci.yml` / `sakthai heal`, and only for CI failures — with a deterministic safety gate whose protected-path list covers `.github/`, dependency pins, the security subsystem and the `selfheal` package itself. See [`docs/self-healing-ci.md`](docs/self-healing-ci.md).
    - An `automated-vulnerability-patching` skill remains unwritten; no skill by that name exists under any persona or the shared library.

3. **Human-in-the-Loop**:
    - **No code is ever merged automatically.**
    - Any AI-generated patch would be presented as a pull request, where a human developer performs the final review and approval. This ensures that all changes are vetted and meet project standards.

The long-term goal remains a closed-loop system where the agent continuously monitors its own codebase, heals vulnerabilities, and adapts its defenses over time — stage 1 runs today, stage 2 triages, and automated patching stays scoped to CI failures behind a safety gate.

## Reporting a Vulnerability

We take all security reports seriously. If you discover a security vulnerability, please help us by reporting it responsibly.

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please send an email directly to **<beer-sakthai@users.noreply.github.com>**.

In your report, please include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce the issue, including any relevant code snippets or configuration.
- Any potential mitigations you have considered.

We will make every effort to acknowledge your report within 48 hours and will work with you to understand and resolve the issue as quickly as possible. We appreciate your efforts to help keep this project secure.
