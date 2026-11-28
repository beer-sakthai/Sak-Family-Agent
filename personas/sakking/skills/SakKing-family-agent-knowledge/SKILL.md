---
name: SakKing-family-agent-knowledge
version: 1.0.0
description: Monorepo navigation, architectural knowledge, persona roles, and setup guidelines for Sak-Family-Agent.
category: productivity
tags:
- agent
- cli
- family
- knowledge
- runner
---

# SakKing Family Agent Knowledge Protocol

## Overview

Provides repository navigation, architectural context, persona specialization rules, and operational guidelines for the **Sak-Family-Agent** monorepo (`beer-sakthai/Sak-Family-Agent`).

Operated by **SakKing** (`@sakking_agent_bot`), Deputy 1 and General Assistant/Runner of the House of Sak.

---

## 1. Principles for Answering Model Capability Inquiries

When evaluating what a SakThai or family model can do:
1. **Check HF First**: Inspect live repository metadata on Hugging Face (`huggingface.co/Nanthasit`). Never answer from memory alone.
2. **Verify `pipeline_tag`**:
   - `text-generation`: Text-only LLM.
   - `image-text-to-text`: Multimodal vision-language (reads images, does not generate them).
   - `text-to-speech`: Audio generation.
3. **Inspect Architecture & Quantization**: Check `config.json` for base model (Qwen, LLaVA, Kokoro) and file formats (GGUF, safetensors).
4. **Identify Active Persona**: Distinguish the 6 family members and direct domain inquiries to the designated specialist.

---

## 2. Invariant Operating Constraints

| Rule | Requirement |
|:---|:---|
| **Coverage Floor** | Maintain $\ge 96\%$ test coverage floor across all core changes (`--cov-fail-under=96`). |
| **Package Parity** | Maintain 100% byte-for-byte identity across all 6 persona package copies (`scripts/sync_personas.py`). |
| **No Auto-Merge** | Never auto-merge PRs (`gh pr merge` or `--auto`); leave open for Beer's review. |
| **Zero Financial Spend** | Maintain strict $0.00 USD API spend policy across standard loops. |

---

## 3. Reference Documents

For detailed command tables, monorepo directory trees, and model discovery logs:
- [Monorepo Architecture & Commands Reference](./references/monorepo_architecture_and_commands.md)
- [Nano Banana Discovery Log](./references/nano-banana-discovery.md)
