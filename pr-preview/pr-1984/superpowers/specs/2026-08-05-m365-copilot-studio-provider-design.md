# Microsoft 365 Copilot Studio Provider — Design

**Status:** Approved (2026-08-05, verbal approval section-by-section in brainstorming session)
**Date:** 2026-08-05
**Owner:** Claude Code (with Beer's scoping decisions during brainstorming)

---

## Context

`sakthai run`/`chat` already route through five providers in
`agent/providers/` (`anthropic`, `google`/gemini, `openai`-compatible,
`ollama`, `gateway`, `huggingface`), selected via `--provider`/`-p` and
detected/instantiated by `agent/providers/__init__.py`. All share the
`Block`/`Response` types and `tenacity` retry logic defined in
`agent/providers/base.py`.

This is unrelated to the four existing Microsoft Graph *tools*
(`send_outlook_mail`, `read_outlook_mail`, `list_calendar_events`,
`create_calendar_event` in `agent/tools.py`) or the OneDrive/Contacts tools
from the same-day design
(`2026-08-05-onedrive-contacts-graph-tools-design.md`). Those use
**delegated user auth** (a cached refresh token) against the Graph API to
act *as the user* on mail/calendar/files. This design adds a sixth
**provider** — a new way to generate a chat *response*, backed by a
Microsoft 365 Copilot Studio agent — using **app-only client-credentials
auth** (tenant/client ID + secret) against the Bot Framework Connector API.
The two auth models and API surfaces do not overlap.

Microsoft 365 Copilot does not expose a simple chat-completions endpoint.
The only realistic way to call a specific Copilot Studio agent
programmatically today is via the Bot Framework Connector API (the same
protocol underlying the Direct Line channel), authenticated with an Entra
app registration.

## Decisions (from brainstorming)

1. **What "Copilot integration" means here:** a new chat *provider*
   (`--provider copilotstudio`), not a Graph-grounding connector and not a
   change to the existing mail/calendar tools.
2. **Scope:** available to all six personas, same as the other five
   providers — not restricted to SakThai.
3. **Access path:** a Copilot Studio agent, called via the Bot Framework
   Connector API, authenticated through an Entra app registration via Azure
   Bot Service (the auth pattern the M365 Agents SDK also uses), not the
   older Direct Line secret. This is about the *auth mechanism* only — see
   Decision 5 for why the implementation calls the Connector API directly
   instead of depending on the M365 Agents SDK package itself.
4. **Client credential type:** client secret for the initial implementation
   (simpler to provision than a certificate). The design isolates secret
   acquisition behind one function so swapping to certificate-based auth
   later is a small change, not a rewrite.
5. **Dependency choice:** `msal` only (Microsoft's lightweight token
   library). No bot-framework or M365 Agents SDK package — this repo's
   existing providers are all thin `httpx` wrappers, and pulling in a
   heavier, less-mature-in-Python SDK for one provider would be
   inconsistent with that.

## Goal

Give `sakthai run --provider copilotstudio "<task>"` (and `chat`) the same
behavior as every other provider: send the prompt, get back a `Response`,
let `agent/loop.py` and everything downstream (memory injection, tool
dispatch, session logging) work unmodified because they only ever see the
common `Block`/`Response` shape.

## Architecture

New module `agent/providers/copilotstudio_provider.py`, registered in
`agent/providers/__init__.py`'s provider-detection/factory alongside the
existing five. Implements the same call signature the other providers
expose (constructing `Block`s from the prompt/history, returning a
`Response`), reusing `base.py`'s retry decorator.

New config functions in `config.py` (no module hardcodes a path or secret —
this stays the single source of truth):

- `ms365_copilot_tenant_id() -> str`
- `ms365_copilot_client_id() -> str`
- `ms365_copilot_client_secret() -> str`
- `ms365_copilot_bot_id() -> str` — the target Copilot Studio agent's Bot
  Framework App ID (the conversation recipient, distinct from the calling
  app's client ID)

New env vars, documented in `.env.example` and the env-var table in
`CLAUDE.md`:

- `MS365_COPILOT_TENANT_ID`
- `MS365_COPILOT_CLIENT_ID`
- `MS365_COPILOT_CLIENT_SECRET`
- `MS365_COPILOT_BOT_ID`

None of these values — including the Application ID already shared during
brainstorming — are written into this spec or any other committed file;
they belong in the developer's local `.env` only, exactly like
`ANTHROPIC_API_KEY` and the other provider credentials already are.

New dependency: `msal` (added to `pyproject.toml`).

## Data Flow

1. **Token acquisition.** `copilotstudio_provider.py` builds a
   `msal.ConfidentialClientApplication` from
   `ms365_copilot_tenant_id()`/`ms365_copilot_client_id()`/
   `ms365_copilot_client_secret()` and calls
   `acquire_token_for_client(scopes=["https://api.botframework.com/.default"])`.
   `msal` owns its own in-process token cache and silent-refresh — this
   mirrors how `auth.py`'s other credential resolvers already work, so no
   new caching layer is needed.
2. **Start conversation.** `POST /v3/conversations` on the Bot Framework
   Connector API with the bearer token → `conversationId`.
3. **Send the turn.** `POST /v3/conversations/{conversationId}/activities`
   with the prompt as a `type: "message"` Activity addressed to
   `ms365_copilot_bot_id()`.
4. **Get the reply.** Short-poll
   `GET /v3/conversations/{conversationId}/activities?watermark=...`
   (interval ~500ms) until an Activity from the bot with non-empty `text`
   arrives, bounded by a provider-level timeout (default aligned with the
   existing `SAKTHAI_MCP_TIMEOUT` convention, ~30s). Map the reply into the
   same `Response`/`Block` shape every other provider returns.
5. **Statelessness.** Each `sakthai run`/`chat` call opens a **fresh**
   Copilot Studio conversation — no cross-call conversation state is kept
   provider-side. This matches how the other five providers behave today;
   continuity across calls already comes from
   `store.render_prompt_block()` injecting memory into the prompt, not from
   provider-side chat history. There is no explicit conversation-teardown
   call in the Connector API; conversations expire server-side on their
   own.

## Error Handling

- **Auth failure** (bad tenant/client ID/secret, expired secret): raises a
  new `CopilotStudioAuthError` (same family as `AuthError` in `auth.py`),
  naming the specific env var that's likely wrong.
- **Connector API 4xx/5xx** on conversation-start or activity-send: retried
  through the same `tenacity` policy `base.py` already provides to every
  provider, then re-raised as that shared provider-error type on final
  failure — no new error taxonomy for transient failures.
- **Poll timeout** (bot never replies within the window): raises
  `CopilotStudioTimeoutError`, including the `conversationId` so the
  interaction is traceable in Copilot Studio's own transcript/analytics
  view.
- No special handling is needed for conversation cleanup (see
  Statelessness above).

## Testing

- New `tests/test_providers_copilotstudio.py`, following the same pattern
  as the three existing `test_providers_*.py` files.
- Mocks `msal.ConfidentialClientApplication` and the `httpx` client at the
  boundary — this repo's tests are hermetic (no network, no real
  credentials), and this provider is no exception.
- Cases to cover:
  - Auth failure → `CopilotStudioAuthError`.
  - Connector API error → retried per the shared `tenacity` policy, then
    raised.
  - Poll timeout with no bot reply → `CopilotStudioTimeoutError`.
  - Happy path → a mocked bot reply Activity maps to the correct
    `Response`/`Block`.
- **Out of scope for automated tests:** an end-to-end call against the real
  Copilot Studio agent and tenant. That can only be verified manually with
  live credentials, and is the acceptance step before merging — noted here
  so it isn't mistaken for a gap in coverage.

## Non-Goals

- No Graph-grounding/retrieval connector (Copilot searching *this repo's*
  data) — that's a different, opposite-direction integration, explicitly
  out of scope per the brainstorming answer.
- No changes to the existing delegated-auth Graph tools
  (`send_outlook_mail` etc.) or the OneDrive/Contacts tools from the
  same-day design — different auth model, different file, no shared code
  path with this provider.
- No certificate-based auth in the initial implementation (see Decision 4)
  — the token-acquisition function is written so this is a follow-up, not
  a redesign.
- No webhook/callback-based reply delivery (Option 3 considered during
  brainstorming) — `web/server.py` refuses non-loopback binds by default,
  and polling is a non-issue since the agent loop already blocks
  synchronously on every other provider's response too.
