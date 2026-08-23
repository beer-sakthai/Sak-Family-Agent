---
name: SakSee-antigravity
description: "Google Antigravity CLI \u2014 AI coding agent from Google. Build, debug, and ship\
  \ from your terminal. Describe what you need, and Antigravity handles the rest.\
  \ Similar to Claude Code / Codex CLI."
---

# Google Antigravity CLI (`agy`)

An AI-powered coding agent CLI from Google. Installs as the `agy` binary.

## Install

```bash
curl -fsSL https://antigravity.google/cli/install.sh | bash
```

Installs to `~/.local/bin/agy`. Also supports Windows via PowerShell.

## Usage

```bash
agy --print "your prompt here"          # Single-shot, non-interactive
agy --prompt-interactive "initial task" # Start interactive session
agy --continue                          # Resume most recent conversation
agy --conversation <id>                 # Resume a specific conversation
agy --new-project                       # Start in a new project context
agy --project <id>                      # Use an existing project
agy --model <model>                     # Select model
agy --sandbox                           # Run in sandbox (terminal restrictions)
agy --dangerously-skip-permissions      # Auto-approve all tool requests
agy --add-dir /path                     # Add directory to workspace
agy --log-file /path                    # Override log file path
agy --print-timeout 10m                 # Custom print timeout (default 5m)
agy models                              # List available models
agy plugin install <name>               # Manage plugins
agy install                             # Configure shell & PATH
agy update                              # Update CLI
agy changelog                           # Show release notes
```

Short aliases:
- `-p` → `--print`
- `-i` → `--prompt-interactive`
- `-c` → `--continue`

## Authentication

**Required before first use.** The CLI opens a browser for Google OAuth sign-in.
Once authenticated, a token is cached locally. On headless servers (no browser),
the user must run the CLI interactively on their local machine first to auth,
or pass a token directly if supported.

```bash
agy --print "hello"  # Triggers auth flow if not signed in
```

## Key Features

- **Print mode** (`--print`): single prompt, non-interactive, returns response — ideal for scripted use
- **Interactive mode** (`--prompt-interactive` or no arg): live conversation with the agent
- **Conversation persistence**: resume previous sessions by ID
- **Projects**: organize work into named projects with workspace context
- **Plugins**: extend capabilities via plugin system
- **Sandbox mode**: runs with terminal restrictions for safety
- **Multi-model**: select different AI models per session

## Pitfalls

- The binary is ~172MB (large download/install).
- Requires Google authentication via browser — cannot auth on headless servers without user help.
- **`--print` has a default 5-minute timeout.**
- On first run without auth, `agy models` and `agy --print` both fail with auth errors.
- **The CLI binary (`agy`) does NOT accept `GEMINI_API_KEY` env var.** Only the Python SDK does. Setting `GEMINI_API_KEY` and running `agy --print` still fails with auth errors.
- **`--prompt-interactive` / `-i` requires a real TTY.** On headless servers it fails with `bubbletea: could not open TTY` because the CLI uses the Go TUI library `bubbletea` for interactive mode — no workaround on a server without a PTY.
- **`--dangerously-skip-permissions` does not bypass auth.** It only skips individual tool permission prompts once authenticated. A non-authenticated `--print` request still hangs until timeout.

## Headless Server Auth Workarounds

When running on a server without a browser, the CLI binary (`agy`) cannot authenticate because it requires Google OAuth via browser. Use the **Python SDK** instead — it accepts `GEMINI_API_KEY` env var.

## Python SDK (headless / no browser)

**Install:** `uv pip install google-antigravity`

The module imports as `google.antigravity` (dot-delimited, not underscore).

**Basic usage with GEMINI_API_KEY:**

```python
import asyncio
import os
os.environ["GEMINI_API_KEY"] = "your-key-here"

from google.antigravity.agent import Agent
from google.antigravity.connections.local.local_connection_config import LocalAgentConfig

async def main():
    async with Agent(config=LocalAgentConfig()) as agent:
        result = await agent.chat("your prompt here")
        text = await result.text()
        print(text)

asyncio.run(main())
```

**One-shot CLI shortcut** (for use inside `execute_code` or `terminal`):

```bash
cd /project/path && GEMINI_API_KEY='key' /opt/data/.venv/bin/python3 -c '
import asyncio, os
os.environ["GEMINI_API_KEY"] = "..."
from google.antigravity.agent import Agent
from google.antigravity.connections.local.local_connection_config import LocalAgentConfig

async def main():
    async with Agent(config=LocalAgentConfig()) as agent:
        t = await (await agent.chat("prompt")).text()
        print(t)

asyncio.run(main())
'
```

**Key API facts:**
| Fact | Detail |
|------|--------|
| Context manager | `async with Agent(config=...) as agent:` — REQUIRED |
| Chat call | `await agent.chat("prompt")` → returns `ChatResponse` |
| Get text | `await result.text()` — all outputs are async |
| Chain-of-thought | `result.thoughts` — async generator |
| Auth | `GEMINI_API_KEY` env var (NOT the CLI `agy` binary) |
| Import path | `google.antigravity` — dot-delimited, not underscore |
| Venv | `/opt/data/.venv/` — source activate or use absolute path |

## Related Components

| Component | Link |
|-----------|------|
| Python SDK | `pip install google-antigravity` → import as `google.antigravity` |
| Antigravity Hub | Download from `antigravity.google/downloads` (DMG/EXE/tar.gz) |
| YouTube | `@GoogleAntigravity` |
