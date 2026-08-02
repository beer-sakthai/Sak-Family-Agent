# HF Learnings Log — hf-inference-client-openai

## 2026-07-25: hf-inference-client-openai-compatibility-and-structured-outputs — Inference Client OpenAI API Compatibility & Structured Outputs Deep Dive (Topic #262)

### Summary
Comprehensive deep-dive on Hugging Face `InferenceClient`'s OpenAI API compatibility layer and structured output capabilities. Covers the OpenAI-compatible `client.chat.completions.create()` syntax (drop-in replacement for `openai.OpenAI`), JSON Schema and regex grammar for structured outputs via `response_format`, JSON mode vs structured outputs distinction, function/tool calling with OpenAI-compatible schemas, streaming support, full parameter reference, provider compatibility matrix, and practical patterns for each feature.

### Source
- HF InferenceClient docs (guides/inference): https://huggingface.co/docs/huggingface_hub/main/en/guides/inference
- HF InferenceClient API reference: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/inference_client
- InferenceClient.chat_completion: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/inference_client#huggingface_hub.InferenceClient.chat_completion
- Inference Providers docs: https://huggingface.co/docs/inference-providers/en/index
- OpenAI Python client: https://github.com/openai/openai-python

### Skill
hf-inference-client-openai — Hugging Face InferenceClient OpenAI compatibility deep reference: chat.completions.create API, structured outputs (JSON Schema/regex), JSON mode, function calling, streaming, full parameter surface, 17+ provider support, and drop-in OpenAI migration patterns

---

### 1. OpenAI Compatibility — Drop-In Replacement

The `InferenceClient` is designed as a **drop-in replacement for OpenAI's Python client**. Only two lines need to change:

```python
# Before (OpenAI)
from openai import OpenAI
client = OpenAI(base_url=..., api_key=...)

# After (Hugging Face)
from huggingface_hub import InferenceClient
client = InferenceClient(base_url=..., api_key=...)
```

The rest of the code stays the same:

```python
output = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Count to 10"},
    ],
    stream=True,
    max_tokens=1024,
)

for chunk in output:
    print(chunk.choices[0].delta.content or "", end="")
```

Key points:
- `client.chat.completions.create()` maps to `InferenceClient.chat_completion()` internally
- The same `model` parameter accepts HF Hub model IDs or Inference Endpoint URLs
- `base_url` is set at initialization time (not per-call) for custom endpoints
- When `base_url` is set, the client talks directly to that endpoint

#### 1.1 Using with Local Endpoints

`InferenceClient` can connect to any OpenAI-compatible local inference server:

```python
client = InferenceClient(model="http://localhost:8080")

response = client.chat.completions.create(
    messages=[{"role": "user", "content": "What is the capital of France?"}],
    max_tokens=100
)
print(response.choices[0].message.content)
```

Supported local servers: llama.cpp, vLLM, LiteLLM, TGI, Ollama, mlx.

#### 1.2 Using with Inference Providers

```python
# Specific provider with routing through HF
client = InferenceClient(
    provider="together",
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    api_key="hf_****"  # HF token (routed billing)
)

# Direct provider API key
client = InferenceClient(
    provider="together",
    api_key="my_together_api_key"  # Direct provider key
)
```

---

### 2. Structured Outputs — JSON Schema

Structured Outputs enforce **both valid JSON and conformance to a predefined JSON Schema**. This is the strict mode for reliable downstream processing.

#### 2.1 How It Works

Set `response_format` to `{"type": "json_schema", "json_schema": {...}}`:

```python
from huggingface_hub import InferenceClient

json_schema = {
    "name": "book",
    "schema": {
        "properties": {
            "name": {
                "title": "Name",
                "type": "string"
            },
            "author": {
                "title": "Author",
                "type": "string"
            },
            "year": {
                "title": "Year",
                "type": "integer"
            }
        },
        "required": ["name", "author", "year"],
        "title": "Book",
        "type": "object"
    },
    "strict": True
}

client = InferenceClient(
    provider="cerebras",
    api_key="your_key"
)

completion = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3.1-8B-Instruct",
    messages=[
        {"role": "user", "content": "Create a book entry for 'The Great Gatsby' by F. Scott Fitzgerald, published 1925."}
    ],
    response_format={
        "type": "json_schema",
        "json_schema": json_schema,
    },
)

print(completion.choices[0].message.content)
# Output: {"name":"The Great Gatsby","author":"F. Scott Fitzgerald","year":1925}
```

#### 2.2 JSON Schema Structure

