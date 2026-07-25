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

*Skill: hf-inference-providers — Hugging Face Inference Providers comprehensive reference: multi-provider serverless inference architecture, 17+ providers, router proxy with selection policies (:fastest/:cheapest/:preferred), Hub integration (widgets, playground, Data Studio AI), client SDK patterns, billing model, security (SOC2, TLS, no data storage), agent integrations, and zero-cost development pathways*
