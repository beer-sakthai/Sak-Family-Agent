# HF Learnings — Agents Course Multi-Agent Orchestration

## 2026-07-24: smolagents Multi-Agent Orchestration Patterns (Topic #143 — Deep Dive on hf-agents-course)

### Summary
Deep-dive into the **multi-agent orchestration patterns** available in `smolagents` v1.26.0, based on the official Hugging Face Agents Course (Unit 2.1) and the smolagents library docs. Covers the two agent paradigms (CodeAgent vs ToolCallingAgent), the manager-worker hierarchy pattern, agent memory management (replay, dynamic mutation, step-by-step execution), custom tool construction, step callbacks, and best practices for building reliable multi-agent systems.

### Source References
- [Hugging Face Agents Course — Unit 2.1: smolagents](https://huggingface.co/learn/agents-course/unit2/smolagents/introduction)
- [smolagents Guided Tour](https://huggingface.co/docs/smolagents/main/en/guided_tour)
- [smolagents Multi-agent Example](https://huggingface.co/docs/smolagents/main/en/examples/multiagents)
- [smolagents Building Good Agents](https://huggingface.co/docs/smolagents/main/en/tutorials/building_good_agents)
- [smolagents Memory Management](https://huggingface.co/docs/smolagents/main/en/tutorials/memory)
- GitHub source: `huggingface/smolagents` — `/docs/source/en/examples/multiagents.md`

---

### 1. Agent Paradigms: CodeAgent vs ToolCallingAgent

smolagents provides two fundamentally different agent types:

| Feature | CodeAgent | ToolCallingAgent |
|---------|-----------|------------------|
| **Action format** | Python code snippets | JSON tool-call blobs |
| **Expressivity** | High — loops, conditionals, nesting, dynamic composition | Low — single tool call per step |
| **Safety** | Requires sandbox (E2B, Docker, Modal, Blaxel) | Safer by design — structured, no arbitrary code execution |
| **Ideal for** | Multi-step reasoning, problem-solving, dynamic tool composition | Simple atomic tasks, API calls, dispatchers |
| **Extra imports** | `additional_authorized_imports=["numpy", "pandas", ...]` | Not applicable (no code execution) |
| **Execution** | Local interpreter or sandbox | JSON parsing + tool dispatch |

**Choice rule:** CodeAgent when you need reasoning/chaining/composition; ToolCallingAgent when you have simple, atomic tools and want high reliability.

```python
from smolagents import CodeAgent, ToolCallingAgent, InferenceClientModel, WebSearchTool

model = InferenceClientModel(model_id="Qwen/Qwen3-Next-80B-A3B-Thinking")

# CodeAgent: for reasoning-heavy tasks
code_agent = CodeAgent(
    tools=[WebSearchTool()],
    model=model,
    additional_authorized_imports=["numpy", "pandas"],
)

# ToolCallingAgent: for structured dispatching
tool_agent = ToolCallingAgent(
    tools=[WebSearchTool()],
    model=model,
    max_steps=10,
)
```

---

### 2. Multi-Agent Hierarchy Pattern

The primary multi-agent pattern in smolagents is a **manager-worker hierarchy**:

```
              +----------------+
              | Manager agent  |
              | (CodeAgent)    |
              +----------------+
                       |
        _______________|______________
       |                              |
Code Interpreter            +------------------+
    tool                    | Web Search agent |
                            | (ToolCallingAgent)|
                            +------------------+
                               |            |
                        Web Search tool     |
                                   Visit webpage tool
```

**How it works:**

1. The **manager** (always a `CodeAgent`) orchestrates the overall task. It receives the user's question, plans, and delegates sub-tasks.
2. **Managed agents** are passed as a list to the `managed_agents` parameter at init.
3. Each managed agent must have `name` and `description` attributes — these are how the manager discovers and calls them.
4. The manager treats managed agents as tools: it "calls" them by name in its generated code.

```python
from smolagents import CodeAgent, ToolCallingAgent, InferenceClientModel, WebSearchTool

model = InferenceClientModel(model_id="Qwen/Qwen3-Next-80B-A3B-Thinking")

# Step 1: Create the worker agent
web_agent = ToolCallingAgent(
    tools=[WebSearchTool(), visit_webpage],   # visit_webpage is a custom tool
    model=model,
    max_steps=10,
    name="web_search_agent",
    description="Runs web searches for you. Returns search results and page content.",
)

# Step 2: Create the manager with managed_agents
manager_agent = CodeAgent(
    tools=[],                                  # Manager has no direct tools — delegates everything
    model=model,
    managed_agents=[web_agent],               # <-- key: list of managed agents
    additional_authorized_imports=["time", "numpy", "pandas"],
)

# Step 3: Run
answer = manager_agent.run("Your complex multi-step question here...")
```

**Key requirements for managed agents:**
- Must have a `name` (string) — used as the function name in manager's code
- Must have a `description` (string) — explains to the manager what this agent does
- The manager sees them as callable functions/tools in its tool list

---

### 3. Building Custom Tools for Web Browsing

Custom tools are functions decorated with `@tool` from smolagents. They must have:
- **Type-annotated parameters** (used for JSON schema generation)
- **A clear docstring** (used as the tool's description by the LLM)
- **Detailed logging** via `print()` statements (appears in observation output)

```python
import re
import requests
from markdownify import markdownify
from requests.exceptions import RequestException
from smolagents import tool

@tool
def visit_webpage(url: str) -> str:
    """Visits a webpage at the given URL and returns its content as a markdown string.

    Args:
        url: The URL of the webpage to visit.

    Returns:
        The content of the webpage converted to Markdown, or an error message if the request fails.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        markdown_content = markdownify(response.text).strip()
        markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)
        print(f"Successfully fetched {url} ({len(markdown_content)} chars)")  # Logging is critical
        return markdown_content
    except RequestException as e:
        return f"Error fetching the webpage: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"
```

**Best practices for tool authoring:**
1. **Provide clear parameter formats** in the docstring (e.g., "date formatted as '%m/%d/%y %H:%M:%S'")
2. **Log everything useful** via `print()` in the tool body — this feeds the LLM's observation
3. **Return structured, readable output** — not raw data
4. **Handle errors gracefully** with descriptive error messages that help the LLM self-correct
5. **Group related functionality** into single tools to minimize LLM calls (fewer calls = fewer errors)

---

### 4. Agent Memory Management

Memory is the agent's history of planning, execution, and errors. smolagents exposes a rich memory API:

#### 4.1 Accessing Memory

```python
from smolagents import ActionStep

# After agent.run(...):
system_prompt_step = agent.memory.system_prompt
print(system_prompt_step.system_prompt)

task_step = agent.memory.steps[0]
print(task_step.task)

for step in agent.memory.steps:
    if isinstance(step, ActionStep):
        if step.error is not None:
            print(f"Step {step.step_number} error: {step.error}")
        else:
            print(f"Step {step.step_number} observations: {step.observations}")
```

#### 4.2 Replaying Agent Runs

```python
# After the agent has run once:
agent.replay()  # Replays the exact same steps from memory
```

#### 4.3 Dynamically Modifying Memory

Useful for:
- Removing old observation images to save token costs
- Injecting prior context from another agent session
- Editing errors before retry

```python
# Remove old screenshots from a browser agent
def update_screenshot(memory_step: ActionStep, agent: CodeAgent) -> None:
    latest_step = memory_step.step_number
    for previous_step in agent.memory.steps:
        if isinstance(previous_step, ActionStep) and previous_step.step_number <= latest_step - 2:
            previous_step.observations_images = None
    # Take new screenshot...
    memory_step.observations_images = [image.copy()]

# Pass as step callback
agent = CodeAgent(
    tools=[...],
    model=model,
    step_callbacks=[update_screenshot],
    max_steps=20,
)
```

#### 4.4 Step-by-Step Execution

Run agents incrementally when operations take a long time:

```python
agent = CodeAgent(tools=[], model=model, verbosity_level=1)
agent.python_executor.send_tools({**agent.tools})

task = "Complex multi-hour task..."
agent.memory.steps.append(TaskStep(task=task, task_images=[]))

final_answer = None
step_number = 1
while final_answer is None and step_number <= 10:
    memory_step = ActionStep(step_number=step_number, observations_images=[])
    final_answer = agent.step(memory_step)
    agent.memory.steps.append(memory_step)
    # Modify memory between steps as needed
    step_number += 1
```

---

### 5. Best Practices for Building Effective Multi-Agent Systems

From the official "Building Good Agents" tutorial + Agents Course guidance:

#### 5.1 Simplify the Workflow
- **Group tools** — combine 2 related API calls into 1 tool (reduces LLM calls, reduces error surface)
- **Use deterministic code** over agentic decisions wherever possible
- **Reduce LLM calls** — each call is a potential point of failure

#### 5.2 Give Clear Instructions
- Pass **system-level instructions** via the `instructions` parameter at agent init
- Pass **task-specific details** in the task string (can be multi-page)
- Include **tool-specific format guidance** in each tool's `description` attribute

#### 5.3 Debugging Strategy
1. **Use a stronger LLM first** (e.g., Qwen3-80B-A3B > smaller models) to rule out reasoning errors
2. **Improve information flow** — add more logging, clearer tool descriptions
3. **Customize prompt templates** only as last resort via `agent.prompt_templates`

#### 5.4 Multi-Agent Design Principles
| Aspect | Recommendation |
|--------|---------------|
| Manager type | Use `CodeAgent` (needs reasoning to plan/orchestrate) |
| Worker type | Use `ToolCallingAgent` for single-timeline tasks (web search, data fetch) |
| Worker count | Keep small (2-4); each worker adds latency and failure points |
| Worker max_steps | Set higher for workers (10+) since they explore/search |
| Manager tools | Keep minimal — manager should delegate, not execute |
| Name/description | Give every worker agent clear, distinct `name` and `description` |

---

### 6. Complete Multi-Agent Web Browser Example

This is the canonical pattern from the smolagents docs:

```python
from smolagents import CodeAgent, ToolCallingAgent, InferenceClientModel, WebSearchTool

# 1. Model
model = InferenceClientModel(model_id="Qwen/Qwen3-Next-80B-A3B-Thinking")

# 2. Custom tool (visit webpage)
@tool
def visit_webpage(url: str) -> str:
    """..."""

# 3. Worker: ToolCallingAgent for web search
web_agent = ToolCallingAgent(
    tools=[WebSearchTool(), visit_webpage],
    model=model,
    max_steps=10,
    name="web_search_agent",
    description="Runs web searches and visits pages. Returns search results and page content.",
)

# 4. Manager: CodeAgent for orchestration
manager_agent = CodeAgent(
    tools=[],
    model=model,
    managed_agents=[web_agent],
    additional_authorized_imports=["time", "numpy", "pandas"],
)

# 5. Run
answer = manager_agent.run(
    "If LLM training continues to scale at current rhythm until 2030, "
    "what electric power in GW would be required? Compare to countries."
)
```

---

### 7. Key Takeaways

1. **smolagents has two execution paradigms**: CodeAgent (code synthesis) and ToolCallingAgent (JSON tool calls). Choose based on task complexity vs. reliability needs.
2. **Multi-agent = manager + workers**: Manager (CodeAgent) plans and delegates; workers (ToolCallingAgent) execute specific tasks. Managed agents need `name` and `description`.
3. **Memory is mutable**: Access `agent.memory.steps` to read/write step history, replay runs, or inject context between sessions.
4. **Step callbacks enable live editing**: Use `step_callbacks` to modify memory during execution (e.g., prune old images to save tokens).
5. **Tools must be well-documented**: Type annotations, clear parameter descriptions, and verbose logging are essential for LLM self-correction.
6. **Best practices reduce errors**: Simplify workflows, group tools, use strong LLMs for reasoning, and provide explicit format instructions.

### Skill
mlops/hf-agents-course — references/hf-learnings.md
