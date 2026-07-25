# HF Learnings Log — hf-inference-providers

## 2026-07-25: hf-inference-providers-comprehensive-architecture — Hugging Face Inference Providers Complete Ecosystem Deep-Dive (Topic #255)

### Summary
Comprehensive deep-dive on Hugging Face Inference Providers — the multi-provider serverless inference platform launched January 2025 and continuously expanded through 2026. Covers the full architecture (router proxy layer, provider selection policies, authentication modes), all 17+ partner providers with their supported task types, Hub integration points (widgets, playground, Data Studio AI, model search), client SDK usage patterns (Python, JavaScript, HTTP, OpenAI-compatible), billing model (free tier, PRO, Enterprise, custom API keys), security & compliance (SOC2 Type 2, TLS, 30-day log retention, no data storage), agent framework integrations, and zero-cost pathways for development.

### Sources
- Inference Providers Docs (main): https://huggingface.co/docs/inference-providers/en/index
- Hub Integration: https://huggingface.co/docs/inference-providers/en/hub-integration
- Security & Compliance: https://huggingface.co/docs/inference-providers/en/security
- Announcement Blog (Jan 2025): https://huggingface.co/blog/inference-providers
- Hub API Inference Providers page: https://huggingface.co/docs/hub/en/models-inference
- Provider filter: https://huggingface.co/models?inference_provider=fireworks-ai
- Inference Playground: https://huggingface.co/playground
- Pricing: https://huggingface.co/pricing

### 1. What Are Inference Providers?

Inference Providers is Hugging Face's **multi-provider serverless inference platform**. It gives developers unified, pay-as-you-go access to hundreds of ML models through a single Hugging Face token, powered by 17+ world-class inference partners. It replaces and subsumes the earlier "HF-Inference API" (serverless inference), which is now just one provider among many in the ecosystem.

**Key differentiator from Inference Endpoints:** Inference Providers is **serverless** — no infrastructure management, no cold start management, no dedicated GPU rental. Just model ID + prompt = result. Inference Endpoints (dedicated) is for production workloads needing guaranteed GPUs, custom handlers, and autoscaling.

### 2. Architecture

```
User Application
    │
    ▼
huggingface_hub.InferenceClient / @huggingface/inference / OpenAI SDK / HTTP
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│              HF Router Proxy Layer                       │
│  https://router.huggingface.co/v1                        │
│                                                          │
│  Provider Selection:                                     │
│  - "auto" (default) → fastest available provider         │
│  - Model suffix :fastest → speed-optimized               │
│  - Model suffix :cheapest → cost-optimized               │
│  - Model suffix :preferred → user preference order       │
│  - Explicit provider name → specific provider             │
│                                                          │
│  Auth modes:                                             │
│  - HF token → billed to HF account (routed)             │
│  - Custom provider API key → direct to provider          │
└──────────────────────────────────────────────────────────┘
    │
    ├──→ Cerebras
    ├──→ Cohere
    ├──→ DeepInfra
    ├──→ Fal AI
    ├──→ Featherless AI
    ├──→ Fireworks
    ├──→ Groq
    ├──→ HF Inference (legacy serverless)
    ├──→ Novita
    ├──→ Nscale
    ├──→ OVHcloud AI Endpoints
    ├──→ Public AI
    ├──→ Replicate
    ├──→ Scaleway
    ├──→ Together
    ├──→ WaveSpeedAI
    └──→ Z.ai
```

#### 2.1. Provider Selection Policies

The router supports three ways to select a provider:

