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
