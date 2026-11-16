---
name: SakThai-hf-spaces-dependencies-and-sdks
version: 1.0.0
description: Complete reference on Hugging Face Spaces dependency management, SDK
  selection (Gradio, Docker, Streamlit, Static), Python requirements, and ZeroGPU
  hardware optimization.
category: mlops
tags:
- dependencies
- docker
- gradio
- hf
- huggingface
- sdks
- spaces
- streamlit
- zerogpu
author: SakThai
license: MIT
---

# HF Spaces Dependencies, SDKs & ZeroGPU Configuration

Configure SDK environments, package manifests, and hardware resources for Hugging Face Spaces.

## Overview

Hugging Face Spaces supports four primary SDK architectures: **Gradio**, **Docker**, **Streamlit**, and **Static**. Each SDK environment defines its runtime dependencies through standardized configuration files.

## SDK Matrix & Manifests

| SDK | Primary Manifests | Ideal Use Case | Zero-Cost Availability |
|:---|:---|:---|:---|
| **Gradio** | `requirements.txt`, `packages.txt`, `README.md` | Interactive ML demos & tools | 2 Free ZeroGPU Spaces per personal account |
| **Docker** | `Dockerfile`, `README.md` | Custom backend microservices, FastAPI, Node | ZeroGPU or CPU basic |
| **Streamlit**| `requirements.txt`, `packages.txt` | Data analysis and dashboard apps | ZeroGPU or CPU basic |
| **Static** | Plain HTML, CSS, JavaScript | Client-side web apps and landing pages | Unlimited Free (CDN served) |

## Dependency Manifest Specifications

### 1. Python Dependencies (`requirements.txt`)
Specify pinned or minimum library versions:
```text
transformers>=4.40.0
torch>=2.2.0
accelerate>=0.30.0
huggingface_hub>=0.23.0
```

### 2. System Debian Packages (`packages.txt`)
Install Linux system packages (via `apt-get` during container build):
```text
ffmpeg
libsm6
libxext6
git-lfs
```

### 3. Space README Metadata Header
Configure runtime parameters in `README.md`:
```yaml
---
title: SakThai Assistant
emoji: 🦁
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 4.44.0
python_version: 3.11
app_file: app.py
pinned: false
---
```

## References
- Comprehensive deep-dive on Dockerfiles, caching layers, and ZeroGPU quotas: [`references/hf-learnings.md`](./references/hf-learnings.md).
