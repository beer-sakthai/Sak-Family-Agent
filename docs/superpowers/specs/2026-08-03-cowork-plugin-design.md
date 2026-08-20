# Copilot Cowork Plugin — Memory & Teams Connectors — Design

**Status:** Draft (awaiting user review)
**Date:** 2026-08-03
**Owner:** Claude Code (with Beer input on approach and hosting)

---

## Context

This started as an attempt to fix `copilot_retrieval_query` in
`services/teams-copilot-mcp` before shipping it. Research established the
Graph Copilot Retrieval API explicitly does not support personal Microsoft
accounts under any auth mode (delegated or application) — Beer's Microsoft
365 is a personal Premium subscription, not a work/school Entra ID tenant,
so that endpoint is a structural dead end. A follow-up idea — browser
automation of the Copilot web chat UI via Playwright or a computer-use
agent — was also ruled out: Microsoft's Copilot Terms of Use explicitly and
unambiguously prohibits "bots or scrapers," reinforced by the Services
Agreement's anti-scraping clauses, with Cloudflare bot protection and prior
enforcement precedent (`EdgeGPT`) as evidence this isn't just theoretical.

A second follow-up — whether Beer's "Office Agent Frontier" access changes
anything — confirmed Frontier is real and free on Microsoft 365 Premium
(Word/Excel/PowerPoint Agents, Agent Mode reaching GA 2026-04-22), but none
of it exposes a programmatic API; it's chat/UI-only.

What Frontier *does* unlock is **Copilot Cowork**, which has a genuine,
Microsoft-documented developer extensibility surface: plugins packaged as
Agent Skills + remote MCP connectors, distributed as a standard M365 app
package, installable for personal use via the Microsoft 365 Agents Toolkit
CLI (`atk install --scope Personal`) — no Partner Center / public app store
submission required. This is the reverse integration direction from
everything tried before: instead of Sak-Family-Agent pulling data out of
Copilot (blocked), Cowork calls *into* an MCP server we build.

This document designs that server (well, three of them).

---

## Decisions (from brainstorming)

| # | Question | Answer |
|---|----------|--------|
| 1 | What should Cowork be able to reach? | SakThai's memory store AND the Teams/Graph tools already in `teams-copilot-mcp` |
| 2 | Hosting | Dev tunnel from Beer's own machine, always-on (not a cloud deploy) |
| 3 | Auth | Full `OAuthPluginVault` — a self-hosted OAuth 2.0 authorization-code-flow server (not GitHub OAuth, not a secret-in-URL) |
| 4 | Architecture | New isolated bridge services, not surgery on sakthai's CI-gated core package |
| 5 | Embedding model for memory search | `google/embeddinggemma-300m` via HF Inference Providers, not Beer's own `sakthai-embedding-multilingual` (not live on any Inference Provider, no formal benchmark yet) |
| 6 | Beer's own embedding model | Out of scope here — Beer will separately plan improving it; the connector calls a configured model ID, so swapping it in later is a config change, not new engineering |

---

## Goal

1. Copilot Cowork (Beer's personal M365 Premium + Frontier) can call into
   SakThai's memory (read/write facts) and the Teams/Graph tools already
   built, through two MCP connectors in one Cowork plugin package.
2. Access is protected by real OAuth 2.0 (authorization-code flow, PKCE),
   not an open endpoint or an easily-leaked static secret.
3. The memory connector's `search` tool does semantic ranking via a
   confirmed-working embedding model, with a safe fallback if that model
   is unreachable.
4. None of this touches sakthai's core package (`personas/sakthai/sakthai/`)
   — that codebase's CI gate (96% coverage, strict mypy/bandit) stays
   exactly as-is; the new services *import* `MemoryStore` but don't modify
   its module.
5. `teams-copilot-mcp`'s existing stdio mode (used by `sakthai run`/Hermes,
   already verified working) is untouched — the HTTP mode is strictly
   additive.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Copilot Cowork (Microsoft cloud)                                  │
└───────────────┬───────────────────────────┬───────────────────────┘
                 │ OAuth redirect              │ Bearer JWT per call
                 ▼                             ▼
