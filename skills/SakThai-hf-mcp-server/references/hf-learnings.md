# HF Learnings — MCP Server Enhancements & hf_fs Consolidation

## 2026-07-26: hf-mcp-server-enhancements-hf-fs-consolidation

### Summary
Deep-dive into the July 2026 Hugging Face MCP Server enhancements. The server was significantly updated with a consolidated `hf_fs` tool (single unified interface replacing multiple separate tools), new one-click installation paths via client connector galleries (Claude, VSCode, Cursor, Gemini CLI), native CLI integration commands (`claude mcp add`, `gemini mcp add`), sandbox support for secure execution environments, SEP-2640 skills directory support, `AUTHENTICATE_TOOL` for OAuth challenges, and extensive new environment variables for fine-grained transport control.

### Key Discovery: Architecture Consolidation

The MCP Server moved from exposing ~28 separate tools to a **consolidated architecture** centered around the `hf_fs` tool. The changelog (Jul 22, 2026) states: *"The main change is the new hf_fs tool which provides a single interface to repositories, storage, documentation, papers and more. It's equipped with search and lets your assistant naturally navigate Hugging Face in just over 1,000 tokens."*

This means the old bouquet/mix system of 28 individual tools is being simplified. The `hf_fs` tool handles:
- Hub navigation (models, datasets, Spaces, papers, docs)
- Semantic search across Documents and Spaces
- Filesystem-style operations on repos

The remaining explicit tools are now just four categories:
| Tool | Description |
|------|-------------|
| `hf_fs` | Consolidated Hub navigation + semantic search |
| Contribute Repos | Create repos and write files |
| Sandboxes | Create and manage secure execution environments |
| Run & Manage Jobs | Schedule and monitor HF infrastructure Jobs |

### New Installation Methods

Previously installation required manual `npx @llmindset/hf-mcp-server` commands. Now every major client has:

**Claude Desktop / claude.ai:**
- Connector gallery at `https://claude.ai/settings/connectors` — click "Hugging Face" to add
- Direct link: `https://claude.ai/redirect/.../directory/37ed56d5...`

**Claude Code:**
- `claude mcp add hf-mcp-server -t http https://huggingface.co/mcp?login`
- Or with token: `claude mcp add hf-mcp-server -t http https://huggingface.co/mcp -H "Authorization: Bearer ***"`

**Gemini CLI:**
- `gemini mcp add -t http huggingface https://huggingface.co/mcp?login`
- Extension: `gemini extensions install https://github.com/huggingface/hf-mcp-server`
- Authenticate with `/mcp auth huggingface` inside Gemini

**VSCode:**
- Install from gallery at `https://code.visualstudio.com/mcp`
- Clickable deep link: `vscode:mcp/install?...`
- Manual config in `mcp.json` with URL `https://huggingface.co/mcp` + `Authorization: Bearer` header

**Cursor:**
- One-click install link: `https://cursor.com/en/install-mcp?name=Hugging%20Face&config=...`
- Manual config with same URL + token pattern

**URL parameter:**
- Append `?no_image_content=true` to remove ImageContent blocks from Gradio Spaces MCP responses

### New `AUTHENTICATE_TOOL` Feature

Setting `AUTHENTICATE_TOOL=true` adds an OAuth-based `Authenticate` tool that issues an OAuth challenge when called. This allows agents to authenticate on-the-fly during execution without pre-configured tokens.

### SEP-2640 Skills Directory Support (`HF_SKILLS_DIR`)

The server now supports a local skills distribution in SEP-2640 format:
- Exposes every file as a `skill://` resource
- Supports `resources/directory/read` for scoped navigation
- Advertises `io.modelcontextprotocol/skills` extension with `directoryRead: true`
- Defaults to `/mnt/hf-skills/distribution/latest`
- Designed for HF Space volumes mounted from `hf://buckets/huggingface/skills`

Mount command:
```bash
hf spaces volumes set <org>/<space> -v hf://buckets/huggingface/skills:/mnt/hf-skills:ro
hf spaces variables add <org>/<space> -e HF_SKILLS_DIR=/mnt/hf-skills/distribution/latest
```

### Stateful Connection Management

