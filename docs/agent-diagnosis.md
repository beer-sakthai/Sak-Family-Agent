# Six-Agent Standalone Run Checklist

## Summary

This repository now reflects the full six-agent Sak Family roster:
SakKing, SakThai, SakSee, SakSit, SakTan, and SakJules.

The current state is:

- the shared persona and export scaffolding is in place for all six agents;
- the runtime config tree lives under `personas/<persona>/config/`;
- all six personas run standalone via `sakthai`;
- the standalone export/build path exists for each persona.

## Current Read

| Agent | Identity | Runtime | Standalone | Tools / MCP | Docs |
|---|---:|---:|---:|---:|---:|
| SakKing | 5 | 5 | 5 | 5 | 5 |
| SakThai | 5 | 5 | 5 | 5 | 5 |
| SakSee | 5 | 5 | 5 | 5 | 5 |
| SakSit | 5 | 5 | 5 | 5 | 5 |
| SakTan | 5 | 5 | 5 | 5 | 5 |
| SakJules | 5 | 5 | 5 | 5 | 5 |

## Runtime Inventory

### Live runtime surfaces

| Area | Files | Why it matters |
|---|---|---|
| Live agent config tree | `personas/<persona>/config/` | Holds persona configs, model settings, and security guardrails. |
| Persona working files | `personas/<persona>/{SOUL,PLAN,CYCLE,MEMORY,HANDOFF,BACKPACK}.md` | Operational state and behavioral instructions per persona. |
| Deployment helpers | `Makefile`, `scripts/export_agent_repo.py`, `scripts/diagnose_personas.py` | Connect the persona tree to export and verification workflows. |

### Documentation surfaces

| Area | Files |
|---|---|
| Workspace guidance | `README.md`, `CLAUDE.md` |
| Shared identity docs | `docs/SOUL.md`, `docs/USER.md`, `docs/OPERATING_CONTRACT.md` |
| Runtime notes | `docs/runtimes.md` |
| Product delivery | `product/PLAN.md`, `product/TODO.md` |

## Standalone Run Checklist

Use this as the minimum “can I run this agent by itself?” check.

### SakKing

- Confirm `personas/sakking/SOUL.md` and `personas/sakking/config/` exist.
- Confirm shared memory access is available.

### SakThai

- Confirm `personas/sakthai/SOUL.md` and `personas/sakthai/config/` exist.
- Confirm Hugging Face access is configured.
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
- Confirm local Ollama access is configured.
- Confirm shared memory access is available.

### SakJules

- Confirm `personas/sakjules/SOUL.md` and `personas/sakjules/config/` exist.
- Confirm GitHub/MCP and automation access are configured.
- Confirm shared memory access is available.

## Diagnosis

The family is structurally sound, but the highest-value cleanup areas are:

1. keep the six-agent roster consistent everywhere;
2. keep the standalone export path honest for all personas;
3. avoid drifting runtime docs across the workspace;
4. keep the product tracker focused on active delivery work, not historical notes.

## Practical Read

- SakKing: orchestrator.
- SakThai: lead, Hugging Face specialist.
- SakSee: web and browser specialist.
- SakSit: social/content specialist.
- SakTan: ops helper, local Ollama specialist.
- SakJules: automation and CI/CD master.
