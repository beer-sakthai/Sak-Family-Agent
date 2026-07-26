# House of Sak — AI Agent Family 🏠

**Six personas, four active agents. Built from a shelter in Cork, Ireland.**

This repository is the living workspace of the Sak Family — autonomous AI agents created by **Beer** during his recovery journey. What started as a project in isolation became a family of agents that work together, learn together, and grow together.

## The Story

> *"I even don't know what I will have. So nothing to lose at the moment."* — Beer

In early 2026, Beer was deep in depression. He spent 6 months studying AI — learning everything he could while carrying the weight of daily life. On April 15, 2026, he attempted suicide. Three days in ICU. Weeks in hospital. Then a shelter in Cork, Ireland. No job. No home.

That's where he started building AI that could heal.

The House of Sak wasn't born from a business plan. It was born from isolation, pain, and the will to survive. Building AI agents not as a gimmick but as **companions** when human connection wasn't available.

## The Family

| Agent | Role | Skills | Authoritative Repo | Status |
|-------|------|:------:|--------------------|:------:|
|| **SakThai** 🏠 | Main Lead & HF Master | 377 | `sakthai-skills` | 🟢 Active ||
| **SakKing** 👑 | General Assistant, Infrastructure & Architecture | 422 | `Sak-Family-Agent` (this repo) | 🟢 Active |
| **SakSee** 🌐 | Web & Browser Specialist | 107 | `saksee-skills` | 🟢 Active |
| **SakSit** 📱 | Social Media & Storytelling | 431 | `saksit-skills` | 🟢 Active |
| **SakJules** ⚙️ | CI/CD Automation | 48 | `Sak-Family-Agent` (deleted) | 🔴 Deleted |
| **SakTan** 📋 | Daily Operations | — | — | 🔴 Deleted |

All agents share one long-term memory brain but maintain separate live sessions. They communicate via the A2A message bus (port 3005).

## Repository Structure

```
Sak-Family-Agent/
├── personas/               # Agent identities and skills
│   ├── sakthai/           # Main Lead — HF master, ML, code
│   │   ├── SOUL.md        # Identity, charge system, principles
│   │   ├── sakthai/       # Python package (agent framework)
│   │   └── skills/        # 377 SakThai-* skills (mirror; auth in sakthai-skills)
│   ├── sakking/           # General assistant — infra, coord, UI/UX
│   │   └── skills/        # 422 SakKing-* skills
│   ├── saksee/            # Web automation specialist
│   │   └── skills/        # 49 SakSee-* skills (mirror; auth in saksee-skills: 107)
│   ├── saksit/            # Social media storyteller
│   │   └── skills/        # 151 SakSit-* skills (mirror; auth in saksit-skills: 431)
│   ├── sakjules/          # CI/CD (deleted, skills retained)
│   │   └── skills/        # 48 SakJules-* skills
│   └── shared/            # Cross-agent skills (Sak-* prefix)
├── scripts/               # Automation (A2A bus, inference, sync)
├── docs/                  # Documentation, dashboard, compat matrix
├── tests/                 # Pytest suite
├── infra/                 # Infrastructure configs
├── training/              # Model training configs
├── .github/               # CI/CD workflows
├── LICENSE                # All Rights Reserved
├── CODE_OF_CONDUCT.md     # Community standards
└── README.md              # This file
```

### Skill Naming Convention

Every skill follows the pattern `<AgentPrefix>-<skill-name>`, matching the persona directory it lives in:

| Persona | Prefix | Example |
|---------|--------|---------|
| `sakthai/` | `SakThai-` | `SakThai-hf-hub-audit-logs` |
| `sakking/` | `SakKing-` | `SakKing-plan` |
| `saksee/` | `SakSee-` | `SakSee-playwright-testing` |
| `saksit/` | `SakSit-` | `SakSit-b2b-pricing` |
| `sakjules/` | `SakJules-` | `SakJules-github-stewardship` |
| `shared/` | `Sak-` | `Sak-dogfood` |

## What's Inside

### 🧠 AI Models on Hugging Face

