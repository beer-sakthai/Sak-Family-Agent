# HF Learnings: Inference Router OpenAI-Compatible Endpoint

## 2026-07-25: HF Inference Router — OpenAI-Compatible Endpoint Architecture and Integration (Topic #361)

### Summary
Comprehensive deep dive into Hugging Face's Inference Router — the OpenAI-compatible proxy endpoint (`https://router.huggingface.co/v1`) that provides server-side provider selection, automatic failover, and unified access to hundreds of open models across 16+ inference providers through a single OpenAI SDK-compatible API. Unlike the `InferenceClient` which handles provider routing on the client side, the Router processes provider selection server-side using model ID suffixes and returns provider-optimized responses. The Router is currently **chat completions only** — other tasks (text-to-image, embeddings, speech) still require the native InferenceClient.

---

### Architecture

```
Application (OpenAI SDK)
    │
    ▼
router.huggingface.co/v1/chat/completions
    │
    ├─► Provider selection (auto / fastest / cheapest / preferred / explicit)
    │
    ├─► Cerebras
    ├─► Together
    ├─► Groq
    ├─► Fireworks AI
    ├─► DeepInfra
    ├─► Novita
    └─► ... 12+ more providers
```

**Key design points:**
- The Router is a **thin proxy** — it translates OpenAI-format requests into each provider's native format and normalizes responses back to OpenAI format
- Provider selection happens **server-side** — the client only specifies a model ID with optional policy suffix
- **Auto-failover**: When `auto` or `:fastest` policies are used, the Router monitors provider health and automatically routes around unavailable providers
- **Single endpoint**: All chat completions go through `/v1/chat/completions` regardless of provider

---

### Provider Selection Policies

Policy suffixes are appended to the model ID with a colon separator:

| Suffix | Description | Behavior |
|--------|-------------|----------|
| `:fastest` | Highest throughput (default) | Selects provider with highest tokens/second |
| `:cheapest` | Lowest cost | Selects provider with lowest output token price |
| `:preferred` | User preference order | Follows order configured at hf.co/settings/inference-providers |
| `:provider-name` | Explicit provider | Routes directly to specified provider (e.g., `:groq`, `:together`) |

**Examples:**
- `Qwen/QwQ-32B` — auto (equivalent to `:fastest`)
- `Qwen/QwQ-32B:fastest` — explicit fastest policy
- `Qwen/QwQ-32B:cheapest` — lowest cost provider
- `Qwen/QwQ-32B:preferred` — user's saved preferences
- `Qwen/QwQ-32B:groq` — force Groq as provider

**Resolution order:**
1. If model ID contains `:provider-name` → route directly (skip policies)
2. If model ID contains `:fastest` → sort providers by `throughput` descending, pick first
3. If model ID contains `:cheapest` → sort providers by `pricing.output` ascending, pick first
4. If model ID contains `:preferred` → follow user's saved provider order
5. If no suffix (auto) → same as `:fastest`
6. If selected provider is unhealthy → fall through to next-available provider

---

### `/v1/models` — Model Discovery

The Router exposes an OpenAI-compatible model listing endpoint:

**GET** `https://router.huggingface.co/v1/models`

Returns all chat-completion models served by at least one inference provider, with per-provider metadata:

```json
{
  "object": "list",
  "data": [
    {
      "id": "thinkingmachines/Inkling",
      "object": "model",
      "created": 1784035394,
      "owned_by": "thinkingmachines",
      "architecture": {
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"]
      },
      "providers": [
        {
          "provider": "together",
          "status": "live",
          "context_length": 524288,
          "pricing": { "input": 1.0, "output": 4.05 },
          "is_free": false,
          "supports_tools": true,
          "supports_structured_output": true,
          "first_token_latency_ms": 218.6,
          "throughput": 110.1,
          "is_model_author": false
        }
      ]
    }
  ]
}
```

