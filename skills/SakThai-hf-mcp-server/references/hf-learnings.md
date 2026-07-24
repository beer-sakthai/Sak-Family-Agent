# HF Learnings — Spaces as MCP Servers: Deep Dive (2026-07-24)

## 2026-07-24: hf-hub-spaces-as-mcp-servers-deep-dive — Complete Workflow Reference

### Summary
Deep-dive into the Hugging Face Spaces as MCP servers feature — the **zero-code** way to expose any public Gradio Space with an MCP badge as a callable tool in any MCP-compatible client (Claude Desktop, Cursor, VS Code, Claude Code, Cline). Also covers the developer workflow for building custom MCP servers with Gradio.

This is distinct from the `hf-mcp-server` CLI tool (which connects the whole HF Hub via 28+ tools). Spaces-as-MCP-servers is about **individual Spaces** acting as discrete MCP tools that can be mixed and matched.

### Sources
- Official Hub docs: https://huggingface.co/docs/hub/en/spaces-mcp-servers
- Gradio MCP guide: https://www.gradio.app/guides/building-mcp-server-with-gradio
- MCP Settings page: https://huggingface.co/settings/mcp
- Browse MCP Spaces: https://huggingface.co/spaces?mcp=true
- Changelog: https://huggingface.co/changelog/hf-mcp-server

---

## 1. The Core Concept: Zero-Code Spaces → MCP Tools

Any **public Gradio Space** that has a visible **MCP badge** (grey badge on Space card) can be added to your MCP client as a tool **without writing a single line of code**. The Space's `launch(mcp_server=True)` automatically generates an MCP schema at `/gradio_api/mcp/schema` that lists all callable functions with their type hints and docstrings as tool definitions.

Key differentiator: Unlike the `hf-mcp-server` (which connects the entire HF Hub through one server), Spaces-as-MCP-servers treats **each Space as an individual tool**. You can add as many Spaces as you want, and they appear as separate tools in your client.

---

## 2. User Workflow: Adding Spaces to Your MCP Tools

### Prerequisites
- A Hugging Face token with **READ** permissions
- An MCP-compatible client (Claude Desktop, Cursor, VS Code, Claude Code, Cline, Zed, etc.)

### Step 1: Configure your MCP Client
1. Go to https://huggingface.co/settings/mcp
2. Select your MCP client from the list (VS Code, Cursor, Claude Code, etc.)
3. Follow the setup instructions — the page generates the exact configuration snippet for your client

### Step 2: Find a Compatible Space
1. Browse https://huggingface.co/spaces?mcp=true
2. Look for the **grey MCP badge** on any Space card
3. The badge indicates the Space is MCP-compatible (has `mcp_server=True` in its launch config)

### Step 3: Add the Space
1. Click the **MCP badge** on the Space card
2. Choose **"Add to MCP tools"**
3. Confirm when asked
4. The Space should appear in your MCP Server settings under the "Spaces Tools" section

### Step 4: Use the Tool
1. If your MCP client is configured correctly, the Space's tools are **available instantly**
2. Most MCP clients list what tools are currently loaded — verify the Space appears
3. The LLM can now call the Space's functions as tools, with the docstrings and type hints informing its usage

### ZeroGPU Considerations
- For ZeroGPU Spaces, your daily quota is consumed when the tool is called
- **Free users**: ~5 minutes of daily ZeroGPU quota
- **PRO users**: 40 minutes of daily quota (8× more), e.g., up to 600 FLUX.1-schnell images/day

---

## 3. Developer Workflow: Building an MCP-Compatible Space

### Minimal Setup
```python
# 1. Install with MCP extras
# pip install "gradio[mcp]"

# 2. Write your app with type hints and docstrings
import gradio as gr

def letter_counter(word: str, letter: str) -> int:
    """Count occurrences of a letter in a word.

    Args:
        word: The word to search in
        letter: The letter to count

    Returns:
        Number of times the letter appears in the word
    """
    return word.lower().count(letter.lower())

demo = gr.Interface(
    fn=letter_counter,
    inputs=["text", "text"],
    outputs="number",
)
demo.launch(mcp_server=True)  # <-- THIS enables MCP
```

