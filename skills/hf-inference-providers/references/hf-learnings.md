# HF Inference Providers — Source Architecture Deep Dive (huggingface_hub v1.24.0, July 2026)

> Author: SakThai · License: MIT
> Source: huggingface_hub v1.24.0 source analysis (`_client.py`, `_providers/`, `_common.py`, `constants.py`)

---

## Architecture Overview

The Hugging Face Inference Providers system routes inference requests from a unified `InferenceClient` through a provider abstraction layer to 18 third-party inference providers. The architecture has four layers:

```
User Code
    │
    ▼
InferenceClient.chat_completion()     ← unified Python API
    │
    ▼
get_provider_helper()                ← resolves provider + task → TaskProviderHelper
    │
    ├─ auto (conversational) → AutoRouterConversationalTask → https://router.huggingface.co/v1/chat/completions
    ├─ auto (other tasks)   → fetches model_info(expand=["inferenceProviderMapping"]) → first live provider
    ├─ <named provider>     → instantiates provider-specific task class
    └─ URL/endpoint URL    → HFInferenceTask (falls through to hf-inference)
    │
    ▼
TaskProviderHelper.prepare_request()  ← builds URL, headers, payload
    │
    ▼
InferenceClient._inner_post()        ← httpx POST, handles streaming/non-streaming
    │
    ▼
Provider endpoint / router.huggingface.co/{provider}
```

### Key Source Files

| File | Purpose |
|------|---------|
| `huggingface_hub/inference/_client.py` | `InferenceClient` — user-facing API |
| `huggingface_hub/inference/_providers/__init__.py` | Provider registry, `get_provider_helper()`, `PROVIDERS` dict |
| `huggingface_hub/inference/_providers/_common.py` | `TaskProviderHelper` base class, `AutoRouterConversationalTask`, `_fetch_inference_provider_mapping()` |
| `huggingface_hub/inference/_providers/*.py` | 18 provider-specific modules |
| `huggingface_hub/inference/_common.py` | `RequestParameters`, `_stream_chat_completion_response()`, shared types |
| `huggingface_hub/constants.py` | `INFERENCE_PROXY_TEMPLATE = "https://router.huggingface.co/{provider}"` |
| `huggingface_hub/hf_api.py` | `HfApi.model_info()` with `expand=["inferenceProviderMapping"]` |

---

## Layer 1: InferenceClient Initialization

```python
client = InferenceClient(
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    provider="auto",          # or "together", "groq", "hf-inference", etc.
    token="hf_...",           # HF token for routing auth
    timeout=None,             # loops until server available
)
```

The constructor stores `self.provider`, `self.model`, `self.token` and aliases:
- `base_url` ↔ `model` (mutually exclusive)
- `api_key` ↔ `token` (mutually exclusive)

When `model` is a URL (Inference Endpoint), `provider` is ignored — routing falls through to `hf-inference`.

### OpenAI Compat Layer

The `.chat` property returns a `ProxyClientChat` → `ProxyClientChatCompletions` → `.create` which returns `InferenceClient.chat_completion`:

```python
client.chat.completions.create(messages=[...])  # identical to client.chat_completion(messages=[...])
```

The proxy chain:
- `InferenceClient.chat` → `@property` → `ProxyClientChat(client)`
- `ProxyClientChat.completions` → `@property` → `ProxyClientChatCompletions(client)`
- `ProxyClientChatCompletions.create` → `@property` → `client.chat_completion`

This is purely syntactic sugar for OpenAI SDK compatibility — no additional logic.

### Class Structure

```python
class _ProxyClient:
    def __init__(self, client: InferenceClient):
        self._client = client

class ProxyClientChat(_ProxyClient):
    @property
    def completions(self) -> "ProxyClientChatCompletions":
        return ProxyClientChatCompletions(self._client)

class ProxyClientChatCompletions(_ProxyClient):
    @property
    def create(self):
        return self._client.chat_completion
```

---

## Layer 2: Provider Resolution — `get_provider_helper()`

This is the core routing function. It resolves `(provider, task, model)` → `TaskProviderHelper` instance.

### Full Resolution Logic

