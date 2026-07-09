# Sentinel's Journal

## 2026-07-09 - [Security Scan Path Hygiene]

**Context/Vulnerability:** Contributor-facing security and CI instructions still referenced the former root-level `sakthai` package path for Bandit and related gates.

**Learning:** Security tooling documentation must point at the canonical package directory (`personas/sakthai/sakthai`) so contributors scan the code that is actually installed and exercised by CI.

**Action/Prevention:** Keep Bandit, Ruff, and mypy examples aligned with the monorepo package location whenever the workspace layout changes.

## 2026-07-09 - [Scoped Typed Security Gates]

**Context/Vulnerability:** Moving the CI guidance to the real package path exposed strict mypy failures that had been hidden by the old path, including untyped PyYAML imports.

**Learning:** CI path corrections can turn previously skipped checks into active gates; when a runtime library lacks usable stubs in the locked environment, any exception should be scoped to the exact importing modules instead of weakening the whole type gate.

**Action/Prevention:** Prefer real type stubs when the lock can be updated safely; otherwise use targeted mypy overrides for the specific modules importing the untyped runtime library.
