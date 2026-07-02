# TODO - Hermes and DSPy deployment roadmap

This file tracks the tasks required to turn `Sak-Family-Agent` into a Hermes-backed, Telegram-operated, self-improving agent stack with persistent memory, skill curation, MCP tool access, and a DSPy learning loop.

Follow `product/PLAN.md` for the strategic context. Keep this file as the living execution checklist.

---

## Phase 1: Baseline Decisions

- [ ] Confirm the target runtime: local VPS, serverless, or mixed deployment.
- [ ] Confirm the primary control plane: Telegram gateway, terminal-only, or both.
- [ ] Confirm the model routing strategy: single provider, fallback pool, or cost-tiered routing.
- [ ] Confirm the memory stack:
  - [ ] `docs/MEMORY.md` for bounded runtime facts.
  - [ ] `docs/USER.md` for bounded operator profile.
  - [ ] SQLite/FTS5 session history for exact recall.
  - [ ] External memory backend such as Honcho if enabled.
- [ ] Confirm whether DSPy self-improvement is in scope for v1 or deferred to v2.

## Phase 2: Host and Runtime Hardening

- [ ] Provision a Linux host with enough RAM for the chosen workload.
- [ ] Install the runtime prerequisites:
  - [ ] Python 3.11 or 3.12.
  - [ ] Node.js for MCP servers that rely on `npx`.
  - [ ] `uv` for Python environment management.
  - [ ] Any browser/runtime dependencies required by web tools.
- [ ] Lock down the host:
  - [ ] SSH key auth only.
  - [ ] Firewall with inbound ports closed unless explicitly needed.
  - [ ] System services configured for restart and persistence.
- [ ] Bootstrap the Hermes workspace under `~/.hermes/`.

## Phase 3: Core Hermes Configuration

- [ ] Define the global persona in `docs/SOUL.md`.
- [ ] Create or update `~/.hermes/config.yaml`.
- [ ] Establish provider routing and fallback order.
- [ ] Configure immutable system prompt layers:
  - [ ] Stable identity layer.
  - [ ] Tool-use guidance layer.
  - [ ] Memory injection layer.
  - [ ] Context override layer.
  - [ ] Platform hint layer.
- [ ] Ensure volatile runtime data stays out of the cached system prefix.

## Phase 4: Memory Architecture

- [ ] Create bounded local memory files:
  - [ ] `docs/MEMORY.md`
  - [ ] `docs/USER.md`
- [ ] Define update rules for each file:
  - [ ] What is allowed to persist.
  - [ ] What must never be stored.
  - [ ] Character or size limits.
- [ ] Wire session transcript storage to SQLite with FTS5.
- [ ] Implement session search modes:
  - [ ] discovery
  - [ ] scroll
  - [ ] browse
- [ ] Decide whether to enable a cloud memory provider.
- [ ] Define sync rules between local memory and any remote backend.

## Phase 5: Skills System

- [ ] Audit the current skills directory under `skills/`.
- [ ] Confirm each skill follows the `SKILL.md` schema.
- [ ] Keep the skills index lightweight and load full skills lazily.
- [ ] Add or update skills for:
  - [ ] repository navigation
  - [ ] debugging
  - [ ] deployment
  - [ ] Telegram operations
  - [ ] MCP tool usage
  - [ ] DSPy workflows
- [ ] Define the skill curator policy:
  - [ ] stale skill detection
  - [ ] duplicate skill merging
  - [ ] archive rules

## Phase 6: Context Management and Compression

- [ ] Implement a prompt assembly pipeline that separates stable and volatile layers.
- [ ] Add token-threshold checks before every model call.
- [ ] Add transcript compression for old tool outputs.
- [ ] Protect tool-call/tool-result pairing across compression boundaries.
- [ ] Summarize compressed middle turns into a rolling state block.
- [ ] Preserve provider-side prefix cache stability.

## Phase 7: Tooling and MCP

- [ ] Build a tool registry that exposes only valid, available tools.
- [ ] Add capability checks for each local or remote tool.
- [ ] Integrate MCP servers with least-privilege filters.
- [ ] Support both stdio and HTTP MCP transports.
- [ ] Define explicit allowlists and blocklists for remote tools.
- [ ] Add command safety checks before shell execution.
- [ ] Route dangerous commands through explicit approval flow.

## Phase 8: Telegram Gateway

- [ ] Bind the agent runtime to the Telegram bot API.
- [ ] Support async inbound messages and outbound replies.
- [ ] Define per-chat session mapping and state lookup.
- [ ] Store credentials in `.env` files outside git.
- [ ] Decide whether the gateway uses webhooks or long polling.
- [ ] Add service management and log rotation for the gateway process.

## Phase 9: DSPy and Self-Improvement Loop

- [ ] Record full execution traces for successful and failed runs.
- [ ] Export trajectories in a structured format suitable for training.
- [ ] Identify the first DSPy program or pipeline to optimize.
- [ ] Add evaluation gates before any prompt or skill mutation is accepted.
- [ ] Define how candidate changes become pull requests or review artifacts.
- [ ] Keep the optimization loop isolated from the production runtime.

## Phase 10: Testing and Verification

- [ ] Verify the agent boots with the intended persona and prompt layers.
- [ ] Verify memory files load correctly and stay within bounds.
- [ ] Verify skills are discoverable and lazily loaded.
- [ ] Verify MCP tools connect and fail safely when unavailable.
- [ ] Verify Telegram round-trip messaging works end to end.
- [ ] Verify token compression preserves enough context for follow-up tasks.
- [ ] Verify DSPy traces are captured and replayable.

## Phase 11: Operations and Cost Control

- [ ] Define the monthly cost budget for host, inference, and auxiliary services.
- [ ] Track token usage by provider and by task class.
- [ ] Add a fallback policy for expensive or unavailable models.
- [ ] Document backup and restore steps for secrets and state.
- [ ] Document upgrade steps for Hermes, skills, and MCP servers.
- [ ] Keep deployment notes current in the repo.

---

## Suggested Implementation Order

1. Host hardening and Hermes bootstrap.
2. Core config, persona, and memory.
3. Skills, tools, and context management.
4. Telegram gateway integration.
5. DSPy trace capture and optimization loop.
6. Verification, cost controls, and operations notes.