The `json_schema` object follows standard JSON Schema (OpenAI-compatible format):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | Yes | Schema name identifier |
| `schema` | `dict` | Yes | The JSON Schema definition |
| `schema.properties` | `dict` | Yes | Field definitions with `type` and `title` |
| `schema.required` | `list[str]` | Yes | Required field names |
| `schema.title` | `str` | No | Schema display name |
| `strict` | `bool` | No | Whether to enforce strict schema adherence (default: true) |

Supported types in `properties`: `string`, `integer`, `number`, `boolean`, `array`, `object`.

#### 2.3 Provider Support for Structured Outputs

Not all providers support structured outputs. Check provider documentation. As of 2026-07-25, providers with `chat_completion()` support may or may not implement `json_schema`. The `response_format` parameter is forwarded to the provider, and unsupported providers return an error.

---

### 3. JSON Mode

JSON Mode produces **syntactically valid JSON** but does NOT enforce a schema. It's lighter than structured outputs:

```python
completion = client.chat.completions.create(
    model="...",
    messages=[
        {"role": "system", "content": "You are a helpful assistant that responds in JSON."},
        {"role": "user", "content": "Create a book entry for 'The Great Gatsby'."}
    ],
    response_format={"type": "json_object"},
)
```

Key differences:

| Feature | JSON Mode | Structured Outputs |
|---------|-----------|---------------------|
| Schema enforcement | No | Yes (JSON Schema) |
| Guaranteed valid JSON | Yes | Yes |
| Type constraints | No | Yes |
| Provider support | Wider | Narrower |
| Use case | Free-form JSON parsing | Reliable downstream extraction |

---

### 4. Function Calling / Tool Use

`InferenceClient` supports OpenAI-compatible function calling via `tools` and `tool_choice` parameters:

```python
completion = client.chat.completions.create(
    model="...",
    messages=[
        {"role": "user", "content": "What's the weather in Paris?"}
    ],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City name"},
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                    },
                    "required": ["location"]
                }
            }
        }
    ],
    tool_choice="auto",  # "auto", "none", or {"type": "function", "function": {"name": "get_weather"}}
)
```

Parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `tools` | `list[ChatCompletionInputTool]` | Function definitions the model can call |
| `tool_choice` | `str` or `dict` | `"auto"` (default), `"none"`, or specific function |
| `tool_prompt` | `str` | Custom prompt prepended before tools |

The output contains `tool_calls` in the message when the model decides to call a function:

```python
message = completion.choices[0].message
if message.tool_calls:
    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        # Execute the function...
```

---

### 5. Streaming Support

Streaming follows the OpenAI SSE (Server-Sent Events) format:

```python
stream = client.chat.completions.create(
    model="...",
    messages=[{"role": "user", "content": "Count to 10"}],
    stream=True,
    max_tokens=1024,
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

Streaming options via `stream_options`:

```python
from huggingface_hub import ChatCompletionInputStreamOptions

