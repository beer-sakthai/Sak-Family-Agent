---
name: SakThai-hf-cookbook
author: SakThai
license: MIT
description: "Practical AI notebooks from the Open-Source AI Cookbook."
version: 0.2.0
tags: [Cookbook, Notebooks, Recipes, HuggingFace, Community]
---

# Open-Source AI Cookbook

Based on the [HF Open-Source AI Cookbook](https://huggingface.co/learn/cookbook). A collection of community-contributed notebooks ("recipes") for practical ML tasks — fine-tuning, inference, deployment, agents, and more. All notebooks are free and open-source.

## When to Use

- User asks for "practical examples" or "real ML recipes"
- User wants to see how to use a specific HF library in practice
- User needs working code for fine-tuning, evaluation, or deployment
- User wants to contribute a recipe to the community

## Prerequisites

- A HF account for running in Spaces or downloading models
- Python environment with relevant libraries
- No paid tier required

## Categories

| Category | Examples |
|----------|----------|
| MLOps | Training pipelines, evaluation, experiment tracking |
| LLM | Fine-tuning, RAG, function-calling, prompting |
| Computer Vision | Image classification, detection, segmentation |
| Diffusion | Text-to-image, LoRA, inpainting, ControlNet |
| Multimodal | Vision-language, audio-visual, CLIP |
| Search | Semantic search, embeddings, retrieval |
| Agents | smolagents, tool use, multi-agent |
| Enterprise Hub | SSO, RBAC, audit logs, storage |

## Procedure

1. **Browse recipes:** go to `https://huggingface.co/learn/cookbook` and scan categories
2. **Find a recipe:** filter by category or search for keywords
3. **Run locally:** download the `.ipynb` notebook and run
4. **Run in Spaces:** fork the associated Space if available
5. **Contribute:** submit PRs to the [GitHub repo](https://github.com/huggingface/cookbook)
6. **Enterprise recipes:** also check `/learn/cookbook/enterprise_*` recipes for SSO, serverless inference, dedicated endpoints, and Dev Spaces workflows

### Latest recipes (July 2026)
- **Concurrent Multi-Config SFT Training with RapidFire AI** — train multiple SFT configs in parallel using RapidFire AI's orchestration layer
- **Optimizing Language Models with DSPy GEPA** — use DSPy's Generalized Exploration Policy Algorithm for prompt/program optimization
- **Efficient Online Training with GRPO and vLLM in TRL** — combine GRPO (Group Relative Policy Optimization) with vLLM for fast rollout generation during online RL training
- **Fine-tuning LLMs for Function Calling with the xLAM Dataset** — train models to call functions/tools using the xLAM dataset
- **Post-training a VLM for Reasoning with GRPO using TRL** — fine-tune vision-language models (e.g., Qwen2-VL) for reasoning tasks with GRPO
- **TRL GRPO Reasoning with Advanced Reward** — advanced reward shaping for GRPO-based reasoning training

### Enterprise recipes
- `enterprise_cookbook_overview` — overview of enterprise HF Hub features
- `enterprise_cookbook_dev_spaces` — using Spaces in enterprise dev workflows
- `enterprise_hub_serverless_inference_api` — serverless inference via HF Hub API
- `enterprise_dedicated_endpoints` — dedicated Inference Endpoints for production
- `enterprise_cookbook_argilla` — data annotation and feedback with Argilla
- `enterprise_cookbook_gradio` — building enterprise demos with Gradio
- `mlflow_ray_serve` — MLflow + Ray Serve integration for model serving

## Pitfalls

- The cookbook is NOT a structured course — it's a collection of standalone notebooks.
- Notebooks may use specific library versions — check requirements.txt before running.
- Some recipes need GPU — look for ZeroGPU-compatible notebooks.
- Community-contributed means varying quality — check comments and freshness.
- Raw markdown for individual recipes may not be accessible via `/index.md` paths — the cookbook is a SvelteKit SPA. Use the GitHub repo instead for raw notebook files: `https://github.com/huggingface/cookbook`. For more on researching HF SPA docs, see `hf-context-engineering` → `references/hf-docs-research.md`.

## Verification

```bash
curl -sL https://huggingface.co/learn/cookbook | grep -oP 'recipe-\w+' | head -5
```
Returns the first few recipe IDs from the cookbook page.

Check the GitHub repo for the latest notebooks:
```bash
curl -sL https://api.github.com/repos/huggingface/cookbook/contents | jq -r '.[].name'
```
