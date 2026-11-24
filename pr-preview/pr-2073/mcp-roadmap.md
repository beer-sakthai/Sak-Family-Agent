# MCP roadmap

Where this package's MCP support is going, and — more usefully — what it is
deliberately not chasing.

Current state is in [`mcp-support-matrix.md`](mcp-support-matrix.md); the
lifecycle policy behind every "deprecated" below is in
[`mcp-deprecations.md`](mcp-deprecations.md).

## The constraint that shapes everything

The specification is revised on a date-stamped schedule, and the revisions are
not additive. `2026-07-28` **removes** `initialize`, `ping`, protocol-level
sessions, `resources/subscribe`, SSE resumability and the HTTP GET stream, and
deprecates roots, sampling and logging. The surface sheds features at least as
fast as an implementation can add them.

So "catch up with the spec" is not a goal that terminates. The goal is: speak a
range of revisions honestly, implement the parts that carry load, and record
the rest as decided rather than pending.

## Shipped

- Protocol negotiation across `2024-11-05` → `2025-11-25`, replacing an
  `initialize` that echoed back whatever the client asked for.
- The namespace guardrail bypass, `args` smuggling, sandbox shell injection and
  unreachable strict mode, all closed. See
  [`mcp-threat-model.md`](mcp-threat-model.md).
- Outbound tool-list pagination — only page one was ever visible — and non-text
  content surfaced rather than silently dropped.
- Inbound Streamable HTTP at `POST /v1/mcp`, with sessions, Origin validation
  and a confirmation filter.
- A feature lifecycle registry with a twelve-month deprecation window.
- `ui://` MCP App views behind `SAKTHAI_EXPERIMENTAL`.
- A registry client, and the supply-chain check it enables.

## Next, in order of what it buys

### 1. A shared base for persona MCP manifests

The three remote docs servers are copy-pasted verbatim into all six persona
`mcp.json` files. `personas/shared/config/` has no `mcp.json`, so there is no
inheritance to use. Six copies of one fact is six places to forget.

A `personas/shared/config/mcp.json` base merged under each persona's overlay,
following the precedence chain `mcp/servers.py` already implements. Small, and
removes a whole class of drift.

### 2. Outbound resources and prompts

`StdioMCPClient` and `RemoteMCPClient` fetch `tools/list` and nothing else. An
external server's resources and prompts are invisible to the agent.

This is a real gap, but it is blocked on something else: the agent loop has no
concept of a resource, so there is nowhere to put one. The work is in
`agent/loop.py` and the system-prompt builder first; the client change is the
easy half.

### 3. OAuth for remote servers

Today a remote server is reached with a static `Authorization` header expanded
from an environment variable. That covers every server the family configures,
all of which issue long-lived tokens, and covers nothing that needs an
authorisation-code flow.

Worth doing when a server the family actually wants requires it — which is the
honest trigger, since the alternative is building a flow against no concrete
consumer.

### 4. `outputSchema` and structured results

Every tool handler returns `str`. Declaring an `outputSchema` first requires
changing that contract, which touches all 23 tools and the agent loop's result
handling. The payoff is real — a host could parse results instead of
pattern-matching text, and the `ui://` view would not have to parse lines — but
the schema is the *last* step of that work, not the first.

## Deferred, with reasons

### `2026-07-28`

The stateless revision. Adopting it means:

- removing the `initialize`/`notifications/initialized` handshake;
- moving the protocol version into per-request
  `_meta["io.modelcontextprotocol/protocolVersion"]`;
- implementing `server/discover`;
- adding a required `resultType` to every result;
- replacing `resources/subscribe` with `subscriptions/listen`;
- removing `ping` and `logging/setLevel`.

That is a second server, not a modified one, and it breaks every host currently
speaking `2024-11-05` through `2025-11-25` to this one. The sane shape is to
run both behind the version table in `mcp/protocol.py` — negotiation already
exists to make that possible — and that is a project with its own plan, not a
line item here.

**Trigger:** a host the family uses requires it, or `2025-11-25` stops being
accepted upstream. Neither has happened.

### The HTTP GET stream, and everything behind it

Sampling, elicitation, roots, logging and progress notifications all need the
server→client channel. Nothing in `BUILTIN_TOOLS` needs to ask the model or the
user anything mid-call — every tool is a local operation over SQLite, the
filesystem, or an API the process already holds credentials for.

Implementing half a stream is worse than none: a host would negotiate the
capability and then wait on a message that never comes.

**Trigger:** a tool that genuinely needs to ask something mid-call. Elicitation
for a destructive confirmation over HTTP is the most plausible candidate, and
would replace the blunt `SAKTHAI_MCP_HTTP_WRITE_ALLOW` filter with something
that can actually ask.

### MCP Apps on the host side

Iframe sandboxing, CSP construction, the `ui/*` postMessage methods,
`visibility` enforcement. This package is a server; the extension further
requires that the iframe document be served by a server the *host* controls, so
the host side is a different product. `apps/sak_agent_dashboard` would be where
it lived, and `web/server.py` sends `X-Frame-Options: DENY` unconditionally
today, so even the groundwork is unbuilt.

**Trigger:** wanting the dashboard to render other servers' views, not just
ours.

### Tasks (`io.modelcontextprotocol/tasks`)

An official extension as of `2026-07-28`, experimental before that. Long-running
tool calls would benefit — `run_agent_loop` especially — but the extension
moved tracks once already, and adopting a moving target to solve a problem
nobody has reported is how the version drift started.

## How to keep this file honest

Every claim here is checkable. When something ships, move it to **Shipped** and
update the matrix in the same change. When a trigger fires, say so. A roadmap
that only grows is a wish list.