**Key fields:**
- `architecture.input_modalities` / `architecture.output_modalities` — model modality (text, image, audio)
- `providers[].pricing` — per-million-token pricing in USD (`input` / `output`)
- `providers[].first_token_latency_ms` — average time to first token
- `providers[].throughput` — tokens per second
- `providers[].supports_tools` — function/tool calling support
- `providers[].supports_structured_output` — JSON mode / structured output support
- `providers[].is_free` — whether this provider serves this model for free
- `providers[].status` — `live` or other status

---

### Authentication

- **Token type**: Fine-grained token with `inference.serverless.write` permission
- **Auth method**: Bearer token in Authorization header
- **Create token**: https://hf.co/settings/tokens/new?ownUserPermissions=inference.serverless.write&tokenType=fineGrained

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key="hf_..."  # your HF token
)
```

```bash
curl https://router.huggingface.co/v1/chat/completions \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "model": "Qwen/QwQ-32B:fastest"
  }'
```

---

### Integration Patterns

#### 1. Python with OpenAI SDK
```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ["HF_TOKEN"],
)

completion = client.chat.completions.create(
    model="Qwen/QwQ-32B:cheapest",  # use cheapest provider
    messages=[{"role": "user", "content": "What is the speed of light?"}],
)

print(completion.choices[0].message.content)
```

#### 2. JavaScript with OpenAI SDK
```javascript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://router.huggingface.co/v1",
  apiKey: process.env.HF_TOKEN,
});

const completion = await client.chat.completions.create({
  model: "openai/gpt-oss-120b:fastest",
  messages: [{ role: "user", content: "Hello!" }],
});

console.log(completion.choices[0].message);
```

#### 3. Streaming
```python
stream = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V4-Pro:fastest",
    messages=[{"role": "user", "content": "Write a poem"}],
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")
```

#### 4. Tool/Function Calling
```python
completion = client.chat.completions.create(
    model="Qwen/QwQ-32B:fastest",
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                }
            }
        }
    }],
    tool_choice="auto",
)
```

#### 5. Structured Outputs
```python
completion = client.chat.completions.create(
    model="openai/gpt-oss-120b:fastest",
    messages=[{"role": "user", "content": "Extract: John is 30"}],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "person",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                }
            }
        }
    }
)
```

---

### Comparison: InferenceClient vs Router Endpoint

| Feature | InferenceClient | Router Endpoint |
|---------|----------------|-----------------|
| **API style** | HF-native (InferenceClient) | OpenAI-compatible |
| **Base URL** | `https://api-inference.huggingface.co` | `https://router.huggingface.co/v1` |
| **Provider selection** | Client-side (`provider` param) | Server-side (model suffix) |
| **Supported tasks** | All (chat, image, audio, embeddings, etc.) | Chat completions only |
| **SDK required** | `huggingface_hub` / `@huggingface/inference` | Any OpenAI SDK |
| **Model listing** | N/A | `/v1/models` with provider metadata |
| **Streaming** | ✅ | ✅ |
| **Tool calling** | ✅ | ✅ (provider-dependent) |
| **Structured outputs** | ✅ | ✅ (provider-dependent) |
| **Free tier** | ✅ (HF Inference provider) | ✅ (via :cheapest or specific providers) |
| **Auto-failover** | ✅ (explicit retry) | ✅ (built-in, transparent) |
| **Migration from OpenAI** | Requires code changes | Drop-in replacement (change base URL + API key) |

---

### Provider Availability per Model

Use the Hub API to find which providers serve a specific model:

```bash
# List providers for Qwen/QwQ-32B
curl -s "https://router.huggingface.co/v1/models" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
for m in data['data']:
    if m['id'] == 'Qwen/QwQ-32B':
        for p in m['providers']:
            print(f\"{p['provider']}: \${p['pricing']['output']}/M tok, {p['throughput']:.0f} tok/s, tools={p['supports_tools']})
"
```

Or use the Hub models API with `inference_provider` filter:

```bash
# List all models served by Groq
curl -s "https://huggingface.co/api/models?inference_provider=groq" | jq '.[].id'

# List models with inference warm status
curl -s "https://huggingface.co/api/models/google/gemma-3-27b-it?expand[]=inference"
```

---

### Free Tier Details

