# CI/CD Supply-Chain Security Review — Sak-Family-Agent

**Question:** For a small team running GitHub Actions on a Node + Python monorepo that already has CodeQL and workflow-hygiene tests, should we adopt StepSecurity Harden-Runner (egress allowlisting, anomalous outbound-call detection, imposter-commit detection, artifact attestations, secrets-in-build-log detection) on top of GitHub-native controls — or are the free GitHub-native controls sufficient? Which controls give the best security-per-effort for a team that cannot staff a dedicated platform-security function, and what is the minimum viable set to ship first?

**Method:** Deep-research workflow — 5 parallel search angles, 21 sources fetched, 98 claims extracted, 25 adversarially verified (20 confirmed, 5 refuted), 11 findings after synthesis. Current as of 2026-08-18.

**Research run stats:** 103 agents · 335 tool uses · ~4.76M tokens · ~33 min.

---

## Recommendation: Adopt-subset, sequenced

Ship the **free GitHub-native baseline first** (largely already in place in this repo), then add **Harden-Runner in audit mode** on public-facing/reusable workflows where runtime egress monitoring adds real marginal value. **Defer Enterprise** until private-repo egress *enforcement* (block mode), workflow run policies, or least-privilege `GITHUB_TOKEN` recommendations justify the per-dev cost.

**Single most material caveat:** Harden-Runner's free Community tier is **public-repos-on-GitHub-hosted-runners ONLY.** If this repo is (or goes) private, the free tier does not apply and the decision becomes *pay $16/contributing-dev/mo, or rely on GitHub-native controls only.*

> **Repo-specific note (verified 2026-08-18):** This repo has *already* adopted Harden-Runner at **Enterprise Policy Store tier** across 25/29 workflows (see "Where this repo already stands"). The adopt-subset recommendation above is the general research conclusion for a GitHub-native-only team; for this repo, the adoption decision is already made and executed. The remaining value of this report here is the background decision-support: tier economics, the public/private attestation gap, scope clarity on action-vs-platform, and the value-over-baseline open question — not a rollout plan.

### Where this repo already stands (verified 2026-08-18 by reading workflow contents)

This repo is **not** the underserved "GitHub-native only" case the research question assumed — it is a **mature StepSecurity Enterprise user**. Verified state of `.github/workflows/`:

- **Harden-Runner is already the first step of 25 of 29 YAML workflows** (`ci.yml`, `codeql.yml`, `eslint.yml`, `bandit.yml`, `subprojects.yml`, `scorecard.yml`, `secret-scan.yml`, `continuous-security.yml`, …), SHA-pinned to `step-security/harden-runner@05e31511f85b41b11d1cf0ef85d0992719546e2c` (v2.21.0).
- **All 25 use `use-policy-store: true`** with `api-key: ${{ secrets.STEP_SECURITY_API_KEY }}` — the **Enterprise Policy Store** mode (backend-hosted allowlist), which is *more* advanced than the audit-mode default the research recommends as a starting point. This repo is already past the "adopt-subset" decision the report frames.
- The **4 workflows without Harden-Runner are all `.lock.yml`** files — compiled gh-aw agentic workflows (`ci-doctor`, `maintain-agents-md`, `maintain-docs`, `release`), not hand-authored YAML. Whether those compiled agentic jobs need egress control is the one genuinely open coverage question (see Open Questions).
- The GitHub-native baseline is also in place: `codeql.yml`, `scorecard.yml`, `dependency-review.yml`, `secret-scan.yml`, `continuous-security.yml`, `ossar.yml`, `sonarcloud.yml`, plus `tests/test_workflow_hygiene.py` enforcing SHA-pinning (40-char SHA rule) and top-level `permissions:` on every workflow.

**Net:** for this repo, the research below is decision-support background (tier economics, the public-vs-private attestation gap, scope clarity on what the action vs. the platform delivers, the value-over-baseline open question) rather than an adoption roadmap — the adoption already happened at Enterprise tier. The "add Harden-Runner in audit mode" recommendation applies to *other* repos that are still GitHub-native-only; it is moot here.

