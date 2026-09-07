---
name: SakThai-hf-inference-providers
description: "A skill for Hf Inference Providers."
---

# Hugging Face Inference Providers

author: SakThai
license: MIT

## Description
Comprehensive knowledge of the Hugging Face Inference Providers ecosystem — the multi-provider serverless inference platform that gives developers unified access to hundreds of ML models through a single API, powered by world-class inference partners.

## Capabilities
- Understand Inference Providers architecture: proxy layer, router, provider selection policies
- Use `huggingface_hub.InferenceClient` with provider selection (`auto`, `:fastest`, `:cheapest`, `:preferred`, explicit provider)
- Configure OpenAI-compatible endpoint at `https://router.huggingface.co/v1` for chat completions
- Set custom API keys per provider in HF settings for direct billing
- Filter Hub models by inference provider (`?inference_provider=fireworks-ai`)
- Use `inference_provider=all` / `hf models ls --warm` to discover all warm models
- Query per-model provider mappings via `inferenceProviderMapping` expand field
- Understand the two billing models: Routed by HF (monthly credits) vs BYOK (direct provider billing)
- Understand monthly free credits, organization billing, and token permissions
- Use Inference Playground, Data Studio AI, and model page widgets backed by Inference Providers
- Configure agent integrations: Hermes Agent, OpenCode, Codex, Claude Code, Pi, Vision Agents
- Understand free-tier, PRO, and Enterprise billing models
- Guide users on zero-cost pathways using free tier credits
- Understand supported task types per provider (chat, feature extraction, text-to-image, text-to-video, speech-to-text)

## Key Commands
- `hf models ls --warm` — list every model served by at least one provider
- `InferenceClient(provider="auto")` — automatic fastest-provider selection
- `InferenceClient(provider="together")` — explicit provider selection
- `model="org/model:cheapest"` — model ID suffix for cost-optimized routing
- `model="org/model:fastest"` — model ID suffix for speed-optimized routing
- `model="org/model:preferred"` — model ID suffix for user preference ordering
- `GET /api/models?inference_provider=all` — REST API equivalent of `--warm`
- `GET /api/models?inference_provider=fireworks-ai&pipeline_tag=text-generation` — filtered provider query
- `api.list_models(inference_provider="together")` — Python SDK equivalent

## Provider List (17 providers, verified 2026-07-25)
Cerebras, Cohere, DeepInfra, Fal AI, Featherless AI, Fireworks, Groq, HF Inference, Novita, Nscale, OVHcloud AI Endpoints, Public AI, Replicate, Scaleway, Together, WaveSpeedAI, Z.ai

## Billing Models
- **Routed by HF** — free monthly credits apply, no provider keys needed, zero markup
- **BYOK (Bring Your Own Key)** — use existing provider accounts, direct billing
- **Organization billing** — Team/Enterprise org credits shared across members

## Agent Integrations
- Hermes Agent: `export HERMES_PROVIDER=hf` + HF token
- OpenCode: `opencode auth login` → select Hugging Face
- Codex: `codex config set provider hf`
- Claude Code: `export CLAUDE_CODE_PROVIDER=hf`

## Security
- SOC2 Type 2 certified
- TLS/SSL encryption
- No request/response data stored for training
- Fine-grained token permissions

## References
- `references/hf-learnings.md` — complete 1565-line reference covering source architecture (1273 lines) + Hub API, Pricing & Agent Integrations deep-dive (292 lines)
- https://huggingface.co/docs/inference-providers/en/index
- https://huggingface.co/docs/inference-providers/en/hub-api
- https://huggingface.co/docs/inference-providers/en/pricing

## Related Skills
- hf-inference-endpoints (dedicated GPU endpoints, different product)
- hf-inference-client-serverless-inference-patterns (older HF Inference API patterns)
- hf-inference-client-provider-fallback-and-routing
- hf-hub-oauth-and-token-management (token creation for inference)
- hf-inference-router-openai-compatible-endpoint (OpenAI-compatible Router endpoint)
- hf-hub-search-discovery-api (model search/discovery API)
- hf-hub-cli-rebuilt (--warm flag on hf models ls)
