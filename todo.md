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

- [ ] 6.1 — Extract providers: new `sakthai/agent/providers/` package with
      `__init__.py` (Provider protocol), `anthropic.py`, `gemini.py`, `openai.py`.
      Each module owns its _call_*, _to_*_messages, and retry decorator.
      loop.py becomes pure orchestration.
      (sakthai/agent/providers/*, sakthai/agent/loop.py, tests/test_agent_loop.py)
- [ ] 6.2 — Integration test markers: add `@pytest.mark.integration` for tests
      that can optionally hit real Ollama/Anthropic endpoints. CI runs with
      `-m "not integration"`.
      (pyproject.toml, .github/workflows/ci.yml, tests/test_integration.py)

## Phase 7 — Streaming output ← CON #2, #3
Goal: progressive token display instead of waiting for full response.

- [ ] 7.1 — Streaming callback interface: add `on_token: Callable | None` param
      to run_agent + provider call(). CLI `--stream` flag wires it to stdout.
      (sakthai/agent/loop.py, sakthai/cli/agent.py)
- [ ] 7.2 — Anthropic streaming: when on_token provided, use
      client.messages.stream() and yield deltas.
      (sakthai/agent/providers/anthropic.py, tests/test_streaming.py)
- [ ] 7.3 — OpenAI-compat streaming: set `"stream": True`, parse SSE chunks,
      yield deltas, accumulate tool_calls.
      (sakthai/agent/providers/openai.py, tests/test_streaming.py)

## Phase 8 — Dashboard & observability ← CON #9
Goal: session history + token charts in the Streamlit dashboard.

- [ ] 8.1 — Session data layer: `collect_session_data()` reads session JSONs,
      parses task/model/tokens/timestamp, aggregates by day and model.
      (sakthai/dashboard/data.py, tests/test_dashboard_sessions.py)
- [ ] 8.2 — Dashboard UI: "Agent Activity" tab (session timeline), "Token Usage"
      tab (cumulative chart by model), "Recent Sessions" section.
      (sakthai/dashboard/app.py)

## Phase 9 — Future (deferred to v3)
- [ ] Google ADK / Vertex AI cloud agent port ← CON #5
- [ ] Multi-user / multi-tenant database isolation ← CON #7

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
