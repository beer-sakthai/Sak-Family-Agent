# 🚀 SakKing → SakJules: Automation Handoff

**From:** SakKing (Lead & Orchestrator)
**To:** SakJules (Master of Automation & CI/CD)
**Date:** 2026-07-04
**Status:** 🚧 Pending — your deployment is the next priority

---

## 1. Your Mission

As **Master of Automation & CI/CD**, you own the entire automation pipeline for the Sak Family. Your job is to make sure every agent is deployed, monitored, and updated without manual intervention.

---

## 2. What You Own

### 2.1 CI/CD Pipelines (`.github/workflows/`)

| Workflow | What It Does |
|----------|-------------|
| `ci.yml` | Run test suite on every push/PR |
| `super-linter.yml` | Code quality & style enforcement |
| `sonarcloud.yml` | Static analysis & code coverage |
| `asset-monitor.yml` | Check family URLs are live |
| `verify-assets.yml` | Asset integrity checks |
| `agent-self-evolution.yml` | Self-improvement pipeline |
| `auto-dependency-update.yml` | Keep dependencies fresh |
| `ossar.yml` / `pylint.yml` | Security scanning |

**→ Your job:** Keep these green. Fix broken workflows. Add new ones as needed.

### 2.2 Infrastructure Deployment (`infra/vm-agents/`)

| File | What It Does |
|------|-------------|
| `sakthai-agent-run.sh` | Startup script for all 6 Telegram bots on Azure VM |
| `systemd/sakthai-telegram@.service` | systemd service unit per bot |
| `env-templates/*.env.example` | One env template per agent |

**→ Your job:** Automate deployment so a `git push` redeploys the right agent.

### 2.3 Training Pipelines (`training/`)

| File | What It Does |
|------|-------------|
| `training/hf-jobs/build_toolcalling_dataset.py` | Build SFT datasets |
| `training/hf-jobs/train_toolcalling_lora.py` | LoRA fine-tuning |
| `training/hf-jobs/train_persona_lora.py` | Persona-specific fine-tuning |
| `training/serving/deploy_hf_endpoint.py` | Deploy HF Inference Endpoint |
| `training/serving/export_ollama.py` | Export to Ollama format |
| `infra/sakthai-training-space/Dockerfile` | HF Space container |
| `infra/sakthai-training-space/configs/deepspeed_zero2.json` | Training config |

**→ Your job:** Automate the training loop — when SakThai builds a new dataset, trigger training automatically.

### 2.4 Monitoring & Self-Healing

- `sakking-family-health-watchdog` — cron job checking every 30m (temp until you take over)
- `.jules/sentinel.md` — your sentinel config (review & activate)
- `.jules/bolt.md` — your bolt/emergency protocol

**→ Your job:** Take over monitoring from me. You're the automation master.

---

## 3. The 6 Agents — Deployment Status

| Agent | Handle | Status | Next Action |
|-------|--------|--------|-------------|
| 👑 **SakKing** | `@SakKing_Agent_bot` | ✅ Deployed | — |
| 🤗 **SakThai** | `@SakThai_Agent_bot` | ✅ Deployed | Training loop automation |
| 🌐 **SakSee** | `@SakSee_Agent_bot` | 🚧 Pending | Deploy when env ready |
| 📣 **SakSit** | `@SakSit_Agent_bot` | ✅ Deployed | — |
| 📗 **SakTan** | `@SakTan_Agent_bot` | ✅ Deployed | — |
| 🤖 **SakJules** | `@SakJules_Agent_bot` | 🚧 Pending | **Need to deploy you!** |

---

## 4. Priority: Deploy SakJules

1. Check `infra/vm-agents/env-templates/sakjules.env.example` for required env vars
2. Add `@SakJules_Agent_bot` Telegram token to Azure Key Vault
3. Add a systemd service entry matching the other agents
4. Run the deploy script with your persona profile

---

## 5. Key Files Reference

```
personas/sakjules/          → Your SOUL.md, config, skills
.Jules/                     → Your Jules config (palette, readme)
.jules/                     → Your sentinel & bolt protocols
infra/vm-agents/            → Deployment scripts & systemd units
.github/workflows/          → All CI/CD pipelines
training/hf-jobs/           → Training automation
docs/*.md                   → Shared documentation
```

---

*Handoff delivered by SakKing on 2026-07-04. Welcome to the family, SakJules. Let's automate everything.*
