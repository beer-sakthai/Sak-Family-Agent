import {
  AntigravityComparisonRow,
  AntigravityData,
  AntigravityFeature,
  AntigravityPrimitive,
} from "./types";

const PRIMITIVES: AntigravityPrimitive[] = [
  {
    id: "agent",
    name: "Agent",
    kind: "agent",
    summary:
      "Batteries-included entry point. Owns the agentic loop, tool registry, MCP connections, and lifecycle — use it as an async context manager to ensure sessions and background triggers shut down cleanly.",
    language: "python",
    snippet: `from google.antigravity import Agent, LocalAgentConfig

config = LocalAgentConfig()

async def main() -> None:
    async with Agent(config) as agent:
        response = await agent.chat("Summarize today's news.")
        print(await response.text())`,
  },
  {
    id: "localagentconfig",
    name: "LocalAgentConfig",
    kind: "config",
    summary:
      "Declarative configuration for a local Antigravity agent — connection strategy, model selection, hook policies, tool set, MCP servers. Fluent-style overrides map straight onto Agent(...).",
    language: "python",
    snippet: `from google.antigravity import LocalAgentConfig, LocalConnectionStrategy

config = LocalAgentConfig(
    connection_strategy=LocalConnectionStrategy(),
    model="gemini-2.5-pro",
    system_instruction="You are a concise research assistant.",
)`,
  },
  {
    id: "conversation",
    name: "Conversation",
    kind: "conversation",
    summary:
      "Stateful session object accumulating turns, tool calls, and model reasoning across chat() invocations. Backs multi-turn agents that need memory beyond a single request.",
    language: "python",
    snippet: `async with Agent(config) as agent:
    convo = await agent.start_conversation()
    r1 = await convo.chat("What did I say last time about metros?")
    r2 = await convo.chat("Plan a route based on that.")
    for step in convo.steps:
        print(step.role, step.summary())`,
  },
  {
    id: "chatresponse",
    name: "ChatResponse",
    kind: "response",
    summary:
      "Rich response object. Await .text() for the final string, or async-iterate to stream tokens, reasoning traces, and tool-call events as they arrive.",
    language: "python",
    snippet: `response = await agent.chat("Draft a launch email.")

async for event in response.stream():
    if event.kind == "token":
        print(event.text, end="", flush=True)
    elif event.kind == "tool_call":
        print(f"\\n[tool] {event.tool_name}({event.arguments})")`,
  },
  {
    id: "interactive-loop",
    name: "run_interactive_loop()",
    kind: "loop",
    summary:
      "One-liner REPL over an Agent — reads user input, streams the model's reply, keeps state. Handy for smoke-testing tool integrations before wiring into a real UI.",
    language: "python",
    snippet: `from google.antigravity import Agent, LocalAgentConfig, run_interactive_loop

async def main() -> None:
    async with Agent(LocalAgentConfig()) as agent:
        await run_interactive_loop(agent)`,
  },
  {
    id: "custom-tool",
    name: "Custom tool registration",
    kind: "tool",
    summary:
      "Register a plain Python function as a tool the agent can call. Type hints become the input schema; the docstring becomes the description the model sees.",
    language: "python",
    snippet: `from google.antigravity import tool

@tool
def get_weather(city: str) -> dict[str, str]:
    """Return a short weather blurb for a city."""
    return {"city": city, "forecast": "sunny, 24C"}

config = LocalAgentConfig(tools=[get_weather])`,
  },
  {
    id: "policy-hook",
    name: "Policy hooks",
    kind: "hook",
    summary:
      "Interpose on tool calls and message events with per-turn hooks — allow, deny, or rewrite arguments. Same pattern as sakthai's GuardrailPolicy but expressed as callables.",
    language: "python",
    snippet: `from google.antigravity import Hook, HookDecision

class ShellGuard(Hook):
    async def on_tool_call(self, call):
        if call.tool_name == "run_shell":
            return HookDecision.deny("shell disabled in prod")
        return HookDecision.allow()

config = LocalAgentConfig(hooks=[ShellGuard()])`,
  },
  {
    id: "mcp-integration",
    name: "MCP server integration",
    kind: "mcp",
    summary:
      "Attach external Model Context Protocol servers directly to an Antigravity agent — their tools merge into the same registry as native tools, callable identically by the model.",
    language: "python",
    snippet: `from google.antigravity import LocalAgentConfig, MCPServerSpec

config = LocalAgentConfig(
    mcp_servers=[
        MCPServerSpec(
            name="teams-copilot",
            command="uv",
            args=["run", "--project", "services/teams-copilot-mcp", "teams-copilot-mcp"],
        )
    ]
)`,
  },
];