```
INPUT: provider, task, model

1. URL DETECTION:
   If model is a URL (http/https): provider ← "hf-inference"
   (URLs always go through the HF Inference API — no provider routing)

2. NONE DETECTION:
   If provider is None AND model is None: provider ← "hf-inference"
   (no model specified → use HF's recommended model)

3. AUTO DETECTION:
   If provider is None or "auto":
     If task == "conversational" AND model is set:
       → Return CONVERSATIONAL_AUTO_ROUTER singleton
         (server-side routing at router.huggingface.co — no provider mapping fetch needed)
     Else (non-conversational tasks):
       → Fetch model_info(expand=["inferenceProviderMapping"])
       → Pick first live provider from the list
       → Continue to step 4

4. NAMED PROVIDER:
   Look up provider in PROVIDERS dict
   Look up task in provider_tasks dict
   → Return the TaskProviderHelper instance
```

### Auto Router — Special Case for Conversational Tasks

For chat completions with `provider="auto"`, the system uses a **server-side router** at `https://router.huggingface.co`:

```python
class AutoRouterConversationalTask(BaseConversationalTask):
    def __init__(self):
        super().__init__(provider="auto", base_url="https://router.huggingface.co")

    def _prepare_base_url(self, api_key: str) -> str:
        if not api_key.startswith("hf_"):
            raise ValueError("Cannot use auto-router with non-HF API key.")
        return self.base_url  # No `/auto` suffix in URL

    def _prepare_mapping_info(self, model: str | None) -> InferenceProviderMapping:
        # No Hub API call — returns dummy mapping
        return InferenceProviderMapping(
            provider="auto",
            hf_model_id=model,
            providerId=model,
            status="live",
            task="conversational",
        )
```

Key points:
- The HF token **must** start with `"hf_"` — non-HF API keys cannot use the auto-router
- No `/auto` suffix in the URL like named providers get
- The model ID is passed directly as the payload `model` parameter
- Provider selection happens **server-side** based on speed or user's preference order
- Avoids an extra Hub API call to fetch provider mappings

### Named Provider — Non-Conversational Tasks

For non-conversational tasks with `provider="auto"`:

```python
@lru_cache(maxsize=None)
def _fetch_inference_provider_mapping(model: str) -> list[InferenceProviderMapping]:
    info = HfApi().model_info(model, expand=["inferenceProviderMapping"])
    return info.inference_provider_mapping  # list of {provider, hf_model_id, providerId, status, task}
```

- Results are cached via `@lru_cache` (never expires in process lifetime)
- The **first provider** in the user's preference order is selected
- `status` can be `"live"`, `"staging"`, or `"error"`
- Staging → warning; error → warning about potential failure

---

## Layer 3: TaskProviderHelper — Request Pipeline

Every provider+task combination extends `TaskProviderHelper`, which defines the 5-step request preparation pipeline:

```python
class TaskProviderHelper:
    def prepare_request(self, *, inputs, parameters, headers, model, api_key) -> RequestParameters:
        api_key = self._prepare_api_key(api_key)                    # step 1: token validation
        provider_mapping_info = self._prepare_mapping_info(model)   # step 2: resolve model ID
        headers = self._prepare_headers(headers, api_key)           # step 3: auth + custom headers
        url = self._prepare_url(api_key, mapped_model)              # step 4: build endpoint URL
        payload = self._prepare_payload_as_dict(...)                # step 5a: JSON payload
        data = self._prepare_payload_as_bytes(...)                  # step 5b: binary payload
        return RequestParameters(url=url, task=..., model=..., json=payload, data=data, headers=...)

    def get_response(self, response, request_params) -> Any:
        return response  # default: pass-through (can be overridden for custom parsing)
```

### Step-by-Step Pipeline

**Step 1 — API Key**: `_prepare_api_key(api_key)`
- Uses user-provided API key, or `get_token()` from local login, or raises `ValueError`
- For `hf-inference` provider only: API key is optional (anonymous access allowed)

**Step 2 — Mapping Info**: `_prepare_mapping_info(model)`
- For explicit providers: fetches `model_info(expand=["inferenceProviderMapping"])` and filters by provider name
- For auto-router: returns dummy mapping (no API call)
- For hf-inference with URLs: returns mapping with providerId = URL
- For hf-inference with no model: fetches `_fetch_recommended_models()` for default

