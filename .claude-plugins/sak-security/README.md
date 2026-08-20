# sak-security

Security review agents for the Sak-Family-Agent workspace.

## Agents

- **security-reviewer** — Adversarial pre-merge reviewer for auth, secrets, network egress, sandboxing, tool/MCP guardrails, and prompt-injection exposure. Run when a change crosses a trust boundary. Verdict-first output (`BLOCK` / `CONCERNS` / `CLEAN`) with `file:line` data-flow traces and idiom-matching fixes.
- **test-writer** — Guides test authoring for this codebase's security surfaces. Contains critical context about known guardrail-testing pitfalls — e.g. the `test_guardrails_containers.py` / rule-6 shadowing hazard (see the file for details).
- **workflow-reviewer** — Reviews `.github/workflows/*.yml` changes for the invariants pinned by `tests/test_workflow_hygiene.py` (SHA-pinned actions, top-level `permissions:`, per-PR `concurrency:` group, job-level `timeout-minutes`, CodeQL default-setup coexistence, fork-safe `pull_request_target` patterns).

## Install (local, from this repo)

```bash
claude plugin add ./path/to/Sak-Family-Agent/.claude-plugins/sak-security
```

Then enable it:

```bash
claude plugin enable sak-security@local
```

Restart Claude Code and the `security-reviewer` agent will be dispatchable.

## Scope

Tailored to this codebase's real surfaces:

- Python core: `personas/sakthai/sakthai/auth.py`, `sandbox.py`, `agent/guardrails.py`, `agent/guardrails_hardened.py`, `telegram/bot.py` (the authorization check in `_reply_with_agent_result`)
- Dashboard: `apps/sak_agent_dashboard/src/lib/safety/ast_sandbox.ts`, `lib/orchestrator/supervisor.ts`
- Corroborates with the repo's own gates: `bandit`, `gitleaks` (`.gitleaks.toml`), `pip-audit`, plus CodeQL/OSSAR/StepSecurity posture

The agent runs `bandit`/`gitleaks`/`pip-audit` to confirm hunches, but clean scans never close a finding reasoned from reading the code.