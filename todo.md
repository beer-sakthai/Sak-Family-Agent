# sakthai-agent-v2 — roadmap

Living task list. Work top-to-bottom; check off with a dated one-line note when done.

## Phase 0 — Quality cleanup (from review cons)
- [x] Make brittle CLI test assertions robust (assert on stable tokens / exit
      codes, not fragile full-string output) — 2026-06-15: shifted mutating-command
      tests to store/file side-effect checks; dropped count/spacing-coupled output
- [x] Add a smoke test for dashboard/app.py (import + render the data path with
      a fake store) or document why it stays excluded — 2026-06-15: importorskip-
      guarded smoke test exercises the figure builders via stubbed st (5 tests,
      pass with [dashboard] extra, skip otherwise); documented the coverage omit
- [x] Depth pass: targeted correctness tests for memory/store.py migrations and
      the agent loop's stop/iteration logic — 2026-06-15: test_store_migrations.py
      (fresh→v3, idempotent reopen, legacy facts-only + confidence backfill) and
      loop cases (terminal max_tokens, unexpected stop, pause_turn, deadline trip)

## Phase 1 — Runtime plugin foundation (use ANY MCP / skill, no manual wiring)
- [x] Dynamic tool registry: merge builtin + runtime tools; make tool lookup
      registry-driven (agent/tools.py, new agent/registry.py) — 2026-06-15: added
      ToolRegistry (get/schemas/with_tools, last-wins merge); routed loop dispatch
      through it, fixing a latent bug where injected tools were advertised but not
      dispatchable. 178 tests.
- [x] MCP client (sakthai/mcp/client.py): spawn an external MCP server over
      stdio, initialize, tools/list, tools/call; reuse the JSON-RPC shapes from
      mcp/server.py; graceful failure (log + continue) — 2026-06-15: StdioMCPClient
      with select-timeout reads, as_tools(prefix=) wrapping, MCPClientError/
      MCPToolError fail-soft; 6 e2e tests vs the real server (184 passed)
- [x] Parse mcpServers manifests ({command,args,env}) from gemini-extension.json
      / .mcp.json (extend extensions/install discovery beyond names) — 2026-06-15:
      mcp/servers.py (MCPServerSpec, parse_mcp_servers, load_server_specs from
      ~/.sakthai/mcp.json + extension manifests, mcp.json wins). 192 passed.
- [x] Wire MCP-client tools into run_agent: load configured servers, convert
      their schemas to Tool objects, merge into the loop, route calls back —
      2026-06-15: mcp/manager.connect_servers (fail-soft, <server>__ namespacing,
      cleanup); proven e2e — an agent run dispatches sk__learn to an external MCP
      subprocess which writes to its own DB. 196 passed.
- [x] Skill injection: render selected SKILL.md bodies into the system prompt
      (loop._build_system + skills.render_skills_prompt_block); collect from
      ~/.sakthai/extensions too — 2026-06-15: render_skills_prompt_block +
      default_skill_roots (bundled+library+extensions); run_agent skills= and
      `sakthai run --with-skills`; injection verified in the system prompt. 203
      passed. **Phase 1 complete.**
- [x] CLI + config: auto-load all configured servers from ~/.sakthai/mcp.json so
      it works with zero flags; `--no-mcp` to opt out — 2026-06-15: `sakthai run`
      wraps run_agent in connect_servers() (no-op when none configured), merges
      external tools into the loop; 2 CLI tests (autoload + --no-mcp). 198 passed.

## Phase 2 — Multi-runtime / local model (self-driving, no API key)
- [x] OpenAI-compatible / Ollama provider — 2026-06-15
- [x] Run-under-another-AI: run_agent_loop MCP tool — 2026-06-15
- [x] docs/plugins.md + docs/runtimes.md — 2026-06-15

## Phase 3 — Hardening
- [x] Hermetic tests for client, registry, and new provider — 2026-06-15
- [x] Update CLAUDE.md / GEMINI.md / README / docs/architecture.md — 2026-06-15

## Phase 4 — Concurrency & safety hardening
- [x] SQLite WAL mode + BEGIN IMMEDIATE — 2026-06-15
- [x] Indirect recursion safety guard — 2026-06-15
- [x] Context token pruning for run_agent_loop — 2026-06-15

## Phase 5 — Robustness (make the agent run reliably) ← CON #6, #8, #10
Goal: the agent runs dependably — retry on transient failures, track costs,
manage sessions. One task at a time: local gate (ruff → format → mypy →
bandit → pytest) → commit → push → **wait for CI green** → next.

