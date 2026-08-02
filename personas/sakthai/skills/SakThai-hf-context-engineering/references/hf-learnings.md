# HF Context Engineering Course — Deep Dive

> Research date: 2026-07-24
> Source: https://huggingface.co/learn/context-course (live research)
> Author: SakThai · Main Lead of the House & Master of Hugging Face
> License: MIT

## Summary

The Hugging Face Context Engineering Course is a free, practical course teaching
how to build context for code agents (Claude Code, Codex, OpenCode, Hermes, and
others). It covers 7 units spanning skills, MCP, plugins, subagents, hooks, and
building a minimal agent harness from scratch.

The core insight: **Code agents are only as good as the context you give them.**
Context engineering is the practice of structuring that knowledge so the agent can
find and use it.

---

## 1. Course Architecture

| Unit | Topic | Description |
|------|-------|-------------|
| 0 | Welcome & Setup | Tool installation, prerequisites, navigating the course |
| 1 | Skills | Portable knowledge files following the Agent Skills Specification |
| 2 | MCP | Model Context Protocol — wire tools and data sources to agents |
| 3 | Plugins | Bundle tools into distributable packages |
| 4 | Subagents | Orchestrate multi-agent workflows |
| 5 | Hooks | Observe, block, and automate the agent lifecycle |
| 6 | Nano Harness | Build a ~220-line agent loop from scratch |

Two certifications available: **Context Fundamentals** (course completion) and
**Context Engineering** (exam-based).

---

## 2. Unit 1: Agent Skills

Skills are the foundational building block of agent context.

### Definition

A **skill** is a self-contained package of knowledge that makes an agent good at
one specific task. Skills are:
- **Portable** across projects and agents
- **Reusable** once installed
- **Structured** in a format agents can parse (YAML frontmatter + markdown)
- **Extensible** through links to scripts and APIs

### Skills vs Long Prompts

| Aspect | Long Prompt | Skill |
|--------|-------------|-------|
| Structure | Ad-hoc prose | YAML frontmatter + sections |
| Reusability | Per-conversation | Install once, use anywhere |
| Discoverability | Manual copy-paste | Automatic load on trigger |
| Updatability | Edit every copy | Edit one file, agents see latest |

### The Agent Skills Specification

An open standard (originally by Anthropic, now adopted by 30+ code agents) for
structuring skills:

```
skills/<category>/<skill-name>/
├── SKILL.md              # Main file: frontmatter + body
├── references/           # Deep knowledge, tutorials, API refs
├── scripts/              # Runnable helper scripts
├── templates/            # File templates
└── assets/               # Images, diagrams, resources
```

The SKILL.md **must** have:
- `name` field (lowercase, hyphens)
- `description` field (≤ 1024 chars)
- Non-empty body after closing `---`
- Starts with `---` at byte 0

**Recommended** (per peer convention, not enforced by validator):
- `author`, `license`, `version`, `metadata.hermes.{tags, related_skills}`

### How Skills Work Across Agents

| Agent | Skill Support |
|-------|---------------|
| **Claude Code** | `.claude/settings.json` — `skills.[name].{urls,filePatterns,commands}` |
| **Codex** | `~/.codex/skills/` — markdown files, auto-loaded |
| **Hermes** | `~/.hermes/skills/` — `hermes skills install`, `skill_view()` |
| **OpenCode** | `.opencode/skills/` — markdown with frontmatter |

---

## 3. Unit 2: Model Context Protocol (MCP)

### The M×N Problem

Without a standard protocol, every agent needs custom integration for every data
source: N agents × M data sources = N×M custom integrations.

MCP eliminates this: write data sources as MCP servers once, and they work with
any MCP-compatible agent.

### Architecture

```
┌──────────┐     JSON-RPC     ┌──────────┐
│   Host   │ ◄──────────────► │  Server  │
│ (Agent)  │   over stdio/SSE │  (Tools) │
└──────────┘                  └──────────┘
     │                              │
     ▼                              ▼
┌──────────┐                 ┌──────────────┐
│  Client  │                 │  Capabilities │
│ (SDK)    │                 │  • Tools      │
└──────────┘                 │  • Resources  │
                             │  • Prompts    │
                             └──────────────┘
```

### Key Components

| Component | Role |
|-----------|------|
| **Host** | The application (agent, IDE, chat) that initiates connections |
| **Client** | SDK within the host that maintains the connection |
| **Server** | Exposes tools, resources, and prompts via JSON-RPC |

### Three Capability Types

1. **Tools** — Callable functions the agent can invoke (read/write files, call
   APIs, query databases). Agent-initiated.

2. **Resources** — Data exposures the agent reads (files, database rows, config
   snippets). Agent-requested.

3. **Prompts** — Pre-written templates the agent or user can trigger. User or
   agent-initiated.

### Skills vs MCP

| Aspect | Skills | MCP |
|--------|--------|-----|
| Nature | Static knowledge | Dynamic capabilities |
| Use case | "How to do X" | "Ability to do X" |
| Examples | Writing prompts, code style guides, workflows | Reading files, calling APIs, querying databases |
| Persistence | File on disk | Running server |
| Auth | None needed | Handles auth scenarios |

**Practical note:** Skills were built after MCP and have absorbed some of MCP's
functionality. But MCP remains essential for authentication scenarios and
live data access.

### Building MCP Servers with FastMCP

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.resource("config://app")
def get_config() -> str:
    """Application configuration"""
    return open("config.yaml").read()

