# Hugging Face InferenceClient — Python Serverless Inference Guide

`InferenceClient` (`huggingface_hub`) is the Python client for HF's Inference API (serverless). It routes requests through multiple providers (Together, Replicate, fal.ai, Novita, etc.) with automatic or explicit provider selection.

---

## Quick Start

```python
from huggingface_hub import InferenceClient

client = InferenceClient()  # uses HF_TOKEN env var automatically

# Chat completion
result = client.chat_completion(
    model="deepseek-ai/DeepSeek-R1",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(result.choices[0].message.content)

# Text-to-image
image = client.text_to_image(
    "A majestic lion in a fantasy forest",
    model="black-forest-labs/FLUX.1-schnell",
)
image.save("lion.png")
```

---

## Provider Selection

```python
# Automatic (fastest available — default)
client = InferenceClient()

# Explicit provider
client = InferenceClient(provider="fal-ai")
client = InferenceClient(provider="together")
client = InferenceClient(provider="novita")
client = InferenceClient(provider="replicate")

# Per-call override — pass provider= to individual methods
result = client.chat_completion(
    model="meta-llama/Llama-3.3-70B-Instruct",
    messages=[{"role": "user", "content": "Hi"}],
    provider="together",
)
```

**Provider Selection Policies:**
| Policy | Meaning |
|--------|---------|
| `auto` (default) | Fastest available provider (highest throughput) |
| `provider="together"` | Force specific provider |
| `:fastest` suffix | Fastest provider (OpenAI-compatible endpoint) |
| `:cheapest` suffix | Lowest cost provider (OpenAI-compatible endpoint) |
| `:preferred` suffix | Your preference order from HF settings |

---

## OpenAI-Compatible Endpoint

For chat completions only, use the drop-in OpenAI-compatible endpoint:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ["HF_TOKEN"],
)

completion = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1:fastest",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

Or with curl:

```bash
curl https://router.huggingface.co/v1/chat/completions \
  -H "Authorization: Bearer $HF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/DeepSeek-R1:fastest",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## Streaming

```python
# Streaming chat
stream = client.chat_completion(
    model="meta-llama/Llama-3.3-70B-Instruct",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")
```

---

## Async Client

```python
from huggingface_hub import AsyncInferenceClient
import asyncio

async def main():
    client = AsyncInferenceClient()
    result = await client.chat_completion(
        model="mistralai/Mistral-7B-Instruct-v0.3",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    print(result.choices[0].message.content)

asyncio.run(main())
```

---

## Task-Specific Methods

| Method | Task |
|--------|------|
| `chat_completion()` | Chat / text generation |
| `text_generation()` | Raw text generation (non-chat) |
| `text_to_image()` | Image generation |
| `image_classification()` | Classify images |
| `image_segmentation()` | Segment images |
| `object_detection()` | Detect objects |
| `automatic_speech_recognition()` | Speech-to-text |
| `text_to_speech()` | Text-to-speech |
| `text_to_audio()` | Audio generation |
| `feature_extraction()` | Embeddings |
| `sentence_similarity()` | Compare texts |
| `fill_mask()` | Masked language modeling |
| `summarization()` | Text summarization |
| `translation()` | Machine translation |
| `zero_shot_classification()` | Zero-shot classification |
| `tabular_classification()` / `tabular_regression()` | Tabular tasks |

---

## Custom Endpoint (Inference Endpoints or Spaces)

Point InferenceClient at a deployed Endpoint or Space:

```python
client = InferenceClient("https://my-endpoint.hf.co")
# or with a specific model
client = InferenceClient(model="my-org/my-model")
```

---

## Timeout

```python
from huggingface_hub import InferenceClient, InferenceTimeoutError

client = InferenceClient(timeout=30)
try:
    result = client.chat_completion(...)
except InferenceTimeoutError:
    print("Inference timed out after 30s.")
```

---

## Binary Inputs

Accepted types for image/audio inputs:
- Raw `bytes`
- File-like object: `with open("audio.flac", "rb") as f: ...`
- Local path: `str` or `Path`
- Remote URL: `"https://example.com/image.jpg"`

```python
client.image_classification(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Cute_dog.jpg/320px-Cute_dog.jpg"
)
```

---

## Billing

```python
# Charge to an Enterprise Hub org
client = InferenceClient(provider="fal-ai", bill_to="my-org")
```

Free users get monthly credits. PRO and Enterprise get higher limits. Credits are consumed per request based on provider pricing.

---

## Function Calling

```python
client.chat_completion(
    model="meta-llama/Llama-3.3-70B-Instruct",
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                },
                "required": ["location"]
            }
        }
    }],
    tool_choice="auto",
)
```

---

## Structured Outputs / JSON Mode

```python
client.chat_completion(
    model="meta-llama/Llama-3.3-70B-Instruct",
    messages=[{"role": "user", "content": "List 3 capitals"}],
    response_format={
        "type": "json_object",
        "schema": {
            "type": "object",
            "properties": {
                "capitals": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
    },
)
```

---

## When to Use Which

| Approach | Best For |
|----------|----------|
| `InferenceClient` Python | All tasks, explicit provider control, async |
| OpenAI-compat endpoint | Chat-only, drop-in migration from OpenAI SDK |
| Direct HTTP/curl | Custom integrations, non-Python environments |
| Spaces custom endpoint | Deployed custom models with Gradio/API |

---

## References
- [HF docs: Run Inference on servers](https://huggingface.co/docs/huggingface_hub/en/guides/inference)
- [Inference Providers docs](https://huggingface.co/docs/inference-providers/en/index)
- [InferenceClient API reference](https://huggingface.co/docs/huggingface_hub/en/package_reference/inference_client)
- [Inference Providers announcement blog](https://huggingface.co/blog/inference-providers)
