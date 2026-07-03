# Hermes-Free VM Deployment Plan

## Summary

Deploy all six Sak Family agents on the VM with Telegram chat and persistent memory, but without requiring Hermes as the runtime. The goal is to preserve the current user-facing behavior: each agent should respond in Telegram, keep its persona, share memory where intended, and start cleanly on reboot or restart.

## Key Changes

- Replace Hermes gateway launch with a VM-native supervisor path, using `systemd --user` services or an equivalent lightweight launcher.
- Keep one runtime instance per agent: SakKing, SakThai, SakSee, SakSit, SakTan, and SakJules.
- Preserve Telegram delivery by wiring each bot directly to the agent loop and its own token.
- Keep shared memory and MCP/tool access available so the agents still behave statefully.
- Use the existing `Sak-Family-Agent` repository as the source of truth for persona files, runtime docs, and deployment scripts.

## Implementation Changes

- Define a repeatable VM bootstrap flow: install dependencies, export secrets, start services, and verify Telegram replies.
- Create per-agent environment files or service drop-ins for model credentials, Telegram tokens, and memory paths.
- Keep SakKing as the lead/orchestrator and preserve the current persona and model assignments for the other agents.
- Document the exact startup order and restart behavior so the VM can recover without Hermes.
- Add a clear smoke test for each agent. The `scripts/diagnose_personas.py` script should be used as the foundation for this, as it already verifies persona composition, configuration, agent preflight, and memory access without requiring live model calls.

## Test Plan

- Dry-run each agent startup without sending Telegram traffic.
- Verify each agent can load its persona and connect to the selected model backend.
- Confirm each bot replies through Telegram with the correct identity.
- Restart the VM services and confirm the agents come back online.
- Check that shared memory and MCP tools still work after restart.

## Assumptions

- The VM remains the live host for the bots.
- Telegram stays the primary user-facing interface.
- Hermes is treated as a reference behavior, not a runtime dependency.
- The Azure/OpenAI-compatible endpoint already validated in `sakthai run` remains available for the agents.

## SakTan Recovery Plan

- Keep `sakthai-telegram@saktan.service` as the primary SakTan process on the VM.
- Disable `hermes-gateway-saktan.service` so the same Telegram token is not polled twice.
- If SakTan must return to Hermes later, fix the Hermes runtime first by exporting or removing the missing `slash_confirm` import from the `tools` package.
- Verify the live path with `systemctl --user is-active sakthai-telegram@saktan.service` and a Telegram test message.
- Treat a `telegram.error.Conflict` or `ImportError: cannot import name 'slash_confirm' from 'tools'` as a sign that the Hermes path is still active.

## Guardrails, Eval, Sync & Persona Handoff

### Summary

Implement five local-first features so the project's enterprise-style pitch
(guardrails, MLOps eval, multi-agent orchestration, secret-scan remediation,
cross-session memory sync) describes real, tested code rather than aspirational
claims. No cloud SDK dependencies (no Model Armor/Defender XDR/Vertex AI calls)
— everything stays local-first per this repo's architecture. Full design lives
at `C:\Users\beern\.claude\plans\hashed-forging-coral.md`.

### Phases

- [x] 2026-07-03 Phase 1: Memory sync pull path (`sakthai/memory/sync.py`, `sakthai/cli/memory.py`)
- [x] 2026-07-03 Phase 2: Local model eval/MLOps logging (`sakthai/agent/eval.py`, `loop.py`, `config.py`)
- [/] Phase 3: Callback guardrails (`sakthai/agent/guardrails.py`, `loop.py`) — paused before writing guardrails.py; next step is designing `GuardrailPolicy`/`DEFAULT_PRE_RULES`/`DEFAULT_POST_RULES` per the design doc, then threading `policy` through `_execute_tool` → `_process_tool_uses` → `_dispatch_tool_calls` → `run_agent`, then tests in `tests/test_guardrails.py` + `tests/test_agent_loop.py`.
- [ ] Phase 4: Persona-aware agent handoff (`sakthai/agent/persona.py`, `tools.py`, `config.py`)
- [ ] Phase 5: Secret-scan remediation tool + CI job restoration (`sakthai/agent/secretscan.py`, `.github/workflows/ci.yml`)

### Test Plan

- Each phase ships with its own unit tests (see design doc for exact files).
- Cross-cutting: `uv run ruff check`, `uv run mypy sakthai` (strict), `uv run bandit`,
  `uv run pytest tests/ -q` with coverage ≥85% before considering this done.

### Assumptions

- Personas already run isolated `memory.db` files in production
  (`infra/vm-agents/sakthai-agent-run.sh` sets `SAKTHAI_HOME=$HOME/.sakthai/$AGENT`).
- The gitleaks CI job described in CLAUDE.md/docs/SECURITY.md does not currently
  exist in `.github/workflows/ci.yml` at HEAD — Phase 5 restores it.
- This section is independent of the Hermes-Free VM Deployment Plan above; do
  not conflate the two.
