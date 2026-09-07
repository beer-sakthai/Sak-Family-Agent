---
name: SakThai-hf-gradio-server-mode
description: "Complete reference for Gradio 6 Server mode (gr.Server) — FastAPI-based API server with queue, SSE streaming, concurrency control, and MCP capabilities without a UI."
---

# Gradio 6 Server Mode (gr.Server)
**license:** MIT  
**skill_type:** reference  
**domain:** gradio  
**version:** 1.0.0  
**created:** 2026-07-25  
**updated:** 2026-07-25  

## Description

Complete reference for Gradio 6 Server mode (`gr.Server`) — a FastAPI-based API server that exposes Gradio's queue, SSE streaming, concurrency control, and MCP capabilities without a UI. Unlike `gr.Blocks()` which renders a full web interface, `gr.Server` is designed for pure API/microservice deployment with OpenAPI docs, standard FastAPI routes, and built-in Gradio event infrastructure.

## Quick Reference

| Feature | `gr.Server` | `gr.Blocks` |
|---------|:-----------:|:-----------:|
| Inherent FastAPI | ✅ (inherits directly) | ❌ (wraps FastAPI) |
| `@server.api()` decorator | ✅ | ❌ |
| Gradio queue + SSE streaming | ✅ | ✅ |
| Standard HTTP routes (`.get()`, `.post()`) | ✅ | ❌ (needs mount) |
| OpenAPI docs (/docs, /redoc, /openapi.json) | ✅ | ❌ (custom API page) |
| Gradio UI components | ❌ | ✅ |
| MCP tool/resource/prompt decorators | ✅ | ✅ (via `.queue()`) |
| Multiple workers scaling | ✅ | ✅ |

## Files

- `references/hf-learnings.md` — Full research with architecture, complete API reference, usage patterns, MCP integration, and production patterns

## Related Skills

- `hf-gradio-6-native-plot-components` — Native plot components
- `hf-gradio-6-chatinterface-deep-dive` — ChatInterface
- `hf-gradio-workflows-deep-dive` — Workflow API
- `hf-gradio-6-mcp-and-new-components` — MCP integration
- `hf-mcp-server-deep-dive-source-analysis` — HF MCP Server