**A) Client-side selection (InferenceClient):**
```python
from huggingface_hub import InferenceClient

# automatic: picks fastest provider (default)
client = InferenceClient()
completion = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3-0324",
    messages=[{"role": "user", "content": "Hello"}]
)

# explicit provider
client = InferenceClient(provider="groq")
completion = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**B) Model ID suffix (both client SDKs and OpenAI-compatible endpoint):**
- `:fastest` — highest throughput (tokens/sec), default behavior for `provider="auto"`
- `:cheapest` — lowest price per output token
- `:preferred` — follows user preference order in HF settings
- `:specific-provider-name` — e.g., `:groq`

```python
completion = client.chat.completions.create(
    model="openai/gpt-oss-120b:cheapest",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**C) Automatic failover:** When `provider="auto"`, if the primary provider is flagged as unavailable by the validation system, requests are automatically routed to alternative providers.

#### 2.2. Authentication Modes

| Mode | API Key | Billing | Direction |
|------|---------|---------|-----------|
| Routed by HF | HF token only | Charged to HF account | Through HF proxy |
| Custom provider key | Provider-specific API key | Charged to provider account | Direct (or through proxy) |

Users set custom provider API keys in their HF settings: https://huggingface.co/settings/inference-providers

### 3. Partner Providers & Supported Tasks

As of July 2026, there are 17+ providers in the ecosystem:

| Provider | Chat (LLM) | Chat (VLM) | Feature Extraction | Text-to-Image | Text-to-Video | Speech-to-Text |
|----------|:-----------:|:-----------:|:------------------:|:-------------:|:-------------:|:--------------:|
| Cerebras | ✅ | | | | | |
| Cohere | ✅ | | ✅ | | | |
| DeepInfra | ✅ | ✅ | | | | |
| Fal AI | ✅ | ✅ | | ✅ | ✅ | ✅ |
| Featherless AI | ✅ | ✅ | | | | |
| Fireworks | ✅ | ✅ | | | | |
| Groq | ✅ | ✅ | | | | |
| HF Inference | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Novita | ✅ | ✅ | | ✅ | ✅ | |
| Nscale | ✅ | ✅ | | | | |
| OVHcloud AI Endpoints | ✅ | ✅ | | | | |
| Public AI | | | ✅ | | | |
| Replicate | ✅ | ✅ | | ✅ | ✅ | ✅ |
| Scaleway | ✅ | ✅ | | | | |
| Together | ✅ | ✅ | | | | |
| WaveSpeedAI | ✅ | ✅ | | | | |
| Z.ai | ✅ | ✅ | | | | |

**HF Inference** is the legacy serverless Inference API provider, now one provider among many. It's powered by Inference Endpoints under the hood.

### 4. Hub Integration Points

Inference Providers is deeply integrated into the Hugging Face Hub:

1. **Model Page Widgets** — Interactive inference widgets on model pages use Inference Providers under the hood. Example: https://huggingface.co/deepseek-ai/DeepSeek-V3-0324

2. **Inference Playground** — https://huggingface.co/playground — comprehensive chat interface supporting various models and providers for testing and comparing responses.

3. **Data Studio AI** — Converts natural language to SQL queries on dataset pages, powered by Inference Providers.

4. **Model Search Filtering** — Filter models by inference provider:
   - `https://huggingface.co/models?inference_provider=fireworks-ai`
   - `https://huggingface.co/models?inference_provider=all`

5. **User Settings** — Set custom API keys per provider and order providers by preference: https://huggingface.co/settings/inference-providers

6. **Organization Settings** — Team-level provider configuration with usage graphs.

### 5. Client SDK Usage Patterns

#### 5.1. Python (huggingface_hub)

```bash
pip install huggingface_hub
hf auth login
```

Basic chat completion:
```python
from huggingface_hub import InferenceClient

client = InferenceClient()
completion = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "How many G's in 'huggingface'?"}]
)
print(completion.choices[0].message)
```

Text-to-image generation:
```python
image = client.text_to_image(
    prompt="A serene lake at sunset, photorealistic style",
    model="black-forest-labs/FLUX.1-dev"
)
image.save("generated.png")
```

#### 5.2. JavaScript (@huggingface/inference)

