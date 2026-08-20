---
name: SakThai-hf-smolagents
author: SakThai
license: MIT
description: >-
  Deep-dive skill for Hugging Face's smolagents library (v1.26.0+). Covers
  CodeAgent, ToolCallingAgent, multi-agent orchestration, agent memory,
  Human-in-the-Loop, async integration, OpenTelemetry telemetry, secure code
  execution, tool creation patterns, and Agentic RAG.
version: 2.0.0
domain: mlops
triggers:
  - smolagents
  - code agent
  - tool calling agent
  - hf agent framework
  - huggingface agent
  - multi-agent
  - agentic rag
  - managed agent
  - agent memory
  - agent telemetry
---

# smolagents — Hugging Face Agent Framework (Deep Dive v2)

## Overview

`smolagents` is an open-source Python library (~thousand lines of core agent logic) for building and running AI agents. It supports **CodeAgents** (actions written in Python code) and **ToolCallingAgents** (JSON/text tool-calling). Both agent types share a common multi-step reasoning loop (ReAct-style), but differ in how they express actions.

**Docs:** https://huggingface.co/docs/smolagents/en/index  
**GitHub:** https://github.com/huggingface/smolagents  
**Version at time of writing:** v1.26.0

## Key Features

- **Simplicity** — agent logic fits in ~1K lines; minimal abstractions
- **CodeAgent** — writes actions as Python code (loops, conditionals, nesting) for composability
- **ToolCallingAgent** — traditional JSON/text tool-calling paradigm
- **Hub integrations** — share/load agents and tools as Gradio Spaces on Hugging Face Hub
- **Model-agnostic** — HF Inference, OpenAI, Anthropic via LiteLLM, local via Transformers/Ollama
- **Modality-agnostic** — handles text, vision, video, audio inputs
- **Tool-agnostic** — use tools from MCP servers, LangChain, or Hub Spaces
- **CLI tools** — `smolagent` and `webagent` commands for quick use
- **Secure code execution** — sandbox via Modal, Blaxel, E2B, or Docker
- **OpenTelemetry** — built-in telemetry via `SmolagentsInstrumentor` for run inspection
- **Step callbacks** — intercept agent steps (planning, tool calls, final answers) for custom behavior

## Installation

```bash
pip install 'smolagents[toolkit]'    # Includes default tools like web search
pip install 'smolagents[litellm]'     # For OpenAI/Anthropic model support
pip install 'smolagents[transformers]' # For local model support
pip install 'smolagents[telemetry]'    # For OpenTelemetry instrumentation
pip install 'smolagents[e2b]'         # For E2B sandboxed execution
pip install 'smolagents[blaxel]'      # For Blaxel sandboxed execution
```

## Agent Architecture

### CodeAgent vs ToolCallingAgent

| Aspect | CodeAgent | ToolCallingAgent |
|--------|-----------|-----------------|
| Action format | Python code execution | JSON tool calls |
| Composability | Loops, conditionals, nesting | Sequential tool calls |
| When to use | Tasks needing logic, multi-step reasoning | Simple tool pipelining, web browsing |
| `max_steps` default | 6 | 6 |
| Code sandbox available | Yes (executor_type) | No |

### Common init parameters

```python
from smolagents import CodeAgent, ToolCallingAgent

agent = CodeAgent(
    tools=[],                          # List of tools
    model=model,                       # Model backend
    max_steps=10,                      # Max reasoning steps
    planning_interval=5,               # Re-plan every N steps
    verbosity_level=1,                 # 0=silent, 1=normal, 2=verbose
    additional_authorized_imports=[],  # Extra Python imports for CodeAgent
    executor_type=None,                # Sandbox: "blaxel", "e2b", "modal", "docker"
    step_callbacks={},                 # Dict of {StepType: callable}
    managed_agents=[],                 # List of sub-agents
)
```

## Multi-Agent Orchestration

smolagents supports **hierarchical multi-agent systems** where a manager agent delegates to specialized sub-agents via `managed_agents`.

### Pattern

```python
from smolagents import CodeAgent, ToolCallingAgent, InferenceClientModel

model = InferenceClientModel(model_id="Qwen/Qwen3-Next-80B-A3B-Thinking")

# Create a sub-agent (must have name + description)
web_agent = ToolCallingAgent(
    tools=[WebSearchTool(), visit_webpage],
    model=model,
    max_steps=10,
    name="web_search_agent",
    description="Runs web searches for you.",
)

# Manager agent owns the planning
manager_agent = CodeAgent(
    tools=[],
    model=model,
    managed_agents=[web_agent],  # Pass sub-agents here
    additional_authorized_imports=["time", "numpy", "pandas"],
)

result = manager_agent.run("Your complex multi-step task")
```

