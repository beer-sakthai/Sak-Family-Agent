# sakthai-hermes-agents

Configuration backup for **four** Telegram bots running on the
[Hermes agent framework](https://github.com/NousResearch) (`hermes_cli`),
installed at `~/.hermes/` on the host. **Config only — no secrets.** All API
keys / bot tokens / OAuth credentials live in `.env` and `auth.json` files that
are deliberately **excluded** (see `.gitignore`); use `env-templates/.env.example`
as the key list and fill real values locally.

## The Sak Family Agents

Each agent is a Hermes **profile** (its own `HERMES_HOME`), run as a systemd
**user** service. They share **one long-term memory brain** (Supermemory,
container `hermes`) but have distinct `SOUL.md` personas and separate live
sessions. Owner Telegram user id: `8618306046`.

> Profile dir names now **match** each agent's identity (renamed 2026-06-21),
> except **SakKing**, which stays on the reserved `default` profile (`default`
> cannot be renamed). Identity is whatever each profile's `SOUL.md` says.
> Current mapping:

| Telegram handle | Bot id | Profile (dir) | Identity | Role | Model | Service |
|---|---|---|---|---|---|---|
| `@sakthai_agent_v2_bot` | 8602426821 | `default` | **SakKing** | Lead & Orchestrator, Master of Code & Self-Healing | `claude-opus-4-8` (Anthropic) | `hermes-gateway.service` |
| `@sakthai_v1_bot` | 8773953106 | `profiles/sakthai` | **SakThai** | Master of Hugging Face | `deepseek-v3.1:671b` (Ollama Cloud) + `gpt-oss:120b` fallback | `hermes-gateway-sakthai.service` |
| `@saksee_bot` | 8315145484 | `profiles/saksee` | **SakSee** | Master of Web | `minimax-m3` (Ollama Cloud) + `gpt-oss:120b` fallback | `hermes-gateway-saksee.service` |
| `@saksit_agent_bot` | — | `profiles/saksit` | **SakSit** | Master of Social Media (IG) | `gemini-2.5-flash-lite` (Google) + `gpt-oss:120b` fallback | `hermes-gateway-saksit.service` |

> **Note:** "Hermes" is only the framework they run on — never an agent's name.
> Each agent identifies by the name in its `SOUL.md`.

## Skills per agent

| Agent | Skill Count | Unique / Notable Skills |
|-------|-------------|------------------------|
| **SakKing** | 18 | `devops`, `software-development` |
| **SakThai** | 20 | `audio-generation`, `tts-voice-generation` |
| **SakSee** | 23 | 6× `chrome-devtools-*` skills |
| **SakSit** | 19 | `ig_linkedin_growth_assistant` |

All agents share a common base of skills: `apple`, `autonomous-ai-agents`,
`computer-use`, `creative`, `data-science`, `dogfood`, `email`, `github`,
`media`, `mlops`, `note-taking`, `productivity`, `research`, `smart-home`,
`social-media`, `software-development`, `yuanbao`.

## MCP servers (per profile)

All four profiles connect to:

| MCP Server | URL / Transport | Status |
|------------|-----------------|--------|
| **supermemory** | `https://mcp.supermemory.ai/mcp` | ✅ Active |
| **zapier** | `${ZAPIER_MCP_URL}` (embedded token) | ✅ Active |
| **github** | `https://api.githubcopilot.com/mcp/` | ⚠️ PAT needs refresh |
| **huggingface** | `https://huggingface.co/mcp` | ✅ Active |
| **composio** | `https://connect.composio.dev/mcp` | ✅ Active |

SakSee additionally connects to a `chrome-devtools` MCP server (npx-based).

## Plugins

| Agent | Plugin | Status |
|-------|--------|--------|
| **SakSit** | `nanobanana` | ✅ Installed & enabled |

## Layout in this repo

```
default/{SOUL.md,config.yaml}              → ~/.hermes/{SOUL.md,config.yaml}
profiles/<name>/{SOUL.md,config.yaml}      → ~/.hermes/profiles/<name>/...
profiles/<name>/cron/jobs.json             → ~/.hermes/profiles/<name>/cron/jobs.json
                                             (scheduled-job DEFINITIONS only; runtime
                                              state + delivery origin stripped)
shared/agents-roster.md                    → ~/.hermes/shared/agents-roster.md
                                             (symlinked as AGENTS.md into each profile)
systemd/*.service                          → ~/.config/systemd/user/*.service
env-templates/.env.example                 → fill values → ~/.hermes[/profiles/<name>]/.env
```

## Restore / apply on a host

1. Copy files to the paths above (and `systemctl --user daemon-reload`).
2. Create each `.env` from `env-templates/.env.example` with real values
   (distinct `TELEGRAM_BOT_TOKEN` per bot — two bots **cannot** share one token,
   or Telegram returns 409 and neither replies).
3. Authenticate providers: `hermes auth ...` / `modal setup` (writes `~/.modal.toml`).
4. In each profile, symlink the roster as context:
   `ln -s ../../shared/agents-roster.md ~/.hermes/profiles/<name>/AGENTS.md`
5. `systemctl --user enable --now hermes-gateway*.service`.
6. (Optional) Restore scheduled jobs: copy `profiles/<name>/cron/jobs.json` into
   `~/.hermes/profiles/<name>/cron/`. These are definitions only — Hermes
   regenerates runtime state and re-binds delivery `origin` on first fire. Verify
   with `hermes --profile <name> cron list`.

## Hardening notes (already baked into the configs here)

- Terminal/code execution is sandboxed via **Modal** (`terminal.backend: modal`)
  — needs `MODAL_TOKEN_ID`/`MODAL_TOKEN_SECRET`.
- Manual approvals + destructive-slash confirmation on.
- Bots locked to the single owner Telegram id.

## Host constraints

The host is small (WSL2, ~3.6 GB RAM, no GPU) — **local LLMs are not viable**
(Hermes' prompt needs ~33k tokens of context; even a tiny model's KV cache for
that exceeds available RAM). Hence cloud models (Anthropic, Google Gemini,
Ollama Cloud). Ollama Cloud's free tier has a **weekly token cap**, which is why
the Ollama-backed bots carry a `fallback_model`.
