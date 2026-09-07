# Sak Family Agent GitHub Actions CI/CD Integration Guide

## Purpose

This guide explains how to integrate `.claude/agents/sak-family-agent-developer.md` into GitHub Actions for the `beer-sakthai/Sak-Family-Agent` repository. The integration has two distinct layers:

1. **Deterministic validation**, which must remain the merge gate. It validates the agent definition, persona invariants, skill composition, exports, linting, typing, security, and tests without requiring an LLM or external credentials.
2. **Optional AI-assisted review**, which may provide additional analysis or draft changes. It must not replace deterministic checks, and it must run with narrowly scoped permissions and explicit secret handling.

The repository already runs its primary quality bar in `.github/workflows/ci.yml`. The recommended design is therefore additive: keep `CI` authoritative, add a focused workflow for agent-contract changes, and use an AI workflow only as a non-blocking review aid until its behavior is proven safe.

> **Important distinction:** A Claude Code agent definition is an instruction file. GitHub Actions does not execute `.claude/agents/sak-family-agent-developer.md` automatically. A workflow must either run deterministic repository checks or explicitly invoke an AI action and tell that action to read the definition.

## Repository contracts to preserve

The integration must respect the following source-of-truth rules.

| Concern | Canonical location | CI/CD implication |
|---|---|---|
| Agent development instructions | `.claude/agents/sak-family-agent-developer.md` | Validate frontmatter and prompt structure when this file changes. |
| Persona identity | `personas/<persona>/SOUL.md` | Run soul-consistency checks for identity, sibling, lane, and tool claims. |
| Runnable Python package | `personas/sakthai/sakthai/` | Use the existing Ruff, mypy, Bandit, and pytest commands. |
| Shared skill tree | `personas/shared/skills/` | Compose all six overlays and detect composition failures. |
| Persona-specific overlay | `personas/<persona>/skills/` | Preserve overlay precedence and naming conventions. |
| Hermes runtime profiles | `infra/hermes-agents/default/` and `infra/hermes-agents/profiles/<persona>/` | Verify the profile scaffold remains present and aligned. |
| Standalone exports | `scripts/export_agent_repo.py` | Exercise all six export paths without publishing or pushing from CI. |
| Persona diagnostics | `scripts/diagnose_personas.py` | Use as an offline integration check; report warnings separately from hard failures. |

The repository contains six personas: `sakking`, `sakthai`, `saksee`, `saksit`, `saktan`, and `sakjules`. SakThai uses the reserved `infra/hermes-agents/default/` profile; the other personas use `infra/hermes-agents/profiles/<persona>/`.

## Recommended workflow architecture

Use three levels of checks.

| Level | Trigger | Required? | Purpose |
|---|---|---:|---|
| Focused agent-contract workflow | Pull requests and pushes touching agent/persona paths | Yes for relevant changes | Fast validation of the new agent definition and persona contracts. |
| Existing `CI` workflow | Every push to `main` and pull request to `main` | Yes | Full Ruff, format, mypy, Bandit, and 96% coverage-gated pytest suite on Python 3.11 and 3.12. |
| Optional AI review workflow | Manual dispatch or controlled pull-request event | No initially | Contextual review using the agent instructions. It should comment or produce an artifact, not control merging until audited. |

The focused workflow should use `permissions: contents: read`, `persist-credentials: false`, pinned action SHAs, a concurrency group, and a timeout. It should not require API keys, GitHub write permissions, or access to production systems.

## Focused deterministic workflow

Create `.github/workflows/sak-family-agent-contract.yml` with the following shape. Replace action SHAs only with reviewed, immutable commit SHAs. The example intentionally uses the repository’s existing commands and does not invoke an LLM.

