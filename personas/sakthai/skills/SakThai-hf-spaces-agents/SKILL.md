---
name: SakThai-hf-spaces-agents
author: SakThai
license: MIT
description: >
  Complete reference on using AI coding agents (Claude Code, Codex, OpenCode, etc.)
  to create Hugging Face Spaces directly from model pages. Covers the "Deploy -> Spaces"
  workflow, the AI prompt generation system, agent-compatible Space templates, and how
  to build, iterate, and publish Spaces programmatically through AI agents.
version: 1.0.0
metadata:
  hermes:
    tags: [huggingface, spaces, agents, ai-agents, gradio, claude-code, codex, deployment]
    category: productivity
---

# Hugging Face Spaces + AI Agents

## What It Is

The **Spaces with Agents** feature lets you create Hugging Face Spaces directly from model
pages using AI coding agents. Instead of manually writing a Gradio app or Dockerfile, you
click "Deploy -> Spaces" on any model page, copy the generated prompt, and paste it into
your AI agent (Claude Code, Codex, OpenCode, etc.). The agent reads the model page and
builds a fully functional Space demo automatically.

## Key Concepts

- **Zero-to-Space in one click**: No manual setup — the agent reads model card metadata,
  picks the right inference API, and writes the demo code.
- **Agent-compatible prompts**: Generated prompts include model details, task type, example
  inputs, and SDK requirements. The agent can iterate and refine.
- **Supports all model types**: Text generation, image generation, audio, multimodal — any
  model page with a "Deploy" dropdown can generate an agent prompt.
- **Uses existing HF tooling**: The agent can use `huggingface_hub`, InferenceClient, MCP
  server tools (`hf_fs`), and Gradio to build the Space.

## Sources

- HF Docs: https://huggingface.co/docs/hub/en/spaces-more-ways-to-create
- Changelog: https://huggingface.co/changelog/spaces-with-agents
- New Space page: https://huggingface.co/new-space?setup=agent
- HF Agents Docs: https://huggingface.co/docs/hub/en/agents
