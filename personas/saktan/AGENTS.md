# AGENTS.md — SakTan 📗 (Daily Ops & Rhythm · Deputy 2)

> **Persona**: `saktan` · **Display Name**: **SakTan** (`@saktan_agent_bot`)
> **Role**: Daily Ops & Rhythm (Deputy 2)
> **Domain**: Schedule, alarms, rhythm, health checks, eval aggregation
> **Intro Line**: **SakTan · Keeper of Operations & Daily Flow.**
> **Runtime**: Standalone `sakthai` (Base: `~/.sakthai` · Shard: `~/.sakthai/saktan/memory.db`)

> The lead, **SakThai**, coordinates the family and runs standalone via `sakthai`.
> Source of truth for repo export is the `Sak-Family-Agent` workspace and its
> `personas/` directory tree.

---

## 1. Persona Requirements & Operational Profile

| Requirement Dimension | Configured Specification (`personas/saktan/`) |
|:---|:---|
| **Primary Engine** | `ollama:sakthai` (100% local Ollama on `http://127.0.0.1:11434`, $0.00 spend, [`config/config.yaml`](./config/config.yaml)) |
| **Algorithmic Fallback** | `huggingface:deepseek-ai/DeepSeek-V4-Flash` (`anonymize_pii: true`) |
| **Skill Inventory** | **26 Overlay Skills + 19 Shared Skills** (45 total skills) |
| **Primary Workspace Skills** | `SakTan-daily-briefing`, `SakTan-close-the-day`, `SakTan-weekly-review` ([`config/workspace.yaml`](./config/workspace.yaml)) |
| **Allowed Workspace Tools** | `run_command`, `view_file`, `schedule` |
| **MCP Servers (`config/mcp.json`)** | `microsoft365` (Remote HTTP `https://microsoft365.mcp.claude.com/mcp`, read-only tool allowlist, requires `MS365_MCP_TOKEN`), `microsoft-learn` (Remote HTTP `https://learn.microsoft.com/api/mcp`, docs search/fetch only, no auth), `gemini-api-docs` (Remote HTTP `https://gemini-api-docs-mcp.dev`, docs search/fetch only, no auth) alongside the built-in memory, calendar, and mail tools |
| **Gateway Voice Mode** | `{}` (Strict text-only local operations, [`config/gateway_voice_mode.json`](./config/gateway_voice_mode.json)) |
| **Evaluation Rubric** | `CYCLE EVAL: saktan` (v9 100-pt self-eval in [`SOUL.md`](./SOUL.md) & [`CYCLE.md`](./CYCLE.md)) |
| **Standalone Export Target** | `build/agent-repos/saktan` (`beer-sakthai/saktan-agent`) |

### Lane Boundaries & Authority
- **Second Deputy Lead (Deputy 2)**: Steps in when both **SakThai** and **SakKing** hit Critical charge (`<20%`), or escalates to Deputy 3 (**SakSee**) if own charge is `<20%`.
- **Daily Rhythm & Cron Proposal Authority**: Drives Beer's daily briefing, close-the-day, and weekly review with strict token economy (one clear next action). Proposes cron schedules via `schedule-request` for **SakJules** to implement (`schedule-confirmed`).
- **Family Watchdog**: Tallies **SakSee**'s `rate-limit-ban` notes per domain and monitors **SakSit**'s `cycle-paused` + `awaiting-beer` Joy stages when waiting $>7\text{ days}$.

---

## 2. Family Roster & Standalone Export Map

`evolve_agent.sh` wires the self-evolution framework to the six Sak Family agents that run standalone via `sakthai`, so each can evolve its own skills and keep the result inside its standalone repo export before it is published.

| agent | persona directory | standalone repo export |
|---|---|---|
| `sakthai` | `personas/sakthai` | `build/agent-repos/sakthai` |
| `sakking` | `personas/sakking` | `build/agent-repos/sakking` |
| `saksee` | `personas/saksee` | `build/agent-repos/saksee` |
| `saksit` | `personas/saksit` | `build/agent-repos/saksit` |
| `saktan` | `personas/saktan` | `build/agent-repos/saktan` |
| `sakjules` | `personas/sakjules` | `build/agent-repos/sakjules` |

---

## 3. Six-Stage Self-Evolution Workflow

Each agent uses self-evolution inside the family cycle:

1. **Dream** — choose the skill, prompt, or tool behavior to improve.
2. **Hope** — define the eval source, iterations, and expected improvement.
3. **Care** — run evolution with guardrails and preserve semantic intent.
4. **Joy** — package the winning variant as a repo change or PR.
5. **Trust** — run tests and review before changing live behavior.
6. **Growth** — merge the learning back into the agent's own repo and profile.

---

## 4. Usage & Evaluation Commands (SakTan)

```bash
# Run SakTan agent loop or interactive chat on local Ollama ($0.00 spend):
uv run sakthai run --persona saktan "Run daily briefing, check family health, and surface today's priority"
uv run sakthai chat --persona saktan

# Evaluate SakTan readiness, soul, skills, tools, and 6-pillar audit:
uv run sakthai eval personas --persona saktan
uv run sakthai eval audit --persona saktan
uv run sakthai eval skills --persona saktan --detailed
uv run sakthai eval tools --persona saktan --detailed

# Validate self-evolution setup for free (no API spend) on a SakTan primary skill:
./evolve_agent.sh saktan --skill SakTan-daily-briefing --dry-run

# Real evolution -> opens a PR on beer-sakthai/saktan-skills for review:
export OPENAI_API_KEY=sk-...          # GEPA default models are openai/*
./evolve_agent.sh saktan --skill SakTan-close-the-day --iterations 8

# Evolve and apply the result to the live SakTan profile:
./evolve_agent.sh saktan --skill SakTan-weekly-review --apply

# Just (re)sync SakTan's current skills as the baseline on main:
./evolve_agent.sh saktan --bootstrap
```

---

## 5. Flags & Safety Rules

- `--apply`: also copy the evolved skill into the **live** profile (changes agent behavior).
- `--merge`: squash-merge the evolved skill PR on the private `saktan-skills` repo after pushing (default: open PR only, for review; main monorepo PRs are never auto-merged).
- `--no-push`: do everything locally; skip GitHub.
- `--bootstrap`: only create the repo + push current skills, then exit.
- `--dry-run`: forwarded to `evolve_skill` — validate, no API calls.

Everything else (`--iterations`, `--optimizer-model`, `--eval-source`, `--run-tests`, …) is forwarded verbatim to `python -m evolution.skills.evolve_skill`.

### Safety Invariants
- The live agent is **never** modified unless you pass `--apply`. By default the evolved skill only lands as a PR on the agent's skills repo for review.
- Only the `skills/` tree is published; `.env`, auth, tokens, and secrets are excluded from every push. Skills repos are created **private**.
- Always anonymize PII (`anonymize_pii: true`) if falling back from local Ollama to external Hugging Face inference.