- Some providers offer free inference for certain models (`is_free: true` in provider metadata)
- The `hf-inference` provider (Hugging Face's own serverless) offers free CPU inference for smaller/classic models (BERT, GPT-2, embeddings, classification, etc.)
- Third-party providers may have their own free tiers with rate limits
- Use `:cheapest` policy to automatically pick the lowest-cost provider
- Check `/v1/models` for `is_free` field per provider

---

### Limitations

1. **Chat completions only** — no text-to-image, embeddings, audio, or other tasks through the Router endpoint
2. **No metadata-only filtering** — the `/v1/models` endpoint returns all models without free/provider filtering parameters (use Hub API for filtered discovery)
3. **Provider feature parity** — not all providers support tools, structured outputs, or streaming; check `supports_tools` and `supports_structured_output` per provider
4. **No custom headers** — the Router does not support provider-specific HTTP headers or configuration beyond the model suffix
5. **Rate limits** — determined by the selected provider, not by Hugging Face's proxy

---

### Skill Created
`hf-inference-router-openai-compatible-endpoint/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md with complete documentation, architecture diagrams, provider selection reference, integration patterns, and comparison matrix.

---

## 2026-07-25: HF Inference Router — Practical Patterns Deep-Dive (Topic #363)

### Summary
Comprehensive deep-dive into the HF Inference Router's practical usage patterns — covering the new **Responses API (beta)** with event-driven streaming and Remote MCP, **structured outputs** with Pydantic/JSON Schema via both `chat.completions` and `responses` APIs, **function calling** execution patterns with tool_choice control, advanced **pricing model** (free tier, Custom Provider Key, Organization billing), and the full **18-provider ecosystem** with capability matrix. This builds on Topic #361 (Router architecture and API surface) to add real-world usage patterns, zero-cost strategies, and the latest Inference Providers features.

**Model:** deepseek-v4-flash · **Provider:** opencode-go

---

### 1. Responses API (Beta) — Unified Event-Driven Interface

The Responses API is a new OpenAI-compatible interface (not to be confused with the older `chat.completions` endpoint) that provides a unified interface for agentic apps with built-in tool orchestration, event-driven streaming, reasoning controls, and Remote MCP tools.

#### 1.1 Configuration

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ["HF_TOKEN"],
)
```

Model IDs support the same provider suffixes as `chat.completions`:
- `model="openai/gpt-oss-120b:groq"` — explicit provider
- `model="moonshotai/Kimi-K2-Instruct-0905"` — auto (`:fastest` default)

#### 1.2 Core Patterns

| Pattern | Description | Key Parameter |
|---------|-------------|---------------|
| **Plain text output** | Single response via `input` string | `input="tell me a story"` |
| **Multimodal inputs** | Mix text + images in `input` array | `input=[{"role":"user","content":[{"type":"input_text"},{"type":"input_image"}]}]` |
| **Multi-turn** | Pass conversation history as `input` array | Add `developer`, `system`, `user` roles |
| **Event streaming** | Receive incremental `response.*` events | `stream=True` |
| **Tool calling** | Functions + MCP tools in `tools` array | `tools=[{"type":"function"}]` |
| **Structured outputs** | Pydantic model via `.parse()` | `text_format=CalendarEvent` |
| **Reasoning controls** | Dial effort up/down | `reasoning={"effort": "low" \| "medium" \| "high"}` |
| **Remote MCP** | Call server-hosted MCP tools | `tools=[{"type":"mcp", "server_url":"..."}]` |

#### 1.3 Event-Driven Streaming

Set `stream=True` to receive incremental events:

```python
stream = client.responses.create(
    model="moonshotai/Kimi-K2-Instruct-0905:groq",
    input=[{"role": "user", "content": "Say 'hello' ten times fast."}],
    stream=True,
)
for event in stream:
    print(event)
```

Events include: `response.created`, `output_text.delta`, `response.completed` — enabling incremental UI rendering and real-time tool monitoring.

#### 1.4 Structured Outputs via `.parse()` (Responses API)

```python
from pydantic import BaseModel

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

response = client.responses.parse(
    model="openai/gpt-oss-120b:groq",
    input=[{"role": "system", "content": "Extract event info."},
           {"role": "user", "content": "Alice and Bob are going to a science fair on Friday."}],
    text_format=CalendarEvent,
)
print(response.output_parsed)  # Typed Pydantic object, not raw JSON string
```

**Key insight:** `.output_parsed` returns the typed Pydantic object directly — no manual `json.loads()` needed.

#### 1.5 Remote MCP Tool Integration

The Responses API can call server-hosted MCP tools directly:

```python
response = client.responses.create(
    model="moonshotai/Kimi-K2-Instruct-0905:groq",
    input="how does tiktoken work?",
    tools=[{
        "type": "mcp",
        "server_label": "gitmcp",
        "server_url": "https://gitmcp.io/openai/tiktoken",
        "allowed_tools": ["search_tiktoken_documentation", "fetch_tiktoken_documentation"],
        "require_approval": "never",
    }],
)
for output in response.output:
    print(output)
```

**Key parameters:**
- `server_label` — Unique identifier for the MCP server
- `server_url` — URL of the remote MCP server
- `allowed_tools` — List of tool names to expose (security measure)
- `require_approval` — `"always"` | `"never"` | `"on_each_tool"`

#### 1.6 Reasoning Effort Controls

```python
response = client.responses.create(
    model="openai/gpt-oss-120b:groq",
    instructions="You are a helpful assistant.",
    input="Say hello to the world.",
    reasoning={"effort": "low"},  # low | medium | high
)
for i, item in enumerate(response.output):
    print(f"Output #{i}: {item.type}", item.content)
```

---

### 2. Structured Outputs with `chat.completions` (Standard API)

When using the standard `chat.completions.create()` endpoint, structured outputs work via `response_format`:

#### 2.1 Using `huggingface_hub` (InferenceClient)

```python
from huggingface_hub import InferenceClient
from pydantic import BaseModel
import json

client = InferenceClient(provider="cerebras", api_key=os.environ["HF_TOKEN"])

class PaperAnalysis(BaseModel):
    title: str
    abstract_summary: str

response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "PaperAnalysis",
        "schema": PaperAnalysis.model_json_schema(),
        "strict": True,
    },
}

response = client.chat_completion(
    messages=[{"role": "system", "content": "Extract paper title and abstract summary."},
              {"role": "user", "content": paper_text}],
    response_format=response_format,
    model="Qwen/Qwen3-32B",
)
structured_data = json.loads(response.choices[0].message.content)
print(f"Title: {structured_data['title']}")
```

#### 2.2 Using OpenAI SDK

```python
completion = client.chat.completions.create(
    model="openai/gpt-oss-120b:groq",
    messages=[{"role": "user", "content": "Extract: John is 30 years old from Paris."}],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "person",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                    "city": {"type": "string"},
                },
                "required": ["name", "age", "city"],
            },
        },
    },
)
```

**Important:** When using `openai/gpt-oss-120b:groq` from JavaScript or raw HTTP, include a brief instruction to return JSON — without it the model may emit markdown even when a schema is provided.

---

### 3. Function Calling Execution Patterns

Full function calling involves defining the tool schema, calling the model, executing the function, and returning the result:

#### 3.1 Define Tool Schema

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "Get current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
            },
            "required": ["location"],
        },
    },
}]
```

#### 3.2 First Call — Model Decides to Call Tool

```python
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1-0528",
    messages=[
        {"role": "system", "content": "You are a helpful assistant with access to weather data."},
        {"role": "user", "content": "What's the weather like in San Francisco?"},
    ],
    tools=tools,
    tool_choice="auto",  # auto | required | specific function name
)
response_message = response.choices[0].message
```

**tool_choice options:**
| Value | Behavior |
|-------|----------|
| `"auto"` | Model decides when to call (0+ calls) |
| `"required"` / `"any"` | Model MUST call at least one tool |
| `{"type":"function","function":{"name":"func_name"}}` | Force specific function |
| `"none"` | Disable tool calling |

#### 3.3 Execute Tool and Return Result

```python
# Check for tool calls
if response_message.tool_calls:
    for tool_call in response_message.tool_calls:
        if tool_call.function.name == "get_current_weather":
            args = json.loads(tool_call.function.arguments)
            weather = get_current_weather(args["location"])

            # Append tool call + result to messages
            messages.append(response_message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(weather),
            })

    # Second call — model synthesizes response with tool results
    final_response = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-R1-0528",
        messages=messages,
        tools=tools,
    )
    print(final_response.choices[0].message.content)
