#!/usr/bin/env python3
"""Fuzz the MCP stdio server's JSON-RPC request handler.

``handle_request`` is the one place this package parses a message written by
another process. It is reachable by anything that can speak to the server's
stdin, it is a pure function over ``(request, store)``, and its output is
serialised straight back onto the wire — which makes it both an ideal fuzz
target and one where "did not raise" is too weak an invariant.

What is asserted:

* It never raises. The stdio loop reads one message at a time; an exception
  here takes the server down, so a malformed request from a peer is a remote
  denial of service.
* Its return value is either ``None`` (notification) or a well-formed JSON-RPC
  2.0 response carrying exactly one of ``result``/``error``.
* That response is JSON-serialisable. The server writes it with ``json.dumps``
  *after* ``handle_request`` returns, so a response holding a non-serialisable
  value fails outside this function and looks like a transport bug.

Only store-backed tools are exposed to the fuzzer. ``tools/call`` really does
invoke the handler, so passing the full ``BUILTIN_TOOLS`` set would let fuzzed
input reach ``run_command``, ``read_file`` and the Telegram/Graph network
tools. The four here read and write nothing but the in-memory store.

Run with Atheris (see fuzz/README.md); the invariant itself is exercised by
tests/test_fuzz_harnesses.py without it.
"""

from __future__ import annotations

import contextlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))

try:  # pragma: no cover - exercised only in a fuzzing environment
    import atheris
except ImportError:  # pragma: no cover - the normal test environment
    atheris = None  # type: ignore[assignment]

from sakthai.agent.tools import BUILTIN_TOOLS  # noqa: E402
from sakthai.mcp.server import handle_request  # noqa: E402
from sakthai.memory.store import MemoryStore  # noqa: E402

_STORE = MemoryStore(":memory:")

_SAFE_TOOL_NAMES = {"learn", "recall", "search", "forget"}
_SAFE_TOOLS = tuple(t for t in BUILTIN_TOOLS if t.name in _SAFE_TOOL_NAMES)


def _requests_from(data: bytes) -> list[Any]:
    """Turn one fuzzer buffer into request objects worth dispatching.

    Random bytes are almost never valid JSON, so a harness that only parsed
    them would spend the campaign on the ``Invalid JSON-RPC 2.0 request`` early
    return. Valid JSON is dispatched as-is; anything else is also wrapped into
    a structurally valid envelope so the method dispatch and ``tools/call``
    paths stay reachable.
    """
    text = data.decode("utf-8", errors="surrogateescape")
    requests: list[Any] = []

    with contextlib.suppress(ValueError, RecursionError):
        requests.append(json.loads(text))

    method, _, rest = text.partition("\x00")
    requests.append(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": {"name": method, "arguments": {"value": rest, "query": rest}},
        }
    )
    return requests


def exercise(data: bytes) -> None:
    """Assert the request-handling contract for one fuzzed buffer."""
    for request in _requests_from(data):
        response = handle_request(request, _STORE, tools=_SAFE_TOOLS)

        if response is None:
            continue

        assert isinstance(response, dict), f"response is not a dict: {response!r}"
        assert response.get("jsonrpc") == "2.0", f"missing JSON-RPC version: {response!r}"

        has_result = "result" in response
        has_error = "error" in response
        assert has_result != has_error, f"must carry exactly one of result/error: {response!r}"

        try:
            json.dumps(response)
        except (TypeError, ValueError) as exc:  # pragma: no cover - the bug being hunted
            raise AssertionError(f"response is not JSON-serialisable: {response!r}") from exc


def _test_one_input(data: bytes) -> None:  # pragma: no cover - Atheris entry point
    exercise(data)


def main() -> None:  # pragma: no cover - Atheris entry point
    if atheris is None:
        raise SystemExit("atheris is not installed; see fuzz/README.md")
    # Without this the campaign has no coverage feedback: libFuzzer reports
    # "no interesting inputs were found" and the corpus never grows past the
    # first input, degrading the fuzzer into a random input generator.
    # `instrument_all` covers the already-imported sakthai modules, which is
    # what lets the imports above stay plain enough to run without Atheris.
    atheris.instrument_all()
    atheris.Setup(sys.argv, _test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":  # pragma: no cover
    main()
