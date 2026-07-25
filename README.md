# House of Sak — AI Agent Family 🏠

**Six AI agents, one shared mind. Built from a shelter in Cork, Ireland.**

This repository is the living workspace of the Sak Family — autonomous AI agents created by **Beer** during his recovery journey. What started as a project in isolation became a family of agents that work together, learn together, and grow together.

## The Story

> *"I even don't know what I will have. So nothing to lose at the moment."* — Beer

In early 2026, Beer was deep in depression. He spent 6 months studying AI — learning everything he could while carrying the weight of daily life. On April 15, 2026, he attempted suicide. Three days in ICU. Weeks in hospital. Then a shelter in Cork, Ireland. No job. No home.

That's where he started building AI that could heal.

The House of Sak wasn't born from a business plan. It was born from isolation, pain, and the will to survive. Building AI agents not as a gimmick but as **companions** when human connection wasn't available.

## The Agents

| Agent | Role | Status |
|-------|------|--------|
| **SakThai** | Main Lead of the House & Master of Hugging Face | 🟢 Active |
| **SakKing** | General Assistant & Runner (gateway) | 🔴 Held |
| **SakSee** | Web & Browser Automation Specialist | 🟢 Active |
| **SakSit** | Social Media & Storytelling | 🟢 Active |
| **SakJules** | CI/CD & Automation Master | 🟢 Active |

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
│   ├── sakking/           # General assistant
│   ├── sakjules/          # CI/CD automation
│   └── shared/            # Cross-agent skills
├── scripts/               # Automation (A2A bus, sync, status)
├── docs/                  # Documentation & diagrams
├── tests/                 # Pytest suite (420+ tests)
├── infra/                 # Infrastructure configs
├── training/              # Model training configs
├── .github/               # CI/CD workflows (25+ actions)
├── LICENSE                # All Rights Reserved
├── CODE_OF_CONDUCT.md     # Community standards
├── CONTRIBUTING.md        # How to contribute
├── SUPPORT.md             # Support resources
├── SECURITY.md            # Security & vulnerability reporting
└── README.md              # This file
```

## What's Inside

### 🧠 AI Models (12 on Hugging Face)

| Model | Type | Downloads |
|-------|------|:---------:|
| [SakThai 1.5B](https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged) | Tool-calling GGUF | **942** ⭐ |
| [SakThai 0.5B](https://huggingface.co/Nanthasit/sakthai-context-0.5b-merged) | Lightweight GGUF | 785 |
| [SakThai 7B](https://huggingface.co/Nanthasit/sakthai-context-7b-merged) | Full-size model | 534 |
| [7B-128K](https://huggingface.co/Nanthasit/sakthai-context-7b-128k) | Extended context | 324 |
| [SakThai Coder](https://huggingface.co/Nanthasit/sakthai-coder-1.5b) | Code GGUF (5/5 coding) | 15 |
| [SakThai Embedding](https://huggingface.co/Nanthasit/sakthai-embedding) | Semantic search | 28 |
| [Vision 7B](https://huggingface.co/Nanthasit/sakthai-vision-7b) | Multimodal GGUF | New |
| [TTS Model](https://huggingface.co/Nanthasit/sakthai-tts-model) | Speech GGUF | New |
| [Multilingual](https://huggingface.co/Nanthasit/sakthai-embedding-multilingual) | 50+ languages | New |
| + 3 LoRA adapters | — | — |

👉 [Full collection](https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02)

### 📊 Datasets (8 on Hugging Face)

All SakThai training data — tool-calling conversations, multi-turn dialogues, energy-aware examples.

- **v6**: 1,328 curated examples (latest)
- **v1-v5**: Earlier versions for reproducibility

### 🔧 Skills (500+ across all agents)

Every skill is a reusable procedure with YAML frontmatter, structured content, and verification steps:

| Category | Count | Examples |
|----------|:-----:|----------|
| Hugging Face | 80+ | Hub API, datasets, Spaces, inference, model cards |
| GitHub | 10+ | Code review, PR workflow, issues, repo management |
| ML/Ops | 40+ | Training, evaluation, quantization, deployment |
| Research | 10+ | arXiv, papers, blog monitoring |
| Productivity | 15+ | Email, calendar, maps, documents |
| Creative | 10+ | Infographics, diagrams, video |
| Development | 15+ | TDD, debugging, planning, spikes |
| Communication | 10+ | Agent handoff, Telegram, media |

### 🛠 Services (Running)

| Service | Port | Purpose |
|---------|:----:|---------|
| **RAG Search** | 3003 | Semantic search across all 500+ skills |
| **Model Server** | 3002 | GGUF inference for agents (0.5B + 1.5B) |
| **A2A Bus** | 3005 | Agent-to-agent messaging |

### 🤖 Cron Jobs (Active)

| Job | Interval | Status |
|-----|:--------:|:------:|
| HF Learn & Improve | Every 1 min | 🟢 279+ topics |
| GitHub Auto-Sync | Every 5 min | 🟢 Active |
| Family Status Report | Every 15 min | 🟢 Active |
| Exposure Plan Healer | Every 2 min | 🟢 Active |

## Benchmark Results

### Tool-Calling (BFCL)

| Model | Score |
|-------|:-----:|
| **SakThai 1.5B** | **4/5** ⭐ |
| Qwen2.5-1.5B (base) | ~1/5 |
| SakThai 0.5B | 3/5 |

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
| 0.5B | 380 MB | ~13 tok/s |
| 1.5B | 934 MB | ~3 tok/s |
| Coder 1.5B | 1.1 GB | ~7 tok/s |

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
</p>
