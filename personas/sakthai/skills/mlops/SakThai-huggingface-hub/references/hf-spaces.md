---
name: hf-spaces
description: "Tracked snapshot of trending Hugging Face Spaces with reports"
version: 3.0.0
author: SakThai Agent
tags: [huggingface, spaces, trending, reports]
---

# Hugging Face Spaces — Trend Report
**Date:** 2026-07-23 (Round 3)
**Author:** SakThai · Main Lead of the House
**Source:** HF API (trending_score sort) + HF Hub API

---

## Top 3 Most Interesting Spaces This Report

### 1. kulkas2pintu/wan555 — Wan2.2 14B Fast Preview
- **Creator:** kulkas2pintu
- **Likes:** 697 · **Trending Score:** 154 (🔥 #1 trending) · **Created:** 2026-05-17 · **SDK:** Gradio
- **What it does:** Generate a video from an image with a text prompt using the Wan 2.2 14B model. Optimised for speed (Fast Preview). The top trending Space on the Hub right now with serious momentum — 697 likes and a wide gap over #2.
- **Tags:** `gradio`, `mcp-server`
- **Link:** https://huggingface.co/spaces/kulkas2pintu/wan555

### 2. smolagents/hf-realtime-voice — HF Realtime Voice
- **Creator:** smolagents (Hugging Face)
- **Likes:** 454 · **Trending Score:** 54 · **Created:** 2026-07-01 · **SDK:** Docker
- **What it does:** Voice chat over WebSocket against a Hugging Face speech-to-speech backend. Drop-in alternative using WebSocket transport instead of WebRTC. Streams mic audio as PCM16 16 kHz mono base64 chunks to the server, receives `response.output_audio.delta` back. Built by the smolagents team — pairs voice interaction with agent capabilities.
- **Tags:** `docker`, `hf-oauth`
- **Link:** https://huggingface.co/spaces/smolagents/hf-realtime-voice

### 3. FINAL-Bench/Aether-Sovereign-AI — Aether-7B-5Attn
- **Creator:** FINAL-Bench (VIDRAFT, Korean AI startup)
- **Likes:** 30 · **Trending Score:** 18 · **Created:** 2026-07-19 · **SDK:** Docker
- **What it does:** A 100% open-source sovereign foundation model (Apache-2.0). Not "open weights" — genuinely everything: weights, training-data recipe (byte-for-byte reproducible from public sources), training code, every hyperparameter, complete training logs, and full architecture source. Built from scratch by Korean AI startup VIDRAFT. 7B parameters with 5 heterogeneous attention heads. Includes a live demo Space and companion instruct-tuned model. A rare example of true open-source LLM development.
- **Tags:** `sovereign-ai`, `open-source-llm`, `fully-open`, `foundation-model`, `korean`, `mixture-of-experts`, `heterogeneous-attention`, `apache-2.0`
- **Link:** https://huggingface.co/spaces/FINAL-Bench/Aether-Sovereign-AI

---

## Honourable Mentions

| Space | Creator | Likes | Created | Description |
|-------|---------|-------|---------|-------------|
| prism-ml/Ternary-Bonsai-27B-Demo | prism-ml | 23 | 2026-07-15 | Chat demo for 1.58-bit ternary 27B model via HF Inference Providers |
| victor/lingbot-video | victor | 53 | 2026-07-08 | LingBot video interaction — multimodal video understanding |
| google/gemma4_vision_token_budget | Google | 26 | 2026-07-14 | Interactive visualisation of Gemma 4's vision token budget |
| microsoft/mage-flow | Microsoft | 36 | 2026-07-22 | Native-resolution image generation and editing (also in prev. report) |
| nineninesix/gepard | nineninesix | 37 | 2026-07-03 | GEPARD — Gradio-based demo (newly trending) |
| sensenova/SenseNova-Vision | SenseTime | 40 | 2026-07-07 | Vision-language model demo from SenseTime |
| yijunwang2/krea2-outpaint | yijunwang2 | 43 | 2026-07-17 | Krea 2 AI outpainting (extend images beyond borders) |
| cinderholm/wan2-2-i2v-v3 | cinderholm | 21 | 2026-07-19 | Wan 2.2 image-to-video v3 variant |

---

## Trends & Observations (Round 3)

- **Video generation dominates.** Wan 2.2 variants hold multiple top spots. The ecosystem is rapidly iterating on image-to-video pipelines.
- **Voice AI is heating up.** smolagents shipping real-time WebSocket voice + the Cerebras/Gemma 4 voice pipeline (from Round 2) point toward voice-first agent interfaces becoming standard.
- **True open-source LLMs are gaining momentum.** Aether is a genuine fully-open (Apache-2.0) foundation model built from scratch — not another "open weights" release. Korean AI ecosystem emerging.
- **Ternary quantization goes mainstream.** The Ternary-Bonsai-27B demo proves 1.58-bit models are practical for inference in the browser/on-device.
- **MCP Server tag spread.** Many trending spaces now tag `mcp-server`, signalling growing integration with the Model Context Protocol ecosystem.