### How Tool Conversion Works
| Aspect | Behavior |
|--------|----------|
| **Function name** | Becomes the MCP tool name |
| **Docstring** | Becomes the tool description for the LLM |
| **Type hints** | Define the input parameter schema |
| **Default values** | From `gr.Textbox("default")` — used if LLM doesn't specify |
| **Multiple functions** | Each Gradio event handler becomes a separate MCP tool |

### Environment Variable Alternative
```bash
export GRADIO_MCP_SERVER=True
# Then launch normally — no code change needed
```

### Schema Endpoint
- **URL**: `http://your-server:port/gradio_api/mcp/schema`
- **Visual**: "View API" link in the Gradio app footer → click "MCP" tab
- **Config URL** for MCP clients: `http://your-server:port/gradio_api/mcp/`

### Converting an Existing Space
1. **Duplicate** the Space (if not yours)
2. **Add docstrings** to functions you want exposed as tools
3. **Add** `mcp_server=True` in `demo.launch()`
4. Re-deploy — the MCP badge appears automatically

---

## 4. Authentication Patterns

### Public Spaces
No auth needed — the Space's tools are publicly callable.

### Private Spaces
Provide your HF token in the MCP client config:
```json
{
  "mcpServers": {
    "my-private-space": {
      "url": "https://username-my-private-space.hf.space/gradio_api/mcp/",
      "headers": {
        "Authorization": "Bearer YOUR_HF_TOKEN"
      }
    }
  }
}
```

### gr.Request — Access Request Headers
```python
def my_tool(x: str, request: gr.Request):
    """Tool that inspects incoming request headers."""
    return str(dict(request.headers))
```

### gr.Header — Extract Specific Header
```python
def make_api_request(
    prompt: str,
    x_api_token: gr.Header
):
    """Make a request authenticated with the caller's token."""
    return "Hello!" if not x_api_token else "Hello with token!"
```
The MCP connection UI automatically displays which headers the server expects when `gr.Header` is used.

---

## 5. Performance Tuning

| Setting | Effect | Trade-off |
|---------|--------|-----------|
| `queue=False` in event handlers | Up to **10× throughput** increase | Disables progress notifications |
| `queue=True` (default) | Shows progress for long tasks | Higher latency per request |

Rule of thumb: short tasks (analytics, transforms) → `queue=False`; long tasks (video gen, batch processing) → `queue=True`.

---

## 6. STDIO Transport for File Uploads

Gradio automatically generates an **additional STDIO-based MCP server** for file uploads:
- Can upload files to any remote Gradio app
- Returns a URL usable for subsequent tool calls
- Useful when the client doesn't support URL-based file references

By default, the Gradio MCP server accepts input images/files as full URLs (`https://...`).

---

## 7. Hub MCP Settings Integration

The full ecosystem uses **https://huggingface.co/settings/mcp** as the central hub:

| Feature | Description |
|---------|-------------|
| **MCP Client config** | Select your client, get exact config snippet |
| **Spaces Tools section** | All your added Spaces listed here |
| **Dynamic Spaces** | Option to dynamically discover and call MCP Spaces at runtime |
| **Remove Embedded Images** | Strip Gradio image output (useful for limited image support) |
| **Authentication** | Token-based auth integration with your HF account |

### One-Click Client Connections
MCP-compatible clients can connect via:
| Client | Connection Method |
|--------|-----------------|
| **Claude Desktop** | Connector gallery at `https://claude.ai/settings/connectors` |
| **Claude Code** | `claude mcp add hf-mcp-server -t http https://huggingface.co/mcp?login` |
| **Cursor** | One-click install from https://cursor.com |
| **VS Code** | Gallery at `https://code.visualstudio.com/mcp` |
| **Gemini CLI** | `gemini mcp add -t http huggingface https://huggingface.co/mcp?login` |

---

## 8. Architecture: How MCP Server Works in Gradio

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Client                            │
│    (Claude Desktop, Cursor, VS Code, Cline, etc.)        │
└─────────────┬───────────────────────────────────────────┘
              │ HTTP or STDIO
              ▼