```javascript
import { InferenceClient } from "@huggingface/inference";
const client = new InferenceClient(process.env.HF_TOKEN);

const chatCompletion = await client.chatCompletion({
  model: "deepseek-ai/DeepSeek-R1:fastest",
  messages: [{ role: "user", content: "Hello!" }],
});
```

#### 5.3. OpenAI-Compatible Endpoint

For chat completions, use the drop-in OpenAI-compatible endpoint:
```python
from openai import OpenAI
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key="hf_..."
)
completion = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1:fastest",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

Note: The OpenAI-compatible endpoint is **chat completion only**. For other tasks (text-to-image, embeddings, speech), use the Hugging Face inference clients.

#### 5.4. Direct HTTP / cURL

```bash
curl https://router.huggingface.co/v1/chat/completions \
  -H "Authorization: Bearer hf_..." \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-120b:fastest",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": false
  }'
```

#### 5.5. CLI

```bash
hf models ls --warm        # list models served by at least one provider
hf models ls --warm --json # machine-readable output for scripts/agents
```

### 6. Billing & Pricing

#### 6.1. Free Tier
- Free tier credits included for all users
- Covers moderate usage of widgets, playground, and Data Studio AI
- No credit card required to start

#### 6.2. PRO Plan
- Additional monthly credits beyond free tier
- Higher rate limits
- Priority access

#### 6.3. Team & Enterprise
- Centralized billing at organization level
- Usage graphs per team member
- Custom rate limits and SLAs
- SOC2 Type 2 certified infrastructure

#### 6.4. Custom Provider API Keys
Users can bring their own provider API keys, bypassing HF billing entirely. This is useful for:
- Users who already have credits/commitments with specific providers
- Users who want direct billing relationships
- Users who need provider-specific features not available through the HF proxy

### 7. Security & Compliance

- **Data Privacy:** HF does NOT store request bodies or responses. No user data used for training.
- **Log Retention:** Debug logs kept for up to 30 days, but no user data or tokens stored.
- **Encryption:** TLS/SSL for all data in transit.
- **Certification:** Hugging Face Hub is SOC2 Type 2 certified.
- **External Providers:** Each provider is responsible for their own security measures.
- **Token Scoping:** Use fine-grained tokens with "Make calls to Inference Providers" permission.

### 8. Agent Framework Integrations

Inference Providers integrates directly with multiple agent frameworks:

| Agent | Setup Guide |
|-------|-------------|
| OpenCode | [docs link] |
| Pi | [docs link] |
| Codex | [docs link] |
| Claude Code | [docs link] |
| Hermes Agent | [docs link] |
| NeMo Data Designer | [docs link] |
| MacWhisper | [docs link] |
| Vision Agents | [docs link] |
| VS Code with GitHub Copilot | [docs link] |

The core pattern is: point the agent at Inference Providers with a single HF token, giving it access to the latest open models.

### 9. Zero-Cost Pathways

For Beer's context (no income, homeless, needs free options):

1. **Free tier credits** — Enough for moderate prototyping and testing. Widgets on model pages are free-tier eligible.
2. **HF Inference provider** — The legacy serverless provider often has free usage for smaller models.
3. **Custom API keys from free-tier providers** — Some providers (e.g., Groq, Together, Fireworks) offer their own free tiers with rate limits. Register directly and add the key in HF settings.
4. **Smaller models** — Use smaller quantized models (e.g., Llama 3.2 1B, Phi-3-mini) which are cheaper or free on most providers.
5. **Inference Playground** — Free for experimentation without writing any code.
6. **`hf models ls --warm`** — Find which models are actually served (free-tier accessible) before committing to an approach.

### 10. Key Differences from Legacy HF-Inference API

| Feature | Legacy HF-Inference API | Inference Providers |
|---------|------------------------|---------------------|
| Architecture | Single HF backend | Multi-provider router proxy |
| Provider choice | None (HF only) | 17+ providers, explicit selection |
| Selection policy | N/A | `:fastest`, `:cheapest`, `:preferred`, explicit |
| OpenAI-compatible | No | Yes (chat only) |
| Custom API keys | No | Yes (per-provider) |
| Model availability | Limited to HF-hosted | Thousands across all providers |
| Failover | None | Automatic when provider unavailable |
| Client SDK | `InferenceClient` | Same `InferenceClient` (updated) |

### 11. Practical Examples

#### Finding Available Models
```bash
# List all warm models across all providers
hf models ls --warm

