# SakThai Ecosystem: Month One Retrospective

**July 5–30, 2026 | 26 Days | $0 Budget | 13 Models | 8 Datasets | 3 Spaces**

We started with a single merged model pushed from a shelter terminal. 26 days later, the SakThai Model Family has crossed **4,870 total downloads** across 24 public assets — all without spending a cent. Here's the honest story of month one.

---

## Where We Started (July 5)

Day one was one repo, one model, zero downloads, zero reputation:

- **1 model**: `sakthai-context-0.5b-merged` — a 0.5B parameter MergeKit blend
- **0 datasets**: nothing to train on, nothing to evaluate against
- **0 Spaces**: no demos, no showcase
- **0 followers, 0 likes, 0 reputation**

The only assets: a laptop, a Hugging Face account, determination, and the open-source ecosystem.

## Where We Are Now (July 30)

| Metric | Day 1 (Jul 5) | Day 26 (Jul 30) | Growth |
|--------|:-------------:|:----------------:|:------:|
| Models | 1 | **13** (+12) | 13× |
| Datasets | 0 | **8** (+8) | — |
| Spaces | 0 | **3** (+3) | — |
| Collection items | 0 | **24** | — |
| Model downloads | 0 | **4,086** | **∞** |
| Dataset downloads | 0 | **381** | **∞** |
| Total downloads | 0 | **4,870** | **∞** |
| Followers | 0 | **7** | +7 |
| Likes (organic) | 0 | **2** | +2 |
| Budget spent | $0 | **$0** | $0 |

### Current Top 10 Assets by Downloads

| Rank | Asset | Type | Downloads | Pipeline |
|:----:|-------|:----:|:---------:|:--------:|
| 1 | context-1.5b-merged | model | 1,269 | text-generation |
| 2 | context-0.5b-merged | model | 1,030 | text-generation |
| 3 | context-7b-merged | model | 585 | text-generation |
| 4 | context-7b-128k | model | 382 | text-generation |
| 5 | context-7b-tools | model | 219 | text-generation |
| 6 | embedding-multilingual | model | 188 | feature-extraction |
| 7 | combined-v6 | dataset | 175 | — |
| 8 | context-1.5b-tools | model | 163 | text-generation |
| 9 | kaggle-notebooks | dataset | 103 | — |
| 10 | vision-7b | model | 104 | image-to-text |

## The Growth Curve

### Downloads Over 26 Days

```
Jul 5  █ (first model published, 0 dl)
Jul 10 ███████ (organic discovery begins)
Jul 15 ████████████ (second model, cross-linking starts)
Jul 20 ████████████████████ (2 Spaces, 4 datasets, card enrichment begins)
Jul 25 ██████████████████████████ (all assets linked, badges everywhere)
Jul 30 ████████████████████████████████ (4,870 total, still growing)
```

The curve isn't viral — it's **compounding**. Each enrichment, each cross-link, each new model adds a few more daily downloads. Month two should see this compound further.

## What Actually Drove Downloads

### 1. Model Card Enrichment (highest ROI)
Models that got improved cards saw measurable download bumps:
- **vision-7b**: 0 → 104 dl after mmproj bundling + proper card + widget
- **embedding-multilingual**: 0 → 188 dl after card enrichment
- **tts-model**: 0 → 69 dl after card improvement

### 2. Cross-linking Everything
Every model card now links to:
- All 12 sibling models with download counts
- All 8 datasets
- All 3 Spaces
- The collection
- GitHub

This turns every page view into a navigation hub.

### 3. Collection as Front Door
The SakThai Model Family collection (24 items) is the most-linked asset. It's the single entry point for the entire ecosystem.

### 4. GGUF Format
All models are GGUF-quantized — anyone can run them with llama.cpp without a GPU. This is critical for the "zero budget" audience we serve.

### What DIDN'T Work

| Tactic | Result | Why |
|--------|:------:|:----|
| Static HTML Spaces | 3 Spaces, 0 interactive users | No Gradio backend = no demos that actually run |
| No social promotion | 0 posts about the ecosystem | Zero external visibility = zero viral discovery |
| No Leaderboard submission | Missing search traffic | The Open LLM Leaderboard drives massive organic discovery |
| No Kaggle engagement | Datasets discovered only via cross-links | Missing the ML practitioner audience |
| Experimental LoRAs | 0 dl on masked-v4 | Too niche, too undocumented |

