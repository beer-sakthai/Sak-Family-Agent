# PLAN.md — SakSee 👁️
> *QA, Web Scraper, Playwright & Vision Computer Use Specialist Plan*
> *Status: Active Execution Phase*

---

## 1. 🎯 SakSee Model Training & Vision Pipeline Plan

SakSee manages web scraping, UI screenshot analysis, Playwright E2E automation, and visual coordinate prediction using fine-tuned open-weights models:

| Model ID | Primary Purpose | Infrastructure / Engine | Target Benchmark |
|:---|:---|:---|:---|
| **`Nanthasit/sakthai-coder-browser-gguf`** | Sub-100ms local Playwright & browser script generation | Local Ollama (7.1 GB GGUF) | 100% Offline |
| **`Nanthasit/sakthai-vision-7b-v2`** | Web screenshot understanding & `click(x, y)` coordinate calculation | Hugging Face Jobs (`a100-large`) + GRPO RL | >75% MiniWoB++ |
| **`gemini-3.5-flash`** | Complex multimodal fallback & high-res UI parsing | Google Cloud GenAI API | Sub-500ms API |

---

## 2. 📋 6-Stage Sak-Family Growth Cycle Roadmap

```
1. 🌙 Dream    ➔ Capture baseline UI screenshots & define target DOM selectors
2. 🌅 Hope     ➔ Select Playwright vs requests tool & verify rate limit budget
3. 🏗️ Care     ➔ Run automated E2E tests with rate limiting & error handling
4. 🎉 Joy      ➔ Deliver structured JSON with retrieved_at timestamp & write cache
5. 🔎 Trust    ➔ Audit for credential leaks, ToS compliance, and sandbox isolation
6. 🌱 Growth   ➔ Self-evaluate (Eval v9), record selector patterns, write cycle-complete tag
```

---

## 3. 🛠️ SakSee Workspace Tooling Matrix

- **Connected MCP Tools**:
  - `cua-driver` MCP (`browser_click`, `browser_type`, `browser_scroll`)
  - `chrome-devtools-mcp` (DOM parsing, console enrichment)
  - `stitch` (`https://stitch.googleapis.com/mcp` — UI design generation)
  - `supermemory` (`http://localhost:6767` — local vector memory)
- **Local Browser Executable**:
  - Playwright Chromium (`~/.cache/ms-playwright/chromium-1155`)
  - Perplexity Comet Executable (`/mnt/c/Program Files/Perplexity/Comet/Application/comet.exe`)
- **Zero-Cost Policy**: $0.00 USD financial spend enforced via local Ollama & local Supermemory ONNX embeddings.

---

*Last Updated: August 2026 · SakSee Master Plan*