┌─────────────────────────────────────────────────────────┐
│              Gradio MCP Server                            │
│              (your-app.hf.space)                          │
├─────────────────────────────────────────────────────────┤
│  Discover:  GET  /gradio_api/mcp/schema  → Tool list     │
│  Call:       POST /gradio_api/mcp/       → Tool execute  │
│  File I/O:   STDIO transport (auto-generated)            │
├─────────────────────────────────────────────────────────┤
│  Tool 1: letter_counter(word: str, letter: str) → int    │
│  Tool 2: generate_image(prompt: str) → file             │
│  ...                                                    │
└─────────────────────────────────────────────────────────┘
```

### MCP URL Structure
| Endpoint | Purpose |
|----------|---------|
| `https://username-space-name.hf.space/gradio_api/mcp/` | MCP server endpoint (add to client config) |
| `https://username-space-name.hf.space/gradio_api/mcp/schema` | JSON schema of all available tools |
| `https://username-space-name.hf.space/gradio_api/mcp/sse` | SSE (Server-Sent Events) transport |

---

## 9. Creative Use Cases: Mixing Spaces

Since HF Spaces is the largest directory of AI apps, you can:

- **Image gen + TTS**: Use FLUX.1-schnell to generate an image, then feed it to a TTS Space for audio description
- **Video + Audio**: Use LTX-Video to generate a clip, then Chatterbox for voice-over (demoed officially)
- **OCR + Translation**: Extract text from an image, then translate to any language
- **Classification + Visualization**: Classify an image, then create a data visualization of the results

The official docs demonstrate this with Lightricks/ltx-video-distilled + ResembleAI/Chatterbox in Claude Code.

---

## 10. Comparison: HF MCP Server vs Spaces MCP Tools

| Feature | HF MCP Server (`hf-mcp-server`) | Spaces MCP Tools (this doc) |
|---------|----------------------------------|------------------------------|
| **Scope** | Full Hub: search models, datasets, Spaces, papers | Individual Space as one tool |
| **Added by** | Pasting generated config at settings/mcp | Clicking MCP badge on Space card |
| **Tools exposed** | 28 built-in tools (hf_fs, sandbox, jobs, etc.) | Space's own functions |
| **Customization** | Proxy tools, bouquets, env vars | Just the Space's API |
| **Best for** | Hub exploration, repo management, compute | Specific AI tasks (gen, analysis, processing) |
| **Auth** | Token in config | Public: none; Private: Bearer token |
| **ZeroGPU** | N/A (uses HF infra) | Space's own quota consumed |

Both can be used **together** — the HF MCP Server for Hub search/management, Spaces MCP tools for task-specific AI.

---

## 11. Key URLs Reference

| Resource | URL |
|----------|-----|
| MCP Settings (central config) | https://huggingface.co/settings/mcp |
| Browse MCP-compatible Spaces | https://huggingface.co/spaces?mcp=true |
| Hub docs: Spaces as MCP servers | https://huggingface.co/docs/hub/en/spaces-mcp-servers |
| Gradio guide: Building MCP server | https://www.gradio.app/guides/building-mcp-server-with-gradio |
| HF MCP Server docs | https://huggingface.co/docs/hub/en/agents-hf-mcp-server |
| MCP changelog | https://huggingface.co/changelog/hf-mcp-server |
| HF MCP Server (GitHub) | https://github.com/huggingface/hf-mcp-server |
| Gradio MCP package | `pip install "gradio[mcp]"` |

---

## 12. Changelog / Recent Updates

- **2026-07-24**: Full docs published for "Spaces as MCP servers" workflow
- **2026-07-22**: HF MCP Server v2.0 consolidation with hf_fs, one-click gallery installs
- **2026-06+**: Gradio adds `mcp_server=True` parameter to `launch()`
- **2026-05+**: Gradio supports `gr.Header` for clean header extraction
- **2026-04+**: MCP badge appears on compatible Spaces; `spaces?mcp=true` filter live
- **2026-03+**: Initial MCP integration in Gradio (experimental)