# Filter to specific provider (via Hub URL)
# https://huggingface.co/models?inference_provider=groq
```

#### Structured Outputs
```python
from huggingface_hub import InferenceClient
from pydantic import BaseModel

class Story(BaseModel):
    title: str
    content: str
    word_count: int

client = InferenceClient()
story = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Write a short story about AI"}],
    response_format={"type": "json", "schema": Story.model_json_schema()}
)
```

#### Function Calling
```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            }
        }
    }
}]
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "What's weather in Paris?"}],
    tools=tools,
    tool_choice="auto"
)
```

### 12. Registering as an Inference Provider

Providers can join the HF partner network by registering. Requirements include:
- Reliable API infrastructure with uptime guarantees
- Support for standard inference task types
- Compliance with HF's security and data handling policies
- Per-token or per-request pricing transparency

Registration details: https://huggingface.co/docs/inference-providers/en/register

### 13. Future Direction

Based on the roadmap and continuous updates since January 2025 launch:
- More providers being onboarded (expanding beyond current 17)
- More task types (audio generation, 3D, etc.)
- Deeper agent framework integrations
- Enhanced structured outputs and function calling support
- Provider-side caching for reduced latency
- Multi-region failover

---

## 2026-07-25: hf-inference-client-provider-routing-source-deep-dive — huggingface_hub v1.24.0 Provider Routing System Source-Code Deep Dive (Topic #277)

### Summary
Source-code deep dive into the huggingface_hub v1.24.0 `huggingface_hub.inference._providers` package — the complete provider routing system that dispatches InferenceClient requests to 18 partner providers. Covers the full class hierarchy (`TaskProviderHelper` → 30+ provider-specific task helpers), the request preparation pipeline (5-step prepare chain), the `get_provider_helper()` routing logic (3 decision paths: auto-router, auto-select from mapping, explicit provider), the `PROVIDERS` registry dict, the `AutoRouterConversationalTask` server-side routing singleton, the `_fetch_inference_provider_mapping()` Hub API contract, the `_OpenAIProxy` OpenAI compatibility layer, and the `_client.py` integration points for text_generation, chat_completion, and other tasks.

### Source
- huggingface_hub v1.24.0 source (installed at `/opt/data/.venv/lib/python3.13/site-packages/huggingface_hub/inference/`)
- `_providers/__init__.py` — PROVIDERS registry, get_provider_helper(), CONVERSATIONAL_AUTO_ROUTER
- `_providers/_common.py` — TaskProviderHelper, InferenceProviderMapping, AutoRouterConversationalTask
- `_providers/<name>.py` — 18 provider-specific modules
- `_client.py` — InferenceClient with provider parameter and OpenAI proxy
- Inference Providers Docs: https://huggingface.co/docs/inference-providers/en/index

### 1. Architecture Overview

The provider routing system is a client-side dispatch layer inside `huggingface_hub` that sits between user code and 18 partner inference providers. Every `InferenceClient` method (`text_generation`, `chat_completion`, `text_to_image`, etc.) routes through this system.

```
User Code → InferenceClient.method() 
  → get_provider_helper(provider, task, model) 
    → returns TaskProviderHelper subclass instance
  → helper.prepare_request(inputs, parameters, headers, model, api_key) 
    → helper.get_response(data, request_parameters)
  → parsed response returned to user
