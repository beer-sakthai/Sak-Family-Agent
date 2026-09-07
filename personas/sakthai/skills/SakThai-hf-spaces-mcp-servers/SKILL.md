---
name: SakThai-hf-spaces-mcp-servers
description: "Complete reference for exposing Hugging Face Spaces as MCP (Model Context Protocol) servers — enabling any Gradio Space to be called as a tool from MCP clients like Claude Desktop, Cursor, Cline, VS Code, and other MCP-compatible agents."
---

# HF Spaces as MCP Servers

Hugging Face Spaces can be exposed as MCP (Model Context Protocol) servers, making any Gradio Space callable as a tool from any MCP-compatible client — without writing a single line of glue code. This bridges the HF Spaces ecosystem into the broader AI agent tooling landscape.

## Overview

MCP (Model Context Protocol) is a standardized protocol for exposing tools, resources, and prompts so LLMs can use them. A Gradio Space with MCP support exposes its API endpoints as MCP tools, automatically generating schemas, descriptions, and parameter types from function signatures and docstrings.

**Key capabilities:**
- Any public Gradio Space with an MCP badge is a one-click-add MCP tool
- Build your own MCP-compatible Space with `mcp_server=True` in `.launch()`
- Supports tools, resources, and prompts (all three MCP primitives)
- Works with any MCP client: Claude Desktop, Cursor, Cline, VS Code, etc.
- Private Spaces and auth-supported endpoints supported
- ZeroGPU Spaces work — quota consumed per tool call
- File handling (images, audio) auto-converted for MCP

## Setup

### Prerequisites

1. **HF Token** — A valid Hugging Face token with **READ** permissions. Create one at https://huggingface.co/settings/tokens/new?tokenType=read
2. **MCP Client** — Any MCP-compatible client (Claude Desktop, Cursor, Cline, VS Code with MCP extension, etc.)

### Configure MCP Client

