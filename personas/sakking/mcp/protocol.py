"""Protocol revisions this package speaks, and how a version is agreed.

The MCP specification is revised on a date-stamped schedule (``YYYY-MM-DD``),
and the revisions are not purely additive — ``2026-07-28`` removes
``initialize``, ``ping``, sessions, roots, sampling and ``logging/setLevel``
outright. So "which revision" is a real compatibility decision, not a constant
to bump.

Both the inbound server and the outbound client used to carry their own
``PROTOCOL_VERSION = "2024-11-05"`` — two independent constants for one
protocol, and ``2024-11-05`` is the *oldest* revision that exists. This module
is the single source of truth for both.

Negotiation, as the targeted revisions define it: the client sends the latest
version it supports; the server replies with the version it intends to use,
which need not be the one asked for; if the client cannot speak the server's
answer it disconnects. The server's obligation is to name a version it actually
implements.

:func:`negotiate_protocol_version` does that. The server previously answered
``params.get("protocolVersion") or PROTOCOL_VERSION`` — it echoed the client's
string back unexamined, so a client asking for ``2026-07-28`` (whose handshake
this package does not implement) or for ``banana`` was told both were fine.
A test asserted that echo as intended behavior.

**Why the range stops at 2025-11-25.** That is the previous stable revision and
the newest one whose shape this package implements: an ``initialize``/
``initialized`` handshake, a session-bearing Streamable HTTP transport, and
server-initiated feature negotiation through ``capabilities``. ``2026-07-28``
replaces all three with a stateless per-request model (``server/discover``,
``_meta["io.modelcontextprotocol/protocolVersion"]``, ``resultType`` on every
result). Adopting it is a rewrite, not a bump, and is tracked separately in
``docs/mcp-roadmap.md``.
"""

from __future__ import annotations

#: Every protocol revision this package implements, oldest first.
#:
#: Order is significant: :func:`negotiate_protocol_version` treats later
#: entries as preferred, and the list being sorted ascending by date is what
#: makes "highest mutually supported" a simple reverse scan. Keep it sorted.
SUPPORTED_PROTOCOL_VERSIONS: tuple[str, ...] = (
    "2024-11-05",
    "2025-03-26",
    "2025-06-18",
    "2025-11-25",
)

#: The revision this package prefers and advertises when given no preference.
LATEST_PROTOCOL_VERSION: str = SUPPORTED_PROTOCOL_VERSIONS[-1]

#: The oldest revision still accepted. Kept as a name because it is referenced
#: by the deprecation registry in ``mcp/lifecycle.py``.
OLDEST_SUPPORTED_PROTOCOL_VERSION: str = SUPPORTED_PROTOCOL_VERSIONS[0]

#: Retained for callers that imported the old module-level constant. It names
#: the *preferred* revision now rather than a hardcoded ``2024-11-05``.
PROTOCOL_VERSION: str = LATEST_PROTOCOL_VERSION

#: HTTP header carrying the agreed revision on the Streamable HTTP transport.
#: Required from ``2025-06-18`` onward; this package did not send it at all,
#: leaking the version only through its ``User-Agent``.
PROTOCOL_VERSION_HEADER = "MCP-Protocol-Version"


def is_supported(version: object) -> bool:
    """Whether ``version`` is a revision this package implements."""
    return isinstance(version, str) and version in SUPPORTED_PROTOCOL_VERSIONS


def negotiate_protocol_version(requested: object) -> str:
    """The revision to answer an ``initialize`` carrying ``requested`` with.

    Returns the requested revision when it is one we implement, and
    :data:`LATEST_PROTOCOL_VERSION` otherwise — including when the client sent
    nothing, sent a revision newer than we implement, or sent something that is
    not a version string at all.

    Answering with our own latest, rather than echoing, is what the targeted
    revisions require: the reply must name a version the server will really
    speak, so that a client which cannot speak it can disconnect rather than
    proceed on a false agreement.
    """
    if is_supported(requested):
        return str(requested)
    return LATEST_PROTOCOL_VERSION
