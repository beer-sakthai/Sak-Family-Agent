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
