# HF Learnings — InferenceClient Streaming Chat Completion Patterns Deep Dive

**author:** SakThai
**license:** MIT

## 2026-07-25: hf-inference-client-streaming-patterns — InferenceClient Streaming Chat Completion Patterns Deep Dive (Topic #328)

### Summary
Source-code-level deep dive into the complete streaming chat completion system in `huggingface_hub v1.24.0`. Covers the SSE event stream wire format, `_stream_chat_completion_response()` and `_format_chat_completion_stream_output()` internals, the sync vs async streaming interface, combining streaming with tools/function calling and structured outputs (`response_format`), provider-specific streaming behavior, stream lifecycle management (error handling, timeout, cancellation), `stream_options` for usage tracking, and practical patterns for real-time agent and chatbot applications.

### Source Files Analyzed

| File | Lines | Purpose |
|------|-------|---------|
| `huggingface_hub/inference/_client.py` | 3394 | `InferenceClient.chat_completion()` with streaming overloads |
| `huggingface_hub/inference/_common.py` | ~1200 | `_stream_chat_completion_response()`, `_format_chat_completion_stream_output()` |
| `huggingface_hub/inference/_generated/types/chat_completion.py` | ~500 | `ChatCompletionStreamOutput`, `ChatCompletionStreamOutputDelta`, `ChatCompletionStreamOutputChoice` |
| `huggingface_hub/inference/_async_client.py` | ~2000 | `AsyncInferenceClient` — async streaming with `async for` |

### Public API

```python
from huggingface_hub import InferenceClient, AsyncInferenceClient
from huggingface_hub.inference._generated.types import (
    ChatCompletionStreamOutput,
    ChatCompletionStreamOutputChoice,
    ChatCompletionStreamOutputDelta,
    ChatCompletionInputStreamOptions,
)
```

---

### 1. SSE Event Stream Architecture

The streaming protocol uses **Server-Sent Events (SSE)** over HTTP POST, transmitted line-by-line via `httpx.Client.stream()`. Each line carries a JSON payload prefixed with `data:`.

**Wire format:**
```
data: {"choices":[{"delta":{"content":"Hello","role":"assistant"},"index":0,"finish_reason":null}],"created":1710498504,"id":"","model":"meta-llama/Meta-Llama-3-8B-Instruct","system_fingerprint":"","usage":null}

data: {"choices":[{"delta":{"content":" world","role":"assistant"},"index":0,"finish_reason":null}],"created":1710498504,"id":"","model":"meta-llama/Meta-Llama-3-8B-Instruct","system_fingerprint":"","usage":null}

data: [DONE]
```

**Parsing pipeline (`_format_chat_completion_stream_output`):**

```
HTTP SSE stream (Iterable[str])
  │
  ├─ Line that doesn't start with "data:" → None (skipped, logger warning)
  ├─ Line == "data: [DONE]" → StopIteration raised (signals end-of-stream)
  └─ Line starts with "data:" →
       │  Strip "data:" prefix
       │  JSON.parse the payload
       │  Check for "error" field → raise TextGenerationError
       │  Parse into ChatCompletionStreamOutput (pydantic)
       └─ Yield ChatCompletionStreamOutput
```

**Key code (`_format_chat_completion_stream_output`):**
```python
def _format_chat_completion_stream_output(line: str) -> ChatCompletionStreamOutput | None:
    if not line.startswith("data:"):
        return None  # empty keepalive line

    if line.strip() == "data: [DONE]":
        raise StopIteration("[DONE] signal received.")

    json_payload = json.loads(line.lstrip("data:").strip())

    if json_payload.get("error") is not None:
        raise _parse_text_generation_error(json_payload["error"], json_payload.get("error_type"))

    return ChatCompletionStreamOutput.parse_obj_as_instance(json_payload)
```

**Key properties:**
- **Keepalive pings**: Empty lines (no `data:` prefix) are silently filtered — they return `None` and are skipped at the caller level.
- **[DONE] sentinel**: Uses `StopIteration` exception to break the generator loop cleanly — this is a Python idiom for signaling end-of-iteration from within a function.
- **Error in stream**: If the server encounters an error mid-stream, it sends a JSON payload with an `error` field, which triggers a `TextGenerationError` exception.
- **Streaming overhead**: Each SSE line carries the full `ChatCompletionStreamOutput` JSON, including `created`, `id`, `model`, and `system_fingerprint` fields — these are redundant across chunks (same values for all tokens in one response), but required by the OpenAI-compatible SSE format.

---

### 2. Sync Streaming

