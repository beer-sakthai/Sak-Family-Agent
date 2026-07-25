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
