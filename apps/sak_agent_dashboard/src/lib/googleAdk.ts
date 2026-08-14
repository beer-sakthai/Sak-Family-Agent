import { AdkData, AdkPrimitive } from "./types";

const PRIMITIVES: AdkPrimitive[] = [
  {
    id: "llm-agent",
    name: "LlmAgent",
    kind: "llm-agent",
    summary:
      "A single LLM-backed agent: instructions, tool set, and a target model. The workhorse used inside any workflow-agent composition.",
    snippet: `from google.adk.agents import LlmAgent

researcher = LlmAgent(
    name="researcher",
    model="gemini-2.5-pro",
    instruction="Answer factual questions using the search tool.",
    tools=[web_search],
)`,
  },
  {
    id: "sequential-agent",
    name: "SequentialAgent",
    kind: "workflow-agent",
    summary:
      "Deterministic pipeline: runs sub-agents in order, threading each output into the next. The plain map-reduce case in ADK.",
    snippet: `from google.adk.agents import SequentialAgent

pipeline = SequentialAgent(
    name="draft-then-edit",
    sub_agents=[researcher, drafter, editor],
)`,
  },
  {
    id: "parallel-agent",
    name: "ParallelAgent",
    kind: "workflow-agent",
    summary:
      "Fan out sub-agents concurrently on the same input; a reducer merges their outputs. Good for multi-perspective synthesis.",
    snippet: `from google.adk.agents import ParallelAgent

panel = ParallelAgent(
    name="expert-panel",
    sub_agents=[optimistic, pessimistic, pragmatic],
)`,
  },
  {
    id: "runner",
    name: "Runner",
    kind: "runner",
    summary:
      "Owns session state and the event loop. Feeds user messages into an agent and receives streamed events (tool calls, tokens, final response).",
    snippet: `from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionStore

runner = Runner(agent=pipeline, session_store=InMemorySessionStore())

async for event in runner.run_async(session_id, user_message="Kick off the draft."):
    print(event)`,
  },
  {
    id: "tool",
    name: "Tool",
    kind: "tool",
    summary:
      "Any Python callable becomes a tool via type-hint reflection. ADK also imports OpenAPI specs directly and exposes attached MCP servers as tools.",
    snippet: `from google.adk.tools import tool

@tool
def get_stock_quote(symbol: str) -> dict[str, float]:
    """Return the current quote for a symbol."""
    return {"symbol": symbol, "price": 123.45}`,
  },
  {
    id: "mcp",
    name: "MCP tools",
    kind: "mcp",
    summary:
      "Attach external Model Context Protocol servers directly to an agent — their tools land in the same registry as native @tool functions.",
    snippet: `from google.adk.tools import mcp

teams_mcp = mcp.connect_stdio(
    name="teams-copilot",
    command="uv",
    args=["run", "--project", "services/teams-copilot-mcp", "teams-copilot-mcp"],
)

researcher = LlmAgent(
    name="researcher",
    model="gemini-2.5-pro",
    tools=[web_search, *teams_mcp.tools()],
)`,
  },
  {
    id: "cli-run",
    name: "adk run / adk web",
    kind: "cli",
    summary:
      "Ship-time entry points: `adk run` launches an agent from a Python module in the terminal; `adk web` serves a local dev UI to click through sessions.",
    snippet: `# terminal REPL
adk run my_project.agents:pipeline

# local dev UI (like Genkit's Developer UI)
adk web`,
  },
];

export function getAdkData(): AdkData {
  return {
    overview: {
      title: "Google ADK — Agent Development Kit for Python",
      description:
        "Google's open-source, code-first framework for building, evaluating, and deploying AI agents. Optimized for Gemini, but works with any provider. Composes single agents into deterministic workflow-agents (Sequential / Parallel) and offloads session + event loop to a Runner.",
      repoUrl: "https://github.com/google/adk-python",
      pypiUrl: "https://pypi.org/project/google-adk/",
      packageName: "google-adk",
      license: "Apache 2.0",
      pythonMin: "3.10+",
    },
    install: "pip install google-adk",
    quickstart: `import asyncio
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionStore
from google.adk.tools import tool

@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b

agent = LlmAgent(
    name="calculator",
    model="gemini-2.5-flash",
    instruction="Use the add tool for arithmetic.",
    tools=[add],
)

async def main() -> None:
    runner = Runner(agent=agent, session_store=InMemorySessionStore())
    async for event in runner.run_async("session-1", user_message="What is 41 + 1?"):
        print(event)

if __name__ == "__main__":
    asyncio.run(main())`,
    primitives: PRIMITIVES,
    cliCommands: [
      { command: "pip install google-adk", purpose: "Install the SDK." },
      { command: "adk run <module>:<agent>", purpose: "Terminal REPL for a defined agent." },
      { command: "adk web", purpose: "Local dev UI (like Genkit's Developer UI)." },
      { command: "adk deploy", purpose: "Bundle and deploy an agent (Cloud Run / Vertex AI targets)." },
    ],
    comparisonNote:
      "ADK sits close to Antigravity and Genkit on the map: all three are Google-adjacent agent frameworks, all three ship a decorator/tool model, and all three integrate MCP servers. ADK's distinguishing move is workflow-agents (SequentialAgent / ParallelAgent) as first-class composition primitives — the same job you'd do with a graph library elsewhere.",
  };
}
