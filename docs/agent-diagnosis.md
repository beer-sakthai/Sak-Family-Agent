# Six-Agent Diagnosis Report

## Summary

This repository now reflects the full six-agent Sak Family roster:
SakKing, SakThai, SakSee, SakSit, SakTan, and SakJules.

The current diagnosis is that the identity and persona sources are broadly in
shape, but the repo still needed one cleanup pass for consistency:

- `5_agents_summary.md` was stale and omitted SakJules.
- `infra/hermes-agents/shared/agents-roster.md` and `SYNC_GUIDE.md` still
  reflected a five-agent runtime.
- SakTan and SakJules need explicit standalone-run callouts because they lean
  harder on the Hermes profile layer than the others.
- The standalone build tree now includes profile scaffolding for both SakTan
  and SakJules, so the export/composition path is covered for all six personas.

## Benchmark Rubric

Scores are 1-5, where 5 is best.

| Agent | Identity | Runtime | Standalone | Tools / MCP | Docs | Notes |
|---|---:|---:|---:|---:|---:|---|
| SakKing | 5 | 4 | 4 | 5 | 4 | Strong lead/orchestrator coverage; reserved `default` profile is the special case. |
| SakThai | 5 | 4 | 4 | 5 | 4 | Cleanly documented Hugging Face specialist; runtime depends on Anthropic/Ollama-cloud auth. |
| SakSee | 5 | 4 | 4 | 5 | 4 | Web/browser stack is clear and well scoped. |
| SakSit | 5 | 4 | 4 | 4 | 4 | Social-media role is coherent, but the runtime depends on HF Spaces plus the Modal sandbox. |
| SakTan | 5 | 3 | 4 | 3 | 3 | The helper role is clear, and the export/composition path now verifies its standalone tree. |
| SakJules | 5 | 3 | 4 | 4 | 3 | Identity is now correct, and the export/composition path now verifies its standalone tree. |

## Hermes Dependency Inventory

The repo core is already Hermes-free in the sense that the `sakthai/` package
implements the provider-agnostic CLI, memory, and MCP surfaces. The Hermes
surface lives around deployment, export, and documentation.

There is no top-level `telegram/` package in this checkout, so the Telegram
integration item in `product/todo.md` maps to the `sakthai/telegram/` package
rather than a repo-root module.

### Runtime-critical Hermes surfaces

| Area | Files | Why it matters |
|---|---|---|
| Live Hermes deployment | `infra/hermes-agents/` | This is the live Telegram gateway/runtime backup tree, including profile configs, deploy tooling, and user services. |
| Profile launchers | `infra/hermes-agents/systemd/hermes-gateway*.service` | These are the actual service definitions that start each Hermes-backed bot. |
| Default/profile config | `infra/hermes-agents/default/`, `infra/hermes-agents/profiles/{saksee,sakthai,saksit,saktan,sakjules}/` | These hold the per-agent Hermes config/state that the deployment scripts load. |
| Deployment helpers | `Makefile` (`deploy-hermes`, `doctor-hermes`) | These commands are explicit Hermes entry points for deployment and diagnostics. |
| Export helpers | `scripts/export_agent_repo.py`, `scripts/diagnose_personas.py` | These scripts still know about Hermes profile paths and service conventions. |

### Documentation-only Hermes references

| Area | Files | Why it matters |
|---|---|---|
| Root orientation docs | `README.md`, `CLAUDE.md` | These explain the family layout, standalone export behavior, and Hermes relationship to the repo. |
| Shared identity docs | `docs/SOUL.md`, `docs/agent-diagnosis.md` | These describe the six-agent roster and the standalone run checklist. |
| Hermes runtime docs | `infra/hermes-agents/README.md`, `infra/hermes-agents/SYNC_GUIDE.md` | These are deployment notes for the Hermes-backed path and can be rewritten once the non-Hermes path is complete. |
| Runtime guidance docs | `docs/plugins.md`, `docs/integrations.md`, `docs/sakthai-live-connect-plan.md` | These still document Hermes-backed and mixed runtime recipes. |

### Removal candidates after migration

- `Makefile` Hermes targets can be removed once the replacement launch path is
  stable and tested.
- `infra/hermes-agents/README.md` and `infra/hermes-agents/SYNC_GUIDE.md` can
  be folded into the new standalone runtime docs after the transition.
- `scripts/export_agent_repo.py` can be simplified once the standalone export
  path no longer needs Hermes profile copies.

### Immediate next step

The next migration step is the smallest safe replacement path: define a local
non-Hermes bootstrap that can run the core agent loop with explicit config and
no profile loader dependency.

### Smallest non-Hermes bootstrap

1. Install the local workspace dependencies with `uv sync --all-extras`.
2. Validate the agent without spending tokens:
   `sakthai run "<task>" --dry-run --no-mcp`.
3. Run the core loop without Hermes profile loading:
   `sakthai run "<task>" --no-mcp --fast --stateless`.
