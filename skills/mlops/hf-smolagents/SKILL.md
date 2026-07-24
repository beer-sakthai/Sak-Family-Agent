---
name: hf-smolagents
author: SakThai
license: MIT
description: >-
version: 1.0.0
  smolagents by Hugging Face — build CodeAgents and ToolCallingAgents with minimal
  code. Covers installation, model backends (HF Inference, LiteLLM, Transformers),
  adding tools (MCP, LangChain, Hub Spaces), secure code execution, and CLI usage.
domain: mlops
triggers:
  - smolagents
  - code agent
  - tool calling agent
  - hf agent framework
  - huggingface agent
---

# smolagents — Hugging Face Agent Framework

## Overview

`smolagents` is an open-source Python library (~thousand lines of core agent logic) for building and running AI agents. It supports **CodeAgents** (actions written in Python code) and **ToolCallingAgents** (JSON/text tool-calling).

> **Broader context:** For the conceptual HF Agents Course (smolagents + LlamaIndex + LangGraph), see the `hf-agents-course` skill. This skill focuses on the smolagents library specifically.

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

## Installation

```bash
pip install 'smolagents[toolkit]'    # Includes default tools like web search
pip install 'smolagents[litellm]'     # For OpenAI/Anthropic model support
pip install 'smolagents[transformers]' # For local model support
```

## Quickstart

### CodeAgent (code-writing agent)

```python
from smolagents import CodeAgent, InferenceClientModel

model = InferenceClientModel()  # Uses default HF Inference model
agent = CodeAgent(tools=[], model=model)
result = agent.run("Calculate the sum of numbers from 1 to 10")
print(result)
```

### Adding tools

```python
from smolagents import CodeAgent, InferenceClientModel, DuckDuckGoSearchTool

model = InferenceClientModel()
agent = CodeAgent(
    tools=[DuckDuckGoSearchTool()],
    model=model,
)
result = agent.run("What is the current weather in Paris?")
```

### Using different models

For a detailed comparison of all backends (setup, costs, pitfalls), see `references/model-backends.md`.

```python
# Hugging Face Inference
model = InferenceClientModel(model_id="meta-llama/Llama-2-70b-chat-hf")

# OpenAI/Anthropic via LiteLLM (requires smolagents[litellm])
from smolagents import LiteLLMModel
model = LiteLLMModel(model_id="gpt-4")

# Local model (requires smolagents[transformers])
from smolagents import TransformersModel
model = TransformersModel(model_id="meta-llama/Llama-2-7b-chat-hf")
```

## Tool Integration

smolagents is **tool-agnostic** — you can load tools from:

- **MCP servers** — `ToolCollection.from_mcp()`
- **LangChain** — `Tool.from_langchain()`
- **Hub Spaces** — `Tool.from_space()`
- **Built-in** — `DuckDuckGoSearchTool`, `VisitWebpageTool`, etc.

## CLI Tools

```bash
smolagent --model "gpt-4" --task "Summarize this article"
webagent --url "https://example.com" --task "Extract all links"
```

## Secure Code Execution

CodeAgent executes Python code. For safety, run in sandboxed environments:

- **Modal** — cloud sandbox
- **Blaxel** — managed sandbox
- **E2B** — sandboxed code execution
- **Docker** — local container sandbox

See [secure code execution tutorial](https://huggingface.co/docs/smolagents/en/tutorials/secure_code_execution).

## Advanced Guides

- **Multi-agent systems** — [building_good_agents](https://huggingface.co/docs/smolagents/en/tutorials/building_good_agents)
- **Custom tools** — [tutorials/tools](https://huggingface.co/docs/smolagents/en/tutorials/tools)
- **Text-to-SQL agent** — [examples/text_to_sql](https://huggingface.co/docs/smolagents/en/examples/text_to_sql)

## Pitfalls

- `InferenceClientModel()` without `model_id` uses the HF default — may change over time; always specify explicitly for production
- CodeAgent **executes arbitrary Python** — always sandbox for untrusted tasks
- LiteLLM backend requires `smolagents[litellm]` extras, not just the base install
- Transformers backend loads models locally — watch GPU memory for large models
