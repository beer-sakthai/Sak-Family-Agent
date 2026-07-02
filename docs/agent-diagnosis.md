# Six-Agent Standalone Run Checklist

## Summary

This repository now reflects the full six-agent Sak Family roster:
SakKing, SakThai, SakSee, SakSit, SakTan, and SakJules.

The current state is:

- the shared persona and export scaffolding is in place for all six agents;
- the runtime config tree lives under `infra/hermes-agents/`;
- SakTan and SakJules still rely on the runtime profile layer for their live configuration;
- the standalone export/build path exists for each persona.

## Current Read

| Agent | Identity | Runtime | Standalone | Tools / MCP | Docs |
|---|---:|---:|---:|---:|---:|
| SakKing | 5 | 4 | 4 | 5 | 4 |
| SakThai | 5 | 4 | 4 | 5 | 4 |
| SakSee | 5 | 4 | 4 | 5 | 4 |
| SakSit | 5 | 4 | 4 | 4 | 4 |
| SakTan | 5 | 3 | 4 | 3 | 3 |
| SakJules | 5 | 3 | 4 | 4 | 3 |

## Runtime Inventory

### Live runtime surfaces

| Area | Files | Why it matters |
|---|---|---|
| Live agent config tree | `infra/hermes-agents/` | Holds live profile configs, deploy tooling, and service definitions. |
| Service launchers | `infra/hermes-agents/systemd/*.service` | Start each live bot/profile on the host. |
| Default/profile configs | `infra/hermes-agents/default/`, `infra/hermes-agents/profiles/{saksee,sakthai,saksit,saktan,sakjules}/` | Store the live persona/config payloads loaded by deployment scripts. |
| Deployment helpers | `Makefile`, `scripts/export_agent_repo.py`, `scripts/diagnose_personas.py` | Connect the config tree to export and verification workflows. |

### Documentation surfaces

| Area | Files |
|---|---|
| Workspace guidance | `README.md`, `CLAUDE.md`, `GEMINI.md` |
| Shared identity docs | `docs/SOUL.md`, `docs/USER.md`, `docs/OPERATING_CONTRACT.md` |
| Runtime notes | `infra/hermes-agents/README.md` |
| Product delivery | `product/PLAN.md`, `product/todo.md` |

## Standalone Run Checklist

Use this as the minimum “can I run this agent by itself?” check.

### SakKing

- Use the reserved `default` profile.
- Confirm `infra/hermes-agents/default/SOUL.md` and `config.yaml` exist.
- Confirm shared memory access is available.

### SakThai

- Confirm `personas/sakthai/SOUL.md` and `personas/sakthai/config/` exist.
- Confirm Hugging Face MCP access is configured.
- Confirm shared memory access is available.

### SakSee

- Confirm `personas/saksee/SOUL.md` and `personas/saksee/config/` exist.
- Confirm browser tooling access is configured.
- Confirm shared memory access is available.

### SakSit

- Confirm `personas/saksit/SOUL.md` and `personas/saksit/config/` exist.
- Confirm the content-generation tooling path is available.
- Confirm shared memory access is available.

### SakTan

- Confirm `personas/saktan/SOUL.md` and `personas/saktan/config/` exist.
- Confirm `infra/hermes-agents/profiles/saktan/SOUL.md` and `config.yaml` exist.
- Confirm the live runtime wiring for daily ops is present.
- Confirm shared memory access is available.

### SakJules

- Confirm `personas/sakjules/SOUL.md` and `personas/sakjules/config/` exist.
- Confirm `infra/hermes-agents/profiles/sakjules/SOUL.md` and `config.yaml` exist.
- Confirm GitHub/MCP and automation access are configured.
- Confirm shared memory access is available.

## Diagnosis

The family is structurally sound, but the highest-value cleanup areas are:

1. keep the six-agent roster consistent everywhere;
2. keep the standalone export path honest for SakTan and SakJules;
3. avoid drifting runtime docs across the workspace;
4. keep the product tracker focused on active delivery work, not historical notes.

## Practical Read

- SakKing: lead/orchestrator, reserved default profile.
- SakThai: Hugging Face specialist.
- SakSee: web and browser specialist.
- SakSit: social/content specialist.
- SakTan: ops helper, runtime-profile dependent.
- SakJules: automation and CI/CD, runtime-profile dependent.