┌────────────────────────┐   ┌──────────────────────┐  ┌──────────────────────┐
│ services/cowork-oauth/  │   │ services/             │  │ services/            │
│ (NEW)                   │   │ teams-copilot-mcp/    │  │ cowork-memory-mcp/    │
│                          │   │ (EXTENDED)            │  │ (NEW)                 │
│ authlib-based OAuth 2.0  │   │ existing FastMCP      │  │ FastMCP: learn/       │
│ auth-code flow, single   │◄──┤ tools, + new HTTP     │  │ recall/search (now    │
│ hardcoded user, PKCE,    │  verify│ run mode           │  │ semantic) + local     │
│ refresh tokens           │  (shared│                    │  │ embedding cache       │
│ /authorize /token        │  module)│                    │  │                       │
│ /refresh /.well-known    │   └──────────────────────┘  └──────────────────────┘
└────────────────────────┘              ▲                          ▲
        ▲                               │ imports                  │ imports
        │                     ┌──────────────────────┐    (MemoryStore from
        │                     │ services/             │     sakthai package,
   devtunnel :A                │ cowork-auth-shared/   │     unmodified)
   devtunnel :B  (one tunnel   │ (NEW, tiny)            │
   devtunnel :C   session,     │ JWT verification only  │
                  three ports) │ — issuance stays in    │
                                │ cowork-oauth only      │
                                └──────────────────────┘
