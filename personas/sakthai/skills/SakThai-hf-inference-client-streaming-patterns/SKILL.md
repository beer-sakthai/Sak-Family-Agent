---
name: SakThai-hf-inference-client-streaming-patterns
description: "Deep reference on Hugging Face InferenceClient streaming chat completion patterns\
  \ \u2014 SSE event stream architecture, sync/async streaming, streaming with tools\
  \ and structured outputs, provider-specific behavior, stream lifecycle management,\
  \ error handl"
---

# HF InferenceClient Streaming Patterns — Deep Dive

Complete reference on Hugging Face `InferenceClient` streaming chat completion patterns — from the SSE event stream wire format to advanced patterns combining streaming with tools, structured outputs, and async generators.

## Capabilities

- Understand the SSE event stream format (`data:` prefix, `[DONE]` sentinel, NDJSON payloads)
- Use synchronous streaming with `stream=True` and iterate over `ChatCompletionStreamOutput` chunks
- Use the asynchronous `AsyncInferenceClient` with `async for` streaming
- Build the full response text by concatenating `delta.content` across chunks
- Combine streaming with tools/function calling (detect `tool_calls` in stream deltas)
- Combine streaming with `response_format` (JSON Schema / regex grammar constraints)
- Handle stream errors, timeouts, and cancellation gracefully
- Understand provider-specific streaming behavior differences (TGI vs third-party)
- Use `stream_options` for usage information and fine-grained control
- Apply streaming in real-world patterns: chatbots, real-time agents, progressive UI

## Key Source Files

| File | Purpose |
|------|---------|
| `huggingface_hub/inference/_client.py` | `InferenceClient.chat_completion()` — sync streaming entry point |
| `huggingface_hub/inference/_common.py` | `_stream_chat_completion_response()`, `_format_chat_completion_stream_output()` |
| `huggingface_hub/inference/_generated/types/chat_completion.py` | `ChatCompletionStreamOutput`, `ChatCompletionStreamOutputDelta` |
| `huggingface_hub/inference/_async_client.py` | `AsyncInferenceClient` — async streaming support |

## Reference Files

- [`references/hf-learnings.md`](references/hf-learnings.md) — Complete deep-dive learning log with source analysis, diagrams, and patterns
