# Security Policy

This document outlines the security posture of the Sak-Family-Agent project, including our automated security measures and how to report vulnerabilities.

## Intelligent Digital Immune System

The security of this project is built on the concept of an "intelligent digital immune system." This is a proactive, self-healing approach to vulnerability management, designed to find and fix issues automatically and continuously.

This system is orchestrated by a nightly GitHub Actions workflow (`.github/workflows/continuous-security.yml`) that executes the agent's own `devsecops` skill.

### The Automated Security Workflow

The workflow consists of three main stages:

1. **Proactive Scanning**:
    - The `devsecops` skill runs a suite of static analysis tools, including `ruff` for code quality and `bandit` for security vulnerabilities, across the entire codebase.
    - This process identifies potential bugs, security hotspots, and style issues.
    - A dedicated `gitleaks` workflow (`.github/workflows/secret-scan.yml`) runs on every push and pull request to detect and prevent hardcoded secrets from being committed to the repository.

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
