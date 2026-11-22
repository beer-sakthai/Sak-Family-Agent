# Capabilities

## Fleet-Wide Persona Comparison Matrix

The House of Sak operates six distinct personas sharing a single modular Python core package (`sakthai`), unified under the **$0.00 USD Financial Spend Policy** (100% local and free tier execution):

| Dimension | SakThai 🤗 | SakKing 👑 | SakSee 👁️ | SakSit 📣 | SakJules 🔧 | SakTan 📗 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Role & Title** | Main Lead & HF Master | General Assistant & Runner (Deputy 1) | Web / Browser Specialist (Deputy 3) | Social / Content Specialist | Master of GitHub, CI/CD & Automation | Daily Ops & Rhythm (Deputy 2) |
| **Bot Handle** | `@sakthai_agent_bot` | `@sakking_agent_bot` | `@saksee_agent_bot` | `@saksit_agent_bot` | `@sakjules_agent_bot` | `@saktan_agent_bot` |
| **Runtime Base** | `~/.sakthai` | `~/.sakthai` | `~/.sakthai` | `~/.sakthai` | `~/.sakthai` | `~/.sakthai` |
| **Memory Shard** | `~/.sakthai/sakthai/memory.db` | `~/.sakthai/sakking/memory.db` | `~/.sakthai/saksee/memory.db` | `~/.sakthai/saksit/memory.db` | `~/.sakthai/sakjules/memory.db` | `~/.sakthai/saktan/memory.db` |
| **Cost Policy** | $0.00 USD (100% Local / Free Tier) | $0.00 USD (100% Local / Free Tier) | $0.00 USD (100% Local / Free Tier) | $0.00 USD (100% Local / Free Tier) | $0.00 USD (100% Local / Free Tier) | $0.00 USD (100% Local / Free Tier) |
| **Primary Engine** | `DeepSeek-V4.1-Flash` (`huggingface`) | `Qwen/Qwen3-Coder-30B-A3B` (`huggingface`) | `DeepSeek-V4.1-Flash` (`huggingface`) | `DeepSeek-V4-Flash` (`huggingface`) | `DeepSeek-V4.1-Flash` (`huggingface`) | `sakthai` (`ollama` local) |
| **Fallback Engine** | `ollama-cloud / gpt-oss:120b` | `ollama-cloud / gpt-oss:120b` | `ollama-cloud / gpt-oss:120b` | `ollama-cloud / gpt-oss:120b` | `ollama-cloud / gpt-oss:120b` | Local Ollama (`11434`) + `DeepSeek-V4-Flash` |
| **Platform Tier** | `ModelTier.LEAD` | `ModelTier.REASONING` | `ModelTier.FAST` | `ModelTier.FAST` | `ModelTier.REASONING` | `ModelTier.LOCAL` |
| **MCP Servers** | `microsoft365` (HF Hub native) | `playwright`, `chrome-devtools`, `hf-media`, `stepsecurity`, `microsoft365` | `playwright`, `chrome-devtools`, `microsoft365` | `hf-media` (FLUX, LTX-Video), `microsoft365` | `stepsecurity` (remote SSE), `microsoft365` | `microsoft365` (native local tools) |
| **Voice Mode** | `telegram:8618306046` ("all") | `telegram:8618306046` ("all") | `telegram:8618306046` ("all") | `telegram:8618306046` ("all") | `telegram:8618306046` ("all") | None (`{}`) — Strict text ops |
| **Skills Loadout** | 170 overlay + 19 shared | 59 overlay + 19 shared | 106 overlay + 19 shared | 45 overlay + 19 shared | 56 overlay + 19 shared | 26 overlay + 19 shared |
| **Extensions Scope** | `~/.sakthai/sakthai/extensions` | `~/.sakthai/sakking/extensions` | `~/.sakthai/saksee/extensions` | `~/.sakthai/saksit/extensions` | `~/.sakthai/sakjules/extensions` | `~/.sakthai/saktan/extensions` |
| **Extensions Health** | 8-Factor Rubric (`sakthai eval extensions`) | 8-Factor Rubric (`sakthai eval extensions`) | 8-Factor Rubric (`sakthai eval extensions`) | 8-Factor Rubric (`sakthai eval extensions`) | 8-Factor Rubric (`sakthai eval extensions`) | 8-Factor Rubric (`sakthai eval extensions`) |
| **Primary Skills** | SpecKit-Bridge, SpecKit, HF-CLI, Learning Loop | Subagents, Coding-TDD, Plan Execution, Debugging | Chrome DevTools CLI, Playwright Visual Snapshot, OCR | AI SEO Strategy, Brand Journalism, HF Model Card SEO | GitHub CI Fix, Triage Issues, Workflows | Daily Briefing, Close Day, Weekly Review |
| **Key Credentials** | `HF_TOKEN`, `GOOGLE_API_KEY` | `HF_TOKEN`, `SAKTHAI_SHELL_ALLOW`, `STEP_SECURITY_API_KEY` | `HF_TOKEN`, `GOOGLE_API_KEY` | `HF_TOKEN` | `HF_TOKEN`, `GH_TOKEN`, `STEP_SECURITY_API_KEY`, `JULES_API_KEY` | `OLLAMA_HOST`, `MS_GRAPH_REFRESH_TOKEN` |