```yaml
name: Sak Family agent contract

on:
  push:
    branches: ["main"]
    paths:
      - ".claude/agents/**"
      - "personas/**/SOUL.md"
      - "personas/**/config/**"
      - "personas/**/skills/**"
      - "personas/shared/**"
      - "infra/hermes-agents/**"
      - "scripts/compose_persona.py"
      - "scripts/diagnose_personas.py"
      - "scripts/export_agent_repo.py"
      - "tests/test_soul_consistency.py"
      - "tests/test_compose_persona.py"
      - "tests/test_export_agent_repo.py"
      - ".github/workflows/sak-family-agent-contract.yml"
  pull_request:
    branches: ["main"]
    paths:
      - ".claude/agents/**"
      - "personas/**/SOUL.md"
      - "personas/**/config/**"
      - "personas/**/skills/**"
      - "personas/shared/**"
      - "infra/hermes-agents/**"
      - "scripts/compose_persona.py"
      - "scripts/diagnose_personas.py"
      - "scripts/export_agent_repo.py"
      - "tests/test_soul_consistency.py"
      - "tests/test_compose_persona.py"
      - "tests/test_export_agent_repo.py"
      - ".github/workflows/sak-family-agent-contract.yml"
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: sak-family-agent-contract-${{ github.ref }}
  cancel-in-progress: true

jobs:
  contract:
    name: Validate agent and persona contracts
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - name: Harden the runner
        uses: step-security/harden-runner@<reviewed-commit-sha>
        with:
          use-policy-store: true
          api-key: ${{ secrets.STEP_SECURITY_API_KEY }}

      - name: Checkout repository
        uses: actions/checkout@<reviewed-commit-sha>
        with:
          persist-credentials: false

      - name: Set up Python
        uses: actions/setup-python@<reviewed-commit-sha>
        with:
          python-version: "3.12"

      - name: Install uv
        uses: astral-sh/setup-uv@<reviewed-commit-sha>

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Validate Claude agent definition
        run: python scripts/validate_agent_definition.py .claude/agents/sak-family-agent-developer.md

      - name: Check whitespace
        run: git show --check --oneline --no-renames HEAD

      - name: Compose all persona skill trees
        run: make compose-personas

      - name: Run persona contract tests
        run: >-
          uv run pytest -q
          tests/test_soul_consistency.py
          tests/test_compose_persona.py
          tests/test_export_agent_repo.py
          tests/test_persona_guardrails_parity.py

```

### Required adjustment for GitHub-hosted runners

The repository-local validator used during development is stored in the Manus skill installation, not in this repository. GitHub-hosted runners will not have `/home/ubuntu/skills/agent-development/scripts/validate-agent.sh`. Choose one of these approaches:

| Approach | Recommendation | Implementation |
|---|---|---|
| Vendor a small validator | Preferred for reproducibility | Add a repository script such as `scripts/validate_agent_definition.py` or copy the relevant checks into a maintained project utility. Test it with the repository suite. |
| Inline shell validation | Acceptable for a minimal first version | Validate file existence, frontmatter delimiters, required fields, and prompt length directly in the workflow. |
| Install a private tooling package | Use only if already governed | Pin the package and document its provenance and update process. |

Do not make CI depend on a Manus sandbox path. The sample command above is a placeholder that must be replaced before committing the workflow. A repository-owned validator is the most portable option because it can run locally, in GitHub Actions, and in standalone exports.

## Suggested repository-owned validator

A lightweight validator should check the exact contract already used for this agent:

- the file exists and begins and ends its YAML frontmatter correctly;
- `name`, `description`, `model`, and `color` are present;
- the name uses lowercase letters, digits, and hyphens and is 3–50 characters long;
- the description contains `Use this agent when`, 2–4 concrete trigger examples, and `When to invoke`;
- the model is `inherit`, `sonnet`, `opus`, or `haiku`;
- the color is one of the supported UI colors;
- the body is between 20 and 10,000 characters;
- the body defines invocation scenarios, responsibilities, process, output, quality standards, and edge cases;
- the declared tool set is intentionally limited.

The validator should return a non-zero exit code for malformed frontmatter or missing required fields. It should emit actionable line-oriented errors so a pull request author can fix the issue without an AI review.

## Export and diagnostics checks

The export helper copies a shared core, one persona overlay, and the matching Hermes profile into a standalone snapshot. CI should validate that all six exports complete, but it should not publish those snapshots or push to the six standalone repositories from an untrusted pull request.

A dedicated export smoke test can be run with:

```bash
set -euo pipefail
for persona in sakking sakthai saksee saksit saktan sakjules; do
  python scripts/export_agent_repo.py "$persona" --out "build/agent-repos/$persona"
  test -s "build/agent-repos/$persona/README.md"
  test -s "build/agent-repos/$persona/AGENTS.md"
done
```

