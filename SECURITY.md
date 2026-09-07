# Security Policy

This document outlines the security posture of the Sak-Family-Agent project, including our automated security measures and how to report vulnerabilities.

## Enforced security gates (GitHub Actions)

These run automatically and are the controls actually enforced on this repository:

| Gate | Where it's defined | What it covers |
|---|---|---|
| Lint + static analysis | `ci.yml` | `ruff`, strict `mypy`, and `bandit` over the core `sakthai` package on every push/PR to `main` |
| Secret scanning | `secret-scan.yml` | `gitleaks` over the full git history (config: `.gitleaks.toml`) on pushes to `main` and every pull request |
| Dependency vulnerability audit | `dependency-audit.yml` | `pip-audit` over the locked dependency set (`uv.lock`) — weekly, on dependency changes, and on demand |
| Code scanning (SAST) | CodeQL default setup | GitHub CodeQL analysis, managed in repository settings (no workflow file — do not add a conflicting `codeql.yml`) |
| Multi-tool SAST | `ossar.yml` | Microsoft Security DevOps (MSDO), results uploaded to the Security tab |
| Quality/security hotspots | `sonarcloud.yml`, `pylint.yml` | SonarCloud analysis and pylint |
| Dependency updates | `.github/dependabot.yml` | Weekly update PRs for Python (uv), npm (`infra/pw-poc`), and pinned GitHub Actions versions |

## Intelligent Digital Immune System

Beyond the enforced gates above, the project's longer-term security concept is an "intelligent digital immune system" — a proactive, self-healing approach to vulnerability management, designed to find and fix issues automatically and continuously.

This system is orchestrated by a nightly workflow (`.github/workflows/continuous-security.yml`) that runs the agent with security-focused skills (`SakThai-coding-security`, `sakthai-security-hardening`). **Note:** an earlier version of this doc claimed that workflow lived only at the repository root, outside `.github/workflows/`, and was therefore dormant. That was inaccurate — an identical copy has been present under `.github/workflows/` (and therefore live, spending `ANTHROPIC_API_KEY`/`GH_PAT_FOR_ACTIONS` nightly) since it was first added; the misleading root-level duplicate has been removed. It also referenced a skill name (`devsecops`) that never resolved against this repo's skill roots, so it ran nightly without any security-skill guidance loaded until that was fixed — see the workflow file's own comments for the full story.

### The Automated Security Workflow

The workflow currently covers the first of three intended stages:

1. **Proactive Scanning** (implemented):
    - The agent runs a suite of static analysis tools, including `ruff` for code quality and `bandit` for security vulnerabilities, across the codebase.
    - This process identifies potential bugs, security hotspots, and style issues.
    - A dedicated `gitleaks` workflow (`.github/workflows/secret-scan.yml`) runs on pushes to `main` and every pull request to detect and prevent hardcoded secrets from being committed to the repository.

2. **Automated Triage and Patching** (aspirational — not yet implemented):
    - The intent is for the agent to trigger an `automated-vulnerability-patching` skill for each actionable finding, following a 5-step isolate/reproduce/generate-fix/test-fix/surface-for-review pipeline.
    - No skill by that name currently exists in this repository (there is no `automated-vulnerability-patching` skill under any persona or the shared library), so this stage does not run yet. Until it's authored, the nightly scan surfaces findings in the run log rather than opening patch PRs automatically.

3. **Human-in-the-Loop**:
    - **No code is ever merged automatically.**
    - Any AI-generated patch would be presented as a pull request, where a human developer performs the final review and approval. This ensures that all changes are vetted and meet project standards.

The long-term goal remains a closed-loop system where the agent continuously monitors its own codebase, heals vulnerabilities, and adapts its defenses over time — stage 1 runs today, stages 2–3 are the roadmap.

## Reporting a Vulnerability

We take all security reports seriously. If you discover a security vulnerability, please help us by reporting it responsibly.

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please send an email directly to **<beer-sakthai@users.noreply.github.com>**.

In your report, please include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce the issue, including any relevant code snippets or configuration.
- Any potential mitigations you have considered.

We will make every effort to acknowledge your report within 48 hours and will work with you to understand and resolve the issue as quickly as possible. We appreciate your efforts to help keep this project secure.