## Tools

These are exposed both to the agent loop (`sakthai run`) and over MCP
(`sakthai mcp`). The registry lives in `personas/sakthai/agent/tools.py`.

| Tool | What it does | Notes |
|------|--------------|-------|
| `learn` | Save a fact (value, kind, key) | The agent's write path into memory |
| `ingest_document` | Split a Markdown/CSV/text file into facts | Parse-only |
| `capture_lead` | Store a structured lead (name, phone, email, query) | — |
| `recall` | List recent facts + top observations | Read what's already known |
| `search` | Substring search over facts + observations | Targeted lookup |
| `search_sessions` | Content search over past session logs | Reads `~/.sakthai/sessions/`, not the store |
| `forget` | Delete a fact by id | — |
| `read_file` | Read a local text file | Sandboxed to cwd + `~/.sakthai` + `SAKTHAI_READ_ALLOW`; 20k-char cap |
| `run_command` | Run a CLI command (no shell) | **Opt-in** via `SAKTHAI_SHELL_ALLOW`; 20k-char cap, 120s max |
| `send_telegram_message` | Send a Telegram message | Needs `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` |
| `send_outlook_mail` | Send mail via Microsoft Graph | Needs `MS_GRAPH_CLIENT_ID` + `MS_GRAPH_REFRESH_TOKEN` |
| `read_outlook_mail` | List recent inbox messages | Same Graph credentials |
| `list_calendar_events` | List upcoming calendar events | Same Graph credentials |
| `create_calendar_event` | Create a calendar event | Same Graph credentials |
| `run_agent_loop` | Delegate a whole task to SakThai's agent loop | MCP-only (filtered out of the in-loop tool set to avoid recursion) |
| `family_recall` | Recall across every persona's memory shard | Read-only `FamilyMemoryView` |
| `family_search` | Search across every persona's memory shard | Read-only `FamilyMemoryView` |
| `delegate_to_persona` | Run a subtask as another Sak Family persona, in-process | Persona name is enum-constrained |

## Memory operations

`sakthai memory …` and the store API behind them:

- `show` / `stats` — list entries; aggregate counts, kinds, tags, time ranges.
- `search` — substring search (LIKE wildcards are escaped).
- `forget` / `forget-obs` — delete by id.
- `export` / `import` — portable JSON snapshot (also CSV / JSONL export).
- `backup` — timestamped copy of `memory.db`.
- `healthcheck` — SQLite `integrity_check`.
- `consolidate` — fold facts older than N seconds into one observation.
- `consolidate-sessions` — mine local session logs through an LLM and learn durable facts about the user (idempotent across runs).
- `deduplicate` — drop duplicate facts/observations (keyed and key-less).
- `family` — merged read-only view across every persona's shard (`--personas a,b,c`).
- `sync` / `pull` — git-backed JSONL export/import and HTTP backup. Both always
  target the unscoped `memory.db` and reject `--persona`.

All of these except `sync`/`pull` accept a group-level `--persona <name>` to act
on that persona's own shard at `~/.sakthai/<persona>/memory.db`.

## Providers

`run_agent` supports four providers, auto-detected from the model name and
available credentials (override with `--provider`):

- **anthropic** — Claude via the `anthropic` SDK (default model `claude-opus-4-8`).
- **google** — Gemini via `google-genai`.
- **openai** — any OpenAI-compatible gateway via `httpx` (`OPENAI_API_BASE` /
  `OPENAI_BASE_URL` + `OPENAI_API_KEY`).
