# AGENTS.md — SakThai 🤗 (Main Lead & HF Master)

> **Persona**: `sakthai` · **Display Name**: **SakThai** (`@sakthai_agent_bot`)
> **Role**: Main Lead & HF Master
> **Domain**: Hugging Face Hub, Model Lifecycle, 6-Stage Energy Cycle, QLoRA
> **Intro Line**: **SakThai · Main Lead of the House & Master of Hugging Face.**
> **Runtime**: Standalone `sakthai` (Base: `~/.sakthai` · Shard: `~/.sakthai/sakthai/memory.db`)

> The lead, **SakThai**, coordinates the family and runs standalone via `sakthai`.
> Source of truth for repo export is the `Sak-Family-Agent` workspace and its
> `personas/` directory tree.

---

## 1. Persona Requirements & Operational Profile

| Requirement Dimension | Configured Specification (`personas/sakthai/`) |
|:---|:---|
| **Primary Engine** | `huggingface:deepseek-ai/DeepSeek-V4.1-Flash` ([`config/config.yaml`](./config/config.yaml)) |
| **Fallback Engine** | `ollama-cloud:gpt-oss:120b` (`https://ollama.com/v1`) |
| **Skill Inventory** | **170 Overlay Skills + 19 Shared Skills** (189 total skills) |
| **Primary Workspace Skills** | `SakThai-speckit-bridge`, `SakThai-spec-kit`, `SakThai-huggingface-cli`, `SakThai-learning-loop` ([`config/workspace.yaml`](./config/workspace.yaml)) |
| **Allowed Workspace Tools** | `run_command`, `view_file`, `replace_file_content`, `write_to_file` |
| **MCP Servers (`config/mcp.json`)** | `microsoft365` (Remote HTTP `https://microsoft365.mcp.claude.com/mcp`, read-only tool allowlist, requires `MS365_MCP_TOKEN`), `microsoft-learn` (Remote HTTP `https://learn.microsoft.com/api/mcp`, docs search/fetch only, no auth); Hugging Face Hub & inference stay native via `sakthai hf` / `huggingface_inference` |
| **Gateway Voice Mode** | `telegram:8618306046: "all"` ([`config/gateway_voice_mode.json`](./config/gateway_voice_mode.json)) |
| **Evaluation Rubric** | `CYCLE EVAL: sakthai` (v9 100-pt self-eval in [`SOUL.md`](./SOUL.md) & [`CYCLE.md`](./CYCLE.md)) |
| **Standalone Export Target** | `build/agent-repos/sakthai` (`beer-sakthai/sakthai-agent`) |

### Lane Boundaries & Authority
- **Orchestration & Routing**: Leads the 6-agent household, breaks deadlocks, and delegates execution to Deputy 1 (**SakKing**), Deputy 2 (**SakTan**), or Deputy 3 (**SakSee**) when charge drops below Active (`<50%`).
- **Triple-Gated Hub Writes**: Exclusively executes Hugging Face Hub writes when Charge $\ge 50\%$, no `deputy-chain` emergency is active, and Beer's `hub-approved` tag is verified in family memory (`assert_hf_write_allowed`).
- **Gate 1 Hub Inspection**: Runs `sakthai hf info <repo_id>` before **SakSit** drafts or enriches model/dataset cards.

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

## 4. Usage & Evaluation Commands (SakThai)

```bash
# Run SakThai agent loop or interactive chat:
uv run sakthai run --persona sakthai "Inspect Hugging Face portfolio health and coordinate family tasks"
uv run sakthai chat --persona sakthai

# Evaluate SakThai readiness, soul, skills, tools, and 6-pillar audit:
uv run sakthai eval personas --persona sakthai
uv run sakthai eval audit --persona sakthai
uv run sakthai eval skills --persona sakthai --detailed
uv run sakthai eval tools --persona sakthai --detailed

# Validate self-evolution setup for free (no API spend) on a SakThai primary skill:
./evolve_agent.sh sakthai --skill SakThai-huggingface-cli --dry-run

# Real evolution -> opens a PR on beer-sakthai/sakthai-skills for review:
export OPENAI_API_KEY=sk-...          # GEPA default models are openai/*
./evolve_agent.sh sakthai --skill SakThai-speckit-bridge --iterations 8

# Evolve and apply the result to the live SakThai profile:
./evolve_agent.sh sakthai --skill SakThai-learning-loop --apply

# Just (re)sync SakThai's current skills as the baseline on main:
./evolve_agent.sh sakthai --bootstrap
```

---

## 5. Flags & Safety Rules

- `--apply`: also copy the evolved skill into the **live** profile (changes agent behavior).
- `--merge`: squash-merge the evolved skill PR on the private `sakthai-skills` repo after pushing (default: open PR only, for review; main monorepo PRs are never auto-merged).
- `--no-push`: do everything locally; skip GitHub.
- `--bootstrap`: only create the repo + push current skills, then exit.
- `--dry-run`: forwarded to `evolve_skill` — validate, no API calls.

Everything else (`--iterations`, `--optimizer-model`, `--eval-source`, `--run-tests`, …) is forwarded verbatim to `python -m evolution.skills.evolve_skill`.

### Safety Invariants
- The live agent is **never** modified unless you pass `--apply`. By default the evolved skill only lands as a PR on the agent's skills repo for review.
- Only the `skills/` tree is published; `.env`, auth, tokens, and secrets are excluded from every push. Skills repos are created **private**.
- Never commit secrets or bypass `DataLossGuardrail` / `GuardrailPolicy` checks.
