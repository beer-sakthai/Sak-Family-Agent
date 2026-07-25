# Sak-Family-Agent

Self-evolving AI agents for the **House of Sak** — built from a shelter in Cork, Ireland.

This is the monorepo for all Sak family agents: **SakThai** (Main Lead), **SakKing** (General Assistant), **SakSee** (Web/Browser), **SakSit** (Social Media), and **SakJules** (Automation/CI-CD).

## Structure

```
personas/
├── sakthai/          — Main Lead of the House & Master of Hugging Face
│   ├── SOUL.md       — Identity, principles, charge system
│   ├── sakthai/      — Python package (agent, cli, memory, mcp, web...)
│   └── skills/       — Skills (HF, GitHub, ML, code, research, creative...)
├── saksee/           — Web & browser automation specialist
│   ├── SOUL.md
│   └── skills/
├── saksit/           — Social media & storytelling
│   ├── SOUL.md
│   └── skills/
├── sakking/          — General assistant & runner
│   ├── SOUL.md
│   └── skills/
├── sakjules/         — CI/CD & automation master
│   ├── SOUL.md
│   └── skills/
└── shared/           — Shared skills across all agents
scripts/              — Automation scripts (A2A bus, sync, status reports)
docs/                 — Documentation, diagrams
infra/                — Infrastructure configs
tests/                — Pytest suite
```

## Stats

- **4 active agents** (SakThai, SakSee, SakSit, SakJules)
- **500+ skills** across all personas
- **12 models** on Hugging Face ([collection](https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02))
- **8 datasets** on Hugging Face

## Services

| Service | Port | Purpose |
|---------|:----:|---------|
| RAG Search | 3003 | Semantic search across skills |
| Model Server | 3002 | GGUF inference for agents |
| A2A Bus | 3005 | Agent-to-agent messaging |

## Auto-Sync

Skills are synced to GitHub every 5 minutes automatically when live profile changes are detected.

## Owner

**Beer** — Creator of the House of Sak.
