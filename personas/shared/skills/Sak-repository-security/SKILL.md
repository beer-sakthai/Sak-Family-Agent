---
name: Sak-repository-security
category: security
description: >-
  Review, implement, and verify security-sensitive changes in Sak-Family-Agent.
  Use when work touches guardrails, credentials, authentication, filesystem or
  shell execution, MCP or external integrations, dependencies, CI security
  controls, or a suspected vulnerability.
version: "1.0.0"
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - security
      - secure-coding
      - review
      - guardrails
      - ci
    related_skills:
      - Sak-repository-quality
---

# Sak-Family-Agent Security

Use this skill for a security review or implementation in `beer-sakthai/Sak-Family-Agent`. Keep changes small, evidence-based, and fail-closed. Do not weaken a control, suppress a finding, relax a test threshold, or bypass branch protection to make a change appear green.

## Start with the authoritative sources

1. Read `AGENTS.md`, `CLAUDE.md`, `SECURITY.md`, and the closest component documentation before editing.
2. Read the workflow or configuration that enforces the control being changed; do not infer a live gate from an old report.
3. Identify the canonical implementation before patching. The installed package is `personas/sakthai/sakthai/`; `personas/shared/sakthai/` and selected persona copies can intentionally diverge.
4. State the protected asset, the untrusted input, the trust boundary, the required denial behavior, and the regression that proves the behavior.

## Map the threat before changing code

Treat paths, shell arguments, URLs, model output, tool arguments, environment variables, configuration, MCP server specifications, tokens, cookies, and provider responses as untrusted unless a boundary has validated them.

| Surface | Required review focus |
| --- | --- |
| Shell or subprocess | Avoid shell interpolation; reject destructive, exfiltrating, or option-smuggling forms before execution; preserve `SAKTHAI_SHELL_ALLOW` as an explicit opt-in. |
| Filesystem or archive input | Canonicalize and contain paths; account for relative paths, separators, `..`, symlinks, case, globs, and time-of-check/time-of-use races. |
| URLs, Git remotes, or network clients | Parse and allowlist schemes and hosts where the boundary requires it; reject option-like values and remote-helper execution; set explicit timeouts. |
| Credentials or logged output | Resolve secrets through approved configuration; redact them from prompts, errors, logs, artifacts, tests, and examples. Never commit a real credential. |
| Web or API authentication | Require authentication by default; compare tokens safely; test missing, malformed, near-miss, query, and cookie inputs when supported. |
| MCP, plugins, and extensions | Validate executable/configuration boundaries, isolate names, and apply least privilege. Do not trust a server merely because it appears in a local configuration file. |
| CI, dependencies, and actions | Preserve pins, lockfiles, checksums, permissions, and scanning producers. Update generated hash locks with their documented generator rather than hand-editing them. |

## Implement defensively

1. Normalize and validate at the boundary, then keep trusted representations separate from raw user input.
2. Prefer explicit allowlists and safe defaults over denylist-only parsing. Make denial decisions before side effects.
3. Keep error messages useful without exposing secrets, absolute sensitive paths, tokens, or internal configuration.
4. Preserve existing security controls. If a control is dead or incomplete, record the evidence and fix or isolate it deliberately rather than assuming it protects production.
5. When modifying `agent/guardrails.py`, add a regression test for every bypass and synchronize the required persona copies. Run the parity test and diff the copies before submitting.
6. When modifying authentication in `web/server.py`, synchronize every documented persona copy and diff the protected block; the repository does not currently enforce this parity automatically.

## Test adversarially

Write focused tests that demonstrate both the intended allowed case and the unsafe case being denied. Vary delimiters, whitespace, encoding, case, separators, option placement, relative paths, and near-miss tokens where relevant. Assert the security outcome and absence of side effects; do not merely execute the code path.

Use fixtures and temporary directories for secrets, home directories, and filesystem writes. Never contact a live provider, install an unpinned package, or invoke an external server merely to exercise a unit test.

## Verify and integrate

1. Inspect `git diff`, run `git diff --check`, and verify that no secret-like content entered the diff.
2. Run the focused regression tests first, then the applicable repository gates. For core Python security changes, use the commands mirrored by `.github/workflows/ci.yml`: Ruff check and format check, strict mypy, Bandit, and pytest with the configured coverage floor.
3. For skill-only changes, validate the shared skill tree with `uv run sakthai skills validate --source library` and validate names with `uv run sakthai skills validate --naming`; run composition when the shared-skill delivery path is affected.
4. Open a reviewable pull request that explains the threat, boundary, test evidence, and any copy synchronization. Wait for required GitHub checks and merge only through the protected pull-request flow.

## Security review output

Report the following concise evidence: protected asset and threat; changed boundary and fail-safe behavior; tests covering allowed and denied cases; repository and GitHub checks; and any deliberately deferred risk with its authoritative tracking location.
