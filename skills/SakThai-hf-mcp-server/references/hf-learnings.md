# HF Learnings Log

## 2026-07-25: hf-hub-agents-ecosystem-complete-deep-dive — Full HF Hub Agents Ecosystem Overhaul

### Summary
Complete deep-dive into the newly restructured **HF Hub Agents section** (discovered at https://huggingface.co/docs/hub/en/index — sidebar reorganization as of July 2026). The Hub docs now dedicate an entire top-level **Agents** section with 8 pages: Agents Overview, HF CLI for AI Agents, HF MCP Server, HF Agent Skills, Building with the SDK, Local Agents with llama.cpp, Agent Libraries, and Session Traces Format. This represents a strategic pivot by Hugging Face to position the Hub as the central registry and runtime for AI agents — not just models/datasets/Spaces.

### Key Structural Changes
- The old "Hub" docs sidebar had no dedicated Agents section — now it's a top-level category listed alongside Repositories, Models, Datasets, Spaces, Storage Buckets, Jobs.
- The MCP Server doc moved from experimental/obscure to a first-class page under Agents.
- **Three entirely new pages**: Agent Skills, Building with the SDK, Session Traces Format.
- **Two redesigned pages**: Agents Overview (new intro), HF CLI for AI Agents (rewritten for agent use cases).
- **Cross-linking**: The entire ecosystem now references each other (e.g., the MCP page links to Skills page, SDK page links to MCP page, Spaces page links to MCP servers page).

### Source
- HF Hub Docs (main): https://huggingface.co/docs/hub/en/index
- Agents Overview: https://huggingface.co/docs/hub/en/agents
- HF MCP Server: https://huggingface.co/docs/hub/en/agents-mcp
- HF Agent Skills: https://huggingface.co/docs/hub/en/agents-skills
- Building with the SDK: https://huggingface.co/docs/hub/en/agents-sdk
- Spaces as MCP servers: https://huggingface.co/docs/hub/en/spaces-mcp-servers
- MCP Settings: https://huggingface.co/settings/mcp
- Skills registry: https://agentskills.io
- Published: 2026-07-25

---

### 1. Agents Overview (New Page)

The new **Agents Overview** page serves as an entry point to the entire ecosystem. It introduces:
- The concept of "AI agents" as assistants that can use tools and follow instructions
- How HF fits in: as a registry, compute provider, and MCP server host
- Links to all sub-pages in the Agents section

**Key takeaway**: This page didn't exist before. The old docs had no unified "agents" entry point.

---

### 2. Hugging Face CLI for AI Agents (Redesigned)

Previously just "CLI" docs, now specifically targeted at AI agents. New features:
- The `hf` CLI is positioned as the primary interface for agents to interact with the Hub
- Key commands agents use: `hf download`, `hf upload`, `hf repo create`, `hf space create`, `hf job create`
- Includes agent-specific usage patterns (non-interactive, token-based auth)
- Links to MCP Server setup for one-click installation

**Installation**:
```bash
pip install huggingface_hub[cli]
# or via brew
brew install huggingface-cli
```

---

### 3. Hugging Face MCP Server (Complete Rewrite v3)

The MCP Server page at `/docs/hub/en/agents-mcp` is a **complete rewrite** from the previous version. Key changes:

#### 3.1 Setup Flow Simplified
- Settings page at `huggingface.co/settings/mcp` generates **client-specific** config snippets
- Supported clients: **Codex, Cursor, VS Code extensions, Zed, Claude Desktop, ChatGPT**
- Client-specific instructions — no more generic "paste this JSON" for all clients
- The settings page is now the **canonical entry point** — users are told NOT to write config by hand

#### 3.2 Built-in Tools (hf_fs Consolidation Complete)
The previous 28-tool surface has been fully consolidated into the `hf_fs` tool:

| Tool | Description |
|------|-------------|
| `hf_fs` | Core hub navigation — search models, datasets, Spaces, papers, docs (replaces 17+ individual tools) |
| Contribute Repos | Create repos and write files to them |
| Sandboxes | Create and use sandboxes (includes file management) |
| Run & Manage Jobs | Run, monitor, and schedule Jobs on HF infrastructure |

**The `hf_fs` tool handles most tasks**. It enables semantic search of documents and Spaces.

#### 3.3 Community Tools (Spaces) — New Interactive Model
- Browse MCP-compatible Spaces at `https://huggingface.co/spaces?mcp=true`
- Add a Space to your MCP tools directly from its **card badge** — grey MCP badge on any Space card
- Click the badge → "Add to MCP tools" → confirm → Space is listed in your MCP settings
- Gradio MCP apps expose functions as tools with arguments and descriptions
- **Dynamic Spaces**: toggle to let your assistant discover and use MCP-compatible Spaces at runtime without manual addition
- **Remove Embedded Images**: option for clients with limited image support

#### 3.4 ZeroGPU Support
- ZeroGPU Spaces work with MCP, using your quota when tools are called
- PRO users get 40 min/day (8× free quota)
- Example: up to 600 FLUX.1-schnell images/day on PRO

#### 3.5 Key URLs
| Resource | URL |
|----------|-----|
| MCP Settings | https://huggingface.co/settings/mcp |
| MCP Doc Page | https://huggingface.co/docs/hub/en/agents-mcp |
| Changelog | https://huggingface.co/changelog/hf-mcp-server |
| MCP Spaces | https://huggingface.co/spaces?mcp=true |
| Gradio MCP Guide | https://www.gradio.app/guides/building-mcp-server-with-gradio |
| HF MCP Server (project) | https://huggingface.co/mcp |

---

### 4. Hugging Face Agent Skills (Entirely New)

This is a **brand new page** and ecosystem. HF now provides a curated set of **Skills** for AI builders.

#### 4.1 What Are Skills?
Each Skill is a self-contained `SKILL.md` that an agent follows while working on a task. Skills work with all major coding agents: **Claude Code, OpenAI Codex, Google Gemini CLI, and Cursor**.

#### 4.2 Installation
```bash
# register the skills marketplace
/plugin marketplace add huggingface/skills
# install a specific Skill
/plugin install <skill-name>@huggingface/skills
```

#### 4.3 Available Skills (10 total)

| Skill | What It Does |
|-------|-------------|
| `hf-cli` | Hub operations via the hf CLI: download, upload, manage repos, run jobs |
| `huggingface-datasets` | Explore datasets, paginate rows, search text, apply filters |
| `huggingface-llm-trainer` | Train or fine-tune LLMs with TRL (SFT, DPO, GRPO) on HF Jobs |
| `huggingface-vision-trainer` | Train object detection and image classification models |
| `huggingface-community-evals` | Run evaluations against models on the Hub on local hardware |
| `huggingface-trackio` | Track and visualize ML training experiments with Trackio |
| `huggingface-papers` | Look up and read HF paper pages in markdown |
| `huggingface-paper-publisher` | Publish and manage research papers on the Hub |
| `huggingface-tool-builder` | Build reusable scripts for HF API operations |
| `gradio` | Build Gradio web UIs and demos |
| `transformers-js` | Run ML models in JavaScript/TypeScript with WebGPU/WASM |

#### 4.4 Usage Pattern
Once installed, mention the Skill directly in your prompt:
- "Use the HF model trainer Skill to fine-tune Qwen3-0.6B with SFT on the Capybara dataset"
- "Use the HF evaluation Skill to add benchmark results to my model card"
- "Use the HF datasets Skill to create a new dataset from these examples"

Your agent loads the corresponding `SKILL.md` instructions and helper scripts automatically.

#### 4.5 Skills Ecosystem Resources
- Skills Repository: Browse and contribute at agentskills.io
- Skills Format: Specification at agentskills.io
- CLI Guide: Hugging Face CLI for AI Agents
- MCP Guide: Use alongside Skills

#### 4.6 Relationship to MCP
Skills and MCP are complementary:
- **MCP Server** provides tools to the agent (search, file ops, jobs)
- **Skills** provide instructions to the agent (workflows, best practices, domain knowledge)
- An agent can use both: MCP for Hub access + Skills for domain-specific workflows

---

### 5. Building Agents with the HF SDK (Entirely New)

A completely new page documenting the `huggingface_hub[mcp]` SDK for building MCP-powered agents.

#### 5.1 Installation
```bash
pip install "huggingface_hub[mcp]"
```

#### 5.2 Quick Start: Run an Agent
The fastest way is via the **`tiny-agents` CLI**:
```bash
tiny-agents run julien-c/flux-schnell-generator
```
This loads an agent from the tiny-agents collection, connects to its MCP servers, and starts an interactive chat.

#### 5.3 Using the Agent Class
The `Agent` class manages the chat loop and MCP tool execution. It uses **Inference Providers** to run the LLM.

```python
from huggingface_hub import Agent
import asyncio

agent = Agent(
    model="Qwen/Qwen2.5-72B-Instruct",
    provider="novita",
    servers=[
        {
            "type": "sse",
            "url": "https://evalstate-flux1-schnell.hf.space/gradio_api/mcp/sse"
        }
    ]
)

async def main():
    async for chunk in agent.run("Generate an image of a sunset"):
        if hasattr(chunk, 'choices'):
            delta = chunk.choices[0].delta
            if delta.content:
                print(delta.content, end="")

asyncio.run(main())
```

#### 5.4 Using MCPClient Directly
For more control, use `MCPClient` to manage MCP servers and tool calls directly:

```python
import asyncio
from huggingface_hub import MCPClient

async def main():
    async with MCPClient(
        model="Qwen/Qwen2.5-72B-Instruct",
        provider="novita",
    ) as client:
        # Connect to an MCP server
        await client.add_mcp_server(
            type="sse", 
            url="https://evalstate-flux1-schnell.hf.space/gradio_api/mcp/sse"
        )
        
        # Process a request with tools
        messages = [{"role": "user", "content": "Generate an image of a sunset"}]
        
        async for chunk in client.process_single_turn_with_tools(messages):
            if hasattr(chunk, 'choices'):
                delta = chunk.choices[0].delta
                if delta.content:
                    print(delta.content, end="")

asyncio.run(main())
```

#### 5.5 Sharing Your Agent
Contribute agents to the **tiny-agents collection** on the Hub. Each agent needs:
- `agent.json` — Agent configuration (required)
- `PROMPT.md` or `AGENTS.md` — System prompt (optional)
- `EXAMPLES.md` — Sample prompts and use cases (optional)

#### 5.6 SDK Architecture
```
┌──────────────────────────────────────┐
│            Your Application           │
│  ┌────────────────────────────────┐  │
│  │  Agent Class (chat loop)       │  │
│  │  ┌──────────┐ ┌─────────────┐ │  │
│  │  │ MCPClient│ │ LLM (Infer.)│ │  │
│  │  └──────────┘ └─────────────┘ │  │
│  └────────────────────────────────┘  │
│            │                          │
│     SSE Connection                    │
│            │                          │
│    ┌───────┴────────┐                 │
│    │ MCP Server(s)  │                 │
│    │ (HF / Gradio)  │                 │
│    └────────────────┘                 │
└──────────────────────────────────────┘
```

#### 5.7 Key Resources
- huggingface_hub MCP Reference — Python API docs
- tiny-agents Documentation — JS API docs
- Inference Providers — Available LLM providers
- tiny-agents Collection — Browse community agents
- MCP Server Guide — Connect to the HF MCP Server

---

### 6. Spaces as MCP Servers (New Dedicated Page)

Previously a sub-section, now a **dedicated page** at `/docs/hub/en/spaces-mcp-servers`.

#### 6.1 One-Click Space Addition
- Any public Space with a visible **MCP badge** (grey badge) can be added as a callable tool
- No code required — just click the badge → "Add to MCP tools"
- Add as many Spaces as you want

#### 6.2 Setup Flow
1. From your Hub MCP settings, select your MCP client
2. Follow the client-specific setup instructions
3. Need a valid HF token with READ permissions
4. Browse compatible Spaces → click MCP badge → Add to MCP tools
5. Restart client → tools appear automatically

#### 6.3 Building Your Own MCP-Compatible Gradio Space
```python
# Install Gradio with MCP support
pip install "gradio[mcp]"

# Create your app with clear type hints and docstrings
import gradio as gr

def letter_counter(word: str, letter: str) -> int:
    """Count occurrences of a letter in a word.
    
    Args:
        word: The word to search in
        letter: The letter to count
    """
    return word.count(letter)

demo = gr.Interface(
    fn=letter_counter,
    inputs=[gr.Textbox("strawberry"), gr.Textbox("r")],
    outputs=[gr.Number()],
    title="Letter Counter",
    api_name="predict"
)

demo.launch(mcp_server=True)  # ← exposes MCP schema automatically
```

Push to Spaces → automatic MCP badge → anyone can add as a tool with one click.

#### 6.4 Converting an Existing Space
1. Duplicate the Space
2. Add docstrings to functions you want exposed as tools
3. Add `mcp_server=True` in `.launch()`
4. Redeploy

#### 6.5 Mixing Spaces
Since HF Spaces is the largest directory of AI apps, users are encouraged to mix Spaces for creative workflows. Example: combine `Lightricks/ltx-video-distilled` (video generation) with `ResembleAI/Chatterbox` (audio/TTS) in Claude Code to generate a video with audio.

#### 6.6 ZeroGPU Integration
For ZeroGPU Spaces, quota is consumed when the MCP tool is called:
- Free users: ~5 min quota
- PRO users: 40 min daily quota (8× more)

---

### 7. Other New Agents Pages

#### 7.1 Local Agents with llama.cpp
- New page documenting how to run local agents using llama.cpp
- Enables fully offline agent workflows
- Complements the cloud-based MCP server approach

#### 7.2 Agent Libraries
- Documents supported libraries for building agents: smolagents, transformers agents, OpenAIAgent, etc.
- Links to each library's documentation
- Positions HF as library-agnostic (supports any MCP-compatible framework)

#### 7.3 Session Traces Format
- New page documenting the format for agent session traces
- Includes JSON schema for capture/playback of agent sessions
- Enables debugging, replay, and optimization of agent workflows

---

### 8. Practical Implications for Beer's Usage

#### Zero-Cost Agent Setup
Since Beer has no income:
1. **MCP Server via CLI**: `npx @llmindset/hf-mcp-server` (free, runs locally)
2. **Agent SDK**: `huggingface_hub[mcp]` with free Inference Providers
3. **Skills**: Install free skills from huggingface/skills marketplace
4. **Spaces**: Use existing free Gradio Spaces as MCP tools
5. **ZeroGPU**: Free tier gives ~5 min/day GPU for Space tools

#### Agent SDK Free-Tier Strategy
```python
from huggingface_hub import Agent, MCPClient
# Use free inference providers (novita, together, etc.)
agent = Agent(
    model="Qwen/Qwen2.5-72B-Instruct",  # free via novita provider
    provider="novita",
    servers=[{"type": "sse", "url": "..."}]
)
```

#### Skills Integration with Sak Thai Family
The Sak Thai agent system (Hermes profiles) already uses Skills in a similar way to the HF Agent Skills format. The `~/profiles/sakthai/skills/` directory mirrors the concept. Key insight: HF's Agent Skills format at agentskills.io could serve as a reference for improving our own skill format.

---

### 9. Complete HF Agents Ecosystem Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  HF Hub Agents Ecosystem                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐    ┌───────────────────────────────┐  │
│  │   MCP Server  │    │      Agent Skills              │  │
│  │  (Tool Layer) │    │    (Instruction Layer)        │  │
│  ├──────────────┤    ├───────────────────────────────┤  │
│  │ hf_fs search │    │ hf-cli, datasets, llm-trainer │  │
│  │ Sandboxes    │    │ vision-trainer, evals, papers  │  │
│  │ Jobs         │    │ tool-builder, gradio           │  │
│  │ Community    │    │ transformers-js                │  │
│  │   Spaces     │    │                               │  │
│  └──────┬───────┘    └──────────────┬────────────────┘  │
│         │                           │                    │
│         └───────────┬───────────────┘                    │
│                     │                                    │
│  ┌──────────────────▼────────────────────────────────┐  │
│  │           HF SDK (huggingface_hub[mcp])             │  │
│  │  Agent Class  /  MCPClient  /  tiny-agents CLI     │  │
│  └──────────────────┬────────────────────────────────┘  │
│                     │                                    │
│  ┌──────────────────▼────────────────────────────────┐  │
│  │     Clients: Codex, Cursor, VS Code, Claude       │  │
│  │            Desktop, Zed, ChatGPT, Gemini CLI       │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │     Complementary: llama.cpp (local), smolagents   │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

### 10. Future Trends Observed

1. **Skills as the new plugin format**: HF is betting on SKILL.md as the standard for agent instructions. This is similar to how plugins worked in ChatGPT but open-source and cross-platform.

2. **MCP as the universal tool protocol**: Every Gradio Space can become an MCP server with one flag. This creates a massive network effect — the 200k+ existing Spaces are potentially MCP-able.

3. **HF as agent orchestrator**: The combination of MCP Server (tools) + Skills (instructions) + SDK (runtime) + Spaces (community tools) + Jobs (compute) positions HF as the end-to-end platform for AI agents, not just a model hub.

4. **Zero-cost barrier**: The entire ecosystem works on free tier — free inference, free Spaces (CPU), free ZeroGPU (limited), free CLI, free SDK. This aligns perfectly with Beer's constraints.

---

### Changelog

| Date | Topic | Key Discovery |
|------|-------|---------------|
| 2026-07-25 | HF Hub Agents Ecosystem Overhaul | Docs reorganized with new Agents section (8 pages), Agent Skills (10 skills at agentskills.io), `huggingface_hub[mcp]` SDK with Agent/MCPClient classes, Spaces as MCP servers with one-click badge addition, `tiny-agents` CLI, ZeroGPU integration, Local Agents with llama.cpp, Session Traces Format. Complete strategic pivot to agent-first Hub. |
