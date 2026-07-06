---
title: "Hugging Face smolagents"
description: "Lightweight HF agent framework — CodeAgent, ToolCallingAgent, model/tool integrations, secure execution, and CLI patterns."
category: "mlops"
---

# Hugging Face smolagents

`smolagents` is an open-source Python library from Hugging Face for building and running AI agents in a few lines of code. Core agent logic fits in ~1,000 lines of code, with minimal abstractions over raw execution.

## Installation

```bash
pip install "smolagents[toolkit]"   # default tools incl. web_search
# Extras: [modal], [e2b], [blaxel], [docker], [gradio], [litellm], [transformers]
```

## Agent Types

| Class | Action format | When to use |
|-------|---------------|-------------|
| `CodeAgent` | Python code snippets (default) | Composability, loops, conditionals; ~30% fewer steps vs JSON per research |
| `ToolCallingAgent` | JSON/text tool calls | Standard JSON tool-calling paradigm |

Both inherit from `MultiStepAgent` and require `model` + `tools`.

```python
from smolagents import CodeAgent, WebSearchTool, InferenceClientModel

model = InferenceClientModel()                       # HF Inference Providers (default)
agent = CodeAgent(tools=[WebSearchTool()], model=model)
result = agent.run("How many seconds would it take for a leopard at full speed to run through Pont des Arts?")
```

## Model Integrations (all LLM-agnostic)

- `InferenceClientModel` — any model on HF Inference Providers; pass `model_id="deepseek-ai/DeepSeek-R1", provider="together"`.
- `LiteLLMModel` — OpenAI/Anthropic/etc via ` litellm` (`gpt-4`, `claude-4-sonnet`, etc.).
- `OpenAIModel` — OpenAI-compatible endpoints (Together, OpenRouter, local servers).
- `TransformersModel` — local `transformers` / `ollama` models with `device_map="auto"`.
- `AzureOpenAIModel` / `AmazonBedrockModel` — cloud platform wrappers.

## Tool Integrations

Tools are first-class and pluggable:

```python
from smolagents import tool, Tool, ToolCollection

@tool
def get_weather(city: str) -> str:
    """Return weather info for a city."""
    ...

# Hub Space as a tool
image_gen = Tool.from_space(
    space_id="black-forest-labs/FLUX.1-schnell",
    name="image-generator",
    description="Generate an image from a prompt"
)

# Bulk tools from Hub collection or MCP server
from mcp import StdioServerParameters
with ToolCollection.from_mcp(StdioServerParameters(
    command="uvx", args=["--quiet", "pubmedmcp@0.1.3"]
), trust_remote_code=True) as tools:
    agent = CodeAgent(tools=[*tools.tools], ...)
```

Key tool classes:
- `ToolCollection.from_hub(collection_slug)` — load a collection of Space tools.
- `ToolCollection.from_mcp(server_parameters)` — MCP stdio/HTTP/SSE.
- `load_tool(repo_id)` — quick-load a tool Space from Hub.

## Hub Sharing

```python
agent.push_to_hub("username/my-agent")   # uploads agent + tools as a Space
agent.from_hub("username/my-agent")      # load back
agent.save("./local-agent")              # saves agent.json, tools/, app.py
```

Saved agents include `agent.json`, `prompt.yaml`, `tools/*.py`, and `app.py` (Gradio UI).

## Secure Code Execution

`LocalPythonExecutor` is **not a security boundary**. It interprets the AST with:
- Import allowlisting (`additional_authorized_imports`).
- Submodule access control.
- Max operation caps (prevents infinite loops).

For real isolation, use a remote sandbox via `executor_type`:

| Executor | Isolation | Notes |
|----------|-----------|-------|
| `"local"` | None (best-effort mitigations only) | Use for trusted models only |
| `"blaxel"` | VM sandbox, ~25ms cold start | Scales to zero; state sent each run |
| `"e2b"` | Cloud sandbox | Multi-agent requires full-in-sandbox setup |
| `"modal"` | Cloud sandbox | Context-manager auto cleanup |
| `"docker"` | Container | Supports multi-agent with custom `DockerSandbox` |

```python
with CodeAgent(model=model, executor_type="modal") as agent:
    agent.run("Compute the 100th Fibonacci number")
```

Docker security tips (from docs): `security_opt=["no-new-privileges"]`, `cap_drop=["ALL"]`, `mem_limit`, `pids_limit`, run as `nobody`.

## CLI

```bash
smolagent "Plan a trip to Tokyo..." \
  --model-type "InferenceClientModel" \
  --model-id "Qwen/Qwen3-Next-80B-A3B-Thinking" \
  --imports pandas numpy --tools web_search

# Interactive: smolagent (guided setup wizard)
webagent "go to xyz.com, click first sale item, return price"
```

- `smolagent`: generalist multi-step `CodeAgent`.
- `webagent`: vision-based web browsing agent built on `helium`.

## Memory & Observability

- `agent.memory` stores `TaskStep`, `ActionStep`, `PlanningStep`, `SystemPromptStep`.
- `agent.memory.get_succinct_steps()` / `get_full_steps()`.
- `agent.memory.return_full_code()` concatenates all code actions.
- `agent.replay(detailed=True)` pretty-prints execution logs.
- `GradioUI(agent).launch()` for a chat UI; supports file uploads and streaming via `stream_to_gradio`.

## Key Design Philosophy

Agency is a spectrum, not binary. Use smolagents when you need the LLM to *control the workflow*; prefer deterministic code when a fixed pipeline solves the problem reliably. Code-as-action outperforms JSON tool calls because: (1) composability, (2) object management, (3) generality, (4) strong representation in LLM training data.

## Identified Gaps / Future Work

- `LocalPythonExecutor` is fundamentally limited for hostile models; the project docs themselves recommend Modal/E2B for security.
- Multi-agent + sandboxed execution still requires manual wiring (E2B needs code shipped entirely into the sandbox; Docker needs custom interpreter setup).
- API is marked "experimental" and subject to change; pin versions in production.
