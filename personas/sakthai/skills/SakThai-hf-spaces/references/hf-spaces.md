---
name: hf-spaces-report
title: HF Spaces Trend Reports
description: Chronological rounds of trending Hugging Face Spaces analysis
current_round: 5
---

# HF Spaces Trend Reports

## Round 4 — 2026-07-23 (evening)

**Source:** EXA web search → workbench parse

### Top 3

#### 1. 🎬 Wan2.2 14B Fast Preview — *by r3gm*
FP8-optimized video generation from text+image prompts on ZeroGPU with MCP support. Multiple iteration Spaces (preview, preview2, preview-2c) showing active optimization. The Wan2.2 video gen family is rapidly expanding with fast-inference variants.
→ https://huggingface.co/spaces/r3gm/wan2-2-fp8da-aoti-preview2

#### 2. 🧠 Gemma 4 — Vision Token Budget — *by Google*
First-party Google Space: upload an image and interactively tweak token budgets (resolution, patch size, token count) to see how Gemma 4's vision-language output quality changes. Essential for production deployments needing cost/quality tradeoff understanding.
→ https://huggingface.co/spaces/google/gemma4_vision_token_budget

#### 3. 💻 AnyCoder — *by akhaliq*
Generate fully functional app code from a plain-text description. 3.26k likes. Supports multiple frameworks — "React dashboard with dark mode" produces complete runnable code, not snippets. Dominant rapid-prototyping Space on HF.
→ https://huggingface.co/spaces/akhaliq/AnyCoder

### Honourable Mentions
| Space | Creator | Likes | Description |
|-------|---------|-------|-------------|
| HuggingFaceTB/smol-training-playbook | HuggingFaceTB | 3.17k | Full guide to building world-class LLMs |
| hf-audio/open-asr-leaderboard | HuggingFace Audio | 1.34k | Speech recognition model benchmarks |
| NeuralFalcon/remove-silence-from-audio | NeuralFalcon | 274 | Clean audio by removing silence |
| linoyts/ltx-2.3-sync | linoyts | 155 | Portrait animation & lipsync |
| Edd16/icml2026-*-repro | Edd16 | Various | Individual ICML 2026 paper reproductions |
| pcuenq/gemma-4-object-detection | pcuenq | New | Object detection with Gemma 4 on Zero |
| zerogpu-aoti/wan2-2-fp8da-aoti-faster | zerogpu-aoti | New | Wan2.2 optimized by ZeroGPU team |

### Ecosystem Pulse
- ZeroGPU now supports MCP → agent-to-Space interactions
- Wan2.2 fast variants multiplying across community + org accounts
- Google shipping official Gemma 4 tooling Spaces (Vision Token Budget, Object Detection)
- Edd16 driving a reproducibility wave with individual ICML 2026 paper reproductions

---

## Round 3 — 2026-07-23 (midday)

**Source:** HF API trending_score sort + HF Hub API

### Top 3

