# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`sakthai-agent` **v2.0** — a personal learning agent with persistent memory. It
gives a Claude or Gemini agent a durable SQLite memory it can read and write
across sessions, plus a shared tool registry and an MCP stdio server so the same
memory is reachable from other runtimes.

This is a **clean, from-scratch rewrite** of the original `SakThai-Agent` (the
"OG"). The OG is a read-only blueprint: consult it for intent, but never copy its
code or layout into this repository — re-derive everything. The OG's Google
ADK / Vertex AI cloud agent is **not** part of v2: there is **no `app/` cloud
bundle, no `sync-app-package.sh` sync step, and no `sakthai/cloud/` module** here.
v2 is local-first — the CLI, the agent loop, and the MCP stdio server.

---

## Related repositories

Three repos under `beer-sakthai` make up the family; this one is the hub. When a
task spans more than the agent runtime, check which repo actually owns the code:

| Repo | Owns | Boundary with this repo |
|---|---|---|
| `beer-sakthai/Sak-Family-Agent` | **This repo.** The `sakthai` package, the six personas, memory, MCP, web API, and the `training/` HF Jobs definitions. | — |
| `beer-sakthai/openenv-rl-training` | The SFT (QLoRA on Qwen2.5) and RL (GRPO over OpenEnv via TRL's `environment_factory`) training pipeline, the agentic-eval harness, and `FINDINGS.md`. | `training/sakthai-7b-lora/train.py` here pushes `Nanthasit/sakthai-context-7b-tools`; that adapter is the GRPO base there. The two repos share **no code** and have deliberately incompatible dependency pinsets — do not cross-import, and do not restate that repo's benchmark numbers here (`FINDINGS.md` and its workspace READMEs are the durable records). |
| `beer-sakthai/codeql-action` | A fork of `github/codeql-action` carrying local dependency-advisory remediation against the action's own dev-dependency tree. | Not referenced by any workflow here. `codeql.yml`, `bandit.yml`, `ossar.yml` and `scorecard.yml` pin **upstream** `github/codeql-action` by commit SHA — repointing them at the fork would break Scorecard's Pinned-Dependencies expectations and is not the intent of the fork. |

---

## Monorepo Structure

This repo is the shared source workspace for the whole Sak family, not just one
package. Only `personas/sakthai/sakthai/` is a build target; everything else is
personas, deployment config, training assets, or docs.

```
personas/          the six agents + the shared package (see below)
tests/             the one pytest suite (imports `sakthai`, ~95 test files)
library/           31 curated skills across 11 categories (a live skill root)
docs/              architecture, security, plans/specs under docs/superpowers/
scripts/           dev + maintenance scripts (compose_persona, export_agent_repo, …)
infra/             hermes-agents profiles, vm-agents systemd/env, pw-poc (npm), servicequotebot
services/          servicequotebot, inference-endpoint, HF dataset publishing, teams-copilot-mcp
apps/              agent_workflow_framework, sak_agent_dashboard
training/          LoRA/model runs, HF jobs, serving configs
evaluation_tasks/  lm-evaluation-harness task YAML + datasets (run-evals.yml)
sakthai-chat-cli/  folded-in copy of the standalone chat-CLI repo (see below)
product/ security/ profiles/ data/ bin/ dataset-cards/
```

`assets/` still exists on disk (two large branding PNGs) but is untracked — see
[`docs/repo-audit-2026-08-08.md`](docs/repo-audit-2026-08-08.md). The orphaned
root `skills/` directory and `migrated-repos-archive/` were removed in that same
cleanup; git history still has them.

### The persona package copies (read this before editing `sakthai/`)

`personas/sakthai/sakthai/` is **the** package: it is what `pyproject.toml`
installs (`[tool.setuptools.packages.find] where = ["personas/sakthai"]`), what
`import sakthai` resolves to, and what mypy/ruff/bandit/pytest run against.
Treat it as the source of truth for anything you are actually running.

`personas/shared/sakthai/` is the canonical *shared* copy that the other
personas point at. The wiring is **not uniform**, and the difference matters:

| Persona | How it gets `sakthai/` |
|---|---|
| `sakthai` | real directory — **the installed package** |
| `sakjules`, `saktan` | `sakthai -> ../shared/sakthai` symlink |
| `sakking`, `saksee`, `saksit` | a **partial real directory** that shadows the shared copy, plus a `sakthai~origin_main -> ../shared/sakthai` symlink alongside it |

Those three partial directories contain only a handful of files —
`agent/guardrails.py` and `web/server.py` for all three, plus
`cli/__init__.py` and `cli/system.py` for SakSee and SakSit. They exist because
security syncs committed files *into* what used to be a symlink path. The
guardrails copies are kept byte-identical to the canonical one (enforced by
`tests/test_persona_guardrails_parity.py`); the SakSee/SakSit `cli/` files are
**stale snapshots** that still register a `dashboard` command the real CLI no
longer has. Don't treat them as live code, and don't "fix" them by deleting the
shadowing files without checking the parity test first.

`personas/sakthai/sakthai/` has also genuinely diverged from
`personas/shared/sakthai/`: `config.py`, `auth.py`, `skills.py`,
`agent/loop.py`, `agent/tools.py`, `agent/chat.py`,
`agent/providers/__init__.py`, `cli/agent.py`, `cli/chat.py`,
`telegram/bot.py` all differ, and `agent/security_hardening.py` +
`agent/guardrails_hardened.py` exist only in the SakThai copy. Reconciling the
two is a known, tracked gap — not yet done.

### Personas

Six agents on disk (`config.PERSONA_NAMES`: sakking, sakthai, saksee, saksit,
sakjules, saktan); **SakThai is lead**. Each persona directory has:

- `SOUL.md` — identity, injected as a system-prompt prefix by `run/chat --persona`.
  Cross-persona consistency is CI-enforced by `tests/test_soul_consistency.py`.
- `skills/` — that persona's own skill overlay, one directory per skill directly
  under `skills/` (no category subdirectories, no duplicate-named skill folders).
  Counts on disk: SakThai 299, SakSee 182, SakJules 180, SakKing 106, SakSit 43,
  SakTan 13. `personas/sakthai/skills/.archive/` is an intentional exception —
  retired skills kept for history, excluded from discovery. A skill directory may
  itself contain a documented "umbrella" sub-skill (see
  `SakThai-environment-automation`'s `cron-watchdog-self-heal`) reached by direct
  file reads rather than the skill index.
- `config/` — `config.yaml` (default model/provider), `mcp.json`,
  `gateway_voice_mode.json`, and for some personas `workspace.yaml`.
- `agent-self-evolution` — symlink to `../shared/agent-self-evolution` for every
  persona except SakThai, whose copy is real and is the one CI builds.

Configured default models (`config/config.yaml`, consumed by
`config.persona_model_defaults()`): SakThai and SakSee `huggingface` /
`gemini-3.1-flash-lite`, SakKing `huggingface` /
`Qwen/Qwen3-Coder-30B-A3B-Instruct`, SakSit `huggingface` / `DeepSeek-V4-Flash`,
SakJules `huggingface` / `gemini-2.5-flash-lite`, SakTan `ollama` / `sakthai`.

**Shared resources:** `personas/shared/` holds `sakthai/` (the shared package
copy), `agent-self-evolution/` (template), `skills/` (3 `Sak-*` skills, identical
across all personas), and `model_roster`.

**Skill naming:** `Sak-` prefix for shared skills, `Sak<Name>-` for per-persona
skills — enforced by `sakthai skills validate --naming`.

### `sakthai-chat-cli/`

A self-contained folded-in copy of the standalone `sakthai-chat-cli` repo
(migrated 2026-08-01, see its `MIGRATION_NOTE.md`). It is deliberately **not**
merged into the canonical package: it has a Textual TUI redesign of `chat` the
canonical package lacks, while the canonical package has the `huggingface`
provider, guardrails hardening, and the dashboard subpackage it lacks. It has its
own `CLAUDE.md` and its own (stale) docs — notably it still describes a
five-persona roster. Don't sync the two trees casually, and don't treat its docs
as authoritative for this repo.

Everything below this point describes the SakThai agent package itself.

---

## Commands

```bash
# Setup (Python >=3.11)
cp .env.example .env      # then fill in ANTHROPIC_API_KEY
uv sync --all-extras      # install all project and optional dependencies

# Test / lint / type-check / security (mirrors .github/workflows/ci.yml)
uv run pytest tests/ -q                      # full unit suite (no network, no GCP)
uv run pytest tests/test_memory_store.py -q  # a single test file
uv run pytest -m "not integration" -q        # exclude network tests (default in CI)
uv run ruff check personas/sakthai/sakthai tests              # lint
uv run ruff format --check personas/sakthai/sakthai tests     # format check (drop --check to apply)
uv run mypy personas/sakthai/sakthai                          # strict type-check
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai   # security scan
make mutation                                # mutmut on core seam modules (slow, local-only, not in CI)
```

`uv sync --all-extras` (not plain `uv sync`) is required: `hypothesis` lives in
the `dev` extra and `tests/test_store_properties.py` fails collection without it,
which aborts the whole run.

Other `make` targets: `compose-personas` (rebuild full skill trees into
`build/personas/`), `export-agent-repos` / `export-agent-repo PERSONA=<name>`
(materialize standalone per-persona repo snapshots), `test`, `lint`.

`.githooks/` holds a `pre-commit` hook that fails if `uv.lock` is out of sync with
`pyproject.toml`, and a `pre-push` hook. Opt in with
`git config core.hooksPath .githooks`.

### CI

Nineteen workflows live in `.github/workflows/`. The ones that gate a change:

| Workflow | Trigger | What it does |
|---|---|---|
| `ci.yml` | push/PR to `main` | ruff check + format → mypy + bandit → pytest with coverage, on Python **3.11 and 3.12** |
| `pylint.yml` | every push | pylint over `personas/sakthai/sakthai` + `tests` |
| `secret-scan.yml` | push to `main`, all PRs | gitleaks (config `.gitleaks.toml`, which allowlists persona docs) |
| `dependency-audit.yml` | PRs touching `pyproject.toml`/`uv.lock`, weekly | pip-audit over `uv.lock` |
| `ossar.yml` | push/PR to `main`, weekly | open-source static analysis |
| `sonarcloud.yml` | push to `main` | SonarCloud analysis |
| `agent-self-evolution.yml` | push/PR touching `personas/sakthai/agent-self-evolution/**` | that subproject's own suite |
| `labeler.yml` | `pull_request_target` | PR labelling |
| `bandit.yml` | push/PR to `main`, weekly | bandit SARIF to code scanning |
| `codeql.yml` | push/PR to `main`, weekly | CodeQL (advanced setup) |

Scheduled / manual only, so they never block a PR: `continuous-security.yml`
(nightly), `verify-assets.yml` (daily HF asset check), `run-evals.yml` (weekly
lm-eval, installs the `evals` dependency group), `auto-dependency-update.yml`
(weekly), `stale.yml` (daily), `summary.yml` (on new issues), `manual.yml`,
`scorecard.yml` (push to `main` + weekly), `code-scanning-cleanup.yml`
(`workflow_dispatch` only).

**The code-scanning producers have to keep running.** A SARIF alert only closes
when a *newer* analysis from the same tool stops reporting it, so deleting the
workflow that produces it freezes its alerts open forever — findings against
files that no longer exist included. `b330e2f` deleted `scorecard.yml`,
`bandit.yml` and `codeql.yml` along with the eight `.github/workflows/*.lock.yml`
files Scorecard had flagged, which is why 41 Scorecard alerts sat open with
nothing left to fix; #1183 restored the producers. Don't delete one to silence
its alerts.

Everything Scorecard's Pinned-Dependencies check re-scans is pinned by digest:
every `uses:` by commit SHA, both Dockerfiles' base images by image digest, and
the pip installs by hash rather than by version — `bandit` from
`.github/bandit-requirements.lock` and `pylint` from
`.github/pylint-requirements.lock`, both generated by `scripts/gen_hash_lock.py`
(never hand-edited; the command is in each lock's header). A bare
`pip install pkg==x.y.z` is still a finding. Dependabot's
`uv`/`npm`/`github-actions`/`docker` ecosystems are what keep those pins current.
The two remaining open Scorecard findings, Branch-Protection and Code-Review,
are repository *settings*, not repository content — no commit can close them.

CodeQL runs as an *advanced* setup (`codeql.yml`), which requires default setup
to stay **disabled** in repository settings — the two cannot coexist, and every
advanced run fails while default setup is on. See the header of `codeql.yml`.
**No smoke-test job is wired into any workflow**, despite
`.claude/skills/run-sakthai-agent-v2/driver.py` existing — treat that as
available tooling, not an enforced gate.

Coverage floor is **96%** (`fail_under = 96`, branch coverage on) over the
`sakthai` package, with `telegram/bot.py` omitted from measurement; the suite
currently sits at **96.56%**. Run the lint→pytest sequence locally before
pushing; green CI is the bar for `main`.

---

## Runtime entry points

One package, four ways in — all sharing `~/.sakthai/memory.db` by default
(override the root with `SAKTHAI_HOME`). On the VM deployment, each persona's
process sets its own `SAKTHAI_HOME=$HOME/.sakthai/$AGENT`, so each persona
naturally gets its own memory shard at `~/.sakthai/<persona>/memory.db`. For
local dev, pass `--persona <name>` to `learn`/`recall`/`run`/`chat`/`memory` to
get the same per-persona shard without setting `SAKTHAI_HOME` yourself — see
"Per-persona memory sharding" below.

1. **CLI** — `sakthai <cmd>` (entry point `sakthai.cli:main`, wired in
   `cli/__init__.py`). Commands:
   - Memory: `learn`, `recall`, and the `memory` group —
     `show|stats|search|forget|forget-obs|backup|healthcheck|export|import|consolidate|consolidate-sessions|deduplicate|family|sync|pull`.
     `--persona <name>` is a **group-level** option on `memory` (and a plain
     option on `learn`/`recall`); `sync` and `pull` explicitly reject it (git/HTTP
     sync always targets the unscoped `memory.db`), and `family` merges across
     every persona's shard (or a `--personas a,b,c` subset) into one read-only view.
   - Agent: `run "<task>"` — `--provider`/`-p`
     (anthropic/google/openai/ollama/gateway/huggingface), `--model`,
     `--max-tokens`, `--max-iterations`, `--max-seconds`, `--with-skills <name>`
     (repeatable), `--no-mcp`, `--dry-run` (validate config, no API call),
     `--stream`, `--fast` (skip the 6-stage cycle), `--stateless` (don't
     load/append memory), `--caveman lite|full|ultra|wenyan-*` (token-compression
     skill), `--sandbox` (run inside the `Dockerfile.sandbox` container; only
     `memory.db` is bind-mounted; not combinable with `--persona`),
     `--persona <name>`, `-v/--verbose`.
   - Chat: `chat` — interactive multi-turn REPL over the same loop and memory.
   - Server: `mcp` (start the MCP stdio server).
   - Web: `web setup` (print/create the API bearer token), `web regen-token`.
   - Cycle: `cycle status|next|set|list`
   - Skills: `skills list|show|validate|create|sync-sakking`
   - Extensions: `extensions install|list|remove`
   - Sessions: `sessions list|show|clean`
   - Eval: `eval summary [--limit N] [--json]`
   - Hugging Face: `hf info|download <repo_id>`
   - System: `doctor`, `setup`, `status`, `tools`
   - There is **no `dashboard` command** — the CLI wiring was removed (a stale
     copy still registering it survives under `personas/saksee|saksit/sakthai/cli/`),
     but `dashboard/data.py` was later re-added as the KPI module behind the web
     API. See the dashboard note under "Other subsystems".

2. **Agent loop** — `sakthai run` drives a provider-agnostic tool-using loop
   (Claude, Gemini, or any OpenAI-compatible/Ollama/gateway/HF endpoint).

3. **Chat REPL** — `sakthai chat` drives the same loop turn by turn.

4. **MCP server** — `sakthai mcp` serves the same tools over JSON-RPC stdio.

`sakthai run` can also reach *out* to external MCP servers: tools discovered from
them are merged into the registry (namespaced `<server>__<tool>`) for that run.

A task starting with `/plugin:command` is treated as a **slash command**:
`_parse_slash_command()` in `agent/loop.py` resolves
`<root>/<plugin>/commands/<command>.md` across the skill roots, strips its
frontmatter, substitutes `$ARGUMENTS`/`$FEATURE`, and injects the body as a
system-prompt block.

---

## Architecture (the big picture)

A small, strictly layered package — each layer has one job. Data flows
CLI/MCP → agent loop → guardrails → tool registry → MemoryStore → SQLite. See
[`docs/architecture.md`](docs/architecture.md) for the full diagram.

### Core modules

- **`config.py`** — single source of truth for paths and env-var names
  (`sakthai_home`, `memory_db_path`, `persona_memory_db_path`, `sessions_dir`,
  `eval_log_path`, `persona_skills_dir`, `persona_mcp_config_path`,
  `persona_model_defaults`, `check_env`). Also owns secret handling:
  `SECRET_PATTERN`, `register_secret()`, `redact_secrets()` — used by the loop,
  the eval log, and the guardrails' output filter. Nothing else hard-codes a
  path; new paths and env-var names go here.
- **`auth.py`** — credential resolution. Always call `resolve_anthropic_client()`
  rather than constructing a client. Anthropic chain: `ANTHROPIC_API_KEY` →
  `ANTHROPIC_AUTH_TOKEN` → Claude CLI OAuth token. Google uses the Gemini CLI
  OAuth token. OpenAI/Ollama uses `resolve_openai_credentials` to locate the base
  URL and API key. Raises `AuthError` when no credentials are found.
- **`sandbox.py`** — backs `sakthai run --sandbox`. Builds/reuses a Docker image
  from `Dockerfile.sandbox` (layer-cached) and re-executes the task inside it;
  only `memory.db` is bind-mounted from the host. Egress is on by default (the
  model provider needs it) — set `SAKTHAI_SANDBOX_NETWORK` (e.g. `none`) to
  restrict it. Raises `SandboxError` if Docker isn't on `PATH`.
- **`giturl.py`** — `validate_git_url()`. Every user-supplied URL handed to a git
  subprocess (memory sync remotes, extension clone URLs) goes through it: it
  rejects `-`-leading values (option smuggling), remote-helper transports
  (`ext::…` runs arbitrary commands), and schemes outside http(s)/ssh/git/file.
- **`hf.py`** — Hugging Face Hub info/download; `huggingface_hub` is imported
  lazily so the package and test suite work without it installed.
- **`sakking_skills.py`** — idempotent import of SakKing's *learned* skills from
  `~/.sakking` into this repo as `SakKing-` prefixed skills (`skills sync-sakking`).

### Memory subsystem (`memory/`)

- **`memory/store.py`** — `MemoryStore` is the **only** code that touches SQLite.
  It holds *facts* (`Fact` dataclass: `id`, kind, key, value, source_session,
  created_at, updated_at, tags) and *observations* (`Observation` dataclass: `id`,
  summary, evidence_session_id, weight, confidence, created_at). Features:
  WAL concurrency, additive migrations in `_migrate_schema()` (ALTER TABLE only,
  under `BEGIN IMMEDIATE`), snapshot export/import (JSONL/CSV), deduplicate, and
  consolidate. `render_prompt_block()` injects memory into the system prompt.
- **`memory/provider.py`** — `SakThaiMemoryProvider` adapts the store to
  system-prompt blocks with context-window limiting.
- **`memory/backup.py`** — timestamped copy of `memory.db`, or of an explicit
  `db_path` (used to back up a persona's own shard).
- **`memory/sync.py`** — git-based JSONL export/import (multi-agent sync) and
  HTTP backup to a configured endpoint.
- **`memory/merged.py`** — `FamilyMemoryView`, a read-only view across every
  persona's memory shard plus the legacy unscoped `memory.db`, deduplicated and
  grouped by persona. Backs `sakthai memory family`.

### Per-persona memory sharding

Each of the six personas gets its own memory shard, `~/.sakthai/<persona>/memory.db`,
distinct from the legacy unscoped `~/.sakthai/memory.db`. This isn't a new
mechanism: it's the same convention already used in production by
`infra/vm-agents/sakthai-agent-run.sh`, which runs each deployed persona with
`SAKTHAI_HOME=$HOME/.sakthai/$AGENT` — `memory_db_path()` (which does honor
`SAKTHAI_HOME`) already resolved to that persona's shard for any process running
that way. What's new is `config.persona_memory_db_path(persona)`, which computes
the same `~/.sakthai/<persona>/memory.db` path directly from `Path.home()`,
**independent of the current process's own `SAKTHAI_HOME`**. That's what makes
two things possible that weren't before:

- **Local CLI parity** — `learn`/`recall`/`run`/`chat`/`memory <subcommand>` all
  accept `--persona <name>` so a local dev shell (which isn't running with a
  persona-scoped `SAKTHAI_HOME`) can still read/write a specific persona's shard.
  `run`/`chat --persona` additionally inject that persona's `SOUL.md` as a
  system-prompt prefix, resolve `--with-skills`/caveman/slash-commands against
  that persona's own skill overlay instead of SakThai's, auto-load its own
  `config/mcp.json` when `SAKTHAI_MCP_CONFIG` isn't already set, and default
  `--model`/`--provider` from its own `config/config.yaml` when those flags are
  left at their CLI defaults. `memory sync`/`memory pull` reject `--persona`
  (they always target the unscoped `memory.db` — no per-persona git/HTTP sync
  exists). `run --persona` can't combine with `--sandbox` (the sandbox only
  bind-mounts the unscoped `memory.db`).
- **The merged family view** — `FamilyMemoryView` (`memory/merged.py`) opens
  every persona's shard (skipping ones that don't exist yet) plus the legacy
  `memory.db` at once, regardless of which single persona the current process
  would otherwise be scoped to, and merges/dedups facts and observations across
  them. `sakthai memory family [--personas a,b,c] [--limit N] [--json]` is the
  CLI surface for it.

A persona's shard file only comes into existence on first write (`learn
--persona X`, or any `run`/`chat --persona X` that calls a memory-writing
tool) — an unwritten-to persona is simply absent from `memory family` output,
not an error.

### Agent subsystem (`agent/`)

- **`agent/tools.py`** — defines `BUILTIN_TOOLS` (14 tools, one schema + handler
  each): `learn`, `ingest_document`, `capture_lead`, `recall`, `search`, `forget`,
  `read_file`, `run_command`, `send_telegram_message`, `send_outlook_mail`,
  `read_outlook_mail`, `list_calendar_events`, `create_calendar_event`,
  `run_agent_loop`. Add a tool here and it appears in both the agent loop and
  the MCP server automatically. Note: `run_agent_loop` is filtered out of the
  in-loop tool set (it's MCP-only) and additionally guards on the
  `SAKTHAI_AGENT_ACTIVE` env var to block indirect recursion. The four Graph
  tools share `_graph_access_token()` / `_graph_request()` / `_graph_safe()`
  helpers: a refresh token (env `MS_GRAPH_REFRESH_TOKEN` or cached at
  `~/.sakthai/graph_token.json`, seeded via `scripts/graph_device_login.py`) is
  exchanged for a short-lived access token on every call.
- **`agent/registry.py`** — `ToolRegistry` keys tools by name; `with_tools()`
  merges sets (later tool wins on name clash, so plugins can shadow built-ins).
- **`agent/loop.py`** — `run_agent()` is the main orchestration loop. Injects
  `store.render_prompt_block()` into the system prompt, resolves slash commands,
  applies the context filter, dispatches every tool call through the guardrail
  policy, appends an `EvalRecord` per run, and writes session logs to
  `~/.sakthai/sessions/`. Returns `AgentResult` (iterations, stop_reason,
  tool_calls, usage). `client`, `store`, `guardrail_policy`, and `context_filter`
  are all injectable for testing. Defaults live here: `DEFAULT_MODEL =
  "claude-opus-4-8"`, `DEFAULT_MAX_TOKENS = 16000`, `DEFAULT_MAX_ITERATIONS = 12`.
- **`agent/chat.py`** — the interactive REPL behind `sakthai chat`. Keeps
  `rich`/`prompt_toolkit` I/O at the module edges (renderers take an injected
  `Console`, the loop takes an injected `read_input`) so conversation flow is
  testable without a terminal.
- **`agent/eval.py`** — local model-eval / MLOps logging. Every `run_agent` call
  appends one `EvalRecord` (model, provider, latency, usage, outcome) to
  `eval_log_path()` (default `~/.sakthai/eval.jsonl`); `summarize_evals()` backs
  `sakthai eval summary`. No cloud dependency.
- **`agent/usage.py`** — `UsageTracker` / `extract_usage()` for token counting.
- **`agent/context_filter.py`** — the `ContextFilter` protocol plus
  `TurnSummarizationFilter` (currently truncates older long turns rather than
  LLM-summarizing them) and `DEFAULT_CONTEXT_FILTER`, wired into `run_agent`.
- **`agent/prompt_builder.py`** / **`agent/context_manager.py`** — an extracted
  prompt-assembly seam (`build_system_prompt`, `render_skills_prompt_block`,
  `ContextManager`). Both are tested (`tests/test_prompt_builder.py`,
  `tests/test_context_manager.py`), but note that `agent/loop.py` still imports
  `render_skills_prompt_block` straight from `skills.py` — the loop has not been
  migrated onto `ContextManager` yet.
- **`agent/providers/`** — provider abstraction:
  - `base.py` — shared types (`Block`, `Response`), retry logic via `tenacity`
  - `anthropic_provider.py` — Claude via the `anthropic` SDK
  - `gemini_provider.py` — Gemini via `google-genai`
  - `openai_provider.py` — OpenAI-compatible APIs, Ollama, the `gateway`
    provider (OpenRouter/LiteLLM/Vercel/Cloudflare AI gateways), and the
    `huggingface` provider (HF Inference Providers router, via `HF_TOKEN`) — all via `httpx`
  - `__init__.py` — provider detection and client factory

### Security subsystem (`agent/guardrails*.py`, `agent/security_hardening.py`)

This is the largest single body of code in the package and the most actively
attacked surface — several rounds of Sentinel audits landed here.

- **`agent/guardrails.py`** (~1,400 lines) — `GuardrailPolicy` with pre- and
  post-execution checks around every tool call; `DEFAULT_POLICY` is what
  `run_agent` uses. Enforces: `run_command` blocked unless `SAKTHAI_SHELL_ALLOW`
  is set, dangerous/destructive shell commands, sensitive-path arguments
  (`_is_sensitive_path` over `_SENSITIVE_BASENAMES` / `_SENSITIVE_DIRS` /
  `_SENSITIVE_KEY_STEMS` / `_CRITICAL_ROOTS`, matched case-insensitively, across
  separators, for relative as well as absolute paths, including `make` recipe
  and `-C`/`-f` resolution), and secret-bearing tool output. A `GuardrailResult`
  carries a `GuardrailAction` (`ALLOW`/`DENY`) plus possibly-rewritten args.
- **`agent/security_hardening.py`** — defense-in-depth primitives: environment
  pinning/verification, MCP server validation and allowlisting,
  `EnhancedPathValidator`, `SymlinkDetector`, `ConfigFileIntegrity`, TOCTOU
  prevention, `ShellCommandHardener`, and an audit logger.
- **`agent/guardrails_hardened.py`** — wires those primitives on top of the base
  policy.

**When you change guardrails, you must sync the file.** `guardrails.py` is
copied per persona and `tests/test_persona_guardrails_parity.py` fails CI the
moment any copy drifts from `personas/sakthai/sakthai/agent/guardrails.py`
(it checks sakthai, sakjules, sakking, saksee, saksit). Roughly 15 test files
(`test_guardrails_*.py`, `test_sentinel_*.py`, `test_security_*.py`) cover this
area; add a regression test for every new bypass you close.

### MCP subsystem (`mcp/`)

- **`mcp/server.py`** — **inbound** JSON-RPC 2.0 stdio server. `handle_request`
  is a **pure function**, testable without a process. Reuses `BUILTIN_TOOLS` so
  behavior matches the agent loop exactly. Advertises protocol version
  `"2024-11-05"`.
- **`mcp/client.py`** — **outbound** stdio client. Launches external MCP servers,
  wraps their tools as local `Tool` objects, auto-namespaces as `<server>__<tool>`.
  Dependency-free; uses `select`-based timeouts (no asyncio).
- **`mcp/manager.py`** — `connect_servers()` context manager starts all configured
  servers, fails soft on errors, merges tools, cleans up on exit.
- **`mcp/servers.py`** — `MCPServerSpec` dataclass + `load_server_specs()`:
  discovers external server specs from `~/.sakthai/mcp.json` (or
  `SAKTHAI_MCP_CONFIG`, or the persona's own `config/mcp.json`) and extensions.

External MCP server config format:

```json
{
  "servers": [
    { "name": "my-server", "command": "npx", "args": ["-y", "my-mcp-pkg"] }
  ]
}
```

### CLI subsystem (`cli/`)

Click commands split by area; all sub-files imported by `cli/__init__.py`, which
binds groups under `*_cmd` aliases on purpose so `sakthai.cli.<name>` keeps
resolving to the *module* rather than the command object:

- `agent.py` — `run`, `mcp`
- `chat.py` — `chat`
- `memory.py` — `learn`, `recall`, `memory` group
- `system.py` — `doctor`, `setup`, `status`, `tools`, `web` group
- `skills.py` — `skills` group
- `cycle.py` — `cycle` group
- `extensions.py` — `extensions` group
- `eval.py` — `eval` group
- `sessions.py` — `sessions` group
- `hf.py` — `hf` group

There is no `dashboard.py` here — see the dashboard note below.

### Other subsystems

- **`cycle/`** — six-stage Dream → Hope → Care → Joy → Trust → Growth state
  machine. `stages.py` defines the `Stage` StrEnum plus a `StageInfo` table
  (goal, commands, guidance per stage); `state.py` persists the current stage as
  a single fact in the store (kind=`cycle`, key=`current_stage`).
- **`skills.py` + `library/` + `personas/*/skills/`** — parse/catalog/validate
  `SKILL.md` files. `default_skill_roots(persona=None)` returns, in order:
  the persona's own overlay (`persona_skills_dir(persona)`, else `SKILLS_DIR` =
  `personas/sakthai/skills/`), `personas/shared/skills/`
  (`SHARED_SKILLS_DIR`/`LIBRARY_DIR`, 3 skills identical across personas), root
  `library/` (`CURATED_LIBRARY_DIR`, 31 curated skills across 11 categories,
  pre-dating the `Sak-`/`SakThai-` convention), `~/.sakthai/extensions`, and the
  Gemini extensions dir if it exists. The **root-level `skills/` directory is not
  a root** — it's orphaned content. Skills reach the system prompt via
  `render_skills_prompt_block()`.
- **Dashboard — backend only.** The CLI's `dashboard` command and the frontend
  (both the old in-package bundle and the repo-root Vite project) are gone, but
  `personas/sakthai/sakthai/dashboard/data.py` was re-added: it collects
  KPI/lead/revenue metrics from the memory store and is served by
  `web/server.py`'s `/api/stages` endpoint (covered by
  `tests/test_dashboard_data.py`). `_STATIC_ROOT` resolves to
  `personas/sakthai/sakthai/dashboard/dist/`, which does not exist, so the web
  server runs API-only and static requests fall through to 404.
- **`web/server.py`** — HTTP API server exposing `/health`, `/api/stages`, and
  `/api/ecosystem`. Refuses non-loopback binds unless `SAKTHAI_WEB_ALLOW_PUBLIC`
  is set. **Every path except `/health` now requires the bearer token** —
  `/api/*` answers 401/403 as JSON, and static paths get a plaintext 401, closing
  the gap described in
  `docs/superpowers/specs/2026-08-03-sakthai-web-auth-design.md`. The token comes
  from `_get_or_create_bearer_token()` (stored as a `web_auth` fact in
  `memory.db`, managed with `sakthai web setup` / `web regen-token`). Static
  serving additionally canonicalises the request path against `_STATIC_ROOT`
  before delegating.
- **`extensions/install.py`** — clones skill/MCP bundles from git into
  `~/.sakthai/extensions` (URLs validated via `giturl.py`, removal containment-
  checked); `list`/`remove` manage installed bundles.
- **`learn/capture.py`** — `learn()` one-shot fact capture used by `sakthai learn`.
  **`learn/ingest.py`** — `ingest_document`, splitting Markdown/text/CSV into facts.
  **`lead/capture.py`** — `capture_lead()`, storing a structured lead fact.
- **`telegram/`** — a standalone `python-telegram-bot` polling bot (`bot.py`,
  `config.py`, `workflow_executor.py`). `bot.py`'s `/workflow <name>` handler
  runs `run_agent()` **in-process** via `asyncio.to_thread` — it does not shell
  out. `workflow_executor.py`'s `run_workflow()`/`_workflow_command()` (which
  *do* shell out to `python -m sakthai run ... --with-skills <name> --fast
  --stateless`) are unit-tested but currently unused by `bot.py` (only
  `get_available_workflows()` is called from there). `telegram/config.py`
  re-exports `ALLOWED_USER_IDS`/`TELEGRAM_BOT_TOKEN` from the central
  `config.py`. `workflow_executor.py`'s skill discovery is persona-aware: it uses
  `config.persona_skills_dir(config.sakthai_persona())` when `SAKTHAI_PERSONA` is
  set (see `infra/vm-agents/env-templates/*.env.example`), falling back to
  `config.SKILLS_DIR`. This subpackage is the one part of the package held to a
  lower bar: mypy skips it and coverage omits `bot.py`.

---

## Tests

Tests live in `tests/` (95 test files, 1,978 tests, ~23,700 lines) and are the only suite —
there is no per-persona test tree. All tests are hermetic: no network, no GCP
credentials. Integration tests that may hit real endpoints (Ollama, Anthropic)
are marked `@pytest.mark.integration` and self-skip when credentials/endpoints
are absent; CI excludes them with `-m "not integration"`.

Key test areas:

- **Memory** — `test_memory_store.py`, `test_memory_sync.py`, `test_memory_aux.py`,
  `test_memory_concurrent.py`, `test_memory_merged.py`,
  `test_memory_secrets_redaction.py`, `test_store_migrations.py`,
  `test_store_properties.py` (hypothesis)
- **Agent** — `test_agent_loop.py`, `test_agent_loop_failure_seams.py`,
  `test_tools.py`, `test_tools_overrides.py`, `test_registry.py`, `test_usage.py`,
  `test_chat.py`, `test_eval*.py`, `test_context_filter.py`,
  `test_context_manager.py`, `test_prompt_builder.py`, `test_providers*.py`,
  `test_provider_contracts.py`, `test_provider_resilience.py`
- **Security** — `test_guardrails*.py` (10 files), `test_sentinel_*.py` (6 files),
  `test_security_hardening.py`, `test_security_sentinel.py`,
  `test_persona_guardrails_parity.py`, `test_sakking_skill_security.py`,
  `test_giturl.py`, `test_web_auth.py`
- **MCP** — `test_mcp_server.py`, `test_mcp_client.py`,
  `test_mcp_client_resilience.py`, `test_mcp_manager.py`, `test_mcp_servers.py`,
  `test_mcp_main.py`
- **CLI** — `test_cli.py`, `test_cli_system.py`, `test_cli_eval.py`,
  `test_cli_consolidate_sessions.py`, `test_sessions_cli.py`, `test_entrypoint.py`
- **Repo/persona invariants** — `test_soul_consistency.py`,
  `test_compose_persona.py`, `test_export_agent_repo.py`,
  `test_persona_workspace_workflows.py`, `test_train_configs.py`
- `conftest.py` — shared fixtures: in-memory `MemoryStore`, temp dirs,
  mock Anthropic clients

**Pattern for new tests:** inject a fresh `MemoryStore(":memory:")` (SQLite
in-memory); mock the Anthropic/Gemini/OpenAI client at the boundary; never
reach out to a real endpoint. Use `tmp_path` fixtures for file I/O.

---

## Conventions specific to this repository

- **The memory store is the seam.** Anything touching SQLite goes through
  `MemoryStore`; anything an agent or MCP client can do goes through the
  `agent/tools.py` registry. Don't bypass either.
- **Config centralization.** No module hard-codes a path — everything goes through
  `config.py`. New paths and env-var names belong there.
- **Dependency injection over global state.** `run_agent()` and `handle_request()`
  accept injectable client, store, policy, and filter arguments; this is what
  makes them testable. Don't use module-level globals for these.
- **Tests assume no network and no GCP credentials.** Keep them hermetic; inject
  clients/stores instead of reaching out.
- **Sandbox defaults are deliberate.** `read_file` is restricted to cwd +
  `~/.sakthai` + `SAKTHAI_READ_ALLOW`; `run_command` is **opt-in** via
  `SAKTHAI_SHELL_ALLOW`. Don't widen these without reason.
- **Guardrail changes must be synced across personas.** Copy the canonical
  `personas/sakthai/sakthai/agent/guardrails.py` to every persona copy, or
  `tests/test_persona_guardrails_parity.py` fails CI.
- **Not linted / not type-checked:** ruff excludes `library/` and `scripts/`;
  mypy covers only `personas/sakthai/sakthai`. Don't "fix" lint/types in the
  other trees.
- **mypy is `strict`** over the package, with exactly one exemption:
  `sakthai.telegram.*` is `ignore_errors = true` (an early-stage standalone
  prototype). Keep all other new code strict-clean.
- **Schema migrations are additive.** Use `ALTER TABLE` only, under
  `BEGIN IMMEDIATE`. Never drop columns or tables in a migration.
- **Tool registry is the MCP server.** `BUILTIN_TOOLS` in `agent/tools.py` is
  the single definition; `mcp/server.py` reuses it directly. Add a tool once and
  it appears in both surfaces.
- **Later tool wins on name clash.** In `ToolRegistry.with_tools()`, a plugin or
  external MCP server tool can shadow a built-in by registering under the same
  name.
- **Ollama uses 127.0.0.1, not localhost.** IPv6 resolution for `localhost` breaks
  some environments; the OpenAI provider explicitly connects to `127.0.0.1`.
- **Scripts must fix up `sys.path`.** There is no root-level `sakthai/` package;
  `import sakthai` only works because of the editable install. Any script under
  `scripts/` that must run outside the installed env has to
  `sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))` first.

---

## Workflow: Plan First

- **Always read and update `PLAN.md` before starting any work** in this repository.
  - Mark tasks `[ ]` → `[/]` (in progress) at the start of a phase.
  - Mark `[/]` → `[x] YYYY-MM-DD` (done with date) once the work is verified.
- **Never start coding a phase until it is checked off in PLAN.md** as in-progress.
- Terse one-word or short user approvals like `process`, `go`, `do it`, `run` after a plan summary = explicit approval to execute all queued plan steps.

### PLAN.md Safety

- **Never overwrite `PLAN.md` entirely.** Use targeted chunk replacements only.
- When marking tasks complete, find and replace only the specific `- [ ]` or `- [/]` line(s) — not whole sections.
- After any edit to `PLAN.md`, immediately re-read it to verify the surrounding content is intact before continuing.

`PLAN.md` is the master index; sub-plans live in `product/PLAN.md`,
`security/SECURITY_FIXES_PLAN.md`, `personas/*/PLAN.md`, and
`docs/superpowers/plans/`. Link, don't duplicate.

---

## Key environment variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Anthropic auth for `sakthai run` / `mcp` (or `ANTHROPIC_AUTH_TOKEN`, or Claude CLI OAuth) |
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Gemini auth (or Gemini CLI OAuth token) |
| `OPENAI_API_KEY` | Key for OpenAI-compatible gateway (defaults to `nokey`) |
| `OPENAI_API_BASE` / `OPENAI_BASE_URL` | Base URL for OpenAI-compatible endpoint |
| `OLLAMA_HOST` | Ollama server address (default: `http://127.0.0.1:11434`) |
| `SAKTHAI_GATEWAY_URL` | Base URL of an OpenAI-compatible AI gateway (OpenRouter/LiteLLM/Vercel/Cloudflare) — enables the `gateway` provider |
| `SAKTHAI_GATEWAY_API_KEY` | Bearer token for the AI gateway (defaults to `nokey`) |
| `HF_TOKEN` | Hugging Face access token — used by `sakthai hf` and the `huggingface` provider |
| `SAKTHAI_HF_API_BASE` | HF Inference Providers router base URL (default: `https://router.huggingface.co/v1`) |
| `SAKTHAI_HOME` | Override the `~/.sakthai` root (memory db, sessions, extensions, eval log) |
| `SAKTHAI_PERSONA` | Persona identity for systemd/Telegram launches — scopes skill discovery |
| `SAKTHAI_MODEL` / `SAKTHAI_PROVIDER` | Default model/provider for non-interactive launches |
| `SAKTHAI_FAST` / `SAKTHAI_STATELESS` / `SAKTHAI_NO_MCP` | Env equivalents of `--fast` / `--stateless` / `--no-mcp` |
| `SAKTHAI_WITH_SKILLS` | Comma-separated skill names injected into the system prompt |
| `SAKTHAI_SYSTEM_PROMPT` / `SAKTHAI_SYSTEM_PROMPT_FILE` | Inline or file-backed system-prompt prefix |
| `SAKTHAI_READ_ALLOW` | `os.pathsep`-separated extra paths the `read_file` tool may read |
| `SAKTHAI_SHELL_ALLOW` | Any non-empty value enables the `run_command` tool |
| `SAKTHAI_SANDBOX_NETWORK` | Docker `--network` value for `run --sandbox` (e.g. `none` to cut egress) |
| `SAKTHAI_MCP_CONFIG` | Override the external MCP server config path |
| `SAKTHAI_MCP_TIMEOUT` | Seconds to wait for an external MCP server reply (default: 30) |
| `SAKTHAI_MCP_ENV_PASSTHROUGH` | Env vars forwarded to spawned MCP servers |
| `SAKTHAI_EVAL_LOG` | Override the eval/MLOps JSONL log path (default `SAKTHAI_HOME/eval.jsonl`) |
| `SAKTHAI_WEB_ALLOW_PUBLIC` | Opt-in to non-loopback binds for the web server (default: refused — loopback-only) |
| `SAKTHAI_AGENT_ACTIVE` | Set by the loop itself; the `run_agent_loop` recursion guard reads it |
| `SAKKING_HOME` | Override the SakKing data dir (default `~/.sakking`) for `skills sync-sakking` |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` / `TELEGRAM_ALLOWED_USER_IDS` | Telegram gateway and the `send_telegram_message` tool |
| `MS_GRAPH_CLIENT_ID` / `MS_GRAPH_TENANT_ID` / `MS_GRAPH_REFRESH_TOKEN` | Microsoft Graph mail + calendar tools (seed via `scripts/graph_device_login.py`) |

---

## Local skills for this repo

- `run-sakthai-agent-v2` — use when asked to build, run, drive, or smoke-test the SakThai CLI/agent loop/MCP server/web API in this monorepo.
- `Sak-family-auto-cycle` — use when asked to run the six-persona (SakKing/SakThai/SakSee/SakSit/SakTan/SakJules) auto-cycle or dispatch them as a team.

## Skills format

A skill is a directory containing a `SKILL.md` with a YAML frontmatter block:

```yaml
---
name: my-skill
category: coding
description: One-line summary of what this skill does
version: "1.0"
platforms: [linux, macos, windows]   # host OSes the skill supports
metadata:
  sakthai:
    tags: [python, testing]
    related_skills: [other-skill]
---

Skill body goes here. This is injected into the agent system prompt when the
skill is active.
```

Note: `tags`/`related_skills` must be nested under `metadata.sakthai` — a flat
top-level `tags:`/`related_skills:` is silently ignored by the parser in
`skills.py`.

Discovery roots are listed under "Other subsystems" above. Run
`sakthai skills list` to see everything discovered, and `sakthai skills validate
--naming` to check the `Sak-`/`Sak<Name>-` prefix convention.
`sakthai run --dry-run` validates `--with-skills` names and fails on
unresolved ones; a live run warns and skips them.

A skill directory may also carry `commands/<name>.md` files, which become
`/skill:command` slash commands for `sakthai run` (see "Runtime entry points").

---

## Adding a new built-in tool

1. Add a `Tool(name=..., description=..., input_schema=..., handler=...)` to
   `BUILTIN_TOOLS` in `personas/sakthai/sakthai/agent/tools.py`.
2. The tool automatically appears in both `sakthai run` (agent loop) and
   `sakthai mcp` (MCP server) — no other wiring needed.
3. Write a test in `tests/test_tools.py` using an injected `MemoryStore(":memory:")`.
4. If the tool touches the filesystem or network, sandbox it appropriately
   (follow the `read_file` / `run_command` patterns) and check whether
   `agent/guardrails.py` needs a matching rule.

---

## Docs

| File | Contents |
|------|---------|
| `docs/architecture.md` | Full layer diagram and SQLite schema |
| `docs/capabilities.md` | Feature list |
| `docs/plugins.md` | Skills and MCP extensibility |
| `docs/replication.md` | Multi-agent memory sync |
| `docs/runtimes.md` | CLI / agent loop / MCP server |
| `docs/workspace.md` | Dev environment setup |
| `docs/og_parity_audit.md` | Comparison with original SakThai |
| `docs/integrations.md` | Composio and cross-agent communication recipes |
| `docs/skill-naming.md` | The `Sak-` / `Sak<Name>-` naming convention |
| `docs/agent-diagnosis.md` | Standalone run checklist and runtime notes |
| `docs/SOUL.md` · `docs/USER.md` · `docs/OPERATING_CONTRACT.md` | Team identity · Beer's profile · agent operating rules |
| `docs/SECURITY.md` · `docs/security-hardening.md` · `docs/SECURITY_HARDENING_IMPLEMENTATION.md` | Security policy/architecture · audit findings and the prevention pattern + regression test for each · implementation notes |
| `docs/security_audit_2026-07-11.md` · `docs/security_audit_2026-07-12.md` | Point-in-time audit reports |
| `docs/superpowers/plans/` · `docs/superpowers/specs/` | Dated feature plans and design specs |
| `AGENTS.md` | Repo guidelines + the SakJules PR protocol |
