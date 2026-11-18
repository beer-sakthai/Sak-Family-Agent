"""Microbenchmarks for SakThai core components using pytest-benchmark."""

from __future__ import annotations

from typing import Any

import pytest

try:
    import pytest_benchmark  # noqa: F401

    has_benchmark = True
except ImportError:
    has_benchmark = False

if not has_benchmark:
    pytest.skip("pytest-benchmark is not installed", allow_module_level=True)

from sakthai.mcp.servers import parse_mcp_servers


def _spec_benchmark_target() -> None:
    data = {
        "mcpServers": {
            "test_server": {
                "command": "node",
                "args": ["server.js"],
                "env": {"KEY": "value"},
            }
        }
    }
    parse_mcp_servers(data)


def test_benchmark_mcp_parse(benchmark: Any) -> None:
    """Benchmark MCP manifest parsing."""
    benchmark(_spec_benchmark_target)