```

#### 3.4 Zero-Cost Function Calling Setup

For Beer's budget-constrained environment:
- **Provider**: `hf-inference` (free CPU) for classic models — but limited tool support
- **Provider**: `groq` (has generous free tier, supports tools on models like Llama, Gemma, Mixtral)
- **Check**: Query `/v1/models` for `supports_tools: true` AND `is_free: true`

```python
# Find free providers that support tools
import requests
data = requests.get("https://router.huggingface.co/v1/models",
    headers={"Authorization": f"Bearer {os.environ['HF_TOKEN']}"}).json()
for m in data["data"]:
    for p in m["providers"]:
        if p["is_free"] and p["supports_tools"]:
            print(f"{m['id']} via {p['provider']}")
```

---

### 4. Pricing & Billing Model

#### 4.1 Free Tier Credits

| Account Type | Monthly Credits | Pay-as-you-go |
|-------------|----------------|---------------|
| **Free Users** | **$0.10** (subject to change) | ✅ (purchase credits) |
| **PRO Users** | **$2.00** | ✅ |
| **Team/Enterprise** | **$2.00 per seat** | ✅ |

**Zero-cost note for Beer:** The $0.10 monthly free credit covers hundreds of lightweight inference calls. Use free providers (`is_free: true`) to stretch credits further.

#### 4.2 Billing Approaches

| Feature | Routed by HF | Custom Provider Key |
|---------|-------------|-------------------|
| How it works | Request routes through HF to provider | Pre-set provider key in HF settings |
| Billing | Pay-as-you-go on HF account | Billed directly by provider |
| Monthly credits | ✅ Apply | ❌ Don't apply |
| Provider account needed | ❌ No | ✅ Yes |
| Best for | Simplicity, experimentation | Billing control, non-integrated providers |

#### 4.3 Organization Billing

Pass `X-HF-Bill-To` header or `bill_to` parameter to bill a Team/Enterprise organization:

```python
client = InferenceClient(bill_to="my-org-name")
completion = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3-0324",
    messages=[{"role": "user", "content": "Hello"}],
)
```

Enterprise can also attribute costs to Resource Groups using `X-HF-Bill-To: <resource-group-id>`.

#### 4.4 HF Inference (formerly Serverless API) Costs

The `hf-inference` provider charges based on compute time × hardware cost:
- CPU inference: Free for classic models (BERT, GPT-2, embeddings, text-classification)
- GPU inference: Billed per-second (e.g., 10s on FLUX.1-dev at $0.00012/s = $0.0012)

---

### 5. Provider Ecosystem — Full Capability Matrix

18+ providers integrated as of July 2026:

| Provider | Chat LLM | Chat VLM | Feature Extraction | Text-to-Image | Text-to-Video | Speech-to-Text |
|----------|----------|----------|-------------------|---------------|---------------|----------------|
| **Cerebras** | ✅ | — | — | — | — | — |
| **Cohere** | ✅ | — | ✅ | — | — | — |
| **DeepInfra** | ✅ | ✅ | — | — | — | — |
| **Fal AI** | ✅ | ✅ | — | ✅ | ✅ | — |
| **Featherless AI** | ✅ | ✅ | — | — | — | — |
| **Fireworks** | ✅ | ✅ | — | — | — | — |
| **Groq** | ✅ | ✅ | — | — | — | — |
| **HF Inference** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Novita** | ✅ | ✅ | ✅ | — | — | — |
| **Nscale** | ✅ | ✅ | ✅ | — | — | — |
| **OVHcloud** | ✅ | ✅ | — | — | — | — |
| **Public AI** | ✅ | ✅ | — | — | — | — |
| **Replicate** | ✅ | ✅ | ✅ | — | — | — |
| **Scaleway** | ✅ | ✅ | — | — | — | — |
| **Together** | ✅ | ✅ | ✅ | — | — | — |
| **WaveSpeedAI** | ✅ | — | — | — | — | — |
| **Z.ai** | ✅ | ✅ | — | — | — | — |
| **Hub API** | Provider registration program | | | | | |

**Key insight:** Only `hf-inference` provides all task types (chat, image, video, audio, speech). Third-party providers primarily focus on chat completion.

---

### 6. Zero-Cost Patterns for Beer

| Pattern | How | Cost |
|---------|-----|------|
| **Free provider routing** | Use `:cheapest` or check `is_free` in `/v1/models` | $0 |
| **Responses API on free models** | Query free models supporting tools | $0 (credit) |
| **Structured outputs via free providers** | Check `supports_structured_output` + `is_free` | $0 (credit) |
| **Custom Provider Key** | Use existing Groq/Together key via HF settings | Provider's free tier |
| **Credit conservation** | Cache responses, batch requests, use small models | $0.10/mo covers light use |
| **Function calling on Groq** | Groq offers free inference with tool support | $0 (free tier) |

#### Find Free Models with Capabilities

```python
import requests, os
data = requests.get(
    "https://router.huggingface.co/v1/models",
    headers={"Authorization": f"Bearer {os.environ['HF_TOKEN']}"}
).json()
free_tool_models = []
for m in data["data"]:
    for p in m["providers"]:
        if p.get("is_free") and p.get("supports_tools"):
            free_tool_models.append((m["id"], p["provider"], p["throughput"]))
