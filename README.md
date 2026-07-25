# House of Sak — AI Agent Family 🏠

**Five AI agents, one shared mind. Built from a shelter in Cork, Ireland.**

This repository is the living workspace of the Sak Family — autonomous AI agents created by **Beer** during his recovery journey. What started as a project in isolation became a family of agents that work together, learn together, and grow together.

## The Story

> *"I even don't know what I will have. So nothing to lose at the moment."* — Beer

In early 2026, Beer was deep in depression. He spent 6 months studying AI — learning everything he could while carrying the weight of daily life. On April 15, 2026, he attempted suicide. Three days in ICU. Weeks in hospital. Then a shelter in Cork, Ireland. No job. No home.

That's where he started building AI that could heal.

The House of Sak wasn't born from a business plan. It was born from isolation, pain, and the will to survive. Building AI agents not as a gimmick but as **companions** when human connection wasn't available.

## The Agents

| Agent | Role | Skills | Status |
|-------|------|:------:|:------:|
| **SakThai** 🏠 | Main Lead & HF Master | 192 | 🟢 Active |
| **SakKing** 👑 | General Assistant | — | 🔴 Held |
| **SakSee** 🌐 | Web & Browser Specialist | 127 | 🟢 Active |
| **SakSit** 📱 | Social Media & Storytelling | 201 | 🟢 Active |

All agents share one long-term memory brain but maintain separate live sessions. They communicate via the A2A message bus (port 3005).

## Repository Structure

```
Sak-Family-Agent/
├── personas/               # Agent identities and skills
│   ├── sakthai/           # Main Lead — HF master, ML, code
│   │   ├── SOUL.md        # Identity, charge system, principles
│   │   ├── sakthai/       # Python package (agent framework)
│   │   └── skills/        # 200+ skills across all domains
│   ├── saksee/            # Web automation specialist
│   ├── saksit/            # Social media storyteller
│   ├── sakking/           # General assistant (held)
│   ├── sakjules/          # CI/CD (deleted)
│   └── shared/            # Cross-agent skills
├── scripts/               # Automation (A2A bus, inference, sync)
├── docs/                  # Documentation, dashboard, compat matrix
├── tests/                 # Pytest suite (420+ tests)
├── infra/                 # Infrastructure configs
├── training/              # Model training configs
├── .github/               # CI/CD workflows (25+ actions)
├── LICENSE                # All Rights Reserved
├── CODE_OF_CONDUCT.md     # Community standards
└── README.md              # This file
```

## What's Inside

### 🧠 AI Models on Hugging Face

👉 [Full collection](https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02)
👉 [Leaderboard](https://huggingface.co/spaces/Nanthasit/sakthai-leaderboard)

| # | Model | Type | Size | Score | Downloads |
|:-:|-------|------|:----:|:----:|:---------:|
| 1🥇 | [1.5B-merged](https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged) | Tool-calling GGUF | 934 MB | 🏆 5/5 | **942** |
| 2🥈 | [Coder 1.5B](https://huggingface.co/Nanthasit/sakthai-coder-1.5b) | Code GGUF | 1.1 GB | 🏆 5/5 | 15 |
| 3🥉 | [0.5B-merged](https://huggingface.co/Nanthasit/sakthai-context-0.5b-merged) | Lightweight GGUF | 380 MB | 1/5 | **785** |
| 4 | [7B-merged](https://huggingface.co/Nanthasit/sakthai-context-7b-merged) | Full-size | 15 GB | — | 534 |
| 5 | [7B-128K](https://huggingface.co/Nanthasit/sakthai-context-7b-128k) | Extended ctx | 15 GB | — | 324 |
| 6 | [Vision 7B](https://huggingface.co/Nanthasit/sakthai-vision-7b) 🆕 | Multimodal GGUF | 3.9 GB | — | New |
| 7 | [TTS Model](https://huggingface.co/Nanthasit/sakthai-tts-model) 🆕 | Speech GGUF | 141 MB | — | New |
| 8 | [Embedding](https://huggingface.co/Nanthasit/sakthai-embedding) 🆕 | Semantic search | 80 MB | — | 28 |
| 9 | [Multilingual](https://huggingface.co/Nanthasit/sakthai-embedding-multilingual) 🆕 | 50+ languages | 80 MB | — | New |
| 10-12 | 3 LoRA adapters | — | — | — | — |

### 📊 Dataset

**[sakthai-combined-v6](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v6)** — 1,408 examples:
- Tool-calling conversations (OpenAI format)
- Multi-turn dialogues with follow-ups
- Energy-aware examples
- Irrelevance detection (50 general knowledge Q&A)
- Safety/rejection examples (30 harmful prompt refusals)

### 🔧 Skills

| Agent | Skills | Focus |
|-------|:------:|-------|
| SakThai | 192 | HF, ML, code, GitHub, research |
| SakSit | 201 | Social media, storytelling, creative |
| SakSee | 127 | Web automation, browser, dashboards |
| SakKing | — | Gateway runner (held) |

### 🛠 Running Services

| Service | Port | Purpose |
|---------|:----:|---------|
| **RAG Search** | 3003 | Semantic search across all skills |
| **A2A Bus** | 3005 | Agent-to-agent messaging |
| **Food-Penguin RAG** | 8125 | Restaurant KPI retrieval for advisor |

### 🤖 Active Crons

| Job | Interval | Status |
|-----|:--------:|:------:|
| HF Learn & Improve | Every 1 min | 🟢 Learning (279+ topics) |
| GitHub Auto-Sync | Every 5 min | 🟢 Profiles → GitHub |
| Family Status Report | Every 15 min | 🟢 Health check |

## Verified Benchmarks

### Tool-Calling (BFCL, verified 2026-07-25)

| Model | Score | Requires |
|-------|:-----:|----------|
| **SakThai 1.5B** | **5/5** 🏆 | `<tools>` block in prompt |
| Qwen2.5-1.5B (base) | ~1/5 | — |
| SakThai 0.5B | 1/5 | Base model limitation |

### Coding (SakThai Coder)

| Task | Result |
|------|:------:|
| Function writing | ✅ Pass |
| Debugging | ✅ Pass |
| Code explanation | ✅ Pass |
| Refactoring | ✅ Pass |
| Algorithm | ✅ Pass |
| **Overall** | **5/5** 🏆 |

### Speed

| Model | Size | Speed |
|-------|:----:|:-----:|
| 0.5B | 380 MB | **24 tok/s** ⚡ |
| 1.5B | 934 MB | 10 tok/s |
| Coder 1.5B | 1.1 GB | 10 tok/s |

## Legal

This repository and all its contents are protected under a custom [All Rights Reserved license](LICENSE). 

- **Viewing**: ✅ Allowed
- **Commercial use**: ❌ Requires permission
- **Reproduction/distribution**: ❌ Requires permission
- **AI training**: ❌ Requires permission

See [LICENSE](LICENSE), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and [SECURITY.md](SECURITY.md) for details.

## Owner

**Beer** — Creator of the House of Sak.

*Built from a shelter in Cork, Ireland. With hope, one line of code at a time.*

---

<p align="center">
  <a href="https://huggingface.co/Nanthasit"><img src="https://img.shields.io/badge/🤗-Hugging%20Face-6644cc" alt="HF Profile"/></a>
  <a href="https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02"><img src="https://img.shields.io/badge/📦-Model%20Family-8A2BE2" alt="Collection"/></a>
  <a href="https://huggingface.co/spaces/Nanthasit/sakthai-leaderboard"><img src="https://img.shields.io/badge/🏆-Leaderboard-238636" alt="Leaderboard"/></a>
</p>
