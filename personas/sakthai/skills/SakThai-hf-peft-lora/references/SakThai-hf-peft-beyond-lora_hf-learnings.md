# HF PEFT Beyond LoRA — Advanced Methods & Benchmarking Deep-Dive

## Overview

LoRA dominates PEFT usage — **98.4%** of model cards on the HF Hub that mention exactly one PEFT technique reference LoRA. On image generation platforms, **95.0%** of PEFT checkpoints are LoRAs. On GitHub code searches, **71.3%** of `from peft import <CONFIG>` results are LoRA.

This dominance is self-reinforcing: LoRA has the most tutorials, the broadest downstream support (vLLM, llama.cpp, Diffusers), and the highest visibility. But researchers continuously claim their techniques beat LoRA — and the PEFT library now includes **40+ distinct PEFT techniques** with a unified API.

The HF PEFT team built a **standardized benchmark** (same base model, dataset, training code, hardware) to compare all methods on equal footing across:
- **Test performance** (accuracy / similarity)
- **Peak VRAM usage**
- **Runtime**
- **Checkpoint size**
- **Forgetting/drift**

## The Pareto Frontier Analysis

Instead of declaring a single "best" method, the benchmark plots tradeoffs. A method is on the **Pareto Frontier** if no other method simultaneously beats it on both metrics (e.g., test accuracy AND memory).

### LLM Math Benchmark (MetaMathQA → GSM8K, Llama-3.2-3B)

| Method | Test Accuracy | Peak VRAM | On Pareto Frontier |
|--------|:------------:|:---------:|:-----------------:|
| **LoRA (default)** | 48.1% | 22.5 GB | ❌ |
| **rs-LoRA** (rank-stabilized init) | **53.2%** | 22.6 GB | ✅ |
| **LoRA-FA** (frozen A matrix) | 32.9% | **20.2 GB** | ✅ |
| **OFT** | 36.5% | 21.8 GB | ❌ |
| **BEFT** | 32.9% | **20.2 GB** | ✅ |
| **Lily** | **54.9%** | 25.6 GB | ✅ |
| **BOFT** | 48.0% | 23.1 GB | ❌ |
| **LoKr** | 48.7% | 22.0 GB | ❌ |

**Key finding:** Default LoRA (48.1%, 22.5 GB) is NOT on the Pareto frontier. Use **rs-LoRA** for better accuracy, **LoRA-FA** or **BEFT** for lower memory.

### Image Generation Benchmark (FLUX.2-klein-base-4B, cat plushy concept)

| Method | DINO Similarity | Peak VRAM | On Pareto Frontier |
|--------|:--------------:|:---------:|:-----------------:|
| **LoRA** | 0.697 | 9.97 GB | ❌ |
| **OFT** | **0.708** | **9.01 GB** | ✅ (dominates LoRA) |
| **GraLoRA** | 0.702 | 9.52 GB | ✅ |
| **VeRA** | 0.618 | 8.89 GB | ❌ |
| **LoHa** | 0.601 | 9.52 GB | ❌ |
| **DoRA** | 0.688 | 9.98 GB | ❌ |

**Key finding:** LoRA is strictly dominated by **OFT** (better score AND lower memory). GraLoRA also beats LoRA on both axes.

## Advanced PEFT Techniques Catalog

### OFT (Orthogonal Fine-Tuning)
- **Paper:** Qiyu Li et al., "Controlling Text-to-Image Diffusion by Orthogonal Finetuning" (NeurIPS 2023)
- **Mechanism:** Reparameterizes pretrained weight matrices with orthogonal matrices, preserving hyperspherical energy (cosine similarity between neurons)
- **Key advantage:** Preserves pretrained model's generative performance during fine-tuning — better subject preservation and controllable generation
- **Variant:** OFTv2 with block-diagonal structure for parameter efficiency
- **Best for:** Image generation / diffusion models where subject preservation matters
- **Adapter conversion:** OFT adapters can be converted to LoRA format

### BOFT (Bayesian Orthogonal Fine-Tuning)
- **Mechanism:** Extends OFT with Bayesian formulation for the orthogonal constraint
- **Key advantage:** Better regularization, prevents overfitting on small datasets

### BEFT (Budget-Efficient Fine-Tuning)
- **Mechanism:** Targets specific layer types (not full model) with trainable tokens
- **Key advantage:** Extremely memory-efficient (20.2 GB for 3B model vs 22.5 GB for LoRA)
- **Trade-off:** Lower test accuracy

### Lily
- **Mechanism:** Advanced adapter method optimized for high performance
- **Key advantage:** Highest test accuracy in benchmarks (54.9%)
- **Trade-off:** Higher peak VRAM (25.6 GB)

### GraLoRA (Gradient-based LoRA)
- **Mechanism:** Uses gradient information to guide rank allocation across layers
- **Key advantage:** Better performance than LoRA with similar memory footprint
- **Adapter conversion:** GraLoRA → LoRA conversion tested with near-identical results (0.702→0.694)

### VeRA (Vector-based Random Matrix Adaptation)
- **Mechanism:** No low-rank matrices — uses random seed vectors that are scaled
- **Key advantage:** Extremely parameter-efficient (much smaller than LoRA)
- **Trade-off:** Lower performance ceiling than LoRA

### Cartridges
- **Mechanism:** Designed to compress long prompts into trainable parameters
- **Key advantage:** Specialized for long-context / prompt-intensive tasks
- **Note:** Not measured in standard benchmarks — domain-specific

