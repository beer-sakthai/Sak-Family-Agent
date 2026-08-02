---
name: SakThai-hf-hub-configuration
author: SakThai
license: MIT
description: Complete reference for huggingface_hub library configuration — all environment variables, cache paths, token management, and customization options
category: mlops
version: 1.0.0
---
# HF Hub Configuration

Trigger when: user asks about huggingface_hub configuration, environment variables, cache paths, token setup, offline mode, proxy settings, or HF_HOME/HF_HUB_CACHE paths.

## Key Areas

- **Path variables**: HF_HOME, HF_HUB_CACHE, HF_ASSETS_CACHE, HF_XET_CACHE, HF_TOKEN_PATH
- **Auth variables**: HF_TOKEN, HF_HUB_DISABLE_IMPLICIT_TOKEN
- **Boolean toggles**: offline mode, telemetry, progress bars, symlinks, update checks
- **Performance**: HF_XET_HIGH_PERFORMANCE, HF_HUB_ENABLE_HF_TRANSFER (deprecated)
- **Endpoint customization**: HF_ENDPOINT, HF_INFERENCE_ENDPOINT
- **Deprecated legacy vars**: HUGGINGFACE_HUB_CACHE, HUGGING_FACE_HUB_TOKEN

See `references/hf-learnings.md` for the complete deep-dive reference.
