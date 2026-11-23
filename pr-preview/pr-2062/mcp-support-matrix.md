# MCP extension support matrix

What this package implements of the Model Context Protocol, on each surface it
exposes, and — where something is absent — whether that is a gap or a decision.

Re-derive rather than trust: this file is written by hand and every count in it
can go stale. The protocol table lives in
[`personas/sakthai/mcp/protocol.py`](../personas/sakthai/mcp/protocol.py); the
lifecycle states live in
[`personas/sakthai/mcp/lifecycle.py`](../personas/sakthai/mcp/lifecycle.py) and
are published in [`mcp-deprecations.md`](mcp-deprecations.md).

## Protocol revisions

| Revision | Status here | Note |
|---|---|---|
| `2024-11-05` | **Supported** | The oldest revision. Hosts do pin it; negotiation makes keeping it nearly free. |
| `2025-03-26` | **Supported** | |
| `2025-06-18` | **Supported** | Introduces the required `MCP-Protocol-Version` header, which the client now sends. |
| `2025-11-25` | **Supported, preferred** | Previous stable upstream. What `initialize` answers with when given no usable preference. |
| `2026-07-28` | **Not supported, deliberately** | Latest upstream. See below. |

A client asking for a revision in that list gets it back. Anything else —
absent, newer, or not a version string at all — is answered with
`2025-11-25`. The server never echoes a revision it cannot speak, because the
client's only recourse under the spec is to disconnect when it cannot speak the
server's answer, and that only works if the answer is honest.

### Why `2026-07-28` is not on the list

It is not an increment. It removes `initialize` and
`notifications/initialized`, protocol-level sessions and `Mcp-Session-Id`,
`ping`, `logging/setLevel`, `resources/subscribe`, SSE resumability and the
HTTP GET stream; it deprecates roots, sampling and logging outright; and it
replaces the handshake with a stateless per-request model
(`server/discover`, `_meta["io.modelcontextprotocol/protocolVersion"]`,
a required `resultType` on every result). Adopting it is a rewrite of the
transport and the handshake, not a version bump, and it would break every host
currently speaking `2024-11-05` through `2025-11-25` to this server.

Listing it without implementing the stateless handshake would be the precise
failure that negotiation exists to prevent. The migration is tracked in
[`mcp-roadmap.md`](mcp-roadmap.md).

## The four surfaces

| | |
|---|---|
| **In·stdio** | The inbound server, `sakthai mcp`. The main surface. |
| **In·HTTP** | The inbound Streamable HTTP endpoint, `POST /v1/mcp` on the gateway. |
| **Out·stdio** | `StdioMCPClient` — an external server we spawn. |
| **Out·HTTP** | `RemoteMCPClient` — an external server we POST to. |

Legend: **Yes** · **Partial** · **No** (a gap) · **n/a** (does not apply to that
surface) · **host** (the host's job, not a server's).

## Core primitives

| Feature | In·stdio | In·HTTP | Out·stdio | Out·HTTP | Note |
|---|---|---|---|---|---|
| `initialize` / version negotiation | Yes | Yes | Yes | Yes | Inbound negotiates; outbound records what the server answered. |
| `tools/list` | Yes | Yes | Yes | Yes | |
| `tools/call` | Yes | Yes | Yes | Yes | Both inbound paths run guardrails and `Tool.safe_call`. |
| Tool `annotations` | Yes | Yes | Partial | Partial | Emitted for every built-in; an external tool's annotations are read but not re-exposed. |
| `resources/list` · `resources/read` | Yes | Yes | No | No | Inbound serves a registry. The outbound client never asks — see *Gaps*. |
| `prompts/list` · `prompts/get` | Yes | Yes | No | No | One inbound prompt. Same outbound gap. |
| `ping` | Yes | Yes | Yes | Yes | |
| Notifications (inbound) | Yes | Yes | n/a | n/a | Swallowed, as a server must. HTTP answers `202` with no body. |
| List pagination (`cursor` / `nextCursor`) | n/a | n/a | Yes | Yes | The outbound client follows cursors; it previously read only page one. |
| | | | | | Inbound returns every tool in one page, which is spec-valid at 23 tools. |

## Content and metadata

| Feature | In·stdio | In·HTTP | Out·stdio | Out·HTTP | Note |
|---|---|---|---|---|---|
| `text` content | Yes | Yes | Yes | Yes | |
| `image` / `audio` content | No | No | Partial | Partial | Inbound: no handler produces one. Outbound: described, not inlined — a base64 image is tens of thousands of useless tokens. |
| `resource_link`, embedded `resource` | No | No | Partial | Partial | Same: surfaced as a line naming the URI rather than dropped. |
| `structuredContent` | No | No | Yes | Yes | Inbound: every handler returns `str`, so there is nothing structured to send. |
| `outputSchema` | No | No | n/a | n/a | Would declare a shape nothing produces. Revisit with the handler contract, not before. |
| Tool `title` | No | No | n/a | n/a | Auto-deriving "Run Command" from `run_command` adds no information over the name. |
| `icons` (SEP-973) | No | No | n/a | n/a | Nothing to point at. |
| `_meta` | Yes | Yes | No | No | Inbound emits `_meta.ui` for MCP Apps. Outbound neither sends nor reads it. |
| Secret redaction on output | Yes | Yes | n/a | n/a | Tool results *and* resource bodies. |