- [x] 5.1 — API retry with exponential backoff — 2026-06-15
- [x] 5.2 — Token usage tracking — 2026-06-15
- [x] 5.3 — Session management CLI — 2026-06-15
- [x] 5.4 — Robust provider construction — 2026-06-15
- [x] 5.5 — Safe memory backup — 2026-06-15
- [x] 5.6 — Preflight `sakthai run --dry-run` — 2026-06-15: loop.preflight()
      resolves provider/effective-model/credential-source/tool-count with no
      client build or API call; `--dry-run` prints the report and exits non-zero
      when no credentials. 9 tests (4 preflight + 2 CLI). **Phase 5 complete.**

## Phase 6 — Architecture cleanup ← CON #1, #4
Goal: loop.py drops from ~700 to ~300 lines by extracting providers.

- [x] 6.1 — Extract providers — 2026-06-15: new `sakthai/agent/providers/`
      package (base.py owns Block/Response + retry + shared adapters;
      anthropic/gemini/openai modules own their call + message adaptation;
      __init__ owns detect_provider/build_client). loop.py is now orchestration
      (823→369 lines) with back-compat shims so the import/patch surface is
      unchanged. 239 tests green.
- [x] 6.2 — Integration test markers — 2026-06-15: registered the `integration`
      marker in pyproject; CI now runs `-m "not integration"`; tests/test_integration.py
      holds live Anthropic/Ollama smokes that self-skip without creds/endpoint, so
      the default run stays hermetic. **Phase 6 complete.**

## Phase 7 — Streaming output ← CON #2, #3
Goal: progressive token display instead of waiting for full response.

- [x] 7.1 — Streaming callback interface — 2026-06-15: `on_token` param threaded
      through run_agent → all three provider calls (accepted now; provider impls
      land in 7.2/7.3); `sakthai run --stream` wires it to stdout and falls back
      to printing the final text when nothing streamed. 4 tests.
- [x] 7.2 — Anthropic streaming — 2026-06-15: call_anthropic streams via
      client.messages.stream() when on_token is set, forwarding text deltas and
      returning the assembled final message (same shape as create()); non-stream
      path unchanged. 2 tests.
- [x] 7.3 — OpenAI-compat streaming — 2026-06-15: when on_token is set and the
      client supports `.stream`, call_openai_compat consumes SSE (stream + usage),
      forwards text deltas, and reassembles tool-call fragments by index into the
      same response shape as the non-stream path. 2 tests. **Phase 7 complete.**

## Phase 8 — Dashboard & observability ← CON #9
Goal: session history + token charts in the Streamlit dashboard.

- [x] 8.1 — Session data layer — 2026-06-15: collect_session_data() reads the
      run_agent session JSON logs and aggregates totals + by-day + by-model +
      recent runs (empty-safe, skips malformed files). 4 tests.
      (sakthai/dashboard/data.py, tests/test_dashboard_sessions.py)
- [x] 8.2 — Dashboard UI — 2026-06-15: split the app into Memory + Agent Activity
      tabs; the new tab shows session KPIs, a sessions-per-day timeline, token
      usage by model, and a recent-sessions table (builders smoke-tested under the
      dashboard extra). **Phase 8 complete.**
      (sakthai/dashboard/app.py, tests/test_dashboard_app.py)

## Phase 9 — Future (deferred to v3)
- [ ] Google ADK / Vertex AI cloud agent port ← CON #5
- [ ] Multi-user / multi-tenant database isolation ← CON #7

## Phase 10 — Addressing Trade-offs & Run Readiness
Goal: Make the agent fully runnable and resolve past architecture cons. One task at a time, check off when done.

- [x] 10.1 — Documentation & Clarification: Update README to clarify v1 deprecation and proprietary license terms.
- [x] 10.2 — Fast-Track Mode: Add `--fast` flag to bypass the rigid 6-stage cycle for simple runs.
- [x] 10.3 — Remote Memory Sync: Implement `sakthai memory sync` for cloud or git backups to reduce local state dependency.
- [x] 10.4 — Basic Cloud Runtime Stubs: Migrate Google ADK / Vertex AI skeleton into v2 for future deployment.

## Phase 11 — Robust Memory Sync & Scalability
Goal: Resolve cons in the Git sync implementation and prepare for standalone agent resilience.