New environment variables for StreamableHTTP transport:

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_CLIENT_HEARTBEAT_INTERVAL` | 30000ms | How often to check connection health |
| `MCP_CLIENT_CONNECTION_CHECK` | 90000ms | How often to check for stale sessions |
| `MCP_CLIENT_CONNECTION_TIMEOUT` | 300000ms | Remove inactive sessions after this duration |
| `MCP_PING_ENABLED` | true | Enable ping keep-alive for sessions |
| `MCP_PING_INTERVAL` | 30000ms | Interval between ping cycles |

### Complete Environment Variable Reference (Updated)

| Variable | Default | Description |
|----------|---------|-------------|
| `TRANSPORT` | streamableHttpJson | Transport: `stdio`, `streamableHttp`, `streamableHttpJson` |
| `DEFAULT_HF_TOKEN` | — | Default token for STDIO; HTTP ignores this for Authorization |
| `HF_TOKEN` | — | Fallback for STDIO when DEFAULT_HF_TOKEN not set |
| `MCP_ALLOWED_HOSTS` | localhost,127.0.0.1,::1 | Comma-separated host allowlist (supports `*.example.com`) |
| `ALLOW_INTERNAL_ADDRESS_HOSTS` | — | Allow internal DNS resolutions for trusted domains |
| `HF_API_TIMEOUT` | 12500ms | Timeout for HF API requests |
| `USER_CONFIG_API` | — | URL for user settings (defaults to local front-end) |
| `MCP_STRICT_COMPLIANCE` | false | GET 405 rejects in JSON mode vs welcome page |
| `AUTHENTICATE_TOOL` | false | Add OAuth Authenticate tool for on-the-fly auth |
| `SEARCH_ENABLES_FETCH` | false | Auto-enable `hf_doc_fetch` when `hf_doc_search` enabled |
| `DISABLE_TOOLS` | — | Comma-separated tool names to hide from `tools/list` |
| `PROXY_TOOLS_CSV` | — | CSV defining StreamableHTTP proxy tool sources |
| `GRADIO_SKIP_INITIALIZE` | false | Skip Gradio MCP initialize handshake |
| `HF_SKILLS_DIR` | /mnt/hf-skills/distribution/latest | SEP-2640 skills distribution directory |
| `MCP_CLIENT_HEARTBEAT_INTERVAL` | 30000ms | Connection health check interval |
| `MCP_CLIENT_CONNECTION_CHECK` | 90000ms | Stale session check interval |
| `MCP_CLIENT_CONNECTION_TIMEOUT` | 300000ms | Inactive session removal timeout |
| `MCP_PING_ENABLED` | true | Ping keep-alive for sessions |
| `MCP_PING_INTERVAL` | 30000ms | Interval between ping cycles |

### Proxy Tools via CSV

The `PROXY_TOOLS_CSV` mechanism lets you load external MCP endpoints as tools at startup:

```csv
tool_name,url,response_type
papers,https://evalstate-hf-papers.hf.space/mcp,SSE
news,https://example.com/mcp,JSON
```

- Each endpoint is fetched once on startup (initialize + tools/list, 10s timeout)
- Single-tool upstreams → tool name = CSV `tool_name`
- Multi-tool upstreams → tool names = upstream tool names
- Collisions → proxy tool is skipped (warning logged)
- `bouquet=proxy` or `mix=proxy` enables all CSV-loaded tools

### Docker Build

```bash
docker build -t hf-mcp-server .
docker run --rm -p 3000:3000 hf-mcp-server  # StreamableHTTP JSON, port 3000
docker run -i --rm -e TRANSPORT=stdio -p 3000:3000 -e DEFAULT_HF_TOKEN=hf_xxx hf-mcp-server
```

### Web Application Dashboard

All transports start a Management Web interface on `http://localhost:3000/`:
- Switch tools on/off (triggers ToolListChangedNotification for STDIO/StreamableHTTP)
- View tool-call statistics (including rejected calls from DISABLE_TOOLS)
- StreamableHTTP at `http://localhost:3000/mcp`

### Key Changes from Previous Version

| Aspect | Previous (v0.3.x) | Current |
|--------|-------------------|---------|
| Installation | Manual `npx @llmindset/hf-mcp-server` | One-click gallery installs + CLI commands |
| Tool Count | ~28 separate tools | 4 consolidated categories + proxy |
| Hub Access | `hf_fs`, `model_search`, `space_search`, etc. | `hf_fs` (consolidated) |
| Auth | Pre-configured Bearer token only | Optional `AUTHENTICATE_TOOL` OAuth |
| Client Support | STDIO-only config | Claude, Gemini CLI, VSCode, Cursor |
| Skills | Not supported | SEP-2640 skills directory |
| Stateful Transport | Not documented | Full heartbeat/ping/timeout config |

### Implications for SakThai

- The `hf_fs` consolidation means fewer tools to document and configure
- One-click install from gallery eliminates complex setup instructions
- The `AUTHENTICATE_TOOL` enables dynamic auth — agents can get tokens mid-session
- Skills directory (SEP-2640) integration means the SakThai skills can be exposed as MCP resources
- The `?no_image_content=true` parameter is useful for text-only agent setups

### Resources
- https://huggingface.co/changelog/mcp-improvements-jul-26
- https://huggingface.co/docs/hub/en/agents-mcp
- https://huggingface.co/settings/mcp
- https://github.com/huggingface/hf-mcp-server
- https://huggingface.co/mcp
- https://www.gradio.app/guides/building-mcp-server-with-gradio

---

## 2026-07-24: hf-hub-spaces-as-mcp-servers — How Gradio Spaces Become MCP Tools (Topic #201)

