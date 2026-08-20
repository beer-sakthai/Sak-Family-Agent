# PRD 0004: Autonomous CI/CD Self-Healing Doctor & Continuous Mutation Governance Daemon

## 1. Project Overview
The **Autonomous CI/CD Self-Healing Doctor & Continuous Mutation Governance Daemon** is a background diagnostic and healing engine that continuously monitors repository health, detects AST regressions, auto-repairs common lint/type anomalies, audits mutation test survival rates, and enforces zero-tolerance security gates across all 6 Sak-Family personas.

---

## 2. Problem Statement
1. **Silent AST & Type Regressions**: In large multi-agent monorepos (>1,000 files), minor syntax errors or type divergences can slip past manual reviews without a proactive diagnostic engine.
2. **Mutation Testing Gaps**: Standard line coverage does not guarantee that tests catch semantic logic mutations (e.g. inverted boolean checks, boundary drift `<` vs `<=`).
3. **Manual CI Fixing Overhead**: When CI checks fail due to deterministic formatting or missing parity files, developers are pulled away from core building to manually run repetitive fix commands.

---

## 3. Goals
- **Proactive Monorepo Doctor**: Run automated diagnostic checks across Python AST, TypeScript `tsc --noEmit`, package parity (`personas/sakthai` $\leftrightarrow$ `personas/shared`), and SQLite integrity.
- **Mutation Governance Daemon**: Inject synthetic boundary and condition mutations into agent code to measure and report mutation survival score ($\text{Kill Ratio} \ge 90\%$).
- **One-Click & Autonomous Auto-Repair**: Provide auto-healing scripts for package synchronization, Ruff lint fixes, and safe dependency resolution.
- **Executive Doctor Panel**: Expose health scores and auto-repair actions on the Next.js War Room dashboard (`/api/governance/doctor`).

---

## 4. Functional Requirements (P0)
- [ ] **Repository Doctor Engine (`personas/sakthai/sakthai/governance/doctor.py`)**:
  - Runs diagnostics: AST syntax check, Package Parity check, Security secret scan, and SQLite WAL health.
  - Generates structured diagnostic report (`HealthScore: 0-100`, list of `DiagnosticIssue` items, recommended fixes).
  - Implements `auto_heal()` for deterministic remediation (e.g. syncing parity replicas, fixing ruff lints).
- [ ] **Mutation Governance Engine (`personas/sakthai/sakthai/governance/mutation_daemon.py`)**:
  - Generates mutation diffs (operator inversion, return value replacement).
  - Calculates mutation score: $\text{Killed Mutations} / \text{Total Mutations}$.
- [ ] **Next.js Dashboard Doctor API (`apps/sak_agent_dashboard/src/app/api/governance/doctor/route.ts`)**:
  - Diagnostic scan and auto-repair triggering endpoint.