@mcp.prompt()
def review_code(path: str) -> str:
    """Code review prompt template"""
    return f"Review the code in {path} for bugs and style issues."
```

### Gradio MCP Integration

Gradio apps can expose their interfaces as MCP tools:

```python
import gradio as gr
from gradio_mcp import gr_mcp

with gr.Blocks() as demo:
    gr.Markdown("# My MCP Tool")
    text = gr.Textbox(label="Input")
    output = gr.Textbox(label="Output")

gr_mcp(demo, server_name="my-tools")
```

This allows agents to call Gradio app functions directly via MCP.

### Configuring Agents as MCP Clients

**Claude Code:**
```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/server", "server.py"]
    }
  }
}
```

**Hermes:**
```
hermes mcp add my-server --command "uv run /path/to/server.py"
hermes mcp test my-server      # Verify connection
hermes mcp configure my-server # Toggle tool selection
```

**Codex:**
```json
{
  "mcp": {
    "servers": {
      "my-tools": {
        "type": "command",
        "command": "python",
        "args": ["-m", "my_tools_server"]
      }
    }
  }
}
```

---

## 4. Unit 4: Subagents

### What They Are

Subagents are isolated agent instances spawned by a parent agent to handle
subtasks, often in parallel. Each has its own context window, execution limits,
and tool access.

### Five Use Cases

| # | Signal | Pattern | Example |
|---|--------|---------|---------|
| 1 | **Research-heavy** — 10+ files to read | Fan-out: read → combine | "Summarize our architecture" |
| 2 | **Independent tasks** — 3+ unrelated work items | Fan-out: parallel execution | Sales metrics + feature list + customer stories |
| 3 | **Fresh perspective** — Need unbiased review | Supervisor: implement → verify | "Implement payment system, then review" |
| 4 | **Pre-commit** — Independent validation before merge | Pipeline: code → test → review | "Propose changes, test, review" |
| 5 | **Pipeline** — Sequential stages | Pipeline with isolated contexts | Design → implement → test |

### The Strong Signal: "10+ Files"

If you're thinking "I need to read 10+ files to understand this" — that's the
strongest signal to use subagents.

### Benefits

- **Parallel execution** across multiple tasks simultaneously
- **Isolated context windows** prevent overflow and cross-contamination
- **Specialized tool access** per agent
- **Failure isolation** — one crash doesn't take down the whole workflow
- **Complexity decomposition** naturally into manageable pieces

### When NOT to Use Subagents

- Sequential dependent work (B needs A's output)
- Same-file parallel edits (git conflicts)
- Small quick tasks (spawn overhead > task itself)
- 5+ specialist agents (coordination becomes chaotic)

### Patterns

| Pattern | Structure | Use For |
|---------|-----------|---------|
| **Fan-out/Fan-in** | Parent spawns N agents, collects all results | Research, independent tasks |
| **Pipeline** | A → B → C (sequential, isolated contexts) | Multi-stage workflows |
| **Supervisor** | Parent + one verifier agent | Code review, quality gate |
| **Swarm** | Many agents, no single parent | Distributed exploration |

---

## 5. Unit 6: Nano Harness

### What Is It

A ~220-line Python agent framework built for learning, not production. Shows
the entire agent loop in one readable file.

### The Agent Loop

```
System Prompt + Task → LLM → Output (Python code) → Execute → Observe → LLM → ... → Done
```

### Core Components

| Component | Purpose |
|-----------|---------|
| **System prompt** | Defines agent identity and behavior |
| **Message loop** | Accumulates conversation history |
| **Tool registry** | Dict mapping names to callable functions |
| **Output parser** | Extracts Python code from model response |
| **Sandbox** | Path confinement, command allowlist, output limits |
| **Step limit** | Prevents infinite loops (default: 50) |

### Key Features

- **Code-first agent**: Model outputs Python code, not JSON/tool calls
- **Constrained tools**: Command allowlist (ls, cat, pwd, echo, head, tail, wc, rg)
- **Sandboxed execution**: Path confinement, output size limits
- **HF Inference Providers**: Default model backend via HF router (OpenAI-compatible)

### Extending the Harness

The course covers extending with:
- **File editing tools** (read, write, patch operations)
- **HF Hub search** (model/dataset search via API)
- **Additional sandbox controls**

---

## 6. Key Takeaways

1. **Skills > long prompts.** Structured, reusable, discoverable knowledge files
   beat one-shot prompts every time.

2. **Skills + MCP = complete context.** Skills provide knowledge; MCP provides
   capabilities. Use both.

3. **Subagents scale horizontally.** The "10+ files" heuristic is the strongest
   signal for splitting work.

4. **The agent loop is simple.** Observe → Think → Act → Observe. A harness is
   ~220 lines.

5. **Context engineering is the bottleneck.** Better context beats a better model
   in most practical scenarios.

---

## 7. Source Files & Tools

| Resource | URL |
|----------|-----|
| Context Course home | https://huggingface.co/learn/context-course |
| Agent Skills Spec | https://github.com/anthropics/agentskills-spec |
| MCP Specification | https://modelcontextprotocol.io/ |
| FastMCP (Python SDK) | `pip install mcp` |
| Gradio MCP | https://huggingface.co/docs/gradio/en/mcp |
| Nano Harness code | https://huggingface.co/learn/context-course/en/unit6 |
| Inference Providers | https://huggingface.co/docs/inference-providers/en/index |
