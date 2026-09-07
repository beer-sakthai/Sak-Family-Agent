---
name: SakThai-hf-async-inference-client
description: "Master async inference patterns with HFs AsyncInferenceClient — concurrent requests, streaming, MCP integration."
---

# HF Async Inference Client

Master async inference patterns with Hugging Face's `AsyncInferenceClient` — concurrent requests, streaming, MCP client integration, and performance optimization.

## Capabilities

- Use `AsyncInferenceClient` for non-blocking inference (sync vs async trade-offs)
- Stream chat completions and text generation with `async for`
- Run concurrent inference with `asyncio.gather()` and semaphore throttling
- Stream image/video generation via async chunked responses
- Integrate with `MCPClient` for tool-use agent loops
- Handle timeouts, errors, and rate limits in async contexts
- Choose between sync `InferenceClient` and `AsyncInferenceClient` per workload
- Use the OpenAI-compatible `client.chat.completions.create()` pattern with async

## Key Files

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — skill definition |
| `references/hf-learnings.md` | Learning log with deep-dive concepts |
