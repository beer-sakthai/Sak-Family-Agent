---
name: SakSit-free-image-generation
category: creative
description: Free image generation via Hugging Face Spaces FLUX - zero-cost fallback when FAL_KEY is missing or image_generate is unavailable. Covers Gradio client workflow, quota management, and Beer's just-do-it preference.
version: 1.0.0
author: SakSit
tags:
  - image-generation
  - flux
  - huggingface-spaces
  - free
  - fallback
  - gradio
related_skills:
  - linkedin-content-publishing
  - saksit-social-media-posting-workflows
---

# SakSit Free Image Generation

Class-level skill for generating images at zero cost when the primary image_generate tool is unavailable (FAL_KEY missing, provider error). Uses FLUX.1-schnell on Hugging Face Spaces via gradio_client - no API key, no credit card, no signup required.

## When to load

Use this skill when:
- image_generate fails with FAL_KEY environment variable is not set
- Beer says make pics or create images and FAL is down
- An infographic, card, or visual needs to be generated with no paid option available
- Beer expresses impatience (do it what you waiting, use easy dont need a key) - take this as a signal to act immediately on the free path without asking

## Beer's rule: Just do it

When a free image generation path exists (HF Spaces, Gradio client), execute it immediately. Do NOT:
- Ask permission
- Explain why other options failed
- Explore paid alternatives first
- Wait for confirmation

Beer's exact words: "do it what you waiting use easy dont need a key" - stop hesitating, use the free tool in front of you.

## Workflow

### 1. Set up environment
```bash
uv venv /tmp/flux-venv
uv pip install --python /tmp/flux-venv/bin/python gradio-client -q
```

### 2. Connect to FLUX Space
```python
from gradio_client import Client
client = Client('black-forest-labs/FLUX.1-schnell')
```

### 3. Generate image
```python
result, seed = client.predict(
    prompt="Your detailed image description here",
    seed=0, randomize_seed=True,
    width=1344, height=768,
    num_inference_steps=4,
    api_name='/infer'
)
```

### 4. Save and deliver
```python
import shutil, os
dst = "/opt/data/profiles/saksit/infographic/image-name.png"
os.makedirs(os.path.dirname(dst), exist_ok=True)
shutil.copy2(result, dst)
# Deliver via MEDIA:/path/to/file
```

## Aspect Ratio Reference

| Desired | width x height | Use Case |
|---------|---------------|----------|
| 16:9 landscape | 1344 x 768 | LinkedIn, YouTube thumbnails |
| 9:16 portrait | 768 x 1344 | Instagram Stories/Reels |
| 1:1 square | 1024 x 1024 | Instagram feed |
| 4:3 | 1152 x 864 | Presentations |
| 3:2 | 1200 x 800 | Blog headers |

## Quota Management

| Detail | Value |
|--------|-------|
| Free GPU per session | ~90 seconds |
| Inference steps default | 4 (good for illustrations) |
| Reset cycle | ~24 hours |
| Cost | $0 |

Quota exhausted error:
```
AppError: You have exceeded your ZeroGPU quota (90s requested vs. 0s left)
```

When exhausted: wait ~24h, try alternative Spaces, or authenticate with HF token.

## Alternative Spaces (separate quotas)

| Space | Status |
|-------|--------|
| black-forest-labs/FLUX.1-schnell | Most reliable |
| Nymbo/FLUX.1-Schnell-Serverless | Often offline |
| Deddy/Unlimited_FLUX_Schnell_V1-3 | Often offline |

## Pitfalls

- Cold start - first request takes 5-15s for GPU boot
- Use num_inference_steps=2 for tests, 4 for real outputs, 8+ for photorealistic
- Clean up: rm -rf /tmp/flux-venv after done
- ZeroGPU quota is per-account, shared across all Spaces
- FLUX is text-to-image only - no image editing
- Always create fresh venv each session
- Clean up with: rm -rf /tmp/flux-venv (and any other /tmp/hf* dirs)
- **Related skills:** baoyu-infographic (infographic prompt design), saksit-huggingface-hub-management (HF repo management + image gen section)
- **HF gated model access**: model_info() returns public data even for gated repos you dont have access to. Use list_repo_files() to verify actual download access. See references/hf-gated-model-api-pitfalls.md.
