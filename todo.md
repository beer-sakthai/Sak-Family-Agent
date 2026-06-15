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
      (--with-skills lands with the skill-injection task below.)

## Phase 2 — Multi-runtime / local model (self-driving, no API key)
- [ ] OpenAI-compatible / Ollama provider (the ~7 touches: config env, auth
      resolver, loop _detect/_build/_call_openai_compat, cli --provider choice)
- [ ] Run-under-another-AI: ship ready-to-paste MCP configs for Claude CLI and
      Gemini CLI; optionally expose the whole agent loop as one MCP tool so an
      external AI can call it
- [ ] docs/plugins.md + docs/runtimes.md (connect any MCP/skill; run on Claude
      CLI / Gemini CLI / Ollama)

## Phase 3 — Hardening
- [ ] Hermetic tests for client (fake subprocess), registry, and the new
      provider (fake httpx) — keep the no-network rule
- [ ] Update CLAUDE.md / GEMINI.md / README / docs/architecture.md

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
- 2026-06-15 — Phase 1.5 done: skill injection into the system prompt (--with-skills) (203 passed). **Phase 1 (plugin foundation) complete.**