```

Three services instead of one because they're genuinely different
concerns: `cowork-oauth` is protocol infrastructure both connectors need
identically; `teams-copilot-mcp` already exists and just grows an HTTP run
mode; `cowork-memory-mcp` is new but deliberately thin, importing the real
`MemoryStore` class rather than reimplementing storage. `cowork-auth-shared`
exists only because JWT *verification* is security-sensitive code needed
identically by both resource servers — duplicating it risks drift; keeping
*issuance* solely in `cowork-oauth` keeps the attack surface for "can mint
a valid token" in exactly one place.

---

## Components

### `services/cowork-oauth/` (NEW)

- `authlib`-based OAuth 2.0 authorization-code-flow server, PKCE-capable.
- Single hardcoded user: an env-configured username + bcrypt-hashed
  password checked at `/authorize`'s login form. No user database — this
  is intentionally not multi-user.
- Endpoints:
  - `GET /authorize` — renders a minimal login+consent page; on successful
    login, issues a short-lived authorization code and redirects to
    `https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect?code=...`
    (this exact redirect URI must be registered with the OAuth client —
    it's fixed by Microsoft, not customizable per app).
  - `POST /token` — exchanges an authorization code (with PKCE verifier)
    or a refresh token for a new access token. Access tokens are JWTs
    (RS256), signed with a keypair generated once at first startup and
    persisted to the service's own state dir (never regenerated silently
    — see Error handling). Claims: `sub` (fixed user id), `aud` (which
    connector this token is valid for — `memory` or `teams`), `exp`
    (short-lived, ~1hr).
  - `GET /.well-known/oauth-authorization-server` — RFC 8414 discovery
    document, so Microsoft 365 Agents Toolkit can auto-fetch the
    authorization/token/refresh endpoint URLs during `atk` setup instead
    of Beer typing them in manually.
- Refresh tokens are opaque, stored server-side (SQLite: hash, issued_at,
  expires_at, revoked flag) so they're revocable — signing out of the
  agent in Copilot clears the stored token, but this server should also
  support explicit revocation.

### `services/teams-copilot-mcp/` (EXTENDED)

- New HTTP entrypoint (FastMCP's native HTTP transport) alongside the
  existing stdio one. The stdio path (`mcp.run()` default, used by
  `sakthai run`/Hermes) is not modified.
- Every HTTP tool call passes through `cowork-auth-shared`'s JWT
  verification (signature via `cowork-oauth`'s public key, `exp` check,
  `aud == "teams"`) before dispatching to any tool. Missing/invalid token
  → 401, surfaced to Cowork as a clean MCP tool error.
- Bound to `::` (not `0.0.0.0`) — a dev-tunnel gotcha found during
  research: tunnels dial `localhost`, which resolves to `::1` first on
  some platforms, and an IPv4-only bind produces silent 502s through the
  tunnel.
- Tool set exposed over HTTP is the same one already shipped over stdio:
  `list_channels`, `send_channel_message`, `list_calendar_events`,
  `get_meeting_transcript`, `search_actions`/`execute_action`/
  `execute_raw`. `copilot_retrieval_query` stays exactly as it is today
  (raises `NotImplementedError` — this design doesn't touch that).

### `services/cowork-memory-mcp/` (NEW)

- Depends on the `sakthai-agent` package to import `MemoryStore` directly
  (editable/path dependency) — reuses the real class, doesn't reimplement
  storage or duplicate its logic.
- Three tools only, deliberately narrow — no `forget`, no shell access, no
  recursive agent loop:
  - `learn(kind, key, value, tags?)` → `MemoryStore.add_fact(...)`, then
    immediately embeds the new fact's text via HF Inference Providers and
    caches the vector (see below). If the embedding call fails, the fact
    write still succeeds — embedding is best-effort and self-heals on the
    next search's backfill.
  - `recall(limit?)` → `MemoryStore.list_facts(...)`, unchanged, no
    ranking needed.
  - `search(query, limit?)` → semantic search: embed the query, compare
    against cached embeddings, return top-N ranked facts/observations.
    Falls back to `MemoryStore.search_memory()` (existing substring match)
    if the embedding call fails, and flags the response as degraded so
    the caller knows quality dropped rather than silently returning worse
    results.
- **Local embedding cache** — its own SQLite file
  (`~/.cowork-memory-mcp/embeddings.db`), separate from sakthai's
  `memory.db`, so nothing here touches sakthai's schema:
  ```sql
  CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY,
    source_table TEXT NOT NULL,   -- 'facts' | 'observations'
    source_id INTEGER NOT NULL,
    content_hash TEXT NOT NULL,   -- detects stale cache if a fact's value changes
    embedding BLOB NOT NULL,
    created_at REAL NOT NULL,
    UNIQUE(source_table, source_id)
  );
  ```
- Embedding calls: HF Inference Providers, model `google/embeddinggemma-300m`
  (confirmed live via `inferenceProviderMapping`, #1 on the ArguAna
  retrieval leaderboard at nDCG@10=71.5, Gemma license). Reuses the
  `HF_TOKEN`/`SAKTHAI_HF_API_BASE` env convention already established in
  sakthai's config, so no new credential plumbing.
- Same bearer-JWT gate as `teams-copilot-mcp` (`aud == "memory"`), via the
  shared verification module.

### `services/cowork-auth-shared/` (NEW, tiny)

- One module: given a bearer token string and an expected `aud` value,
  verify signature (against `cowork-oauth`'s public key, fetched once at
  startup or embedded via shared config) and expiry; return the decoded
  claims or raise a typed auth error the calling service turns into a 401.
- Contains no token *issuance* logic — that stays solely in `cowork-oauth`,
  so there is exactly one place capable of minting a valid token.
- Naming note: the JWT `aud` claim uses short-form values (`"memory"`,
  `"teams"`) while the manifest's `agentConnectors[].id` uses full-form
  (`"cowork-memory"`, `"cowork-teams"`). These are deliberately two
  separate identifier namespaces — JWT claims vs. app-manifest IDs — and
  never need to match syntactically; this is not a typo.

### M365 packaging

One `.zip` package, manifest v1.28, `agentConnectors` array with two
entries (`cowork-memory`, `cowork-teams`), each `authorization.type:
OAuthPluginVault` referencing the auth config Beer creates via `atk`
(which auto-discovers `cowork-oauth`'s `.well-known` endpoint). No custom
`agentSkills` in this package for v1 — connector-only (see Out of scope).

---

## Data flow

**First-time OAuth consent:**
```
Cowork → cowork-oauth GET /authorize (rendered login form)
Beer enters password → cowork-oauth verifies → issues auth code
  → redirect to https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect?code=...
Teams exchanges code → POST /token → cowork-oauth issues
  {access_token (JWT, aud=memory|teams, ~1hr), refresh_token}
  → stored in Microsoft's Enterprise Token Store