- [x] 11.1 — Incremental JSON Exports: Split `snapshot.json` into `facts.jsonl` and `observations.jsonl` to reduce Git bloat.
- [x] 11.2 — Auto-Merge Strategy: Intercept Git conflicts on JSONL files and merge by `id`.
- [x] 11.3 — Zero-Dependency HTTP Fallback: Provide a simple HTTP POST export fallback for syncing without local Git.
- [x] 11.4 — SQLite Replication Exploration: Evaluate wrapper for Turso/Litestream true DB replication.

## Phase 12 — OG → v2 information parity (audit + backfill)
Goal: nothing of value in the locked OG blueprint is lost in the rewrite.
Re-derive (never copy) each item, or consciously decline it. Process with
caution — v2 is intentionally curated, so triage before bulk-adding.

> Decisions for 12.1–12.5 are recorded in [`docs/og_parity_audit.md`](docs/og_parity_audit.md).
> 📋 items below = decision made; re-derivation of the keep-lists is scoped follow-on
> work pending sign-off (no verbatim copying).

### 12.1 — Identity & governance docs (high value, low risk)
- [x] Re-derive SAKTHAI.md (project identity) for v2 — 2026-06-17: v2-accurate
      agent identity; tool set updated (adds send_telegram_message, run_agent_loop)
