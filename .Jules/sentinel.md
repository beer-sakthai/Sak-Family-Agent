# Sentinel's Journal

## 2026-07-09 - [Security Scan Path Hygiene]

**Context/Vulnerability:** Contributor-facing security and CI instructions still referenced the former root-level `sakthai` package path for Bandit and related gates.

**Learning:** Security tooling documentation must point at the canonical package directory (`personas/sakthai/sakthai`) so contributors scan the code that is actually installed and exercised by CI.

**Action/Prevention:** Keep Bandit, Ruff, and mypy examples aligned with the monorepo package location whenever the workspace layout changes.

## 2026-07-09 - [Typed Security Gate Dependencies]

**Context/Vulnerability:** Moving the CI guidance to the real package path exposed strict mypy failures that had been hidden by the old path, including untyped PyYAML imports.

**Learning:** CI path corrections can turn previously skipped checks into active gates; the dev dependency set must include required type stubs so the strict gate is reproducible.

**Action/Prevention:** Keep type stubs for runtime libraries in the `dev` extra whenever strict mypy checks import those libraries.