#### Basic Usage

```python
from huggingface_hub import InferenceClient

client = InferenceClient()

# stream=True returns Iterable[ChatCompletionStreamOutput]
stream = client.chat_completion(
    messages=[{"role": "user", "content": "Count to 10"}],
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    max_tokens=100,
    stream=True,
)

# Type: generator of ChatCompletionStreamOutput
for chunk in stream:
    print(chunk.choices[0].delta.content, end="")
```

**Each `ChatCompletionStreamOutput` chunk has:**
```python
@dataclass
class ChatCompletionStreamOutput:
    choices: list[ChatCompletionStreamOutputChoice]
    created: int             # Unix timestamp (same for all chunks in one response)
    id: str                  # Request ID (same for all chunks)
    model: str               # Model name
    system_fingerprint: str  # Deployment fingerprint
    usage: ChatCompletionStreamOutputUsage | None = None  # Only in final chunk if stream_options

@dataclass
class ChatCompletionStreamOutputChoice:
    delta: ChatCompletionStreamOutputDelta  # The actual token content
    index: int                               # Choice index (0 for single-completion)
    finish_reason: str | None = None         # "stop", "length", "eos_token", or None mid-stream

@dataclass
class ChatCompletionStreamOutputDelta:
    content: str | None = None    # Token text (None for tool_calls-only chunks)
    role: str | None = None       # Usually None after first chunk
    tool_calls: list | None = None  # Tool call data (populated for tool-use chunks)
```

#### Usage Tracking with stream_options

To get usage statistics (token counts) in streaming mode, pass `stream_options`:

```python
from huggingface_hub import ChatCompletionInputStreamOptions

stream = client.chat_completion(
    messages=[{"role": "user", "content": "Hello!"}],
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    stream=True,
    max_tokens=100,
    stream_options=ChatCompletionInputStreamOptions(include_usage=True),
)

for chunk in stream:
    if chunk.usage is not None:
        # Only the final chunk carries usage data
        print(f"Prompt tokens: {chunk.usage.prompt_tokens}")
        print(f"Completion tokens: {chunk.usage.completion_tokens}")
        print(f"Total tokens: {chunk.usage.total_tokens}")
```

**Usage behavior:**
- `include_usage=True`: Server sends a final chunk with `usage` populated and `choices[0].delta.content = None`
- `include_usage=False` (default): No usage data in stream chunks
- Usage chunk is guaranteed to be the **last** chunk in the stream (after the `[DONE]` sentinel equivalents)

#### Accumulating the Full Response

```python
def stream_to_full_response(stream):
    """Accumulate streaming chunks into a complete response string."""
    content_parts = []
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            content_parts.append(delta.content)
        if chunk.choices[0].finish_reason:
            finish_reason = chunk.choices[0].finish_reason
    return "".join(content_parts), finish_reason

full_text, reason = stream_to_full_response(stream)
```

#### Stream Lifecycle

```
client.chat_completion(stream=True)
  │
  ├─ _inner_post(stream=True)
  │   └─ get_session().stream("POST", url, ...)
  │       └─ Returns httpx.Response with streaming body
  │
  ├─ response.iter_lines()  ← Iterable[str]
  │   └─ Each line = SSE event or empty keepalive
  │
  ├─ _stream_chat_completion_response(lines)
  │   ├─ for line in lines:
  │   │   ├─ _format_chat_completion_stream_output(line)
  │   │   │   ├─ If not "data:" → skip
  │   │   │   ├─ If "data: [DONE]" → raise StopIteration → break
  │   │   │   ├─ If "data: {..." → parse → ChatCompletionStreamOutput
  │   │   │   └─ If error → raise TextGenerationError
  │   │   └─ yield ChatCompletionStreamOutput
  │   └─ StopIteration → break loop
  │
  └─ Generator exhausted → httpx.Response stream finalized
      → Connection returned to pool
```

---

### 3. Async Streaming

The `AsyncInferenceClient` mirrors the sync API but uses `async for`:

```python
from huggingface_hub import AsyncInferenceClient

async_client = AsyncInferenceClient()

# Async streaming
stream = await async_client.chat_completion(
    messages=[{"role": "user", "content": "Count to 10"}],
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    stream=True,
    max_tokens=100,
)

async for chunk in stream:
    print(chunk.choices[0].delta.content, end="")
```

**Implementation differences:**
- `AsyncInferenceClient` uses `httpx.AsyncClient` instead of `httpx.Client`
- `_inner_post` uses `await ` for all HTTP operations
- The async streaming response uses `response.aiter_lines()` instead of `response.iter_lines()`
- The async stream generator is an `AsyncGenerator` yielding `ChatCompletionStreamOutput`

