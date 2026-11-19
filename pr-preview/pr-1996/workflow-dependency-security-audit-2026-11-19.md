# GitHub Actions dependency security audit

**Repository:** `beer-sakthai/Sak-Family-Agent`
**Audit date:** 2026-11-19
**Scope:** all 179 workflow files under `.github/workflows/`, including generated `.lock.yml` workflows.

## Executive summary

The audit found no confirmed known vulnerability in the five explicitly versioned npm tools installed by workflow scripts, based on OSV package-version queries performed on the audit date. Every external `uses:` reference is pinned to a full 40-character commit SHA after parsing action subpaths correctly. The online `zizmor` audit found one medium-confidence provenance warning: a release comment claimed `v1.4.0`, but that tag points to a different commit. The existing PR corrects that misleading comment without changing the action pin.

The principal remaining risks are maintenance and reproducibility risks rather than confirmed CVEs. Ten third-party action repositories used by workflows are currently archived upstream. Several workflow steps install tools without a lockfile or exact version, and one generated agentic-workflow lock file contains `alpine:latest`. These should be handled as follow-up hardening work because replacing marketplace actions or changing generated lockfiles can alter workflow behavior.

## Inventory and verification results

| Check | Result | Interpretation |
|---|---:|---|
| Workflow files | 179 | Complete `.github/workflows` inventory |
| External action-use lines | 929 | Includes repeated uses across workflows |
| Unique external action refs | 162 | All use full 40-character commit SHAs after path-aware parsing |
| Online zizmor findings | 1 medium | The mismatched version comment documented below; fixed in this PR |
| Explicitly versioned npm tools queried with OSV | 5 | Zero advisories returned for the requested versions |
| Archived upstream action repositories | 10 | Supply-chain and maintenance risk; not proof of a vulnerability |
| GitHub repository security-alert APIs | unavailable | The configured token returned HTTP 403 for Dependabot, code scanning, and secret-scanning endpoints |

The apparent “nine unresolved refs” in an initial mechanical pass were false positives caused by treating action subpaths such as `github/codeql-action/upload-sarif` as repository names. The actual repository is `github/codeql-action`; the remaining path is the action name. The corrected parser found no unpinned external action reference.

## Confirmed integrity finding fixed in the PR

`mlaplante/githubprreviewhelperextension` was pinned to commit `84c713e117ecfb6fa835075bf23f5dc48d6d657b`, but its `# v1.4.0` comment was inaccurate: upstream tag `v1.4.0` points to `05b074cd6cec0ee8ca0545db6277a9a5e14aaf25`. The pin was deliberately left unchanged; the comment now states that it is a reviewed commit with no matching release tag. This removes the misleading provenance metadata and makes the online `zizmor` check pass for this finding.

## Archived action repositories requiring follow-up review

The following action repositories are archived upstream: `Khan/pull-request-comment-trigger`, `technote-space/auto-cancel-redundant-workflow`, `github/automatic-contrib-prs`, `johnmanjiro13/auto-reviewer-assign`, `drengskapur/gitbot-config`, `github/setup-licensed`, `hngprojects/pr-deploy`, `convictional/trigger-workflow-and-wait`, `SonarSource/sonarcloud-github-action`, and `technote-space/workflow-conclusion-action`. Their pins remain immutable, which limits tag-movement risk, but archived code no longer receives normal maintenance. Before replacing any of them, review each workflow’s permissions and behavior, then test the replacement in an isolated PR.

Three archived-action uses are already covered by explicit `zizmor` configuration exceptions. The remaining archived actions should either be migrated, removed if their workflow is obsolete, or documented with an owner, reason, and review date. This is intentionally not mass-replaced in the current PR.

## Runtime dependency and container findings

OSV package-version queries returned zero advisories for `@google/gemini-cli@0.64.0`, `@playwright/cli@0.1.23`, `pyright@1.1.399`, `typescript@5.8.3`, and `typescript-language-server@4.3.3`. This is a point-in-time known-advisory result, not a guarantee that the packages are safe or that transitive dependencies are risk-free.

The following workflow installs are not reproducibly locked: `ruff` in `lint-check.yml` and `reviewdog-suggester.yml`; `pytest` and `pytest-benchmark` in `continuous-benchmark.yml`; and the editable development install in `agent-self-evolution.yml`. The repository already uses `uv.lock` successfully in many workflows, so the recommended remediation is to route these jobs through locked `uv sync`/`uv run` environments or pin and hash the standalone tools. The generated `skill-pr-reviewer.lock.yml` also lists `alpine:latest`; it should be regenerated with a digest-pinned Alpine image if that image is required.

## Recommended follow-up order

First, review or retire the ten archived actions, prioritizing actions with write permissions or issue/comment mutation. Next, make the four direct Python-tool installation patterns reproducible through the repository lockfiles. Then replace `alpine:latest` with a digest-pinned image in the source generator and regenerate affected lockfiles. Finally, enable or repair repository security-alert permissions for the audit identity and add a scheduled OSV or dependency-review gate that covers both lockfiles and workflow-installed tools.

## Method and references

The audit combined local workflow parsing, SHA and upstream repository metadata checks through the GitHub API, the online `zizmor` workflow auditor, direct OSV API package-version queries, and inspection of generated workflow manifests. GitHub’s secure-use guidance recommends full-length SHA pins, verification that the SHA belongs to the intended repository, and source auditing for third-party actions. OpenSSF Scorecard provides complementary checks for vulnerabilities, dangerous workflows, pinned dependencies, and token permissions. OSV supports vulnerability queries by package version or commit hash.

References: [GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use), [OpenSSF Scorecard](https://scorecard.dev/), [OSV](https://osv.dev/), [actions/checkout](https://github.com/actions/checkout), and [actions/upload-artifact](https://github.com/actions/upload-artifact).