**Step 3 — Headers**: `_prepare_headers(headers, api_key)`
- Default: `build_hf_headers(token=api_key)` merged with user headers
- Can be overridden per provider for auth scheme differences

**Step 4 — URL Construction**: `_prepare_url(api_key, mapped_model)`
- For named providers with HF token: `https://router.huggingface.co/{provider}/{route}`
- For named providers with external key: `{provider_base_url}/{route}`
- For hf-inference: `https://router.huggingface.co/hf-inference/models/{model_id}`
- For hf-inference with URL: the URL itself (Inference Endpoint or TGI deployment)

**Step 5a — JSON Payload**: `_prepare_payload_as_dict(inputs, parameters, mapping_info)`
- Conversational: `{"messages": inputs, "model": provider_id, ...parameters}` (OpenAI format)
- Text generation: `{"prompt": inputs, "model": provider_id, ...parameters}`
- Binary tasks return `None` (use step 5b)

**Step 5b — Binary Payload**: `_prepare_payload_as_bytes(inputs, parameters, mapping_info, extra_payload)`
- For image, audio, video inputs
- Returns `MimeBytes` with content type and encoded data
- Only one of step 5a or 5b should return a value

### URL Routing Modes

```python
def _prepare_base_url(self, api_key: str) -> str:
    if api_key.startswith("hf_"):
        # Route through HF proxy
        return constants.INFERENCE_PROXY_TEMPLATE.format(provider=self.provider)
        # e.g., https://router.huggingface.co/groq
    else:
        # Direct to provider
        return self.base_url
        # e.g., https://api.groq.com
```

Two routing modes:
1. **Via HF proxy** (HF token): `https://router.huggingface.co/{provider}/{route}` → billing on HF account
2. **Direct** (provider API key): `{provider_base_url}/{route}` → billing on provider account

### Chat Completion Route

For all conversational tasks, the route is always `/v1/chat/completions` (OpenAI-compatible).

---

## Layer 4: The 18 Inference Providers (huggingface_hub v1.24.0)

### Provider-Task Registry

```python
PROVIDERS: dict[str, dict[str, TaskProviderHelper]] = {
    "cerebras":       {"conversational": CerebrasConversationalTask()},
    "cohere":         {"conversational": CohereConversationalTask()},
    "deepinfra":      {"asr": DeepInfraASRTask, "conversational": ..., "text-generation": ...},
    "fal-ai":         {"asr", "text-to-image", "text-to-speech", "text-to-video", "image-to-video", "image-to-image", "image-segmentation"},
    "featherless-ai": {"conversational", "text-generation"},
    "fireworks-ai":   {"conversational"},
    "groq":           {"conversational"},
    "hf-inference":   {"conversational", "text-generation", "text-classification", "question-answering", "audio-classification", "asr", "fill-mask", "feature-extraction", "image-classification", "image-segmentation", "document-question-answering", "image-to-text", "object-detection", "audio-to-audio", "zero-shot-image-classification", "zero-shot-classification", "image-to-image", "sentence-similarity", "table-question-answering", "tabular-classification", "text-to-speech", "token-classification", "translation", "summarization", "visual-question-answering", "text-to-image"},
    "novita":         {"text-generation", "conversational", "text-to-video"},
    "nscale":         {"conversational", "text-to-image"},
    "openai":         {"conversational"},
    "ovhcloud":       {"conversational"},
    "publicai":       {"conversational"},
    "replicate":      {"asr", "image-to-image", "text-to-image", "text-to-speech", "text-to-video"},
    "scaleway":       {"conversational", "feature-extraction"},
    "together":       {"conversational", "feature-extraction", "image-to-image", "image-to-video", "text-generation", "text-to-image", "text-to-speech", "text-to-video"},
    "wavespeed":      {"text-to-image", "text-to-video", "image-to-image", "image-to-video"},
    "zai-org":        {"conversational", "text-to-image"},
}
```

### Provider Base URLs & Routes

