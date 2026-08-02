# HF Learnings — Inference Providers Serverless Inference Patterns

**author:** SakThai
**license:** MIT

## 2026-07-26: hf-inference-client-serverless-inference-patterns — HF Inference Providers: Modern Serverless API Patterns (Topic #221 Deepened)

### Summary

Comprehensive research into Hugging Face Inference Providers' serverless inference API patterns — the unified proxy layer connecting 18+ AI providers. This deep-dive covers the **Responses API (beta)** (new OpenAI-compatible unified interface with event-driven streaming and Remote MCP tools), **provider selection policies** (`:fastest`, `:cheapest`, `:preferred`, or explicit provider), **structured outputs** (guaranteed JSON Schema compliance), **function calling** (tools/tool_choice lifecycle), **streaming patterns** (SSE events), **pricing tiers** (free $0.10/mo, PRO $2.00/mo, Custom Provider Key bypass), and **zero-cost strategies** for credit-constrained users.

Key insight: The Inference Providers API ecosystem has consolidated around two API surfaces — the modern **Responses API** (for agentic apps with tools, MCP, streaming, and structured outputs) and the classic **Chat Completions API** (simpler, broader provider compatibility, function calling). Both route through `router.huggingface.co/v1` with interchangeable provider selection policies.

---

### 1. Architecture Overview

```
User Application (SDK / HTTP)
        │
        ▼
┌─────────────────────────────────┐
│  router.huggingface.co/v1       │
│  Inference Providers Proxy      │
│  ┌──────────┬──────────┬──────┐ │
│  │Responses │  Chat    │Other │ │
│  │  API     │Completions│Tasks │ │
│  │(unified) │(standard) │(img, │ │
│  │         │          │audio)│ │
│  └──────────┴──────────┴──────┘ │
│  ┌────────────────────────────┐ │
│  │  Provider Selection Engine │ │
│  │  (auto | fastest | cheapest│ │
│  │   | preferred | explicit)  │ │
│  └────────────────────────────┘ │
└──────────┬──────────────────────┘
           │
           ▼ (routed to selected provider)
┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
│Groq │ │Novita│ │Together│Fal AI│...18+
└─────┘ └─────┘ └─────┘ └─────┘ └─────┘
```

**Two API surfaces** serve different needs:

| Aspect | Responses API (beta) | Chat Completions API |
|--------|---------------------|---------------------|
| **Endpoint** | `POST /v1/responses` | `POST /v1/chat/completions` |
| **Input** | `instructions` + `input` (string or messages[]) | `messages[]` array |
| **Streaming** | Event-driven (`response.created`, `.delta`, `.completed`) | Standard `data:` SSE chunks |
| **Tools** | Built-in (functions, MCP, web search, code interpreter) | Function calling via `tools` parameter |
| **Structured outputs** | `text.format` parameter with JSON Schema | `response_format` parameter |
| **Remote MCP** | ✅ Yes (`tools` array with `server_url`) | ❌ No |
| **Reasoning** | ✅ `reasoning.effort` parameter | ⚠️ Via model-specific params |
| **Best for** | Agentic apps, multi-step, tool-heavy | Simple chat, broad compatibility |

---

### 2. Provider Selection System

#### 2.1 Selection Policies

Provider selection is controlled via a **suffix appended to the model ID**:

| Policy | Suffix | Behavior |
|--------|--------|----------|
| **Fastest** (default) | `:fastest` | Highest throughput (tokens/second) |
| **Cheapest** | `:cheapest` | Lowest price per output token |
| **Preferred** | `:preferred` | User's order in Inference Provider settings |
| **Explicit provider** | `:groq`, `:novita`, `:together`, etc. | Forces a specific provider |

**Examples:**

```python
from openai import OpenAI
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key="hf_..."
)

# Fastest available provider
response = client.responses.create(
    model="openai/gpt-oss-120b:fastest",  # default if no suffix
    input="Hello!",
)

# Cheapest provider
response = client.responses.create(
    model="moonshotai/Kimi-K2-Instruct-0905:cheapest",
    input="Hello!",
)

# Explicit provider
response = client.responses.create(
    model="deepseek-ai/DeepSeek-R1:groq",
    input="Hello!",
)
```

#### 2.2 Automatic Failover