```

**A memory search call, later:**
```
Cowork → POST https://<tunnel-C>/mcp
  {"method":"tools/call","params":{"name":"search","arguments":{"query":"..."}}}
  Header: Authorization: Bearer <JWT>

cowork-memory-mcp:
  cowork_auth_shared.verify(token, aud="memory") → claims or 401
  embed(query) via HF Inference Providers
  load cached vectors from embeddings.db; embed+cache any facts/observations
    that don't have one yet
  cosine-rank all cached vectors against the query embedding
  return top-N facts/observations
```

---

## Error handling

| Failure | Behavior |
|---------|----------|
| JWT missing / invalid signature / expired / wrong `aud` | 401; clean MCP tool-error message, no stack trace to the caller |
| HF embedding call fails during `search` | Fall back to `MemoryStore.search_memory()` (substring); response includes a flag noting degraded/non-semantic results |
| HF embedding call fails during `learn` | Fact write still succeeds (independent write path); embedding is simply missing from the cache until the next `search` backfills it |
| Refresh token expired or revoked | Cowork/Teams re-triggers the `/authorize` flow automatically — standard OAuth behavior, no special handling needed here |
| Dev tunnel down or host machine asleep | The call times out on Cowork's side. Inherent to the "dev tunnel from my machine" hosting decision — not something this design can paper over |
| `cowork-oauth`'s signing keypair missing or unreadable at startup | Refuse to start, loud error. Never silently generate a replacement key — that would invalidate every outstanding access token without any signal to the holder |
| `embeddings.db` locked/corrupted | `search` falls back to substring match (same path as an HF failure) rather than hard-failing the tool call |

---

## Testing strategy

1. **`cowork-oauth`**: auth-code issuance and single-use enforcement, PKCE
   verification, `/token` exchange (code and refresh grant types),
   rejection of expired/replayed codes, JWT claim shape (`sub`, `aud`,
   `exp`) and signature.
2. **`cowork-memory-mcp`**: unit tests against a fake HF embeddings
   endpoint (no real network calls in CI) — cosine-ranking correctness,
   lazy-backfill behavior, fallback-to-substring path when the fake
   endpoint errors. Reuses the `MemoryStore(":memory:")` pattern already
   established in sakthai's own test suite for the underlying store.
3. **`teams-copilot-mcp` HTTP mode**: extends the real-subprocess,
   real-MCP-client verification pattern already used for the stdio server
   (`mcp.client.stdio` → equivalent HTTP client) — confirm 401 with no
   token, confirm success with a valid test-signed JWT, confirm the
   existing stdio path is unaffected by the new code paths.
4. **`cowork-auth-shared`**: unit tests for valid/expired/wrong-audience/
   malformed tokens — this is the one piece both resource servers trust,
   so it gets tested in isolation before either service's own tests lean
   on it.
5. **Manual, end-to-end**: package the `.zip`, `atk install --file-path
   ... --scope Personal`, ask Cowork a real memory question in a fresh
   conversation, confirm the one-time OAuth consent screen fires, confirm
   the tool call succeeds and returns sensible results, confirm a Teams
   tool call also works through the second connector.

---

## Out of scope (deferred)

- **Public Partner Center distribution.** Personal sideload only
  (`atk install --scope Personal`), matching the actual audience (just
  Beer).
- **Cloud/production hosting.** Dev tunnel from Beer's own machine is the
  explicit decision (#2 above); a real always-on deploy is a separate
  future decision if the machine-must-stay-on trade-off becomes annoying.
- **Custom Agent Skills (`SKILL.md` workflow files).** This package is
  connector-only for v1 — no prompt-based skill workflows designed here.
- **Improving `sakthai-embedding-multilingual`.** Beer's own stated
  follow-up, explicitly not part of this design. The connector calls a
  configured model ID, so this is a swap-in later, not a blocker now.
- **`forget` in the memory connector.** Only `learn`/`recall`/`search` are
  exposed — no delete capability reachable from Cowork, by design.
- **New Graph/Teams tools.** This design HTTP-exposes what
  `teams-copilot-mcp` already has; it doesn't add new Graph operations.
- **Multi-user support.** Single hardcoded user is intentional, not a v1
  shortcut to fix later.

---

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Dev tunnel down / machine off → Cowork calls fail | Medium | Accepted trade-off (decision #2); revisit hosting if this becomes frequent |
| Self-hosted OAuth server is genuinely security-critical code (signing key handling, code/token exchange correctness) | Medium impact if wrong | Needs real code review before use, not just "it's small so it's fine" — this is the one piece of this design where a bug has outsized consequence |
| `google/embeddinggemma-300m`'s Gemma license has usage terms beyond plain MIT/Apache | Low, confirmed | Read the terms directly: personal use via a hosted API, with no redistribution of the model/derivatives, is compatible with the base license (§3.2/3.3, [ai.google.dev/gemma/terms](https://ai.google.dev/gemma/terms)) — the only remaining item is a quick skim of the linked Gemma Prohibited Use Policy, which is standard AUP-style content (harmful-use restrictions) not expected to affect a personal memory-search tool |
| HF Inference Providers rate limits or latency on `search` | Low | Personal-scale call volume; fallback path already covers outages, not just to avoid failure but also implicitly covers slowness if paired with a timeout |
| M365 manifest v1.28's strict `additionalProperties: false` schema causes packaging trial-and-error | Medium | Known from research (a stray field like `packageName` hard-fails the upload) — expect a few iterations, not a one-shot package |

---

## Open questions

1. **~~How does one shared `cowork-oauth` server interact with two separate
   per-connector OAuth client registrations?~~ Largely resolved.** The
   standard Agents Toolkit MCP-plugin walkthrough adds connectors one at a
   time ("Add an Action" → "Start with an MCP Server"), and prompts for
   OAuth client ID/secret/scopes separately *per action added* — "Agents
   Toolkit updates the plugin manifest for you" each time
   ([Build a plugin for a declarative agent from an MCP server](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/build-mcp-plugins),
   Step 1 & Step 2). Nothing in this flow prevents entering the *same*
   client ID/secret/authorization/token/refresh URLs both times — so the
   design's assumption holds: one shared `cowork-oauth` server, two
   separate auth-config records (one per connector) that happen to point
   at identical provider details. Expect to run the OAuth-client-entry
   step twice during setup, once per connector, not once total — a UX
   detail for the plan, not a design blocker.
2. **`atk install --scope Personal` on a personal (non-tenant) account —
   still unresolved, and there's now a specific reason for concern.** The
   same walkthrough's sideload step requires confirming that **"Custom App
   Upload Enabled"** and **"Copilot Access Enabled"** show under the
   Microsoft 365 account in Agents Toolkit's Accounts pane — and if they
   don't, the doc says "check with your organization admin"
   ([same source](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/build-mcp-plugins),
   Step 3). That phrasing assumes an organization exists. A second
   targeted search turned up no documentation stating whether these
   toggles are default-on for a personal MSA account, or whether personal
   accounts can see/set them at all absent an org admin. This needs
   hands-on verification early in implementation — right after `atk auth
   login`, before building anything else — since if personal accounts
   can't clear this gate, the whole "dev tunnel + personal sideload"
   hosting decision (#2 in Decisions) needs revisiting before, not after,
   the OAuth server gets built.

---

## Definition of done

- [ ] `cowork-oauth`, `cowork-auth-shared`, `cowork-memory-mcp` scaffolded
      and passing their own test suites.
- [ ] `teams-copilot-mcp` HTTP mode added; existing stdio tests still pass
      unmodified.
- [ ] M365 manifest package built and validated (passes `atk package`
      without schema errors).
- [ ] Dev tunnel running, all three services reachable over HTTPS.
- [ ] Package sideloaded via `atk install --scope Personal`; manual
      end-to-end walkthrough (both connectors) completed successfully.
- [ ] `services/teams-copilot-mcp/README.md` updated to document the new
      HTTP mode alongside the existing stdio instructions.
- [ ] Open questions above resolved or explicitly re-flagged if still
      unresolved at implementation time.

---

## Approval

- [ ] Beer — architecture and scope
- [ ] Beer — hosting/auth trade-offs (dev tunnel, self-hosted OAuth)
- [ ] Reviewer — code review before use, especially `cowork-oauth`