- **ollama** — local models via Ollama (`OLLAMA_HOST`, default
  `http://127.0.0.1:11434`); no API key, **no cost**.

All are normalised to one response shape, so the loop logic is provider-agnostic.

## Sessions

Each `run_agent` call writes a JSON session log to `~/.sakthai/sessions/`
(task, model, messages, and the result with tool calls).

## Dashboard & Telemetry

The dashboard is managed via the `sakthai dashboard` CLI command group (`dev`, `build`, `test`, `start`, `status`) and served by the Next.js application at `apps/sak_agent_dashboard/` (which embeds `apps/sak_agent_dashboard/workflow_engine/`).

Under the hood, `personas/sakthai/sakthai/dashboard/data.py` builds an honest snapshot of the memory store (testable, with zero UI dependencies), which is served over HTTP by `web/server.py` alongside the core API endpoints:

| Endpoint | Payload |
|---|---|
| `/health` | liveness; the only unauthenticated path |
| `/api/stages` | the `dashboard/data.py` snapshot |
| `/api/ecosystem` | ecosystem status |
| `/api/personas` · `/api/metrics` · `/api/sessions` · `/api/memory` · `/api/audit` · `/api/workflows` | the dashboard payloads built by `web/api.py`, shaped by `web/contracts.py` |

Every path except `/health` requires the bearer token configured via `sakthai web setup`.

## Unified Agent Platform

The `sakthai.agent_platform` subsystem unifies advanced agent engineering and enterprise orchestration capabilities:

- **Accidental Data Loss Guardrails (`safety.py`, `guardrails_hardened.py`)**: Real-time evaluation of destructive shell commands (`rm -rf`, `gsutil rm`, `bq rm`, `git reset --hard`, `git clean -f`, `mkfs`, `dd`, `terraform destroy`, `kubectl delete ns/all`) and raw SQL mutations (`DROP`, `TRUNCATE`, unconstrained `DELETE`) with HMAC-based authorization tokens (`check_data_loss_guardrail`).
- **Reactive Python Dependency Detection & Isolated Runner (`dep_manager.py`)**: Environment introspection adhering to a strict hierarchy (`uv` → `poetry` → `pipenv` → `conda` → `venv+pip`), preventing global package pollution, plus automatic command wrapping (`wrap_with_isolated_runner` / `sakthai platform wrap-cmd`).
- **Progressive Disclosure Customizations & Skills (`customizations.py`, `skills.py`)**: Hierarchical instruction resolution (`AGENTS.md`, `GEMINI.md`, `.rules.md`) and lightweight progressive disclosure summary tables (`render_skills_progressive_summary` / `sakthai platform skills`) to minimize prompt bloat.
- **Jules Task Delegation (`jules_worker.py`)**: GitHub remote resolution, asynchronous patch planning, and delegation session formatting.
- **Dual Agent Core Engine & Model Selection Presets (`agent_engine.py`)**: Abstraction layer unifying Google Antigravity SDK (`LocalAgentConfig` / LiteRT) and Google ADK execution models with built-in safety interception and standardized model tiers (`ModelTier.FAST`, `ModelTier.REASONING`, `ModelTier.LOCAL`, `ModelTier.LEAD`).
- **Autonomous Antigravity Agent (`antigravity_agent.py`)**: Production-ready agent runner supporting hosted Gemini, on-device LiteRT, and local Ollama backends with streaming responses and data loss prevention guardrails (`sakthai platform antigravity`).
- **Harness AI Agent Spec Exporter (`harness_exporter.py`)**: Deterministic canonical identifier generation (`ca_<slug>`) and declarative Harness v1 agent template and pipeline step export (`sakthai platform export-harness`).

## Model Context Protocol (MCP)

`sakthai mcp` exposes the unified runtime over JSON-RPC 2.0 and connects to external MCP servers:

- **Inbound MCP Server (`sakthai mcp` / `sakthai mcp serve`)**:
  - Tools: All `BUILTIN_TOOLS` (`tools/list`, `tools/call`).
  - Resources: Sharded memory status at `sakthai://memory/status` (`resources/list`, `resources/read`).
  - Prompts: Standard agent prompt templates (`prompts/list`, `prompts/get`).