When using automatic provider selection (`:fastest`, `:cheapest`, `:preferred`), the system automatically fails over to alternative providers if the primary provider is flagged as unavailable by the validation system. This provides built-in reliability without application-level retry logic.

#### 2.3 Provider Compatibility

Not all providers support all features. Key constraints:

| Feature | Compatible Providers | Notes |
|---------|---------------------|-------|
| Chat completion | All 18+ providers | Universal support |
| Streaming | Most providers | Some may not support |
| Function calling | HF Inference + Groq + others | Check per-model |
| Structured outputs | HF Inference + Groq + others | Via `response_format` or `text.format` |
| Responses API | Most chat completion providers | Beta feature |
| Image generation | Fal AI, Replicate, HF Native | Routed separately |
| Audio (TTS/ASR) | HF Native, specific providers | Not via router |

---

### 3. Responses API (Beta) — Deep Dive

The Responses API provides a **unified interface for agentic applications** with built-in tool orchestration, event-driven streaming, and reasoning controls.

#### 3.1 Core Response Patterns

**Plain text output:**

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_TOKEN"),
)

response = client.responses.create(
    model="moonshotai/Kimi-K2-Instruct-0905:groq",
    instructions="You are a helpful assistant.",
    input="Tell me a three-sentence bedtime story about a unicorn.",
)
print(response.output_text)
```

**Conversation with message history:**

```python
response = client.responses.create(
    model="openai/gpt-oss-120b:fastest",
    input=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "Paris."},
        {"role": "user", "content": "What is its most famous landmark?"},
    ],
)
print(response.output_text)
```

#### 3.2 Event-Driven Streaming

The Responses API uses **semantic events** instead of raw SSE chunks:

```python
response = client.responses.create(
    model="openai/gpt-oss-120b:groq",
    instructions="You are a helpful assistant.",
    input="Write a short poem about AI.",
    stream=True,  # Enable event streaming
)

for event in response:
    if event.type == "response.output_text.delta":
        print(event.delta, end="", flush=True)
    elif event.type == "response.completed":
        print("\n[Done]")
