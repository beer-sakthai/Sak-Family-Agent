---
name: SakThai-hf-context-engineering
author: SakThai
license: MIT
description: "Context engineering for code agents — skills, MCP, hooks."
version: 1.0.0
tags: [ContextEngineering, Agents, MCP, Plugins, Subagents, Hooks]
---

# Context Engineering for Code Agents

Based on the [HF Context Course](https://huggingface.co/learn/context-course). Covers building skills, MCP tools, plugins, subagents, and hooks for code agents like Claude Code, Codex, and OpenCode.

## When to Use

- User wants to "structure agent knowledge" or "build agent context"
- User asks about Model Context Protocol (MCP)
- User needs to create skills, plugins, or tool definitions
- User wants to orchestrate multi-agent workflows with subagents
- User needs to observe/monitor agent lifecycle with hooks
- User wants to understand context injection patterns and strategies

## Prerequisites

- A code agent installed (Claude Code, Codex, OpenCode, or Hermes)
- Python 3.10+
- For MCP: an MCP-compatible client (or the `mcp` CLI)
- `pip install mcp` for building MCP servers

## Course Units Reference

| Unit | Topic | What You Learn |
|------|-------|----------------|
| 1 | Skills | Portable knowledge files agents load automatically |
| 2 | MCP | Model Context Protocol — wire tools and APIs to agents |
| 3 | Plugins | Bundle tools into distributable packages |
| 4 | Subagents | Spawn specialized agents for parallel work |
| 5 | Hooks | Observe, block, and automate the agent lifecycle |
| 6 | Nano Harness | Build a minimal agent loop from scratch |

## Procedures

### 1. Skills

Create markdown files with YAML frontmatter. Agents load them as context:

```yaml
---
name: my-skill
description: "Does XYZ."
version: 1.0.0
tags: [tool, reference]
---
# Skill Content
Useful reference and procedures here.
```

#### Skill Naming Conventions
- Lowercase with hyphens: `my-skill-name`
- Keep descriptions tight (overly broad → loaded too often)
- One skill per concept — don't combine unrelated topics

#### Skill Loading Strategies
- **Auto-loading**: Some agents load matching skills based on task detection
- **Explicit loading**: `skill_view(name="my-skill")` in Hermes
- **Context injection**: Skills are injected into agent context as system prompts

### 2. MCP (Model Context Protocol) — Complete Server Setup

#### Basic MCP Server
```python
# mcp_server.py
from mcp.server import Server
import httpx

server = Server("my-tools")

@server.tool()
def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}!"

# Run the server
if __name__ == "__main__":
    server.run()
```

#### MCP Server with HTTP Calls
```python
# mcp_server_advanced.py
from mcp.server import Server
import httpx

server = Server("web-tools")

@server.tool()
async def fetch_url(url: str) -> str:
    """Fetch a URL and return its content."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text[:5000]  # Truncate long responses

@server.tool()
def search(query: str, max_results: int = 5) -> list:
    """Search for information."""
    # Implement your search logic
    return [{"title": "Example", "url": "https://example.com"}]

@server.tool()
def calculate(expression: str) -> float:
    """Evaluate a mathematical expression safely."""
    import ast
    import operator
    
    safe_ops = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow,
    }
    
    def eval_expr(node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            return safe_ops[type(node.op)](eval_expr(node.left), eval_expr(node.right))
        raise ValueError("Unsafe expression")
    
    return eval_expr(ast.parse(expression, mode='eval').body)

if __name__ == "__main__":
    server.run()
```

#### MCP Server Configuration
```json
{
  "mcp_servers": {
    "my-tools": {
      "command": "python",
      "args": ["mcp_server.py"],
      "env": {
        "API_KEY": "${API_KEY}"
      }
    }
  }
}
```

#### STDIO vs SSE Transport
```python
# STDIO transport (default) — for local use:
# python mcp_server.py

# SSE transport — for remote/networked use:
from mcp.server import Server
server = Server("remote-tools")

# Add tools...

# Run with SSE
import asyncio
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route

async def handle_sse(request):
    transport = SseServerTransport("/messages/")
    async with transport.connect_sse(request.scope, request.receive, request._send) as session:
        await server.run(session, server.create_initialization_options())

app = Starlette(routes=[
    Route("/sse", endpoint=handle_sse),
])
```

#### Tool Patterns

| Pattern | Description | Use Case |
|---------|-------------|----------|
| **Simple Function** | Basic tool wrapping a function | Stateless operations, calculations |
| **Stateful Tool** | Tool that maintains state | Caching, session management |
| **Async Tool** | Non-blocking I/O tools | API calls, file operations |
| **Composite Tool** | Combines multiple sub-tools | Complex multi-step operations |
| **Validation Tool** | Validates input/output | Safety guardrails |
| **Search Tool** | Retrieves information | RAG, knowledge lookups |

#### Tool Design Best Practices
```python
from mcp.server import Server
from typing import Optional

server = Server("best-practices")

# ✅ GOOD: Clear name, docstring, typed parameters
@server.tool()
def get_weather(city: str, units: Optional[str] = "celsius") -> dict:
    """Get current weather for a city.
    
    Args:
        city: City name (e.g., "London", "Tokyo")
        units: Temperature units — "celsius" or "fahrenheit"
    """
    return {"city": city, "temperature": 22, "conditions": "sunny"}

# ❌ BAD: Vague name, no docstring, untyped
@server.tool()
def do(x):  # What does this do? What is x?
    return x

# ✅ GOOD: Return structured data with error handling
@server.tool()
def safe_divide(a: float, b: float) -> dict:
    """Safely divide two numbers."""
    if b == 0:
        return {"error": "Division by zero", "result": None}
    return {"error": None, "result": a / b}
```

### 3. Subagents

Delegate focused work to child agents with isolated context and tools.

```python
# Hermes subagent pattern
from hermes import Agent

# Delegate a research task
research_agent = Agent(
    system_prompt="You are a research specialist. Find relevant information.",
    tools=["web_search", "read_file"],
)

# Execute in parallel with limited scope
result = research_agent.run(
    "Research the latest developments in MCP protocol",
    max_iterations=5,
)
```

#### Subagent Communication Patterns
```
Parent Agent
├── Subagent A (Research) — gathers information
├── Subagent B (Code) — writes implementation
└── Subagent C (Verification) — tests results
    ↓
Parent Agent compiles final result
```

#### Subagent Memory and Context
- Subagents are stateless unless you explicitly pass context
- Pass relevant context as `system_prompt` or initial messages
- Memory can be shared via files or database

### 4. Hooks

Attach lifecycle scripts at key execution points to enforce guardrails, log errors, or verify outcomes.

#### Hook Lifecycle
```
Step Start → Pre-Execution Hook → Action → Post-Execution Hook → Step End
```

#### Pre-Execution Hook Pattern
```bash
#!/bin/bash
# pre-exec-guard.sh — Runs before every agent action
# Purpose: Prevent dangerous operations

# Block destructive commands
if [[ "$ACTION_TYPE" == "file_write" ]]; then
    TARGET="$ACTION_PATH"
    if [[ "$TARGET" == /etc/* || "$TARGET" == /sys/* ]]; then
        echo "BLOCKED: Writing to system path $TARGET"
        exit 1  # Blocks the action
    fi
fi

# Verify resource limits
if [[ "$ACTION_TYPE" == "command" ]]; then
    echo "Executing: $ACTION_COMMAND" >> /var/log/agent-actions.log
fi
```

#### Post-Execution Hook Pattern
```python
#!/usr/bin/env python3
"""post-write-verify.py — Verifies file writes are valid."""

import sys
import json

def verify_file_write(event):
    """Check that written files pass validation."""
    path = event.get("output_path")
    if path and path.endswith(".py"):
        try:
            compile(open(path).read(), path, 'exec')
            print(f"✅ Valid Python: {path}")
        except SyntaxError as e:
            print(f"❌ Invalid Python: {path} — {e}")
            return False
    return True

if __name__ == "__main__":
    event = json.loads(sys.stdin.read())
    if not verify_file_write(event):
        sys.exit(1)  # Signal failure
```

#### Hook Configuration
```yaml
hooks:
  pre_execution:
    - path: hooks/pre-exec-guard.sh
      blocking: true  # Block action if hook fails
  post_execution:
    - path: hooks/post-write-verify.py
      blocking: false  # Log only, don't block
  on_error:
    - path: hooks/error-capture.sh
      blocking: false
```

### 5. Agent Context Strategies

| Strategy | Description | When to Use |
|----------|-------------|-------------|
| **Skill Injection** | Load relevant skills as context | Task-specific knowledge needed |
| **Tool Provisioning** | Give agent precisely scoped tools | Focused task execution |
| **Memory Passing** | Pass structured context between steps | Multi-step workflows |
| **System Prompt Engineering** | Set clear boundaries and expectations | Guiding agent behavior |
| **Hierarchical Agents** | Manager + specialist subagents | Complex multi-domain tasks |
| **Context Window Management** | Prioritize and trim context | Long-running sessions |
| **Feedback Loops** | Iterative refinement via hooks | Quality-critical tasks |

#### Context Budget Management
```yaml
# Strategy for managing context window
context_strategy:
  essentials:  # Always included
    - system_prompt
    - task_definition
    - critical_skills
  
  conditional:  # Loaded on demand
    - relevant_skills
    - tool_descriptions
    
  ephemeral:  # Can be trimmed
    - conversation_history
    - intermediate_results
```

### 6. Nano Harness

For understanding how an agent loop works under the hood, see `references/nano-harness.md` — a minimal Observed → Think → Act → Observe loop in ~80 lines of Python.

### Researching HF Documentation
HF docs are SvelteKit SPAs — the rendered HTML is an empty shell. Fetch raw markdown at predictable URLs instead. See `references/hf-docs-research.md` for the pattern and examples.

## Sak Family Application

The 6 concepts map to the Sak Family Agent architecture. All 6 are now built:

| Concept | Sak Family Use | Status | Artifacts |
|---------|----------------|--------|-----------|
| **Skills** | Shared `beer-sakthai/sakthai-skills` repo — all 3 siblings sync via GitHub | Live | Repos: sakthai-skills, saksee-skills, saksit-skills |
| **MCP** | Composio MCP (12+ apps) + n8n (installed) + Linear (needs OAuth) | Live | `config.yaml` `mcp_servers:` section |
| **Subagents** | Formal Research → Build → Verify pipeline in `sak-family-handoff` v2.0.0 | Live | `sak-family-handoff/SKILL.md` |
| **Hooks** | Pre/post guardrails: auto-chown, verify integrity, log error patterns | Live | `hooks/pre-exec-guard.sh`, `hooks/error-capture.sh`, `scripts/post-write-verify.py` |
| **Plugins** | Hermes plugin system explored; 3 types: general, memory, context engine | Scoped | `hermes plugins` interactive UI |
| **Nano Harness** | Minimal agent loop (~80 lines Python) documented | Built | `references/nano-harness.md` |

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| MCP server won't connect | Path/env issues | Check `command` and `args` in config; verify server runs standalone |
| Skill not loading | Wrong frontmatter | Ensure valid YAML with `name:`, `description:` |
| Subagent returns no result | Context not passed | Pass relevant info via `system_prompt` or initial message |
| Hook blocks everything | Hook logic too broad | Add specific conditions; set `blocking: false` for logging hooks |
| MCP tool not found | Server not started | Ensure server is listed in `mcp_servers` and process is running |
| Context too large | Too many skills loaded | Use conditional loading, trim irrelevant history |
| Agent loops forever | Missing stopping condition | Set `max_iterations` or add a "task_complete" check in hooks |

## Pitfalls

- Skills with overly broad descriptions get loaded often — keep descriptions tight.
- MCP servers must be running for the agent to connect; configure in agent settings.
- Subagents are stateless unless you pass memory explicitly.
- Hooks can slow down the agent if they make network calls on every step.
- Tool descriptions are critical — agents choose tools based on descriptions, not names.
- MCP STDIO transport is simple but doesn't scale across machines — use SSE for remote.
- Hook failure handling: decide if a failed hook should block the action or just log.
- Context window is finite — prioritize essential information over exhaustive context.
- Different agents implement MCP differently — test your server with each agent.

## Verification

Load a skill via the agent and confirm the content is accessible in context:
```bash
skill_view(name="my-skill")
```

Test MCP server:
```bash
python mcp_server.py
# Server should start and wait for connections
```

Test hooks:
```bash
# Simulate a hook event
echo '{"action_type": "file_write", "output_path": "/tmp/test.py"}' | python hooks/post-write-verify.py
```
