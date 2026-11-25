# PatchFlow — Automated Patching Engine MVP

> Autonomous vulnerability remediation, code healing, and CI/CD automated patching with strict Anti-Gaming & Holdout Isolation safeguards.

---

## 🚀 Overview
**PatchFlow** is an autonomous patching engine built on the House of Sak architecture. It ingests vulnerability alerts (Dependabot, Trivy, Bandit), linter findings (Ruff, Mypy), and test failure traces (Pytest), synthesizes surgical code patches, verifies them against **Anti-Gaming & Holdout Isolation Safeguards**, and prepares hardened pull requests.

## 🛡️ Anti-Gaming & Holdout Safeguards
Every patch synthesized by PatchFlow is subject to 5 strict release gates before a PR can be emitted:
1. **Three-Way Dataset Split:** Partition test and eval cases into `dev`, `validation`, and locked `holdout`.
2. **Paired Blind Judging:** Randomized A/B evaluation against `assets/eval-judge.prompt` to eliminate verbosity and position bias.
3. **Description Token Ceiling:** Rejects tool edits or descriptions exceeding token limits (<=120 tokens) or attempting few-shot gaming.
4. **Human Approval Gate:** Explicit operator confirmation required for tool deletions, breaking schemas, or permission expansions.
5. **Snapshot Rollback:** Automatically reverts memory and workspace state via `FileSessionStore` on benchmark regressions.

## 📦 Architecture
```
services/patchflow/
├── src/
│   ├── engine.py              # Main PatchFlow orchestration engine
│   ├── scanners/              # Vulnerability & failure ingestors
│   │   ├── dependabot.py      # Dependabot / CVE alert parser
│   │   ├── linter.py          # Ruff / Mypy / Bandit finding parser
│   │   └── test_failure.py    # Pytest failure trace parser
│   ├── generator.py           # Patch synthesizer
│   ├── gate.py                # Anti-Gaming verification gate
│   └── pr_emitter.py          # SakJules PR generator (manual merge only)
├── tests/                     # Comprehensive test suite
├── config.yaml                # Engine configuration
└── SOUL.md                    # PatchFlow Persona guidelines
```