| Provider | Base URL (Direct) | Chat Route | Text Gen Route | Other Routes |
|----------|-------------------|------------|----------------|------|
| Together | `https://api.together.xyz` | `v1/chat/completions` | `v1/completions` | Per-task |
| DeepInfra | `https://api.deepinfra.com` | `v1/openai/chat/completions` | `v1/inference/{model_id}` | — |
| Fireworks | `https://api.fireworks.ai` | `v1/chat/completions` | — | — |
| Groq | `https://api.groq.com` | `openai/v1/chat/completions` | — | — |
| Cerebras | `https://api.cerebras.ai` | `v1/chat/completions` | — | — |
| Novita | `https://api.novita.ai` | `v3/openai/chat/completions` | `v3/openai/completions` | — |
| Fal AI | `https://fal.run` | — | — | Per-task |
| Replicate | `https://api.replicate.com` | — | — | Per-task |
| Scaleway | `https://api.scaleway.ai` | `v1/chat/completions` | — | — |
| OVHcloud | `https://ai-endpoints-endpoint.ovh.ai` | `v1/chat/completions` | — | — |

### The "hf-inference" Provider

The default `hf-inference` provider is special:
- Supports **26 tasks** — covers every standard Hugging Face pipeline
- Uses HF Inference API (serverless) at `https://router.huggingface.co/hf-inference`
- Can accept URLs directly (Inference Endpoints or TGI deployments)
- Does **NOT require** an API key (falls back to local token or anonymous)
- Fetches recommended models via `_fetch_recommended_models()` when no model specified
- For binary input tasks (images, audio), uses `HFInferenceBinaryInputTask` → multipart/form-data
- For feature-extraction and sentence-similarity, uses URL path: `/models/{model}/pipeline/{task}`

### HF-Inference Helper Classes

```python
# Text-in/text-out tasks
class HFInferenceTask(TaskProviderHelper):
    def _prepare_payload_as_dict(self, inputs, parameters, ...):
        return filter_none({"inputs": inputs, "parameters": parameters})

# Binary input tasks (image, audio, video)
class HFInferenceBinaryInputTask(HFInferenceTask):
    def _prepare_payload_as_dict(self, ...) -> None: return None
    def _prepare_payload_as_bytes(self, inputs, ...) -> MimeBytes: ...

# Chat completion
class HFInferenceConversational(HFInferenceTask):
    def _prepare_payload_as_dict(self, inputs, parameters, ...):
        return filter_none({"messages": inputs, "parameters": parameters, ...})
```

---

## Layer 5: Model-to-Provider Mapping

The bridge between model IDs and providers:

```python
# Retrieved via: HfApi().model_info("org/model", expand=["inferenceProviderMapping"])
{
    "inference_provider_mapping": [
        {
            "provider": "together",
            "hf_model_id": "org/model",
            "providerId": "org/model",        # model name on provider's side
            "task": "conversational",
            "status": "live"                  # live | staging | error
        },
        {
            "provider": "fireworks-ai",
            "hf_model_id": "org/model",
            "providerId": "org/model",
            "task": "conversational",
            "status": "live"
        }
    ]
}
```

Key facts:
- Provider mappings are cached in-memory via `@lru_cache` (one cache per model ID)
- The order reflects user preference order (set at `https://hf.co/settings/inference-providers`)
- When `provider="auto"` for non-conversational tasks, the **first live** provider is selected
- Status `"staging"` → warning but inference allowed
- Status `"error"` → warning about potentially failed calls

### Hardcoded Model Mapping (Dev Purposes)

```python
HARDCODED_MODEL_INFERENCE_MAPPING: dict[str, dict[str, InferenceProviderMapping]] = {
    "cerebras": {},
    "cohere": {},
    "deepinfra": {},
    "fal-ai": {},
    "fireworks-ai": {},
    "groq": {},
    "hf-inference": {},
    "nscale": {},
    "ovhcloud": {},
    "replicate": {},
    "scaleway": {},
    "together": {},
    "wavespeed": {},
    "zai-org": {},
}
```

Used for local testing before a model is registered on the Hub for a given provider.

### Model ID Suffixes for Routing

| Suffix | Behavior |
|--------|----------|
| `org/model` | Routes to `auto` (fastest available) |
| `org/model:fastest` | Speed-optimized routing |
| `org/model:cheapest` | Cost-optimized routing |
| `org/model:preferred` | User's preference ordering |

These suffixes are parsed **server-side** by the router.

---

## Layer 6: Complete Request Lifecycle

