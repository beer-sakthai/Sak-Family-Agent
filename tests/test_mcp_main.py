"""Tests for the ``python -m sakthai.mcp`` entry point.

Two complementary tests:
1. A unit test that imports the module under ``__name__ == "__main__"`` with
   ``serve`` mocked — exercises the ``if __name__ == "__main__": serve()`` guard
   and provides in-process coverage.
2. An integration test that spawns the real subprocess, sends an ``initialize``
   JSON-RPC request, and checks the response.
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from unittest.mock import patch


def test_mcp_main_guard_calls_serve() -> None:
    """Running the module as __main__ invokes serve() exactly once."""
    with patch("sakthai.mcp.server.serve") as mock_serve:
        import sakthai.mcp.__main__ as main_mod  # noqa: F401 — side-effectful import

        # The module already ran at import; re-run it via runpy to trigger the guard.
        import runpy

        with patch("sakthai.mcp.__main__.serve", mock_serve):
            runpy.run_module("sakthai.mcp.__main__", run_name="__main__", alter_sys=False)
    mock_serve.assert_called_once()


def test_mcp_main_responds_to_initialize() -> None:
    """Subprocess integration: the server returns a valid initialize response."""
    request = (
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "0"},
                },
            }
        )
        + "\n"
    )

    proc = subprocess.Popen(
        [sys.executable, "-m", "sakthai.mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        stdout, _ = proc.communicate(input=request.encode(), timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        raise

    assert stdout, "No output from mcp module — server did not start"
    response = json.loads(stdout.decode().strip())
    assert response.get("id") == 1
    assert "result" in response
    assert response["result"].get("protocolVersion") is not None
