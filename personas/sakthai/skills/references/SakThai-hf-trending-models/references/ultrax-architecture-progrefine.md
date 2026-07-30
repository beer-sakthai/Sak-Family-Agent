# UltraX: Function-Calling Programmatic Data Refinement

**Model:** `openbmb/UltraX-0.6B-Preview`
**Paper:** https://arxiv.org/abs/2607.08646
**Tags:** data-refinement, function-calling, programmatic-editing, pretraining
**Pipeline:** text-generation
**License:** Apache-2.0
**Params:** 0.6B
**Context:** 20,480 tokens

## What It Is

UltraX is NOT a chatbot or generation model — it's a **pretraining data refinement model** that predicts structured editing function calls to clean web-crawled text. Instead of end-to-end LLM rewriting (expensive/unreliable at scale) or rule-based filters (rigid), UltraX trains a lightweight 0.6B SFT model to output a sequence of atomic editing operations that are deterministically executed on the original document.

## Architecture

- **Base:** Standard causal language model (0.6B params, bfloat16)
- **Training:** Full-parameter SFT via ms-swift + DeepSpeed ZeRO3, 8x GPU
- **Decoding:** Predicts function calls per line — NOT free-text generation
- **Inference:** Sliding-window prediction → global operation aggregation → systematic post-processing

### Function Space (5 Operations)

| Function | Purpose |
|----------|---------|
| `keep_all()` | Document is clean, no changes needed |
| `remove_all()` | Document is valueless (error pages, SEO spam, gibberish) |
| `remove_lines(start, end)` | Delete a range of lines |
| `replace_str(line, old, new)` | Replace a substring within a specific line |
| `add_line(base, sub_idx, content)` | Insert a new line near a base position |

The **completion of the editing function space** (adding `add_line` on top of deletion + modification) is a key innovation — prior work (ProX) only supported removal and replacement, so it couldn't handle concatenated content or restructure lines.

### LAM + DCR Pipeline

1. **Dataset-Adaptive Prompt Optimization** — guides an expert LLM to produce high-quality refined texts tailored to each dataset
2. **Line Alignment and Mapping (LAM)** — aligns raw and refined texts at line level
3. **Dynamic Context Replacement (DCR)** — converts character-level edits into reliable `replace_str` calls with unique context anchoring
4. **Low-Confidence Filtering** — removes noisy supervision
5. **Ratio-Controlled Sampling** — balances operation combinations in the training distribution

## Benchmarks

Trained on FineWeb (20B tokens) → evaluated zero-shot on a 1B MiniCPM across 10 benchmarks:

| Metric | Raw | ProX-C | UltraX |
|--------|-----|--------|--------|
| Average | 45.08 | 45.05 | **46.14** |
| #Wins (out of 10) | 0 | 0 | **10** |

UltraX wins on **all 10 benchmarks** (ARC-C, ARC-E, CSQA, HellaSwag, MMLU, OBQA, PIQA, SIQA, WinoGrande, SciQ). At the 16B-token checkpoint it already reaches 45.5 avg vs raw's 44.3 at 20B — demonstrating **stronger data efficiency**.

**Human evaluation** (100 samples × 6 judges):
- UltraX: **9.60/10** (σ=0.85)
- ProX-C: **9.17/10** (σ=1.57)
- Noise edits: 0.38% vs 2.59%
- Overall win rate vs ProX-C: 22.90% UltraX better, 65.30% tie, 11.80% ProX-C better

**Qualitative wins:**
- Preserves product specifications that ProX-C deletes
- Restores concatenated form fields via `add_line` calls (12 insertions)
- Correctly identifies gibberish/SEO spam and calls `remove_all()`
- Decomposes concatenated news feeds into individual paragraphs
- Preserves event metadata (speaker, venue, date) while removing registration URLs

## Usage Pattern

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("openbmb/UltraX-0.6B-Preview")
tokenizer = AutoTokenizer.from_pretrained("openbmb/UltraX-0.6B-Preview")
```

Input format: text with line-number markers (`<lid:N>` prefix per line) + system instruction.
Output format: one function call per line (e.g., `remove_lines(1, 3)\nreplace_str(5, 'old', '')\n`).

## Why It Matters for Trends

UltraX represents a shift in the pretraining data pipeline — from "collect more data" to "refine existing data programmatically." The 0.6B size means it's deployable on a single GPU for batch processing. Combined with the `openbmb/UltraX-Preview` dataset (on HF Datasets), it forms a complete data refinement pipeline. The approach generalizes across corpora (FineWeb, RedPajama-v2, AICC, Ultra-FineWeb) with consistent gains.
