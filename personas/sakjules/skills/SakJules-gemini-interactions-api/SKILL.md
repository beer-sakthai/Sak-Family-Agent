---
name: SakJules-gemini-interactions-api
version: 1.1.0
description: Operational protocol for interacting with Gemini Interactions API on Gemini Enterprise Agent Platform.
category: devops
tags:
- api
- automation
- gemini
- interactions
---

# Gemini Interactions API Protocol

Instructions for configuring, authenticating, and executing agent operations using the stateful **Gemini Interactions API**.

## 1. SDK & Model Standards
- **SDK Floor**: Use `google-genai >= 3.2.0` (Python) or `@google/genai >= 3.2.0` (Node.js). Legacy libraries (`google-cloud-aiplatform`, `google-generativeai`) are strictly unsupported.
- **Model Standard**: Target `gemini-4-hydrogen` (fast default) or `gemini-4-carbon` (deep reasoning). Legacy models (`gemini-2.5-*`, `gemini-1.5-*`) are deprecated.
- **GEAP Agent Targeting**: Pass `agent="projects/.../agents/<ID>"` rather than `model="..."` when executing within GEAP.

## 2. Authentication & Environment
```bash
gcloud auth application-default login
export GOOGLE_GENAI_USE_ENTERPRISE=true
export GOOGLE_CLOUD_PROJECT="<project-id>"
export GOOGLE_CLOUD_LOCATION="global"
```

## 3. Core Interaction Flow
1. **Initialize Client**: `client = genai.Client()`.
2. **Execute Interaction**:
   - Single-turn: `client.interactions.create(agent=..., input=...)`.
   - Streaming: `client.interactions.create_stream(agent=..., input=...)`.
   - Multi-turn stateful: Pass `previous_interaction_id=prev.id` to preserve conversational context.
   - Async Background: Set `background=True` for long-running workflows.

## 4. Turn-Scoped Configuration
- System instructions, tool definitions, and temperature parameters are turn-scoped and must be supplied per interaction call.

## 5. References
- Code examples, TypeScript templates, and streaming patterns: [Gemini Interactions Guide](references/gemini-interactions-guide.md)