### rs-LoRA (Rank-Stabilized LoRA)
- **Mechanism:** Scales LoRA contribution differently from default initialization (`lora_alpha / rank` vs default with scaling)
- **Key advantage:** Significantly better accuracy than default LoRA (48.1% → 53.2%) with same memory
- **Usage:** Set `use_rslora=True` in `LoraConfig`

### LoRA-FA (LoRA with Frozen A)
- **Mechanism:** Freezes matrix A, only tunes matrix B; uses specialized optimizer
- **Key advantage:** Cuts activation memory (not sensitive to rank). 20.2 GB vs 22.5 GB for 3B model
- **Trade-off:** Lower accuracy (but memory savings are substantial)
- **Usage:** `optim="lora_fa"` or use `LoraFAConfig`

### DoRA (Weight-Decomposed Low-Rank Adaptation)
- **Mechanism:** Decomposes weights into magnitude and direction components; applies LoRA only to direction
- **Key advantage:** Closer to full fine-tuning behavior
- **Covered separately:** See `hf-peft-dora-deep-dive` skill

### AdaLoRA (Adaptive Budget Allocation)
- **Mechanism:** Dynamically allocates rank budget across layers based on importance
- **Key advantage:** More efficient use of parameter budget
- **Status:** Available in PEFT library

## Adapter Conversion (Non-LoRA → LoRA)

A major limitation of non-LoRA PEFT methods is limited downstream support (e.g., vLLM, llama.cpp only load LoRA adapters). **PEFT now supports converting any adapter type into LoRA format.**

### How it works:
```python
from peft import PeftModel, LoraConfig

# Load a non-LoRA adapter (e.g., GraLoRA)
model = PeftModel.from_pretrained(base_model, "path/to/gralora-adapter")

# Convert to LoRA config (automatically merges adapter weights into LoRA format)
model = model.to_lora()  # Returns a PeftModel with LoraConfig
```

### Validation:
- GraLoRA → LoRA conversion tested: similarity score 0.702 → 0.694 (near-identical)
- Visual quality of generated images is comparable before and after conversion
- Not all techniques have conversion support yet (being expanded)

## Choosing the Right PEFT Technique

### Decision Matrix:

| If you need... | Consider... | Why |
|---------------|-------------|-----|
| Best accuracy, can afford memory | **Lily** or **rs-LoRA** | Highest test scores |
| Lowest memory footprint | **BEFT** or **LoRA-FA** | ~10% less VRAM than LoRA |
| Best for image generation | **OFT** or **GraLoRA** | Beat LoRA on both score and memory |
| Parameter efficiency | **VeRA** or **LoRA-FA** | Fewest trainable params |
| Downstream compatibility | **LoRA variants** or **convert** | Convert non-LoRA → LoRA |
| Long-prompt tasks | **Cartridges** | Purpose-built |
| Quick drop-in replacement | **rs-LoRA** (set `use_rslora=True`) | One flag change |

### Switching Methods:
Thanks to PEFT's unified API, switching is literally one config import:

```python
# LoRA → OFT change
-from peft import LoraConfig, get_peft_model
+from peft import OFTConfig, get_peft_model

config = OFTConfig(target_modules=["q_proj", "v_proj"])  # was LoraConfig
model = get_peft_model(base_model, config)
```

## PEFT Benchmark Infrastructure

The benchmark is designed for:
- **Reproducibility:** Same base model, dataset, code, hardware across all methods
- **Consumer hardware:** Runs on single GPU (RTX 3090/4090, 24 GB VRAM for most tests)
- **Extensibility:** Anyone can contribute experiments via PR to the PEFT repo
- **Multi-metric:** Tracks not just accuracy but memory, runtime, forgetting, checkpoint size

### Interactive Comparison Space
The **PEFT Method Comparison** Space (`peft/peft-method-comparison`) lets you:
- Toggle between LLM math and image gen benchmarks
- Choose metric pair for Pareto frontier (accuracy vs memory, accuracy vs runtime, etc.)
- View individual sample images for qualitative comparison
- Filter by method capabilities (quantization support, mergeable, etc.)

### Contributing:
1. Add a new PEFT config to the benchmark scripts
2. Run on your hardware
3. Open a PR at https://github.com/huggingface/peft

## Limitations & Considerations

1. **Hyperparameter sensitivity:** Benchmark uses fixed hyperparams per method — tuning could shift rankings
2. **Not all capabilities measured:** Cartridges (prompt compression), quantization support, mergeability are tracked separately
3. **Layer type restrictions:** Not all methods can modify all layer types
4. **Quantization compatibility:** Some methods don't support quantized base models (being expanded)
5. **LoRA ecosystem advantage:** vLLM, llama.cpp, Diffusers have first-class LoRA support; other methods rely on adapter conversion

## Files Created
`hf-peft-beyond-lora/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md with complete deep-dive of advanced PEFT methods, benchmark results, Pareto frontier analysis, adapter conversion guide, and decision matrix.

## Sources
- https://huggingface.co/blog/peft-beyond-lora — Official "Beyond LoRA" blog post
- https://huggingface.co/docs/peft — PEFT documentation
- https://huggingface.co/spaces/peft/peft-method-comparison — Interactive benchmark Space
- https://huggingface.co/docs/peft/en/package_reference/oft — OFT/BOFT docs
- https://huggingface.co/docs/peft/en/package_reference/lora — LoRA variant docs
- https://github.com/huggingface/peft — PEFT GitHub repository