**Key difference — async `_inner_post`:**
```python
# Sync
response = self.exit_stack.enter_context(
    get_session().stream("POST", url, ...)
)
return response.iter_lines()

# Async
response = await self.exit_stack.enter_async_context(
    get_session().stream("POST", url, ...)
)
return response.aiter_lines()
```

**Practical pattern — async agent loop with streaming:**

```python
async def agent_loop(messages, tools):
    full_response = ""
    
    stream = await async_client.chat_completion(
        messages=messages,
        tools=tools,
        stream=True,
        max_tokens=2000,
    )
    
    async for chunk in stream:
        delta = chunk.choices[0].delta
        
        # Check for tool calls in stream
        if delta.tool_calls:
            for tc in delta.tool_calls:
                # Accumulate tool call data across chunks
                # (tool_calls may span multiple chunks)
                pass
        
        # Accumulate text content
        if delta.content:
            full_response += delta.content
            
        # Check finish reason
        if chunk.choices[0].finish_reason:
            if chunk.choices[0].finish_reason == "tool_calls":
                # Model wants to call a tool
                # Parse accumulated tool_calls, execute, continue
                pass
    
    return full_response
```

---

### 4. Streaming with Tools/Function Calling

When streaming with `tools`, the stream may contain **both** text content and tool call data, potentially interleaved across chunks.

**Tool call streaming format:**
```python
# Chunk 1: text + partial tool call start
chunk.choices[0].delta.content = "I'll look that up for you."
# Or:
chunk.choices[0].delta.tool_calls = [
    ChatCompletionStreamOutputDeltaToolCall(
        index=0,
        id="call_abc123",
        function=ChatCompletionStreamOutputDeltaToolCallFunction(
            name="search_weather",
            arguments="",
        ),
        type="function",
    )
]

# Chunk 2: arguments streaming (character by character)
chunk.choices[0].delta.tool_calls = [
    ChatCompletionStreamOutputDeltaToolCall(
        index=0,
        id=None,  # Only in first chunk
        function=ChatCompletionStreamOutputDeltaToolCallFunction(
            name=None,  # Only in first chunk
            arguments='{"loc',
        ),
        type=None,
    )
]

# Chunk N: final chunk with finish_reason="tool_calls"
chunk.choices[0].finish_reason = "tool_calls"
```

**Accumulating tool calls from stream:**

```python
def accumulate_tool_calls(stream):
    """Accumulate tool calls from streaming chunks."""
    tool_calls = {}  # index -> {id, function: {name, arguments}}
    full_text = []
    
    for chunk in stream:
        delta = chunk.choices[0].delta
        
        if delta.content:
            full_text.append(delta.content)
        
        if delta.tool_calls:
            for tc in delta.tool_calls:
                idx = tc.index
                if idx not in tool_calls:
                    tool_calls[idx] = {
                        "id": tc.id,
                        "type": tc.type or "function",
                        "function": {"name": "", "arguments": ""},
                    }
                if tc.function:
                    if tc.function.name:
                        tool_calls[idx]["function"]["name"] = tc.function.name
                    if tc.function.arguments:
                        tool_calls[idx]["function"]["arguments"] += tc.function.arguments
        
        if chunk.choices[0].finish_reason:
            finish_reason = chunk.choices[0].finish_reason
    
    return "".join(full_text), list(tool_calls.values()), finish_reason
```

**Key observations:**
1. **Tool call data is split across chunks**: `id` and `name` only appear in the first chunk for each tool call index. Subsequent chunks only carry `arguments`.
2. **Arguments arrive character-by-character**: The `arguments` field is streamed as it's generated (JSON string), so concatenation is required.
3. **`finish_reason="tool_calls"`**: Indicates the model decided to call a tool rather than produce final text.
4. **Multiple tool calls**: Each tool call has a unique `index` — they may be interleaved in the chunk stream.

---

### 5. Streaming with Structured Outputs (response_format)

`response_format` constraints (JSON Schema or regex grammar) work correctly with streaming — each token delta conforms to the constraint:

```python
stream = client.chat_completion(
    messages=[{"role": "user", "content": "Extract the date and location."}],
    model="meta-llama/Meta-Llama-3-70B-Instruct",
    stream=True,
    max_tokens=500,
    response_format={
        "type": "json",
        "value": {
            "properties": {
                "date": {"type": "string"},
                "location": {"type": "string"},
            },
            "required": ["date", "location"],
        },
    },
)

# Each token delta is valid JSON that, when concatenated, forms the full JSON object
full_json = ""
for chunk in stream:
    if chunk.choices[0].delta.content:
        full_json += chunk.choices[0].delta.content
        # partial JSON may not be parseable yet

# After accumulation, full_json is a complete JSON string
import json
result = json.loads(full_json)
```