```

**Event types:**

| Event Type | When It Fires | Contains |
|-----------|---------------|----------|
| `response.created` | Initial response created | Response ID, metadata |
| `response.in_progress` | Processing started | Status |
| `response.output_text.delta` | New text token generated | `delta` (incremental text) |
| `response.output_text.done` | Text output complete | Full text content |
| `response.function_call_arguments.delta` | Function call arg tokens | `delta` (incremental JSON) |
| `response.function_call_arguments.done` | Function call complete | Full arguments JSON |
| `response.completed` | Entire response done | Final response object |
| `response.failed` | Error occurred | Error details |

#### 3.3 Structured Outputs with Responses API

Use `text.format` to enforce JSON Schema compliance:

```python
response = client.responses.create(
    model="openai/gpt-oss-120b:groq",
    input="Extract: Title: Attention Is All You Need. Authors: Vaswani et al.",
    text={
        "format": {
            "type": "json_schema",
            "name": "paper_extraction",
            "schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "authors": {"type": "array", "items": {"type": "string"}},
                    "year": {"type": "integer"},
                },
                "required": ["title", "authors"],
                "additionalProperties": False,
            },
        }
    },
)
import json
data = json.loads(response.output_text)
print(data["title"])  # "Attention Is All You Need"
```

#### 3.4 Function Calling in Responses API

```python
response = client.responses.create(
    model="openai/gpt-oss-120b:groq",
    input="What's the weather in San Francisco?",
    tools=[{
        "type": "function",
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        },
    }],
    tool_choice="auto",
)
```

#### 3.5 Remote MCP Tools

The Responses API supports calling server-hosted MCP tools directly:

```python
response = client.responses.create(
    model="openai/gpt-oss-120b:groq",
    input="Search for recent AI papers.",
    tools=[{
        "type": "mcp",
        "server_url": "https://mcp.example.com/sse",
        "allowed_tools": ["search_papers", "get_paper"],
    }],
)
```

#### 3.6 Reasoning Controls

```python
response = client.responses.create(
    model="openai/gpt-oss-120b:groq",
    input="Solve: 2+2=?", 
    reasoning={
        "effort": "low"  # low | medium | high
    },
)
```

---

### 4. Chat Completions API — Standard Patterns

The classic OpenAI-compatible endpoint for simpler use cases:

```python
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1:fastest",
    messages=[
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hello!"},
    ],
    stream=False,
)
```

#### 4.1 Streaming (Chat Completions)

```python
stream = client.chat.completions.create(
    model="openai/gpt-oss-120b:groq",
    messages=[{"role": "user", "content": "Write a poem."}],
    stream=True,
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

#### 4.2 Function Calling (Chat Completions)

```python
import json

tools = [{
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "Get the current weather",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        },
    },
}]

response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1:groq",
    messages=[{"role": "user", "content": "Weather in Paris?"}],
    tools=tools,
    tool_choice="auto",
)

message = response.choices[0].message
if message.tool_calls:
    for tool_call in message.tool_calls:
        print(f"Calling: {tool_call.function.name}")
        print(f"Args: {tool_call.function.arguments}")
```

#### 4.3 Structured Outputs (Chat Completions)

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b:groq",
    messages=[{"role": "user", "content": "Extract: Title: AI. Year: 2024."}],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "extraction",
            "schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "year": {"type": "integer"},
                },
                "required": ["title", "year"],
            },
        },
    },
)
```

---

### 5. Pricing and Billing

#### 5.1 Credit System

Every Hugging Face user receives **monthly credits** for Inference Providers:

| Account Type | Monthly Credits | Pay-as-you-go |
|-------------|----------------|---------------|
| **Free Users** | **$0.10** (subject to change) | ✅ Yes (credit purchase required) |
| **PRO Users** | **$2.00** | ✅ Yes |
| **Team/Enterprise** | **$2.00 per seat** | ✅ Yes |

#### 5.2 Billing Approaches

| Feature | Routed by Hugging Face | Custom Provider Key |
|---------|----------------------|---------------------|
| How it works | Request routes through HF to provider | Custom provider key set in HF settings |
| Billing | Pay-as-you-go on HF account | Billed directly by provider |
| Monthly credits | ✅ Apply | ❌ No credits |
| Provider account | ❌ Not needed | ✅ Required |
| Best for | Simplicity, experimentation | Control, consistent usage |

#### 5.3 Organization Billing

To use Team/Enterprise included credits, specify the organization via header:
```
X-HF-Bill-To: your-org-name
```

#### 5.4 Free Tier Credit Optimization

$0.10/month translates to roughly:
- **~10,000-20,000** lightweight chat completions (small models, short outputs)
- **~100-200** tool-calling calls with moderate output
- **~3-5** image generations (if using image models)

**Zero-cost strategies:**
1. Use `:cheapest` policy to minimize per-call costs
2. Check `is_free: true` models via `/v1/models` endpoint
3. Cache responses for repeated queries
4. Use streaming to fail fast on long generations
5. Batch requests where possible
6. Use Custom Provider Key to leverage existing provider free tiers

---

### 6. Available Models Discovery

```python
# List available models with provider info
response = client.models.list()
for model in response.data:
    print(f"{model.id} - owned by {model.owned_by}")
```

The `/v1/models` endpoint returns all models with their provider routing info. Models with `is_free: true` won't consume credits.

---

### 7. Error Handling Patterns

#### 7.1 Rate Limiting

```python
from openai import RateLimitError
import time

