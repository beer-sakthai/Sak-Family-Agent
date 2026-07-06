---
name: sakthai-playwright-openai-computer-use
category: dogfood
description: Record Playwright browser sessions into OpenAI Computer-Using Agent formatted
  JSONL bundles for cross-tool agent narratives, replay, and audit.
version: 1.0.0
platforms:
- linux
- macos
- windows
metadata:
  sakthai:
    tags:
    - hermes
    - dogfood
    related_skills: []
    source: hermes:playwright-openai-computer-use
---

# Playwright → OpenAI Computer-Use JSON Bundles

## Problem

Hermes (and other agent runtimes) can reason about browser state far better when UI actions exist as a clean, interoperable event stream: OpenAI's computer-use format supplies a structured JSONL schema with normalized action/anthropic-bridge entries, timestamps, and screenshot references. Playwright already records events, but manual shims are usually one-off. This skill provides a reusable export path.

## When to Use

- You need a browser run in a shareable agent narrative format
- Cross-tool handoff: Playwright trace → OpenAI computer-use JSONL
- Auditing an autonomous workflow in a spec-compatible representation
- Replaying a session without re-running the browser

## Target Schema

OpenAI computer-use expects entries like:
```jsonl
{"type":"computer_call","action":{"type":"click","x":0.5,"y":0.5},"call_id":"...","id":"...","ts":1234.567}
{"type":"anthropic_bridge","source":"playwright","heredoc":"...","ts":1234.568}
```
Fields the writer must produce consistently:
- `type`: computer_call / anthropic_bridge
- `action`: normalized with `type`, `x`, `y`, `text` as needed
- `call_id`, `id`: stable UUIDs/links across entries
- `ts`: unix float seconds
- Screenshot references via `screenshot` when applicable

## Core Capabilities

### 1. Inspect Available Schema Docs

First, check the project's `docs/` for the latest computer-use schema. If the schema is not present, ask; this pattern assumes the marketing-label schema -- plain JSONL.

```python
print(Path("/home/sakthai/sakthai-agent-v2/docs").exists())
```

### 2. Writer Skeleton for a Static Bundle

```python
import json
from pathlib import Path
from uuid import uuid4

bundle_path = Path("/home/sakthai/sakthai-agent-v2/cli/tools/misc/integrations/computer-use/playwright-2026-06-15.jsonl")

bundle_path.parent.mkdir(parents=True, exist_ok=True)
entries = []
entries.append({
  "type": "computer_call",
  "action": {"type": "click", "x": 0.5, "y": 0.5},
  "call_id": str(uuid4()),
  "id": str(uuid4()),
  "ts": 1234.567
})
entries.append({
  "type": "anthropic_bridge",
  "source": "playwright",
  "heredoc": "...",
  "ts": 1234.568
})
bundle_path.write_text("\n".join(json.dumps(e) for e in entries) + "\n")
print(bundle_path, bundle_path.stat().st_size)
```

### 3. Validate Output

```bash
wc -l /home/sakthai/sakthai-agent-v2/cli/tools/misc/integrations/computer-use/playwright-2026-06-15.jsonl
```

Non-empty output means the file is ready.

## Workflow Integration

- Apply only to green Playwright QA screenshots
- Preserve compaction and fallback semantics
- Use with the `cli-smoke-retry` MCP server and `playwright` CLI tool
- Trigger on cron jobs at 00:06 (install: 00:07)
- If delivery fails after 3 retries, print a confirmation to stdout instead

## Anti-Patterns

- Do not write large JSONL bundles in the project root -- always keep them inside the computer-use bundle directory shown above
- Do not drop stable IDs mid-session; continuity between entries matters for replay
- Do not bundle secrets in the JSONL; screenshots may be shared externally

## Verification

1. Confirm the directory exists
2. Write a one-entry bundle with a computer_call + anthropic_bridge
3. Validate with `wc -l`
4. Treat success as standard output of the path + size, failure as a clear error before any delivery retry logic

## Reference

This capability complements:
- `playwright-session-persistence` for auth state
- `playwright-network-reliability` for deterministic录制
