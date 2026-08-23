---
name: SakSit-sak-family-agent-knowledge
description: Help and support for the Sak-Family-Agent monorepo.
...
---

# Sak-Family-Agent — Help & Support Knowledge

A reference for the **Sak-Family-Agent** monorepo (`github.com/beer-sakthai/Sak-Family-Agent`). This skill covers what the repo is, its structure, the six Sak Family agent personas, the architecture, setup, integration, security posture, and operational rules. It does NOT cover any single persona's skills in detail — those live in their respective skill trees.

## Principles for answering model capability questions

When asked what a SakThai model can or cannot do:
1. **Check HF first.** Query the Hugging Face API for models by the Nanthasit author and inspect actual model cards. Beer's exact correction: "Check in hugging face omg check first." Never answer from memory alone.
2. **Read the pipeline_tag.** A model with `pipeline_tag: text-generation` is text-only. `image-text-to-text` means vision-language — can READ images but NOT generate them. `text-to-speech` generates audio. Neither is a diffusion model (FLUX/SDXL) that creates pictures.
3. **Read the config.json and README.** These reveal the base architecture (Qwen2.5, LLaVA, Kokoro), quantization format (GGUF, safetensors), and actual capabilities. Pipeline_tag alone can be misleading.
4. **Enumerate the full family.** The Nanthasit account has 20+ repos including text models (sakthai-context-*, 0.5B/1.5B/7B), vision (sakthai-vision-7b = LLaVA v1.5-7B GGUF, reads images only), TTS (Kokoro-82M), embedding (multilingual), and datasets. Always report which type you checked.
5. **List available models.** Use `GET https://generativelanguage.googleapis.com/v1beta/models?key=...` to discover what models exist. Confirmed discovery 2026-07-25: `nano-banana-pro-preview` is a real Google Gemini image model.

## When to Use

- You are asked to help with, debug, or navigate the Sak-Family-Agent repo.
- You need to understand how the six Sak agents relate to each other.
- You need to set up, build, test, or integrate SakThai on a new machine.
- You are troubleshooting MCP, memory, or agent loop issues.
- You need to compose or export persona skill trees.

## Prerequisites

- Python >= 3.11
- `uv` installed (project uses uv for dependency management)
- For full agent loop: an API key (Anthropic, Google, or OpenAI-compatible) OR a local Ollama model
- Git access to `github.com/beer-sakthai/Sak-Family-Agent`
- Credentials in `.env` (copy from `.env.example`)
- For HF operations: `huggingface_hub` installed (optional — the CLI shows a clear install hint)
- For HF Jobs training: `hf` CLI installed (`pip install huggingface-hub[cli]`) + `HF_TOKEN` in env

## Quick Reference

| Command | Purpose |
|---------|---------|
| `uv sync --all-extras` | Install all dependencies |
| `make test` | Run pytest suite |
| `make lint` | Run ruff checks |
| `uv run mypy personas/sakthai/sakthai` | Strict type checking |
| `uv run bandit -c pyproject.toml -r personas/sakthai/sakthai` | Security scan |
| `make mutation` | Local mutation testing (slow) |
| `sakthai run "<prompt>"` | Run the agent loop |
| `sakthai mcp` | Start MCP stdio server |
| `sakthai learn "<fact>" [--kind pref/note/project]` | Save a memory fact |
| `sakthai recall` | List memory facts |
| `sakthai memory consolidate` | Fold old facts into observations |
| `sakthai dashboard` | Streamlit memory dashboard |
| `python scripts/compose_persona.py <name> --out <dir>` | Compose persona skill tree |
| `python scripts/export_agent_repo.py <name> --out <dir>` | Export standalone repo |
| `sakthai run "<prompt>" --dry-run` | Preflight (zero cost) |
| `sakthai run "<prompt>" --no-mcp` | Disable external MCP servers |
| `sakthai hf info <repo_id>` | Hugging Face model info |
| `sakthai hf download <repo_id>` | Download model snapshot to cache |
| `hf jobs uv run --flavor <gpu> --secrets HF_TOKEN --timeout <m> <script>` | Run training on HF Jobs |
|
## Procedure

