---
name: SakTan-devsecops
category: software-development
description: Orchestrates static analysis, vulnerability scanning, and automated patching into a continuous security workflow.
version: 1.0.0
author: Gemini Code Assist
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [devsecops, security, ci, automation, self-healing, ruff, bandit]
    related_skills: [automated-vulnerability-patching, systematic-debugging, test-driven-development, github-pull-request]
---

# DevSecOps: Continuous Security Workflow

## Vision: The Digital Immune System in Action

This skill is the proactive orchestrator for the agent's "intelligent digital immune system." While `automated-vulnerability-patching` is the reactive "cure" for a known disease, this `devsecops` skill is the continuous "health monitoring" that detects diseases early.

The goal is to create a closed loop: continuously scan for weaknesses, automatically triage them, and trigger the patching pipeline to heal the codebase in near real-time.

## When to Use

This skill should be used to perform a comprehensive security and quality sweep of the codebase. It can be triggered:

- **On a schedule:** As a cron job or scheduled task to perform daily or weekly health checks.
- **In CI/CD:** On every commit or pull request to prevent new issues from being merged.
- **Manually:** When a developer or agent wants to initiate a full security audit.

## The DevSecOps Workflow

This is a sequential process. Each step feeds into the next.

---

### 1. Proactive Scanning

The first step is to run a battery of static analysis tools to identify potential linting errors, code quality issues, and security vulnerabilities.

**Action:**

1. Run `ruff check .` to find linting and style issues.
2. Run `bandit -r . -c pyproject.toml` to find common security vulnerabilities in Python code.
3. Collect and consolidate all findings from the tools into a single list. For each finding, preserve the tool name, error code/message, file path, and line number.

**Goal:** Generate a comprehensive list of potential issues across the entire codebase.

---

### 2. Triage and Prioritization

Not all findings are critical or even real. This step involves using the agent's intelligence to filter out noise and identify actionable issues.

**Action:**

1. For each finding from Step 1, perform a quick analysis.
2. Use `read_file` to examine the code at the specified file and line number.
3. Make a judgment call:
    - Is this a clear bug or vulnerability that needs a fix? (e.g., SQL injection, uninitialized variable).
    - Is this a style issue that can be auto-formatted? (e.g., line too long, incorrect import order).
    - Is this likely a false positive or a non-critical issue that can be ignored for now?
4. Create a prioritized list of actionable bugs and vulnerabilities.

**Goal:** Filter the raw tool output into a high-confidence list of issues that require a code change.

---

### 3. Automated Remediation

For each actionable issue identified in Step 2, trigger the appropriate remediation skill.

**Action:**

1. **For security vulnerabilities and bugs:**
    - Invoke the `automated-vulnerability-patching` skill.
    - Provide the tool report (error, file, line number) as the input.
    - The patching skill will take over: create a failing test, generate a fix, test it, and create a pull request.
2. **For style and linting issues:**
    - Run `ruff format .` and `ruff check . --fix` to automatically fix what can be fixed safely.
    - For remaining issues, decide if they warrant a manual fix or can be added to an ignore list.

**Goal:** Systematically address each identified issue using the most appropriate automated tool, culminating in pull requests for human review. This closes the loop on the "find, fix, and verify" cycle.

---