**Important considerations:**
- JSON Schema grammar is enforced server-side — each token satisfies the schema constraint
- Partial JSON in mid-stream may not be parseable (invalid JSON until the final token)
- This is different from regular streaming where content is free-form text
- All content appears in `delta.content` — not as structured fields
- `finish_reason` will be `"stop"` when the JSON is complete (if length doesn't cause truncation)

---

### 6. Provider-Specific Streaming Behavior

**TGI-based providers (hf-inference, some third parties using TGI):**

| Feature | Behavior |
|---------|----------|
| Chunk structure | Standard OpenAI-compatible SSE (`data:` prefix) |
| Keepalive | Empty lines every ~15s during long generations |
| Token granularity | One token per SSE message |
| Tool calls | Split across chunks (arguments arriving character by character) |
| `[DONE]` sentinel | `data: [DONE]` at end |
| Usage in stream | Available via `stream_options.include_usage=True` — final chunk |
| Error format | JSON with `error` and `error_type` fields |

**Third-party provider differences (Groq, Together, etc.):**

| Provider | Streaming Behavior Notes |
|----------|------------------------|
| **Groq** | Very low latency per token, standard OpenAI SSE format |
| **Together** | Standard OpenAI SSE, supports `stream_options` |
| **DeepInfra** | Standard OpenAI SSE, may have different keepalive timing |
| **Cerebras** | Standard OpenAI SSE, extremely fast token emission |
| **Fireworks** | Standard OpenAI SSE, supports usage tracking |
| **Replicate** | May use slightly different chunk format — normalized by `InferenceClient` |
| **Fal AI** | Image/video generation only, no chat streaming |

**Key insight:** The `_format_chat_completion_stream_output` function normalizes all providers into the same `ChatCompletionStreamOutput` format. Any provider-specific differences are abstracted away at the SSE parsing layer. However, some providers may:
- Send fewer fields per chunk (e.g., missing `system_fingerprint`)
- Use different keepalive timing
- Not support `stream_options.include_usage=True`
- Handle tool calls differently in the chunk structure

**Provider detection per event:**
```python
# Check which model/provider generated the stream
for chunk in stream:
    model_name = chunk.model  # The model ID from the response
    # Use this to determine provider-specific handling
```

---

### 7. Stream Error Handling

Errors can occur at three layers during streaming:

#### Layer 1: HTTP Error (before stream starts)
```python
from huggingface_hub import HfHubHTTPError, InferenceTimeoutError

try:
    stream = client.chat_completion(messages, model=..., stream=True)
except HfHubHTTPError as e:
    print(f"HTTP {e.response.status_code}: {e.server_message}")
except InferenceTimeoutError as e:
    print(f"Timeout: {e}")
```

#### Layer 2: Error mid-stream (server-side error)
```python
from huggingface_hub.errors import TextGenerationError

try:
    for chunk in stream:
        print(chunk.choices[0].delta.content, end="")
except TextGenerationError as e:
    print(f"Stream error: {e}")
```

The server may send an error mid-stream for reasons like:
- Rate limiting hit mid-generation
- Model unloaded from memory
- Provider routing failure
- Content filter triggered

#### Layer 3: Network error (connection dropped)
```python
try:
    for chunk in stream:
        print(chunk.choices[0].delta.content, end="")
except httpx.ReadError as e:
    print(f"Connection lost: {e}")
    # Can attempt to reconnect with a new request (stateless)
```

**Stateless reconnection pattern:**
```python
def stream_with_retry(client, messages, max_retries=3):
    accumulated = ""
    retries = 0
    while retries < max_retries:
        try:
            stream = client.chat_completion(
                messages + [{"role": "assistant", "content": accumulated}],
                stream=True,
                model="meta-llama/Meta-Llama-3-8B-Instruct",
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    accumulated += delta.content
                    yield delta.content
                if chunk.choices[0].finish_reason:
                    return  # Normal completion
        except (httpx.ReadError, ConnectionError) as e:
            retries += 1
            if retries >= max_retries:
                raise
            # accumulated text is preserved for reconnection context
    return accumulated
```

---

### 8. OpenAI Compatibility — Streaming Equivalence

The `InferenceClient` is designed as a drop-in replacement for OpenAI's Python client. The streaming API is identical:

```python
# OpenAI style (works with InferenceClient too)
from huggingface_hub import InferenceClient

client = InferenceClient()  # instead of OpenAI()

stream = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    messages=[{"role": "user", "content": "Hello!"}],
    stream=True,
    max_tokens=100,
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
    if chunk.choices[0].finish_reason:
        print(f"\n[Finished: {chunk.choices[0].finish_reason}]")
```

**Only two lines need to change when migrating from OpenAI:**
```python
# Before
from openai import OpenAI
client = OpenAI(api_key="sk-...")

# After
from huggingface_hub import InferenceClient
client = InferenceClient(api_key="hf_...")
```

---

### 9. Comparison: Sync vs Async

| Aspect | Sync (`InferenceClient`) | Async (`AsyncInferenceClient`) |
|--------|-------------------------|-------------------------------|
| HTTP Client | `httpx.Client` | `httpx.AsyncClient` |
| Stream iteration | `for chunk in stream:` | `async for chunk in stream:` |
| Response method | `response.iter_lines()` | `response.aiter_lines()` |
| Context manager | `exit_stack.enter_context()` | `exit_stack.enter_async_context()` |
| Use case | Scripts, notebooks, CLIs | Web servers, agents, concurrent apps |
| Thread safety | Not thread-safe | Safe for concurrent task loops |
| Performance | Good for sequential workloads | Better for I/O-bound concurrent workloads |

---

### 10. Practical Patterns

#### Pattern A: Real-time Chatbot with Streaming Display

```python
def streaming_chat(client, messages):
    """Stream a response and display it token-by-token."""
    print("Assistant: ", end="", flush=True)
    stream = client.chat_completion(
        messages=messages,
        stream=True,
        max_tokens=2000,
    )
    full_response = ""
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)
            full_response += delta.content
        if chunk.choices[0].finish_reason:
            print()  # newline
    return full_response
```

#### Pattern B: Agent with Streaming + Tool Detection

```python
def streaming_agent(client, messages, tools):
    """Stream a response, detecting tool calls mid-stream."""
    stream = client.chat_completion(
        messages=messages,
        tools=tools,
        tool_choice="auto",
        stream=True,
        max_tokens=2000,
    )
    
    content_parts = []
    tool_calls_accum = {}
    
    for chunk in stream:
        delta = chunk.choices[0].delta
        
        if delta.content:
            content_parts.append(delta.content)
            yield ("text", delta.content)
        
        if delta.tool_calls:
            for tc in delta.tool_calls:
                idx = tc.index
                if idx not in tool_calls_accum:
                    tool_calls_accum[idx] = {
                        "id": tc.id,
                        "type": tc.type or "function",
                        "function": {"name": "", "arguments": ""},
                    }
                if tc.function:
                    if tc.function.name:
                        tool_calls_accum[idx]["function"]["name"] = tc.function.name
                    if tc.function.arguments:
                        tool_calls_accum[idx]["function"]["arguments"] += tc.function.arguments
        
        if chunk.choices[0].finish_reason == "tool_calls":
            yield ("tool_calls", list(tool_calls_accum.values()))
```

#### Pattern C: Streaming with Structured Output + Validation

```python
def streaming_structured(client, messages, schema):
    """
    Stream a structured JSON response, yielding only after
    each valid JSON fragment.
    """
    stream = client.chat_completion(
        messages=messages,
        response_format={"type": "json", "value": schema},
        stream=True,
        max_tokens=1000,
    )
    buffer = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            buffer += chunk.choices[0].delta.content
            # Try to parse as we go
            try:
                partial = json.loads(buffer)
                yield ("partial", partial)
            except json.JSONDecodeError:
                yield ("token", chunk.choices[0].delta.content)
        if chunk.choices[0].finish_reason:
            yield ("complete", json.loads(buffer))
```

---

### Sources

- Source code: `huggingface_hub/inference/_client.py` (3394 lines, v1.24.0)
- Source code: `huggingface_hub/inference/_common.py` (~1200 lines, v1.24.0)
- Source code: `huggingface_hub/inference/_async_client.py` (~2000 lines, v1.24.0)
- Source code: `huggingface_hub/inference/_generated/types/chat_completion.py` (~500 lines)
- Official docs: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/inference_client
- Inference guide: https://huggingface.co/docs/huggingface_hub/main/en/guides/inference
- Inference Providers: https://huggingface.co/docs/inference-providers/en/index
- GitHub: https://github.com/huggingface/huggingface_hub
