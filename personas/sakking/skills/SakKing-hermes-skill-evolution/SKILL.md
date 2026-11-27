---
name: SakKing-hermes-skill-evolution
version: 1.0.0
description: Evolve SakKing skills using DSPy and GEPA reflective optimization within the standalone self-evolution pipeline.
category: productivity
tags:
- cli
- evolution
- optimization
- runner
- skill
---

# SakKing Self-Evolution & GEPA Optimization

## Overview

SakKing leverages an automated self-evolution engine powered by **DSPy + GEPA** (Generative Error-driven Prompt Analysis). The pipeline systematically evolves skills, prompts, and tool descriptions by analyzing execution traces and optimizing text representations with zero GPU spend.

---

## 1. Engine Location & Architecture

The self-evolution engine lives directly inside `personas/sakking/evolution/` and is orchestrated via `evolve_agent.sh`:

```
personas/sakking/evolution/
├── core/               # Constraints, evaluation harnesses, and fitness metrics
├── skills/             # DSPy module wrappers and mutation operators
├── prompts/            # System prompt section parameterizers
├── code/               # Darwinian AST code evolver
└── monitor/            # Performance tracking and auto-triage ranker
```

---

## 2. Six-Stage Self-Evolution Cycle

1. **Dream** — Choose target skill (`--skill SakKing-coding-tdd`).
2. **Hope** — Define evaluation criteria and test iterations.
3. **Care** — Run GEPA reflective optimization with strict safety guardrails.
4. **Joy** — Package the winning variant as a Pull Request on GitHub.
5. **Trust** — Validate test suite (`uv run pytest tests/ -q`) and size limits ($\le 15$ KB).
6. **Growth** — Optionally apply the variant to the live profile (`--apply`).

---

## 3. Operational CLI Commands

```bash
# Dry-run validation (zero API spend, validates dataset & pipeline):
./evolve_agent.sh sakking --skill SakKing-coding-tdd --dry-run

# Run full evolution (opens a PR on beer-sakthai/sakking-skills):
./evolve_agent.sh sakking --skill SakKing-systematic-debugging --iterations 5

# Evolve and deploy directly to live profile:
./evolve_agent.sh sakking --skill SakKing-executing-plans --apply
```
