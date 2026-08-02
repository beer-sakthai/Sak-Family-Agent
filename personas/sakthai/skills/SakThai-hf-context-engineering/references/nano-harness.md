# Nano Harness — Build Your Own Agent Loop

Based on the bonus unit of the HF Context Course. A minimal agent loop implements
the **Observe → Think → Act → Observe** cycle in ~200 lines of Python.

## Core Loop

```python
"""Minimal code agent harness — Hermes-style tool execution loop."""
import json, sys
from typing import Callable

class Tool:
    def __init__(self, name: str, fn: Callable, desc: str):
        self.name = name
        self.fn = fn
        self.desc = desc

class Agent:
    def __init__(self, tools: list[Tool], model_api: Callable):
        self.tools = {t.name: t for t in tools}
        self.model = model_api

    def run(self, task: str, max_steps: int = 10):
        messages = [{"role": "user", "content": task}]
        for step in range(max_steps):
            # Think: call the LLM
            response = self.model(messages)
            content = response["choices"][0]["message"]["content"]
            print(f"\n--- Step {step} ---\n{content}")

            # Act: parse tool call
            if "```tool" in content:
                tool_block = content.split("```tool")[1].split("```")[0].strip()
                call = json.loads(tool_block)
                tool = self.tools.get(call["name"])
                if tool:
                    result = tool.fn(**call["args"])
                    messages.append({"role": "user", "content": f"Result: {result}"})
                else:
                    messages.append({"role": "user", "content": f"Unknown tool: {call['name']}"})
            else:
                # Final answer — stop
                return content
        return "Max steps reached"
```

## Key Concepts

| Component | What it does |
|-----------|-------------|
| **Tool registry** | Dict mapping tool names to callable functions + descriptions |
| **Message loop** | Accumulates conversation history (user + assistant + tool results) |
| **Parsing** | Extract tool calls from model output (regex, JSON block, or function tokens) |
| **Step limit** | Prevents infinite loops |
| **Context window** | Truncates oldest messages when history exceeds model's limit |

## Usage

```python
def search(query: str) -> str:
    return f"Results for: {query}"

agent = Agent(
    tools=[Tool("search", search, "Web search")],
    model_api=my_llm_call
)
print(agent.run("Find latest HF models"))
```

## Pitfalls

- The `model_api` must return parseable tool calls — different models use different formats
- No error recovery: if a tool throws, the loop breaks
- Context accumulation: long sessions exceed LLM context windows
- No parallel execution: each step waits for the LLM
