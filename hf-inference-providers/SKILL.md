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
- Use Inference Playground, Data Studio AI, and model page widgets backed by Inference Providers
- Understand free-tier, PRO, and Enterprise billing models
- Guide users on zero-cost pathways using free tier credits
- Integrate with agent frameworks (OpenCode, Codex, Claude Code, Hermes Agent, Pi)
- Understand supported task types per provider (chat, feature extraction, text-to-image, text-to-video, speech-to-text)

## Key Commands
- `hf models ls --warm` — list every model served by at least one provider
- `InferenceClient(provider="auto")` — automatic fastest-provider selection
- `InferenceClient(provider="together")` — explicit provider selection
- `model="org/model:cheapest"` — model ID suffix for cost-optimized routing
- `model="org/model:fastest"` — model ID suffix for speed-optimized routing
- `model="org/model:preferred"` — model ID suffix for user preference ordering

## Provider List (as of 2026-07-25)
Cerebras, Cohere, DeepInfra, Fal AI, Featherless AI, Fireworks, Groq, HF Inference, Novita, Nscale, OVHcloud AI Endpoints, Public AI, Replicate, Scaleway, Together, WaveSpeedAI, Z.ai

## Related Skills
- hf-inference-endpoints (dedicated GPU endpoints, different product)
- hf-inference-client-serverless-inference-patterns (older HF Inference API patterns)
- hf-inference-client-provider-fallback-and-routing
- hf-hub-oauth-and-token-management (token creation for inference)