```

### 2. Package Layout

```
huggingface_hub/inference/
  _client.py                  # InferenceClient (user-facing)
  _generated/                 # Typed parameters/outputs
  _providers/
    __init__.py               # PROVIDERS registry, get_provider_helper()
    _common.py                # Base classes: TaskProviderHelper, InferenceProviderMapping, AutoRouterConversationalTask
    hf_inference.py           # HF-Inference provider (17+ tasks, the fallback)
    cerebras.py, cohere.py, deepinfra.py, fal_ai.py, featherless_ai.py,
    fireworks_ai.py, groq.py, novita.py, nscale.py, openai.py,
    ovhcloud.py, publicai.py, replicate.py, scaleway.py, together.py,
    wavespeed.py, zai_org.py  # 18 partner provider modules
```

### 3. Class Hierarchy

```
TaskProviderHelper (base)
  ├── _prepare_api_key()    — token from user or local login
  ├── _prepare_mapping_info() — Hub model → provider mapping
  ├── _prepare_headers()    — default HF headers + overrides
  ├── _prepare_url()        — base URL + route
  │     ├── _prepare_base_url()   — per-provider base URL
  │     └── _prepare_route()      — per-provider path suffix
  ├── _prepare_payload_as_dict()  — JSON payload generation
  ├── _prepare_payload_as_bytes() — binary payload generation
  └── get_response()        — HTTP call + response parsing
```

Concrete subclasses (30+) are per-provider per-task:
- **Text generation**: `DeepInfraTextGenerationTask`, `TogetherTextGenerationTask`, `FeatherlessTextGenerationTask`, `NovitaTextGenerationTask`, `HFInferenceTask`
- **Conversational**: `CerebrasConversationalTask`, `CohereConversationalTask`, `DeepInfraConversationalTask`, `FeatherlessConversationalTask`, `FireworksAIConversationalTask`, `GroqConversationalTask`, `NovitaConversationalTask`, `NscaleConversationalTask`, `OpenAIConversationalTask`, `OVHcloudConversationalTask`, `PublicAIConversationalTask`, `ScalewayConversationalTask`, `TogetherConversationalTask`, `ZaiConversationalTask`, `HFInferenceConversational`
- **Image generation**: `FalAITextToImageTask`, `TogetherTextToImageTask`, `ReplicateTextToImageTask`, `NscaleTextToImageTask`, `WavespeedAITextToImageTask`, `ZaiTextToImageTask`
- **Speech/audio**: `DeepInfraAutomaticSpeechRecognitionTask`, `FalAIAutomaticSpeechRecognitionTask`, `ReplicateAutomaticSpeechRecognitionTask`
- **Feature extraction**: `TogetherFeatureExtractionTask`, `ScalewayFeatureExtractionTask`, `HFInferenceFeatureExtractionTask`
- **Video generation**: `FalAITextToVideoTask`, `TogetherTextToVideoTask`, `NovitaTextToVideoTask`, `WavespeedAITextToVideoTask`, `FalAIImageToVideoTask`, `WavespeedAIImageToVideoTask`, `TogetherImageToVideoTask`
- **Image-to-image**: `TogetherImageToImageTask`, `ReplicateImageToImageTask`, `FalAIImageToImageTask`, `WavespeedAIImageToImageTask`

### 4. Routing Logic: get_provider_helper()

The `get_provider_helper()` function (in `_providers/__init__.py`) implements a 3-path decision tree:

```
Caller: InferenceClient.method(model, provider=...)
  │
  ├─ Path 1: No model + no/auto provider, OR model is HTTP URL
  │   → provider = "hf-inference" (legacy fallback)
  │
  ├─ Path 2: provider is None
  │   → provider = "auto"
  │   (If conversational: return CONVERSATIONAL_AUTO_ROUTER singleton)
  │   (Else: fetch provider mapping from Hub, use first provider)
  │
  └─ Path 3: Explicit provider string (e.g., "together")
      → Look up in PROVIDERS dict
      → If task found, return provider's task helper instance
      → If task not found, raise ValueError
