---
name: SakThai-hf-agents-course
description: Build AI agents with smolagents, LlamaIndex, LangGraph.
...
---

# AI Agents Course Reference

Based on the [HF Agents Course](https://huggingface.co/learn/agents-course). Covers building, testing, and deploying AI agents using smolagents, LlamaIndex, and LangGraph.

## When to Use

- User wants to "build an AI agent"
- User asks about smolagents, LangGraph, or LlamaIndex
- User needs agentic RAG, function-calling, or tool-use patterns
- User wants to deploy agent demos to HF Spaces

## Prerequisites

- `pip install smolagents llama-index langgraph`
- HF account for sharing agents on the Hub
- API key for the LLM provider the agent uses

## Framework Comparison

| Feature | smolagents | LlamaIndex | LangGraph |
|---------|-----------|------------|-----------|
| **Architecture** | Agent loop (CodeAgent / ToolCallingAgent) | RAG pipeline with agentic layers | Graph-based state machine |
| **Primary Use Case** | Tool-use agents that write & execute Python | Document indexing + query + agentic RAG | Multi-step, branching workflows |
| **Agent Type** | CodeAgent (code-writing), ToolCallingAgent (JSON calls) | QueryEngine agents, ReAct agents | StateGraph nodes with conditional edges |
| **Memory** | Built-in conversation context | Index + chat memory stores | Custom state schema (any typed dict) |
| **Tool Definition** | `@tool` decorator or Tool class | FunctionTool from callables | `@tool` or `ToolNode` |
| **Human-in-Loop** | Manual confirmation hooks | N/A | `interrupt_after` / `Command` |
| **Streaming** | Token-level streaming | Streaming query engine | Streaming via `.astream_events()` |
| **HF Integration** | Native (InferenceClientModel) | `HuggingFaceInferenceAPI` LLM | `ChatHuggingFace` |
| **Deployment** | `gradio` Spaces, `smolagents` CLI | Gradio, FastAPI | LangGraph Cloud / Platform |
| **Learning Curve** | Low | Medium | High |
| **Docs** | [smolagents docs](https://huggingface.co/docs/smolagents) | [LlamaIndex docs](https://docs.llamaindex.ai) | [LangGraph docs](https://langchain-ai.github.io/langgraph/) |

## Code Examples

### smolagents (HF-native)

```python
from smolagents import CodeAgent, InferenceClientModel, tool

@tool
def get_weather(location: str) -> str:
    """Get current weather for a location."""
    return f"Sunny in {location}, 22°C"

model = InferenceClientModel("Qwen/Qwen2.5-72B-Instruct")
agent = CodeAgent(tools=[get_weather], model=model, add_base_tools=True)
agent.run("What's the weather in Paris and what's 123*456?")
```

**With tool calling (not code-writing):**
```python
from smolagents import ToolCallingAgent, HfApiModel

agent = ToolCallingAgent(
    tools=[],
    model=HfApiModel(),
    max_steps=5,
    verbosity_level=2
)
agent.run("Search the web for latest HF news")
```

### LlamaIndex (Agentic RAG)

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.agent import ReActAgent
from llama_index.llms.huggingface import HuggingFaceInferenceAPI

documents = SimpleDirectoryReader("./data").load_data()
index = VectorStoreIndex.from_documents(documents)

query_tool = QueryEngineTool(
    query_engine=index.as_query_engine(),
    metadata=ToolMetadata(
        name="documents",
        description="Provides info from the document corpus"
    )
)

agent = ReActAgent.from_tools(
    [query_tool],
    llm=HuggingFaceInferenceAPI(model_name="Qwen/Qwen2.5-72B-Instruct"),
    verbose=True
)
response = agent.chat("Summarize the key findings from the docs")
```

### LangGraph (Graph-based)

```python
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_huggingface import ChatHuggingFace

class AgentState(TypedDict):
    messages: list
    next_step: str

def call_model(state: AgentState) -> AgentState:
    llm = ChatHuggingFace(model="Qwen/Qwen2.5-72B-Instruct")
    response = llm.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}

def router(state: AgentState) -> Literal["tools", "end"]:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "end"

def run_tools(state: AgentState) -> AgentState:
    return {"messages": state["messages"]}

graph = (
    StateGraph(AgentState)
    .add_node("agent", call_model)
    .add_node("tools", run_tools)
    .add_conditional_edges("agent", router)
    .add_edge("tools", "agent")
    .set_entry_point("agent")
    .compile()
)

result = graph.invoke({"messages": [HumanMessage("What is RLHF?")]})
print(result["messages"][-1].content)
```

## Key Concepts

- **Tools:** Functions the agent can call
- **Agent Loop:** Observe → Think → Act → Observe cycle
- **Memory:** Short-term (conversation context) and long-term (external store)
- **Observability:** Logging traces, monitoring agent decisions
- **Multi-agent:** LangGraph supports sub-graphs for hierarchical agents

## Official Docs & Links

| Resource | URL |
|----------|-----|
| HF Agents Course | [https://huggingface.co/learn/agents-course](https://huggingface.co/learn/agents-course) |
| smolagents docs | [https://huggingface.co/docs/smolagents](https://huggingface.co/docs/smolagents) |
| LlamaIndex docs | [https://docs.llamaindex.ai](https://docs.llamaindex.ai) |
| LangGraph docs | [https://langchain-ai.github.io/langgraph/](https://langchain-ai.github.io/langgraph/) |
| HF smolagents skill | See `mlops/hf-smolagents` in this repo |

## Pitfalls

- Agents are only as good as their tools — provide well-documented, well-named functions.
- smolagents `CodeAgent` writes and executes Python — be cautious with untrusted input.
- LangGraph is graph-based; think in terms of state transitions, not linear flows.
- Agent loops can be expensive — set `max_iterations` limits.
- LlamaIndex agents default to ReAct loop; for complex tasks switch to OpenAI function-calling agent.
- Tool-calling LLMs vary in reliability — test with small runs before scaling.

## Verification

```python
from smolagents import CodeAgent, InferenceClientModel
agent = CodeAgent(tools=[], model=InferenceClientModel())
print(agent.run("What is 2+2?"))  # Should return 4
```
