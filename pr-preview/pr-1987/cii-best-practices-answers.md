# OpenSSF Best Practices badge: draft answers (passing level)

Drafted 2026-10-09 for project
[14039](https://www.bestpractices.dev/en/projects/14039), which is 19%
complete: 13 passing criteria answered, 54 still `?`. Only a project owner
signed in to bestpractices.dev can enter these. Paste each status and
justification at
<https://www.bestpractices.dev/en/projects/14039/passing/edit>.

The statuses are what the repository supports today, not what would make the
badge pass. Where a criterion isn't met, the row says what would meet it.

**The badge cannot reach passing as things stand.** Passing needs every MUST
criterion Met (or N/A where allowed), and three are Unmet:

| MUST criterion | Why it's Unmet | What would meet it |
|---|---|---|
| `floss_license` | `LICENSE` is "House of Sak Intellectual Property License — All Rights Reserved", a deliberate change from MIT (see `CHANGELOG.md`). It isn't a FLOSS licence. | Relicense under an OSI-approved licence. That's an owner decision, not a code change. |
| `test` | The criterion needs a test suite released as FLOSS; `tests/` is under the same licence. | Met by the same relicensing. |
| `version_unique` | Releases aren't identified: `pyproject.toml` has said `2.0.0` throughout and there are no tags or published releases. | Tag and publish releases (for example `v2.0.0`) and bump the version for each one. |

Scorecard's CII-Best-Practices alert (#15462) stays open until the badge
reaches passing. See [`scorecard-accepted-risks.md`](scorecard-accepted-risks.md).

Links below are relative to
`https://github.com/beer-sakthai/Sak-Family-Agent/blob/main/`.

## Basics

| Criterion | Level | Suggested | Justification and evidence |
|---|---|---|---|
| `description_good` | MUST | Met | The README opens with what the software is (a personal learning agent with persistent SQLite memory, an agent loop and an MCP server) and its "What is included" section. `README.md` |
| `interact` | MUST | Met | Obtain: README "Quick start" (`git clone`, `uv sync`). Feedback: GitHub Issues (bug, feature and question templates) and Discussions. Contributing: `CONTRIBUTING.md`. |
| `contribution` | MUST | Met (already) | `CONTRIBUTING.md` explains the process: issues and discussions are welcome; outside pull requests are not accepted. |
| `contribution_requirements` | SHOULD | Met | `AGENTS.md` sets the requirements: ruff formatting at 100 columns, type annotations, tests for every behaviour change, and a 96% coverage floor. |
| `floss_license` | MUST | **Unmet** | `LICENSE` reserves all rights. See the table above. |
| `floss_license_osi` | SUGGESTED | **Unmet** | Same reason. |
| `license_location` | MUST | Met (already) | `LICENSE` at the repository root. |
| `documentation_basics` | MUST | Met (already) | `README.md` quick start, and `docs/` (architecture, runtimes, capabilities, workspace setup). |
| `documentation_interface` | MUST | Met | `docs/runtimes.md` documents the CLI, agent loop and MCP stdio server. The web API's payloads are defined once in `personas/sakthai/sakthai/web/contracts.py`, with generated TypeScript types. |
| `sites_https` | MUST | Met (already) | GitHub and the Hugging Face homepage are HTTPS only. |
| `discussion` | MUST | Met (already) | GitHub Issues and Discussions are enabled, public, searchable and linkable. |
| `english` | SHOULD | Met | All documentation is in English, and reports in English are accepted. |
| `maintained` | MUST | Met | Commits land on `main` weekly, and Dependabot updates are merged regularly. |

## Change control

| Criterion | Level | Suggested | Justification and evidence |
|---|---|---|---|
| `repo_public` | MUST | Met (already) | <https://github.com/beer-sakthai/Sak-Family-Agent> |
| `repo_track` | MUST | Met (already) | git records who changed what, and when. |
| `repo_interim` | MUST | Met | Every change lands through a pull request on `main`, so interim states are public, not just final releases. |
| `repo_distributed` | SUGGESTED | Met (already) | git |
| `version_unique` | MUST | **Unmet** | See the table above. |
| `version_semver` | SUGGESTED | Unmet | `CHANGELOG.md` says the project aims to follow SemVer, and `2.0.0` is SemVer, but no releases are cut. Met once releases are tagged. |
| `version_tags` | SUGGESTED | Unmet | No git tags. Met by tagging each release. |
| `release_notes` | MUST | N/A (currently Met) | No releases are published; users run `main`. `CHANGELOG.md` says itself that it lags the repository, so claiming per-release notes overstates it. Once releases are tagged, give each one a `CHANGELOG.md` section and switch this to Met. |
| `release_notes_vulns` | MUST | N/A | No releases, as above. |

## Reporting

| Criterion | Level | Suggested | Justification and evidence |
|---|---|---|---|
| `report_process` | MUST | Met (already) | GitHub Issues with templates (`.github/ISSUE_TEMPLATE/`). |
| `report_tracker` | SHOULD | Met | GitHub Issues. |
| `report_responses` | MUST | Met | No bug reports were filed in the last 12 months, so none went unacknowledged. |
| `enhancement_responses` | SHOULD | Met | No enhancement requests were filed in the last 12 months. |
| `report_archive` | MUST | Met | GitHub Issues and pull requests are public and searchable. |
| `vulnerability_report_process` | MUST | Met | `SECURITY.md`, "Reporting a Vulnerability". |
| `vulnerability_report_private` | MUST | Met | GitHub private vulnerability reporting is enabled; `SECURITY.md` links its form (`/security/advisories/new`), and `docs/SECURITY.md` gives an email alternative. |
| `vulnerability_report_response` | MUST | Met | No vulnerability reports in the last 6 months (no repository advisories). `docs/SECURITY.md` commits to acknowledging within 3 business days. |

## Quality

| Criterion | Level | Suggested | Justification and evidence |
|---|---|---|---|
| `build` | MUST | Met (already) | `uv sync` builds and installs the package from `pyproject.toml` (setuptools); `npm ci && npm run build` builds the dashboard. |
| `build_common_tools` | SUGGESTED | Met (already) | uv, setuptools, npm, Next.js |
| `build_floss_tools` | SHOULD | Met | All of those build tools are FLOSS. |
| `test` | MUST | **Unmet** | An automated suite exists (`tests/`, pytest; `uv run pytest tests/`), but it isn't released as FLOSS. See the table above. |
| `test_invocation` | SHOULD | Met | `uv run pytest tests/` or `make test`; `npm test` for the dashboard. |
| `test_most` | SUGGESTED | Met | Branch coverage of the core package is enforced at ≥96% (`--cov-fail-under=96` in `.github/workflows/ci.yml`). |
| `test_continuous_integration` | SUGGESTED | Met | `ci.yml` runs the suite on Python 3.11 and 3.12 for every push and pull request; `apps.yml` runs the dashboard tests. |
| `test_policy` | MUST | Met | `AGENTS.md`: "Add or update tests with any behavior change." |
| `tests_are_added` | MUST | Met | Recent major changes added tests. #1581 added fast-check fuzzing of the URL parser plus a regression test for the bug it found; #1514 added a test that drives the real agent loop through persona delegation. |
| `tests_documented_added` | SUGGESTED | Met | `AGENTS.md` (the contribution instructions) documents the test policy. |
| `warnings` | MUST | Met | ruff, strict mypy and bandit (`ci.yml`); eslint and `tsc` (`apps.yml`); pylint (`pylint.yml`). |
| `warnings_fixed` | MUST | Met | CI fails on any ruff, mypy, eslint or tsc finding, so warnings can't accumulate. |
| `warnings_strict` | SUGGESTED | Met | mypy runs in `strict` mode over the whole package. |

## Security

| Criterion | Level | Suggested | Justification and evidence |
|---|---|---|---|
| `know_secure_design` | MUST | Met | The maintainer applies least privilege, input validation and fail-closed defaults throughout. Evidence: the tool sandbox (`read_file` restricted to allowed roots; `run_command` opt-in), the guardrail policy, and the hardening rounds recorded in `docs/security-hardening.md`. |
| `know_common_errors` | MUST | Met | `docs/security-hardening.md` records each class handled, with its mitigation and regression test: path traversal, command and option injection (`giturl.py`), secret leakage in output, cookie construction from user input, workflow token scope and supply-chain pinning. |
| `crypto_published` | MUST | Met | Only standard primitives, through Python's `secrets` and `hashlib` (SHA-256) and TLS via OpenSSL. No custom cryptography. |
| `crypto_call` | SHOULD | Met | Uses the standard library and OpenSSL; nothing is reimplemented. |
| `crypto_floss` | MUST | Met | Python standard library and OpenSSL. |
| `crypto_keylength` | MUST | Met | Bearer tokens are 128-bit (`secrets.token_hex(16)`); TLS uses OpenSSL defaults. |
| `crypto_working` | MUST | Met | No MD4, MD5, DES, RC4 or similar anywhere in the package. |
| `crypto_weaknesses` | SHOULD | Met | No SHA-1 or CBC-mode use. |
| `crypto_pfs` | SHOULD | Met | Outbound HTTPS uses OpenSSL's default ECDHE suites. The local web API serves plain HTTP and refuses non-loopback binds unless explicitly allowed. |
| `crypto_password_storage` | MUST | N/A | No user passwords are stored. The web API authenticates with a random bearer token. |
| `crypto_random` | MUST | Met | Tokens come from `secrets` (a CSPRNG), never from `random`. |
| `delivery_mitm` | MUST | Met (already) | Code is delivered over HTTPS from GitHub; dependencies come over HTTPS and are checked against hash-pinned lockfiles (`uv.lock`, `package-lock.json`, the training image's `*.lock`). |
| `delivery_unsigned` | MUST | Met | Hashes come from lockfiles committed to the repository, never fetched over HTTP. |
| `vulnerabilities_fixed_60_days` | MUST | Met | No medium-or-higher vulnerability in the software has stayed public for over 60 days unpatched. `nltk` and `sqlitedict`, which had no upstream fix, were removed from the lock instead of left open. The one advisory `npm audit` still reports, `braces` (GHSA-vfj7-8cjw-p6xm), covers every released version and sits only in the dashboard's lint tooling (`eslint-config-next`, a dev dependency), so it doesn't ship. |
| `vulnerabilities_critical_fixed` | SHOULD | Met | Fixable advisories are fixed within days, often the same day (multidict and sharp, 2026-10-06). |
| `no_leaked_credentials` | MUST | Met | gitleaks scans the commits of every pull request and every push to `main`, and a nightly sweep scans every branch tip's tree (`.github/workflows/secret-scan.yml`, config `.gitleaks.toml`). |

## Analysis

| Criterion | Level | Suggested | Justification and evidence |
|---|---|---|---|
| `static_analysis` | MUST | Met | CodeQL (`codeql.yml`), Bandit (`bandit.yml` and `ci.yml`), Trivy (`ossar.yml`), ruff, mypy, pylint and SonarCloud run on every change. |
| `static_analysis_common_vulnerabilities` | SUGGESTED | Met | CodeQL security queries (`security-extended` for workflows) and Bandit both target common vulnerability classes. |
| `static_analysis_fixed` | MUST | Met | CodeQL, Bandit and Trivy have no open alerts on `main`. Findings are fixed when confirmed. |
| `static_analysis_often` | SUGGESTED | Met | They run on every push and pull request, and CodeQL, Bandit and Scorecard also run weekly. |
| `dynamic_analysis` | SUGGESTED | Met | Property-based testing with Hypothesis (`tests/test_store_properties.py`) and fast-check fuzzing (`apps/sak_agent_dashboard/src/tests/url-state.fuzz.test.ts`) run in CI. |
| `dynamic_analysis_unsafe` | SUGGESTED | N/A | Python and TypeScript only, both memory-safe. |
| `dynamic_analysis_enable_assertions` | SUGGESTED | Met | Tests and fuzzing run with assertions enabled (pytest without `-O`; vitest). |
| `dynamic_analysis_fixed` | MUST | Met | Bugs found dynamically are fixed. Example: the fuzzer's first run found an inexact page number in the URL parser, fixed in #1581. |