### 1. Understanding the Repository

The Sak-Family-Agent is a **monorepo** containing:

- **Core Python package** at `personas/sakthai/sakthai/` — installable as `sakthai-agent` v2.0.0
- **Six persona overlays** at `personas/<name>/` — sakthai (Lead), sakking, saksee, saksit, saktan, sakjules
- **Shared documentation** in `docs/`
- **CI/CD infrastructure** in `.github/workflows/`
- **Training scripts** in `training/`
- **Business/product strategy** in `product/`
- **Deployment configs** in `infra/vm-agents/`

Key rule: there is **no root-level `sakthai/` package** — import resolves because `personas/sakthai/` is editable-installed. Scripts that import `sakthai` must insert `personas/sakthai/` into `sys.path` explicitly.

### 2. The Six Sak Family Personas

Each persona has a `SOUL.md` defining its identity. They share one SQLite memory at `~/.sakthai/memory.db` but keep separate live sessions.

| Agent | Handle | Role |
|-------|--------|------|
| **SakThai** | `@sakthai_agent_bot` | Lead & Orchestrator · Main Lead of the House & Master of Hugging Face |
| **SakKing** | `@sakking_agent_bot` | General Assistant, Runner & Self-Healing (owns all skills) |
| **SakSee** | `@saksee_agent_bot` | Master of Web (Playwright + Chrome DevTools) |
| **SakSit** | `@saksit_agent_bot` | Master of Social Media |
| **SakTan** | `@saktan_agent_bot` | Daily Ops Helper (calendar, email, life admin) |
| **SakJules** | `@sakjules_agent_bot` | Master of Automation & CI/CD |

**Model policy:** Every agent defaults to the free local Ollama `sakthai` model. Cloud backends (Anthropic, Gemini, OpenAI, HF router, Ollama Cloud) are opt-in only with Beer's explicit OK — he is cost-constrained.

**Skill access:** SakKing can use and add ALL persona skills. Other agents use only shared skills (`Sak-` prefix) + their own (`Sak<Name>-` prefix). Shared skills (byte-identical across all 6) live under `personas/shared/skills/`.

**Value cycle:** Dream (SakThai) → Hope (SakKing) → Care (SakSit) → Joy (SakTan) → Trust (SakJules) → Growth (SakSee) → back to Dream.

### 3. Architecture Layers

```
sakthai run ───▶ CLI (click) ◀─── sakthai mcp
                    │                │
              ┌─────▼──┐       ┌──────▼──────┐
              │ agent/  │       │  mcp/server  │
              │ (loop)  │       │(JSON-RPC MCP)│
              └────┬────┘       └──────┬───────┘
                   │ Shared Tool Registry
                   └────────┬──────────┘
                            │
                   ┌────────▼────────┐
                   │  memory/store   │
                   │ (SQLite, WAL)   │
                   └────────┬────────┘
                            │
                   ~/.sakthai/memory.db
```

- **`config.py`** — single source of truth for paths and env vars
- **`auth.py`** — credential resolution (Anthropic, Google, OpenAI, Ollama)
- **`memory/store.py`** — SQLite facts/observations with search, dedupe, consolidation, backup
- **`agent/`** — tool registry + agent loop (supports 4 providers: anthropic, google, openai, ollama)
- **`mcp/server.py`** — dependency-free JSON-RPC 2.0 stdio server
- **`cycle/`** — 6-stage Dream→Growth state machine
- **`skills.py`** — parse/catalog/validate SKILL.md files
- **`dashboard/`** — Streamlit memory view

### 4. Setup

```bash
git clone https://github.com/beer-sakthai/Sak-Family-Agent.git
cd Sak-Family-Agent
cp .env.example .env   # then fill in credentials
uv sync --all-extras   # install everything
```

To verify: `sakthai run "test" --dry-run` prints tool count with zero API cost.

### 5. Composing and Exporting Personas

To rebuild a persona's full skill tree (shared + overlay):
```bash
python scripts/compose_persona.py sakthai --out /tmp/sakthai-skills
```

