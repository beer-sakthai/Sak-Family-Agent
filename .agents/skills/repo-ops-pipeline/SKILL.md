---
name: repo-ops-pipeline
description: Automated DevOps & CI/CD pipeline skill for the Sak Family workspace. Runs full QA
  audits (Pytest, Ruff, MyPy, Bandit, Vitest), checks GitHub PR divergence and overlap,
  and builds the full-stack Next.js web dashboard.
...
---

# Repository Operations & CI/CD Pipeline

Use this skill to execute automated quality assurance, verify GitHub remote sync before opening PRs, and build the full-stack application stack.

---

## 🛠️ Available Automated Workflows

### 1. Run Automated CI/CD & QA Suite
Executes linters, security scanners, type checkers, and test suites across both the Python core package and the Next.js web dashboard:

```bash
.agents/skills/repo-ops-pipeline/scripts/qa_suite.sh
```

### 2. Run GitHub PR Preflight & Remote Sync Check
Checks remote branch divergence, lists open PRs to avoid duplicates, and checks working tree hygiene:

```bash
.agents/skills/repo-ops-pipeline/scripts/pr_preflight.sh
```

### 3. Full-Stack Web Dashboard Build
Builds the Next.js production bundle and verifies local Python environment health:

```bash
.agents/skills/repo-ops-pipeline/scripts/build_deploy.sh
```

---

## 📋 Pre-Release & Pull Request Checklist
Refer to [references/checklist.md](./references/checklist.md) for the mandatory requirements before merging or deploying changes.