const FEATURES: AntigravityFeature[] = [
  {
    id: "multimodal",
    title: "Multimodal ingestion",
    description:
      "Images, videos, audio, and documents passed to chat() alongside text — the SDK handles encoding + upload to Gemini.",
    category: "multimodal",
  },
  {
    id: "custom-tools",
    title: "Custom tools",
    description:
      "Plain Python callables become model tools via the @tool decorator; type hints drive the JSON schema.",
    category: "tools",
  },
  {
    id: "mcp",
    title: "MCP integration",
    description:
      "External MCP servers attach directly; their tools merge into the same registry as first-party ones.",
    category: "mcp",
  },
  {
    id: "hooks",
    title: "Policy hooks",
    description:
      "Interpose on tool calls and messages to allow, deny, or rewrite — like sakthai's guardrails, but as callables.",
    category: "policy",
  },
  {
    id: "background-triggers",
    title: "Background triggers",
    description:
      "Schedule side channels that push events back into an active conversation — timers, webhooks, external subscriptions.",
    category: "background",
  },
  {
    id: "streaming",
    title: "Streaming reasoning + tokens",
    description:
      "Async-iterate the ChatResponse to receive tokens, tool-call events, and the model's reasoning trace as they arrive.",
    category: "streaming",
  },
];

const COMPARISON: AntigravityComparisonRow[] = [
  {
    dimension: "Vendor",
    antigravity: "Google (Gemini)",
    chatkit: "OpenAI (GPT)",
    mcpSdk: "Anthropic + community (protocol)",
  },
  {
    dimension: "Layer",
    antigravity: "Full agent framework (loop + hooks + tools)",
    chatkit: "Conversational UI + backend samples",
    mcpSdk: "Wire protocol + primitives for tool servers",
  },
  {
    dimension: "Runtime",
    antigravity:
      "Requires a compiled binary shipped in the platform wheel — installing from source alone will not work.",
    chatkit: "Pure JavaScript + Python",
    mcpSdk: "Pure Python",
  },
  {
    dimension: "Transport for tools",
    antigravity: "In-process @tool + attached MCP servers",
    chatkit: "Server tool calls via FastAPI",
    mcpSdk: "stdio / SSE (JSON-RPC 2.0)",
  },
  {
    dimension: "Streaming",
    antigravity: "Tokens + reasoning traces + tool events",
    chatkit: "Tokens + widget events",
    mcpSdk: "Protocol-level — depends on the server",
  },
];

export function getAntigravityData(): AntigravityData {
  return {
    overview: {
      title: "Google Antigravity — Python SDK",
      description:
        "Full-stack agent framework from Google: an Agent class that owns the agentic loop, a Conversation for stateful sessions, a ChatResponse that streams tokens and reasoning, hooks for policy enforcement, first-class MCP attachment, and background triggers. Powered by Antigravity + Gemini.",
      repoUrl: "https://github.com/google-antigravity/antigravity-sdk-python",
      docsUrl: "https://github.com/google-antigravity/antigravity-sdk-python#readme",
      license: "Apache License 2.0",
      author: "Google",
      pypiUrl: "https://pypi.org/project/google-antigravity/",
      packageName: "google-antigravity",
    },
    install: {
      pypi: "pip install google-antigravity",
      warning:
        "The SDK ships a compiled runtime binary in the platform-specific wheel — cloning the source repo alone is NOT enough, you must install from PyPI so the wheel drops the binary in place.",
    },
    quickstart: `import asyncio
from google.antigravity import Agent, LocalAgentConfig

async def main() -> None:
    config = LocalAgentConfig()
    async with Agent(config) as agent:
        response = await agent.chat("Give me three ideas for tonight's dinner.")
        print(await response.text())

if __name__ == "__main__":
    asyncio.run(main())`,
    primitives: PRIMITIVES,
    features: FEATURES,
    comparison: COMPARISON,
  };
}
