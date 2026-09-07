#!/usr/bin/env python3
"""Driver for running and smoke-testing the sakthai chat CLI offline.

Stdlib-only. Three subcommands:

  python3 .claude/skills/run-sakthai-chat-cli/driver.py smoke
      Full offline smoke: CLI basics, memory learn/recall, MCP stdio
      JSON-RPC round trip, and a real chat REPL round trip in tmux
      against the built-in stub model server. Prints PASS/FAIL per
      step; exits non-zero on any failure.

  python3 .claude/skills/run-sakthai-chat-cli/driver.py stub [--port N]
      Run only the stub OpenAI-compatible server (POST /v1/chat/completions,
      streaming and non-streaming). Replies "STUB-REPLY: you said <msg>".

  python3 .claude/skills/run-sakthai-chat-cli/driver.py chat [--port N]
      Start the stub server and a tmux session ("sakchat") running
      `sakthai chat` against it, then leave both running for interactive
      poking via `tmux send-keys -t sakchat ... Enter` and
      `tmux capture-pane -t sakchat -p`. Ctrl-C stops the stub.

Everything writes to a throwaway SAKTHAI_HOME so the real ~/.sakthai is
never touched.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TMUX_SESSION = "sakchat"
DEFAULT_PORT = 8765


# --------------------------------------------------------------------------
# Stub OpenAI-compatible server
# --------------------------------------------------------------------------


class _StubHandler(BaseHTTPRequestHandler):
    """Minimal /v1/chat/completions: echoes the last user message back."""

    def do_POST(self) -> None:  # noqa: N802 (http.server API)
        if not self.path.endswith("/chat/completions"):
            self.send_error(404)
            return
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        last_user = next(
            (
                m.get("content") or ""
                for m in reversed(body.get("messages", []))
                if m.get("role") == "user" and isinstance(m.get("content"), str)
            ),
            "",
        )
        reply = f"STUB-REPLY: you said {last_user!r}"
        if body.get("stream"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            for chunk in (
                {"choices": [{"index": 0, "delta": {"role": "assistant", "content": reply}}]},
                {"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                 "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}},
            ):
                self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
            self.wfile.write(b"data: [DONE]\n\n")
        else:
            payload = json.dumps(
                {
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": reply},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    def log_message(self, fmt: str, *args: object) -> None:  # silence per-request noise
        pass


def start_stub(port: int) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", port), _StubHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


# --------------------------------------------------------------------------
# Smoke steps
# --------------------------------------------------------------------------


def _run(cmd: list[str], env: dict[str, str], input_text: str | None = None) -> str:
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env=env,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} exited {proc.returncode}:\n{proc.stderr[-2000:]}")
    return proc.stdout


def _tmux(*args: str) -> str:
    return subprocess.run(
        ["tmux", *args], capture_output=True, text=True, timeout=30
    ).stdout


def _wait_for_pane_text(needle: str, timeout: float) -> str:
    deadline = time.time() + timeout
    pane = ""
    while time.time() < deadline:
        pane = _tmux("capture-pane", "-t", TMUX_SESSION, "-p")
        if needle in pane:
            return pane
        time.sleep(1)
    raise RuntimeError(f"never saw {needle!r} in tmux pane; last screen:\n{pane}")


def smoke(port: int) -> int:
    home = Path(tempfile.mkdtemp(prefix="sakthai-smoke-"))
    env = {**os.environ, "SAKTHAI_HOME": str(home)}
    env.pop("ANTHROPIC_API_KEY", None)  # prove the offline path needs no creds
    failures: list[str] = []

    def step(name: str, fn) -> None:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 (report and continue)
            failures.append(name)
            print(f"  FAIL  {name}: {exc}")

    print(f"smoke: repo={REPO_ROOT} SAKTHAI_HOME={home}")

    step("cli --help lists commands", lambda: _assert_in("chat", _run(["uv", "run", "sakthai", "--help"], env)))
    step("doctor runs", lambda: _assert_in("SakThai Doctor", _run(["uv", "run", "sakthai", "doctor"], env)))
    step("tools lists built-ins", lambda: _assert_in("recall", _run(["uv", "run", "sakthai", "tools"], env)))
    step(
        "learn stores a fact",
        lambda: _assert_in(
            "learned",
            _run(["uv", "run", "sakthai", "learn", "smoke fact alpha", "--tag", "smoke"], env),
        ),
    )
    step(
        "recall finds it",
        lambda: _assert_in("smoke fact alpha", _run(["uv", "run", "sakthai", "recall", "alpha"], env)),
    )

    def mcp_round_trip() -> None:
        requests = "\n".join(
            json.dumps(r)
            for r in (
                {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                 "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                            "clientInfo": {"name": "smoke", "version": "0"}}},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                 "params": {"name": "recall", "arguments": {"query": "alpha"}}},
            )
        )
        out = _run(["uv", "run", "sakthai", "mcp"], env, input_text=requests + "\n")
        responses = {json.loads(line)["id"]: json.loads(line) for line in out.splitlines() if line.strip()}
        assert responses[1]["result"]["serverInfo"]["name"] == "sakthai"
        names = [t["name"] for t in responses[2]["result"]["tools"]]
        assert "recall" in names and "learn" in names, names
        assert "smoke fact alpha" in responses[3]["result"]["content"][0]["text"]

    step("mcp stdio JSON-RPC round trip", mcp_round_trip)

    def chat_round_trip() -> None:
        if not shutil.which("tmux"):
            raise RuntimeError("tmux not installed (apt-get install -y tmux)")
        server = start_stub(port)
        _tmux("kill-session", "-t", TMUX_SESSION)
        try:
            subprocess.run(
                ["tmux", "new-session", "-d", "-s", TMUX_SESSION, "-x", "160", "-y", "40",
                 f"cd {REPO_ROOT} && SAKTHAI_HOME={home} OLLAMA_HOST=http://127.0.0.1:{port} "
                 "uv run sakthai chat 2>&1"],
                check=True, timeout=30,
            )
            _wait_for_pane_text("SAK FAMILY TERMINAL", timeout=30)
            _tmux("send-keys", "-t", TMUX_SESSION, "hello from the smoke test", "Enter")
            _wait_for_pane_text("STUB-REPLY", timeout=30)
            _tmux("send-keys", "-t", TMUX_SESSION, "/exit", "Enter")
            time.sleep(2)
        finally:
            _tmux("kill-session", "-t", TMUX_SESSION)
            server.shutdown()

    step("chat REPL round trip vs stub model", chat_round_trip)

    shutil.rmtree(home, ignore_errors=True)
    print("smoke:", "FAILED" if failures else "OK", f"({len(failures)} failure(s))" if failures else "")
    return 1 if failures else 0


def _assert_in(needle: str, haystack: str) -> None:
    assert needle in haystack, f"{needle!r} not found in output:\n{haystack[:1000]}"


# --------------------------------------------------------------------------
# Interactive chat session against the stub
# --------------------------------------------------------------------------


def interactive_chat(port: int) -> int:
    home = Path(tempfile.mkdtemp(prefix="sakthai-chat-"))
    start_stub(port)
    _tmux("kill-session", "-t", TMUX_SESSION)
    subprocess.run(
        ["tmux", "new-session", "-d", "-s", TMUX_SESSION, "-x", "160", "-y", "40",
         f"cd {REPO_ROOT} && SAKTHAI_HOME={home} OLLAMA_HOST=http://127.0.0.1:{port} "
         "uv run sakthai chat 2>&1"],
        check=True, timeout=30,
    )
    print(f"stub on 127.0.0.1:{port}; tmux session {TMUX_SESSION!r} running `sakthai chat`.")
    print(f"  poke it :  tmux send-keys -t {TMUX_SESSION} 'hi there' Enter")
    print(f"  read it :  tmux capture-pane -t {TMUX_SESSION} -p")
    print("Ctrl-C here stops the stub server (tmux session survives).")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["smoke", "stub", "chat"])
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    if args.command == "smoke":
        return smoke(args.port)
    if args.command == "chat":
        return interactive_chat(args.port)
    start_stub(args.port)
    print(f"stub OpenAI-compatible server on http://127.0.0.1:{args.port}/v1 (Ctrl-C to stop)")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
