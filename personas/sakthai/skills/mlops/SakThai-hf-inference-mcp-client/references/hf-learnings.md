# HF Inference MCP Client & Agent Framework — Deep Dive

**Learned:** 2026-07-25 | **Topic:** `hf-inference-mcp-client-agent-framework-deep-dive`
**Sources:** `huggingface_hub` v1.24.0 source code — `inference/_mcp/` module

---

## 1. What is the HF Inference MCP Client?

The Hugging Face Inference MCP Client is a first-class MCP client built directly into `huggingface_hub`. It allows any model accessed through the HF Inference API to connect to MCP (Model Context Protocol) servers — discovering tools, calling them, and feeding results back into the chat loop.

Unlike the **HF Hub MCP Server** (`SakThai-hf-mcp-server`), which *exposes* the HF Hub as an MCP server, this is a *client* that *consumes* MCP servers from within the HF Inference ecosystem.

**Key difference:** The Hub MCP Server lets external MCP clients access HF Hub resources. The Inference MCP Client lets HF models access external MCP tools.

## 2. Module Architecture

```
huggingface_hub/inference/_mcp/
├── __init__.py          # Empty
├── _cli_hacks.py        # Process group patching for CLI Ctrl+C handling
├── agent.py             # Agent class — multi-turn loop over MCPClient
├── cli.py               # `hf app` CLI entry point
├── constants.py         # Default agent config, system prompts, exit tools
├── mcp_client.py        # MCPClient — core client (395 lines)
├── types.py             # TypedDict config schemas
└── utils.py             # Result formatting, config loading
```

### Public API

`MCPClient` is exported at the top level of `huggingface_hub`:
```python
from huggingface_hub import MCPClient
```

