---
name: SakSit-hermes-skill-evolution
description: Evolve skills using DSPy and GEPA optimization.
...
---

# Hermes Skill Evolution

Evolve a Hermes agent's SKILL.md files using DSPy + GEPA (reflective optimization). The pipeline lives **inside** the agent's profile under `sak-family-agent/packages/agent-self-evolution/`. The standalone Sak-Family-Agent monorepo at `/opt/data/` was removed on 2026-07-09 — only the per-profile copy survived.

## Location

```
/opt/data/profiles/<agent>/sak-family-agent/packages/agent-self-evolution/
```

Only agent `saksit` has a confirmed pipeline copy. Other agents' profiles may lack it — verify existence before evolving for non-saksit agents.

## Pipeline Overview

1. **Load skill** — finds and parses the target SKILL.md file from the agent's profile skills dir
2. **Build eval dataset** — generates synthetic test cases (default 20 examples, 50/25/25 train/val/holdout split)
3. **Run GEPA optimizer** — DSPy's reflective evolution engine mutates the skill text, evaluates on trainset, refines via reflection
4. **Validate constraints** — checks size limits, structure, caching compatibility
5. **Evaluate on holdout** — scores baseline vs evolved on held-out examples
6. **Save output** — evolved skill + metrics + baseline comparison saved to `output/<skill>/<timestamp>/`

## Setup

```bash
cd /opt/data/profiles/<agent>/sak-family-agent/packages/agent-self-evolution/

# Create venv (no venv exists by default — must create first)
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Quick Start (Dry Run)

```bash
# Validate setup without API spend
./evolve_agent.sh saksit --skill github-auth --dry-run
```

## Running Evolution

### Via evolve_agent.sh (recommended)

The wrapper handles: repo sync, venv setup, PR creation, and live deployment.

```bash
# Full evolution → PR on beer-sakthai/<agent>-skills for review
export OPENROUTER_API_KEY="sk-or-..."
./evolve_agent.sh saksit --skill github-auth --iterations 8 \
  --optimizer-model openrouter/anthropic/claude-3-haiku

# Evolve + auto-apply to live profile
./evolve_agent.sh sakthai --skill arxiv --merge --apply

# Bootstrap (just sync current skills to repo baseline)
./evolve_agent.sh saksee --bootstrap
```

### Evolve Agent Script Flags

| Flag | Effect |
|------|--------|
| `--apply` | Copy evolved skill into LIVE profile (changes agent behavior) |
| `--merge` | Auto-squash-merge the PR after pushing |
| `--no-push` | Do everything locally; skip GitHub |
| `--dry-run` | Validate only, no API calls |
| `--bootstrap` | Only create repo + push current skills baseline |
| `--iterations N` | GEPA iterations (default 10, 5-8 for faster runs) |

All other flags (`--eval-source`, `--run-tests`, etc.) pass through to `python -m evolution.skills.evolve_skill`.

### Direct Python (bypass wrapper)

```bash
cd /opt/data/profiles/<agent>/sak-family-agent/packages/agent-self-evolution/
source .venv/bin/activate
export EVO_OPTIMIZER_MODEL="openrouter/anthropic/claude-3-haiku"
export EVO_EVAL_MODEL="openrouter/anthropic/claude-3-haiku"
python -m evolution.skills.evolve_skill --skill github-auth --iterations 8
```

## Model Configuration

| Env Var | Purpose | Default |
|---------|---------|---------|
| `EVO_MODEL` | All roles (fallback) | `ollama_chat/qwen2.5-coder:1.5b` |
| `EVO_OPTIMIZER_MODEL` | GEPA reflections | Falls back to EVO_MODEL |
| `EVO_EVAL_MODEL` | LLM-as-judge scoring | Falls back to EVO_MODEL |
| `EVO_JUDGE_MODEL` | Dataset generation | Falls back to EVO_MODEL |
| `EVO_MAX_TOKENS` | Per-call limit | `2048` |
| `EVO_DATASET_SIZE` | Eval examples | `20` |
| `EVO_MAX_TOKENS` | Max tokens per LLM call | `2048` (capped from DSPy's huge default) |

**For this environment:** No Ollama running. Use OpenRouter models:
- `openrouter/anthropic/claude-3-haiku` (fast, cheap)
- `openrouter/openai/gpt-4o-mini` (alternative)

## Previous Run Results

| Skill | Agent | Result | Notes |
|-------|-------|--------|-------|
| `github-auth` | sakking | ❌ FAILED | Constraint validation rejected the evolved variant. Saved to `output/github-auth/evolved_FAILED.md` |

The constraint failure is expected for many skills — the evolved text may exceed size limits or change structure too much. Try: more focused iterations, better eval source, or relaxed constraints.

## Known Pitfalls

- **No venv exists** by default — must `uv venv` + `uv pip install -e ".[dev]"` before running
- **Default model is local Ollama** which doesn't exist here — always set `EVO_OPTIMIZER_MODEL` and `EVO_EVAL_MODEL` to OpenRouter models
- **`hermes evolve` CLI** does not exist — use `evolve_agent.sh` or direct `python -m`
- **Constraint validation can reject** evolved skills even when GEPA improves quality — check `output/<skill>/evolved_FAILED.md` to inspect what changed
- **PR creation** requires `gh` CLI authenticated with GitHub — if not configured, use `--no-push` for local-only runs
- **The `hermes-agent` repo** auto-discovery looks for `~/.hermes/hermes-agent` or `../hermes-agent` — for Sak agents, pass `--hermes-repo ~/.hermes/profiles/<agent>` explicitly via the wrapper (handled automatically by `evolve_agent.sh`)

## 6-Cycle Integration

| Cycle | Step |
|-------|------|
| **Dream** | Choose the skill to improve. What behavior needs optimization? |
| **Hope** | Set eval source, iterations, expected improvement threshold |
| **Care** | Run evolution with constraint guardrails; review PASS/FAIL |
| **Joy** | Package winning variant as repo change or PR |
| **Trust** | Run tests, review diff against baseline |
| **Growth** | Apply evolved skill to live profile (`--apply`), save learning |
