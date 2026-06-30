# Hermes-agents history (the standalone repo is gone)

## Status

`infra/hermes-agents/` **is the sole source of truth** for the Hermes Telegram
bots. The former standalone `beer-sakthai/sakthai-hermes-agents` GitHub repo was
subtree-merged into this monorepo and then **deleted** — there is no upstream
left to sync from. Make all Hermes config changes directly here.

This file is retained only as a record of the final consolidation.

## What was merged (2026-06-29 session)

The standalone repo's work was applied into `infra/hermes-agents/`; all of the
following are present here now:

- `default/config.yaml` — HuggingFace model, MCP fleet, edge TTS BrianNeural
- `default/SOUL.md` — SakKing persona
- `profiles/*/config.yaml` + `profiles/*/SOUL.md` — canonical per-agent personas & voices
- `deploy.py` — automated config sync script
- `doctor.py` — workspace health diagnostics
- `.agents/AGENTS.md`, `.agents/skills/hermes-deploy/`, `.agents/skills/sak-tts-voices/`
- `env-templates/.env.example` — complete with HF_TOKEN, GITHUB_TOKEN, ZAPIER_MCP_URL, COMPOSIO_MCP_KEY

## Voice registry (canonical)

| Agent | Voice | Gender |
|-------|-------|--------|
| SakKing (default) | en-US-BrianNeural | Male |
| SakSee | en-US-AriaNeural | Female |
| SakThai | en-US-AndrewNeural | Male |
| SakSit | en-US-ChristopherNeural | Male |
| SakTan | en-US-GuyNeural | Male |

All agents: `tts.provider: edge`