### Chat Completion Example

```python
client = InferenceClient(provider="groq")
response = client.chat_completion(
    messages=[{"role": "user", "content": "Hello!"}],
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    temperature=0.7,
)
```

**Internal flow:**

1. `client.provider` = `"groq"`, `client.model` = `None`
2. `model_id_or_url` = `"meta-llama/Meta-Llama-3-8B-Instruct"` (from arg)
3. `payload_model` = `"meta-llama/Meta-Llama-3-8B-Instruct"` (from arg)
4. `get_provider_helper("groq", "conversational", "meta-llama/...")`
5. → Looks up `PROVIDERS["groq"]["conversational"]` → returns `GroqConversationalTask()` instance
6. `GroqConversationalTask.prepare_request(...)`:
   - `_prepare_api_key`: gets `get_token()` from local HF token
   - `_prepare_mapping_info`: fetches `model_info("meta-llama/...", expand=["inferenceProviderMapping"])`, finds Groq mapping with status `"live"`
   - `_prepare_headers`: `build_hf_headers(token="hf_...")` merged with user headers
   - `_prepare_url`: token starts with `"hf_"` → base = `https://router.huggingface.co/groq`; route = `/v1/chat/completions` → full URL = `https://router.huggingface.co/groq/v1/chat/completions`
   - `_prepare_payload_as_dict`: `{"messages": [...], "model": "meta-llama/Meta-Llama-3-8B-Instruct", "temperature": 0.7}`
7. `RequestParameters` returned with URL, headers, JSON payload
8. `_inner_post(request_parameters, stream=False)`: POST to URL with JSON body
9. Response JSON parsed as `ChatCompletionOutput`

### Streaming Flow

If `stream=True`:

```python
data = self._inner_post(request_parameters, stream=True)  # returns httpx.Response
return _stream_chat_completion_response(data)
```

- `_inner_post` sends POST with `stream=True` → returns raw `httpx.Response`
- `_stream_chat_completion_response` wraps the response in an SSE parser
- Yields `ChatCompletionStreamOutput` objects token-by-token

---

## Layer 7: Error Handling

| Scenario | Error |
|----------|-------|
| Missing model when `provider="auto"` | `ValueError: "Specifying a model is required when provider is 'auto'"` |
| Unsupported provider name | `ValueError` with all valid provider names listed |
| Unsupported task for provider | `ValueError` with available tasks listed |
| Non-HF token with auto-router | `ValueError: "Cannot use auto-router with non-HF API key"` |
| No provider mapping for model | `ValueError: "No provider mapping found for model {model}"` |
| Model not supported by provider | `ValueError: "Model {model} is not supported by provider {provider}."` |
| Both payload and data set | `ValueError: "Both payload and data cannot be set in the same request."` |
| `bill_to` with external API key | `UserWarning` (ignored) |

---

## Layer 8: Key Design Patterns

1. **Singleton helpers**: All provider task helpers are instantiated once at import time in the `PROVIDERS` dict — no per-request allocation overhead
2. **Lazy Hub API calls**: Provider mapping is only fetched when `provider="auto"` — explicit provider selection bypasses the Hub API call entirely
3. **Server-side routing for chat**: Conversational tasks use `AutoRouterConversationalTask` which avoids client-side Hub API calls and lets the server select the optimal provider
4. **OpenAI compatibility at two levels**: Client init (`base_url`/`api_key` aliases) and method level (`client.chat.completions.create`)
5. **HF token vs external keys**: HF tokens → route through proxy for billing; external keys → direct to provider
6. **Filter-none payload cleaning**: `filter_none()` recursively removes `None` values from payload dicts/lists, keeping requests clean

---

## Comparison: Before vs After Provider System

| Aspect | Prior to v1.20 (HF-Inference only) | v1.24.0 (Provider System) |
|--------|-------------------------------------|--------------------------|
| Backend | Single `api-inference.huggingface.co` | 18 providers via `router.huggingface.co` |
| Provider choice | None | Explicit, auto, suffix-based |
| OpenAI compat | No | Yes (`client.chat.completions.create`) |
| Custom API keys | No | Yes (per-provider in HF settings) |
| Model availability | HF-hosted only | Thousands across all providers |
| Failover | None | Automatic when provider unavailable |

