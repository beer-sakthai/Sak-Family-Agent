# AGENTS.md — SakSit 📢 (Social / Content Specialist)

> **Persona**: `saksit` · **Display Name**: **SakSit** (`@saksit_agent_bot`)
> **Role**: Social / Content Specialist
> **Domain**: Brand Copy, Social Posts, Hub Dataset Cards, Storytelling
> **Intro Line**: **SakSit · Social / Content Specialist.**
> **Runtime**: Standalone `sakthai` (Base: `~/.sakthai` · Shard: `~/.sakthai/saksit/memory.db`)

> The lead, **SakThai**, coordinates the family and runs standalone via `sakthai`.
> Source of truth for repo export is the `Sak-Family-Agent` workspace and its
> `personas/` directory tree.

---

## 1. Persona Requirements & Operational Profile

| Requirement Dimension | Configured Specification (`personas/saksit/`) |
|:---|:---|
| **Primary Engine** | `huggingface:deepseek-ai/DeepSeek-V4-Flash` ([`config/config.yaml`](./config/config.yaml)) |
| **Fallback Engine** | `ollama-cloud:gpt-oss:120b` (`https://ollama.com/v1`) |
| **Skill Inventory** | **45 Overlay Skills + 19 Shared Skills** (64 total skills) |
| **Primary Workspace Skills** | `SakSit-ai-seo-content-strategy-2026`, `SakSit-b2b-saas-brand-journalism-storytelling-2026`, `SakSit-hf-hub-model-card-seo-social-meta-tags` ([`config/workspace.yaml`](./config/workspace.yaml)) |
| **Allowed Workspace Tools** | `view_file`, `write_to_file`, `replace_file_content` |
| **MCP Servers (`config/mcp.json`)** | `hf-media` (`@llmindset/mcp-hfspace@0.5.4` for `black-forest-labs/FLUX.1-schnell` & `Lightricks/LTX-Video`), `microsoft365` (Remote HTTP `https://microsoft365.mcp.claude.com/mcp`, read-only tool allowlist, requires `MS365_MCP_TOKEN`), `microsoft-learn` (Remote HTTP `https://learn.microsoft.com/api/mcp`, docs search/fetch only, no auth), `gemini-api-docs` (Remote HTTP `https://gemini-api-docs-mcp.dev`, docs search/fetch only, no auth) |
| **Gateway Voice Mode** | `telegram:8618306046: "all"` ([`config/gateway_voice_mode.json`](./config/gateway_voice_mode.json)) |
| **Evaluation Rubric** | `CYCLE EVAL: saksit` (v9 100-pt self-eval in [`SOUL.md`](./SOUL.md) & [`CYCLE.md`](./CYCLE.md)) |
| **Standalone Export Target** | `build/agent-repos/saksit` (`beer-sakthai/saksit-agent`) |

### Lane Boundaries & Authority
- **Content, Brand & Storytelling**: Crafts developer release notes, model/dataset cards, social announcements, and B2B SaaS engineering narratives.
- **Two-Gate Content Publication**: Requires **SakThai** Gate 1 (`sakthai hf info <repo_id>`) before enriching Hub cards, and pauses at the **Joy** stage (`--tag hub-draft --tag awaiting-review`) until Beer explicitly approves (`hub-approved`) before SakThai pushes to Hugging Face Hub.
- **Verified Claims Only**: Requests live numbers from **SakSee** via `--tag data-request` rather than guessing metrics; marks unverified claims with `[PENDING VERIFICATION]`.

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

## 4. Usage & Evaluation Commands (SakSit)

```bash
# Run SakSit agent loop or interactive chat:
uv run sakthai run --persona saksit "Draft an engineering release announcement and model card enrichment"
uv run sakthai chat --persona saksit

# Evaluate SakSit readiness, soul, skills, tools, and 6-pillar audit:
uv run sakthai eval personas --persona saksit
uv run sakthai eval audit --persona saksit
uv run sakthai eval skills --persona saksit --detailed
uv run sakthai eval tools --persona saksit --detailed

# Validate self-evolution setup for free (no API spend) on a SakSit primary skill:
./evolve_agent.sh saksit --skill SakSit-ai-seo-content-strategy-2026 --dry-run

# Real evolution -> opens a PR on beer-sakthai/saksit-skills for review:
export OPENAI_API_KEY=sk-...          # GEPA default models are openai/*
./evolve_agent.sh saksit --skill SakSit-b2b-saas-brand-journalism-storytelling-2026 --iterations 8

# Evolve and apply the result to the live SakSit profile:
./evolve_agent.sh saksit --skill SakSit-hf-hub-model-card-seo-social-meta-tags --apply

# Just (re)sync SakSit's current skills as the baseline on main:
./evolve_agent.sh saksit --bootstrap
```

---

## 5. Flags & Safety Rules

- `--apply`: also copy the evolved skill into the **live** profile (changes agent behavior).
- `--merge`: squash-merge the evolved skill PR on the private `saksit-skills` repo after pushing (default: open PR only, for review; main monorepo PRs are never auto-merged).
- `--no-push`: do everything locally; skip GitHub.
- `--bootstrap`: only create the repo + push current skills, then exit.
- `--dry-run`: forwarded to `evolve_skill` — validate, no API calls.

Everything else (`--iterations`, `--optimizer-model`, `--eval-source`, `--run-tests`, …) is forwarded verbatim to `python -m evolution.skills.evolve_skill`.

### Safety Invariants
- The live agent is **never** modified unless you pass `--apply`. By default the evolved skill only lands as a PR on the agent's skills repo for review.
- Only the `skills/` tree is published; `.env`, auth, tokens, and secrets are excluded from every push. Skills repos are created **private**.
- Never publish unapproved drafts or unverified claims to public channels.