- [x] Add CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md (v2-accurate: uv, no app/ bundle)
      — 2026-06-17: CONTRIBUTING/SECURITY already present & v2-accurate (verified);
      re-derived CODE_OF_CONDUCT.md (MIT-aligned; OG's "proprietary/CLA" wording corrected)
- [x] Decide on WORKSPACE.md — 2026-06-17: DECLINED (OG's is a workspace-root CLAUDE.md
      for Hermes/colab/root-playwright; none exist in v2; context already in CLAUDE.md + README + ~/CLAUDE.md)
- [x] CHANGELOG.md — generate from v2 history, do NOT copy OG — 2026-06-17: Keep-a-Changelog
      built from v2 phase log + git; OG's 993-line v1 changelog not copied
- [x] DASHBOARD_IMPROVEMENTS.md — 2026-06-17: declined the 426-line v1 proposal (most done
      in Phase 8 / v3-scoped); 3 still-open ideas folded into og_parity_audit.md#dashboard-backlog
- [x] Re-derive SAKTHAI.md (project identity) for v2 — 2026-06-17
- [x] Add CODE_OF_CONDUCT.md and confirm CONTRIBUTING.md / SECURITY.md exist — 2026-06-17
- [x] Decide on WORKSPACE.md (re-derived as docs/workspace.md) — 2026-06-17
- [x] CHANGELOG.md (generated from v2 history) — 2026-06-17
- [x] DASHBOARD_IMPROVEMENTS.md (folded into docs/dashboard_improvements.md) — 2026-06-17

### 12.2 — Doc / data info files
- [x] Port docs/devtools_ai_capabilities.md — 2026-06-17: DECLINED (445-byte browser-DevTools note; no such workflow in v2)
- [x] Re-derive data/hf_dataset_readme.md — 2026-06-17: DECLINED (v2 ships no dataset; data/ holds only the snapshot format)

### 12.3 — Sakthai-own skills backfill (skills/  — OG 111 vs v2 17)
- [x] Triage the ~80 OG sakthai-* skills + re-derive keepers — 2026-06-17: triaged by
      prefix in the audit. Most keepers were ALREADY in v2 library/ (recall/search/
      consolidate/planning/sessions/tools/prompting/providers/feedback/patterns).
      Re-derived the 3 genuine gaps fresh: library/memory/sakthai-memory-store,
      library/agent/sakthai-agent-reasoning, library/learning/sakthai-learning-curation
      (validated with parse_skill). Remaining OG skills declined as v1-specific/off-mission.
- [x] Decide on the ~18 GCP/data skills + media/ — 2026-06-17: OUT OF SCOPE / defer to v3
      cloud port (no BigQuery/Spanner/Dataflow surface in v2)

### 12.4 — Library corpus triage (library/ — OG 357 files / 23 categories vs v2 12)
- [x] Per-category keep/drop decision — 2026-06-17: recorded in the audit (decline
      creative/mlops/web/media/apple/email/social/etc.; cherry-pick research/security/devops/
      software-development/github/red-teaming/autonomous-ai-agents/productivity)
- [x] Re-derive kept skills into v2's curated library/ grouping — 2026-06-17: re-derived 5 kept skills (codebase-knowledge, github-workflows, debugging, tdd, and red-teaming). 48 skills validated.
- [x] CAUTION recorded — 2026-06-17: category-level rationale in the audit; per-file rationale at re-derive time

### 12.5 — Code / feature module gaps (roadmap, evaluate vs decline)
- [x] Evaluate all module gaps — 2026-06-17: recorded in the audit. sandbox.py + an eval/ harness
      are the strongest re-derive candidates; hf.py/gemini_plugin.py deferred; terraform/app/ADK → v3;
      web gallery + LoRA/colab/finetune + artifacts/junk → declined

### 12.6 — Extension Integration
- [x] Workflows & Caveman Integration Audit (docs/workflows_caveman_integration_audit.md) — 2026-06-17
- [x] Unified extension paths & discovery (~/.gemini/extensions/) — 2026-06-17
- [x] Namespaced slash command router (/plugin:command) in loop.py — 2026-06-17
- [x] Native caveman runtime toggle (--caveman) in sakthai run — 2026-06-17

## Phase 13 — Local-run reliability & CI breadth (from 2026-06-18 run session)
Goal: close the gaps surfaced while driving a live `sakthai run` against local
Ollama. No test/lint/type/security section currently fails — the full gate is
green on Python 3.11/3.12 and 3.14 (ruff, format, mypy, bandit, 668 passed /
1 skipped). These are reliability + coverage improvements, not bug-fixes for a
red CI. One task at a time: local gate → commit → push → wait for CI green.

- [x] 13.1 — Ollama localhost/IPv6 fix — 2026-06-18: `config.ollama_host()` now
      defaults to `http://127.0.0.1:11434` (was `localhost`); updated the docstring,
      the `OLLAMA_HOST` env note (`config.py:31`), and docs/runtimes.md. Fixes
      `[Errno 111] Connection refused` from `sakthai run -p ollama` on hosts where
      `localhost`→IPv6 `::1` but Ollama binds IPv4-only. 2 regression tests
      (default-is-IPv4 + env honoured/slash-stripped) in test_config_reports.py.
- [x] 13.2 — Surface text-emitted tool calls — 2026-06-18: added
      `_detect_untriggered_tool_call()` (conservative — parses JSON, optionally
      strips a markdown fence, matches OpenAI/`name`/`tool`/`function` shapes, and
      only fires when the named tool is *registered*). The terminal-stop branch of
      `run_agent` now logs a warning + emits a `tool_call_in_text` event without
      hard-failing (model quality, not an app error); nothing is dispatched. 11
      tests (positive/negative parametrized + an end-to-end run).
- [ ] 13.3 — Widen CI Python matrix: add `"3.13"` to
      `.github/workflows/ci.yml:33` (`["3.11", "3.12"]`). The full gate already
      passes clean on 3.14 locally, so 3.13 is low-risk and catches newer-Python
      regressions earlier. Refresh `uv.lock` / `requires-python` classifiers if CI
      flags drift.

---

## Log
- 2026-06-18 — Full CI gate run, all green on Python 3.14 (ruff ✓, format ✓,
  mypy strict ✓, bandit ✓, pytest 668 passed / 1 skipped [streamlit] / 2 deselected
  [integration]). No section fails. Added Phase 13 (local-run reliability + CI breadth)
  from a live `sakthai run` session against Ollama: localhost→IPv6 connect-refused fix,
  text-emitted tool-call warning, and widening the CI Python matrix.
- 2026-06-17 — Phase 12.4 done: re-derived 5 kept skills into curated library/ grouping (codebase-knowledge, github-workflows, debugging, tdd, red-teaming). 48 skills validated.
- 2026-06-17 — Phase 12 MERGED to main: PR #32 (governance docs + audit + 3 re-derived
  library skills) merged; its CI flagged pre-existing ruff errors in sakthai/skills.py + tests
  (not from this work — library/ is ruff-excluded), fixed by follow-up PR #33. main now green
  on all gates (ruff/format/mypy/bandit, 43 skills validated, 655 passed / 1 skipped).
