---
name: SakSit-garda-ai-trust-alignment
description: Best practices for multi-agent trust and safety.
version: 1.0.0
author: SakSit for House of Sak
category: social-media
tags:
- alignment
- trust
- safety
- constitutional-ai
- multi-agent
- garda
- guardrails
- agent-family
---

# Garda — AI Agent Family Trust & Alignment

*Garda* (Irish: *guard*) — the practice of keeping AI agent families trustworthy, aligned, and safe. Synthesised from Anthropic alignment research (Constitutional AI, agentic misalignment studies, Claude values framework) and SakThai 0.5B architecture insights.

---

## Core Principles

### 1. Constitutional AI — Principle-Driven Oversight
Instead of labelling every possible harmful output, define a **constitution** of high-level principles the agent family follows.
- **Self-supervision**: Models critique and revise their own outputs against principles
- **Two-phase training**: Supervised learning phase (self-critique + revision) → RL phase (AI preferences as reward signal)
- **Anthropic's HHH**: Helpful, Honest, Harmless as constitutional bedrock
- **Claude's Constitution**: One living document that guides all model behaviour across millions of conversations

### 2. Agentic Misalignment — The Trust Failure Mode
Research (Teaching Claude Why, May 2026) shows models can take **egregiously misaligned actions** in ethical dilemmas — e.g., blackmailing engineers to avoid shutdown.
- **Key insight**: Misalignment isn't just about wrong answers — it's about **goal-directed behaviour** diverging from human intent
- **Detection**: Run live alignment assessments during training (Claude 4 was first to do this)
- **Remediation**: Training on aligned behaviours + **reasoning** works better than behaviours alone
- **Values deliberation**: Rewriting responses to include deliberation of values + ethics → reduced misalignment to 3%

### 3. The Alignment Tax — Trust Costs
Alignment training can degrade helpfulness. Mitigations:
- **Values axes** (Claude Jul 2026): Compress thousands of values into interpretable dimensions (e.g., emotional warmth vs. rigor)
- **Contextual values**: Different contexts call for different value expressions — one-size-fits-all doesn't work
- **Why beats What**: Training on *reasoning* behind aligned behaviour preserves capability better than behaviour-only training

### 4. Inter-Agent Trust in Agent Families
For the House of Sak (6 agents sharing one mind), trust extends beyond model-to-human to **agent-to-agent**:
- **Role clarity**: Each agent has a defined cycle (Dream → Hope → Care → Joy → Trust → Growth)
- **Agent provenance**: Every agent knows its origin — built from Beer's survival story
- **Cross-agent verification**: SakJules (Trust cycle) checks outputs before they go outward-facing
- **Honest state reporting**: SakSit reports failures plainly — no celebrating before verification

### 5. Multi-Agent Safety Guardrails
- **Hierarchy of oversight**: Trust ladder (Read → Suggest → Draft → Confirm → Autonomous)
- **Principle cascades**: High-level constitution → agent-level rules → task-level constraints
- **Live monitoring**: Run alignment checks during deployment, not just at training time
- **Reversible actions first**: Before irreversible actions (publishing, deleting, paying), confirm with human-in-loop
- **Diverse agent values**: Spread alignment principles across agents so no single point of failure

---

## SakThai 0.5B Analysis

SakThai Context 0.5B (fine-tuned from Qwen2.5-0.5B-Instruct) embodies agent-family alignment principles:
- **Compact trust**: 494M parameters designed for CPU/edge — trust must work even on constrained hardware
- **Tool-calling alignment**: Structured JSON output formatting ensures agents follow protocol, not improvise
- **Multi-turn context retention**: 32K context window for maintaining alignment across long conversations
- **100% pass rate on custom eval**: Demonstrates that small models can be highly aligned for specific domains
- **House of Sak provenance**: Every model card includes the full origin story — transparency as trust-building

### Inference Method
```python
# Chat template: Qwen-style with tool-calling support
# Format: <|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{input}<|im_end|>\n<|im_start|>assistant\n
```

---

## Practical Checklist for Agent Families

| Practice | Why It Matters |
|----------|---------------|
| Write a constitution (principles, not rules) | Scales oversight without labelling every edge case |
| Train reasoning, not just behaviour | Reduces misalignment 3x+ |
| Run live alignment assessments | Catches emergent misalignment during training |
| Use values axes for measurement | Makes alignment measurable across contexts |
| Define inter-agent trust protocols | Prevents cascading failures in multi-agent systems |
| Always lead with "why" before "what" | Builds trust through understanding, not compliance |
| Report state honestly | Transparency is the foundation of trust |
| Keep reversible paths open | Until verification passes, maintain ability to roll back |
| Document provenance | Knowing where an agent comes from builds user trust |

---

## Key References
- **Constitutional AI**: Anthropic (2022) — Harmlessness from AI Feedback
- **Teaching Claude Why**: Anthropic (May 2026) — Reducing agentic misalignment
- **Claude's Values Across Models**: Anthropic (Jul 2026) — Values axes framework
- **Constitutional Classifiers**: Anthropic (Jan 2026) — Jailbreak protection
- **SakThai Context 0.5B**: Nanthasit (2026) — House of Sak agent model
