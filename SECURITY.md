# Security Policy

This document outlines the security posture of the Sak-Family-Agent project, including our automated security measures and how to report vulnerabilities.

## Enforced security gates (GitHub Actions)

These run automatically and are the controls actually enforced on this repository:

| Gate | Workflow | What it covers |
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

This system is designed to be orchestrated by a nightly workflow that executes the agent's own `devsecops` skill. **Note:** that workflow currently lives at the repository root (`continuous-security.yml`), *outside* `.github/workflows/`, so it is **dormant** — GitHub never schedules it. Activating it is a deliberate decision (it spends LLM API credits nightly and requires the `ANTHROPIC_API_KEY` and `GH_PAT_FOR_ACTIONS` secrets); move it into `.github/workflows/` to turn it on.

### The Automated Security Workflow

The workflow consists of three main stages:

1. **Proactive Scanning**:
    - The `devsecops` skill runs a suite of static analysis tools, including `ruff` for code quality and `bandit` for security vulnerabilities, across the entire codebase.
    - This process identifies potential bugs, security hotspots, and style issues.
    - A dedicated `gitleaks` workflow (`.github/workflows/secret-scan.yml`) runs on pushes to `main` and every pull request to detect and prevent hardcoded secrets from being committed to the repository.

2. **Automated Triage and Patching**:
    - For each actionable vulnerability found, the agent triggers the `automated-vulnerability-patching` skill.
    - This skill follows a rigorous 5-step pipeline inspired by Google's automated patching systems:
        1. **Isolate**: The bug report from the scanner is captured.
        2. **Reproduce**: A new, failing test case is automatically generated to reliably reproduce the bug.
        3. **Generate Fix**: An LLM is prompted with the code, the error, and the failing test to generate a patch.
        4. **Test Fix**: The patch is applied, and the entire test suite is run to verify the fix and check for regressions.
        5. **Surface for Review**: If all tests pass, the agent automatically creates a new branch and opens a pull request with the proposed fix, including all context for human review.

3. **Human-in-the-Loop**:
    - **No code is ever merged automatically.**
    - Every AI-generated patch is presented as a pull request, where a human developer performs the final review and approval. This ensures that all changes are vetted and meet project standards.

This closed-loop system allows the agent to continuously monitor its own codebase, heal vulnerabilities, and adapt its defenses over time, significantly reducing the window of opportunity for exploits.

## Reporting a Vulnerability

We take all security reports seriously. If you discover a security vulnerability, please help us by reporting it responsibly.

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please send an email directly to **<beer-sakthai@users.noreply.github.com>**.

In your report, please include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce the issue, including any relevant code snippets or configuration.
- Any potential mitigations you have considered.

We will make every effort to acknowledge your report within 48 hours and will work with you to understand and resolve the issue as quickly as possible. We appreciate your efforts to help keep this project secure.