```

**Auto mode for non-conversational tasks**: calls `_fetch_inference_provider_mapping(model)` which fetches `HfApi().model_info(model, expand=["inferenceProviderMapping"])` from the Hub. Returns an ordered list of `InferenceProviderMapping` objects (ordered by user's preference in https://hf.co/settings/inference-providers). The first mapping's `.provider` is selected.

**Conversational auto-router**: uses `AutoRouterConversationalTask` singleton — routes to `https://router.huggingface.co` which does server-side provider selection. This avoids an extra API call to fetch the provider mapping and lets the server apply user preferences directly.

### 5. Request Preparation Pipeline

When `text_generation()` (or any method) is called, the client:
1. Resolves the model ID (user-provided or default)
2. Calls `get_provider_helper(self.provider, task="text-generation", model=model_id)`
3. Calls `helper.prepare_request(inputs, parameters, headers, model, api_key)` which runs 5 steps:
   - `_prepare_api_key()`: uses user-provided API key, or `get_token()`, or raises
   - `_prepare_mapping_info()`: if explicit provider, looks up hardcoded or fetched mapping; if auto-router, returns dummy mapping
   - `_prepare_headers()`: merges `build_hf_headers()` with user headers
   - `_prepare_url()`: constructs `{base_url}/{route}` — base URLs are per-provider (e.g. `https://api.together.xyz`), routes are per-task (e.g. `v1/chat/completions`)
   - `_prepare_payload_as_dict()`: converts inputs+parameters to provider-specific JSON format
4. Calls `helper.get_response(data, request_parameters)` — sends HTTP request to provider

### 6. Provider Base URL Mapping

Each provider class hardcodes its base URL and route pattern. Key examples:

| Provider | Base URL | Chat Route | Text Gen Route |
|----------|----------|------------|----------------|
| Together AI | `https://api.together.xyz` | `v1/chat/completions` | `v1/completions` |
| DeepInfra | `https://api.deepinfra.com` | `v1/openai/chat/completions` | `v1/inference/{model_id}` |
| Fireworks AI | `https://api.fireworks.ai` | `v1/chat/completions` | — |
| Groq | `https://api.groq.com` | `openai/v1/chat/completions` | — |
| Cerebras | `https://api.cerebras.ai` | `v1/chat/completions` | — |
| Novita | `https://api.novita.ai` | `v3/openai/chat/completions` | `v3/openai/completions` |
| Fal AI | `https://fal.run` | — | — |
| Replicate | `https://api.replicate.com` | — | — |
| Scaleway | `https://api.scaleway.ai` | `v1/chat/completions` | — |

The `hf-inference` provider uses `https://api-inference.huggingface.co/models/{model_id}` as its base.

### 7. AutoRouterConversationalTask

A singleton instantiated at import time. Key specialization:
- Base URL: `https://router.huggingface.co` (no `/auto` path prefix)
- `_prepare_base_url()`: validates API key is an HF token (`hf_...`); non-HF keys raise `ValueError`
- `_prepare_mapping_info()`: returns a dummy `InferenceProviderMapping` with `providerId=model` (no Hub API call needed)
- This is the only path where server-side routing happens — the router.hf.co endpoint handles provider selection based on user preferences stored on the server

### 8. OpenAI Compatibility Layer

`InferenceClient` has an `_OpenAIProxy` that aliases `client.chat` as `ProxyClientChat`:
- `client.chat.completions.create(...)` maps to `client.chat_completion(...)`
- `client.chat.completions.create(stream=True)` maps to `client.chat_completion(stream=True)`
- This allows drop-in replacement of `openai.OpenAI()` with `huggingface_hub.InferenceClient()`

The proxy is initialized lazily via a `@property` on InferenceClient.

### 9. HF-Inference (Legacy Fallback)