---

## Sources
- huggingface_hub v1.24.0 source code: `_client.py`, `_providers/__init__.py`, `_providers/_common.py`, `_providers/*.py`
- HF Inference Providers settings: https://hf.co/settings/inference-providers
- HF Inference API docs: https://huggingface.co/docs/huggingface_hub/guides/inference
- HF API: `model_info(expand=["inferenceProviderMapping"])`

---

# Previous Learnings

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
  -H "Authorization: Bearer ***" \
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
- OpenCode, Pi, Codex, Claude Code, Hermes Agent, NeMo Data Designer, MacWhisper, Vision Agents, VS Code with GitHub Copilot

The core pattern: point the agent at Inference Providers with a single HF token, giving it access to the latest open models.

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
Source-code deep dive into the huggingface_hub v1.24.0 `huggingface_hub.inference._providers` package — the complete provider routing system that dispatches InferenceClient requests to 18 partner providers. Covers the full class hierarchy (`TaskProviderHelper` → 30+ provider-specific task helpers), the request preparation pipeline (5-step prepare chain), the `get_provider_helper()` routing logic (3 decision paths: auto-router, auto-select from mapping, explicit provider), the `PROVIDERS` registry dict, the `AutoRouterConversationalTask` server-side routing singleton, the `_fetch_inference_provider_mapping()` Hub API contract, the OpenAI compatibility layer, and the `_client.py` integration points.

### Source
- huggingface_hub v1.24.0 source (installed at `/opt/data/.venv/lib/python3.14/site-packages/huggingface_hub/inference/`)
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

`InferenceClient` has a `ProxyClientChat` that aliases `client.chat`:
- `client.chat.completions.create(...)` maps to `client.chat_completion(...)`
- `client.chat.completions.create(stream=True)` maps to `client.chat_completion(stream=True)`
- This allows drop-in replacement of `openai.OpenAI()` with `huggingface_hub.InferenceClient()`

The proxy is initialized lazily via a `@property` on InferenceClient.

### 9. HF-Inference (Legacy Fallback)

The `hf-inference` provider handles 17+ task types via multiple helper classes:
- `HFInferenceTask` — for text-in/text-out tasks (text-generation, classification, translation, etc.)
- `HFInferenceBinaryInputTask` — for tasks with binary inputs (image, audio)
- `HFInferenceConversational` — for chat completion via the old TGI endpoint
- `HFInferenceFeatureExtractionTask` — for embedding generation

These route to `https://api-inference.huggingface.co/models/{model_id}` and use the standard HF Inference API protocol.

### 10. Provider-Specific Customizations

Each provider module can override any of the 6 hook methods in `TaskProviderHelper`:

- **Auth**: Some providers append `Authorization: Bearer ***` in `_prepare_headers()` while others (Scaleway, Novita) handle it via the payload
- **Payload format**: Together's conversational payload uses `model: provider_id`; DeepInfra uses `model` in the body; others use URL path segments
- **Route construction**: Together uses `v1/completions` for text gen, `v1/chat/completions` for chat; DeepInfra uses model-specific route like `v1/inference/{model_id}`; Novita uses `v3/openai/chat/completions`
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

---

## 2026-07-25: hf-inference-providers-pricing-billing-hub-api-deep-dive — Inference Providers Pricing, Billing, Hub API & Security (Topic #278)

### Summary
Deep-dive on the newly documented Pricing & Billing model, Hub API query patterns, and Security & Compliance posture of Hugging Face Inference Providers. Covers the two billing approaches (Routed by HF vs Custom Provider Key), free credit allocations per account type ($0.10 free, $2.00 PRO, $2.00/seat Team/Enterprise), Organization billing with the `X-HF-Bill-To` header, HF-Inference as a provider with its own compute-time pricing, Hub API endpoints for listing provider-served models (`?inference_provider=`), provider-aware model info (`expand=inference`), the OpenAI-compatible models listing endpoint (`/v1/models`), the `hf CLI` integration (`--warm`, `--inference-provider`), security posture (SOC2 Type 2, TLS, 30-day log retention, no data storage), and zero-cost optimization strategies.

