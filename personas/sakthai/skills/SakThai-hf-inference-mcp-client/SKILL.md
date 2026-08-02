---
name: SakThai-hf-inference-mcp-client
author: SakThai
license: MIT
title: Hugging Face Inference MCP Client & Agent Framework
category: mlops
tags: [mcp, inference, agent, tool-use, function-calling, huggingface-hub, async]
related_skills:
  - SakThai-hf-mcp-server
  - hf-inference-client-tool-use-and-function-calling
  - hf-smolagents
description: >-
  Complete reference for the Hugging Face Inference MCP Client and Agent
  framework built into huggingface_hub. Covers the MCPClient class for
  connecting to MCP servers (stdio, SSE, HTTP), tool discovery and management,
  chat completion with tool execution, multi-turn agent loops, CLI agent runner
  (hf app), and the Tiny Agent config format.
version: 1.0.0
---

# Hugging Face Inference MCP Client & Agent Framework

## Overview

`huggingface_hub` v1.24+ ships a complete **MCP Client** and **Agent** framework
in `huggingface_hub.inference._mcp`. This module connects Hugging Face's
Inference Client to any MCP (Model Context Protocol) server — local stdio,
SSE remote, or StreamableHTTP — enabling models to discover and call tools
from MCP servers during chat completions.

## Architecture

- `MCPClient` — core client that connects to MCP servers and orchestrates
  tool-augmented chat completions
- `Agent` — multi-turn agent loop built on top of MCPClient
- `app` CLI — CLI entry point (`hf app`) for running agents from config files
- `utils` — result formatting (text, image, audio, resource) and config loading

## Server Types

| Type | Protocol | Use Case |
|------|----------|----------|
| `stdio` | stdin/stdout | Local processes (npx servers, scripts) |
| `sse` | Server-Sent Events | Remote servers with streaming |
| `http` | StreamableHTTP | HTTP-based MCP servers |

## Key API

- `MCPClient(model=..., provider=...)` — create client with optional model/provider
- `add_mcp_server(type, **params)` — connect an MCP server, discover its tools
- `process_single_turn_with_tools(messages, ...)` — stream chat with tool execution
- `Agent(model=..., servers=[...])` — create a multi-turn agent
- `agent.run(user_input)` — run the agent loop

## Zero-Cost

`MCPClient` and `Agent` use HF Inference API under the hood. Serverless
inference with HF-provided models is free for many models. The MCP servers
themselves (stdio) run locally at no cost.
