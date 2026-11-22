#!/usr/bin/env python3
"""Smoke-drive the sakthai-agent-v2 CLI, stub server, and its MCP stdio server.

This is the agent-facing harness for the skill. It exercises every surface a
PR is likely to touch — the memory CLI, doctor/cycle/sessions/skills, a
memory export→import roundtrip, the zero-cost agent preflight (with and
without skill injection), the web API server (`python -m sakthai.web.server`),
and a live JSON-RPC roundtrip against `sakthai mcp` — in a throwaway
SAKTHAI_HOME, and exits non-zero if anything misbehaves.

No API key or network is required: the agent loop is exercised only via
`run --dry-run` (preflight), never a real model call.

Usage:
    python .claude/skills/run-sakthai-agent-v2/driver.py [smoke]
    python .claude/skills/run-sakthai-agent-v2/driver.py stub [--port N]
    python .claude/skills/run-sakthai-agent-v2/driver.py chat [--port N]
    SAKTHAI_BIN=/path/to/sakthai python .../driver.py   # override the binary
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
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BIN = os.environ.get("SAKTHAI_BIN", "sakthai")
TMUX_SESSION = "sakchat"
DEFAULT_PORT = 8765
failures: list[str] = []


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
                {
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                },
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


def _tmux(*args: str) -> str:
    return subprocess.run(["tmux", *args], capture_output=True, text=True, timeout=30).stdout


def interactive_chat(port: int) -> int:
    home = Path(tempfile.mkdtemp(prefix="sakthai-chat-"))
    start_stub(port)
    _tmux("kill-session", "-t", TMUX_SESSION)
    subprocess.run(
        [
            "tmux",
            "new-session",
            "-d",
            "-s",
            TMUX_SESSION,
            "-x",
            "160",
            "-y",
            "40",
            f"cd {REPO_ROOT} && SAKTHAI_HOME={home} OLLAMA_HOST=http://127.0.0.1:{port} "
            "uv run sakthai chat 2>&1",
        ],
        check=True,
        timeout=30,
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


def check(label: str, ok: bool, detail: str = "") -> None:
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {label}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(label)


def run(args: list[str], env: dict[str, str], stdin: str | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        [BIN, *args],
        env=env,
        input=stdin,
        capture_output=True,
        text=True,
        timeout=120,
        shell=False,
    )
    return proc.returncode, proc.stdout + proc.stderr


def drive_mcp(env: dict[str, str]) -> dict[int, dict]:
    """Pipe a JSON-RPC session into `sakthai mcp` and collect responses by id."""
    requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05"},
        },
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "learn",
                "arguments": {"value": "drove the MCP server", "kind": "note"},
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "recall", "arguments": {}},
        },
    ]
    payload = "".join(json.dumps(r) + "\n" for r in requests)
    proc = subprocess.run(
        [BIN, "mcp"],
        env=env,
        input=payload,
        capture_output=True,
        text=True,
        timeout=60,
        shell=False,
    )
    out: dict[int, dict] = {}
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        out[msg.get("id")] = msg
    return out


def smoke() -> int:
    home = Path(tempfile.mkdtemp(prefix="sakthai-smoke."))
    env = {**os.environ, "SAKTHAI_HOME": str(home)}
    print(f"sakthai-agent-v2 smoke · SAKTHAI_HOME={home}\n")

    try:
        print("CLI memory surface:")
        rc, out = run(["status"], env)
        check("status", rc == 0)
        rc, out = run(["learn", "prefers dark mode", "--kind", "pref", "--key", "ui"], env)
        check("learn", rc == 0 and "learned" in out.lower())
        rc, out = run(["recall", "dark"], env)
        check("recall finds the fact", rc == 0 and "dark mode" in out)
        rc, out = run(["memory", "stats"], env)
        check("memory stats", rc == 0 and "facts:" in out)
        rc, out = run(["tools"], env)
        check("tools lists builtins", rc == 0 and "learn" in out)

        print("\nSystem / state-machine surface:")
        rc, out = run(["doctor"], env)
        check("doctor", rc == 0)
        rc, out = run(["cycle", "status"], env)
        check("cycle status", rc == 0 and "DREAM" in out)
        rc, out = run(["cycle", "next"], env)
        check("cycle next advances stage", rc == 0 and "HOPE" in out)
        rc, out = run(["sessions", "list"], env)
        check("sessions list", rc == 0)
        rc, out = run(["skills", "list"], env)
        check("skills list discovers library", rc == 0 and "skill(s)" in out)

        print("\nMemory snapshot roundtrip (export → import into a fresh home):")
        snap = home / "snap.jsonl"
        rc, out = run(["memory", "export", str(snap)], env)
        check("memory export", rc == 0 and snap.exists())
        home2 = Path(tempfile.mkdtemp(prefix="sakthai-smoke2."))
        try:
            env2 = {**os.environ, "SAKTHAI_HOME": str(home2)}
            rc, out = run(["memory", "import", str(snap)], env2)
            check("memory import", rc == 0 and "imported" in out.lower())
            rc, out = run(["recall", "dark"], env2)
            check("imported fact recalls in new home", rc == 0 and "dark mode" in out)
        finally:
            shutil.rmtree(home2, ignore_errors=True)

        print("\nAgent preflight (no API call):")
        # A dry run exits 1 when the provider has no credentials, so hand it a
        # placeholder key: preflight only checks that one is present and never
        # calls the API.
        preflight_env = {**env, "ANTHROPIC_API_KEY": "sk-ant-placeholder"}
        rc, out = run(["run", "say hi", "--dry-run", "--no-mcp", "-p", "anthropic"], preflight_env)
        check("run --dry-run", rc == 0 and "runnable:    yes" in out)
        rc, out = run(
            [
                "run",
                "say hi",
                "--dry-run",
                "--no-mcp",
                "-p",
                "anthropic",
                "--with-skills",
                "sakthai-security-red-teaming",
            ],
            preflight_env,
        )
        check("run --dry-run --with-skills", rc == 0 and "runnable:    yes" in out)

        print("\nWeb API server (headless):")
        # The `dashboard` CLI command was removed (5de2c25); the JSON surface
        # now lives in `python -m sakthai.web.server` on 127.0.0.1:3001. All
        # /api/* endpoints require a Bearer token (web_auth fact in the same
        # MemoryStore the server reads), so fetch it via `sakthai web setup`.
        rc, setup_out = run(["web", "setup"], env)
        token = ""  # nosec B105 — empty initializer, filled from `web setup` below
        if rc == 0:
            for line in setup_out.splitlines():
                if line.strip().startswith("Token:"):
                    token = line.split(":", 1)[1].strip()
                    break
        srv = subprocess.Popen(
            [sys.executable, "-m", "sakthai.web.server"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            stages: dict = {}
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                try:
                    req = urllib.request.Request(
                        "http://127.0.0.1:3001/api/stages", headers=headers
                    )
                    # nosec B310 — literal http://127.0.0.1 loopback URL built a
                    # few lines up; no user input reaches the scheme or host.
                    with urllib.request.urlopen(req, timeout=2) as r:  # nosec B310
                        stages = json.loads(r.read())
                    break
                except OSError:
                    time.sleep(0.3)
            check("web server serves /api/stages JSON", "kpis" in stages)
            eco: dict = {}
            try:
                req = urllib.request.Request(
                    "http://127.0.0.1:3001/api/ecosystem", headers=headers
                )
                # nosec B310 — same literal loopback URL as above.
                with urllib.request.urlopen(req, timeout=2) as r:  # nosec B310
                    eco = json.loads(r.read())
            except OSError:
                pass
            check("web server serves /api/ecosystem JSON", "generated_at" in eco)
        finally:
            srv.terminate()
            srv.wait(timeout=10)

        print("\nMCP stdio server (live JSON-RPC roundtrip):")
        resp = drive_mcp(env)
        check(
            "initialize",
            resp.get(1, {}).get("result", {}).get("serverInfo", {}).get("name") == "sakthai",
        )
        check(
            "tools/list returns tools", len(resp.get(2, {}).get("result", {}).get("tools", [])) > 0
        )
        learn_text = resp.get(3, {}).get("result", {}).get("content", [{}])[0].get("text", "")
        check("tools/call learn stores a fact", "Stored fact" in learn_text)
        recall_text = resp.get(4, {}).get("result", {}).get("content", [{}])[0].get("text", "")
        check("tools/call recall reads it back", "drove the MCP server" in recall_text)
    finally:
        shutil.rmtree(home, ignore_errors=True)

    print()
    if failures:
        print(f"FAILED: {len(failures)} check(s): {', '.join(failures)}")
        return 1
    print("OK: all checks passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", default="smoke", choices=["smoke", "stub", "chat"])
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    if args.command == "chat":
        return interactive_chat(args.port)
    if args.command == "stub":
        start_stub(args.port)
        print(f"stub OpenAI-compatible server on http://127.0.0.1:{args.port}/v1 (Ctrl-C to stop)")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            return 0

    return smoke()


if __name__ == "__main__":
    sys.exit(main())
