import {
  AdkA2aService,
  AdkAppField,
  AdkCrossCuttingConfig,
  AdkData,
  AdkPlugin,
  AdkPrimitive,
} from "./types";

const PRIMITIVES: AdkPrimitive[] = [
  {
    id: "app",
    name: "App",
    kind: "core",
    summary:
      "The top-level container. Binds a root agent to everything that belongs to the application rather than to one agent: its name (sessions are keyed by it), its plugins, and the context-caching / event-compaction / resumability configs. A Pydantic model, so unknown keywords raise ValidationError instead of being silently dropped.",
    snippet: `from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.plugins import LoggingPlugin


def get_weather(city: str) -> str:
    """Returns a one-line weather report for the given city."""
    return f"It is sunny in {city}."


root_agent = LlmAgent(
    name="weather_agent",
    model="gemini-2.5-flash",
    instruction="Answer weather questions using the get_weather tool.",
    tools=[get_weather],
)

app = App(
    name="weather_app",
    root_agent=root_agent,
    plugins=[LoggingPlugin()],
)`,
  },
  {
    id: "llm-agent",
    name: "LlmAgent",
    kind: "llm-agent",
    summary:
      "A single LLM-backed agent: name, model, instruction, and a tool list. Tools are plain Python functions — ADK reads the signature for the schema and the docstring for the description. No decorator required.",
    snippet: `from google.adk.agents import LlmAgent


def web_search(query: str) -> str:
    """Search the web and return a short summary."""
    return f"Results for {query}"


researcher = LlmAgent(
    name="researcher",
    model="gemini-2.5-pro",
    instruction="Answer factual questions using the web_search tool.",
    tools=[web_search],
)`,
  },
  {
    id: "sequential-agent",
    name: "SequentialAgent",
    kind: "workflow-agent",
    summary:
      "Deterministic pipeline: runs sub-agents in order, threading each output into the next.",
    snippet: `from google.adk.agents import SequentialAgent

pipeline = SequentialAgent(
    name="draft_then_edit",
    sub_agents=[researcher, drafter, editor],
)`,
  },
  {
    id: "parallel-agent",
    name: "ParallelAgent",
    kind: "workflow-agent",
    summary:
      "Fans sub-agents out concurrently over the same input, then merges their outputs. Good for multi-perspective synthesis.",
    snippet: `from google.adk.agents import ParallelAgent

panel = ParallelAgent(
    name="expert_panel",
    sub_agents=[optimistic, pessimistic, pragmatic],
)`,
  },
  {
    id: "loop-agent",
    name: "LoopAgent",
    kind: "workflow-agent",
    summary:
      "Repeats a sub-agent (or a pipeline of them) until an exit condition is met — the research → judge → refine cycle in the course-creation reference architecture is a LoopAgent wrapping a SequentialAgent.",
    snippet: `from google.adk.agents import LoopAgent, SequentialAgent

refine_cycle = LoopAgent(
    name="research_until_good_enough",
    sub_agents=[SequentialAgent(
        name="research_and_judge",
        sub_agents=[researcher, judge],
    )],
    max_iterations=3,
)`,
  },
  {
    id: "runner",
    name: "Runner",
    kind: "runner",
    summary:
      "Owns the event loop and the deployment wiring. Takes the App plus the services (session, artifact, memory, credential). session_service is the one required service. Yields events — tool calls, model output, final response — as they happen.",
    snippet: `import asyncio

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


async def main() -> None:
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=app.name, user_id="user"
    )
    runner = Runner(app=app, session_service=session_service)
    async for event in runner.run_async(
        user_id="user",
        session_id=session.id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text="What is the weather in Zurich?")],
        ),
    ):
        if event.content and event.content.parts:
            print(event.author, event.content.parts[0].text)


if __name__ == "__main__":
    asyncio.run(main())`,
  },
  {
    id: "inmemory-runner",
    name: "InMemoryRunner",
    kind: "runner",
    summary:
      "Development shortcut — supplies in-memory session, artifact, and memory services and takes the same App unchanged. The same App can run against in-memory services in a test and persistent ones in production.",
    snippet: `from google.adk.runners import InMemoryRunner

runner = InMemoryRunner(app=app)`,
  },
  {
    id: "remote-a2a-agent",
    name: "RemoteA2aAgent",
    kind: "tool",
    summary:
      "Treats another ADK service as a sub-agent over the Agent-to-Agent protocol. The orchestrator composes remote agents exactly like local ones — the transport is the only difference.",
    snippet: `import os

from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

researcher = RemoteA2aAgent(
    name="researcher",
    agent_card=os.environ["RESEARCHER_AGENT_CARD_URL"],
)`,
  },
  {
    id: "mcp",
    name: "MCP tools",
    kind: "mcp",
    summary:
      "Attach external Model Context Protocol servers to an agent — their tools land in the same registry as native Python functions and are called identically by the model.",
    snippet: `from google.adk.tools.mcp_tool import MCPToolset, StdioServerParameters

teams_toolset = MCPToolset(
    connection_params=StdioServerParameters(
        command="uv",
        args=[
            "run", "--project",
            "services/teams-copilot-mcp",
            "teams-copilot-mcp",
        ],
    )
)

researcher = LlmAgent(
    name="researcher",
    model="gemini-2.5-pro",
    tools=[web_search, teams_toolset],
)`,
  },
  {
    id: "cli-run",
    name: "adk run / adk web / adk api_server",
    kind: "cli",
    summary:
      "These build the Runner for you. They look for a module-level `app` variable first and fall back to `root_agent` only when no App is found — so exporting the App is what makes plugins and cross-cutting configs take effect.",
    snippet: `# terminal REPL
adk run my_project.agents

# local dev UI
adk web

# headless HTTP API
adk api_server`,
  },
];