**Rules:**
- Sub-agents MUST have `name` and `description` attributes — these are how the manager knows what each agent does
- Sub-agents are listed in the manager's system prompt, the manager can call them like tools
- `ToolCallingAgent` is preferred for sub-agents doing focused tasks (web search, data fetch)
- `CodeAgent` works better as the manager (planning, reasoning, code)
- Multi-agent systems can nest arbitrarily deep

## Agent Memory Management

Agent memory stores all steps taken during a run. You can inspect and reuse it.

### Inspecting memory

```python
print(f"Memory contains {len(agent.memory.steps)} steps:")
for i, step in enumerate(agent.memory.steps):
    step_type = type(step).__name__
    print(f"  {i+1}. {step_type}")
```

### Resuming execution with preserved memory

```python
# First run
agent.run(task, reset=True)   # Fresh memory

# Resume with preserved memory
agent.run(task, reset=False)  # Continues from where it left off
```

**Step types:** `PlanningStep`, `ToolCallStep`, `FinalAnswerStep`, `ActionStep`

## Tool Creation Patterns

### Method 1: @tool decorator (simple)

```python
from smolagents import tool
import requests
from markdownify import markdownify

@tool
def visit_webpage(url: str) -> str:
    """Visits a webpage and returns its content as markdown.
    Args:
        url: The URL of the webpage to visit.
    Returns:
        The webpage content as markdown string.
    """
    response = requests.get(url)
    response.raise_for_status()
    return markdownify(response.text).strip()
```

### Method 2: Tool subclass (advanced)

```python
from smolagents import Tool
from huggingface_hub import list_models

class HFModelDownloadsTool(Tool):
    name = "model_download_counter"
    description = "Returns the most downloaded model for a given task on the Hub."
    inputs = {
        "task": {
            "type": "string",
            "description": "Task category (text-classification, depth-estimation, etc.)"
        }
    }
    output_type = "string"

    def forward(self, task: str):
        model = next(iter(list_models(filter=task, sort="downloads", direction=-1)))
        return model.id
```

### Sharing tools to the Hub

```python
tool.push_to_hub("{username}/my-tool", token="<token>")
```

**Rules for Hub sharing:**
- All imports must be defined inside the tool's methods (not at module top-level)
- `__init__` can only take `self` as argument (no custom init params)
- Use class attributes for hard-coded values

## Human-in-the-Loop (Plan Customization)

Use **step callbacks** to let a human review and modify the agent's plan mid-execution.

```python
from smolagents import PlanningStep

def interrupt_after_plan(step, agent, task, **kwargs):
    """Callback that pauses after planning for human review."""
    print("\n=== AGENT PLAN ===")
    for i, s in enumerate(step.plan, 1):
        print(f"{i}. {s}")
    print("=================")
    choice = input("Choose: 1=Approve, 2=Modify, 3=Cancel: ")
    if choice == "2":
        new_plan = input("Enter new plan (one step per line, '---' to end):\n")
        step.plan = [f"{i+1}. {line}" for i, line in enumerate(new_plan.split("---"))]
    elif choice == "3":
        raise InterruptedError("Execution cancelled by user.")

agent = CodeAgent(
    model=model,
    tools=[DuckDuckGoSearchTool()],
    planning_interval=5,
    step_callbacks={PlanningStep: interrupt_after_plan},
    max_steps=10,
)
```

**Key points:**
- `step_callbacks` is a dict keyed by step type classes (e.g., `PlanningStep`, `ToolCallStep`, `FinalAnswerStep`)
- Callback signature: `callback(step, agent, task, **kwargs)`
- Use `reset=False` on subsequent `agent.run()` calls to preserve memory after interruption

## Async Integration (Starlette)

Blocking `agent.run()` in async web apps blocks the event loop. Use `anyio.to_thread.run_sync`:

```python
import anyio.to_thread
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from smolagents import CodeAgent, InferenceClientModel

agent = CodeAgent(
    model=InferenceClientModel(model_id="Qwen/Qwen3-Next-80B-A3B-Thinking"),
    tools=[],
)

async def run_agent(request):
    data = await request.json()
    task = data.get("task", "")
    # Run agent in background thread to avoid blocking event loop
    result = await anyio.to_thread.run_sync(agent.run, task)
    return JSONResponse({"result": str(result)})

app = Starlette(routes=[Route("/run-agent", run_agent, methods=["POST"])])
```