### Sources
- Pricing & Billing: https://huggingface.co/docs/inference-providers/en/pricing
- Hub API: https://huggingface.co/docs/inference-providers/en/hub-api
- Security & Compliance: https://huggingface.co/docs/inference-providers/en/security
- Main docs: https://huggingface.co/docs/inference-providers/en/index
- Hub integration: https://huggingface.co/docs/inference-providers/en/hub-integration
- Provider settings: https://hf.co/settings/inference-providers
- Model listing API: https://huggingface.co/api/models?inference_provider=fireworks-ai

### 1. Pricing & Billing Model

#### Free Credits Per Account Type

Every Hugging Face user receives monthly credits to experiment with Inference Providers. Credits auto-apply when requests route through Hugging Face:

| Account Type | Monthly Credits | Extra Usage |
|---|---|---|
| Free Users | $0.10 (subject to change) | Yes (credits purchase required) |
| PRO Users | $2.00 | Yes |
| Team or Enterprise Organizations | $2.00 per seat | Yes |

- **Team/Enterprise credits are shared** among all org members.
- Credits apply to **Routed by Hugging Face** billing only, **not** to Custom Provider Key billing.
- All users can purchase additional credits after exhausting monthly credits — ensures uninterrupted production access.

#### Two Billing Approaches

| Feature | Routed by Hugging Face | Custom Provider Key |
|---|---|---|
| How it Works | Request routes through HF to the provider | You set a custom provider key in HF settings |
| Billing | Pay-as-you-go on your HF account | Billed directly by the provider |
| Monthly Credits | ✅ Yes — apply to eligible providers | ❌ No |
| Provider Account Needed | ❌ No | ✅ Yes |
| Best For | Simplicity, experimentation, consolidated billing | More billing control, existing provider accounts |

**Integration surface** for both approaches: SDKs, Playground, widgets, Data Studio AI.

**Decision guide:**
- Start with **Routed by HF** for simplicity and to use monthly credits
- Use **Custom Provider Key** for specific provider features or consistent single-provider usage

#### Pay-as-you-Go Details

- **No markup:** Hugging Face charges you the same rates as the provider — costs are passed through directly.
- **No infrastructure management:** Just pay for what you use.
- **Usage tracking:** Visit https://hf.co/settings/inference-providers to see usage broken down by model and provider for the past month.
- **Organization tracking:** Same detailed view available for orgs under the organization's settings.

#### Organization Billing (Team & Enterprise)

Team & Enterprise orgs can **centralize billing** for all users. Each user keeps their own User Access Token, but requests are billed to the org:

```http
X-HF-Bill-To: my-org-name
```

**Resource Groups support** (Enterprise): Attribute inference costs to a specific resource group:

```http
X-HF-Bill-To: <resource-group-id>
```

The user's token must be a member of the resource group. Team & Enterprise orgs receive a pool of free usage credits based on seat count.

#### HF-Inference Cost Model

The `hf-inference` provider (formerly "Inference API / serverless") bills differently from external providers:

- **Charged by compute time × hardware price**, not per-token
- Example: A FLUX.1-dev request taking 10 seconds on a GPU costing $0.00012/sec → billed $0.0012
- As of July 2025: Focuses mostly on CPU inference (embeddings, text-ranking, text-classification, smaller LLMs like BERT, GPT-2)
- Still accessible through the same `InferenceClient` API as any other provider

### 2. Hub API for Inference Providers

The Hugging Face Hub provides several API endpoints for interacting with Inference Providers programmatically.

#### List Models by Provider (`inference_provider` query param)

```bash
# List all models served by Fireworks AI
curl -s https://huggingface.co/api/models?inference_provider=fireworks-ai | jq '.[].id'
# Returns: deepseek-ai/DeepSeek-V3-0324, deepseek-ai/DeepSeek-R1, Qwen/QwQ-32B, ...

# Combine with pipeline_tag filter
curl -s https://huggingface.co/api/models?inference_provider=fal-ai&pipeline_tag=text-to-image | jq '.[].id'
# Returns: black-forest-labs/FLUX.1-dev, stabilityai/stable-diffusion-3.5-large, ...

# Comma-separated provider list
curl -s https://huggingface.co/api/models?inference_provider=nscale,novita&pipeline_tag=image-text-to-text | jq '.[].id'

# All models served by any provider
curl -s https://huggingface.co/api/models?inference_provider=all&pipeline_tag=text-to-video | jq '.[].id'
# Returns: Wan-AI/Wan2.1-T2V-14B, Lightricks/LTX-Video, tencent/HunyuanVideo, ...
```

