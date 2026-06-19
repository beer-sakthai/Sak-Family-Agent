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

## 🔌 Consuming External MCP Servers (e.g. Hermes)

The reverse of the above: during `sakthai run`, SakThai auto-loads external MCP
servers from `~/.sakthai/mcp.json` and merges their tools into the loop,
namespaced `<server>__<tool>`. For example, to give SakThai the
[Hermes](https://github.com/) agent's conversation/messaging tools over local
stdio (no API cost):

```json
{
  "mcpServers": {
    "hermes": { "command": "hermes", "args": ["mcp", "serve"] }
  }
}
```

Hermes' tools then appear as `hermes__*`. Confirm discovery with a cost-free
preflight: `sakthai run "list tools" --dry-run`. Full recipes (Hermes both
directions, Composio, skill sync) are in [integrations.md](./integrations.md).

---

## 🧠 Exposing the Agent Loop as an MCP Tool

SakThai also exposes a special `run_agent_loop` tool through its MCP server. 

When an external AI (like Claude or Gemini) calls this tool, it invokes SakThai's own multi-step agent loop. This allows the host AI to delegate complex, multi-iteration tasks (like running commands, reading directories, and self-correcting) to SakThai as a single tool call:

* **Tool Name**: `run_agent_loop`
* **Parameters**:
  * `task` (string, required): The task prompt to run to completion.
  * `model` (string, optional): Model override.
  * `provider` (string, optional): Provider override (`anthropic`, `google`, `openai`, `ollama`).
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