### Summary
Deep-dive into the **Spaces as MCP servers** feature — where any Gradio Space on the Hub can expose its functions as callable MCP tools with `mcp_server=True`. Covers architecture, badge system, Dynamic Spaces, client setup, ZeroGPU quotas, and composability patterns. Verified against https://huggingface.co/docs/hub/en/spaces-mcp-servers.

### Architecture

The Spaces-as-MCP system has four layers:

1. **Gradio Space** — a Gradio app deployed to HF Spaces with `demo.launch(mcp_server=True)`
2. **MCP Badge** — grey badge auto-added to MCP-enabled Spaces; clicking it offers "Add to MCP tools"
3. **Hub MCP Settings** — at `https://huggingface.co/settings/mcp`, users manage Space tools, Dynamic Spaces toggle, and Remove Embedded Images toggle
4. **MCP Client** — the AI assistant (Claude Code, Cursor, VS Code, Codex, etc.)

### Creating an MCP-enabled Space

```python
# pip install "gradio[mcp]"
import gradio as gr

def letter_counter(word: str, letter: str) -> int:
    """Count occurrences of a letter in a word.
    Args:
        word: The word to search in
        letter: The letter to count
    Returns:
        Number of times the letter appears
    """
    return word.lower().count(letter.lower())

demo = gr.Interface(fn=letter_counter,
                    inputs=["text", "text"],
                    outputs="number")
demo.launch(mcp_server=True)   # ← single flag enables MCP
```

**Requirements:**
- `gradio[mcp]` package
- Type hints on all function parameters and return values
- Docstrings on exposed functions (become tool descriptions)
- `mcp_server=True` in `demo.launch()`

After pushing to a Gradio Space, the MCP badge appears automatically. Functions become callable MCP tools with typed arguments and descriptions.

### Adding Existing Spaces as Tools

Browse compatible Spaces (grey MCP badge on card), click badge → "Add to MCP tools" → confirm. The Space appears under "Spaces Tools" in MCP settings and becomes available to the client.

### Dynamic Spaces

The **Dynamic Spaces** toggle enables runtime discovery: the AI assistant can find and use MCP-compatible Spaces on-the-fly without manual addition. Ideal for open-ended tasks where the right tool isn't known in advance.

### Remove Embedded Images

Strips images from Gradio Space MCP responses. Useful when the client has limited image rendering or text-only output is preferred.

### ZeroGPU Considerations

- MCP calls to ZeroGPU Spaces consume the user's quota
- Free accounts: limited daily GPU minutes
- PRO accounts: 40 min/day ZeroGPU (8x free), ~600 images/day on FLUX.1-schnell
- Calls fail when quota is exhausted

### Composability: Mixing Spaces as Tools

Any MCP-compatible Space becomes a composable tool. An AI assistant can chain Spaces:
```
User: "Generate a video with audio describing this image."
  → Space A (image understanding) extracts description
  → Space B (video generation) creates video  
  → Space C (TTS) generates narration
  → Combined result returned
```

### Gradio MCP Protocol Details

Under the hood:
1. Generates MCP server manifest from Gradio app function signatures
2. Each `gr.Interface` or `gr.ChatInterface` function becomes an MCP tool
3. Tool name = Python function name, description = docstring
4. Parameters from type hints, return from return annotation
5. Manifest served at `/.well-known/mcp` endpoint
6. Hub's MCP Server proxies calls to the Space's Gradio endpoint

### Client Integration

Works with any MCP-compatible client: Claude Code (`claude mcp add`), Cursor, VS Code, Codex, OpenCode, ChatGPT, Zed. Each client reads the user's MCP settings from the Hub.

### Comparison: Built-in vs Community MCP Tools

| Aspect | Built-in (hf_fs, etc.) | Community Spaces |
|--------|------------------------|-----------------|
| Source | `huggingface/hf-mcp-server` | Any Gradio Space |
| Discovery | Always available | Manual add or Dynamic Spaces |
| Maintenance | HF team | Space author |
| Tool count | 4 categories | Unlimited |
| ZeroGPU | N/A | Consumes user quota |

### Use Cases

1. **Image gen**: FLUX, SDXL as MCP tools
2. **Audio**: TTS, STT, music gen Spaces
3. **Video**: Video diffusion Spaces (e.g., LTX Video)
4. **LLM inference**: Chat Spaces via MCP
5. **Multi-modal chains**: Image → caption → audio pipeline

### Best Practices

- Clear type hints and docstrings on exposed functions
- Descriptive function names (become tool names)
- Test in regular Gradio UI before enabling MCP
- Set appropriate timeouts for long-running tools
- Consider ZeroGPU quota — prefer lightweight models for frequent calls
- Use `pip install "gradio[mcp]"` in requirements.txt

### Sources
- HF Spaces as MCP servers: https://huggingface.co/docs/hub/en/spaces-mcp-servers
- HF MCP settings: https://huggingface.co/settings/mcp
- Gradio MCP guide: https://www.gradio.app/guides/building-mcp-server-with-gradio
- HF Changelog (Jul 22, 2026): https://huggingface.co/changelog/hf-mcp-server
