# TODO — ServiceQuoteBot MVP

This file tracks the tasks required to build the "ServiceQuoteBot" MVP, as defined in `product/PLAN.md`.

## Product Direction

The project is a **business-first AI team platform** with customer-specific packaging.
Business is the primary target, and personal/family modes remain supported as secondary
variants when a customer needs them. See [`product/decision.md`](decision.md) for the
short decision note.

The initial MVP remains a Telegram-based agent that provides quotes from a business's
price book and captures leads.

## Phase 1: Core Agent & Knowledge Base

- [ ] **Define Persona:**
  - Create a new, dedicated persona `ServiceQuoteBot` by running `make new-persona`.
  - Write its `SOUL.md` to be focused on customer service, quoting, and lead capture. It will leverage the skills of `SakTan` (ops) and `SakThai` (logic).

- [ ] **Knowledge Ingestion:**
  - Develop a new tool `ingest_document` for the agent.
  - This tool should parse common document formats (e.g., Markdown, CSV, plain text) containing a price list or FAQs.
  - It will use the `learn` tool internally to save the parsed information as structured `fact` entries in the `memory.db`.

- [ ] **Quoting & Lead Capture:**
  - Create a new skill `service-quoting` that guides the agent on how to construct a quote by recalling pricing facts.
  - Create a new tool `capture_lead` that saves customer contact details (name, phone/email) and their query into a `lead` kind in the memory store.

## Phase 2: Telegram Integration & Deployment

- [ ] **Refactor Telegram Bot:**
  - Mature the existing prototype `telegram/` bot into a production-ready component.
  - Align its configuration (`telegram/config.py`) to use the central `sakthai/config.py` and `sakthai/auth.py` modules.
  - Modify the bot to run the main `sakthai run` agent loop with a persistent session, rather than as a stateless subprocess.

- [ ] **Deployment Plan:**
  - Document the steps to deploy the ServiceQuoteBot for a customer.
  - This should include creating a systemd service file or a Dockerfile for easy, repeatable deployment.
  - Write a script to automate the setup for a new client (e.g., setting API keys, ingesting their price book).