const APP_FIELDS: AdkAppField[] = [
  {
    field: "name",
    type: "str",
    defaultValue: "required",
    description: "The application name. Sessions are keyed by it.",
  },
  {
    field: "root_agent",
    type: "BaseAgent | BaseNode",
    defaultValue: "required",
    description:
      "Entry point for execution. BaseNode is the workflow node base class in google.adk.workflow, so a Workflow can be the root too — there is no separate root-node field.",
  },
  {
    field: "plugins",
    type: "list[BasePlugin]",
    defaultValue: "[]",
    description:
      "Application-wide plugins. Their callbacks fire for every agent, model call, and tool call in the tree.",
  },
  {
    field: "context_cache_config",
    type: "ContextCacheConfig | None",
    defaultValue: "None",
    description:
      "Enables context caching for every LLM agent in the app. Absent means caching is off.",
  },
  {
    field: "events_compaction_config",
    type: "EventsCompactionConfig | None",
    defaultValue: "None",
    description:
      "Summarizes older session events so context stops growing without bound.",
  },
  {
    field: "resumability_config",
    type: "ResumabilityConfig | None",
    defaultValue: "None",
    description:
      "Lets an invocation pause on a long-running function call and resume later.",
  },
];

const PLUGINS: AdkPlugin[] = [
  {
    name: "LoggingPlugin",
    importPath: "google.adk.plugins",
    purpose:
      "Logs every agent, model, and tool callback. The default way to see what the tree is actually doing.",
  },
  {
    name: "CountInvocationPlugin",
    importPath: "google.adk.plugins",
    purpose:
      "Counts agent and LLM runs and reports them — cheap instrumentation for cost and loop-depth sanity checks.",
  },
  {
    name: "SaveFilesAsArtifactsPlugin",
    importPath: "google.adk.plugins.save_files_as_artifacts_plugin",
    purpose:
      "Persists files produced during a run into the artifact service instead of leaving them in memory.",
  },
];

const CONFIGS: AdkCrossCuttingConfig[] = [
  {
    id: "context-cache",
    name: "ContextCacheConfig",
    importPath: "google.adk.agents.context_cache_config",
    purpose:
      "Prompt caching across invocations — cuts latency and cost. Params: cache_intervals, ttl_seconds, min_tokens.",
    experimental: true,
  },
  {
    id: "events-compaction",
    name: "EventsCompactionConfig",
    importPath: "google.adk.apps.app",
    purpose:
      "Periodically summarizes older turns. Needs at least one trigger, and each trigger is a pair that must be set together: compaction_interval + overlap_size (sliding window), or token_threshold + event_retention_size (token budget). Leaving summarizer unset makes ADK build an LlmEventSummarizer from the root agent's model.",
    experimental: true,
  },
  {
    id: "resumability",
    name: "ResumabilityConfig",
    importPath: "google.adk.apps",
    purpose:
      "Pause an invocation on a long-running function call and resume it later. Resumption is at-least-once, so a resumable tool must be idempotent.",
    experimental: true,
  },
];

