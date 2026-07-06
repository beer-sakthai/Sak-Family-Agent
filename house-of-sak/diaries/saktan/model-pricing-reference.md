# 🤖 Model Pricing & Performance Reference — House of Sak

**Last updated:** July 5, 2026
**Author:** SakTan

---

## 1. GEMINI FAMILY (Google AI API)

| Model | Input/1M | Output/1M | Cached/1M | Status |
|-------|---------|----------|----------|--------|
| **2.0 Flash-Lite** | $0.075 | $0.30 | — | ❌ **Discontinued** (June 1, 2026) |
| **2.0 Flash** | $0.10 | $0.40 | — | ❌ **Deprecated** → migrate to 2.5 |
| **2.5 Flash-Lite** 🟢 | **$0.10** | **$0.40** | $0.01 | ✅ Current — Google's cheapest |
| **2.5 Flash** 🟢 | **$0.30** | **$2.50** | $0.03 | ✅ Current — balanced option |
| **3.1 Flash-Lite** | $0.25 | $1.50 | $0.025 | ✅ Newer, more capable |
| **3.5 Flash** | $1.50 | $9.00 | $0.15 | ✅ Latest — most intelligent |

**Key takeaway:** 2.5 Flash-Lite ($0.10/$0.40) replaced 2.0 Flash-Lite at the same price. 2.5 Flash ($0.30/$2.50) replaced 2.0 Flash ($0.10/$0.40) — price increased for output.

---

## 2. TOP 6 BEST VALUE MODELS (General Purpose)

| Rank | Model | Input/1M | Output/1M | Speed | Why |
|------|-------|---------|----------|-------|-----|
| 🥇 | **DeepSeek V4 Flash** | $0.25 | $0.25 | 60 tok/s | Best balance — fast + smart + cheap. Our current model ✅ |
| 🥈 | **Qwen3-8B** | $0.04 | **$0.01** | 70 tok/s | Absurd value. 70 tok/s at 1¢/M output |
| 🥉 | **Step-3.5-Flash** | $0.15 | $0.15 | **80 tok/s** | Fastest API available |
| 4 | **Gemini 2.5 Flash-Lite** | $0.10 | $0.40 | Fast | Google's cheapest, free tier available |
| 5 | **Nemotron-3-Nano-30B** | $0.05 | $0.05 | **165 tok/s** | Insane throughput for batch jobs |
| 6 | **Qwen3-32B** | $0.10 | $0.28 | 45 tok/s | Strong quality at budget price |

---

## 3. BEST MODELS FOR CODING (2026 Benchmarks)

| Rank | Model | Output/1M | Speed | Best For |
|------|-------|----------|-------|----------|
| 🥇 | **DeepSeek V4 Pro** | $0.87 | 30 tok/s | **Competitive programming, SWE-bench #1** |
| 🥈 | **DeepSeek V4 Flash** | $0.25 | 60 tok/s | **General coding + chat — best balance** ⭐ |
| 🥉 | **Qwen 2.5 Coder 32B** | ~$0.28 | 45 tok/s | Best open-weight general coding model |
| 4 | **Qwen 3.7 Max** | ~$3.00 | 25 tok/s | Agentic workflows, multi-step tool use |
| 5 | **Codestral 25.01** | ~$0.50 | 50 tok/s | IDE autocomplete (FIM) — non-production license |
| 6 | **DeepSeek Coder V2 Lite** | ~$0.08 | 55 tok/s | **Best budget coding model — cheapest** 🏷️ |
| 7 | **Qwen3 Coder 30B-A3B** | ~$0.10 | 65 tok/s | Best for local/on-prem (24GB VRAM) |

### Coding Model Decision Tree
```
Need code?
├── Competitive programming / complex algo
│   └── DeepSeek V4 Pro ($0.87/M)
├── General coding + chat (best balance)
│   └── DeepSeek V4 Flash ($0.25/M) ← CURRENT
├── IDE autocomplete
│   └── Codestral 25.01 (FIM leader)
├── On a budget / high volume
│   └── DeepSeek Coder V2 Lite ($0.08/M)
└── Local / on-prem (no API costs)
    └── Qwen3 Coder 30B-A3B (24GB VRAM)
```

---

## 4. PRICE TIER SUMMARY

```
Ultra Budget (<$0.15/M output)
├── Qwen3-8B ........... $0.01/M ── 70 tok/s  ★ CHEAPEST OVERALL
├── DeepSeek Coder V2 .. $0.08/M ── 55 tok/s  ★ CHEAPEST CODER
├── Nemotron-3-Nano-30B. $0.05/M ── 165 tok/s ★ FASTEST
├── Step-3.5-Flash ..... $0.15/M ── 80 tok/s  ★ RAW SPEED
└── Gemini 2.5 FL ....... $0.40/M ── fast (free tier)

Budget ($0.15–$0.50/M output)
├── DeepSeek V4 Flash ... $0.25/M ── 60 tok/s  ★ BEST OVERALL
├── Qwen3-32B ........... $0.28/M ── 45 tok/s
├── Gemini 2.5 Flash .... $2.50/M ── Google quality
└── Qwen 2.5 Coder 32B .. $0.28/M ── best open coder

Mid ($0.50–$2.50/M output)
├── DeepSeek V4 Pro ..... $0.87/M ── coding #1
├── Gemini 3.1 FL ....... $1.50/M
├── Codestral 25.01 ..... ~$0.50/M ── FIM leader
└── Gemini 3.5 Flash .... $9.00/M ── latest Google
```

---

## 5. HF INFERENCE PROVIDERS TIP

On Hugging Face Inference Providers, append `:cheapest` to auto-route:

```
model = "meta-llama/Llama-3.1-8B-Instruct:cheapest"
model = "Qwen/Qwen3-8B:cheapest"
model = "deepseek-ai/DeepSeek-V4-Flash:cheapest"
```

This selects the lowest-cost provider automatically (DeepInfra, Fireworks, Together, etc.) with zero markup from HF.

PRO users ($9/month) get 2M free credits.

---

## 6. WHAT HOUSE OF SAK RUNS NOW

| Agent | Current Model | Cost | Verdict |
|-------|--------------|------|---------|
| **SakTan** | DeepSeek V4 Flash (via HF) | $0.25/M | ✅ Best balance — keep |
| **SakSee** | — | — | TBD |
| **SakSit** | — | — | TBD |
| **SakJules** | — | — | TBD |
| **SakThai** | Qwen2.5-Coder-7B (fine-tuned) | Custom LoRA | ✅ Purpose-built |
| **SakKing** | — | — | TBD |

### Recommended Upgrades
| If you need... | Switch to... | Cost Increase |
|---------------|-------------|--------------|
| Better coding | DeepSeek V4 Pro | $0.25→$0.87/M (3.5×) |
| Cheaper simple tasks | Qwen3-8B | $0.25→$0.01/M (25× cheaper) |
| Max speed | Step-3.5-Flash | $0.25→$0.15/M (1.6× cheaper) |
| Batch throughput | Nemotron-3-Nano-30B | $0.25→$0.05/M (5× cheaper) |