#### 1. kulkas2pintu/wan555 — Wan2.2 14B Fast Preview
697 likes · trending score 154 (#1 trending). Generate video from image+text prompt. Optimised FP8 inference. MCP-server tagged.
→ https://huggingface.co/spaces/kulkas2pintu/wan555

#### 2. smolagents/hf-realtime-voice — HF Realtime Voice
454 likes. Voice chat over WebSocket against HF speech-to-speech backend. Built by smolagents team — pairs voice interaction with agent capabilities.
→ https://huggingface.co/spaces/smolagents/hf-realtime-voice

#### 3. FINAL-Bench/Aether-Sovereign-AI — Aether-7B-5Attn
30 likes. 100% open-source foundation model (Apache-2.0) — not just "open weights". Everything open: training data recipe, code, hyperparameters, logs. Built from scratch by Korean AI startup VIDRAFT. 7B parameters with 5 heterogeneous attention heads.
→ https://huggingface.co/spaces/FINAL-Bench/Aether-Sovereign-AI

### Trends
- Video generation dominates (Wan2.2 variants)
- Voice AI heating up (WebSocket voice pipelines)
- True open-source LLMs gaining momentum (Aether)
- Ternary quantization going mainstream (Ternary-Bonsai-27B)
- MCP Server tag spreading across trending Spaces

---

## Round 2 — 2026-07-23 (morning)

**Source:** HF Spaces trending page + EXA/Composio web search + HF API

### Top 3

#### 1. webml-community/bonsai-webgpu-kernels
297 likes. 1-bit 27B LLM in-browser on WebGPU. Ternary quantization fits entire model in VRAM.
→ https://huggingface.co/spaces/webml-community/bonsai-webgpu-kernels

#### 2. victor/gemma-avatar
151 likes. Talk to Gemma 4 via 3D lip-synced avatar. Real-time voice + vision pipeline with Cerebras inference.
→ https://huggingface.co/spaces/victor/gemma-avatar

#### 3. nvidia/Nemotron-Labs-Audex
27 likes. NVIDIA's unified audio-text LLM — speech recognition, audio understanding, generation in one decoder.
→ https://huggingface.co/spaces/nvidia/Nemotron-Labs-Audex

---

## Round 1 — 2026-07-22

**Source:** Initial HF Spaces trend scan

### Top 3

#### 1. baidu/Unlimited-OCR
280 likes. High-accuracy OCR from images and PDFs.
→ https://huggingface.co/spaces/baidu/Unlimited-OCR

#### 2. tencent/Hy3
53 likes. Hunyuan Hy3 multi-turn streaming chat + function calling.
→ https://huggingface.co/spaces/tencent/Hy3

#### 3. microsoft/mage-flow
36 likes. Efficient native-resolution image generation and editing.
→ https://huggingface.co/spaces/microsoft/mage-flow


## Round 5 — 2026-07-23 (night)

**Source:** HF Hub API (`sort=trendingScore`) + EXA context searches

### Top 3

#### 1. ICML 2026 Agent Reproductions — *by ICML-2026-agent-repro*
Running Jul 15 to Aug 2: a community challenge to reproduce ICML 2026 agent papers at scale. 174 likes, static site with dashboards tracking reproduction status per paper. Represents the reproducibility crisis in AI shifting from complaint to coordinated action — HF as the infrastructure layer for open science.
→ https://huggingface.co/spaces/ICML-2026-agent-repro/challenge

#### 2. TripoSplat — Generative 3D Gaussians — *by VAST-AI*
Single 2D image to high-quality variable-count 3D Gaussian splats with learned density control. 307 likes. No multi-view input needed. From VAST-AI (known for TripoSR, Tripo3D). Pushes real-time 3D asset creation toward practical quality.
→ https://huggingface.co/spaces/VAST-AI/TripoSplat

#### 3. Krea 2 Identity Edit — *by conradlocke*
Identity-preserving image editing with KREA 2: change style, background, or expression while keeping the subject recognizable. 109 likes. Also forked by `hugging-apps` official account — signalling HF-backed adoption.
→ https://huggingface.co/spaces/conradlocke/krea2-identity-edit

### Honourable Mentions
| Space | Creator | Likes | Description |
|-------|---------|-------|-------------|
| prism-ml/Ternary-Bonsai-27B-Demo | Prism ML | 23 | Ternary-quantized 27B GGUF inference — ternary goes mainstream beyond niche research |
| hugging-apps/gnm | hugging-apps | 15 | Google GNM interactive 3D face model — MCP-server tagged, browser-based real-time rendering |
| feyninc/pulpie | Feyn Inc | 43 | Small language model with live benchmark dashboard (ROUGE-5 F1); open-weight SLM from a new lab |
| hugging-apps/unise-speech-enhancement | hugging-apps | 61 | Neural speech enhancement with MCP-server support — clean audio in real time |
| Soofi-Project/Pretraining-Tech-Report | Soofi Project | 23 | Open technical report documenting pretraining methodology, data mixes, and hyperparameter search |

### Ecosystem Pulse
- Reproducibility goes collective — ICML 2026 Agent Reproductions is the first large-scale coordinated reproduction challenge on HF, with live dashboards and leaderboards
- 3D assets from single images — TripoSplat shows 3D Gaussian splatting hitting production quality; no multi-view capture needed
- Identity-preserving editing takes off — KREA 2 Identity Edit points to a new paradigm: edit everything except the subject's identity
- MCP-server tag spreads — now appearing on 3D (gnm), video, and audio Spaces, not just LLM agents
- Prism ML brings ternary to GGUF — after bonsai-webgpu-kernels (round 2), ternary-quantized 27B is now available as a downloadable GGUF