stream = client.chat.completions.create(
    ...,
    stream=True,
    stream_options=ChatCompletionInputStreamOptions(
        include_usage=True  # Include token usage in final chunk
    ),
)
```

Non-streaming returns `ChatCompletionOutput`, streaming returns `Iterable[ChatCompletionStreamOutput]`.

---

### 6. Full Parameter Reference

The `chat.completions.create()` method accepts these parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `messages` | `list[dict]` | Required | Conversation history (role + content pairs) |
| `model` | `str` | Recommended | Model ID or endpoint URL |
| `frequency_penalty` | `float` | 0.0 | [-2.0, 2.0] Penalize frequent tokens |
| `logit_bias` | `list[float]` | None | Adjust token likelihood |
| `logprobs` | `bool` | False | Return log probabilities |
| `max_tokens` | `int` | 100 | Max tokens in response |
| `n` | `int` | 1 | Number of completions to generate |
| `presence_penalty` | `float` | 0.0 | [-2.0, 2.0] Penalize repeated topics |
| `response_format` | `dict` | None | `json_schema` or `json_object` |
| `seed` | `int` | None | Reproducible generation |
| `stop` | `list[str]` | None | Stop sequences (max 4) |
| `stream` | `bool` | False | Enable streaming |
| `stream_options` | `dict` | None | Streaming configuration |
| `temperature` | `float` | 1.0 | [0, 2] Randomness control |
| `top_logprobs` | `int` | None | [0, 5] Top-K logprobs per token |
| `top_p` | `float` | 1.0 | [0, 1] Nucleus sampling |
| `tool_choice` | `str/dict` | "auto" | Function calling mode |
| `tools` | `list` | None | Function definitions |
| `tool_prompt` | `str` | None | Custom tool prompt |
| `extra_body` | `dict` | None | Provider-specific parameters |

---

### 7. Provider Compatibility Matrix (Chat Completion)

As of 2026-07-25, these providers support `chat_completion()`:

| Provider | Chat Completion | Structured Outputs | Function Calling |
|----------|----------------|-------------------|------------------|
| Cerebras | ✅ | Check provider | Check provider |
| Cohere | ✅ | Check provider | Check provider |
| DeepInfra | ✅ | Check provider | Check provider |
| Featherless AI | ✅ | Check provider | Check provider |
| Fireworks AI | ✅ | Check provider | Check provider |
| Groq | ✅ | Check provider | Check provider |
| HF Inference | ✅ | Check provider | Check provider |
| Novita AI | ✅ | Check provider | Check provider |
| Nscale | ✅ | Check provider | Check provider |
| OVHcloud AI Endpoints | ✅ | Check provider | Check provider |
| Public AI | ✅ | Check provider | Check provider |
| Scaleway | ✅ | Check provider | Check provider |
| Together | ✅ | Check provider | Check provider |
| Zai | ✅ | Check provider | Check provider |

**Not supported**: Replicate, fal-ai, Wavespeed (do not support chat completion).

> Always check the provider's documentation for feature support.

---

### 8. Authentication Modes

Two authentication paths:

**1. Routed through Hugging Face (proxy mode):**
```python
client = InferenceClient(
    provider="together",
    api_key="hf_****"  # Your HF User Access Token
)
```
Usage billed to HF account. HF acts as proxy with provider keys.

**2. Direct provider access:**
```python
client = InferenceClient(
    provider="together",
    api_key="tgp_****"  # Direct Together AI API key
)
```
Usage billed to your provider account directly.

**3. Local token (auto-detected):**
```python
# Uses token from `huggingface-cli login`
client = InferenceClient(provider="together")
```

---

### 9. Response Types

#### Non-streaming (`ChatCompletionOutput`)
```python
output = client.chat.completions.create(...)
# output.choices[0].message.content       → str
# output.choices[0].finish_reason         → "stop" | "length" | "eos_token"
# output.usage.prompt_tokens              → int
# output.usage.completion_tokens          → int
# output.usage.total_tokens               → int
# output.model                            → str
```

#### Streaming (`ChatCompletionStreamOutput`)
```python
for chunk in stream:
    # chunk.choices[0].delta.content       → str | None
    # chunk.choices[0].finish_reason       → str | None
    # chunk.choices[0].index               → int
```

---

### 10. Zero-Cost Pathways

| Pathway | Cost | Details |
|---------|------|---------|
| **HF Inference (free tier)** | Free | Rate-limited, no API key needed for small usage |
| **Local endpoints** | Free | llama.cpp, vLLM, TGI on your hardware |
| **Provider free tiers** | Free | Groq, Together, DeepInfra offer free tiers |
| **Routed through HF** | Paid | Billed to HF account at provider rates |
| **Direct provider keys** | Paid | Billed at provider rates |

---

### 11. Practical Migration Guide

#### From OpenAI to InferenceClient

```python
# Step 1: Change import
from huggingface_hub import InferenceClient

# Step 2: Change client initialization
client = InferenceClient(
    model="meta-llama/Meta-Llama-3-8B-Instruct",  # HF model ID
    provider="together",  # or any supported provider
    api_key="hf_****",  # HF token (routed) or provider key (direct)
)

# Step 3: Everything else stays the same
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=100,
)
```

#### Key Differences to Remember

| Aspect | OpenAI | Hugging Face InferenceClient |
|--------|--------|------------------------------|
| Model IDs | `gpt-4`, `gpt-3.5-turbo` | HF Hub model IDs (`meta-llama/Llama-3.1-8B-Instruct`) |
| Provider selection | OpenAI only | 17+ providers via `provider=` |
| Authentication | OpenAI API key | HF token (routed) or provider key (direct) |
| Default max_tokens | None (unlimited) | 100 |
| Structured outputs | JSON Schema | JSON Schema + regex (grammar) |
| Base URL | For self-hosted | For local/self-hosted endpoints |

---

### Zero-Cost Note

All research for this deep-dive was performed by reading the public Hugging Face documentation and Hugging Face Hub source code. No paid API calls were made. Development and testing can be done using free provider tiers (Groq, DeepInfra) or local inference servers (llama.cpp, vLLM).
