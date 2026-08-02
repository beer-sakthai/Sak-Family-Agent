#!/usr/bin/env python3
"""Smoke-drive the sakthai-agent-v2 CLI and its MCP stdio server.

This is the agent-facing harness for the skill. It exercises every surface a
PR is likely to touch — the memory CLI, doctor/cycle/sessions/skills, a
memory export→import roundtrip, the zero-cost agent preflight (with and
without skill injection), the web API server (`python -m sakthai.web.server`),
and a live JSON-RPC roundtrip against `sakthai mcp` — in a throwaway
SAKTHAI_HOME, and exits non-zero if anything misbehaves.

No API key or network is required: the agent loop is exercised only via
`run --dry-run` (preflight), never a real model call.

Usage:
    python .claude/skills/run-sakthai-agent-v2/driver.py
    SAKTHAI_BIN=/path/to/sakthai python .../driver.py   # override the binary
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

BIN = os.environ.get("SAKTHAI_BIN", "sakthai")
failures: list[str] = []


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


def main() -> int:
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
        rc, out = run(["run", "say hi", "--dry-run", "--no-mcp"], env)
        check("run --dry-run", rc == 0 and "runnable:" in out)
        rc, out = run(
            [
                "run",
                "say hi",
                "--dry-run",
                "--no-mcp",
                "--with-skills",
                "sakthai-security-red-teaming",
            ],
            env,
        )
        check("run --dry-run --with-skills", rc == 0 and "runnable:" in out)

        print("\nWeb API server (headless):")
        # The `dashboard` CLI command was removed (5de2c25); the JSON surface
        # now lives in `python -m sakthai.web.server` on 127.0.0.1:3001.
        srv = subprocess.Popen(
            [sys.executable, "-m", "sakthai.web.server"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            stages: dict = {}
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                try:
                    with urllib.request.urlopen("http://127.0.0.1:3001/api/stages", timeout=2) as r:
                        stages = json.loads(r.read())
                    break
                except OSError:
                    time.sleep(0.3)
            check("web server serves /api/stages JSON", "kpis" in stages)
            eco: dict = {}
            try:
                with urllib.request.urlopen("http://127.0.0.1:3001/api/ecosystem", timeout=2) as r:
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


if __name__ == "__main__":
    sys.exit(main())
