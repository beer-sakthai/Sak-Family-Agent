# sakthai-agent-v2 — roadmap

Living task list. Work top-to-bottom; check off with a dated one-line note when done.

## Phase 0 — Quality cleanup (from review cons)
- [ ] Make brittle CLI test assertions robust (assert on stable tokens / exit
      codes, not fragile full-string output)
- [ ] Add a smoke test for dashboard/app.py (import + render the data path with
      a fake store) or document why it stays excluded
- [ ] Depth pass: targeted correctness tests for memory/store.py migrations and
      the agent loop's stop/iteration logic

## Phase 1 — Runtime plugin foundation (use ANY MCP / skill, no manual wiring)
- [ ] Dynamic tool registry: merge builtin + runtime tools; make tool lookup
      registry-driven (agent/tools.py, new agent/registry.py)
- [ ] MCP client (sakthai/mcp/client.py): spawn an external MCP server over
      stdio, initialize, tools/list, tools/call; reuse the JSON-RPC shapes from
      mcp/server.py; graceful failure (log + continue)
- [ ] Parse mcpServers manifests ({command,args,env}) from gemini-extension.json
      / .mcp.json (extend extensions/install discovery beyond names)
- [ ] Wire MCP-client tools into run_agent: load configured servers, convert
      their schemas to Tool objects, merge into the loop, route calls back
- [ ] Skill injection: render selected SKILL.md bodies into the system prompt
      (loop._build_system + skills.render_skills_prompt_block); collect from
      ~/.sakthai/extensions too
- [ ] CLI + config: `sakthai run --with-extensions --with-skills`; auto-load all
      configured servers from ~/.sakthai/mcp.json so it works with zero flags

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