`scripts/diagnose_personas.py` performs broader offline checks, including skill composition, model configuration, MCP manifest loading, dry-run preflight, memory round-trips, and Hermes profile scaffolds. It creates temporary `SAKTHAI_HOME` directories and should not need production credentials. Its documented behavior treats skill naming drift and an unavailable self-evolution dependency as warnings, while hard runtime contract failures return non-zero. The current repository intentionally gives SakTan an empty MCP manifest, but the diagnostic currently treats an empty server list as a hard failure. For that reason, the ready-to-use merge-gating workflow does not invoke this broader diagnostic; run it manually when investigating runtime profiles, and resolve the SakTan diagnostic contract before making it required.

If diagnostics become slow, keep the focused workflow limited to the contract tests and run the full diagnostics in a separately required integration job. The existing `CI` workflow is the repository's full quality gate, but it does not currently invoke `scripts/diagnose_personas.py`. Do not weaken the checks silently; record the decision in the workflow comments and guide.

## Integrating with the existing CI workflow

The existing `.github/workflows/ci.yml` remains the source of truth for the full quality bar. It currently:

- runs on pushes to `main` and pull requests targeting `main`;
- tests Python 3.11 and 3.12;
- installs all optional dependencies with `uv sync --all-extras`;
- runs Ruff check and format validation;
- runs mypy and Bandit;
- runs pytest with an explicit 96% coverage floor;
- grants only `contents: read` and disables persisted checkout credentials.

The focused agent workflow should not duplicate the full matrix unless the agent change affects executable Python behavior. Instead, require both checks as follows:

1. Require the focused `Sak Family agent contract / Validate agent and persona contracts` check for changes under the agent paths.
2. Keep the existing `CI / test (3.11)` and `CI / test (3.12)` checks required for all normal code changes.
3. Require the focused check itself to run on workflow changes by including its own path in `on.paths`.
4. Configure branch protection so an incomplete or skipped required check cannot be mistaken for a successful validation.
5. Re-run the focused workflow on `workflow_dispatch` after changing runner versions, action pins, or repository-owned validator code.

## Optional AI-assisted review

The agent definition can guide an AI review, but the review must be treated as advisory until it has been evaluated against representative pull requests. Use an official Claude Code GitHub integration or another approved action according to its current documentation. Pin the action to a reviewed commit SHA and use the least privileged permissions supported by the action.

A safe initial rollout has these properties:

| Control | Initial policy |
|---|---|
| Trigger | Manual `workflow_dispatch`, or a controlled comment/mention workflow. |
| Secrets | Use a dedicated repository or environment secret. Never expose it to fork pull requests. |
| Repository token | `contents: read`; add comment or pull-request write permission only if the action genuinely needs it. |
| Checkout | `persist-credentials: false`; never run untrusted PR code with write-capable credentials. |
| Merge gate | Non-blocking until false positives, prompt injection, and failure behavior are understood. |
| Scope | Ask the model to review only the diff and the relevant agent/persona contracts. |
| Changes | Prefer a report artifact or comment. Do not allow automatic pushes or merges in the first rollout. |
| Logging | Ensure prompts, outputs, and tool traces do not include credentials, private memory, or sensitive user context. |

The AI review prompt should direct the model to:

```text
Read .claude/agents/sak-family-agent-developer.md and follow its repository-specific contract.
Review only the current pull request diff and the relevant files under the Sak Family Agent
repository. Check persona identity, six-agent invariants, runtime/profile alignment, export
behavior, tests, security boundaries, and documentation drift. Do not modify files, push
commits, merge the pull request, access unrelated repositories, or use secrets. Return
findings with severity, file/line references, evidence, and a concrete recommendation.
```

Do not use `pull_request_target` to run arbitrary checkout contents with write permissions. That event runs in the base repository security context and can expose secrets or write access to untrusted pull-request code if the workflow is designed incorrectly. If comments are required, separate the trusted comment-posting step from the untrusted analysis step, or use the official integration’s documented security model.

## CI/CD promotion flow

The recommended promotion sequence is:

