# SakThai-Agent v2 — Plan: Live Connect + Robust Agent Runtime
Owner: Beer (via Hermes-SakThai)  
Status: Completed  
Scope: Phases 5–8, aligned with existing todo.md

## Current state (from v2 repo)
- Phases 0–4 complete
- Multiruntime + MCP + skills wired
- Next frontier: Phase 5 robustness, Phase 6 providers, Phase 7 streaming, Phase 8 dashboard
- Live external assets: HF (Nanthasit) Spaces/model/datasets/buckets, Composio 7 tools/20+ app connections

## Goal
Close the loop between the live real-world SakThai stack and the v2 code by making the agent runtime production-grade, observable, and ready for voice-first automation on Telegram.

## Phase 5 — Robustness (existing tasks, exact order)
1. 5.1 API retry with exponential backoff (`tenacity`)
2. 5.2 Token usage tracking (`UsageTracker` in AgentResult + session logs)
3. 5.3 Session management CLI (`sakthai sessions list/show/clean`)
4. 5.4 Robust provider construction (clean `AgentError` for missing creds)
5. 5.5 Safe memory backup preflight
6. 5.6 `sakthai run --dry-run` (provider/model/tool count, no API call)

Acceptance: new tests pass; no regressions in Phase 0–4 tests.

## New: Phase 5½ — Live integration contract
1. Add `docs/integrations.md` capturing one-shot recipes for:
   - Composio MCP server (`composio`) as an outbound MCP source for `sakthai run`
   - HF Spaces exports → agent session logs / dataset ingest
2. Canonicalize Composio config: store server spec in `~/.sakthai/mcp.json`, not just Hermes `~/.hermes/config.yaml`
3. Add script `scripts/regenerate-supermemory-canonicals.py` for pairwise dedup of memory entries
4. Document token-cost guardrails: prefer edge-TTS, local small models, and Composio batch tool use before expensive single calls

## Phase 6 — Architecture cleanup (as written, unchanged)
- Extract providers into `sakthai/agent/providers/{anthropic,gemini,openai}.py`
- Integration pytest markers

## Phase 7 — Streaming output (as written, unchanged)
- `on_token` callback; Anthropic + OpenAI-compat SSE support
- CLI `--stream`

## Phase 8 — Dashboard observability — expanded
- Session timeline + token-usage tab
- Add “Memory / Cost / Connections” section:
  - Supermemory hit rate vs local fallback
  - Composio last-used timestamp + active connection count (from saved profile)
  - HF data freshness: models/datasets updated within last 24h

## Phase 5–8 definition of done
- Green CI on Python 3.11 and 3.12
- `todo.md` updated with completion dates
- This plan archived in `docs/` and linked from README

## Execution rules
1. Work one task at a time; run full `pytest tests/ -q` after each logical slice
2. Commit after green suite with message: `feat: SakThai v2 — Phase X.Y <short>`
3. Post Phase 5.2+, log token estimates to Session JSON if the provider exposes them