## Telemetry & Run Inspection (OpenTelemetry)

smolagents uses OpenTelemetry for run instrumentation:

```python
# 1. Set up collector (e.g., Arize Phoenix)
# Terminal: python -m phoenix.server.main serve

# 2. Instrument
from phoenix.otel import register
from openinference.instrumentation.smolagents import SmolagentsInstrumentor

register()
SmolagentsInstrumentor().instrument()

# 3. Run agents normally — all steps logged to the platform
from smolagents import CodeAgent, InferenceClientModel
agent = CodeAgent(model=InferenceClientModel(), tools=[])
agent.run("Your task")  # Automatically traced
```

**Why telemetry matters for agents:**
- Agent runs are non-deterministic and hard to debug
- Console logs fill quickly with "LLM dumb" errors that auto-correct
- Telemetry provides structured logs for post-hoc inspection
- Compatible with any OpenTelemetry backend (Phoenix, Grafana, Datadog, etc.)

## Agentic RAG

Agentic RAG transforms RAG from a rigid pipeline into an interactive reasoning process:

```python
from smolagents import CodeAgent, ToolCallingAgent, InferenceClientModel

# Create a knowledge retrieval tool
@tool
def query_knowledge_base(query: str) -> str:
    """Search the knowledge base for relevant documents.
    Args:
        query: The search query.
    Returns:
        Relevant document excerpts.
    """
    # Your vector store / retrieval logic here
    ...

agent = CodeAgent(
    model=InferenceClientModel(),
    tools=[query_knowledge_base],
    max_steps=10,
)
result = agent.run("Answer based on our documentation")
```

**Benefits over traditional RAG:**
- Formulates optimized retrieval queries (HyDE-like)
- Performs multiple retrieval iterations
- Reasons over and synthesizes content from multiple sources
- Self-critiques and refines queries based on results
- Can cite sources from retrieved content

## Secure Code Execution

CodeAgent executes arbitrary Python. For production, sandbox execution:

| Provider | Extras | Setup | Latency | Multi-agent support |
|----------|--------|-------|---------|-------------------|
| **Blaxel** | `smolagents[blaxel]` | blaxel.ai account, API key | <25ms cold start | No |
| **E2B** | `smolagents[e2b]` | e2b.dev account, API key | ~500ms cold start | No |
| **Modal** | `smolagents` | modal.com account | ~2s cold start | No |
| **Docker** | Docker installed | Local Docker daemon | Variable | No |

```python
# Sandboxed execution (Blaxel example)
with CodeAgent(
    model=InferenceClientModel(),
    tools=[],
    executor_type="blaxel",
) as agent:
    agent.run("Can you give me the 100th Fibonacci number?")
    # Sandbox cleaned up on context manager exit
```

## CLI Reference

```bash
smolagent [prompt] [options]
  --model-type       InferenceClientModel | OpenAIModel | LiteLLMModel | TransformersModel
  --action-type      code | tool_calling
  --model-id         Model ID to use
  --tools            Space-separated list of tool names
  --provider         Inference provider
  --api-base         Custom API base URL
  --api-key          API key

webagent --url <url> --task <description>
```

## Resources

- **Docs:** https://huggingface.co/docs/smolagents/en/index
- **GitHub:** https://github.com/huggingface/smolagents
- **Multi-agent example:** https://huggingface.co/docs/smolagents/en/examples/multiagents
- **Agentic RAG:** https://huggingface.co/docs/smolagents/en/examples/rag
- **Memory management:** https://huggingface.co/docs/smolagents/en/tutorials/memory
- **Tools guide:** https://huggingface.co/docs/smolagents/en/tutorials/tools
- **Human-in-the-Loop:** https://huggingface.co/docs/smolagents/en/examples/plan_customization
- **Async agents:** https://huggingface.co/docs/smolagents/en/examples/async_agent
- **Telemetry:** https://huggingface.co/docs/smolagents/en/tutorials/inspect_runs
- **Secure code execution:** https://huggingface.co/docs/smolagents/en/tutorials/secure_code_execution
- **Reference (agents API):** https://huggingface.co/docs/smolagents/en/reference/agents
