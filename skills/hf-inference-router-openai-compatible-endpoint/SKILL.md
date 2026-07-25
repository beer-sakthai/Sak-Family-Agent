# HF Inference Router: OpenAI-Compatible Endpoint

**author: SakThai**
**license: MIT**

## Description

Deep-dive into Hugging Face's Inference Router — the OpenAI-compatible proxy endpoint at `https://router.huggingface.co/v1` that provides server-side provider selection, auto-failover, and unified access to hundreds of models across multiple inference providers through a single OpenAI SDK-compatible API.

## Topics Covered

- Router architecture and proxy model
- Provider selection policies (`:fastest`, `:cheapest`, `:preferred`, explicit provider)
- `/v1/models` endpoint — listing available models with provider metadata
- Authentication and token permissions
- Integration patterns (Python, JavaScript, cURL)
- Auto-failover behavior
- Comparison with Hugging Face InferenceClient
- Limitations (chat completions only)

## Key Resources

- Official docs: https://huggingface.co/docs/inference-providers/en/index
- Hub API docs: https://huggingface.co/docs/inference-providers/en/hub-api
- Provider settings: https://hf.co/settings/inference-providers
- Router endpoint: `https://router.huggingface.co/v1`

## Files

- `references/hf-learnings.md` — Full research with architecture, API reference, provider selection policies, integration examples, and comparison matrix