**Available providers** (from docs sidebar): Cerebras, Cohere, DeepInfra, Fal AI, Featherless AI, Fireworks, Groq, HF Inference, Novita, Nscale, OVHcloud AI Endpoints, Public AI, Replicate, Scaleway, Together, WaveSpeedAI, Z.ai

#### Using `hf CLI`

```bash
# List every model served by at least one provider
hf models ls --warm

# Search served models for a specific term
hf models ls --warm --search GLM-5.2

# Filter by provider and task
hf models ls --inference-provider fal-ai --pipeline-tag text-to-image

# Sort by downloads
hf models ls --inference-provider fireworks-ai --sort downloads
```

Flags:
- `--warm` — only models served by at least one provider
- `--inference-provider <name>` — filter by specific provider (repeatable for multiple)
- `--pipeline-tag <tag>` — filter by task type
- `--search <term>` — search model names
- `--expand inferenceProviderMapping` — shows which provider serves each model + provider-specific model ID
- `--json` — machine-readable output
- `--sort downloads` — order by popularity

#### Get Model Inference Status

Check if a model is served by an inference provider:

```python
from huggingface_hub import model_info

# Warm model (served by at least one provider)
info = model_info("google/gemma-3-27b-it", expand="inference")
print(info.inference)  # 'warm'

# Cold model (not served by any provider)
info = model_info("manycore-research/SpatialLM-Llama-1B", expand="inference")
print(info.inference)  # None
```

The `inference` attribute is either `"warm"` (served) or `None` (not served).

#### OpenAI-Compatible Models Listing

The router exposes an OpenAI-compatible endpoint listing all chat-completion models served by Inference Providers, with provider metadata:

```bash
curl -s https://router.huggingface.co/v1/models | jq '.data'
```

Response includes per-model provider info:
```json
{
  "id": "deepseek-ai/DeepSeek-V4-Pro",
  "object": "model",
  "created": 1776837885,
  "owned_by": "deepseek-ai",
  "architecture": {
    "input_modalities": ["text"],
    "output_modalities": ["text"]
  },
  "providers": [
    {
      "provider": "together",
      "provider_model_id": "deepseek-ai/DeepSeek-V4-Pro"
    }
  ]
}
```

This endpoint is useful for:
- Discovering which chat models are available across all providers
- Getting provider-specific model IDs for routing
- Checking model architecture capabilities (modalities)
- Building model selection UIs

### 3. Security & Compliance

#### Data Security / Privacy

- **No data stored for training:** Hugging Face does not store request body or response when routing requests
- **Logs:** Kept for debugging for up to 30 days — no user data or tokens stored in logs
- **In-transit encryption:** TLS/SSL for all Inference Provider routing
- **External providers:** Each provider is responsible for their own data security policies — refer to their individual policies

#### Hub Security

- **SOC2 Type 2 certified:** The Hugging Face Hub (which Inference Providers is a feature of) maintains SOC2 Type 2 compliance
- **Hub security documentation:** https://huggingface.co/docs/hub/security

### 4. Zero-Cost Pathways & Optimization

For Beer's zero-cost constraint, here's how to maximize free Inference Providers usage:

1. **Use Routed by HF billing** — takes advantage of the $0.10/mo free credits (enough for hundreds of small inference calls)
2. **Prefer `hf-inference` for CPU-friendly tasks** — embeddings, text classification, feature extraction — these are cheapest and often free-tier-eligible
3. **Use `:cheapest` suffix** on model IDs to always route to the lowest-cost provider:
   ```
   model="Qwen/Qwen2.5-7B-Instruct:cheapest"
   ```
4. **Provider-specific free tiers** — some providers may have their own free tiers accessible via Custom Provider Key
5. **Monitor usage** at https://hf.co/settings/inference-providers — track per-model and per-provider spend
6. **Batch model checks with the Hub API** — use `inference_provider=all` to discover which models are available before coding against them
7. **Use `hf models ls --warm`** to find freely-available models before committing to a specific one