## Transports

| Feature | Status | Note |
|---|---|---|
| stdio | Yes | Both directions. |
| Streamable HTTP (POST) | Yes | Both directions. |
| `Mcp-Session-Id` | Yes | Inbound mints, validates, expires and terminates; outbound echoes. |
| `MCP-Protocol-Version` header | Yes | Inbound validates (`400` on unsupported); outbound sends. |
| `DELETE` to terminate a session | Yes | Inbound. |
| HTTP GET stream (server→client) | **No** | Deliberate — see *Gaps*. |
| SSE resumability (`Last-Event-ID`) | **No** | Requires the GET stream. A broken request is re-issued whole. |
| HTTP+SSE (the pre-2025-03-26 transport) | n/a | Deprecated upstream in `2026-07-28`; never implemented here. |
| Origin validation / DNS-rebinding defence | Yes | Inbound HTTP, loopback plus `SAKTHAI_MCP_HTTP_ORIGIN`. |

## Client-initiated features

| Feature | Status | Note |
|---|---|---|
| Sampling (`sampling/createMessage`) | **No** | Needs the GET stream. See *Gaps*. |
| Elicitation (`elicitation/create`) | **No** | Same. |
| Roots (`roots/list`) | **No** | Same, and deprecated upstream in `2026-07-28`. |
| Logging (`logging/setLevel`, `notifications/message`) | **No** | Diagnostics go to stderr. Deprecated upstream in `2026-07-28`. |
| Progress notifications | **No** | Long tools are silent until they finish. |
| Completions (`completion/complete`) | **No** | One prompt with one free-text argument; there is nothing to complete. |
| Resource subscriptions | **No** | Advertised as `subscribe: false`, which is honest. |
| `listChanged` notifications | **No** | The tool set is a frozen tuple fixed at startup, so it cannot change. |
| Tasks (`tasks/*`) | **No** | An official *extension* as of `2026-07-28`, experimental before that. |
| OAuth (any flow) | **No** | Outbound sends static headers from the manifest. Inbound HTTP uses the gateway's bearer token. |

## Extensions

| Extension | Status | Note |
|---|---|---|
| `io.modelcontextprotocol/ui` (MCP Apps, SEP-1865) | **Partial, behind a flag** | Server side only. Declared in `capabilities.extensions`, serves `ui://` views at `text/html;profile=mcp-app`, links them via `_meta.ui.resourceUri`. Gated behind `SAKTHAI_EXPERIMENTAL` because the extension is Draft. |
| MCP Apps — host side | **host** | Iframe sandboxing, CSP construction, the `ui/*` postMessage methods, `visibility` enforcement. SakThai is a server; the spec further requires the iframe document be served by a server the *host* controls. |
| `io.modelcontextprotocol/tasks` | **No** | See above. |

## Gaps, and which are decisions

**The GET stream is the single structural absence.** Streamable HTTP's
server→client channel is what carries sampling, elicitation, roots, logging and
progress. Without it the server can only answer; it can never ask. Nothing in
`BUILTIN_TOOLS` needs to ask — every tool is a local operation over SQLite, the
filesystem, or an API the process already has credentials for. Implementing
half a stream would be worse than none: a host would negotiate the capability
and then wait. **Decision, revisit if a tool ever needs to ask the model
something mid-call.**

**The outbound client ignores resources and prompts.** It fetches only
`tools/list`. An external server's resources and prompts are invisible to the
agent. **This is a real gap**, not a decision — the agent loop has no concept of
a resource yet, so there is nowhere to put them. Tracked in the roadmap.

**No OAuth outbound.** A remote server is reached with whatever static
`Authorization` header the manifest carries, expanded from an environment
variable. Fine for the four servers the family configures, all of which issue
long-lived tokens. **A real gap for anything requiring an authorisation-code
flow.**

**`outputSchema`, `title` and `icons` are not emitted.** Every tool handler
returns `str`, so there is no structured output to declare a schema for; an
auto-derived title repeats the tool name; and there are no icons to point at.
Adding the fields with nothing behind them would make the matrix read better
and tell a host nothing. **Decision.**

**Inbound list methods return one page.** Valid: `nextCursor` absent means the
listing is complete. With 23 tools, one resource registry and one prompt, paging
would be machinery with no load to carry. **Decision.**
