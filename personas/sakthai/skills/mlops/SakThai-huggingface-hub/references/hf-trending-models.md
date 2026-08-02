# HF Trending Models — Live Reference

> **Purpose:** Track and report currently trending models on Hugging Face Hub.
> **Source:** `GET https://huggingface.co/api/models?sort=trendingScore&limit=15`
> **Last updated:** 2026-07-23 (fourth tick — 14:34 UTC)

## Current Top 5 (2026-07-23 · 14:34 UTC)

| # | Model | Creator | Type | License | Downloads | Likes | TrendingScore | Why Hot |
|---|-------|---------|------|---------|-----------|-------|--------------|---------|
| 1 | **baidu/Unlimited-OCR** | Baidu | Universal OCR (image-text-to-text) | MIT | 2,414,259 | 2,829 | 755 | SOTA multilingual OCR — trained with ms-swift, runs at 1024px / 32K context. Dominating trends for weeks. |
| 2 | **thinkingmachines/Inkling** | Thinking Machines Lab | Multimodal MoE (image-text-to-text + audio) | Apache 2.0 | 24,669 | 1,486 | 725 | Massive multimodal MoE — handles image, text, audio, NVFP4 quant available. Rapid adoption since release. |
| 3 | **poolside/Laguna-S-2.1** | Poolside | Code MoE (text-generation) | openmdw-1.1 | 13,285 | 464 | 458 | 118B total / 8B active — agentic coding MoE built for long-horizon software tasks. vLLM-compatible. |
| 4 | **prism-ml/Ternary-Bonsai-27B-gguf** | Prism ML | Ternary 1-bit (text-generation, GGUF) | Apache 2.0 | 576,083 | 967 | 387 | Ternary quantization — 27B-class reasoning in ~4GB. ~26 tok/s on Apple M5 Pro. 95% intelligence retention. |
| 5 | **DavidAU/Qwen3.6-27B-Fable-Fusion-711-…-GGUF** | DavidAU | Qwen merge (image-text-to-text, GGUF) | Apache 2.0 | 334,847 | 373 | 359 | Aggressive uncensored Qwen3.6 merge — ARC-c 700+ in 8-bit and 4-bit. Heretic ARA fine-tune method. |

**Links:**
[Unlimited-OCR](https://huggingface.co/baidu/Unlimited-OCR) ·
[Inkling](https://huggingface.co/thinkingmachines/Inkling) ·
[Laguna-S-2.1](https://huggingface.co/poolside/Laguna-S-2.1) ·
[Ternary-Bonsai-27B-GGUF](https://huggingface.co/prism-ml/Ternary-Bonsai-27B-gguf) ·
[Qwen3.6 Fable Fusion GGUF](https://huggingface.co/DavidAU/Qwen3.6-27B-Fable-Fusion-711-Uncensored-Heretic-NM-DAU-NEO-MAX-MTP-GGUF)

## Positions 6–10

| # | Model | License | Pipeline | Downloads | Likes | TS | Notes |
|---|-------|---------|----------|-----------|-------|----|-------|
| 6 | **upstage/Solar-Open2-250B** | other | text-generation | 362 | 388 | 339 | Fresh 250B open model from Upstage, released 2026-07-22. Early days. |
| 7 | **Nanbeige/Nanbeige4.2-3B** | Apache 2.0 | text-generation | 4,532 | 287 | 284 | Compact 3B release, Apache 2.0. Uploaded 2026-07-21. |
| 8 | **zai-org/GLM-5.2** | MIT | text-generation | 596,442 | 4,357 | 283 | 753B MoE — still highest-likes on this list. MIT license, established leaderboard presence. arxiv:2602.15763 |
| 9 | **prism-ml/Bonsai-27B-gguf** | Apache 2.0 | text-generation (GGUF) | 1,910,116 | 611 | 283 | Non-ternary sibling of #4 — standard quant of Bonsai-27B. |
| 10 | **HauhauCS/Qwen3.6-35B-A3B-Uncensored** | Apache 2.0 | image-text-to-text (GGUF) | 2,027,080 | 3,023 | 195 | Another aggressive Qwen3.6 uncensored merge — highest downloads this tick. |

## Trends

| Signal | Examples | Direction |
|--------|----------|-----------|
| Multimodal MoE domination | Inkling (952B moe), Unlimited-OCR — both `image-text-to-text` | 🔥 Dominant |
| Qwen merge wave | DavidAU (27B), HauhauCS (35B) — uncensored Qwen3.6 GGUF variants | 🔥 Hot |
| Ternary / extreme quantization | Bonsai family — 1-bit weights, on-device inference | 📈 Growing |
| Code-specific MoE | Laguna-S-2.1 — agentic coding with openMDW license | 📈 Steady |
| Compact new releases | Nanbeige4.2-3B — small models gaining traction | 🆕 Emerging |

## Also Notable (11–15)

| # | Model | Pipeline | Likes | Downloads | TS | Notes |
|---|-------|----------|-------|-----------|----|-------|
| 11 | conradlocke/krea2-identity-edit | — | 513 | 0 | 195 | Identity-based image editing — new concept, zero downloads yet? |
| 12 | Motif-Technologies/Motif-3-Beta | text-generation | 169 | 1,856 | 164 | New 3B model from Motif. Beta release. |
| 13 | microsoft/Mage-Flow | text-to-image | 164 | 411 | 162 | Microsoft's latest text-to-image pipeline. |
| 14 | empero-ai/Qwythos-9B-Claude-Mythos-5-1M-GGUF | image-text-to-text | 2,432 | 2,126,755 | 161 | Qwen-based merge — high downloads, Claude-Mythos lineage. |
| 15 | openbmb/MiniCPM-RobotManip | robotics | 160 | 408 | 147 | Robotics model from OpenBMB — robot manipulation tasks. |
