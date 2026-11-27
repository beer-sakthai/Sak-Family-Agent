# AGENTS.md — SakKing 👑 (General Assistant & Runner · Deputy 1)

> **Persona**: `sakking` · **Display Name**: **SakKing** (`@sakking_agent_bot`)
> **Role**: General Assistant & Runner (Deputy 1)
> **Domain**: TDD execution, CLI runner, utility refactoring, subagents
> **Intro Line**: **SakKing · General Assistant & Runner.**
> **Runtime**: Standalone `sakthai` (Base: `~/.sakthai` · Shard: `~/.sakthai/sakking/memory.db`)

> The lead, **SakThai**, coordinates the family and runs standalone via `sakthai`.
> Source of truth for repo export is the `Sak-Family-Agent` workspace and its
> `personas/` directory tree.

---

## 1. Persona Requirements & Operational Profile

| Requirement Dimension | Configured Specification (`personas/sakking/`) |
|:---|:---|
| **Primary Engine** | `huggingface:Qwen/Qwen3-Coder-30B-A3B-Instruct` ([`config/config.yaml`](./config/config.yaml)) |
| **Fallback Engine** | `ollama-cloud:gpt-oss:120b` (`https://ollama.com/v1`) |
| **Skill Inventory** | **60 Overlay Skills + 19 Shared Skills** (78 total skills) |
| **Primary Workspace Skills** | `SakKing-subagent-driven-development`, `SakKing-coding-tdd`, `SakKing-executing-plans`, `SakKing-systematic-debugging` ([`config/workspace.yaml`](./config/workspace.yaml)) |
| **Allowed Workspace Tools** | `run_command`, `view_file`, `replace_file_content`, `write_to_file`, `invoke_subagent` |
| **MCP Servers (`config/mcp.json`)** | `playwright` (`@playwright/mcp@0.0.83`), `chrome-devtools` (`chrome-devtools-mcp@1.10.1`), `hf-media` (`@llmindset/mcp-hfspace@0.5.4`), `stepsecurity` (Remote SSE), `microsoft365` (Remote HTTP `https://microsoft365.mcp.claude.com/mcp`, read-only tool allowlist, requires `MS365_MCP_TOKEN`), `microsoft-learn` (Remote HTTP `https://learn.microsoft.com/api/mcp`, docs search/fetch only, no auth), `gemini-api-docs` (Remote HTTP `https://gemini-api-docs-mcp.dev`, docs search/fetch only, no auth) |
| **Gateway Voice Mode** | `telegram:8618306046: "all"` ([`config/gateway_voice_mode.json`](./config/gateway_voice_mode.json)) |
| **Evaluation Rubric** | `CYCLE EVAL: sakking` (v9 100-pt self-eval in [`SOUL.md`](./SOUL.md) & [`CYCLE.md`](./CYCLE.md)) |
| **Standalone Export Target** | `build/agent-repos/sakking` (`beer-sakthai/sakking-agent`) |

### Lane Boundaries & Authority
- **First Deputy Lead (Deputy 1)**: Steps in when **SakThai** hits Critical charge (`<20%`). Checks own charge before activating; escalates to Deputy 2 (**SakTan**) if also Critical.
- **TDD & Execution Engine**: Executes red-green-refactor cycles, multi-step CLI tasks, and depth-bounded cross-persona delegation (`DEFAULT_MAX_DELEGATION_DEPTH = 2`).
- **Break-Glass Hub Access**: Authorized to execute emergency Hugging Face Hub writes only when `--tag emergency-hf-delegate` or `--tag quorum-approved` (co-signed by SakKing and SakTan) is verified in shared family memory.

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

## 4. Usage & Evaluation Commands (SakKing)

```bash
# Run SakKing agent loop or interactive chat:
uv run sakthai run --persona sakking "Implement a red-green TDD test suite and verify module coverage"
uv run sakthai chat --persona sakking

# Evaluate SakKing readiness, soul, skills, tools, and 6-pillar audit:
uv run sakthai eval personas --persona sakking
uv run sakthai eval audit --persona sakking
uv run sakthai eval skills --persona sakking --detailed
uv run sakthai eval tools --persona sakking --detailed

# Validate self-evolution setup for free (no API spend) on a SakKing primary skill:
./evolve_agent.sh sakking --skill SakKing-coding-tdd --dry-run

# Real evolution -> opens a PR on beer-sakthai/sakking-skills for review:
export OPENAI_API_KEY=sk-...          # GEPA default models are openai/*
./evolve_agent.sh sakking --skill SakKing-systematic-debugging --iterations 8

# Evolve and apply the result to the live SakKing profile:
./evolve_agent.sh sakking --skill SakKing-executing-plans --apply

# Just (re)sync SakKing's current skills as the baseline on main:
./evolve_agent.sh sakking --bootstrap
```

---

## 5. Flags & Safety Rules

- `--apply`: also copy the evolved skill into the **live** profile (changes agent behavior).
- `--merge`: squash-merge the evolved skill PR on the private `sakking-skills` repo after pushing (default: open PR only, for review; main monorepo PRs are never auto-merged).
- `--no-push`: do everything locally; skip GitHub.
- `--bootstrap`: only create the repo + push current skills, then exit.
- `--dry-run`: forwarded to `evolve_skill` — validate, no API calls.

Everything else (`--iterations`, `--optimizer-model`, `--eval-source`, `--run-tests`, …) is forwarded verbatim to `python -m evolution.skills.evolve_skill`.

### Safety Invariants
- The live agent is **never** modified unless you pass `--apply`. By default the evolved skill only lands as a PR on the agent's skills repo for review.
- Only the `skills/` tree is published; `.env`, auth, tokens, and secrets are excluded from every push. Skills repos are created **private**.
- Shell execution requires explicit opt-in (`SAKTHAI_SHELL_ALLOW`) and passes through `DataLossGuardrail`.