- **Outbound MCP Client (`StdioMCPClient` & `RemoteMCPClient`)**:
  - Connects to external MCP servers configured in `~/.sakthai/mcp.json` or persona configs.
  - Supports stdio sub-processes and remote HTTP/SSE endpoints (`transport: "sse"` or `"http"`).
  - Enforces URL scheme validation (`http://` / `https://`) and command sanitization.
  - Fine-grained tool scoping with allowlists (`spec.tools`).
  - Tools are auto-namespaced as `<server>__<tool>`.
- **Developer & Diagnostic CLI Tools**:
  - `sakthai mcp list [--persona <name>] [--json]`: Inspect configured external servers and transports.
  - `sakthai mcp ping [<name>] [--persona <name>]`: Probe responsiveness and health of external servers.
  - `sakthai mcp tools [--persona <name>]`: List discovered external tools and schemas.

## Model Training & Serving (`sakthai train`)

The `sakthai train` CLI command group provides end-to-end tooling to generate synthetic agent datasets, fine-tune models, evaluate tool-calling fidelity, and export adapters for offline or cloud serving:

- `sakthai train list [--json]`: Discovers available fine-tuning runs and datasets under `training/`.
- `sakthai train dataset [--synthetic-tools]`: Compiles instruction datasets (`build_v12.py`) or generates synthetic tool-calling examples (`build_toolcalling_dataset.py`) for the 8 core SakThai built-in tools.
- `sakthai train sft [--recipe <recipe>] [--dry-run]`: Launches parameter-efficient fine-tuning (QLoRA) using targeted recipes (`sft_qlora`, `toolcalling`, `persona`, `coder`, `7b`).
- `sakthai train eval [--dry-run]`: Runs probe evaluation prompts against fine-tuned adapters (`eval_toolcalling.py`) to verify tool call emission and direct answering behavior.
- `sakthai train export [--out <dir>] [--dry-run]`: Merges LoRA adapter weights and writes an Ollama `Modelfile` (`export_ollama.py`) to enable running the agent loop 100% offline via `sakthai run --provider ollama --model sakthai`.
- `sakthai train deploy [--repo <id>] [--create] [--dry-run]`: Dry-runs or provisions a Hugging Face Text Generation Inference (TGI) endpoint exposing an OpenAI-compatible `/v1` endpoint (`deploy_hf_endpoint.py`).

## Runtime Gateway (OpenAI-Compatible & REST API)

The `sakthai.gateway` subsystem provides a unified, multi-threaded HTTP server exposing an OpenAI-compatible API and comprehensive REST endpoints for the House of Sak fleet:

- **OpenAI Compatibility**:
  - `/v1/chat/completions`: Supports standard message payloads, temperature, max tokens, and both buffered JSON and streaming Server-Sent Events (`stream: true`).
  - `/v1/models`: Enumerates available personas (`sakthai`, `sakking`, `saksee`, `sakjules`, `saksit`, `saktan`) and model tiers.
- **Dynamic Persona Routing**: Requests targeting a specific persona model ID execute in that persona's identity context with access to their curated skills and memory shard.
- **DataLossGuardrail Protection**: The `/v1/tools/execute` endpoint intercepts high-risk commands (`rm -rf`, `DROP TABLE`, destructive disk/network mutations) and requires an explicit HMAC approval token.
- **Filesystem Isolation**: File access tools enforce safe root isolation (`Path.cwd()`, `~/.sakthai`, `SAKTHAI_READ_ALLOW`) and block access to sensitive files.
- **Constant-Time Authentication**: Bearer tokens are verified using `secrets.compare_digest` to prevent timing side-channels.
- **External Client Integration**: Drop-in compatible with Cursor, Claude Code, Aider, OpenCode, and standard OpenAI SDKs (`OPENAI_BASE_URL="http://localhost:8080/v1"`).
- **Developer CLI Tools**:
  - `sakthai gateway serve [--host <host>] [--port <port>] [--token <tok>] [--cors <origin>]`: Start gateway server.
  - `sakthai gateway status [--url <url>]`: Inspect gateway health, uptime, and active personas.
  - `sakthai gateway models [--url <url>] [--token <tok>]`: List served personas and model presets.
  - `sakthai gateway chat <prompt> [--model <model>] [--stream]`: Test chat completions interactively.