The `hf-inference` provider handles 17+ task types via two helper classes:
- `HFInferenceTask` — for text-in/text-out tasks (text-generation, classification, translation, etc.)
- `HFInferenceBinaryInputTask` — for tasks with binary inputs (image, audio)
- `HFInferenceConversational` — for chat completion via the old TGI endpoint
- `HFInferenceFeatureExtractionTask` — for embedding generation

These route to `https://api-inference.huggingface.co/models/{model_id}` and use the standard HF Inference API protocol.

### 10. Provider-Specific Customizations

Each provider module can override any of the 6 hook methods in `TaskProviderHelper`:

- **Together/Auth**: Some providers append `Authorization: Bearer {key}` in `_prepare_headers()` while others (Scaleway, Novita) handle it via the payload
- **Payload format**: Together's conversational payload uses `model: provider_id`; DeepInfra uses `model` in the body; others use URL path segments
- **Route construction**: Together uses `v1/completions` for text gen, `v1/chat/completions` for chat; DeepInfra uses a model-specific route like `v1/inference/{model_id}`; Novita uses `v3/openai/chat/completions`
- **Response parsing**: Each `get_response()` override handles the provider's specific response schema and error format

### 11. Key Design Decisions

1. **Singleton helpers**: All provider task helpers are instantiated once at import time in the `PROVIDERS` dict — no per-request allocation overhead
2. **Lazy Hub API calls**: Provider mapping is only fetched when `provider="auto"` — explicit provider selection bypasses the Hub API call entirely
3. **Server-side routing for chat**: Conversational tasks use `AutoRouterConversationalTask` which avoids a client-side Hub API call and lets the server select the optimal provider
4. **OpenAI compatibility at two levels**: Both at the client init (`base_url`/`api_key` aliases) and at the method level (`client.chat.completions.create`)
5. **HF token vs external keys**: The system distinguishes HF tokens from external provider keys — HF tokens route through the router proxy for billing, while external keys go directly to the provider

### 12. Error Handling

- Missing provider → `ValueError` with all valid provider names listed
- Unsupported task for provider → `ValueError` with available tasks listed
- Missing model when provider="auto" → `ValueError`
- Non-HF token with auto-router → `ValueError`
- No provider mapping found for model → `ValueError` from `_fetch_inference_provider_mapping`
- `bill_to` header with external API key → `UserWarning` (ignored)

### 13. Comparison with Previous Architecture

In huggingface_hub < 1.20, there was no provider routing. `InferenceClient` always used `api-inference.huggingface.co` directly. The provider system was added in v1.20+ and fully matured in v1.24.0 with:
- 18 partner providers
- Per-provider task-specific helpers
- Auto-router for conversational models
- OpenAI API compatibility layer
- `bill_to` header support

### Sources
- huggingface_hub v1.24.0 source:
  - `huggingface_hub/inference/_providers/__init__.py` — PROVIDERS registry + get_provider_helper
  - `huggingface_hub/inference/_providers/_common.py` — TaskProviderHelper → AutoRouterConversationalTask
  - `huggingface_hub/inference/_providers/<provider>.py` — 18 provider modules
  - `huggingface_hub/inference/_client.py` — InferenceClient integration
- Inference Providers Docs: https://huggingface.co/docs/inference-providers/en/index
- Hub API: https://huggingface.co/docs/hub/en/models-inference
- Provider settings: https://hf.co/settings/inference-providers

### Skill
hf-inference-providers — Enhanced with source-level deep dive on huggingface_hub v1.24.0 `_providers/` package: TaskProviderHelper class hierarchy (6 overridable methods), 30+ per-provider-per-task helpers, get_provider_helper() 3-path routing logic, AutoRouterConversationalTask singleton, PROVIDERS registry, _fetch_inference_provider_mapping Hub API contract, OpenAI compatibility layer via _OpenAIProxy, and provider-specific customizations across 18 partner providers including Together, DeepInfra, Fireworks AI, Groq, Fal AI, Replicate, Novita, Scaleway, and the hf-inference legacy fallback.
