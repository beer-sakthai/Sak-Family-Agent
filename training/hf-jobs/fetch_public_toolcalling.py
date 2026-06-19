#!/usr/bin/env python3
"""Fetch + convert a slice of glaiveai/glaive-function-calling-v2 to our schema.

Uses the HF datasets-server /rows API (no datasets lib). Parses each row's
flat `chat` string into a single-turn {tools, messages} example with one
assistant tool call. Drops rows we can't parse cleanly.
"""

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

TOK = Path(os.path.expanduser("~/.cache/huggingface/token")).read_text().strip()
DATASET = "glaiveai/glaive-function-calling-v2"
WANT = 300  # target converted rows
PAGE = 100
NEUTRAL_SYS = (
    "You are a helpful assistant with access to tools. Call a tool when the "
    "request requires it; otherwise answer directly."
)


def fetch_page(offset):
    url = (
        f"https://datasets-server.huggingface.co/rows?dataset={DATASET}"
        f"&config=default&split=train&offset={offset}&length={PAGE}"
    )
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + TOK})
    delay = 3
    for _attempt in range(6):
        try:
            return json.load(urllib.request.urlopen(req))["rows"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"  429 rate-limited, backing off {delay}s")
                time.sleep(delay)
                delay = min(delay * 2, 30)
                continue
            raise
    raise RuntimeError("giving up after repeated 429s")


def extract_json_objects(text):
    """Yield top-level {...} JSON objects found in text via brace matching."""
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                yield text[start : i + 1]
                start = None


def parse_tools(system_text):
    tools = []
    for blob in extract_json_objects(system_text):
        try:
            fn = json.loads(blob)
        except json.JSONDecodeError:
            continue
        if "name" in fn and "parameters" in fn:
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": fn["name"],
                        "description": fn.get("description", ""),
                        "parameters": fn["parameters"],
                    },
                }
            )
    return tools


CALL_RE = re.compile(r"<functioncall>\s*(\{.*?\})\s*(?:<\|endoftext\|>|$)", re.DOTALL)


def parse_first_turn(chat):
    # first user utterance
    m_user = re.search(r"USER:\s*(.*?)(?:\n\n\nASSISTANT:|\nASSISTANT:)", chat, re.DOTALL)
    if not m_user:
        return None
    user = m_user.group(1).strip()
    # first assistant functioncall
    m_call = CALL_RE.search(chat)
    if not m_call:
        return None
    raw = m_call.group(1).strip()
    try:
        call = json.loads(raw)
    except json.JSONDecodeError:
        return None
    name = call.get("name")
    args = call.get("arguments")
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            return None
    if not name or not isinstance(args, dict):
        return None
    return user, name, args


def main():
    out_rows = []
    offset = 0
    while len(out_rows) < WANT and offset < 8000:
        for r in fetch_page(offset):
            row = r["row"]
            tools = parse_tools(row.get("system", "") or "")
            if not tools:
                continue
            parsed = parse_first_turn(row.get("chat", "") or "")
            if not parsed:
                continue
            user, name, args = parsed
            if name not in {t["function"]["name"] for t in tools}:
                continue
            out_rows.append(
                {
                    "tools": tools,
                    "messages": [
                        {"role": "system", "content": NEUTRAL_SYS},
                        {"role": "user", "content": user},
                        {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [
                                {"type": "function", "function": {"name": name, "arguments": args}}
                            ],
                        },
                    ],
                }
            )
            if len(out_rows) >= WANT:
                break
        offset += PAGE
        print(f"  offset={offset} collected={len(out_rows)}")
        time.sleep(1.5)
    out = Path("glaive_converted.jsonl")
    with out.open("w") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(out_rows)} converted public rows -> {out}")


if __name__ == "__main__":
    main()
