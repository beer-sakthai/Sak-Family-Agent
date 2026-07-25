# HF Learnings — InferenceClient Tool Use & Function Calling Deep Dive

## 2026-07-25: hf-inference-client-tool-use-and-function-calling-deep-dive — Complete Tool/Function Calling Reference (Topic #155 Deepened)

### Summary
Comprehensive technical deep-dive into tool use and function calling with Hugging Face's `InferenceClient` across both API styles (native huggingface_hub and OpenAI-compatible). Covers every API parameter, output type, multi-turn tool loop patterns, streaming with tools, the experimental MCPClient, structured outputs, and provider compatibility — sourced from huggingface_hub source code (v1.24.0+) and official docs.

### Architecture Overview

InferenceClient supports two API styles for tool calling:

| Style | Syntax | Best For |
|-------|--------|----------|
| **Native** | `client.chat_completion(messages, tools=tools, tool_choice="auto")` | Full feature set, explicit model control |
| **OpenAI-compatible** | `client.chat.completions.create(model=..., messages=..., tools=tools)` | Migration from OpenAI SDK, direct drop-in replacement |

Both styles are backed by the same underlying HTTP calls to the Hugging Face Router API at `https://router.huggingface.co/v1`.

### Tool Definition Format (ChatCompletionInputTool)

Tools follow the OpenAI function-calling schema. The type definition from the huggingface_hub codebase:

```python
@dataclass
class ChatCompletionInputTool:
    function: ChatCompletionInputFunctionDefinition
    type: str  # Always "function"

@dataclass
class ChatCompletionInputFunctionDefinition:
    name: str
    parameters: Any          # JSON Schema object
    description: str | None  # Model hint for when to call this tool
```

**Concrete example** (the canonical format):
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current temperature for a given location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and country e.g. Paris, France"
                    }
                },
                "required": ["location"]
            }
        }
    }
]
```

**Key notes:**
- The `type` must be `"function"` — this is the only supported tool type currently
- `parameters` follows JSON Schema (OpenAPI 3.0 subset) — supports `object`, `array`, `string`, `number`, `integer`, `boolean`, `enum`, nested objects
- `description` on both the function and individual parameters helps the model decide when to call
- Tools can be passed as dicts (like above) or as `ChatCompletionInputTool` dataclass instances

### The `tool_choice` Parameter

Controls whether and which tool the model should use:

| Value | Type | Behavior |
|-------|------|----------|
| `"auto"` | `ChatCompletionInputToolChoiceEnum` | Model decides whether to call a tool or respond directly (default) |
| `"none"` | `ChatCompletionInputToolChoiceEnum` | Model must respond directly — never call a tool |
| `"required"` | `ChatCompletionInputToolChoiceEnum` | Model must call one of the provided tools |
| `{"type": "function", "function": {"name": "tool_name"}}` | `ChatCompletionInputToolChoiceClass` | Force a specific tool |

```python
# Let model decide (default)
client.chat_completion(messages=messages, tools=tools, tool_choice="auto")

# Force tool usage
client.chat_completion(messages=messages, tools=tools, tool_choice="required")

# Force specific tool
client.chat_completion(messages=messages, tools=tools, tool_choice={
    "type": "function",
    "function": {"name": "get_weather"}
})
```

The `ChatCompletionInputToolChoiceClass` dataclass:
```python
@dataclass
class ChatCompletionInputToolChoiceClass:
    function: ChatCompletionInputFunctionName  # Just the name field
```

Where `ChatCompletionInputFunctionName` is:
```python
@dataclass
class ChatCompletionInputFunctionName:
    name: str