To export a standalone agent repo (shared core + one persona):
```bash
python scripts/export_agent_repo.py sakjules --out build/agent-repos/sakjules
```

To compose ALL personas at once: `make compose-personas`.

### 6. Integration Points

**MCP servers** configured in `~/.sakthai/mcp.json` (Claude-Desktop-compatible format). During `sakthai run`, all enabled servers are discovered and their tools merged namespaced as `<server>__<tool>`. `--no-mcp` disables all.

- **Claude CLI:** Add to `~/.claude/config.json` with `command: "sakthai"`, `args: ["mcp"]`
- **Gemini CLI:** Same format in active `.mcp.json`
- **SakKing ↔ SakThai:** Interop over local MCP stdio (zero network cost)
- **Composio:** Configure in `~/.sakthai/mcp.json` for managed tool integrations
- **SakKing-learned skills:** Import via `sakthai skills sync-sakking`

### 7. Hugging Face in the Sak-Family-Agent

SakThai's persona title is **Master of Hugging Face** — HF operations are a
first-class capability in the repo, not an afterthought.

#### Built-in HF module

`personas/sakthai/sakthai/hf.py` wraps `huggingface_hub` with lazy imports (no
hard dep — fails with a clear install hint when missing). Provides:

| CLI command | What it does |
|-------------|--------------|
| `sakthai hf info <repo_id>` | Model info (downloads, likes, tags) |
| `sakthai hf download <repo_id>` | Download snapshot to `~/.sakthai/hf/<repo_id>` (path-traversal protected) |

Each persona also carries its own copy of `hf.py` at `personas/<name>/sakthai/hf.py`.

#### Fine-tuning infrastructure (`training/hf-jobs/`)

PEP 723 uv-scripts designed to run on **Hugging Face Jobs** (GPU compute),
driven from a machine without a local GPU:

| Script | Purpose | Suggested GPU |
|--------|---------|--------------|
| `train_persona_lora.py` | QLoRA SFT of Qwen2.5-0.5B on persona/doc data — teaches voice/style only | `t4-small` |
| `train_toolcalling_lora.py` | QLoRA SFT of Qwen2.5-1.5B on tool-calling dataset — teaches when/how to emit tool calls | `l4x1` |
| `build_toolcalling_dataset.py` | Generates synthetic tool-calling examples for the 8 built-in tools (+ "no-tool" negatives) | local |
| `fetch_public_toolcalling.py` | Pulls + reformats `glaiveai/glaive-function-calling-v2` into the same schema | local |

Run on HF Jobs:
```bash
hf jobs uv run --flavor t4-small --secrets HF_TOKEN --timeout 30m train_persona_lora.py
hf jobs uv run --flavor l4x1 --secrets HF_TOKEN --timeout 1h train_toolcalling_lora.py
```

#### Models and datasets on the Hub (under `Nanthasit`)

| Artifact | Type | Purpose |
|----------|------|---------|
| `Nanthasit/sakthai-persona-0.5b-lora` | QLoRA adapter | Voice/style training (Qwen2.5-0.5B base) |
| `Nanthasit/sakthai-toolcalling-1.5b-lora` | QLoRA adapter | Tool-calling behaviour (Qwen2.5-1.5B base) |
| `Nanthasit/sakthai-context-1.5b-tools` | QLoRA adapter | From `training/sakthai-1.5b-lora/` — Colab-trained |
| `Nanthasit/sakthai-context-1.5b-merged` | Merged model | Full weights from the 1.5B LoRA |
| `Nanthasit/sakthai-context-0.5b` | LoRA adapter | **Stale** — dead local base path; use public Qwen base instead |
| `Nanthasit/sakthai-toolcalling-v1` | Dataset | 167 examples (151 train / 16 test), `messages`+`tools` format |
| `Nanthasit/sakthai-combined-v5` | Dataset | Used by `training/sakthai-1.5b-lora/` Colab notebook |
| `Nanthasit/hermes-dataset` | Dataset | Hermes persona/doc data for the persona LoRA |
| `Nanthasit/hf-training-composio-tools-50` | Dataset | Sample dataset for the dataset-publishing service |

#### HF skill tree (extensive)

