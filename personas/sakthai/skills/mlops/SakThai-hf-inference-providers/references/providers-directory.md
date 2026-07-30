# Inference Providers Directory

Complete provider list verified from HF docs (2026-07). Use for quick-lookup of which providers support which task types.

## Chat Completion (LLM)

| Provider | Slug | Notes |
|----------|------|-------|
| Cerebras | `cerebras` | High-speed inference |
| Cohere | `cohere` | Also supports VLM |
| DeepInfra | `deepinfra` | Broad LLM catalog |
| Featherless AI | `featherless-ai` | |
| Fireworks | `fireworks-ai` | |
| Groq | `groq` | Fast LPU inference |
| HF Inference | `hf-inference` | HF's own infra |
| Novita | `novita` | |
| Nscale | `nscale` | |
| OVHcloud | `ovhcloud` | EU-hosted |
| Public AI | `publicai` | |
| Scaleway | `scaleway` | EU-hosted, also embeddings |
| Together | `together` | Broad catalog |
| Z.ai | `zai-org` | |

## Image Generation (Text→Image)

| Provider | Slug | Notes |
|----------|------|-------|
| Fal AI | `fal-ai` | Fast FLUX serving |
| HF Inference | `hf-inference` | |
| Nscale | `nscale` | |
| Replicate | `replicate` | |
| Together | `together` | |
| WaveSpeedAI | `wavespeed` | |

## Video Generation (Text→Video)

| Provider | Slug |
|----------|------|
| Fal AI | `fal-ai` |
| Novita | `novita` |
| Replicate | `replicate` |
| WaveSpeedAI | `wavespeed` |

## Speech-to-Text

| Provider | Slug |
|----------|------|
| Fal AI | `fal-ai` |
| HF Inference | `hf-inference` |
| Replicate | `replicate` |

## Feature Extraction (Embeddings)

| Provider | Slug |
|----------|------|
| HF Inference | `hf-inference` |
| Scaleway | `scaleway` |

## Provider Selection Policies (Model ID Suffixes)

| Suffix | Effect |
|--------|--------|
| `:fastest` | Highest throughput (default) |
| `:cheapest` | Lowest price per output token |
| `:preferred` | Your hf.co/settings/inference-providers order |
| `:groq` (or any slug) | Pin to exact provider |

## Client-Side Provider Parameter

When using `InferenceClient` (Python/JS), pass `provider="groq"` directly:

```python
client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1",
    provider="novita",  # client-side provider selection
    messages=[{"role": "user", "content": "Hello"}],
)
```

## Important URLs

- **Router (OpenAI-compatible)**: `https://router.huggingface.co/v1`
- **Chat completions**: `POST /v1/chat/completions`
- **Provider settings page**: `https://hf.co/settings/inference-providers`
- **Docs**: `https://huggingface.co/docs/inference-providers/en/index.md`
- **Model browser (inference-warm)**: `https://huggingface.co/models?inference_provider=all`
