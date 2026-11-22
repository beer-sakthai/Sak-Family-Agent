# Google AI Studio Rate Limits, Quotas & Model Tier Guide

This document captures the verified November 2026 ground-truth rate limits, quotas, and operational constraints for the Google Gemini family in Google AI Studio (observed baseline for project `flutter-ai-playground-a63ab` and standard AI Studio projects).

---

## 1. Text & Multimodal Reasoning Models (Free-Tier Eligible)

Google dynamically assigns project-level quotas across **RPM** (Requests Per Minute), **TPM** (Input Tokens Per Minute), and **RPD** (Requests Per Day).

| Category | Model Name | Model ID | Input / Output Token Window | Free RPM | Free TPM | Free RPD | Notes & Architectural Constraints |
|---|---|---|---|---|---|---|---|
| **Frontier Reasoning (Gemini 4)** | **Gemini 4 Hydrogen** | `gemini-4-hydrogen` | 1,048,576 unified (65,536 sync output; up to 1M via long decode) | ~5 RPM | ~250,000 TPM | ~20 RPD | **Only Gemini 4 model on Free Tier**. Supports `low`, `medium`, `high` (default), and `xhigh` thinking levels. |
| **Balanced Multimodal (Gemini 3)** | **Gemini 3.8 Flash** | `gemini-3.8-flash` | 1,048,576 / 65,536 | ~5 RPM | ~250,000 TPM | ~20 RPD | Flagship Gemini 3 Flash model; includes free explicit and implicit context caching. |
| **Balanced Multimodal (Gemini 3)** | **Gemini 3.6 Flash** | `gemini-3.6-flash` | 1,048,576 / 65,536 | ~5 RPM | ~250,000 TPM | ~20 RPD | Previous-generation Flash; supports context caching and code execution. |
| **Balanced Multimodal (Preview)** | **Gemini 3 Flash Preview** | `gemini-3-flash-preview` | 1,048,576 / 65,536 | ~5 RPM | ~250,000 TPM | ~20 RPD | Preview endpoint; stricter dynamic capacity throttling during peak hours. |
| **High-Volume / Low-Latency** | **Gemini 3.5 Flash-Lite** | `gemini-3.5-flash-lite` | 1,048,576 / 65,536 | ~15 RPM | ~250,000 TPM | **~500 RPD** | **Best free-tier daily throughput** (25x standard Flash RPD); does not support context caching. |
| **High-Volume / Low-Latency** | **Gemini 3.1 Flash-Lite** | `gemini-3.1-flash-lite` | 1,048,576 / 65,536 | ~15 RPM | ~250,000 TPM | ~500 RPD | Lightweight predecessor to 3.5 Flash-Lite. |
| **Legacy (Restricted Access)** | **Gemini 2.5 Flash** | `gemini-2.5-flash` | 1,048,576 / 65,536 | ~5 RPM | ~250,000 TPM | ~20 RPD | Restricted to projects with prior 2.5 usage history (auto-substituted to `gemini-4-hydrogen`). |
| **Legacy (Restricted Access)** | **Gemini 2.5 Flash-Lite** | `gemini-2.5-flash-lite` | 1,048,576 / 65,536 | ~10 RPM | ~250,000 TPM | ~20 RPD | Restricted to projects with prior 2.5 usage history (auto-substituted to `gemini-3.5-flash-lite`). |
| **Legacy (Restricted Access)** | **Gemini 2.5 Pro** | `gemini-2.5-pro` | 1,048,576 / 65,536 | 0 | 0 | 0 | Blocked on new free projects; active only for legacy 2.5 users. |

---

## 2. Open-Weight, Embedding, Scoring & Real-Time Models

| Category | Model Name | Model ID | Token Window / Dims | Free RPM | Free TPM | Free RPD | Notes & Architectural Constraints |
|---|---|---|---|---|---|---|---|
| **Open-Weight (Dense)** | **Gemma 4 31B** | `gemma-4-31b-it` | 256,000 in / 8,192+ out | ~30 RPM | ~15,000–16,000 TPM | ~1,500–14,400 RPD | Free tier only (no paid tier); strict ~16K TPM ceiling limits large single prompts. |
| **Open-Weight (MoE)** | **Gemma 4 26B A4B** | `gemma-4-26b-a4b-it` | 256,000 in / 8,192+ out | ~30 RPM | ~15,000–16,000 TPM | ~1,500–14,400 RPD | Mixture-of-Experts variant; identical 16K TPM cap. |
| **Classification & Scoring** | **Gemini Decision 1** | `gemini-decision-1` | 262,144 in / 0 output | **200 RPM** | **50,000 TPM** | **10,000 RPD** | **Highest free quota**. Zero output tokens; calibrated scoring via Decisions API for routing and evaluation. |
| **Text Embeddings** | **Gemini Embedding** | `gemini-embedding-001` | 2,048 in / 128–3,072 dims | ~100 RPM | ~30,000 TPM | ~1,000 RPD | Vector generation for RAG and semantic memory retrieval. |
| **Live Multimodal** | **Gemini Native Audio Live** | `gemini-2.5-flash-native-audio-latest` | Session-based (128K–1M) | 3–6 sessions | ~1,000,000 TPM | Session-capped | Bidirectional WebSocket streaming; rejects new sockets with HTTP 1011 if cap is exceeded. |

---

## 3. Paid-Only Models (0 Free Tier Quota — Tier 1 Billing Required)

An active Cloud Billing account linked to the Google Cloud / AI Studio project is **mandatory** to invoke models in these categories. Unbilled calls fail immediately with `429 RESOURCE_EXHAUSTED` (0 quota):