def generate_with_retry(client, **kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return client.responses.create(**kwargs)
        except RateLimitError as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt * 2
                print(f"Rate limited, retrying in {wait}s...")
                time.sleep(wait)
                continue
            raise
```

#### 7.2 Provider Failover

```python
providers = ["groq", "novita", "together"]

for provider in providers:
    try:
        response = client.responses.create(
            model=f"openai/gpt-oss-120b:{provider}",
            input="Hello!",
        )
        return response
    except Exception as e:
        print(f"{provider} failed: {e}")
        continue
```

#### 7.3 Content Filter Detection

```python
try:
    response = client.responses.create(
        model="openai/gpt-oss-120b:groq",
        input="Generate harmful content",
    )
except Exception as e:
    if "content_filter" in str(e).lower():
        print("Content filter triggered — try a different prompt")
    else:
        raise
```

---

### 8. Complete Client Comparison

| Feature | `InferenceClient` (huggingface_hub) | OpenAI SDK (router endpoint) |
|---------|-------------------------------------|------------------------------|
| **Base URL** | Automatic | `https://router.huggingface.co/v1` |
| **Chat completion** | `chat_completion()` | `client.chat.completions.create()` |
| **Responses API** | ❌ Not yet | ✅ `client.responses.create()` |
| **Text-to-image** | ✅ `text_to_image()` | ❌ (use HF SDK) |
| **Audio** | ✅ `text_to_speech()`, `automatic_speech_recognition()` | ❌ |
| **Embeddings** | ✅ `feature_extraction()` | ❌ |
| **Streaming** | `stream=True` returning generator | `stream=True` with event types |
| **Structured outputs** | `response_format` param | `text.format` or `response_format` |
| **Function calling** | `tools` param | `tools` param |
| **Provider selection** | Implicit (model-based) | Suffix-based (`:groq`) |
| **Auto-failover** | ✅ Yes | ✅ Yes |
| **Dependency** | `huggingface_hub` (Python) | `openai` (Python) or any HTTP client |

**When to use which:**
- Use **OpenAI SDK** for: chat completion, Responses API, streaming, function calling, structured outputs — any pattern that maps to the chat/router endpoint
- Use **InferenceClient** for: image generation, audio (TTS/ASR), embeddings, feature extraction — tasks not available through the chat router

---

### 9. Zero-Cost Reference for Beer's Use Case

Since Beer has no income and uses the free tier ($0.10/mo):

| Strategy | Implementation | Impact |
|----------|---------------|--------|
| **Free models** | Use `:cheapest` + check `is_free` models | $0 cost for supported models |
| **Groq free tier** | `model="...:groq"` — offers free inference with tool support | Free function calling |
| **Cache responses** | Store results for repeated queries | Avoids duplicate credit spend |
| **Stream to fail fast** | `stream=True` → stop early if output is wrong | Saves partial credits |
| **Batch requests** | Combine multiple queries in one call | Single response cost |
| **Local fallback** | Use llama.cpp with GGUF models for zero-cost local inference | Completely free |
| **Credit monitoring** | Check `settings/billing` dashboard regularly | Prevent surprise depletion |

---

### 10. Key Takeaways

1. **Two API surfaces** serve different needs: Responses API (agentic, modern) vs Chat Completions (standard, compatible)
2. **Provider selection** is model-based via suffix syntax — no config changes needed to switch providers
3. **Free tier** ($0.10/mo) is genuinely usable for light experimentation and simple tool-calling
4. **Custom Provider Key** bypasses HF billing entirely — use existing provider free tiers
5. **Structured outputs** via `text.format` (Responses API) or `response_format` (Chat Completions) eliminate JSON parsing issues
6. **Remote MCP** is a Responses API exclusive — not available on the standard chat endpoint
7. **Auto-failover** provides built-in reliability for automatic provider selection
8. **`:cheapest` policy** is the best default for credit-constrained users
9. **Hybrid approach**: OpenAI SDK for chat/router tasks, InferenceClient for images/audio/embeddings
10. **The router endpoint** (`router.huggingface.co/v1`) is the single entry point for all chat-based inference

### Sources

- https://huggingface.co/docs/inference-providers/en/index — Inference Providers overview
- https://huggingface.co/docs/inference-providers/en/guides/responses-api — Responses API guide
- https://huggingface.co/docs/inference-providers/en/guides/structured-output — Structured outputs guide
- https://huggingface.co/docs/inference-providers/en/guides/function-calling — Function calling guide
- https://huggingface.co/docs/inference-providers/en/pricing — Pricing and billing docs
- https://huggingface.co/docs/inference-providers/en/guides/first-api-call — First API call guide
- https://huggingface.co/docs/inference-providers/en/guides/building-first-app — Building first app guide
- https://huggingface.co/settings/inference-providers — Provider settings and preference order
- https://huggingface.co/settings/billing — Billing dashboard and credit usage

### Skill Deepened

`hf-inference-client-serverless-inference-patterns/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md created with complete serverless inference patterns reference covering Responses API, Chat Completions, provider selection, structured outputs, function calling, pricing, and zero-cost strategies.

Tracking ID: `hf-inference-client-serverless-inference-patterns`
