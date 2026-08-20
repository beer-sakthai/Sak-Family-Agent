---
name: SakSee-antigravity-cli-usage
description: Use the Google Antigravity CLI (agy) for AI-powered coding assistance, including installation,
  authentication, and common usage patterns.
...
---

# Google Antigravity CLI Usage

Use the Google Antigravity CLI (agy) for AI-powered coding assistance, including installation, authentication, and common usage patterns.

## When to Use

- When you need AI-powered coding assistance from the command line
- When working with the Google Antigravity CLI (`agy`) binary
- When you need to integrate AI coding assistance into automated workflows
- When working in environments where browser-based tools are not available

## Prerequisites

- Basic understanding of command-line interfaces
- Access to the Google Antigravity CLI binary (`agy`)
- Google account for authentication (for interactive use)
- GEMINI_API_KEY environment variable (for headless/Python SDK use)

## Quick Reference

| Command | Action |
|---------|--------|
| `agy --print "prompt"` | Single-shot, non-interactive AI response |
| `agy --prompt-interactive "task"` | Start interactive session |
| `uv pip install google-antigravity` | Install Python SDK |
| `GEMINI_API_KEY='key' python script.py` | Use Python SDK with API key |

## Procedure

### 1. Installation

Install the Google Antigravity CLI:

```bash
# Install the CLI binary
curl -fsSL https://antigravity.google/cli/install.sh | bash

# Verify installation
agy --version
```

### 2. Authentication

Authenticate with Google (required for first use):

```bash
# Triggers auth flow if not signed in
agy --print "hello"

# For headless environments, use the Python SDK instead
```

### 3. Basic Usage

Use the CLI for various tasks:

```bash
# Single-shot, non-interactive mode
agy --print "Explain how to use React hooks"

# Start interactive session
agy --prompt-interactive "Help me debug this React component"

# Resume most recent conversation
agy --continue

# List available models
agy models

# Update the CLI
agy update
```

### 4. Using the Python SDK (Headless)

For headless environments or programmatic use:

```bash
# Install the Python SDK
uv pip install google-antigravity

# Use with GEMINI_API_KEY
cd /project/path && GEMINI_API_KEY='your-key-here' python3 -c '
import asyncio, os
os.environ["GEMINI_API_KEY"] = "your-key-here"
from google.antigravity.agent import Agent
from google.antigravity.connections.local.local_connection_config import LocalAgentConfig

async def main():
    async with Agent(config=LocalAgentConfig()) as agent:
        result = await agent.chat("your prompt here")
        text = await result.text()
        print(text)

asyncio.run(main())
'
```

### 5. Advanced Usage

Use advanced features of the CLI:

```bash
# Select a specific model
agy --model gemini-1.5-pro --print "Explain quantum computing"

# Run in sandbox mode (terminal restrictions)
agy --sandbox --print "List directory contents"

# Skip permissions (only works after authentication)
agy --dangerously-skip-permissions --print "Modify system files"

# Add directory to workspace
agy --add-dir /path/to/project --print "Analyze this codebase"

# Set custom timeout
agy --print-timeout 10m --print "Complex code analysis"
```

## Pitfalls

- **Large download size**: The binary is ~172MB, which may be problematic on slow connections
- **Authentication requirements**: Interactive mode requires Google OAuth via browser, which doesn't work on headless servers
- **Timeout limitations**: `--print` has a default 5-minute timeout
- **Environment variables**: The CLI binary (`agy`) does NOT accept `GEMINI_API_KEY` env var - only the Python SDK does
- **TTY requirements**: `--prompt-interactive` requires a real TTY and fails on headless servers
- **Permission skipping**: `--dangerously-skip-permissions` does not bypass auth, only skips tool permission prompts
- **Headless authentication**: In headless environments, CLI authentication often fails with "authentication failed or timed out" error. Use the Python SDK with GEMINI_API_KEY instead.

## Verification

To verify that you've successfully used the Antigravity CLI:

1. Confirm the CLI is installed and accessible: `agy --version`
2. Verify authentication is working: `agy --print "hello"`
3. Test basic functionality: `agy --print "Explain a simple concept"`
4. For headless use, verify the Python SDK works with your API key
5. Check that advanced features work as expected for your use case

See `references/antigravity-cli-examples.md` for specific examples and use cases.
