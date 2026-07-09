# Sentinel's Journal

## 2026-07-09 - [Security Scan Path Hygiene]

**Context/Vulnerability:** Contributor-facing security and CI instructions still referenced the former root-level `sakthai` package path for Bandit and related gates.

**Learning:** Security tooling documentation must point at the canonical package directory (`personas/sakthai/sakthai`) so contributors scan the code that is actually installed and exercised by CI.

**Action/Prevention:** Keep Bandit, Ruff, and mypy examples aligned with the monorepo package location whenever the workspace layout changes.
