#!/usr/bin/env python3
"""Smoke-drive the sakthai-agent-v2 CLI and its MCP stdio server.

This is the agent-facing harness for the skill. It exercises every surface a
PR is likely to touch — the memory CLI, the zero-cost agent preflight, the
dashboard JSON export, and a live JSON-RPC roundtrip against `sakthai mcp` —
in a throwaway SAKTHAI_HOME, and exits non-zero if anything misbehaves.

No API key or network is required: the agent loop is exercised only via
`run --dry-run` (preflight), never a real model call. If no Anthropic
credential is present in the environment, a placeholder `ANTHROPIC_API_KEY`
is injected so the "runnable" preflight check has something to resolve —
`--dry-run` never uses it to make a request.

Usage:
    python .claude/skills/run-sakthai-agent-v2/driver.py
    SAKTHAI_BIN=/path/to/sakthai python .../driver.py   # override the binary
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
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
        [BIN, "mcp"], env=env, input=payload, capture_output=True, text=True, timeout=60
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
    if not env.get("ANTHROPIC_API_KEY") and not env.get("ANTHROPIC_AUTH_TOKEN"):
        env["ANTHROPIC_API_KEY"] = "sk-ant-smoke-dry-run-placeholder"
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

        print("\nAgent preflight (no API call):")
        rc, out = run(["run", "say hi", "--dry-run", "--no-mcp"], env)
        check("run --dry-run", rc == 0 and "runnable:" in out)

        print("\nDashboard export (headless):")
        snap = home / "data.json"
        rc, out = run(["dashboard", "--export", str(snap)], env)
        ok = rc == 0 and snap.is_file()
        if ok:
            try:
                json.loads(snap.read_text())
            except Exception:
                ok = False
        check("dashboard --export writes valid JSON", ok)

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
        subprocess.run(["rm", "-rf", str(home)])

    print()
    if failures:
        print(f"FAILED: {len(failures)} check(s): {', '.join(failures)}")
        return 1
    print("OK: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