4. Add external tools only through `~/.sakthai/mcp.json`; do not require
   `~/.hermes/` for the bootstrap path.
5. Use this path as the baseline smoke route before introducing any Telegram or
   runtime-wrapper seam.

### Runtime seam completed

The first executable seam is the Telegram workflow executor:

- it now reads available workflows from the package-configured `skills/` tree,
  not the current working directory;
- it launches the agent with `sys.executable`, not a hardcoded `python`;
- its command construction is covered by focused tests so the seam stays
  portable across local shells and service launches.

## Standalone Requirements

### SakKing

- `infra/hermes-agents/default/SOUL.md`
- `infra/hermes-agents/default/config.yaml`
- Playwright, Chrome DevTools, Hugging Face, and HF media MCP access
- Shared memory and the common skill library

### SakThai

- `personas/sakthai/SOUL.md`
- `personas/sakthai/config/`
- Hugging Face MCP access
- Shared memory and the common skill library

### SakSee

- `personas/saksee/SOUL.md`
- `personas/saksee/config/`
- Playwright and Chrome DevTools MCP access
- Shared memory and the common skill library

### SakSit

- `personas/saksit/SOUL.md`
- `personas/saksit/config/`
- Hugging Face Spaces for image/video generation
- Modal-backed terminal sandbox for content workflows
- Shared memory and the common skill library

### SakTan

- `personas/saktan/SOUL.md`
- `personas/saktan/config/`
- `infra/hermes-agents/profiles/saktan/SOUL.md`
- `infra/hermes-agents/profiles/saktan/config.yaml`
- Gemini auth
- Hermes profile runtime wiring for daily ops
- Shared memory and the common skill library

### SakJules

- `personas/sakjules/SOUL.md`
- `personas/sakjules/config/`
- `infra/hermes-agents/profiles/sakjules/SOUL.md`
- `infra/hermes-agents/profiles/sakjules/config.yaml`
- Gemini auth
- GitHub MCP access
- Composio MCP access
- Hermes profile runtime wiring for repository stewardship
- Shared memory and the common skill library

## Standalone Run Checklist

Use this as the minimum “can I run this agent by itself?” check.

### SakKing

- Use the reserved `default` Hermes profile, not a `profiles/sakking/` folder.
- Confirm `infra/hermes-agents/default/SOUL.md` and `config.yaml` are present.
- Confirm the lead tool surface is wired for Playwright, Chrome DevTools,
  Hugging Face, and HF media generation.
- Confirm shared memory access is available.

### SakThai

- Confirm `personas/sakthai/SOUL.md` and `personas/sakthai/config/` exist.
- Confirm Hugging Face MCP access is configured.
- Confirm shared memory access is available.

### SakSee

- Confirm `personas/saksee/SOUL.md` and `personas/saksee/config/` exist.
- Confirm Playwright and Chrome DevTools MCP access is configured.
- Confirm shared memory access is available.

### SakSit

- Confirm `personas/saksit/SOUL.md` and `personas/saksit/config/` exist.
- Confirm Hugging Face Spaces access for image/video generation is configured.
- Confirm the Modal-backed terminal sandbox path is available.
- Confirm shared memory access is available.

### SakTan

- Confirm `personas/saktan/SOUL.md` and `personas/saktan/config/` exist.
- Confirm `infra/hermes-agents/profiles/saktan/SOUL.md` and `config.yaml` exist.
- Confirm Gemini auth is available.
- Confirm the Hermes profile runtime wiring for daily ops is present.
- Confirm shared memory access is available.

### SakJules

- Confirm `personas/sakjules/SOUL.md` and `personas/sakjules/config/` exist.
- Confirm `infra/hermes-agents/profiles/sakjules/SOUL.md` and `config.yaml` exist.
- Confirm Gemini auth is available.
- Confirm GitHub MCP access is configured.
- Confirm Composio MCP access is configured.
- Confirm the Hermes profile runtime wiring for repository stewardship is present.
- Confirm shared memory access is available.

## Diagnosis

The family is structurally sound, but the highest-value fixes were documentation
alignment and explicit standalone run guidance.

Top issues:

1. The old five-agent summary was the most visible mismatch. That is now fixed.
2. SakJules needed to be treated as a first-class citizen everywhere the roster
   or skill table is shown. That is now explicit.
3. SakTan and SakJules are the two agents most likely to be misunderstood if
   the Hermes profile layer is not called out.
4. The export/composition path was exercised for both new standalone personas,
   which confirms the build tree stays honest.

## Practical Read

If you want the shortest possible operational view:

- SakKing: lead/orchestrator, strongest coding coverage, reserved profile.
- SakThai: Hugging Face specialist.
- SakSee: browser/web specialist.
- SakSit: social-media content specialist.
- SakTan: daily-ops helper.
- SakJules: GitHub repository steward.

That division is now reflected consistently across the family docs.
