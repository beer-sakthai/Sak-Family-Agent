# TODO — ServiceQuoteBot MVP

This file tracks the tasks required to build the "ServiceQuoteBot" MVP, as defined in `product/PLAN.md`.

The Hermes runtime roadmap now lives in the root [`PLAN.md`](../PLAN.md). Keep this file focused on product delivery and the Hermes-free migration path.

## Product Direction

The project is a **business-first AI team platform** with customer-specific packaging.
Business is the primary target, and personal/family modes remain supported as secondary
variants when a customer needs them. See [`product/decision.md`](decision.md) for the
short decision note.

The initial MVP remains a Telegram-based agent that provides quotes from a business's
price book and captures leads.

## Migration Guideline

For Hermes-free migration work, keep the order fixed:
1. inventory the Hermes dependency surface,
2. define the smallest safe replacement path,
3. implement one runtime seam at a time,
4. add tests before expanding the surface,
5. verify with a local smoke run,
6. commit, open a PR, wait for CI, and merge only after green checks.

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

- [x] **Dependency inventory:**
  - Inventory captured in `docs/agent-diagnosis.md`.
  - Lists Hermes-specific profiles, launchers, services, and environment conventions.
  - Marks which pieces are runtime-critical, which are documentation-only, and which are removal candidates after the non-Hermes path is proven.

- [x] **Replacement path:**
  - Defined in `docs/agent-diagnosis.md` as the smallest non-Hermes bootstrap.
  - Uses the existing `sakthai run` CLI with `--dry-run --no-mcp` for validation.
  - Uses `sakthai run --no-mcp --fast --stateless` as the local smoke route.
  - Avoids `~/.hermes/` for bootstrap and relies on `~/.sakthai/mcp.json` for external tools.

- [x] **Runtime seams:**
  - The Telegram workflow executor now uses the package-configured skills directory and the active Python interpreter, instead of assuming the cwd or hardcoding `python`.
  - This keeps the workflow-launch seam portable across local shells, services, and standalone repos.

- [x] **Test coverage:**
  - Added focused tests for the workflow-executor seam.
  - Covers skills-directory discovery, command construction, and subprocess invocation using the current interpreter.

- [x] **Local verification:**
  - Smoke run passed with `uv run sakthai run "smoke check" --dry-run --no-mcp`.
  - Targeted tests passed with `uv run pytest tests/test_telegram_workflow_executor.py tests/test_cli.py -q`.

- [x] **GitHub delivery:**
  - This checklist update was committed and merged to GitHub after verification.