---

## Decision matrix

| Dimension | GitHub-native (free) | Harden-Runner Community (free) | Harden-Runner Enterprise ($16/dev/mo) |
|---|---|---|---|
| Cost | $0 | $0 — **public repos only** | $16/contributing-dev/mo (14-day trial) |
| Egress control on hosted runners | ❌ none (unrestricted outbound) | ✅ audit + block (DNS/HTTPS/L3-4); block Linux-only, Win/mac audit-only | ✅ same + workflow run policies, Checks pass/fail |
| SHA-pinning / action blocklisting | ✅ `!`-prefix blocklist (GA Aug 2025); pinning *permitted*, not *enforced* — your `test_workflow_hygiene.py` is what enforces it | — | — |
| Least-privilege `GITHUB_TOKEN` | ✅ `permissions: {}` workflow-level + job grants | — | ✅ min-permission recommendations |
| Dependabot / secret scanning | ✅ free | — | — |
| SLSA artifact attestations | ✅ free for **public** repos; ❌ private needs GitHub Enterprise Cloud | — | — (separate cost decision) |
| Imposter-commit / secrets-in-log / source-overwrite detection | ❌ | ⚠️ broader **StepSecurity platform/Enterprise** capabilities — *not* the `harden-runner` action itself | ✅ |
| Maintenance burden | low (policy edits, Dependabot PRs) | block-mode = inline allowlist edits → PR per endpoint change | Policy Store (backend-hosted) removes in-repo edits but moves allowlist out of VCS |
| False-positive noise | minimal | ML-baseline anomaly detection alerts on every legitimate new endpoint until baseline updates | same; Checks fails on baseline change |
| Integration effort | config + workflow YAML | one `uses: step-security/harden-runner@v2` step as first step per job (audit mode = no other changes) | same + runner/policy setup |

---

## Prioritized minimum-viable rollout

