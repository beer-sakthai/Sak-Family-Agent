# TODO — ServiceQuoteBot MVP

This file tracks the tasks required to build the "ServiceQuoteBot" MVP, as defined in `product/PLAN.md`.

Keep this file focused on product delivery and the runtime implementation work needed for the bot.

## Product Direction

The project is a **business-first AI team platform** with customer-specific packaging.
Business is the primary target, and personal/family modes remain supported as secondary
variants when a customer needs them. See [`product/decision.md`](decision.md) for the
short decision note.

The initial MVP remains a Telegram-based agent that provides quotes from a business's
price book and captures leads.

## Phase 1: Core Agent & Knowledge Base

- [x] **Define Persona:**
  - Created `personas/servicequotebot/SOUL.md` as the dedicated `ServiceQuoteBot` persona.
  - The persona is focused on customer service, quoting, and lead capture.
  - It explicitly leans on `SakTan` for ops and `SakThai` for logic.

- [x] **Knowledge Ingestion:**
  - Added the `ingest_document` tool to parse Markdown, CSV, and plain-text source files.
  - The tool stores each extracted line as a structured `fact` entry in the active `memory.db`.
  - It uses the existing `learn` path internally so document facts flow through the same memory layer as manual facts.

- [x] **Quoting & Lead Capture:**
  - Added the `service-quoting` skill to guide quote construction from stored pricing facts.
  - Added the `capture_lead` tool to store customer contact details and their query as a `lead` fact.

## Phase 2: Telegram Integration & Deployment

- [x] **Refactor Telegram Bot:**
  - Mature the existing prototype `telegram/` bot into a production-ready component.
  - Align its configuration (`telegram/config.py`) to use the central `sakthai/config.py` and `sakthai/auth.py` modules.
  - Modify the bot to run the main `sakthai run` agent loop with a persistent session, rather than as a stateless subprocess.

- [x] **Deployment Plan:**
  - Document the steps to deploy the ServiceQuoteBot for a customer.
  - This should include creating a systemd service file or a Dockerfile for easy, repeatable deployment.
  - Write a script to automate the setup for a new client (e.g., setting API keys, ingesting their price book).

## Phase 3: Hermes-free runtime migration

## Phase 4: Memory architecture and session search

- [x] 2026-08-25 **Architecture audit:**
  - Documented in `docs/superpowers/specs/2026-07-02-phase4-memory-session-search-design.md`.
  - Confirms `MemoryStore`'s schema is unchanged by this phase; the gap is a missing search
    surface over session logs, which live outside the store entirely.

- [x] 2026-08-25 **`search_sessions()`:**
  - Implemented in `sakthai/memory/session_search.py`.
  - AND-of-terms, case-insensitive query over task/result.text/result.tool_calls.
  - On-demand scan (no persistent index), timestamp-descending order.

- [x] 2026-08-25 **CLI command:**
  - `sakthai sessions search <query> [--limit N]` in `sakthai/cli/sessions.py`.

- [x] 2026-08-25 **Agent tool:**
  - `search_sessions` added to `BUILTIN_TOOLS`; reachable from both `sakthai run` and `sakthai mcp`.

- [x] 2026-08-25 **Test coverage:**
  - `tests/test_session_search.py`, plus extensions to `tests/test_tools.py` and
    `tests/test_sessions_cli.py`.

- [x] 2026-08-25 **Local verification:**
  - `uv run pytest tests/test_session_search.py tests/test_tools.py tests/test_sessions_cli.py -q`
    passing, plus a manual `sakthai sessions search` smoke run.

- [x] 2026-08-25 **GitHub delivery:**
  - Committed, pushed, PR opened, merged after green CI.
