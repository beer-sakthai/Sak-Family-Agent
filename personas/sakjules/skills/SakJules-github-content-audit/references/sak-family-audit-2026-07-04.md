# Sak-Family-Agent Audit (2026-07-04)

Concrete example of auditing a 6-agent family monorepo for Beer (`beer-sakthai`).

## Repo Info

| Field | Value |
|-------|-------|
| Owner/Repo | `beer-sakthai/Sak-Family-Agent` |
| Branch | `main` |
| Language | Python |
| Size | ~72MB |
| Visibility | Public |

## The 6 Sak Family Agents

| # | Agent | Handle | Role | State |
|---|-------|--------|------|-------|
| 1 | SakKing | `@SakKing_Agent_bot` | Lead & Orchestrator | ✅ deployed |
| 2 | SakThai | `@SakThai_Agent_bot` | Master of Hugging Face | ✅ deployed |
| 3 | SakSee | `@SakSee_Agent_bot` | Master of Web (Playwright) | 🚧 pending |
| 4 | SakSit | `@SakSit_Agent_bot` | Master of Social Media | ✅ deployed |
| 5 | SakTan | `@SakTan_Agent_bot` | Daily Ops Helper | ✅ deployed |
| 6 | SakJules | `@SakJules_Agent_bot` | Master of Automation & CI/CD | 🚧 pending |

**Models:** All use `sakthai-resource` Azure AI Foundry backend via OpenAI-compatible `/openai/v1` API. Models vary by agent: `gpt-4o-mini`, `gpt-5.4-mini`, `Phi-4-mini-reasoning`, `model-router`.

**Secrets:** Azure Key Vault + VM managed identity (see `infra/vm-agents/sakthai-agent-run.sh`). No static secret files on disk.

## Persona Directory Structure

Each agent = one directory under `personas/<agent>/`:

```
personas/
├── sakking/     → SOUL.md (5.9KB), config/, skills/
├── sakthai/     → SOUL.md (3.9KB), config/, skills/
├── saksee/      → SOUL.md (3.5KB), config/, skills/
├── saksit/      → SOUL.md (3.7KB), config/, skills/
├── saktan/      → SOUL.md (3.6KB), config/, skills/
├── sakjules/    → SOUL.md (3.4KB), config/, skills/
└── servicequotebot/ → SOUL.md, config/, skills/ (bonus persona)
```

## Key Infrastructure Files

| File | Purpose |
|------|---------|
| `infra/vm-agents/sakthai-agent-run.sh` | VM startup: fetches secrets from KV, launches all bots |
| `infra/vm-agents/systemd/sakthai-telegram@.service` | systemd unit template (one per agent) |
| `infra/vm-agents/env-templates/<agent>.env.example` | Per-agent env templates (7 total) |
| `.github/workflows/ci.yml` | Main CI pipeline |
| `.github/workflows/super-linter.yml` | Linting |
| `.github/workflows/asset-monitor.yml` | Uptime monitoring |
| `.Jules/` | Jules-specific config (palette.md, README.md) |
| `.jules/` | Jules sentinel/monitor files (bolt.md, sentinel.md) |

## Training Infrastructure

| Path | Contents |
|------|----------|
| `training/hf-jobs/` | `build_toolcalling_dataset.py`, `train_toolcalling_lora.py`, `train_persona_lora.py` |
| `training/serving/` | `deploy_hf_endpoint.py`, `export_ollama.py`, `eval_toolcalling.py` |
| `infra/sakthai-training-space/` | Dockerfile, deepspeed configs, SFT dataset (JSONL) |

## Handoff Pattern for SakJules

SakJules is Master of Automation & CI/CD (pending). Handoff includes:

1. **CI/CD workflows** — 18 files in `.github/workflows/` (lint, test, security, deploy, monitor)
2. **Deployment automation** — `infra/vm-agents/sakthai-agent-run.sh` + systemd unit
3. **Training pipelines** — HF Jobs training scripts (auto-trigger on dataset update)
4. **Env templates** — all 7 `.env.example` files (one per agent)
5. **Missing automation** — no automated deploy-on-push, no agent health dashboard, no automated dataset→training pipeline trigger

## SakThai's Hugging Face Assets

Models under `Nanthasit` org:
- `sakthai-context-0.5b` (base model for LoRA)
- `sakthai-coder-3b`
- `sakthai-tts`
- `VibeVoice-1.5B`

Datasets:
- `SimpleToolCalling`
- `sakthai-toolcalling-v1`
- `sakthai-combined-v1`
- `sakthai-combined-v3`

## Tools Used in This Audit

- Composio GitHub toolkit: `GITHUB_LIST_REPOSITORIES_FOR_THE_AUTHENTICATED_USER`, `GITHUB_GET_A_REPOSITORY`
- Composio workbench: `proxy_execute("GET", "/repos/o/r/contents/path", "github")` + `base64.b64decode()`
- Direct GitHub API calls via `requests` in workbench (parallelizable with ThreadPoolExecutor)