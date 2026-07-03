"""Tests for the ``python -m sakthai.mcp`` entry point.

Two complementary tests:
1. A unit test that imports the module under ``__name__ == "__main__"`` with
   ``serve`` mocked — exercises the ``if __name__ == "__main__": serve()`` guard
   and provides in-process coverage.
2. An integration test that spawns the real subprocess, sends an ``initialize``
   JSON-RPC request, and checks the response.
"""

from __future__ import annotations

import json
import runpy
import subprocess
import sys
from unittest.mock import patch

import pytest


def test_mcp_main_guard_calls_serve() -> None:
    """Running the module as __main__ invokes serve() exactly once."""
    with patch("sakthai.mcp.server.serve") as mock_serve:
        import sakthai.mcp.__main__  # noqa: F401 — side-effectful import

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


def test_mcp_main_handles_invalid_json() -> None:
    """Subprocess integration: the server should handle malformed JSON gracefully."""
    request = "this is not json\n"

    proc = subprocess.Popen(
        [sys.executable, "-m", "sakthai.mcp"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        stdout, stderr = proc.communicate(input=request.encode(), timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        pytest.fail("MCP process timed out on invalid JSON input.")

    # The server should handle this gracefully. The most robust behavior is to return
    # a JSON-RPC error on stdout. A simpler, but also acceptable, behavior is to
    # exit with a non-zero status and print an error to stderr. We'll check for
    # the simpler case first, as it's a common implementation pattern.
    if proc.returncode != 0 and stderr:
        # Case 1: The process exited with an error and wrote to stderr. This is acceptable.
        error_message = stderr.decode().lower()
        assert "json" in error_message or "decode" in error_message, (
            "stderr should contain a JSON-related error message."
        )
    elif stdout:
        # Case 2: The process returned a JSON-RPC error response on stdout. This is ideal.
        try:
            response = json.loads(stdout.decode())
            assert "error" in response, (
                "Server should return a JSON-RPC error for malformed request"
            )
            assert response["error"]["code"] == -32700  # Parse error
        except json.JSONDecodeError:
            pytest.fail("Server response was not valid JSON.")
    else:
        pytest.fail(
            "Server did not handle invalid JSON gracefully (no stderr error or stdout response)."
        )
