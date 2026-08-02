# smolagents Model Backends — Reference

## Comparison

| Backend | Import | Install Extras | Use Case | Cost |
|---------|--------|---------------|----------|------|
| **InferenceClientModel** | `from smolagents import InferenceClientModel` | none (base) | Quick prototyping via HF Inference API; no local GPU needed | Free tier available via HF Inference |
| **LiteLLMModel** | `from smolagents import LiteLLMModel` | `smolagents[litellm]` | OpenAI, Anthropic, Gemini, and 100+ providers | Pay-per-token (provider API keys) |
| **TransformersModel** | `from smolagents import TransformersModel` | `smolagents[transformers]` | Local inference, offline, privacy-sensitive | Free (local GPU/CPU) |

## InferenceClientModel (Default)

```python
# Default model (HF-managed)
model = InferenceClientModel()

# Specific model
model = InferenceClientModel(model_id="meta-llama/Llama-2-70b-chat-hf")

# With custom Inference endpoint
model = InferenceClientModel(
    model_id="https://xyz.us-east-1.aws.endpoints.huggingface.cloud/mistral-7b"
)
```

**Pitfalls:**
- Omitting `model_id` uses the HF default which may change without notice. Always specify for production.
- Requires internet access to `https://api-inference.huggingface.co`
- Free tier has rate limits; use with `max_iterations` to control costs

## LiteLLMModel (OpenAI/Anthropic/Gemini)

```bash
pip install 'smolagents[litellm]'
```

```python
from smolagents import LiteLLMModel

# OpenAI
model = LiteLLMModel(model_id="gpt-4")

# Anthropic
model = LiteLLMModel(model_id="claude-3-5-sonnet-20241022")

# Gemini
model = LiteLLMModel(model_id="gemini/gemini-1.5-pro")

# Any LiteLLM-supported provider
model = LiteLLMModel(model_id="together_ai/mistralai/Mixtral-8x7B-Instruct-v0.1")
```

**Pitfalls:**
- Requires `smolagents[litellm]` extras — base install alone won't work
- Set `api_key` via env vars: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.
- Rate limits and costs depend on the provider, not smolagents

## TransformersModel (Local)

```bash
pip install 'smolagents[transformers]'
```

```python
from smolagents import TransformersModel

# Small model for CPU
model = TransformersModel(model_id="meta-llama/Llama-2-7b-chat-hf")

# Quantized for memory efficiency (requires bitsandbytes)
model = TransformersModel(
    model_id="meta-llama/Llama-2-7b-chat-hf",
    device_map="auto",
    load_in_4bit=True,
)
```

**Pitfalls:**
- Large models require significant GPU memory — use quantization for consumer GPUs
- First load downloads the model weights (can be several GB)
- `device_map="auto"` is recommended for multi-GPU setups
- Fallback to CPU will be very slow for models >1B parameters