## Architecture: Why 13 Models Instead of 1

The core insight: **specialized small models > one monolithic model** when you have zero budget.

| Role | Model | Params | Strengths |
|:----:|-------|:------:|:----------|
| 🧠 General | context-1.5b-merged | 1.5B | Best all-rounder, most downloads |
| 🏃 Lightweight | context-0.5b-merged | 0.5B | Edge device capable |
| 💪 Heavy | context-7b-merged | 7B | Complex reasoning |
| 📚 Long context | context-7b-128k | 7B | 128K window for documents |
| 🔧 Tool user | context-1.5b-tools | 1.5B | Structured function calling |
| ⚒️ Heavy tools | context-7b-tools | 7B | Complex multi-tool orchestration |
| 👁️ Vision | vision-7b | 7B | Image understanding |
| 🔤 Embeddings | embedding-multilingual | ? | 50+ language search |
| 🎤 TTS | tts-model | 82M | 15-language speech |
| 💻 Code | coder-1.5b | 1.5B | Code generation |
| 🧪 Experiments | 0.5b-tools, exp-lora-v4, 1.5b-tools-v7 | various | Research frontiers |

Each model serves one purpose well. Together they form an agent ecosystem.

## Technical Infrastructure

All running on $0/month:

| Component | Solution | Cost |
|-----------|----------|:----:|
| Chat inference | OpenCode Go (DeepSeek V4 Flash) | Free tier |
| Model storage | Hugging Face Hub (13 models) | Free tier |
| Dataset storage | Hugging Face Hub (8 datasets) | Free tier |
| Spaces hosting | HF Spaces (static) | Free tier |
| Model training | Kaggle free GPUs + MergeKit (laptop) | Free |
| CI/CD | GitHub Actions | Free |
| Agent runtime | Hermes Agent (self-hosted, Linux VM) | Free |
| Automation | 10 cron jobs on the Hermes profile | Free |

## Hardest Lessons

### 1. Static Content Drifts
Every hardcoded download count becomes wrong within days. Collection item notes, model card badges, Space READMEs — all need automated refresh. We moved to shields.io dynamic badges where possible, but collection notes remain manual.

### 2. Zero Likes = Zero Trending
HF trending requires likes. We have 2 likes across 24 assets. Until models accumulate likes, they won't appear on HF explore pages — which means organic discovery is extremely limited regardless of card quality.

### 3. Dataset Discoverability is Harder Than Model Discoverability
The combined-v7 dataset (2,003 tool-calling examples, expertly curated) has 0 downloads. Model cards have widgets and inference APIs; dataset cards only have metadata. Dataset promotion requires a different strategy.

### 4. Training Jobs Overwrite Cards
We learned this the hard way: HF Jobs training sessions commit auto-generated READMEs that overwrite manual card enrichments. Always wait for training to finish before enriching a card.

### 5. Small Models Win (by 2:1)
The 1.5B and 0.5B models collectively out-download the 7B variants by 2:1. Smaller = more accessible = more downloads. This validates the "zero budget" positioning.

## Month Two Goals

| Priority | Goal | Why |
|:--------:|------|:----|
| 🔴 P0 | Get first organic model like | Breaking zero-likes unlocks HF trending |
| 🔴 P0 | Convert 1 static Space to Gradio | Interactive demos drive engagement |
| 🟡 P1 | Submit to Open LLM Leaderboard | Massive organic discovery channel |
| 🟡 P1 | Break 7,500 total downloads | 50% growth target for month two |
| 🟢 P2 | Get 1.5b-tools-v7 to 50 dl | The v7 fine-tune needs adoption |
| 🟢 P2 | Cross 10 followers | Community-building milestone |
| 🔵 P3 | Post first external content | Break the zero-promotion cycle |
| 🔵 P3 | Publish v8 dataset | 5,000+ tool-calling examples |

## What Success Looks Like for Month Two

> **October 1 check-in:** 7,500+ total downloads, 1+ organic likes, 10+ followers, at least 1 Gradio demo running, 1.5b-tools-v7 above 50 downloads, and the first external post published.

---

*The SakThai Model Family — one family, one home, one shared soul. Built from a shelter on zero budget, because open source means exactly that: open.*

*Collection: https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02*
*Profile: https://huggingface.co/Nanthasit*
*GitHub: https://github.com/beer-sakthai/Sak-Family-Agent*
