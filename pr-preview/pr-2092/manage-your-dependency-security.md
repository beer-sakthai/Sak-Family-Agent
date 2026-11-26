# Managing Dependency Security in Sak-Family-Agent

**Document Version:** 1.0  
**Effective Date:** 2026-11-18  
**Owner:** SakJules · Master of Automation & CI/CD  
**Reference:** [GitHub Docs — Managing your dependency security](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security)

---

## 1. Executive Summary & Purpose

Modern software supply chains face threats ranging from vulnerable transitive dependencies and malicious packages (e.g., typosquatting, account hijacking) to restrictive open source license compliance issues.

The **House of Sak (Sak-Family-Agent)** implements a comprehensive, defense-in-depth dependency security framework based on [GitHub's Dependency Security Architecture](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security). This guide documents our multi-layered approach across our four distinct package ecosystems:

1. **Python (`uv`)**: Core agent loop, persona execution engines, CLI, MCP servers, and evaluation tools (`pyproject.toml`, `uv.lock`).
2. **Node.js / npm**: Next.js dashboard (`apps/sak_agent_dashboard`), end-to-end testing (`infra/pw-poc`), and UI specialist skills (`personas/saksee/skills/`).
3. **GitHub Actions**: Workflows in `.github/workflows/` pinned to immutable full-length commit SHAs.
4. **Docker Base Images**: Containerized execution runtimes (`Dockerfile`) pinned to immutable image digests (`sha256:...`).

---

## 2. Multi-Layer Supply Chain Architecture

Our dependency security strategy employs defensive layers across the entire software development lifecycle:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Developer / Agent PR                            │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Pre-Merge Gate: Dependency Review Action (.github/dependency-review-config.yml) │
│ • Evaluates PR dependency delta against GitHub Advisory Database (GHSA)│
│ • Enforces Open Source SPDX License Allowlist                           │
│ • Scans both runtime and development scopes                            │
│ • Comments findings directly on failing PRs                            │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Automated Upkeep: Dependabot (.github/dependabot.yml)                  │
│ • Daily & weekly version/security scans across 4 ecosystems           │
│ • 7-day cooldown on new releases (mitigates malicious releases)        │
│ • Isolated grouping to prevent O(N²) workflow re-parsing timeouts      │
│ • Automated triage & safe auto-merge workflows                         │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Continuous Post-Merge & Scheduled Audits                               │
│ • pip-audit (dependency-audit.yml): checks uv.lock against PyPA/OSV   │
│ • npm-audit (npm-audit.yml): audits JavaScript trees                   │
│ • OpenSSF Scorecard (scorecard.yml): verifies Pinned-Dependencies      │
│ • StepSecurity Harden-Runner: audits runtime network egress            │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Configuring the Dependency Review Action

We use [actions/dependency-review-action](https://github.com/actions/dependency-review-action) pinned to an immutable commit SHA (`bbc44d14a204704ccc493733616cd1e93a0321ec` / v5.0.1) in [`.github/workflows/dependency-review.yml`](../.github/workflows/dependency-review.yml).

### External Configuration File

Rather than inline configuration, our policy is centralized in [`.github/dependency-review-config.yml`](../.github/dependency-review-config.yml):

```yaml
# Severity threshold to block merge
fail-on-severity: high

# Scopes evaluated for vulnerabilities
fail-on-scopes:
  - runtime
  - development

# Allowed Open Source Licenses (SPDX License Identifiers)
allow-licenses:
  - 0BSD
  - Apache-2.0
  - BSD-2-Clause
  - BSD-3-Clause
  - CC-BY-3.0
  - CC-BY-4.0
  - CC0-1.0
  - ISC
  - LGPL-2.1
  - LGPL-3.0
  - MIT
  - MPL-2.0
  - PSF-2.0
  - Python-2.0
  - Unlicense
  - Zlib

# Exempted GitHub Advisory Database IDs (Audited Exceptions)
allow-ghsas:
  - GHSA-fc5q-39xc-vjpf
```

### Key Policy Invariants:
1. **Severity Threshold (`high`)**: Blocks any PR introducing `high` or `critical` known vulnerabilities.
2. **Scope Coverage (`runtime` & `development`)**: Catches compromised dependencies across production code and build-time testing utilities.
3. **PR Feedback (`comment-summary-in-pr: on-failure`)**: Posts an automated summary table on the PR describing flagged dependencies, CVSS scores, and remediation advice.
4. **Harden-Runner Egress**: Wrapped in StepSecurity Harden-Runner to ensure auditability of network interactions during review.

---

## 4. Open Source License Policies & SPDX Enforcement

To protect intellectual property, prevent viral copyleft infections, and ensure compatibility with open deployment, all introduced dependencies must comply with our SPDX license allowlist.

### Approved License Categories:
- **Permissive**: MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC, 0BSD, PSF-2.0, Python-2.0, Zlib, Unlicense, CC0-1.0.
- **Weak Copyleft (File-Level)**: MPL-2.0, LGPL-2.1, LGPL-3.0 (acceptable for dynamically linked or standalone libraries).
- **Prohibited Without Approval**: AGPL-1.0, AGPL-3.0, SSPL, Commons Clause, or non-commercial licenses.

Any dependency with a non-compliant or unrecognized license will fail the `Dependency Review` check, preventing automated or accidental merges.

---

## 5. Controlling Dependabot Updates (`.github/dependabot.yml`)

Our Dependabot configuration in [`.github/dependabot.yml`](../.github/dependabot.yml) follows specific optimization guidelines:

### 1. Release Cooldown (`default-days: 7`)
Newly released package versions must age for 7 days before Dependabot generates a PR.
- **Threat Mitigated**: Maintainer account takeover or sudden zero-day package poisoning. Malicious releases are typically reported and yanked by package registries within 48–72 hours.
- **Security Updates**: Dependabot automatically exempts critical security advisories from cooldown, ensuring CVE patches are opened immediately.

### 2. Ecosystem Grouping & Rate Limiting
- **Python**: Grouped by `minor` and `patch` to prevent PR noise.
- **npm**: Separated directories (`/infra/pw-poc`, `/apps/sak_agent_dashboard`, and `/personas/saksee/skills/*`) with explicit `open-pull-requests-limit` caps (3 to 5 PRs max per tree) to prevent queue exhaustion.
- **GitHub Actions**: Explicitly scoped to trusted namespaces (`actions/*`, `github/*`, `step-security/*`, `astral-sh/*`, `ossf/*`, `PyCQA/*`). Catch-all wildcards (`*`) are disallowed because grouping 115+ actions across 120+ workflows triggers an $O(N^2)$ re-parsing loop that exceeds Dependabot's 45-minute timeout.
- **Docker**: Monitored across root and infra Dockerfiles to ensure base image digests remain current.

### 3. Deliberate Version Ignores
- **Build Backend Floors**: `setuptools` is ignored because it appears only under `[build-system] requires` as a floor (`>=83.0.0`), which Dependabot's `uv` FileUpdater cannot write.
- **Upstream Transitive Constraints**: `tenacity` is ignored for `>=9.2.0` because `google-genai` imposes `<9.2.0`, avoiding unsolvable resolution failures.
- **Major Framework Migrations**: `tailwindcss` (v4 requires PostCSS migration) and `typescript` (TS 7 requires upstream `eslint-config-next` support) are pinned against breaking major bumps until intentional migration.

---

## 6. Auto-Triage Rules & Alert Prioritization

GitHub Dependabot alerts and security updates are prioritized using risk-based criteria:

| Severity | Scope | Exploit Maturity | Action Required | SLA |
|---|---|---|---|---|
| **Critical** | Runtime | Proof-of-Concept or Active | Immediate patch via Dependabot security PR or manual lockfile bump | 24 hours |
| **High** | Runtime | Known Advisory | Auto-merge eligible if tests pass; review within 48 hours | 48 hours |
| **Moderate** | Development | Theoretical | Grouped weekly Dependabot PR | 7 days |
| **Low** | Any | Informational | Grouped weekly or auto-dismissed if non-reachable | 30 days |

### Auto-Triage Presets:
- **Development Tool Alerts**: Alerts in dev dependencies for npm packages with low severity and no known exploit may be snoozed or auto-triaged if reachability analysis confirms no production path.
- **Accepted Risks**: Unpatchable upstream vulnerabilities (such as `GHSA-fc5q-39xc-vjpf` where upstream has no fix available) are documented in [`docs/scorecard-accepted-risks.md`](./scorecard-accepted-risks.md) and explicitly exempted in `.github/dependency-review-config.yml`.

---

## 7. Private & Public Registry Governance

### Public Registries (PyPI & npm)
- Packages are retrieved over HTTPS.
- Workflows running `uv sync` or `npm install` are guarded by StepSecurity Harden-Runner with explicit egress auditing to ensure network requests only reach legitimate endpoints (`pypi.org`, `files.pythonhosted.org`, `registry.npmjs.org`).

### Private & Authenticated Registries (Hugging Face Hub)
- **Token Handling**: Hub interactions use `HF_TOKEN` stored exclusively in GitHub Actions Secrets and developer local environment files (`.env`).
- **No Hardcoded Secrets**: Secret scanning push protection and CodeQL secret rules prevent accidental commit of registry credentials.

---

## 8. Pull Request Operations & Automation

We automate safe dependency updates through specialized workflows:

1. **Metadata Extraction (`dependabot/fetch-metadata`)**:
   - Workflow: [`.github/workflows/dependabot-fetch-metadata.yml`](../.github/workflows/dependabot-fetch-metadata.yml).
   - Uses `dependabot/fetch-metadata@25dd0e34f4fe68f24cc83900b1fe3fe149efef98` (pinned to v3.1.0) to extract structured outputs from Dependabot pull requests, including:
     - `steps.dependabot-metadata.outputs.update-type` (e.g. `version-update:semver-patch`, `version-update:semver-minor`, `version-update:semver-major`)
     - `steps.dependabot-metadata.outputs.dependency-names` (comma-separated list of changed dependencies)
     - `steps.dependabot-metadata.outputs.package-ecosystem` (e.g. `uv`, `npm`, `github-actions`, `docker`)
     - `steps.dependabot-metadata.outputs.alert-state` and vulnerability details.
   - Enables fine-grained conditional logic and automated label or review assignment.

2. **Auto-Merge**:
   - Workflows: [`.github/workflows/dependabot-auto-merge.yml`](../.github/workflows/dependabot-auto-merge.yml), [`.github/workflows/safe-dependabot.yml`](../.github/workflows/safe-dependabot.yml), and [`.github/workflows/enable-automerge-dependabot.yml`](../.github/workflows/enable-automerge-dependabot.yml).
   - Evaluates if the PR is authored by `dependabot[bot]`.
   - Confirms all required CI checks (`ci.yml`, `repository-security-quality.yml`) pass.
   - Merges automatically using GitHub's auto-merge facility.

3. **Operator Commands**:
   - `@dependabot rebase`: Re-aligns a stale PR against latest `main`.
   - `@dependabot recreate`: Re-generates the lockfile and update branch from scratch.
   - `@dependabot merge`: Manually approves and merges a compliant update.

---

## 9. Operational Runbooks & Troubleshooting

### Problem 1: Blocked Host or Network Failure in Dependabot
- **Symptom**: Dependabot job log shows `ERROR: Network unreachable` or connection reset when downloading metadata.
- **Cause**: Outbound firewall or temporary registry outage.
- **Remediation**:
  1. Inspect the job logs in GitHub Actions under the Dependabot update tab.
  2. Verify if the registry status is operational.
  3. Re-run the Dependabot job via GitHub UI or trigger `@dependabot recreate` on the PR.

### Problem 2: Merge Conflict in Lockfiles (`uv.lock` or `package-lock.json`)
- **Symptom**: PR indicates merge conflicts with `main`.
- **Remediation**:
  - Do NOT resolve lockfile conflicts by hand in the GitHub editor.
  - Comment `@dependabot rebase` on the PR. Dependabot will pull latest `main` and re-resolve the lockfile cleanly.
  - Alternatively, checkout the branch locally and run:
    ```bash
    git checkout dependabot/<branch>
    git merge main
    uv lock  # or npm install
    git commit -am "chore(deps): regenerate lockfile after merge"
    git push
    ```

### Problem 3: Dependency Resolution Conflict (Upper Bounds)
- **Symptom**: Dependabot reports `Dependency resolution error`.
- **Cause**: A bumped package conflicts with an existing package's version cap (e.g., Package A requires `B < 2.0`, while Dependabot tries to bump `B` to `2.1.0`).
- **Remediation**:
  - Add an entry in `.github/dependabot.yml` under `ignore` specifying `versions: [">= 2.1.0"]` until Package A updates its upper bound.

---

## 10. Audit & Verification Commands

Verify dependency security locally using the canonical validation commands:

```bash
# 1. Run pip-audit over the uv environment
uv run pip-audit

# 2. Run npm audit across the dashboard
cd apps/sak_agent_dashboard && npm audit && cd ../..

# 3. Check for scalar permissions in workflows
uv run pytest tests/test_marketplace_actions.py -k "test_marketplace_workflow_permissions_remain_strict_mappings"

# 4. Verify dependency review configuration integrity
uv run pytest tests/test_dependency_security.py
```

---

## 11. Related Documentation

- [`.github/dependency-review-config.yml`](../.github/dependency-review-config.yml) — Dependency Review Action configuration.
- [`.github/dependabot.yml`](../.github/dependabot.yml) — Dependabot multi-ecosystem configuration.
- [`docs/scorecard-accepted-risks.md`](./scorecard-accepted-risks.md) — OpenSSF Scorecard & advisory accepted risks.
- [`docs/stepsecurity-integration.md`](./stepsecurity-integration.md) — Runtime network egress guard documentation.
- [`docs/marketplace-actions-catalog.md`](./marketplace-actions-catalog.md) — Pinned Marketplace actions catalog.
