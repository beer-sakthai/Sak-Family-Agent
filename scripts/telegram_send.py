#!/usr/bin/env python3
"""Send a Telegram message through the sakthai `send_telegram_message` tool.

A thin, repeatable wrapper around the live MCP roundtrip used to smoke-test the
Telegram surface. Unlike a hand-typed JSON-RPC pipe it:

  * loads TELEGRAM_* from sakthai-agent-v2/.env if not already exported,
  * auto-discovers the chat id from getUpdates when TELEGRAM_CHAT_ID is unset
    (and tells you to message the bot first if there's been no contact),
  * drives the real `sakthai mcp` server so it exercises the same path an agent
    or MCP client would, then prints the tool's reply and exits non-zero on
    failure.

Usage:
    python scripts/telegram_send.py "your message here"
    python scripts/telegram_send.py            # sends a default test message

Requires the venv's `sakthai` on PATH (`source .venv/bin/activate`) or
SAKTHAI_BIN=/abs/path/to/sakthai.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = REPO_ROOT / ".env"


def load_env_file(path: Path) -> None:
    """Populate os.environ from KEY=VALUE lines in .env (existing vars win)."""
    if not path.is_file():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def discover_chat_id(token: str) -> str | None:
    """Return the most recent private chat id that has messaged the bot."""
    if not re.match(r"^[0-9]+:[a-zA-Z0-9_-]+$", token):
        print(f"  invalid TELEGRAM_BOT_TOKEN format: {token}", file=sys.stderr)
        return None
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:  # nosec B310
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"  getUpdates failed: {exc}", file=sys.stderr)
        return None
    chat_id: str | None = None
    for update in data.get("result", []):
        msg = update.get("message") or update.get("edited_message") or {}
        chat = msg.get("chat") or {}
        if chat.get("id") is not None:
            chat_id = str(chat["id"])
    return chat_id


def send_via_mcp(message: str) -> int:
    sakthai_bin = os.environ.get("SAKTHAI_BIN", "sakthai")
    env = dict(os.environ)
    env["SAKTHAI_HOME"] = tempfile.mkdtemp(prefix="sakthai-tg.")
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2024-11-05"}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "send_telegram_message",
                    "arguments": {"message": message}}},
    ]
    stdin = "".join(json.dumps(r) + "\n" for r in requests)
    proc = subprocess.run(
        [sakthai_bin, "mcp"], input=stdin, capture_output=True, text=True, env=env,
    )
    if proc.returncode != 0:
        print(proc.stderr.strip() or "sakthai mcp exited non-zero", file=sys.stderr)
        return proc.returncode or 1
    reply = ""
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        if msg.get("id") == 2:
            reply = msg.get("result", {}).get("content", [{}])[0].get("text", "")
    print(reply or "(no reply from send_telegram_message)")
    return 0 if reply.startswith("Telegram message sent") else 1


def main(argv: list[str]) -> int:
    message = argv[1] if len(argv) > 1 else (
        "✅ sakthai-agent-v2 → Telegram live send works."
    )
    load_env_file(ENV_FILE)

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN is not set (checked env and .env).", file=sys.stderr)
        return 2
    if not re.match(r"^[0-9]+:[a-zA-Z0-9_-]+$", token):
        print(f"TELEGRAM_BOT_TOKEN has an invalid format: {token}", file=sys.stderr)
        return 2

    if not os.environ.get("TELEGRAM_CHAT_ID"):
        print("TELEGRAM_CHAT_ID unset — discovering from getUpdates…")
        chat_id = discover_chat_id(token)
        if not chat_id:
            print(
                "No chat contact found. Open the bot in Telegram, tap Start / send "
                "any message, then re-run.", file=sys.stderr,
            )
            return 3
        os.environ["TELEGRAM_CHAT_ID"] = chat_id
        print(f"  discovered chat id: {chat_id}")

    print(f"Sending to chat {os.environ['TELEGRAM_CHAT_ID']} via sakthai mcp…")
    return send_via_mcp(message)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