```

### The `tool_prompt` Parameter (Legacy)

```python
tool_prompt: str | None = None
```

A prompt appended **before** the tool definitions in the system message. This is a Hugging Face-specific extension (not in the OpenAI API). Some providers use it to inject instructions like "You have the following tools available..." which can improve tool selection for models not fine-tuned for tool use.

**Current status:** Deprecated in favor of proper tool chat templates. Not needed for models like Llama-3, Qwen2.5, or DeepSeek that have native tool-use support. Still useful for older base models being used instruct-style.

### Tool Call Output Types

When the model decides to call a tool, the response contains `tool_calls` on the output message:

```python
response = client.chat_completion(
    model="meta-llama/Meta-Llama-3-70B-Instruct",
    messages=messages,
    tools=tools,
    tool_choice="auto",
)

# Check for tool calls
message = response.choices[0].message
if message.tool_calls:
    for tc in message.tool_calls:
        print(f"Tool: {tc.function.name}")
        print(f"Args: {tc.function.arguments}")
        print(f"ID:   {tc.id}")  # Unique call ID for matching
```

**ChatCompletionOutputMessage structure:**
```python
@dataclass
class ChatCompletionOutputMessage:
    role: str
    content: str | None           # None when calling tools
    name: str | None
    tool_calls: list[ChatCompletionOutputToolCall] | None

@dataclass
class ChatCompletionOutputToolCall:
    function: ChatCompletionOutputFunctionDefinition
    id: str
    type: str  # "function"

@dataclass
class ChatCompletionOutputFunctionDefinition:
    arguments: str | dict  # JSON string or parsed dict
    name: str
    description: str | None
```

**Note:** The `arguments` field in output can be either a JSON string or a parsed dict depending on the provider. Always parse with `json.loads()` if it's a string.

### Multi-Turn Tool Use Pattern

The fundamental pattern for tool-augmented LLM interactions:

```python
import json
from huggingface_hub import InferenceClient

client = InferenceClient(provider="novita")

def execute_tool(tool_call) -> str:
    """Execute a tool and return its result."""
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments) if isinstance(tool_call.function.arguments, str) else tool_call.function.arguments
    
    if name == "get_weather":
        # Actually call your weather API here
        return json.dumps({"temperature": 72, "conditions": "sunny", "location": args["location"]})
    elif name == "get_n_day_weather_forecast":
        return json.dumps({"forecast": "Sunny all week"})
    return json.dumps({"error": f"Unknown tool: {name}"})

# Tools definition
tools = [...]  # as defined above

# Initial call
response = client.chat_completion(
    model="Qwen/Qwen2.5-72B-Instruct",
    messages=[{"role": "user", "content": "What's the weather in SF for the next 3 days?"}],
    tools=tools,
    tool_choice="auto",
    max_tokens=500,
)

# Handle tool calls
while response.choices[0].message.tool_calls:
    message = response.choices[0].message
    
    # Add assistant message with tool calls to history
    messages.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})
    
    # Execute each tool and add results
    for tc in message.tool_calls:
        result = execute_tool(tc)
        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": result
        })
    
    # Continue the conversation
    response = client.chat_completion(
        model="Qwen/Qwen2.5-72B-Instruct",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=500,
    )

# Final text response
print(response.choices[0].message.content)
```

**Critical details:**
- The `tool_call_id` in the tool response **must** match the `id` from the assistant's `tool_calls` — this links each result to its call
- The assistant message with `tool_calls` should have `content=None` or omit content entirely (many providers expect this)
- Tool result messages use `role="tool"` — this is the OpenAI convention
- Keep passing the full `tools` list on every call in the loop (the model needs to see definitions again for follow-up calls)
- Set a maximum iteration limit to prevent infinite loops

### Streaming with Tool Calls

Tool calls in streaming mode are received as delta chunks:

```python
from huggingface_hub import InferenceClient

client = InferenceClient()

stream = client.chat_completion(
    model="meta-llama/Meta-Llama-3-70B-Instruct",
    messages=messages,
    tools=tools,
    tool_choice="auto",
    max_tokens=500,
    stream=True,
)

tool_calls_buffer = {}
current_index = None