const A2A_SERVICES: AdkA2aService[] = [
  {
    name: "orchestrator",
    role:
      "Main entry point and ADK API Service. Drives the workflow with LoopAgent + SequentialAgent and reaches the workers through RemoteA2aAgent.",
    kind: "orchestrator",
  },
  {
    name: "researcher",
    role: "Standalone A2A microservice that gathers information using Google Search.",
    kind: "worker",
  },
  {
    name: "judge",
    role: "Standalone A2A microservice that evaluates research quality and gates the loop.",
    kind: "worker",
  },
  {
    name: "content_builder",
    role: "Standalone A2A microservice that compiles the final artifact.",
    kind: "worker",
  },
  {
    name: "app",
    role: "Web application that queries the orchestrator and renders progress and results.",
    kind: "app",
  },
];

export function getAdkData(): AdkData {
  return {
    overview: {
      title: "Google ADK — Agent Development Kit for Python",
      description:
        "Google's open-source, code-first framework for building, evaluating, and deploying AI agents. Optimized for Gemini but provider-agnostic. Single agents compose into deterministic workflow-agents (Sequential / Parallel / Loop); an App wraps the tree with application-wide config; a Runner supplies the deployment wiring; and A2A turns any agent into a network-addressable microservice.",
      repoUrl: "https://github.com/google/adk-python",
      docsUrl: "https://google.github.io/adk-docs/",
      pypiUrl: "https://pypi.org/project/google-adk/",
      packageName: "google-adk",
      license: "Apache 2.0",
      pythonMin: "3.10+",
    },
    install: "pip install google-adk",
    quickstart: `import asyncio

from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


root_agent = LlmAgent(
    name="calculator",
    model="gemini-2.5-flash",
    instruction="Use the add tool for arithmetic.",
    tools=[add],
)

app = App(name="calculator_app", root_agent=root_agent)


async def main() -> None:
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=app.name, user_id="user"
    )
    runner = Runner(app=app, session_service=session_service)
    async for event in runner.run_async(
        user_id="user",
        session_id=session.id,
        new_message=types.Content(
            role="user", parts=[types.Part(text="What is 41 + 1?")]
        ),
    ):
        if event.content and event.content.parts:
            print(event.author, event.content.parts[0].text)


if __name__ == "__main__":
    asyncio.run(main())`,
    primitives: PRIMITIVES,
    cliCommands: [
      { command: "pip install google-adk", purpose: "Install the SDK." },
      {
        command: "adk run <module>",
        purpose: "Terminal REPL. Prefers a module-level `app`, falls back to `root_agent`.",
      },
      { command: "adk web", purpose: "Local dev UI for clicking through sessions." },
      { command: "adk api_server", purpose: "Serve the agent as a headless HTTP API." },
    ],
    comparisonNote:
      "ADK sits close to Antigravity and Genkit: all three are Google-adjacent, all three take plain Python callables as tools, all three attach MCP servers. ADK's distinguishing moves are (1) workflow-agents — Sequential / Parallel / Loop as first-class composition primitives rather than a graph library, and (2) the App container, which holds the cross-cutting configs so they travel with the agent definition instead of the call site that happens to build the Runner.",
    app: {
      intro:
        "An agent describes one participant in a conversation. Several things a real deployment needs are not properties of any single agent: the application has one name that sessions are keyed by, plugins observe every agent and every model and tool call in the tree, and caching / compaction / resumability apply to the whole tree at once. App is where those live.",
      snippet: `from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.plugins import LoggingPlugin

app = App(
    name="weather_app",
    root_agent=root_agent,
    plugins=[LoggingPlugin()],
)`,
      runnerSnippet: `session_service = InMemorySessionService()
session = await session_service.create_session(
    app_name=app.name, user_id="user"
)
runner = Runner(app=app, session_service=session_service)`,
      fields: APP_FIELDS,
      plugins: PLUGINS,
      configs: CONFIGS,
      configSnippet: `from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.apps import App, ResumabilityConfig
from google.adk.apps.app import EventsCompactionConfig

app = App(
    name="weather_app",
    root_agent=root_agent,
    context_cache_config=ContextCacheConfig(
        cache_intervals=10, ttl_seconds=1800, min_tokens=2048
    ),
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=5, overlap_size=1
    ),
    resumability_config=ResumabilityConfig(is_resumable=True),
)`,
      legacyNote:
        "Runner accepts either an App or a bare agent, and wraps the bare agent in an App before doing anything else. The two paths are not equivalent — the legacy form is ADK 1.x and still supported, but it silently gives up the cross-cutting configs.",
      legacySnippet: `# Current — the App carries the application-wide configuration.
runner = Runner(app=app, session_service=session_service)

# Legacy — the agent is wrapped in an App for you.
runner = Runner(
    app_name="weather_app",
    agent=root_agent,
    session_service=session_service,
)`,
      legacyDifferences: [
        "The implicit wrapping skips App's validation, so an app name App would reject is accepted here.",
        "context_cache_config, events_compaction_config, and resumability_config are left unset — there is no Runner argument for them, an App is the only way to set them.",
        "Runner(plugins=[...]) is deprecated and raises DeprecationWarning. Passing both app and plugins raises ValueError — put the plugins on the App.",
        "When app and app_name are both given, app_name wins for session lookups while app.name is unchanged. Passing both is rarely what you want.",
      ],
      nameRules:
        'The name must start with a letter, then may contain letters, digits, underscores, and hyphens. "user" is rejected — it is reserved for end-user input. validate_app_name is exported from google.adk.apps.app if you want to check a name before constructing the App.',
      limitations: [
        "EventsCompactionConfig, ResumabilityConfig, and ContextCacheConfig all emit an experimental warning on construction and may change without notice.",
        "EventsCompactionConfig is not re-exported: google.adk.apps exports only App and ResumabilityConfig. Import it from google.adk.apps.app.",
        "Resumption is best-effort — a resumable tool must be idempotent, because resumption guarantees at-least-once execution and any in-memory state is lost across the pause.",
        "Runner logs a warning when the app name does not match the directory the agent was loaded from, naming the directory it expected.",
      ],
    },
    a2a: {
      intro:
        "Agent-to-Agent turns each agent into its own deployable service. The orchestrator composes them with RemoteA2aAgent exactly as it would local sub-agents; each worker runs in its own container and advertises itself through an Agent Card. This is the topology behind Google's distributed course-creation reference architecture.",
      services: A2A_SERVICES,
      agentCardPath: "/a2a/agent/.well-known/agent.json",
      snippet: `import os

from google.adk.agents import LoopAgent, SequentialAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.apps import App

researcher = RemoteA2aAgent(
    name="researcher",
    agent_card=os.environ["RESEARCHER_AGENT_CARD_URL"],
)
judge = RemoteA2aAgent(
    name="judge",
    agent_card=os.environ["JUDGE_AGENT_CARD_URL"],
)
content_builder = RemoteA2aAgent(
    name="content_builder",
    agent_card=os.environ["CONTENT_BUILDER_AGENT_CARD_URL"],
)

root_agent = SequentialAgent(
    name="course_creation",
    sub_agents=[
        LoopAgent(
            name="research_until_good_enough",
            sub_agents=[SequentialAgent(
                name="research_and_judge",
                sub_agents=[researcher, judge],
            )],
            max_iterations=3,
        ),
        content_builder,
    ],
)

app = App(name="orchestrator", root_agent=root_agent)`,
      envVars: [
        {
          key: "RESEARCHER_AGENT_CARD_URL",
          value: "https://<researcher-url>/a2a/agent/.well-known/agent.json",
        },
        {
          key: "JUDGE_AGENT_CARD_URL",
          value: "https://<judge-url>/a2a/agent/.well-known/agent.json",
        },
        {
          key: "CONTENT_BUILDER_AGENT_CARD_URL",
          value: "https://<content-builder-url>/a2a/agent/.well-known/agent.json",
        },
        { key: "AGENT_URL", value: "https://<orchestrator-url>" },
      ],
      sharedFiles: [
        {
          file: "a2a_utils.py",
          purpose:
            "Rewrites agent URLs in the A2A Agent Card when deployed to Cloud Run, where the runtime hostname isn't known at build time.",
        },
        {
          file: "adk_app.py",
          purpose: "ADK API Service implementation with the additional A2A endpoints.",
        },
        {
          file: "authenticated_httpx.py",
          purpose:
            "httpx client extension carrying identity tokens for Cloud Run service-to-service calls.",
        },
      ],
    },
  };
}