free_tool_models.sort(key=lambda x: -x[2])  # fastest first
for mid, prov, tput in free_tool_models[:10]:
    print(f"{mid:50s} {prov:15s} {tput:8.1f} tok/s")
```

---

### 7. Key New Integrations (for Coding Agents)

HF Inference Providers now has dedicated integration guides for:

| Agent | Setup |
|-------|-------|
| **OpenCode** | /docs/inference-providers/en/integrations/opencode |
| **Pi** | /docs/inference-providers/en/integrations/pi |
| **Codex** | /docs/inference-providers/en/integrations/codex |
| **Claude Code** | /docs/inference-providers/en/integrations/claude-code |
| **Hermes Agent** | /docs/inference-providers/en/integrations/hermes-agent |
| **Vision Agents** | /docs/inference-providers/en/integrations/visionagents |

These integrations allow coding agents to use the Router as a drop-in OpenAI-compatible endpoint with a single HF token.

---

### 8. Trade-offs Summary

| Approach | Pros | Cons |
|----------|------|------|
| **chat.completions** | Standard OpenAI API, full tool support, streaming | Must handle tool execution manually |
| **responses.create()** | Built-in tool orchestration, MCP tools, `.parse()`, reasoning controls | Beta status, fewer provider guarantees |
| **InferenceClient** | All task types (image, audio, video), client-side provider selection | Non-OpenAI API, requires huggingface_hub |

---

### Skill Updated
`hf-inference-router-openai-compatible-endpoint/` — SKILL.md updated, references/hf-learnings.md extended with practical patterns deep-dive (Topic #363).

### Sources
- https://huggingface.co/docs/inference-providers/en/index — Inference Providers docs
- https://huggingface.co/docs/inference-providers/en/guides/responses-api — Responses API guide
- https://huggingface.co/docs/inference-providers/en/guides/structured-output — Structured outputs guide
- https://huggingface.co/docs/inference-providers/en/guides/function-calling — Function calling guide
- https://huggingface.co/docs/inference-providers/en/pricing — Pricing and billing
- https://huggingface.co/docs/inference-providers/en/guides/first-api-call — Getting started
- https://huggingface.co/docs/inference-providers/en/guides/building-first-app — Building first app
