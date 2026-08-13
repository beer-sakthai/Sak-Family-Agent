import {
  GenkitData,
  GenkitPrimitive,
  GenkitProvider,
} from "./types";

const PRIMITIVES: GenkitPrimitive[] = [
  {
    id: "genkit-init",
    name: "Genkit(...)",
    kind: "core",
    summary:
      "Root SDK object. Configure plugins, tracing, and the default model here; every decorator + generate call goes through this instance.",
    language: "python",
    snippet: `from genkit.core import Genkit
from genkit_google_genai import googleAI

ai = Genkit(
    plugins=[googleAI()],
    model="googleai/gemini-2.5-flash",
)`,
  },
  {
    id: "tool-decorator",
    name: "@ai.tool()",
    kind: "decorator",
    summary:
      "Register a Python function as a type-safe model tool. Pydantic type hints become the JSON schema the model sees; the docstring becomes the description.",
    language: "python",
    snippet: `from pydantic import BaseModel

class WeatherIn(BaseModel):
    city: str

class WeatherOut(BaseModel):
    forecast: str

@ai.tool()
async def get_weather(input: WeatherIn) -> WeatherOut:
    """Return a short weather blurb for a city."""
    return WeatherOut(forecast=f"{input.city}: sunny, 24C")`,
  },
  {
    id: "define-agent",
    name: "@ai.define_agent()",
    kind: "decorator",
    summary:
      "Declare an autonomous agent with persistent state, a tool set, and a session store. Genkit owns the loop; you just describe the agent.",
    language: "python",
    snippet: `from genkit.stores import FirestoreSessionStore

@ai.define_agent(
    name="research_assistant",
    tools=[get_weather],
    session_store=FirestoreSessionStore(collection="agents/research"),
)
async def research_assistant(input: dict) -> str:
    return await ai.chat("Answer using the tools you have.", history=input.get("history"))`,
  },
  {
    id: "generate-stream",
    name: "ai.generate_stream()",
    kind: "generation",
    summary:
      "Async-streaming generation. Yields chunks as the model produces them — pipe straight into an HTTP SSE response or a CLI printer.",
    language: "python",
    snippet: `async for chunk in ai.generate_stream(
    prompt="Draft a launch email.",
    model="googleai/gemini-2.5-pro",
):
    print(chunk.text, end="", flush=True)`,
  },
  {
    id: "chat",
    name: "ai.chat()",
    kind: "generation",
    summary:
      "Multi-turn conversational interface with automatic history handling. Sits on top of generate() and works with any registered model provider.",
    language: "python",
    snippet: `history = []
while True:
    user = input("You: ")
    response = await ai.chat(user, history=history)
    print(f"AI: {response.text}")
    history = response.history`,
  },
  {
    id: "firestore-session",
    name: "FirestoreSessionStore",
    kind: "session",
    summary:
      "Persistent session storage backed by Firestore — swap for an in-memory store in dev, or bring your own by implementing the store protocol.",
    language: "python",
    snippet: `from genkit.stores import FirestoreSessionStore

store = FirestoreSessionStore(
    collection="agents/sessions",
    project="my-gcp-project",
)`,
  },
  {
    id: "pydantic-output",
    name: "Structured output (Pydantic)",
    kind: "model",
    summary:
      "Ask any model for output shaped by a Pydantic BaseModel. Genkit adds the schema, validates the response, and re-raises validation errors so you can retry.",
    language: "python",
    snippet: `class Recipe(BaseModel):
    title: str
    ingredients: list[str]
    steps: list[str]

recipe = await ai.generate(
    prompt="Give me a quick pasta recipe.",
    output_schema=Recipe,
)
print(recipe.output.title)`,
  },
];

const PROVIDERS: GenkitProvider[] = [
  {
    id: "google-genai",
    name: "Google Gemini",
    packageName: "genkit-google-genai",
    description:
      "First-party plugin covering the Gemini family (2.5-flash, 2.5-pro, and multimodal variants).",
    supported: true,
  },
  {
    id: "vertex",
    name: "Vertex AI",
    packageName: "genkit-vertexai",
    description:
      "Vertex-hosted Gemini + custom-tuned models, with IAM-based auth.",
    supported: true,
  },
  {
    id: "anthropic",
    name: "Anthropic Claude",
    packageName: "genkit-anthropic",
    description: "Claude family via the Anthropic Messages API.",
    supported: true,
  },
  {
    id: "openai",
    name: "OpenAI",
    packageName: "genkit-openai",
    description: "GPT-4 family and any OpenAI-compatible endpoint.",
    supported: true,
  },
  {
    id: "ollama",
    name: "Ollama",
    packageName: "genkit-ollama",
    description: "Local model runner — same programming model, offline execution.",
    supported: true,
  },
];

export function getGenkitData(): GenkitData {
  return {
    overview: {
      title: "Genkit — Python",
      description:
        "Google's open-source framework for building full-stack, AI-powered and agentic applications. The Python port brings the same decorator + Pydantic-driven programming model as the JS/TS version, with unified provider APIs, native OpenTelemetry tracing, and a local Developer UI for inspecting flows.",
      repoUrl: "https://github.com/genkit-ai/genkit-python",
      pypiUrl: "https://pypi.org/project/genkit/",
      packageName: "genkit",
      license: "Apache 2.0",
      author: "Google (genkit-ai organization)",
      pythonMin: "3.10+",
    },
    install:
      "uv add genkit genkit-google-genai genkit-google-cloud genkit-middleware",
    quickstart: `import asyncio
from pydantic import BaseModel
from genkit.core import Genkit
from genkit_google_genai import googleAI

ai = Genkit(
    plugins=[googleAI()],
    model="googleai/gemini-2.5-flash",
)

class RecipeInput(BaseModel):
    theme: str

@ai.tool()
async def suggest_recipe(input: RecipeInput) -> str:
    """Suggest a recipe matching a theme."""
    return f"How about a {input.theme} pasta?"

async def main() -> None:
    response = await ai.chat("Give me a recipe for weeknight dinner.")
    print(response.text)

if __name__ == "__main__":
    asyncio.run(main())`,
    primitives: PRIMITIVES,
    providers: PROVIDERS,
    distinctiveFeatures: [
      "Type-safety via native Python annotations + Pydantic — schemas are inferred, not hand-written.",
      "Unified model API across Gemini, Vertex, Claude, OpenAI, and Ollama — same call, swap the provider string.",
      "Integrated OpenTelemetry tracing — flows and tool calls emit spans automatically.",
      "Local Developer UI for inspecting flow execution, replaying runs, and testing tools interactively.",
      "Persistent agents via session stores (Firestore ships in-box; bring-your-own for other backends).",
    ],
  };
}
