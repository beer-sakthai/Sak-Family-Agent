# Build Spaces with AI Agents — Complete Deep Dive

**Last updated:** 2026-07-25
**Source:** HF Changelog + Hub Docs
**Author:** SakThai
**License:** MIT

## Overview

On **July 16, 2026**, Hugging Face launched a new option on the Space creation page that lets users build Spaces using AI coding agents. Instead of manually writing all the code, users copy a generated command from the new-space page into any major AI agent, and the agent builds, iterates, and deploys the Space.

**Upvotes:** 122 (+117 in one week) — among the highest-rated changelog entries, indicating strong community demand.

## How It Works

### Architecture

```
User → new-space page (https://hf.co/new-space)
  → selects SDK, name, visibility
  → clicks "Build with AI Agent"
  → page generates agent command
  → user copies command to their agent
  → agent builds Space code
  → agent pushes to HF repo
  → Space auto-deploys
```

### Supported Agents

The feature works with all major coding agents:
- **Claude Code** (Anthropic)
- **OpenCode** (open-source terminal agent)
- **OpenAI Codex** (CLI agent)
- **Gemini CLI** (Google)
- **Cursor** (AI IDE)
- Any agent that can execute shell commands and push to Git

### Space Types Supported

Agents can build any Space SDK:
- **Gradio Spaces** — Python-based interactive ML demos
- **Static Spaces** — HTML/CSS/JS frontends (free)
- **Docker Spaces** — Custom environments with Dockerfiles
- **Streamlit Spaces** — Data app demos

### Use Cases

- **From a model:** "Build a Space that demonstrates Qwen3-0.6B text generation with adjustable temperature"
- **From a paper:** "Build a Space reproducing the key results from the Gemma 3 technical report"
- **From a local folder:** "Take this local ML project and deploy it as a Space"
- **From scratch:** "Build a Space that transcribes audio files using Whisper"

## Generated Command Format

The new-space page generates a command tailored to your agent. The command typically includes:

1. **Repo creation** — Creates the Hugging Face Space repo via `hf` CLI or API
2. **Template setup** — Clones a starter template or creates files from scratch
3. **Build instructions** — The user's natural language description of what the Space should do
4. **Push instructions** — Git push to deploy

Example (conceptual):
```
# Create Space for model demo
hf space create my-demo --sdk gradio --template gradio-base
# Then build and iterate...
```

## URL Parameters

The new-space page supports:
- `?setup=agent` — Opens the AI agent build flow directly
- `?sdk=gradio` (or `docker`, `static`) — Preselect SDK
- Standard repo creation URL params

## Practical Patterns

### Pattern 1: Demo a Model
1. Find a model on HF Hub (e.g., `Qwen/Qwen3-0.6B`)
2. Go to new-space page, select "Build with AI Agent"
3. Paste: "Create a Space that loads Qwen3-0.6B via Inference Providers and lets users chat with adjustable parameters"
4. Agent builds the Gradio app, pushes to Space, it auto-deploys

### Pattern 2: Reproduce a Paper
1. Open the paper page on HF Papers
2. Go to new-space > Build with AI Agent
3. Paste: "Reproduce the inference pipeline from this paper, include example inputs and visualizations"
4. Agent builds the complete demo

### Pattern 3: Deploy Local Project
1. Go to new-space > Build with AI Agent  
2. Paste: "Take the model inference code from my local folder ./deploy and create a Space with a Gradio interface"
3. The agent reads your local files and adapts them for Spaces

## Zero-Cost Deployment

- **Static Spaces:** Free for everyone. No compute costs.
- **Gradio on ZeroGPU:** Free for personal accounts in good standing (up to 2 Spaces). Uses Nvidia A100s with fair-use scheduling.
- **Docker Spaces:** Require PRO plan. Not zero-cost.
- **PRO plan:** $9/mo. Not required for ZeroGPU Gradio or Static Spaces.

## Best Practices

1. **Be specific in your instructions** — Tell the agent the SDK, key libraries, and UI layout you want
2. **Use the `?setup=agent` URL** — Skips directly to the agent flow
3. **Iterate naturally** — Agents can modify and improve the Space across multiple turns
4. **Use with existing models** — The agent can load models directly from HF Hub
5. **Combine with Inference Providers** — For zero-cost model inference in your Space

## Limitations (as of Jul 2026)

- Requires an AI agent that can execute shell commands and push to Git
- The feature is new and the generated commands may evolve
- Docker Spaces require a paid plan
- No built-in multi-agent orchestration yet

## Sources

- https://huggingface.co/changelog/spaces-with-agents
- https://huggingface.co/docs/hub/en/spaces-overview
- https://huggingface.co/new-space
- https://huggingface.co/docs/hub/en/spaces-sdks-gradio