- 2026-06-17 — Phase 12.1–12.5 processed: re-derived SAKTHAI.md, CODE_OF_CONDUCT.md (MIT),
  CHANGELOG.md; verified CONTRIBUTING/SECURITY already v2-accurate; declined WORKSPACE.md,
  DASHBOARD_IMPROVEMENTS.md, devtools_ai_capabilities.md, hf_dataset_readme.md. Full skills/
  library/code-module triage with keep/drop rationale in docs/og_parity_audit.md. Backfill:
  found v2 library/ already held most keepers; re-derived the 3 genuine gaps
  (memory-store, agent-reasoning, learning-curation). Done on branch phase12-og-parity.
- 2026-06-17 — Phase 12.1 done: re-derived identity and governance documentation (SAKTHAI.md, CODE_OF_CONDUCT.md, docs/workspace.md, CHANGELOG.md, docs/dashboard_improvements.md).
- 2026-06-17 — Phase 12.6 done: implemented unified extension paths, namespaced command routing, and native caveman runtime toggle.
- 2026-06-17 — Phase 12.6 done: completed workflows and caveman integration audit and saved to docs/workflows_caveman_integration_audit.md.
- 2026-06-16 — Phase 12 added: OG→v2 information-parity audit (identity/governance
  docs, skills 111→8, library 357→~20, code/feature gaps) recorded for triage.
- 2026-06-16 — Phase 11.4 done: documented Turso/Litestream architectural evaluation in docs/replication.md.
- 2026-06-16 — Phase 11.3 done: added `--http-url` zero-dependency fallback to `sakthai memory sync`.
- 2026-06-16 — Phase 11.2 done: implemented auto-merge strategy utilizing local sqlite DB to resolve git JSONL conflicts seamlessly.
- 2026-06-16 — Phase 11.1 done: updated memory sync to dump incremental `facts.jsonl` and `observations.jsonl`.
- 2026-06-16 — Phase 10.4 done: Migrated Google ADK/Vertex AI skeleton into v2 as cloud runtime stubs.
- 2026-06-16 — Phase 10.3 done: implemented `sakthai memory sync` (Git-backed remote) and added the `sakthai-memory-admin` skill.
- 2026-06-16 — Phase 10.2 done: implemented --fast mode to bypass cycle overhead.
- 2026-06-16 — Phase 10.1 done: clarified v1 deprecation and license in README.
- 2026-06-15 — todo.md created and committed; roadmap approved.
- 2026-06-15 — Phase 0.1 done: robust CLI test assertions (159 tests green).
- 2026-06-15 — Phase 0.2 done: dashboard/app.py smoke test (164 with extra; skips without).
- 2026-06-15 — Phase 0.3 done: store-migration + loop stop/iteration depth tests (172 passed). Phase 0 complete.
- 2026-06-15 — Phase 1.1 done: dynamic ToolRegistry; loop dispatch routed through it (178 passed).
- 2026-06-15 — Phase 1.2 done: StdioMCPClient (spawn/handshake/call external MCP servers) (184 passed).
- 2026-06-15 — Phase 1.3 done: MCP server manifest parsing + config discovery (192 passed).
- 2026-06-15 — Phase 1.4 done: connect_servers wires external MCP tools into an agent run (196 passed).
- 2026-06-15 — Phase 1.6 done: `sakthai run` auto-loads MCP servers from config; --no-mcp opt-out (198 passed).
- 2026-06-15 — Phase 1.5 done: skill injection into the system prompt (--with-skills) (203 passed). **Phase 1 complete.**
- 2026-06-15 — Phase 2 done: OpenAI/Ollama provider, integration guides, run_agent_loop tool (207 passed). **Phase 2 complete.**
- 2026-06-15 — Phase 3 done: hermetic tests, strict mypy, updated docs. **Phase 3 complete.**
- 2026-06-15 — Phase 4 done: WAL mode/locks, recursion guard, token pruning (209 passed). **Phase 4 complete.**
- 2026-06-15 — Phase 5 done: API retry/backoff, token-usage tracking, sessions CLI, robust provider construction, safe backup, `run --dry-run` preflight. **Phase 5 complete.**
- 2026-06-15 — Phase 6 done: providers extracted into sakthai/agent/providers/ (loop 823→369); integration test markers (CI `-m "not integration"`). **Phase 6 complete.**
- 2026-06-15 — Phase 7 done: streaming — on_token interface + `run --stream`, Anthropic messages.stream, OpenAI SSE with tool-call reassembly. **Phase 7 complete.**
- 2026-06-15 — Phase 8 done: dashboard session data layer + Agent Activity tab (timeline, token usage by model, recent sessions). **Phase 8 complete.** Phase 9 deferred to v3.
