---
name: SakThai-hf-spaces-build-with-ai-agents
description: "Build and deploy Hugging Face Spaces using AI coding agents — generate commands from the new-space page and let agents iterate on Spaces for models, papers, or local folders"
---

# HF Spaces — Build with AI Agents

## Purpose
The Hugging Face Spaces creation page now includes an option to build a Space using an AI coding agent. Generate a command from the new-space page, paste it into any major coding agent (Claude Code, Codex, Gemini CLI, Cursor), and the agent builds, iterates, and deploys the Space automatically.

## Zero-Cost
- **Free:** Static Spaces are free. Gradio Spaces on ZeroGPU are free for personal accounts in good standing (up to 2 Spaces).
- **No GPU required for setup:** The agent builds the Space code locally or on HF infra; deployment to Spaces is free for static and ZeroGPU tiers.

## Quick Start
1. Go to https://huggingface.co/new-space?setup=agent
2. Enter your Space details (name, SDK, visibility)
3. Copy the generated agent command
4. Paste into your AI agent (Claude Code, OpenCode, Codex, Cursor, etc.)
5. The agent will build, iterate, and push the Space

## Key Resources
- `references/hf-learnings.md` — complete deep-dive with architecture, setup flow, and agent command patterns
- Changelog: https://huggingface.co/changelog/spaces-with-agents
- New Space: https://huggingface.co/new-space
- Spaces docs: https://huggingface.co/docs/hub/en/spaces-overview

## Related Skills
- `hf-spaces-configuration-reference` — Space YAML and SDK configuration
- `hf-gradio-6-chatinterface-deep-dive` — Gradio 6 patterns for Spaces
- `hf-spaces-docker-custom` — Docker-based Spaces
