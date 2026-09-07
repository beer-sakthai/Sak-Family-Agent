---
name: SakThai-hf-transformers-watermarking
description: ">   Complete reference on AI watermarking in the Hugging Face ecosystem —   Transformers watermarking system (Kirchenbauer + SynthID Text), logits   processors, detectors (WatermarkDetector, BayesianDetectorModel,   SynthIDTextWatermarkDetector), Gra"
---

# Hugging Face Transformers Watermarking System

## Overview

Watermarking in the Hugging Face ecosystem spans three layers:

1. **Transformers Built-in Watermarking** — Logits processors and detectors
   integrated directly into `transformers` for marking and detecting AI-generated
   text during `model.generate()`.

2. **SynthID Text Watermarking** (Google DeepMind) — Tournament-based watermarking
   using a Bayesian detector, integrated as `SynthIDTextWatermark*` classes.

3. **Grado Visible Watermarking** — Client-side watermark overlay on images,
   video, and chatbot text via the `watermark` parameter.

4. **Hub Ecosystem** — Community Spaces for watermarking/detection (IMATAG,
   Truepic, Watermark for LLMs, AudioSeal).

## 1. Transformers Built-in Watermarking

Based on the paper *"A Watermark for Large Language Models"*
(https://huggingface.co/papers/2306.04634) by Kirchenbauer et al.

### Architecture

Watermarking works by splitting the vocabulary into "green" and "red" tokens
based on a pseudo-random seed derived from previous tokens:

- **Green tokens** get a bias added to their logits (making them more likely)
- **Red tokens** are unchanged (or suppressed)
- Detection works by checking what fraction of generated tokens are "green"

### WatermarkingConfig

```python
from transformers import WatermarkingConfig

config = WatermarkingConfig(
    greenlist_ratio=0.25,   # Fraction of vocab considered "green" (0.0–1.0)
    bias=2.0,               # Logit bias added to green tokens (recommended: 0.5–2.0)
    hashing_key=15485863,   # Private key for greenlist generation (millionth prime)
    seeding_scheme="lefthash",  # "lefthash" (Algorithm 2) or "selfhash" (Algorithm 3)
    context_width=1,        # Number of previous tokens for seeding
)
```

**Schemes:**
- `"lefthash"` (default): Green tokens depend on the last generated token. Fast.
- `"selfhash"`: Green tokens depend on the current candidate token. More robust
  but slower (rejection sampling up to 40 candidates).

### Usage with model.generate()

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, WatermarkingConfig

model = AutoModelForCausalLM.from_pretrained("openai-community/gpt2")
tokenizer = AutoTokenizer.from_pretrained("openai-community/gpt2")
tokenizer.pad_token_id = tokenizer.eos_token_id

inputs = tokenizer(["Alice and Bob are"], return_tensors="pt")

# Watermarked generation
watermarking_config = WatermarkingConfig(bias=2.5, context_width=2, seeding_scheme="selfhash")
out = model.generate(
    **inputs,
    watermarking_config=watermarking_config,
    max_length=20,
    do_sample=False
)
print(tokenizer.batch_decode(out, skip_special_tokens=True)[0])
```

### WatermarkLogitsProcessor

The low-level processor that modifies logits during generation. Used internally
by `WatermarkingConfig.construct_processor()`.

```python
from transformers.generation.logits_process import WatermarkLogitsProcessor

processor = WatermarkLogitsProcessor(
    vocab_size=50257,
    device="cpu",
    greenlist_ratio=0.25,
    bias=2.0,
    hashing_key=15485863,
    seeding_scheme="lefthash",
    context_width=1,
)
```

Key internals:
- **`set_seed(input_seq)`**: Determines RNG seed from last `context_width` tokens
- **`_get_greenlist_ids(input_seq)`**: Returns a random subset of vocab as "green" tokens
- **`_score_rejection_sampling()`**: For "selfhash" scheme — finds the highest-probability
  token that falls in the greenlist by checking up to 40 candidates

### WatermarkDetector

Detects whether text was generated with a specific watermark configuration.

```python
from transformers import WatermarkDetector, WatermarkingConfig

# Must use the EXACT same config used during generation
detector = WatermarkDetector(
    model_config=model.config,
    device="cpu",
    watermarking_config=watermarking_config,
    ignore_repeated_ngrams=False,
    max_cache_size=128,
)

# Detection
detection_out = detector(
    out_watermarked,           # input_ids tensor
    z_threshold=3.0,           # sensitivity (lower = more sensitive)
    return_dict=True,
)

print(detection_out.prediction)   # array([ True, False, ...])
print(detection_out.z_score)      # array of z-scores
print(detection_out.confidence)   # array of confidence scores (1 - p_value)
```

**Output fields** (`WatermarkDetectorOutput`):
| Field | Type | Description |
|-------|------|-------------|
| `num_tokens_scored` | np.ndarray | Number of tokens scored per batch |
| `num_green_tokens` | np.ndarray | Number of "green" tokens found |
| `green_fraction` | np.ndarray | Fraction of green tokens |
| `z_score` | np.ndarray | Standard deviations from expected green count |
| `p_value` | np.ndarray | Statistical significance |
| `prediction` | np.ndarray | Boolean: True = watermarked |
| `confidence` | np.ndarray | 1 - p_value |

**Important:** The detector must be initialized with the **exact same**
`WatermarkingConfig` used during generation. Different config = no detection.

### Best Practices for Watermark Strength

- **bias=2.0** (default): Good balance of detectability vs. text quality
- **bias=0.5**: Minimal quality impact, weaker detection
- **bias=2.5+**: Strong detection, may degrade text quality with greedy decoding
- Increase `context_width` for more robustness against editing
- Use `seeding_scheme="selfhash"` for stronger watermark (slower generation)
- Watermark detection requires **sufficient text length** (short texts have low
  confidence due to fewer tokens to score)

## 2. SynthID Text Watermarking (Google DeepMind)

Based on the paper *"Scalable watermarking for identifying large language model
outputs"* (https://www.nature.com/articles/s41586-024-08025-4) by Dathathri et al.

A more sophisticated tournament-based watermark that uses a
**Bayesian detector** trained to distinguish watermarked from unwatermarked text.

### Architecture

- **Tournament-based watermarking**: Multiple layers of tournament matches
  determine g-values (binary values: 0 or 1) at each position
- **G-values** are computed from n-gram context using a pre-computed sampling table
- **Bayesian detector** computes P(watermarked | g_values) using a trained
  likelihood model

### SynthIDTextWatermarkingConfig

```python
from transformers import SynthIDTextWatermarkingConfig

config = SynthIDTextWatermarkingConfig(
    keys=[654, 400, 836, 123, 340, 443, 597, 160, 57],  # One key per depth layer
    ngram_len=5,                    # N-gram context length
    context_history_size=1024,      # Seen contexts tracking buffer
    sampling_table_seed=0,          # RNG seed for sampling table
    sampling_table_size=65536,      # Sampling table size (must be < 2^24)
    skip_first_ngram_calls=False,   # Skip first ngram calls
    debug_mode=False,               # Uniform logits for testing
)
```

**Keys:** A list of integers, one per "depth" layer of the tournament. More keys
= more watermarking depth = stronger signal. The paper uses 9 keys (depth=9).

### Generation with SynthID

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, SynthIDTextWatermarkingConfig

tokenizer = AutoTokenizer.from_pretrained('google/gemma-2-2b', padding_side="left")
model = AutoModelForCausalLM.from_pretrained('google/gemma-2-2b')

watermarking_config = SynthIDTextWatermarkingConfig(
    keys=[654, 400, 836, 123, 340, 443, 597, 160, 57],
    ngram_len=5,
)

tokenized_prompts = tokenizer(["Once upon a time, "], return_tensors="pt", padding=True)
output_sequences = model.generate(
    **tokenized_prompts,
    watermarking_config=watermarking_config,
    do_sample=True,
    max_new_tokens=10,
)
```

### SynthIDTextWatermarkLogitsProcessor

Low-level processor that handles:

- **State management**: Tracks token sequences for key generation
- **G-value sampling**: Maps hash of n-gram keys to binary g-values via
  a pre-computed sampling table (similar to hashtable used in
  facebookresearch/three_bricks)
- **Score adjustment**: Applies g-values to modify logits during generation
- **Context repetition handling**: Avoids watermarking repeated contexts
- **EOS token masking**: Prevents EOS token from being watermarked
- **Utility functions**: `compute_g_values()`, `compute_context_repetition_mask()`,
  `compute_eos_token_mask()`, `expected_mean_g_value()`

### Detection with SynthID

SynthID detection uses a trained Bayesian detector model:

```python
from transformers import (
    AutoTokenizer,
    BayesianDetectorModel,
    SynthIDTextWatermarkLogitsProcessor,
    SynthIDTextWatermarkDetector,
)

# Load a trained detector module
detector_model = BayesianDetectorModel.from_pretrained("joaogante/dummy_synthid_detector")

# Create logits processor with same config used during generation
logits_processor = SynthIDTextWatermarkLogitsProcessor(
    **detector_model.config.watermarking_config,
    device="cpu",
)

tokenizer = AutoTokenizer.from_pretrained(detector_model.config.model_name)
detector = SynthIDTextWatermarkDetector(detector_model, logits_processor, tokenizer)

# Detect
test_input = tokenizer(["This is a test input"], return_tensors="pt")
is_watermarked = detector(test_input.input_ids)  # bool
```

### BayesianDetectorModel

A trained PyTorch module that computes posterior probability
P(watermarked | g_values) using Bayes' rule:

```
P(w|g) = P(g|w) * P(w) / P(g)
       = sigmoid(log_odds_prior + sum(log_odds_likelihood))
```

**Components:**
- `BayesianDetectorWatermarkedLikelihood`: Neural model P(g_values | watermarked)
  — a logistic regression on tournament g-values
- Prior P(w): Learned parameter (default base_rate=0.5)
- Likelihood P(g | unwatermarked): Always 0.5 (Bernoulli)

The detector outputs a posterior probability in [0, 1]; >0.5 suggests watermarked.

### BayesianDetectorConfig

```python
from transformers import BayesianDetectorConfig

config = BayesianDetectorConfig(
    watermarking_depth=9,     # Number of tournament layers
    base_rate=0.5,            # Prior probability P(w) a text is watermarked
)
```

### Training a SynthID Detector

Training scripts live in `examples/synthid_text/detector_training.py` in the
transformers repo. Research project reference:
https://github.com/huggingface/transformers-research-projects/tree/main/synthid_text

The detector is trained on paired data:
- Watermarked text → g-values with known watermark
- Unwatermarked text → random g-values (Bernoulli(0.5))

## 3. Gradio Visible Watermarking

Introduced in Gradio (blog post September 2025), visible watermarks can be added
to generated media with a single parameter.

### Images

```python
import gradio as gr

gr.Image(
    my_generated_image,
    watermark="path/to/watermark.png",  # File, numpy array, or URL
)
```

### Video

```python
gr.Video(
    my_generated_video,
    watermark="path/to/watermark.png",
)
```

### Chatbot (Text)

```python
gr.Chatbot(
    label="My Model",
    watermark="Generated by AI",  # Text overlay on copy
    type="messages",
    show_copy_button=True,
    show_copy_all_button=True,
)
```

The text watermark appears when users copy content from the chatbot —
automatically appending attribution to the clipboard.

### QR Code Watermarks

QR watermarks can carry more information about content provenance and can be
style-matched to the image. See the
[QR Code AI Art Generator Space](https://huggingface.co/spaces/huggingface-projects/QR_Code_AI_Art_Generator).

## 4. Hub Ecosystem: Watermarking Spaces

| Space | Purpose | Type |
|-------|---------|------|
| [Watermark for LLMs](https://huggingface.co/spaces/watermark/watermark-for-llms) | Demo of text watermarking (red/green token visualization) | Open |
| [IMATAG SDXL Turbo](https://huggingface.co/spaces/imatag/imatag-sdxl-turbo) | Invisible watermark during image generation | Closed watermarker |
| [Truepic](https://huggingface.co/spaces/truepic/truepic-watermark) | C2PA metadata + invisible watermark after generation | Closed detector |
| [AudioSeal](https://huggingface.co/facebook/audioseal) | Speech-localized watermarking | Open |
| [Watermark Demo](https://huggingface.co/spaces/huggingface/watermark-demo) | Gradio visible watermarking demo | Open |
| [Chatbot Watermark Demo](https://huggingface.co/spaces/huggingface/chatbot-watermark-demo) | Chatbot text watermarking demo | Open |
| [Deepfake Detection](https://huggingface.co/spaces/huggingface/deepfake-detection) | General deepfake detection | Open |

### Specialized Watermarking Models on HF Hub

- **stabilityai/sdxl-turbo** — IMATAG-modified version for invisible watermarking
  during generation
- **facebook/audioseal** — Jointly trained generator + detector for audio
  watermarking at sample-level resolution (1/16k sec)

## 5. TGI Watermarking

Text Generation Inference (TGI) also implements the Kirchenbauer watermarking
algorithm. Parameters:
- `--watermark`: Enable watermarking
- `--watermark_greenlist_ratio`: Greenlist ratio (default: 0.25)
- `--watermark_bias`: Bias added to green tokens (default: 2.0)

## 6. Data Poisoning & Related Techniques

Related anti-AI-manipulation tools on the Hub:
| Tool | Purpose |
|------|---------|
| **Nightshade** | Poison training data to impact model quality |
| **Fawkes** | Cloak faces against facial recognition training |
| **Photoguard** | Guard images against generative AI manipulation |
| **Glaze** | Imperceptibly alter images for AI processing protection |

## Practical Workflow: Full Cycle

```python
# 1. Generate watermarked text
from transformers import AutoModelForCausalLM, AutoTokenizer, WatermarkingConfig, WatermarkDetector

model_id = "openai-community/gpt2"
model = AutoModelForCausalLM.from_pretrained(model_id)
tokenizer = AutoTokenizer.from_pretrained(model_id)
tokenizer.pad_token_id = tokenizer.eos_token_id
tokenizer.padding_side = "left"

inputs = tokenizer(["This is the beginning of a long story"], padding=True, return_tensors="pt")

# 2. Generate with watermark
wm_config = WatermarkingConfig(bias=2.5, seeding_scheme="selfhash")
out_wm = model.generate(**inputs, watermarking_config=wm_config, max_length=30, do_sample=False)

# 3. Detect watermark
detector = WatermarkDetector(
    model_config=model.config,
    device="cpu",
    watermarking_config=wm_config,
)
result = detector(out_wm, return_dict=True)
print(f"Watermarked: {result.prediction}, Confidence: {result.confidence}")
```

## Summary: Two Watermark Systems Comparison

| Feature | Kirchenbauer Watermark | SynthID Text Watermark |
|---------|----------------------|----------------------|
| Paper | arXiv 2306.04634 | Nature 2024 |
| Vocab splitting | Green/red (random partition) | Tournament g-values (multi-layer) |
| Detection | Statistical (z-score) | Bayesian (trained model) |
| Config class | `WatermarkingConfig` | `SynthIDTextWatermarkingConfig` |
| Processor | `WatermarkLogitsProcessor` | `SynthIDTextWatermarkLogitsProcessor` |
| Detector | `WatermarkDetector` | `SynthIDTextWatermarkDetector` |
| Requires training | No | Yes (BayesianDetectorModel) |
| Quality impact | Low (adjustable via bias) | Low (tournament-based) |
| Robustness | Moderate | Higher (depth layers) |
| Availability | TGI + Transformers | Transformers (main branch) |

## Key URLs

| Resource | URL |
|----------|-----|
| Kirchenbauer paper | https://huggingface.co/papers/2306.04634 |
| SynthID Nature paper | https://www.nature.com/articles/s41586-024-08025-4 |
| Blog: AI Watermarking 101 | https://huggingface.co/blog/watermarking |
| Blog: Visible Watermarking | https://huggingface.co/blog/watermarking-with-gradio |
| Watermarking in TGI | https://huggingface.co/docs/text-generation-inference/en/conceptual/watermarking |
| SynthID research project | https://github.com/huggingface/transformers-research-projects/tree/main/synthid_text |
| Transformers source | https://github.com/huggingface/transformers/blob/main/src/transformers/generation/watermarking.py |
| Transformers logits_process | https://github.com/huggingface/transformers/blob/main/src/transformers/generation/logits_process.py |
| Watermark for LLMs Space | https://huggingface.co/spaces/watermark/watermark-for-llms |
