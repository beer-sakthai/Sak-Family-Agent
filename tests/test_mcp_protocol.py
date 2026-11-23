"""The protocol-revision table and version negotiation.

`mcp/server.py` and `mcp/client.py` each carried their own
`PROTOCOL_VERSION = "2024-11-05"` — two independent constants for one protocol,
both naming the *oldest* revision that exists. `mcp/protocol.py` is now the
single source, and the server negotiates instead of echoing the client's value
back unexamined.
"""

from __future__ import annotations

import pytest

from sakthai.mcp import client as client_mod
from sakthai.mcp import server as server_mod
from sakthai.mcp.protocol import (
    LATEST_PROTOCOL_VERSION,
    OLDEST_SUPPORTED_PROTOCOL_VERSION,
    PROTOCOL_VERSION,
    PROTOCOL_VERSION_HEADER,
    SUPPORTED_PROTOCOL_VERSIONS,
    is_supported,
    negotiate_protocol_version,
)

# --- the table ---------------------------------------------------------------


def test_versions_are_sorted_ascending() -> None:
    """`negotiate_protocol_version` and `LATEST` both rely on the ordering."""
    assert list(SUPPORTED_PROTOCOL_VERSIONS) == sorted(SUPPORTED_PROTOCOL_VERSIONS)


def test_versions_are_unique() -> None:
    assert len(set(SUPPORTED_PROTOCOL_VERSIONS)) == len(SUPPORTED_PROTOCOL_VERSIONS)


def test_latest_and_oldest_are_the_ends_of_the_table() -> None:
    assert SUPPORTED_PROTOCOL_VERSIONS[-1] == LATEST_PROTOCOL_VERSION
    assert SUPPORTED_PROTOCOL_VERSIONS[0] == OLDEST_SUPPORTED_PROTOCOL_VERSION


def test_every_version_is_a_date_stamp() -> None:
    import re

    for version in SUPPORTED_PROTOCOL_VERSIONS:
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", version), version


def test_the_stateless_revision_is_deliberately_absent() -> None:
    """`2026-07-28` removes `initialize`, `ping`, sessions, roots and sampling.

    Supporting it is a rewrite, not a bump — tracked in docs/mcp-roadmap.md.
    Listing it here without implementing the stateless handshake would make the
    server advertise a protocol it cannot speak, which is the exact failure
    negotiation exists to prevent.
    """
    assert "2026-07-28" not in SUPPORTED_PROTOCOL_VERSIONS


def test_the_legacy_default_is_still_accepted() -> None:
    """Hosts pinned to the first revision must keep working."""
    assert "2024-11-05" in SUPPORTED_PROTOCOL_VERSIONS


# --- is_supported ------------------------------------------------------------


@pytest.mark.parametrize("version", SUPPORTED_PROTOCOL_VERSIONS)
def test_is_supported_accepts_table_entries(version: str) -> None:
    assert is_supported(version)


@pytest.mark.parametrize("value", ["", "x", "2026-07-28", "9999-01-01", None, 20241105, [], {}])
def test_is_supported_rejects_everything_else(value: object) -> None:
    assert not is_supported(value)


# --- negotiation -------------------------------------------------------------


@pytest.mark.parametrize("version", SUPPORTED_PROTOCOL_VERSIONS)
def test_negotiation_grants_a_supported_request(version: str) -> None:
    assert negotiate_protocol_version(version) == version


@pytest.mark.parametrize(
    "value",
    [None, "", "x", "banana", "2026-07-28", "9999-01-01", 20241105, {"a": 1}],
)
def test_negotiation_falls_back_to_latest(value: object) -> None:
    """Anything we cannot speak is answered with what we can."""
    assert negotiate_protocol_version(value) == LATEST_PROTOCOL_VERSION


def test_negotiation_never_invents_a_version() -> None:
    for value in [None, "x", "2026-07-28", *SUPPORTED_PROTOCOL_VERSIONS]:
        assert is_supported(negotiate_protocol_version(value))


# --- the single source -------------------------------------------------------


def test_server_and_client_share_one_version() -> None:
    assert server_mod.PROTOCOL_VERSION == client_mod.PROTOCOL_VERSION == PROTOCOL_VERSION


def test_the_shared_version_is_the_latest_not_the_oldest() -> None:
    """Both modules used to hardcode the oldest revision."""
    assert PROTOCOL_VERSION == LATEST_PROTOCOL_VERSION
    assert PROTOCOL_VERSION != "2024-11-05"


def test_header_name_is_spelled_as_the_spec_does() -> None:
    assert PROTOCOL_VERSION_HEADER == "MCP-Protocol-Version"