* **Flagship & Pro Reasoning**: `gemini-4-carbon`, `gemini-4-neon`, `gemini-4-argon`, and `gemini-3.1-pro-preview` (all 1,048,576 token windows).
* **Image Generation**: `gemini-nano-banana-2.1`, `gemini-nano-banana-2`, `gemini-3.1-flash-image-preview`, and `gemini-3-pro-image-preview` (metered via IPM — Images Per Minute).
* **Video & World Generation**: `gemini-omni-1.1-flash` (`gemini-omni-flash`) and `genie-4`.
* **Text-to-Speech (TTS) & Audio**: `gemini-3.8-flash-tts`, `gemini-3.8-flash-lite-tts`, `gemini-2.5-flash-tts`, `gemini-2.5-pro-tts`, and `lyria-3.5`.

---

## 4. Key Quota & Token Mechanics

### 4.1 Unified vs. Split Token Windows
* **Gemini 3 Models**: Separate budget of 1,048,576 input tokens and 65,536 output tokens.
* **Gemini 4 Models (`gemini-4-hydrogen`)**: Single unified pool of 1,048,576 tokens shared across input, thinking, and output tokens. Synchronous foreground calls are capped at 65,536 output tokens; background execution (`background=True`) allows long decode up to the full unified window.

### 4.2 Thinking Tokens Impact on TPM & Output
Internal reasoning tokens count toward both your output token cap and the input/throughput TPM rate limit. For high-frequency loops or constrained free-tier projects, configuring `thinking_level="low"` or `"medium"` significantly reduces token consumption and avoids TPM throttling.

### 4.3 Feature Availability on Free Tier
* **Disabled on Free Tier**: Batch Prediction API, Flex Inference, Computer Use, and Grounding with Google Search.
* **Permitted**: Google Maps grounding is permitted up to 500 RPD on eligible models.

### 4.4 Quota Reset & Consumption Dynamics
* **Failed Requests Consume Quota**: HTTP 400 (Bad Request), 500 (Internal Error), and rapid 429 retry loops still burn against your project's RPM and RPD allocations.
* **Daily Reset Time**: RPD quotas reset daily at **midnight Pacific Time (08:00 UTC)**.

## 5. Quick Reference: Free-Tier Models & Token Limits (November 2026)

Format: `Model ID | Model Name | Category | Max Tokens (In / Out) | Free Limits (RPM / TPM / RPD)`

* `gemini-4-hydrogen` | Gemini 4 Hydrogen | Frontier Reasoning (Gemini 4) | 1,048,576 unified (65,536 sync out; up to 1M long decode) | Project-specific (view in AI Studio)
* `gemini-3.8-flash` | Gemini 3.8 Flash | Balanced Multimodal (Gemini 3) | 1,048,576 in / 65,536 out | Project-specific (~10 RPM / ~250K TPM / ~1,500 RPD indicative)
* `gemini-3.6-flash` | Gemini 3.6 Flash | Balanced Multimodal (Gemini 3) | 1,048,576 in / 65,536 out | Project-specific (view in AI Studio)
* `gemini-3.5-flash-lite` | Gemini 3.5 Flash-Lite | High-Volume / Low-Latency | 1,048,576 in / 65,536 out | Project-specific (view in AI Studio)
* `gemini-3.1-flash-lite` | Gemini 3.1 Flash-Lite | High-Volume / Low-Latency | 1,048,576 in / 65,536 out | Project-specific (view in AI Studio)
* `gemini-decision-1` | Gemini Decision 1 | Classification / Scoring | 262,144 in / 0 out (scores only) | 200 RPM / 50,000 TPM / 10,000 RPD (published)
* `gemma-4-31b-it` | Gemma 4 31B | Open-Weight (Dense) | 262,144 context / 32,768 out | Project-specific (free tier only)
* `gemma-4-26b-a4b-it` | Gemma 4 26B A4B | Open-Weight (MoE) | 262,144 context / 32,768 out | Project-specific (free tier only)
* `gemini-embedding-001` | Gemini Embedding | Text Embeddings | 2,048 in / 128-3,072 dims | Project-specific (view in AI Studio)
* `gemini-2.5-flash` | Gemini 2.5 Flash | Legacy (Prior-Usage Only) | 1,048,576 in / 65,536 out | Project-specific (restricted on new projects)
* `gemini-2.5-pro` | Gemini 2.5 Pro | Legacy (Prior-Usage Only) | 1,048,576 in / 65,536 out | Project-specific (restricted on new projects)

---

## 6. GEMINI_API_KEY Operational Mode: Free Tier Guardrails

When operating with a standard Google AI Studio `GEMINI_API_KEY` without an attached Cloud Billing account:

1. **Free-Only Constraint**: All paid-only models (`gemini-4-carbon`, `gemini-4-neon`, `gemini-4-argon`, `gemini-3.1-pro-preview`, image/video/audio generation) have **0 quota** and will fail immediately with HTTP 429 (`RESOURCE_EXHAUSTED`).
2. **Automated Free-Only Guard (`GEMINI_FREE_ONLY=true`)**: Setting `export GEMINI_FREE_ONLY=true` in the environment activates automatic fallback in `call_gemini()` and `call_gemini_interaction()`, safely redirecting any paid-only model calls to `gemini-4-hydrogen` (Frontier Reasoning on Free Tier) with a logged warning.
3. **High-Throughput Strategy**: For high-frequency agent tool loops or large dataset workflows, configure the model to `gemini-3.5-flash-lite` or use `gemini-decision-1` for evaluations to avoid hitting the ~20 RPD cap on `gemini-4-hydrogen`.