1. **Pull request:** run the focused deterministic contract workflow and the existing CI matrix. Run optional AI review as advisory analysis.
2. **Merge to `main`:** rerun both required workflows on the merge commit. Build persona compositions and export snapshots as ephemeral artifacts if they are useful for inspection.
3. **Post-merge deployment:** publish or synchronize runtime profiles only from a protected workflow triggered by `push` to `main` or manual approval. Do not deploy from a fork pull request.
4. **Standalone repositories:** if exports are synchronized to the six standalone repositories, use a separate trusted workflow with an allowlisted persona matrix, environment protection, and explicit repository-boundary checks. Keep export generation read-only until the artifact has passed validation.
5. **Rollback:** retain the previous deployment artifact or commit SHA and provide a manual workflow dispatch path to redeploy the last known-good version. Do not implement rollback by deleting branches, tags, or repository data automatically.

A deployment job that writes to external repositories, updates a live service, or changes credentials is a consequential action. It requires a protected environment, narrow tokens, audit logs, and an explicit approval policy. Ordinary pull-request validation should never have those capabilities.

## Failure handling and observability

Each job should fail closed for malformed agent definitions, missing persona files, failed tests, security-scan findings, and export errors. The workflow should print the exact failing command and preserve useful test reports or generated snapshots as artifacts where appropriate.

Distinguish these outcomes in job summaries:

| Outcome | Meaning | Action |
|---|---|---|
| Failed | A required contract or quality check did not pass. | Block merge and fix the cause. |
| Passed | All required checks completed successfully. | Continue through branch protection. |
| Warning | A documented non-blocking diagnostic issue occurred. | Record it and create follow-up work if it is persistent. |
| Skipped | A job did not run because its path or event filter did not match. | Confirm that the check is not incorrectly configured as required. |
| Cancelled | A newer commit superseded the run. | Wait for the newest run; do not treat cancellation as success. |

Avoid embedding private memory, user health information, API keys, or full environment dumps in logs. Mask values before printing diagnostics. Keep `set -x` disabled in shell steps that handle secrets.

## Local reproduction checklist

Before opening a pull request that changes the agent definition or persona contracts, run:

```bash
python scripts/validate_agent_definition.py .claude/agents/sak-family-agent-developer.md
uv sync --all-extras
make compose-personas
uv run pytest -q \
  tests/test_soul_consistency.py \
  tests/test_compose_persona.py \
  tests/test_export_agent_repo.py \
  tests/test_persona_guardrails_parity.py
```

For changes to executable package code, also run the same quality commands used by `.github/workflows/ci.yml`:

```bash
uv run ruff check personas/sakthai/sakthai tests
uv run ruff format --check personas/sakthai/sakthai tests
uv run mypy personas/sakthai/sakthai
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai
uv run pytest --cov=sakthai --cov-report=xml --cov-fail-under=96 tests/
```

## Implementation checklist

- [ ] Add a repository-owned agent-definition validator or replace the placeholder validator command.
- [ ] Add the focused workflow with path filters, read-only permissions, pinned action SHAs, timeout, and concurrency cancellation.
- [ ] Include the workflow’s own path in its trigger filters.
- [ ] Run focused soul, composition, export, and guardrail tests.
- [ ] Decide whether full persona diagnostics belong in the focused workflow or the main CI workflow based on runtime.
- [ ] Configure required checks and verify the skipped-check behavior on unrelated pull requests.
- [ ] Keep AI review advisory until its security and accuracy behavior has been evaluated.
- [ ] Use protected environments for any post-merge deployment or cross-repository synchronization.
- [ ] Document action pin updates and review them through normal dependency-maintenance processes.
- [ ] Test one normal pull request, one fork pull request, a workflow-only change, a persona-only change, and a failed validator run.

## References

[1]: https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions "GitHub Actions workflow syntax"

[2]: https://docs.github.com/actions/using-workflows/events-that-trigger-workflows "GitHub Actions events that trigger workflows"

[3]: https://docs.github.com/actions/security-for-github-actions/security-hardening-for-github-actions "GitHub Actions security hardening"

[4]: https://code.claude.com/docs/en/github-actions "Claude Code GitHub Actions"

[5]: https://github.com/anthropics/claude-code-action "Anthropic Claude Code Action"

[6]: https://github.com/beer-sakthai/Sak-Family-Agent/blob/main/.github/workflows/ci.yml "Sak Family Agent primary CI workflow"

[7]: https://github.com/beer-sakthai/Sak-Family-Agent/blob/main/.github/workflows/agent-self-evolution.yml "Sak Family Agent self-evolution workflow"