for chunk in stream:
    delta = chunk.choices[0].delta if chunk.choices else None
    if delta is None:
        continue
    
    # Regular content
    if delta.content:
        print(delta.content, end="")
    
    # Tool call deltas
    if delta.tool_calls:
        for tc_delta in delta.tool_calls:
            idx = tc_delta.index
            
            if idx not in tool_calls_buffer:
                tool_calls_buffer[idx] = {
                    "id": "",
                    "type": "function",
                    "function": {"name": "", "arguments": ""}
                }
            
            if tc_delta.id:
                tool_calls_buffer[idx]["id"] = tc_delta.id
            if tc_delta.function:
                if tc_delta.function.name:
                    tool_calls_buffer[idx]["function"]["name"] += tc_delta.function.name
                if tc_delta.function.arguments:
                    tool_calls_buffer[idx]["function"]["arguments"] += tc_delta.function.arguments
    
    # Check finish reason
    if chunk.choices[0].finish_reason == "tool_calls":
        print("\n[Model requested tool calls]")
        # tool_calls_buffer now contains complete tool calls
    elif chunk.choices[0].finish_reason == "stop":
        print("\n[Done]")
```

**Stream delta structure:**
```python
@dataclass
class ChatCompletionStreamOutputDelta:
    content: str | None
    role: str | None
    tool_calls: list[ChatCompletionStreamOutputDeltaToolCall] | None

@dataclass
class ChatCompletionStreamOutputDeltaToolCall:
    index: int
    id: str | None
    function: ChatCompletionStreamOutputDeltaFunction | None
    type: str | None

@dataclass
class ChatCompletionStreamOutputDeltaFunction:
    name: str | None
    arguments: str | None
```

Key streaming behavior:
- Tool call names arrive in the **first** delta for each index (not split)
- Arguments arrive **incrementally** as chunks — you must concatenate them
- The `finish_reason="tool_calls"` signals the end of all tool calls
- Multiple tool calls arrive with different `index` values (parallel tool calls)

### OpenAI-Compatible Syntax

The `client.chat.completions.create()` method is an alias for `chat_completion` with slightly different defaults:

```python
from huggingface_hub import InferenceClient

# Instead of: from openai import OpenAI
client = InferenceClient(
    base_url="https://router.huggingface.co/v1",  # Optional — auto-detected
    api_key="hf_...",
)

# OpenAI-compatible call with tools
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-72B-Instruct",
    messages=messages,
    tools=tools,
    tool_choice="auto",
    max_tokens=500,
    stream=True,
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

**Compatibility notes:**
- All OpenAI parameters are supported: `tools`, `tool_choice`, `response_format`, `stream`, `max_tokens`, `temperature`, `top_p`, `stop`, `frequency_penalty`, `presence_penalty`, `seed`, `logprobs`, `top_logprobs`, `n`
- The `tool_choice` parameter accepts `"auto"`, `"none"`, `"required"`, or `{"type": "function", "function": {"name": "..."}}`
- The response format is **not** identical to OpenAI's — the `ChatCompletionOutput` class wraps the response but should be compatible

### Provider-Specific Behavior (from official huggingface_hub docs)

The docs explicitly note: *"Please refer to the providers' documentation to verify which models are supported by them for Function/Tool Calling."*

**Tested provider support patterns (verified 2026-07-24 from huggingface_hub source examples):**

| Provider | Tool Calling | Structured Outputs | Notes |
|----------|:-----------:|:------------------:|-------|
| **Novita** | ✅ | ❓ | Docs example uses Novita for Qwen2.5-72B |
| **Together** | ✅ | ❓ | Broad model support |
| **Fireworks AI** | ✅ | ❓ | Known for function-calling support |
| **DeepInfra** | ✅ | ❓ | Good tool support |
| **Cerebras** | ❓ | ✅ | Docs example uses Cerebras for structured outputs |
| **Featherless AI** | ✅ | ❓ | Free tier, basic tool support |
| **Groq** | ✅ | ✅ | LPU — fast tool calls + structured outputs |
| **HF Inference** | ✅ | ❓ | Free tier, smaller models |

