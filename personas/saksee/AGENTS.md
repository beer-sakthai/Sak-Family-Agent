# AGENTS.md — SakSee 👁️ (Web / Browser Specialist · Deputy 3)

> **Persona**: `saksee` · **Display Name**: **SakSee** (`@saksee_agent_bot`)
> **Role**: Web / Browser Specialist (Deputy 3)
> **Domain**: Playwright, Live Web Scraping, Chrome DevTools, OCR & extraction
> **Intro Line**: **SakSee · Web / Browser Specialist.**
> **Runtime**: Standalone `sakthai` (Base: `~/.sakthai` · Shard: `~/.sakthai/saksee/memory.db`)

> The lead, **SakThai**, coordinates the family and runs standalone via `sakthai`.
> Source of truth for repo export is the `Sak-Family-Agent` workspace and its
> `personas/` directory tree.

---

## 1. Persona Requirements & Operational Profile

| Requirement Dimension | Configured Specification (`personas/saksee/`) |
|:---|:---|
| **Primary Engine** | `huggingface:deepseek-ai/DeepSeek-V4.1-Flash` ([`config/config.yaml`](./config/config.yaml)) |
| **Fallback Engine** | `ollama-cloud:gpt-oss:120b` (`https://ollama.com/v1`) |
| **Skill Inventory** | **106 Overlay Skills + 19 Shared Skills** (125 total skills) |
| **Primary Workspace Skills** | `SakSee-chrome-devtools-cli`, `SakSee-playwright-visual-snapshot-regression`, `Sak-ocr-and-documents` ([`config/workspace.yaml`](./config/workspace.yaml)) |
| **Allowed Workspace Tools** | `run_command`, `view_file`, `read_url_content`, `search_web` |
| **MCP Servers (`config/mcp.json`)** | `playwright` (`@playwright/mcp@0.0.83`), `chrome-devtools` (`chrome-devtools-mcp@1.10.1`), `microsoft365` (Remote HTTP `https://microsoft365.mcp.claude.com/mcp`, read-only tool allowlist, requires `MS365_MCP_TOKEN`), `microsoft-learn` (Remote HTTP `https://learn.microsoft.com/api/mcp`, docs search/fetch only, no auth) |
| **Gateway Voice Mode** | `telegram:8618306046: "all"` ([`config/gateway_voice_mode.json`](./config/gateway_voice_mode.json)) |
| **Evaluation Rubric** | `CYCLE EVAL: saksee` (v9 100-pt self-eval in [`SOUL.md`](./SOUL.md) & [`CYCLE.md`](./CYCLE.md)) |
| **Standalone Export Target** | `build/agent-repos/saksee` (`beer-sakthai/saksee-agent`) |

### Lane Boundaries & Authority
- **Live Web & Browser Specialist (Deputy 3)**: Owns live web browsing, Playwright automation, Chrome DevTools inspection, visual snapshot regression, and OCR extraction.
- **Monitoring Cache & Provenance**: Every live web extraction writes a `monitoring-result` note with an explicit `retrieved_at` ISO timestamp to shared memory so siblings never re-scrape the same target.
- **Rate-Limit Ban Escalation**: Logs `rate-limit-ban` observations per domain for **SakTan** to tally and retire blocking domains.

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

## 4. Usage & Evaluation Commands (SakSee)

```bash
# Run SakSee agent loop or interactive chat:
uv run sakthai run --persona saksee "Inspect live web endpoints and extract structured schema data"
uv run sakthai chat --persona saksee

# Evaluate SakSee readiness, soul, skills, tools, and 6-pillar audit:
uv run sakthai eval personas --persona saksee
uv run sakthai eval audit --persona saksee
uv run sakthai eval skills --persona saksee --detailed
uv run sakthai eval tools --persona saksee --detailed

# Validate self-evolution setup for free (no API spend) on a SakSee primary skill:
./evolve_agent.sh saksee --skill SakSee-chrome-devtools-cli --dry-run

# Real evolution -> opens a PR on beer-sakthai/saksee-skills for review:
export OPENAI_API_KEY=sk-...          # GEPA default models are openai/*
./evolve_agent.sh saksee --skill SakSee-playwright-visual-snapshot-regression --iterations 8

# Evolve and apply the result to the live SakSee profile:
./evolve_agent.sh saksee --skill SakSee-web-scraping --apply

# Just (re)sync SakSee's current skills as the baseline on main:
./evolve_agent.sh saksee --bootstrap
```

---

## 5. Flags & Safety Rules

- `--apply`: also copy the evolved skill into the **live** profile (changes agent behavior).
- `--merge`: squash-merge the evolved skill PR on the private `saksee-skills` repo after pushing (default: open PR only, for review; main monorepo PRs are never auto-merged).
- `--no-push`: do everything locally; skip GitHub.
- `--bootstrap`: only create the repo + push current skills, then exit.
- `--dry-run`: forwarded to `evolve_skill` — validate, no API calls.

Everything else (`--iterations`, `--optimizer-model`, `--eval-source`, `--run-tests`, …) is forwarded verbatim to `python -m evolution.skills.evolve_skill`.

### Safety Invariants
- The live agent is **never** modified unless you pass `--apply`. By default the evolved skill only lands as a PR on the agent's skills repo for review.
- Only the `skills/` tree is published; `.env`, auth, tokens, and secrets are excluded from every push. Skills repos are created **private**.
- All MCP servers (`@playwright/mcp@0.0.83`, `chrome-devtools-mcp@1.10.1`) use pinned versions; `@latest` is forbidden.