1. **`permissions: {}` at workflow level** + grant only what each job needs; restrict default `GITHUB_TOKEN` in repo settings. *(free, OWASP-endorsed, highest win)* — ✅ largely in place via `test_workflow_hygiene.py`. [F7]
2. **SHA-pin every third-party action** to a commit SHA. ✅ already enforced by `test_workflow_hygiene.py`. Note: GitHub's Aug 2025 policy *permits* pinning/blocking but does **not** mandate SHA-pinning — the hygiene test is the actual enforcement. [F8, F10b]
3. **Dependabot** on npm + Python; **secret scanning** + push protection. ✅ `secret-scan.yml` / `dependency-review.yml` present. *(free)*
4. **Action blocklist** (`!` prefix) for rapid response to compromised actions (manual policy edit, not auto-blocking). [F8]
5. **SLSA build-provenance attestations** via `actions/attest-build-provenance` — free **if the repo is public**; if private, requires GitHub Enterprise Cloud (a separate, larger cost decision — don't bundle it into the Harden-Runner call). [F9]
6. **Harden-Runner in audit mode** on public-facing / reusable workflows — the one control GitHub gives you natively nothing for. *(For this repo: already done — and beyond, at Enterprise Policy Store tier; see "Where this repo already stands.")* [F1, F4, F6]
7. **Enterprise tier** — defer until you need private-repo egress *enforcement* (block mode), workflow run policies that block compromised-action/secret-exfil runs, or least-privilege `GITHUB_TOKEN` recommendations. Re-evaluate then whether per-dev cost beats GitHub-native + CodeQL. [F0]

---

## Drop-in audit-mode workflow snippet

Add this as the **first step of each job**. Audit mode needs no allowlist and no other workflow changes — it only observes and reports. SHA-pinned to v2.21.0 (released 2026-08-15) per this repo's `test_workflow_hygiene.py` rule.

> **Repo-specific note:** This repo does **not** use this audit-mode shape — it uses the **Policy Store mode** (`use-policy-store: true` + `api-key: ${{ secrets.STEP_SECURITY_API_KEY }}`), a third option beyond audit/block where the allowlist is hosted in the StepSecurity backend rather than inline in YAML. The audit-mode snippet below is reference for repos not yet on Harden-Runner; the block-mode variant shows the inline-allowlist alternative the Policy Store mode replaces.

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - name: Harden Runner
        uses: step-security/harden-runner@05e31511f85b41b11d1cf0ef85d0992719546e2c  # v2.21.0
        with:
          egress-policy: audit
      # ... existing steps follow unchanged
```

**To move to block mode later** (the actual enforcement — Linux only):

```yaml
      - name: Harden Runner
        uses: step-security/harden-runner@05e31511f85b41b11d1cf0ef85d0992719546e2c  # v2.21.0
        with:
          egress-policy: block
          allowed-endpoints: |
            github.com:443
            api.github.com:443
            registry.npmjs.org:443
            pypi.org:443
            files.pythonhosted.org:443
            # add only what your job actually needs
```

**Block-mode friction (F5):** the free tier keeps the allowlist inline in the YAML, so each endpoint change forces a workflow-file PR. Enterprise's backend Policy Store removes that but moves the allowlist out of version control — a tradeoff to weigh when considering the paid tier.

> ⚠️ **Scope clarity (F10a):** the research question named imposter-commit detection, artifact attestations, and secrets-in-build-log as "Harden-Runner features," but verification clarified these are **broader StepSecurity platform/Enterprise capabilities**, not delivered by the `harden-runner` action itself. The action delivers runtime egress allowlisting/anomaly detection. The other detections come with the Enterprise platform tier.

---

## Key findings (cited)

- **F0 (high, 3-0)** — Tier structure: Community = unlimited public repos on GitHub-hosted runners; Enterprise = $16/dev/mo, gates private repos, self-hosted/ARC/GitLab/Azure, run policies, Checks integration, min-`GITHUB_TOKEN`, file/process telemetry. *stepsecurity.io/pricing · docs.stepsecurity.io · marketplace listing · harden-runner README*
- **F1 (high, 3-0)** — Runtime egress control at DNS/HTTPS/L3-4 + DNS-exfil blocking; GitHub hosted runners have unrestricted outbound otherwise. Two historical DNS-exfil bypass CVEs fixed in v2.16.0 (Mar 2026), Community-tier only; Enterprise unaffected. Block mode Linux-only. *docs.stepsecurity.io*
- **F2 (high, 3-0)** — Six detection categories exist on the platform (imposter-commit, secrets-in-log, source-overwrite, suspicious-process, agent-tampering, Runner.Worker memory-read) — confirmed against the live StepSecurity platform. **Caveat: Enterprise-tier platform detections, not the `harden-runner` action's own feature list.** *docs.stepsecurity.io/workspace/detections*
- **F3 (high, 3-0)** — Anomaly detection is ML-baseline-based (Creating/Stable/Unstable). Once stable, any new endpoint alerts until baseline updates → real FP-triage burden for a team that changes deps often. *marketplace · docs · README*
- **F4 (high, 3-0)** — Integration = one `uses: step-security/harden-runner@v2` first step per job; audit mode needs no other changes; block mode needs an allowlist. *docs.stepsecurity.io*
- **F5 (medium, 2-1/3-0)** — Free-tier block-mode friction: inline allowlist → PR per endpoint change. Backend Policy Store fixes it but moves the allowlist out of VCS and is effectively a managed/paid mechanism. *discussions/84 · issues/217*
- **F6 (high, 3-0)** — OWASP independently names Harden-Runner as the example egress-restriction control for hosted runners — a distinct control beyond the free GitHub-native baseline. *OWASP GitHub Actions Security Cheat Sheet*
- **F7 (high, 3-0)** — OWASP: `permissions: {}` workflow-level + job-level grants + restrict default `GITHUB_TOKEN` in settings. Free, consensus best practice. *OWASP cheat sheet*
- **F8 (high, 3-0)** — GitHub Actions policy (free, GA Aug 2025) supports `!`-prefix action blocklisting that overrides any allow policy. Manual edit required — not real-time auto-blocking. *github.blog changelog · docs.github.com*
- **F9 (high, 3-0)** — SLSA attestations free for public repos on all plans; private/internal needs GitHub Enterprise Cloud. *actions/attest-build-provenance · docs.github.com/enterprise-cloud*
- **F10 (refuted/clarified)** — (a) imposter-commit/attestations/secrets-in-log are **not** in the `harden-runner` action's own README feature list — broader platform/Enterprise capabilities; (b) GitHub does **not** natively *enforce* SHA-pinning (only permits/blocks); (c) audit (warn-only) mode **does** exist and is the default — "block-only, no warn mode" was refuted.

---

## Caveats

- All findings rest primarily on **vendor primary sources** (StepSecurity pricing/docs, GitHub docs/changelog) + OWASP for the independent egress-control endorsement — appropriate for descriptive product-capability claims but inherently favorable to the vendor's framing; **no independent benchmark or comparative detection-quality study was found.**
- Pricing/tier boundaries are **time-sensitive** (StepSecurity has revised tiers before: Enterprise was $12 then $16/dev/mo). Current as of 2026-08-18.
- The **maintenance-friction finding (F5, 2-1) is the weakest-confirmed** and slightly imprecise — friction applies to block mode, not the audit-mode default.
- The research question named imposter-commit/attestations/secrets-in-log as "Harden-Runner features," but verification clarified these are **broader StepSecurity platform/Enterprise capabilities**, not all delivered by the action itself — scope clarity matters for the adoption decision.
- **No data was found** on actual false-positive rates in production at comparable-size teams, nor on detection latency for novel supply-chain attacks.

---

## Open questions (unresolved by sources)

1. Real-world FP rate / triage burden of the baseline anomaly detection for a small unstaffed team on a Node+Python monorepo with frequently-changing deps?
2. For a **private** monorepo, is $16/dev/mo justified over the free GitHub-native baseline once run-policies + min-`GITHUB_TOKEN` are included — or do allowlist + Dependabot + CodeQL already cover the marginal threats?
3. Does Harden-Runner's baseline detection overlap the existing CodeQL + `test_workflow_hygiene.py` (redundant alerts), or cover a complementary runtime/egress surface they don't address? *(Working read: complementary — CodeQL is static SAST, hygiene tests are workflow-config invariants, Harden-Runner is runtime egress. Minimal overlap.)*
4. For private-repo SLSA attestations, how does GitHub Enterprise Cloud cost/benefit compare to self-hosted cosign/Sigstore or StepSecurity's attestation offering?

---

## Sources (21)

**Primary:** stepsecurity.io/pricing · docs.stepsecurity.io/github-actions/harden-runner · docs.stepsecurity.io/github-actions/harden-runner/workflow-runs · docs.stepsecurity.io/workspace/detections · github.com/marketplace/actions/harden-runner · github.com/step-security/harden-runner/ · github.com/step-security/harden-runner/discussions/84 · github.com/step-security/harden-runner/issues/58 · OWASP GitHub Actions Security Cheat Sheet · github.blog/changelog/2025-08-15 (Actions policy `!`-blocklist + SHA-pinning) · github.com/actions/attest-build-provenance/ · docs.github.com/enterprise-cloud (artifact attestations) · sysdig.com/blog/security-mechanism-bypass-in-harden-runner (CVE analysis) · github.com/advisories/GHSA-mrrh-fwg8-r2c3 · github.blog supply-chain posts (×2)

**Practitioner/blog:** okulbida.com · safeguard.sh · asecurityengineer.com ("tags are not pins") · stepsecurity.io/blog (TeampCP/trivy attack teardown) · devopsil.com (MVP hardening order) · dev.to (org hardening guide)

**Dropped as unreliable:** learn.github.com product-guide (0 claims extracted).

---

*Generated 2026-08-18 via a deep-research workflow (103 agents, 5 search angles, 3-vote adversarial claim verification). Full structured JSON: see workflow output. This is a decision-support report, not a security audit.*