**General guidance from docs:**
- Models **fine-tuned for tool use** (Llama-3.1, Qwen2.5, DeepSeek, Hermes) work best
- Models like Phi-3, Gemma may not support tool calling reliably
- Always check `supports_tools` field from the Router API (`/v1/models/{model_id}`) for per-model info
- Providers that don't support tools will either silently ignore the `tools` parameter or error

### MCPClient — Experimental Tool Orchestration

Hugging Face Hub v1.24.0+ includes an experimental `MCPClient` that combines `AsyncInferenceClient` with the Model Context Protocol:

```python
import os
from huggingface_hub import MCPClient, ChatCompletionInputMessage, ChatCompletionStreamOutput

async def main():
    async with MCPClient(
        provider="novita",
        model="Qwen/Qwen2.5-72B-Instruct",
        api_key=os.environ["HF_TOKEN"],
    ) as client:
        # Add an MCP server (local or remote) that exposes tools
        await client.add_mcp_server(
            type="sse",  # "sse" for remote, "stdio" for local
            url="https://evalstate-flux1-schnell.hf.space/gradio_api/mcp/sse"
        )
        
        messages = [{"role": "user", "content": "Generate a picture of a cat on the moon"}]
        
        async for chunk in client.process_single_turn_with_tools(messages):
            if isinstance(chunk, ChatCompletionStreamOutput):
                delta = chunk.choices[0].delta
                if delta.content:
                    print(delta.content, end="")
            elif isinstance(chunk, ChatCompletionInputMessage):
                print(f"\nCalled tool '{chunk.name}'. Result: '{chunk.content[:1000] if chunk.content else '...'}'")
```

**Key MCPClient features:**
- `add_mcp_server(type="sse"|"stdio", url=..., command=...)` — Register an MCP server
- `process_single_turn_with_tools(messages, ...)` — Single loop: chat → tool call → result → response
- Returns a stream of `ChatCompletionStreamOutput` (text tokens) and `ChatCompletionInputMessage` (tool results)
- Uses OpenAI-compatible base URL under the hood
- Automatically manages tool call/result cycles within a single turn

**MCP transport types:**
| Type | Description | Example URL |
|------|-------------|-------------|
| `sse` | Server-Sent Events (remote) | `https://example.space.hf.space/gradio_api/mcp/sse` |
| `stdio` | Local subprocess (command) | `npx @modelcontextprotocol/server-filesystem` |

### Structured Outputs & JSON Mode (`response_format`)

Beyond tool calling, InferenceClient supports two structured output modes:

```python
# JSON Mode — guarantees valid JSON, no schema enforcement
response = client.chat_completion(
    model="Qwen/Qwen3-32B",
    messages=[{"role": "user", "content": "List 3 books"}],
    response_format={"type": "json_object"},
)

# Structured Outputs (JSON Schema) — guarantees valid JSON matching schema
json_schema = {
    "name": "book",
    "schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "authors": {"type": "array", "items": {"type": "string"}},
            "year": {"type": "integer"}
        },
        "required": ["name", "authors"]
    },
    "strict": True,
}

response = client.chat_completion(
    model="Qwen/Qwen3-32B",
    messages=[{"role": "user", "content": "Extract book info: 'The Great Gatsby' by F. Scott Fitzgerald"}],
    response_format={
        "type": "json_schema",
        "json_schema": json_schema,
    },
)
```

**Structured Output types (from type defs):**
```python
@dataclass
class ChatCompletionInputResponseFormatJSONSchema:
    type: str  # "json_schema"
    json_schema: ChatCompletionInputJSONSchema

@dataclass
class ChatCompletionInputJSONSchema:
    name: str
    description: str | None = None
    schema: dict[str, object] | None = None
    strict: bool | None = None

# Also supported:
# response_format={"type": "text"} — default
# response_format={"type": "json_object"} — JSON mode
```

**Important distinction:**
- `json_object` — Model is told to output JSON, but structure isn't enforced. Faster, less reliable structure.
- `json_schema` — Model output is constrained to the schema. Slower, guaranteed structure.
- Not all providers support both modes — check the Router API's `supports_structured_output` field.

