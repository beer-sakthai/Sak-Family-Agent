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

- [ ] 10.1 — Documentation & Clarification: Update README to clarify v1 deprecation and proprietary license terms.
- [ ] 10.2 — Fast-Track Mode: Add `--fast` flag to bypass the rigid 6-stage cycle for simple runs.
- [ ] 10.3 — Remote Memory Sync: Implement `sakthai memory sync` for cloud or git backups to reduce local state dependency.
- [ ] 10.4 — Basic Cloud Runtime Stubs: Migrate Google ADK / Vertex AI skeleton into v2 for future deployment.

---

## Log
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