The repo carries **hundreds of HF skills** across all personas — everything from
hub operations to inference providers, Spaces, PEFT, TRL, datasets, model cards,
and deep-dive research. Key locations:

- `personas/sakthai/skills/SakThai-hf-*` — 13 SakThai-specific HF skills
- `personas/sakthai/skills/mlops/` — 50+ general HF skills (hub, datasets,
  transformers, spaces, inference, fine-tuning, courses)
- `personas/sakking/skills/SakKing-hf-*` — additional SakKing-level HF skills
- `data/hf-topics-covered.json` — registry of 230+ covered HF topics

SakSit's own HF skill: `personas/saksit/skills/mlops/SakSit-huggingface-hub/`.

#### Dataset publishing service (`services/hugging-face-dataset-publishing/`)

A paid service pitch: custom tool-use datasets built from raw logs, validated,
uploaded, with README/license. Priced $300–$800 per dataset with $100/month
maintenance. Sample deliverable:
`Nanthasit/hf-training-composio-tools-50`.

#### Running inference on trained models

The trained adapters can be served via **vLLM, SGLang, llama.cpp, or MLX**.
**TGI is in maintenance mode** (June 2026) — do not start new TGI or Inference
Endpoint deployments; use vLLM/SGLang instead. See `training/serving/` for
endpoint deployment scripts.

### 8. Security & CI Gates

| Gate | Coverage |
|------|----------|
| `ci.yml` | ruff, strict mypy, bandit on core sakthai package |
| `secret-scan.yml` | gitleaks over full git history |
| `dependency-audit.yml` | pip-audit on uv.lock (weekly + on change) |
| CodeQL | GitHub-managed SAST |
| `ossar.yml` | Microsoft Security DevOps |
| `sonarcloud.yml` | SonarCloud analysis |
| Dependabot | Weekly update PRs (Python, npm, Actions) |
| `continuous-security.yml` | Dormant — outside `.github/workflows/`. Move to activate |

## Pitfalls

- **No root-level `sakthai/` package.** Importing `sakthai` in scripts requires `sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))` unless in the editable-installed environment.
- **`run_command` disabled by default.** Opt-in via `SAKTHAI_SHELL_ALLOW=1`. The agent loop cannot run shell commands without it.
- **MCP fails soft.** If an MCP server from `mcp.json` won't start, SakThai logs a warning and continues — the agent loop may lack expected tools.
- **Shared skills are conservative.** `personas/shared/skills/` only holds byte-identical files across ALL 6 personas. Most overlap stays in each persona's own overlay.
- **continuous-security.yml is dormant.** It lives at the repo root, outside `.github/workflows/`, so GitHub never triggers it. Moving it activates nightly API-costly LLM runs.
- **Archived standalone repos (sakthai-agent, sakking-agent, etc.) may exist** but the single source of truth is the monorepo. The export script degrades silently for some infra paths.
- **No Google ADK/Vertex AI** in v2.0. The OG had a cloud agent; v2 is local-first (CLI + agent loop + MCP stdio). No cloud bundle, no sync script.
- **Skill naming collisions:** 31 pre-existing conflicts remain unrenamed (a differently-prefixed skill with different content already occupies the target name). Run `sakthai skills validate --naming` to see the current list.
- **TGI is in maintenance mode** (June 2026). Do not deploy new TGI or HF Inference Endpoints for serving; use vLLM, SGLang, llama.cpp, or MLX instead.
- **Dual-repo HF model cards.** When a HF repo has both a model and dataset side, `push_to_hub` on the model side does NOT update the dataset side — you must update both explicitly.
- **HF_TOKEN as job secret.** The HF token is forwarded as `--secrets HF_TOKEN` on HF Jobs — never baked into images or committed. Without it, private datasets and model uploads will fail silently.

## Verification

The simplest smoke test that the repo is set up correctly:

```bash
cd /path/to/Sak-Family-Agent
sakthai run "list the available tools" --dry-run
```

Expected output: a JSON-like summary showing the tool count (typically 8 tools + any MCP-discovered ones), confirming the CLI, package, and credential resolution work without making any API call.