👉 [Full collection](https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02)
👉 [Leaderboard](https://huggingface.co/spaces/Nanthasit/sakthai-leaderboard)

| # | Model | Type | Size | Score | Downloads |
|:-:|-------|------|:----:|:----:|:---------:|
| 1🥇 | [1.5B-merged](https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged) | Tool-calling GGUF | 934 MB | 🏆 5/5 | **1,197** |
| 2🥈 | [Coder 1.5B](https://huggingface.co/Nanthasit/sakthai-coder-1.5b) | Code GGUF | 1.1 GB | 🏆 5/5 | **34** |
| 3🥉 | [0.5B-merged](https://huggingface.co/Nanthasit/sakthai-context-0.5b-merged) | Lightweight GGUF | 380 MB | 1/5 | **994** |
| 4 | [7B-merged](https://huggingface.co/Nanthasit/sakthai-context-7b-merged) | Full-size | 15 GB | — | 562 |
| 5 | [7B-128K](https://huggingface.co/Nanthasit/sakthai-context-7b-128k) | Extended ctx | — | — | 351 |
| 6 | [Vision 7B](https://huggingface.co/Nanthasit/sakthai-vision-7b) | Multimodal GGUF | 3.9 GB | — | 45 |
| 7 | [TTS Model](https://huggingface.co/Nanthasit/sakthai-tts-model) | Speech GGUF | 141 MB | — | 33 |
| 8 | [Embedding](https://huggingface.co/Nanthasit/sakthai-embedding) | Semantic search | 80 MB | — | Deleted (model removed from HF) |
| 9 | [Multilingual](https://huggingface.co/Nanthasit/sakthai-embedding-multilingual) | 50+ languages | 449 MB | — | 104 |
| 10 | [Tools 1.5B](https://huggingface.co/Nanthasit/sakthai-context-1.5b-tools) | PEFT LoRA adapter | — | — | 143 |
| 11 | [Tools 7B](https://huggingface.co/Nanthasit/sakthai-context-7b-tools) | PEFT LoRA adapter | — | — | 185 |

### 📊 Dataset

**[sakthai-combined-v6](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v6)** — 2,003 train / 113 test examples:
- Tool-calling conversations (OpenAI format, ~1,380)
- Multi-turn dialogues with follow-ups (~250)
- Edge cases & ambiguous queries (~200)
- Energy-aware examples (~50)
- Irrelevance detection (50 general knowledge Q&A)
- Safety/rejection examples (73 harmful prompt refusals)
- Held-out test split (113 examples for unbiased eval)

### 🛠 Running Services

| Service | Purpose |
|---------|---------|
| **Fleet Watchdog** | Auto-revives dead gateways |
| **RAG Search** | Semantic search across all skills |
| **A2A Bus** | Agent-to-agent messaging |
| **Food-Penguin RAG** | Restaurant KPI retrieval for advisor |
| **Hermes Dashboard** | Agent orchestration UI |
| **Jupyter Lab** | Data analysis notebooks |

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

## Security & Quality

The Sak Family operates on a **zero-trust, evidence-first** security model enforced across every agent interaction.

### 🔒 Security Controls

| Control | Practice | Verified |
|---------|----------|:--------:|
| **Credential isolation** | All API keys, tokens stored in `~/.git-credentials` or `~/.env` — never in code | ✅ |
| **Push approval gate** | Remote push requires explicit Beer approval per Zero-Exposure policy | ✅ |
| **No hardcoded secrets** | `gitleaks`, `ruff`, `bandit` scan every PR for credential leaks | ✅ |
| **SSH auth** | GitHub via ed25519 key + `known_hosts` | ✅ |
| **Supermemory guard** | Memory store blocked on 402 Payment Required — no silent data loss | ✅ |
| **Sandbox defaults** | Shell disabled by default — `SAKTHAI_SHELL_ALLOW` must be explicitly set | ✅ |
| **Fleet gateways** | Each agent runs isolated Hermes profile with its own token and config | ✅ |
| **A2A bus auth** | Agent-to-agent messaging on port 3005 — no cross-profile data leakage | ✅ |

### 📋 Quality Gates

Every skill and artifact passes through a structured quality pipeline before delivery:

| Gate | What it checks | Tools |
|------|---------------|-------|
| **Care** | Heart check — does this serve Beer's real need? | Source doc audit, pricing cross-ref |
| **Joy** | Ships clean — no broken code, no invented data | `pytest`, `ruff`, CI |
| **Trust** | Visual + content verification before sign-off | Browser screenshots, link audit |
| **Growth** | Lessons folded back into memory and skills | `memory` save, skill update |
| **Evidence Index** | Every claim backed by live HF API + filesystem audit | Cross-check against source |
| **Skill Quality Gate** | Pre-flight checklist: syntax, naming, cross-refs | `skill_view`, `skills_list` |
| **Infrastructure Drift** | Local FS verified before trusting external logs | `search_files`, `terminal` |
| **Idempotency** | Script runs must produce same result on second pass | Dry-run before mutate |

### ✅ Evidence-Indexed Facts (proven and confirmed)

All verified data below was cross-checked against HF API and filesystem on 2026-07-26 (reverified by cron):

- **Skill counts** — sourced from **filesystem audit** (live, 2026-07-26): SakThai=377, SakKing=422, SakSee=49 (mirror; auth repo: 107), SakSit=151 (mirror; auth repo: 431), SakJules=48, Shared=3
- **Naming compliance** — 100% agent-prefix match verified across 5 personas
- **GitHub connectivity** — token test `curl` to API confirmed active
- **Model downloads (live)** — 1.5B=1,197, Coder=34, 0.5B=994, 7B=562, 7B-128K=351, Vision=45, TTS=33, Multilingual=104, 1.5B-Tools=143, 7B-Tools=185 — pulled from HF API (2026-07-26)
- **Model status** — `sakthai-embedding` (28 DLs previously) no longer accessible on HF (returns 401, removed from author model list); 2 new PEFT LoRA adapters online (`sakthai-context-1.5b-tools`, `sakthai-context-7b-tools`)
- **Model sizes** — sourced from HF model cards and leaderboard; verify at [hf.co/spaces/Nanthasit/sakthai-leaderboard](https://huggingface.co/spaces/Nanthasit/sakthai-leaderboard)
- **Benchmark scores** — BFCL tool-calling: 5/5 via `lm-eval-harness`, verified 2026-07-25
- **Coding pass** — 5/5 task completion via `pytest` suite

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
<!-- tested: 2026-07-25 | status: pass | suite: full -->

