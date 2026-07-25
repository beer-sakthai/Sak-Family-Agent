# HF Learning: Spaces with AI Agents — Deploy-to-Space from Model Pages

> **Topic**: `spaces-with-agents`
> **Date**: 2026-07-25
> **Sources**: HF Docs (spaces-more-ways-to-create), HF Changelog (spaces-with-agents), HF Agents Docs

---

## 1. What Changed

The Hugging Face Hub now lets you create a Space demo from **any model page** by clicking
**"Deploy -> Spaces"**. This opens a modal with a pre-generated prompt tailored to the
model. You copy the prompt, paste it into an AI coding agent (Claude Code, Codex, Hermes,
OpenCode), and the agent builds the Space — including the Gradio app, dependencies, and
inference setup — automatically.

A separate entry point at `/new-space?setup=agent` on the new Space creation page gives you
the same workflow for building Spaces from scratch (not tied to a specific model).

---

## 2. The Workflow

### Step 1: Navigate to a Model Page
Any model on the Hub (text, image, audio, video, multimodal) with a "Deploy" dropdown can
be used as the starting point.

### Step 2: Click "Deploy -> Spaces"
The modal opens with:
- Model name and task type
- Suggested SDK / framework (Gradio, Docker, Static)
- Example inference code snippet
- A copyable agent prompt

### Step 3: Paste into an AI Agent
The prompt contains all context the agent needs:
- Model repo ID (e.g., `meta-llama/Meta-Llama-3.1-8B`)
- Task type (text-generation, text-to-image, etc.)
- Inference API example calls
- Gradio component recommendations
- Hardware requirements (CPU, GPU, ZeroGPU)

### Step 4: Agent Builds and Publishes
The agent:
1. Reads the model card and config files
2. Creates `app.py` (or `Dockerfile` + `requirements.txt`)
3. Uses `huggingface_hub` or `gradio` to create the Space repo
4. Pushes code, waits for build, reports the URL

### Step 5: Iterate (Optional)
The agent can refine the Space — add examples, improve UI, fix bugs — in subsequent
prompt turns.

---

## 3. Architecture & Design

```
Model Page ──→ "Deploy -> Spaces" ──→ Prompt Generator
                                            │
                                   ┌────────▼────────┐
                                   │  Agent Prompt    │
                                   │  (copyable text) │
                                   └────────┬────────┘
                                            │ paste into agent
                                   ┌────────▼────────┐
                                   │  AI Coding Agent │
                                   │  (Claude Code,   │
                                   │   Codex, Hermes) │
                                   └────────┬────────┘
                                            │ creates & pushes
                                   ┌────────▼────────┐
                                   │  HF Space        │
                                   │  (Gradio/Docker) │
                                   └─────────────────┘
```

**Key Design Decisions:**
- **Prompt-first, not API-first**: The feature doesn't define a new API. It generates a
  natural-language prompt that agents already understand. This makes it agent-agnostic.
- **Zero new infra**: No new endpoints, no new auth flows. The agent uses existing HF tools
  (`huggingface_hub`, `InferenceClient`, MCP, Gradio) to build the Space.
- **Model card as data source**: The prompt is dynamically generated from the model card's
  YAML metadata, config.json, and README.

---

## 4. What the Agent Prompt Contains

A typical generated prompt includes:

```
Build a Gradio Space for model [repo_id].

Model details:
- Task: text-generation
- Pipeline tag: text-generation
- Library: transformers
- Inference API endpoint: https://api-inference.huggingface.co/models/[repo_id]

Create a file app.py with:
- A Gradio Blocks or ChatInterface UI
- Uses InferenceClient with the model
- Includes example inputs from the model card
- Shows generation parameters (temperature, max_tokens)

Push to a new Space under user [username] named [space_name].
```

The agent processes this and:
1. Creates `app.py` with Gradio UI calling `InferenceClient`
2. Creates `requirements.txt` with `huggingface_hub`, `gradio`, `transformers`
3. Creates `README.md` with model card info
4. Pushes to HF using `huggingface_hub` CLI or `HfApi.create_repo()` + `upload_folder()`