From your Hub MCP settings (https://huggingface.co/settings/mcp), select your MCP client type and follow the setup instructions. The settings page provides ready-to-copy configuration snippets for each client.

The general pattern for client configs:

```json
{
  "mcpServers": {
    "gradio": {
      "url": "https://<space-subdomain>.hf.space/gradio_api/mcp/"
    }
  }
}
```

## Adding Existing Spaces as MCP Tools

### Via the MCP Badge

1. Browse [compatible Spaces](https://huggingface.co/spaces?filter=mcp-server) — look for the grey **MCP** badge on any Space card
2. Click the badge → **Add to MCP tools** → confirm
3. The Space appears in your Hub MCP Server settings under "Spaces Tools"
4. Tools are instantly available in your MCP client (restart if they don't appear)

### Finding MCP-enabled Spaces

Filter on the Spaces hub: `https://huggingface.co/spaces?filter=mcp-server`

This returns only Spaces published with MCP support enabled.

## Building an MCP-compatible Gradio Space

### Installation

```bash
pip install "gradio[mcp]"
```

### Minimal Example

```python
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

demo = gr.Interface(fn=letter_counter,
                    inputs=["text", "text"],
                    outputs="number")
demo.launch(mcp_server=True)   # exposes an MCP schema automatically
```

**What this does:**
1. Starts the regular Gradio web interface
2. Also starts an MCP server at `/gradio_api/mcp/`
3. Automatically converts each function into an MCP tool with name, description, and input schema derived from the function's docstring and type hints
4. The Space receives the MCP badge automatically upon deployment

### Converting an Existing Space

1. **Duplicate** the Space (if not yours)
2. **Add docstrings** to all functions you want as tools — Google-style `Args:` blocks with typed parameters
3. **Add `mcp_server=True`** to the `.launch()` call
4. Push to a new Space

## Key Features

### Tool Conversion

Every API endpoint in your Gradio app becomes an MCP tool. The function name becomes the tool name; the docstring becomes the tool description; type hints determine parameter schemas.

To view the generated schema: `http://your-server:port/gradio_api/mcp/schema` or visit the "View API" link in your Space footer and click "MCP".

### Environment Variable Activation

Instead of `mcp_server=True` in code, set:

```bash
export GRADIO_MCP_SERVER=True
```

### File Handling

MCP tools handle file data transparently:
- Image and audio files are automatically converted between MCP and Gradio formats
- Input files accepted as URLs (`http://` / `https://`)
- A companion STDIO-based MCP server is also generated for file uploads to remote apps

### Authentication & Headers

**Private Spaces:** Add an Authorization header to your client config:

```json
{
  "mcpServers": {
    "gradio": {
      "url": "https://abidlabs-mcp-tools.hf.space/gradio_api/mcp/",
      "headers": {
        "Authorization": "Bearer <YOUR-HF-TOKEN>"
      }
    }
  }
}
```

**Per-request auth via `gr.Header`:** Extract headers like `X-API-Token` from incoming MCP calls:

```python
import gradio as gr

def make_api_request(prompt: str, x_api_token: gr.Header):
    """Make a request on behalf of user.
    Args:
        prompt: The prompt to send.
    Returns:
        The response from the API.
    """
    return "Hello!" if not x_api_token else "Hello with token!"

gr.Interface(make_api_request, [gr.Textbox(label="Prompt")], gr.Textbox()).launch(mcp_server=True)
```

**`gr.Request` for full header access:** Add a parameter of type `gr.Request` to access the full Starlette request object (headers, IP, etc.).

### Progress Updates

Automatic progress notifications are sent to the MCP client during tool execution. For custom progress:

```python
def slow_reverser(text: str, progress=gr.Progress()):
    for i in range(len(text)):
        progress(i / len(text), desc="Reversing text")
        time.sleep(0.3)
    return text[::-1]
```

Disable progress overhead (saves ~500ms per call) with `queue=False` on your event handler.

### Tool Description Customization

Control tool descriptions via `api_description`:
- `None` (default): auto-generated from function docstring
- `False`: no description sent to LLM
- `str`: custom description string

Control which endpoints appear: `show_api=True` (default) or `show_api=False` to hide from MCP.

### ZeroGPU Integration

ZeroGPU Spaces use your account's daily GPU quota when called as MCP tools:

| Account Type | Daily GPU Quota |
|---|---|
| Unauthenticated | 2 minutes |
| Free account | 5 minutes |
| PRO account | 40 minutes |

PRO users can extend quota with pre-paid credits at $1/10 min.

## MCP Resources and Prompts

Gradio supports all three MCP primitives via decorators:

### Resources (`@gr.mcp.resource`)

Expose static or templated data:

```python
@gr.mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"
```

Clients request `greeting://Alice` → receives "Hello, Alice!". Return non-text data by specifying `mime_type` in the decorator and returning a Base64 string.

### Prompts (`@gr.mcp.prompt`)

Define reusable prompt templates:

```python
@gr.mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {"friendly": "Write a warm greeting", "formal": "Write a formal greeting"}
    return f"{styles.get(style)} for {name}."
```

## MCP-Only Functions (no UI)

Use `gr.api()` inside a `gr.Blocks()` context for pure logic functions that should return raw data without a UI update:

```python
import gradio as gr

def slice_list(lst: list, start: int, end: int) -> list:
    """Slice a list given start and end index.
    Args:
        lst: The list to slice.
        start: The start index.
        end: The end index.
    Returns:
        The sliced list.
    """
    return lst[start:end]

with gr.Blocks() as demo:
    gr.Markdown("## MCP-only tool: slice a list")
    gr.api(slice_list)

_, url, _ = demo.launch(mcp_server=True)
```

The function signature MUST be fully typed (including return value) for MCP tool schema generation.

## FastMCP Integration

For advanced use cases (stateful sessions, selective tool startup, multiple Spaces):

```python
from mcp.server.fastmcp import FastMCP
from gradio_client import Client
import sys, io

mcp = FastMCP("gradio-spaces")
clients = {}

def get_client(space_id: str) -> Client:
    if space_id not in clients:
        clients[space_id] = Client(space_id)
    return clients[space_id]

@mcp.tool()
async def generate_image(prompt: str, space_id: str = "ysharma/SanaSprint") -> str:
    """Generate an image.
    Args:
        prompt: Text prompt for the image
        space_id: HuggingFace Space ID to use
    """
    client = get_client(space_id)
    return client.predict(prompt=prompt, api_name="/infer")

# Run with stdio transport
mcp.run(transport='stdio')
```

Client config for this approach (static file-based MCP server):

```json
{
  "mcpServers": {
    "gradio-spaces": {
      "command": "python",
      "args": ["/path/to/gradio_mcp_server.py"]
    }
  }
}
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| MCP tools not appearing | Client needs restart | Restart MCP client after adding tools |
| Schema errors | Missing/wrong docstrings | Ensure `Args:` block with param names and types |
| `int` params failing | Some clients don't support numeric types | Change params to `str` and cast in function body |
| Streamable HTTP not supported | Client uses older MCP transport | Use `mcp-remote` (Node.js) as bridge: `npx mcp-remote http://.../gradio_api/mcp/` |
| ZeroGPU quota exceeded | Free users have 5 min/day | Upgrade to PRO for 40 min/day, or add pre-paid credits |
| Connection refused | Space not running | Wait for Space to wake from sleep; check if on free hardware |
| Private Space 401 | No auth in config | Add `Authorization: Bearer` header to MCP client config |

## Verification Checklist

- [ ] `pip install "gradio[mcp]"` succeeds
- [ ] `demo.launch(mcp_server=True)` starts MCP server on `/gradio_api/mcp/`
- [ ] Schema accessible at `http://localhost:port/gradio_api/mcp/schema`
- [ ] MCP badge appears on the Space after deploying to HF
- [ ] Tool shows up in MCP client after adding from hub settings
- [ ] Function docstrings follow `Args:` format with proper type hints
- [ ] Private Space accessible with `Authorization: Bearer` header
- [ ] ZeroGPU quota consumption tracks correctly

## Reference

- [HF Docs: Spaces as MCP Servers](https://huggingface.co/docs/hub/en/spaces-mcp-servers)
- [Gradio MCP Guide](https://www.gradio.app/guides/building-mcp-server-with-gradio)
- [MCP-enabled Spaces filter](https://huggingface.co/spaces?filter=mcp-server)
- [Hub MCP Settings](https://huggingface.co/settings/mcp)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Inspector Tool](https://github.com/modelcontextprotocol/inspector)
- [mcp-remote (stdio bridge)](https://github.com/geelen/mcp-remote)
- [Gradio Client Guide](https://www.gradio.app/guides/getting-started-with-the-python-client)
- [gr.api docs](https://www.gradio.app/main/docs/gradio/api)