### Provider Discovery for Tool Support

Use the Router API to check which providers support tools for a specific model:

```python
import httpx

resp = httpx.get(
    "https://router.huggingface.co/v1/models/meta-llama/Meta-Llama-3.1-8B-Instruct",
    headers={"Authorization": "Bearer hf_..."},
)
data = resp.json()
for p in data.get("providers", []):
    print(f"{p['provider']:20s} tools={p.get('supports_tools', '?'):5} "
          f"structured={p.get('supports_structured_output', '?'):5} "
          f"status={p.get('status', '?'):10}")
```

### Key Implementation Details from Source

1. **Tool calling follows OpenAI spec exactly** — tools are passed as-is to the provider's API
2. **No client-side tool execution** — InferenceClient does NOT execute tools for you (you must handle tool execution)
3. **The `tool_prompt` parameter** is passed in the `extra_body` — it's appended to the system message on the server side
4. **Parallel tool calls** — supported when the model generates multiple `tool_calls` in a single response; each has a unique `id` and `index`
5. **Tool call IDs** are provider-generated — the client passes them through without modification
6. **Max tool call iterations** — must be handled client-side (no server-side limit in the API)
7. **Error handling**: If a provider doesn't support tools, some silently ignore the parameter, others return errors. Test with your chosen provider.

### Best Practices

1. **Start with `tool_choice="auto"`** — let the model decide when to use tools
2. **Always set `max_tokens`** when using tools — tool call generations often need more tokens than text responses
3. **Include tool descriptions** — well-written descriptions dramatically improve tool selection accuracy
4. **Use specific tool forcing sparingly** — `tool_choice={"type": "function", ...}` is useful for routing known intents but reduces flexibility
5. **Limit tool call loops** — always set a max iteration count (5-10) to prevent infinite loops
6. **Validate tool arguments** — never trust model-generated JSON; validate against your schema before execution
7. **Stream for responsiveness** — streaming provides lower perceived latency even when tool calls are involved
8. **Cache tool definitions** — don't regenerate the same tool list on every call
9. **Provider fallback** — use the provider discovery API to find providers that support tools, then implement a fallback chain
10. **Test tool + structured output combinations** — some providers support both, but the interaction is provider-specific

### Provider Selection Strategy for Tool Calling

```python
from huggingface_hub import InferenceClient, HfApi

def find_tool_providers(model_id: str) -> list[str]:
    """Find providers that support tool calling for a model."""
    api = HfApi()
    info = api.model_info(model_id, expand="inferenceProviderMapping")
    providers = []
    for pm in (info.inference_provider_mapping or []):
        if pm.status == "live":
            providers.append(pm.provider)
    return providers

# Prefer providers known to support tools, fall back to others
TOOL_CAPABLE_PROVIDERS = {"novita", "together", "deepinfra", "fireworks-ai", "groq"}

model_id = "meta-llama/Meta-Llama-3.1-8B-Instruct"
available = find_tool_providers(model_id)
preferred = [p for p in available if p in TOOL_CAPABLE_PROVIDERS]
provider = preferred[0] if preferred else available[0] if available else "auto"

client = InferenceClient(provider=provider)
```

### Resources
- huggingface_hub docs (inference guide): https://huggingface.co/docs/hub/en/guides/inference
- huggingface_hub source: `src/huggingface_hub/inference/_client.py` (chat_completion around line 458)
- Hugging Face Hub Router API: `https://router.huggingface.co/v1`
- Provider selection: https://huggingface.co/settings/inference-providers
- OpenAI function calling docs: https://platform.openai.com/docs/guides/function-calling
- MCP spec: https://modelcontextprotocol.io
- Gradio MCP guide: https://www.gradio.app/guides/building-mcp-server-with-gradio
- Hugging Face API inference detailed parameters: https://huggingface.co/docs/api-inference/detailed_parameters
