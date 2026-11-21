# Runtime Integrations & Local Execution

SakThai can be run directly from the command line, integrated into third-party AI interfaces (Claude CLI, Gemini CLI) as an MCP server, or executed offline using local models.

---

## 💻 Integration with Claude CLI

You can expose the SakThai tools directly to Claude CLI (built into `claude-code`).

Add the following configuration to `~/.claude/config.json`:

```json
{
  "mcpServers": {
    "sakthai": {
      "command": "sakthai",
      "args": ["mcp"]
    }
  }
}
```

If you are running in a virtual environment, use:

```json
{
  "mcpServers": {
    "sakthai": {
      "command": "uv",
      "args": ["run", "--package", "sakthai-agent", "sakthai", "mcp"]
    }
  }
}
```

Once configured, Claude CLI will have access to all of SakThai's memory tools (`learn`, `recall`, `search`, `forget`).

---

## ♊ Integration with Gemini CLI

To connect Gemini CLI to SakThai, register it in your active `.mcp.json` config:

```json
{
  "mcpServers": {
    "sakthai": {
      "command": "sakthai",
      "args": ["mcp"]
    }
  }
}
```

This lets Gemini CLI read from and write to the same shared memory database (`~/.sakthai/memory.db`).

---

## 🔌 Consuming External MCP Servers

The reverse of the above: during `sakthai run`, SakThai auto-loads external MCP
servers from `~/.sakthai/mcp.json` and merges their tools into the loop,
namespaced `<server>__<tool>`. For example, to give SakThai external
agent conversation/messaging tools over local stdio (no API cost):

```json
{
  "mcpServers": {
    "external-tools": { "command": "external-cli", "args": ["mcp", "serve"] }
  }
}
```

The tools then appear as `external-tools__*`. Confirm discovery with a cost-free
preflight: `sakthai run "list tools" --dry-run`. Full recipes (integrations,
Composio, skill sync) are in [integrations.md](./integrations.md).

---

## 🧠 Exposing the Agent Loop as an MCP Tool

SakThai also exposes a special `run_agent_loop` tool through its MCP server.

When an external AI (like Claude or Gemini) calls this tool, it invokes SakThai's own multi-step agent loop. This allows the host AI to delegate complex, multi-iteration tasks (like running commands, reading directories, and self-correcting) to SakThai as a single tool call:

* **Tool Name**: `run_agent_loop`
* **Parameters**:
  * `task` (string, required): The task prompt to run to completion.
  * `model` (string, optional): Model override.
  * `provider` (string, optional): Provider override (`anthropic`, `google`, `openai`, `ollama`, `gateway`).
  * `max_iterations` (int, optional): Tool-use loop iteration limit.

---

## 🦙 Local Models & Ollama (Self-Driving, No API Key)

You can run SakThai offline without external API keys by pointing it to Ollama or any OpenAI-compatible server.

### Prerequisites

Ensure you have Ollama running locally. For example, to use Qwen 2.5 Coder:

```bash
ollama run qwen2.5-coder:7b
```

### Running with CLI Choice

To force local execution via the CLI:

```bash
sakthai run "your task" --provider ollama --model qwen2.5-coder:7b
```

### Environment Variables

Alternatively, you can configure your environment to use an OpenAI-compatible/Ollama endpoint:

* `OLLAMA_HOST`: Set to your Ollama endpoint (defaults to `http://127.0.0.1:11434`). The IPv4 literal avoids a `Connection refused` on hosts where `localhost` resolves to IPv6 `::1` but Ollama binds IPv4 only.
* `OPENAI_API_BASE` / `OPENAI_BASE_URL`: Point to any other OpenAI-compatible gateway (e.g., LocalAI, vLLM, DeepSeek).
* `OPENAI_API_KEY`: Provide a key if the endpoint requires one (defaults to `"nokey"`).

---

## 🌐 AI Gateways (OpenRouter, LiteLLM, Vercel, Cloudflare)

The `gateway` provider is a first-class route to any OpenAI-compatible **AI
gateway** — a proxy that fronts many upstream models behind one endpoint
(OpenRouter, LiteLLM, the Vercel AI Gateway, the Cloudflare AI Gateway, …). It
is configured independently of the `OPENAI_*` and `OLLAMA_*` variables, so a
gateway and a direct OpenAI key can coexist without one shadowing the other.

### Environment Variables

* `SAKTHAI_GATEWAY_URL`: Base URL of the gateway (required), e.g.
  `https://openrouter.ai/api/v1`.
* `SAKTHAI_GATEWAY_API_KEY`: Bearer token for the gateway (defaults to `"nokey"`
  for keyless gateways).

### Running

Select the gateway explicitly, or via a `gateway`-prefixed model name:

```bash
export SAKTHAI_GATEWAY_URL="https://openrouter.ai/api/v1"
export SAKTHAI_GATEWAY_API_KEY="sk-or-..."

# explicit provider flag
sakthai run "your task" --provider gateway --model anthropic/claude-3.5-sonnet

# or auto-detected from a gateway/* model name
sakthai run "your task" --model gateway/anthropic/claude-3.5-sonnet
```

When no other provider is selected, SakThai also falls back to the gateway if
`SAKTHAI_GATEWAY_URL` is set and no Anthropic/Google/OpenAI credentials are
present.

---

## 🚪 Runtime Gateway (OpenAI-Compatible & REST API)

SakThai includes a built-in, multi-threaded Runtime Gateway (`sakthai.gateway`) that exposes an OpenAI-compatible API and REST endpoints for all 6 personas and agent tools.

### Running the Gateway

```bash
# Start the live Runtime Gateway on default port 8080
sakthai gateway serve

# Or customize host, port, authentication token, and CORS
sakthai gateway serve --host 127.0.0.1 --port 8080 --token secret123 --cors "*"
```

Or run via the standalone script:

```bash
python scripts/serve_gateway.py --port 8080
```

### Endpoints

- `GET /health` or `GET /v1/health`: Gateway health status, active personas, uptime.
- `GET /v1/models`: Returns available models/personas (`sakthai`, `sakking`, `saksee`, `sakjules`, `saksit`, `saktan`, plus tier presets like `gemini-2.5-flash`).
- `POST /v1/chat/completions`: Standard OpenAI chat completions endpoint (supports both non-streaming JSON and streaming SSE `stream: true`).
- `GET /v1/personas`: Persona metadata, handles, roles, and default models.
- `GET /v1/personas/<name>`: Specific persona details.
- `GET /v1/tools`: Registered tools in OpenAI function/tool format.
- `POST /v1/tools/execute`: Executes a tool with DataLossGuardrail protection.
- `GET /api/status`: System status check.
- `GET /api/saksee/status`: SakSee dashboard compatibility status check.

### Connecting External Clients

Any OpenAI-compatible client (Cursor, Claude Code, Aider, OpenCode, Python OpenAI SDK, curl) can target the gateway:

```bash
export OPENAI_BASE_URL="http://localhost:8080/v1"
export OPENAI_API_KEY="$SAKTHAI_GATEWAY_BEARER_TOKEN"  # or leave empty if unauthenticated

# Query available models via curl
curl http://localhost:8080/v1/models

# Chat completion with streaming
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "sakthai",
    "messages": [{"role": "user", "content": "Hello SakThai!"}],
    "stream": true
  }'
```

### CLI Inspection Commands

```bash
# Check gateway health
sakthai gateway status --url http://127.0.0.1:8080

# List models served by the gateway
sakthai gateway models --url http://127.0.0.1:8080

# Quick chat test via the gateway
sakthai gateway chat "Tell me your role" --model sakjules --stream
```