---

## 5. Relation to Other HF Agent Features

| Feature | What It Does |
|---------|-------------|
| **Spaces with Agents** (this) | Create Spaces from model pages via agent prompts |
| **HF MCP Server** | Hub-wide tool access for agents (search, read, write repos) |
| **Spaces as MCP Tools** | Expose individual Gradio Spaces as MCP callable tools |
| **HF Agent Skills** | Reusable skill definitions for agents (Hermes-native) |
| **Spaces as Agent Tools** | Register Spaces as agent tools for task-specific actions |
| **HF CLI for AI Agents** | CLI commands (`hf mcp`, `hf skills`) for agent workflows |

The Spaces-with-Agents feature complements the MCP Server: while MCP gives agents Hub-wide
read/write access, this feature gives them a **starter template** tailored to a specific
model.

---

## 6. How to Use It (Quick Reference)

### From a Model Page
1. Go to any model page (e.g., `https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3`)
2. Click the **"Deploy"** dropdown button (top right, next to "Use this model")
3. Select **"Spaces"**
4. Copy the prompt from the modal
5. Paste into your agent's chat/terminal

### From the New Space Page
1. Go to `https://huggingface.co/new-space?setup=agent`
2. Configure Space name, license, hardware (CPU/GPU)
3. Copy the generated agent command
4. Run it in your agent

### Supported Agents
- **Claude Code** (Anthropic)
- **Codex CLI** (OpenAI)
- **Hermes Agent** (Nous Research) — also supports `hf mcp serve` and `hf skills`
- **OpenCode** (opencode-go)
- Any MCP-compatible agent with HF Hub access

---

## 7. Best Practices

1. **Use with a READ-scoped HF token**: The agent needs `huggingface_hub` login to create
   repos. For CI/CD, use fine-grained tokens with write access to Spaces.

2. **Specify hardware upfront**: If your model needs a GPU, mention it in the prompt or use
   the Spaces hardware selector on the new-space page. ZeroGPU Spaces are free for
   PyTorch-based demos.

3. **Iterate in rounds**: The first build may be basic. Let the agent refine — add
   examples, improve the UI, fix edge cases — in follow-up prompts.

4. **Combine with MCP**: If your agent has the HF MCP Server connected, it can
   `hf_fs search` for similar Spaces, `hf_fs read` model cards, and `hf_fs create`
   the Space repo — all via natural language.

5. **Check the build logs**: After pushing, check
   `https://huggingface.co/spaces/<user>/<space-name>/logs` for build output. The agent
   can read these logs and self-correct.

---

## 8. Limitations

- **Prompt quality varies by model**: Models with sparse model cards may generate weaker
  prompts. Well-documented models get better Spaces.
- **Agent capability dependent**: Simple agents may only scaffold a basic app. Advanced
  agents (Claude Code, Codex) can build production-quality demos.
- **No auto-retry on build failure**: The agent must detect build failures from logs and
  self-correct. The feature doesn't automate this.
- **Spaces hardware limits**: Free Spaces have CPU only. ZeroGPU is available for
  PyTorch-based Spaces but must be explicitly configured.
- **Not for all Space types**: Docker and Static Spaces are supported but the prompt
  generator favors Gradio (the most common demo type).

---

## 9. Comparison: Before vs After

| Aspect | Before | After |
|--------|--------|-------|
| Setup time | 15-30 min manual coding | 30s prompt copy + 2-5 min agent build |
| Skill required | Gradio + Python + HF Hub API | Copy-paste + basic agent usage |
| Customization | Full control, any SDK | Agent does most work; refine in rounds |
| Learning curve | Steep for new users | Minimal — just click and paste |
| Build quality | Depends on developer skill | Depends on agent capability |

---

## Summary

The Spaces-with-Agents feature marks a shift from "write code to deploy" to "describe what
you want and an agent builds it." By generating model-tailored prompts from the Deploy
button, HF makes Space creation accessible to anyone who can use an AI coding agent —
without learning Gradio, Docker, or the HF Hub API first. For experienced users, it
accelerates the scaffolding phase so you can focus on customizing the demo.