The `Agent` class and CLI are accessible through the inference module but not top-level exported (they're experimental).

## 3. MCPClient — Core Client

### 3.1 Constructor

```python
MCPClient(
    *,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
)
```

Creates an `AsyncInferenceClient` internally. At least one of `model` or `base_url` is required.

- `model`: HF model ID (e.g., `"meta-llama/Meta-Llama-3-8B-Instruct"`)
- `provider`: Inference provider (defaults to `"auto"` — user's provider order from https://hf.co/settings/inference-providers)
- `base_url`: Custom endpoint URL (bypasses HF providers)
- `api_key`: Auth token (defaults to local HF token)

### 3.2 Context Manager

`MCPClient` is an async context manager:
```python
async with MCPClient(model="Qwen/Qwen2.5-72B-Instruct") as client:
    ...
```

On enter: initializes the inference client sub-resources.
On exit: closes the inference client and `AsyncExitStack` (which manages MCP connections).

### 3.3 `add_mcp_server()` — Connecting to MCP Servers

```python
async def add_mcp_server(
    self,
    type: ServerType,  # "stdio" | "sse" | "http"
    **params           # Server-specific parameters
) -> None:
```

This is the core method that connects to an MCP server and discovers its tools.

**Stdio servers** (local process):
```python
await client.add_mcp_server(
    type="stdio",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/path"],
    env={"KEY": "value"},
    cwd="/working/dir",
    allowed_tools=["read_file", "write_file"],  # optional tool filter
)
```

**SSE servers** (remote streaming):
```python
await client.add_mcp_server(
    type="sse",
    url="https://mcp.example.com/sse",
    headers={"Authorization": "Bearer token"},
    timeout=30.0,
    sse_read_timeout=300.0,
    allowed_tools=["search", "fetch"],
)
```

**HTTP servers** (StreamableHTTP):
```python
await client.add_mcp_server(
    type="http",
    url="https://mcp.example.com",
    headers={"Authorization": "Bearer token"},
    timeout=timedelta(seconds=30),
    sse_read_timeout=timedelta(minutes=5),
    terminate_on_close=True,
    allowed_tools=["text", "embed"],
)
```

#### Internal flow:
1. Creates appropriate MCP transport (`stdio_client`, `sse_client`, or `streamablehttp_client`)
2. Creates a `ClientSession` with the transport streams, identifying as `"huggingface_hub.MCPClient"` with the library version
3. Calls `session.initialize()` to establish the MCP connection
4. Lists available tools via `session.list_tools()`
5. Optionally filters tools by `allowed_tools`
6. Stores each tool → session mapping in `self.sessions` dict
7. Converts each MCP tool to `ChatCompletionInputTool` and appends to `self.available_tools`

**Tool name conflict resolution:** If a tool name is already registered (from a different server), it's skipped with a warning. First-come-first-served.

### 3.4 `process_single_turn_with_tools()` — Chat + Tool Execution

```python
async def process_single_turn_with_tools(
    self,
    messages: list[Union[dict, ChatCompletionInputMessage]],
    exit_loop_tools: Optional[list[ChatCompletionInputTool]] = None,
    exit_if_first_chunk_no_tool: bool = False,
) -> AsyncIterable[Union[ChatCompletionStreamOutput, ChatCompletionInputMessage]]:
```

This is the heart of the MCP client. It:

1. **Streams a chat completion** with the model, including all available MCP tools as `tool_choice="auto"` function definitions
2. **Yields streaming chunks** to the caller as they arrive
3. **Accumulates tool calls** — if the model decides to use tools, it streams the tool call arguments across multiple chunks
4. **Executes tool calls** — for each tool call, finds the corresponding MCP session and calls `session.call_tool(name, args)`
5. **Yields tool results** — formats the tool output and yields it back
6. **Supports early exit** — if `exit_if_first_chunk_no_tool` is True and the first 2 chunks contain no tool calls, it returns immediately (used by the Agent to detect when the agent wants to respond directly)

#### Stream lifecycle

```
User messages → model streaming → tool call detected → call MCP tool → yield result
                                                                             ↓
                                                            (loop continues if Agent)
```

#### Tool call handling

The method handles:
- **Multiple parallel tool calls** — the model can request several tool calls in one turn
- **Streaming arguments** — tool call arguments are accumulated across chunks, with `final_tool_calls[idx].function.arguments += ...`
- **JSON parse errors** — if the model generates invalid JSON for tool arguments, it yields an error message as a tool result
- **MCP execution errors** — if `session.call_tool()` raises an exception, it yields the error message
- **Missing sessions** — if a tool name has no registered session (shouldn't happen but handled defensively), yields an error
- **Exit loop tools** — if a called tool matches an `exit_loop_tool`, the generator yields the result and returns (stops)

### 3.5 State Management

- `self.sessions: dict[str, ClientSession]` — maps tool names to MCP sessions (each tool → its server session)
- `self.available_tools: list[ChatCompletionInputTool]` — all discovered and registered tools
- `self.exit_stack: AsyncExitStack` — manages all async context managers (transports, sessions)
- `self.client: AsyncInferenceClient` — the underlying inference client

Multiple calls to `add_mcp_server()` accumulate tools. There is no `remove_mcp_server()` method.

## 4. Agent — Multi-Turn Agent Loop

`Agent` extends `MCPClient` to create a multi-turn agent:

```python
class Agent(MCPClient):
    def __init__(
        self,
        *,
        model: str | None = None,
        servers: Iterable[ServerConfig],
        provider: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        prompt: str | None = None,
    ):
```

### 4.1 Configuration

- **`servers`**: List of MCP server configurations (dicts with `type`, `command`/`url`, `args`, `env`, etc.)
- **`prompt`**: System prompt. Defaults to `DEFAULT_SYSTEM_PROMPT` from constants.py:
  > "You are an agent - please keep going until the user's query is completely resolved... You MUST plan extensively before each function call..."

- **Default agent config** (when no agent_path is given):
  ```json
  {
    "model": "Qwen/Qwen2.5-72B-Instruct",
    "provider": "novita",
    "servers": [
      {"type": "stdio", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "~/Desktop"]},
      {"type": "stdio", "command": "npx", "args": ["@playwright/mcp@latest"]}
    ]
  }
  ```

### 4.2 `load_tools()` - Batch Server Connection

```python
async def load_tools(self) -> None:
    for cfg in self._servers_cfg:
        await self.add_mcp_server(**cfg)
```

Connects to all configured servers and discovers their tools in sequence.

### 4.3 `run()` - The Agent Loop

```python
async def run(
    self,
    user_input: str,
    *,
    abort_event: Optional[asyncio.Event] = None,
) -> AsyncGenerator[Union[ChatCompletionStreamOutput, ChatCompletionInputMessage], None]:
```

The agent loop:

1. Appends `user_input` as a user message to `self.messages`
2. Enters a while loop (max 10 turns, from `MAX_NUM_TURNS` constant)
3. Calls `self.process_single_turn_with_tools()` with `exit_loop_tools` (task_complete, ask_question) and `exit_if_first_chunk_no_tool` enabled after the first turn
4. After the turn, checks:
   - If the last message was a tool call to `task_complete` or `ask_question` → exit loop
   - If the last message is NOT a tool result → exit loop (model responded directly)
   - If max turns reached → exit loop
5. Otherwise loops back for another turn of tool execution

#### Exit Tools

Two built-in tools signal the agent to stop:
- **`task_complete`**: Called when the task is fully resolved
- **`ask_question`**: Called when the agent needs more info from the user

Both have empty parameters — they're signals, not data carriers.

### 4.4 Usage Pattern

```python
async with Agent(
    model="Qwen/Qwen2.5-72B-Instruct",
    servers=[{"type": "stdio", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]}],
) as agent:
    await agent.load_tools()
    async for result in agent.run("Read the file /tmp/notes.txt and summarize it"):
        if isinstance(result, ChatCompletionStreamOutput):
            print(result.choices[0].delta.content or "", end="")
```

## 5. CLI — `hf app`

The `hf app` CLI provides a ready-to-use agent runner:

### Usage

```bash
# Run with default agent (Qwen 72B + filesystem + Playwright)
hf app

# Run with a local config
hf app path/to/agent-folder/
hf app path/to/config.json

# Run with a built-in config from tiny-agents dataset
hf app agent-name
```

### Configuration Format

The agent config is a JSON file (`agent.json`) following the `AgentConfig` type:

```json
{
  "model": "Qwen/Qwen2.5-72B-Instruct",
  "provider": "novita",
  "apiKey": "${input:MY_API_KEY}",
  "inputs": [
    {"id": "MY_API_KEY", "description": "Novita API key", "type": "text", "password": true}
  ],
  "servers": [
    {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
      "allowed_tools": ["read_file"]
    },
    {
      "type": "http",
      "url": "https://my-mcp-server.com",
      "headers": {"Authorization": "Bearer ${input:MY_API_KEY}"}
    }
  ]
}
```

#### Input Variables

Configs support `${input:VAR_NAME}` syntax for injecting values at startup:
- At launch, prompts user for each input variable
- Values are substituted into `env` (stdio), `headers` (SSE/HTTP), and `apiKey` fields
- If left empty, reads from the corresponding environment variable

### CLI Architecture

```python
async def run_agent(agent_path: str | None) -> None:
    config, prompt = _load_agent_config(agent_path)
    
    # Handle inputs (env variable injection)
    resolved_inputs = await prompt_for_inputs(config.get("inputs", []))
    
    # Create agent with resolved config
    async with Agent(model=..., servers=..., prompt=prompt) as agent:
        await agent.load_tools()
        # Interactive loop: read input → run agent → print output
```

The CLI patches `anyio.open_process` to set `start_new_session=True` (Unix) or `CREATE_NEW_PROCESS_GROUP` (Windows), preventing stdio MCP processes from being killed by Ctrl+C.

## 6. Result Formatting

The `format_result()` function converts `mcp.types.CallToolResult` into human-readable strings:

| Content Type | Formatting |
|---|---|
| `text` | Plain text content |
| `image` | `[Binary Content: Image {mimeType}, {size} bytes]` + completion note |
| `audio` | `[Binary Content: Audio {mimeType}, {size} bytes]` + completion note |
| `resource` (text) | Extracted text content |
| `resource` (blob) | `[Binary Content ({uri}): {mimeType}, {size} bytes]` + completion note |

Binary content is intentionally NOT embedded in the text stream — the format signals completion without including raw bytes.

## 7. Constants & Defaults

| Constant | Value | Description |
|---|---|---|
| `DEFAULT_SYSTEM_PROMPT` | Multi-line agent prompt | Instructs model to plan, use tools, and keep going until task is complete |
| `MAX_NUM_TURNS` | `10` | Maximum agent loop iterations |
| `FILENAME_CONFIG` | `"agent.json"` | Config file name |
| `PROMPT_FILENAMES` | `("PROMPT.md", "AGENTS.md")` | Optional prompt file names |
| `DEFAULT_REPO_ID` | `"tiny-agents/tiny-agents"` | HF dataset for built-in agent configs |
| `TASK_COMPLETE_TOOL` | Function tool with no params | Signals task completion |
| `ASK_QUESTION_TOOL` | Function tool with no params | Requests user input |

## 8. Integration with HF Inference Providers

The MCP Client uses `AsyncInferenceClient` under the hood, which supports:

- **Any HF model** available through Inference Providers (serverless)
- **Custom endpoints** via `base_url` (Inference Endpoints, local servers)
- **Provider routing** — `provider="auto"` picks the cheapest/fastest available provider
- **API key auth** — use your own provider API key for direct access
- **Streaming** — the entire chat completion is streamed, enabling real-time output

The tool calling integration follows OpenAI's tool format (`ChatCompletionInputTool`), which is supported by most modern HF-provided models (Qwen, Llama, etc.).

## 9. Key Insights

1. **MCPClient is async-only** — requires `async with` and `await` for all operations
2. **Tool deduplication** — if two servers provide tools with the same name, only the first one is registered (warning logged)
3. **No per-server remove** — once a server is added, its tools are available for the lifetime of the MCPClient
4. **`allowed_tools` filtering** — happens server-side at connection time, not per-request
5. **Exit loop tools** are a pattern, not a protocol — they signal the Agent loop to stop by matching tool names (`task_complete`, `ask_question`)
6. **Early exit optimization** — if the model responds without tools in the first 2 chunks and `exit_if_first_chunk_no_tool` is True, the loop short-circuits (avoids waiting for full generation)
7. **MCPClient is separate from the HF MCP Server** — the client connects TO MCP servers, while the server exposes HF Hub AS an MCP server
8. **The default config uses Novita as provider** — but any HF-supported provider or custom endpoint works
9. **Binary content from tools is summarized, not embedded** — prevents token/bandwidth waste
10. **The `hf app` CLI is a thin wrapper** — the `Agent` class can be used programmatically without the CLI

## 10. Comparison: MCPClient vs. Other Tool-Use Approaches

| Aspect | MCPClient + Agent | smolagents (CodeAgent) | Direct Chat Completions |
|--------|-------------------|----------------------|------------------------|
| Tool source | Any MCP server | Python functions | Must be in chat API |
| Multi-turn | Built-in (Agent) | Built-in | Manual loop |
| Async | Native async | Sync or async | Configurable |
| Server types | stdio, SSE, HTTP | N/A (Python only) | N/A |
| Config format | JSON (agent.json) | Python code | Programmatic |
| CLI | `hf app` | `smolagents` CLI | None |
| Dependencies | `mcp` package | None extra | None |

## 11. Practical Patterns

### Pattern 1: Single-turn tool use (no agent loop)

```python
async with MCPClient(model="Qwen/Qwen2.5-72B-Instruct") as client:
    await client.add_mcp_server(type="stdio", command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"])
    messages = [{"role": "user", "content": "List files in /tmp"}]
    async for chunk in client.process_single_turn_with_tools(messages):
        # handle streaming output
        pass
```

### Pattern 2: Custom system prompt agent

```python
async with Agent(
    model="meta-llama/Meta-Llama-3-70B-Instruct",
    servers=[{"type": "stdio", "command": "my-tool-server"}],
    prompt="You are a data analysis assistant. Use the available tools to load, process, and visualize data.",
) as agent:
    await agent.load_tools()
    async for output in agent.run("Analyze the CSV file at /data/sales.csv"):
        print(output)
```

### Pattern 3: Multiple MCP servers

```python
async with MCPClient(model="Qwen/Qwen2.5-72B-Instruct") as client:
    # Connect multiple servers
    await client.add_mcp_server(type="stdio", command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/data"])
    await client.add_mcp_server(type="stdio", command="npx",
        args=["-y", "@playwright/mcp@latest"])
    # All tools from both servers are available
    ...
```

### Pattern 4: Error handling in tool calls

Tool errors (MCP failures, invalid JSON, missing tools) are captured and returned as tool messages — they DON'T crash the client. The model sees the error and can decide how to proceed.

## 12. References

- Source: `huggingface_hub/inference/_mcp/mcp_client.py` (395 lines)
- Source: `huggingface_hub/inference/_mcp/agent.py` (100 lines)
- Source: `huggingface_hub/inference/_mcp/cli.py` (245 lines)
- Source: `huggingface_hub/inference/_mcp/constants.py` (81 lines)
- Source: `huggingface_hub/inference/_mcp/types.py` (45 lines)
- Source: `huggingface_hub/inference/_mcp/utils.py` (130 lines)
- Source: `huggingface_hub/inference/_mcp/_cli_hacks.py` (88 lines)
- Public export: `huggingface_hub.__init__.py` line 562, 797, 1745
- Default agent dataset: https://huggingface.co/datasets/tiny-agents/tiny-agents
- MCP specification: https://modelcontextprotocol.io
- Tool use docs: https://huggingface.co/docs/huggingface_hub/main/en/guides/inference#tool-use-and-agent
