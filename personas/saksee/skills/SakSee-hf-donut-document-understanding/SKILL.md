---
name: SakSee-SakThai-hf-donut-document-understanding
description: "Hugging Face Donut (Document Understanding Transformer) \u2014 comprehensive reference\
  \ for OCR-free document understanding with Swin Transformer encoder + BART decoder\
  \ architecture, inference pipelines, fine-tuning, and model card documentation."
---

# HF Donut: Document Understanding Transformer

## Purpose
Deep knowledge of Hugging Face Donut — an end-to-end OCR-free document understanding model. Covers architecture (Swin encoder + BART decoder), available checkpoints, inference patterns (document parsing, VQA, classification), fine-tuning, quantization, and deployment.

## Paper & Background
- **Paper**: [Donut: Document Understanding Transformer](https://huggingface.co/papers/2111.15664) (2021-11-30, arXiv:2111.15664)
- **Authors**: Geewook Kim, Teakgyu Hong, Moonbin Yim, et al. (NAVER Clova AI / Clova Information Extraction)
- **Key Innovation**: First end-to-end Transformer-based document understanding model that **eliminates OCR** entirely
- **License**: MIT

## Architecture

Donut uses a **Vision Encoder + Text Decoder** architecture:

### Encoder: Swin Transformer (DonutSwinModel)
- Hierarchical vision transformer with shifted window attention
- Processes document images (no OCR pre-processing needed)
- Configurable via `DonutSwinConfig`:
  - `image_size`: 2560×1920 (default), can be reduced for speed
  - `patch_size`: 4×4
  - `window_size`: 10
  - `embed_dim`, `depths`, `num_heads`: stage-wise configuration
- Outputs image patch embeddings

### Decoder: BART (mBART-like)
- Standard Transformer decoder with cross-attention to encoder outputs
- Generates token sequences conditioned on the visual features
- Task-specific prompt tokens guide the decoder (e.g., `<s_cord-v2>`)

### Processor: DonutProcessor
- Combines `DonutImageProcessor` (image preprocessing) + `BartTokenizerFast` (text tokenization)
- Handles: image resizing, normalization, tensor conversion + text tokenization, decoding
- `token2json()` method converts generated token sequences to structured JSON
- Key methods: `__call__()`, `batch_decode()`, `decode()`, `from_pretrained()`, `save_pretrained()`

## Available Models on Hugging Face Hub

All original checkpoints under [naver-clova-ix](https://huggingface.co/naver-clova-ix):

| Model ID | Task | Downloads | Description |
|----------|------|-----------|-------------|
| `naver-clova-ix/donut-base` | Base | 61.7k | Pre-trained backbone (no fine-tuning) |
| `naver-clova-ix/donut-base-finetuned-cord-v2` | Receipt parsing | 27.6k | CORD dataset — receipt information extraction |
| `naver-clova-ix/donut-base-finetuned-docvqa` | Doc VQA | — | Document Visual Question Answering |
| `naver-clova-ix/donut-base-finetuned-rvlcdip` | Doc classification | 2.06k | RVL-CDIP — 16 document categories |
| `naver-clova-ix/donut-base-finetuned-zhtrainticket` | Ticket parsing | 179 | Chinese train ticket information extraction |
| `naver-clova-ix/donut-base-finetuned-kuzushiji` | Japanese cursive | — | Historical Japanese character recognition |
| `naver-clova-ix/donut-base-finetuned-cord-v1` | Receipt parsing | 11 | Earlier CORD fine-tune |
| `naver-clova-ix/donut-proto` | Prototype | 28 | Early experimental version |

Community variants include `philschmid/donut-base-finetuned-cord-v2` and various Spaces demos.

## Inference Patterns

### 0. Installation
```bash
pip install transformers datasets torch
# For quantization:
pip install torchao
```

### 1. Document Visual Question Answering (DocVQA)
```python
from transformers import pipeline
from datasets import load_dataset

# Pipeline approach (simplest)
pipe = pipeline(
    task="document-question-answering",
    model="naver-clova-ix/donut-base-finetuned-docvqa",
)

dataset = load_dataset("hf-internal-testing/example-documents", split="test")
image = dataset[0]["image"]
print(pipe(image=image, question="What time is the coffee break?"))
```

### 2. Document Classification
```python
import re
import torch
from transformers import DonutProcessor, VisionEncoderDecoderModel
from datasets import load_dataset

processor = DonutProcessor.from_pretrained(
    "naver-clova-ix/donut-base-finetuned-rvlcdip"
)
model = VisionEncoderDecoderModel.from_pretrained(
    "naver-clova-ix/donut-base-finetuned-rvlcdip",
    device_map="auto"
)

dataset = load_dataset("hf-internal-testing/example-documents", split="test")
image = dataset[1]["image"]

# Task prompt signals what to do
task_prompt = "<s_rvlcdip>"
decoder_input_ids = processor.tokenizer(
    task_prompt, add_special_tokens=False, return_tensors="pt"
).input_ids

pixel_values = processor(image, return_tensors="pt").pixel_values

outputs = model.generate(
    pixel_values=image_pixel_values,
    decoder_input_ids=decoder_input_ids,
    max_length=model.decoder.config.max_position_embeddings,
    pad_token_id=processor.tokenizer.pad_token_id,
    eos_token_id=processor.tokenizer.eos_token_id,
    use_cache=True,
    bad_words_ids=[[processor.tokenizer.unk_token_id]],
    return_dict_in_generate=True,
)

sequence = processor.batch_decode(outputs.sequences)[0]
sequence = sequence.replace(processor.tokenizer.eos_token, "").replace(
    processor.tokenizer.pad_token, ""
)
sequence = re.sub(r"<.*?>", "", sequence, count=1).strip()
print(processor.token2json(sequence))
# → {'class': 'advertisement'}
```

### 3. Document Parsing (Receipt Understanding)
```python
import re
import torch
from transformers import DonutProcessor, VisionEncoderDecoderModel
from datasets import load_dataset

processor = DonutProcessor.from_pretrained(
    "naver-clova-ix/donut-base-finetuned-cord-v2"
)
model = VisionEncoderDecoderModel.from_pretrained(
    "naver-clova-ix/donut-base-finetuned-cord-v2",
    device_map="auto"
)

dataset = load_dataset("hf-internal-testing/example-documents", split="test")
image = dataset[2]["image"]

task_prompt = "<s_cord-v2>"
decoder_input_ids = processor.tokenizer(
    task_prompt, add_special_tokens=False, return_tensors="pt"
).input_ids
pixel_values = processor(image, return_tensors="pt").pixel_values

outputs = model.generate(
    pixel_values=pixel_values,
    decoder_input_ids=decoder_input_ids,
    max_length=model.decoder.config.max_position_embeddings,
    pad_token_id=processor.tokenizer.pad_token_id,
    eos_token_id=processor.tokenizer.eos_token_id,
    use_cache=True,
    bad_words_ids=[[processor.tokenizer.unk_token_id]],
    return_dict_in_generate=True,
)

sequence = processor.batch_decode(outputs.sequences)[0]
sequence = sequence.replace(processor.tokenizer.eos_token, "").replace(
    processor.tokenizer.pad_token, ""
)
sequence = re.sub(r"<.*?>", "", sequence, count=1).strip()
result = processor.token2json(sequence)
print(result)
# → {'menu': {'nm': 'CINNAMON SUGAR', 'unitprice': '17,000', ...}, ...}
```

### 4. AutoModel API (Transformers v5)
```python
from transformers import AutoModelForImageTextToText, AutoProcessor

processor = AutoProcessor.from_pretrained(
    "naver-clova-ix/donut-base-finetuned-docvqa"
)
model = AutoModelForImageTextToText.from_pretrained(
    "naver-clova-ix/donut-base-finetuned-docvqa",
    device_map="auto"
)

task_prompt = f"<s_docvqa><s_question>What is the invoice total?</s_question><s_answer>"
inputs = processor(image, task_prompt, return_tensors="pt").to(model.device)

outputs = model.generate(
    input_ids=inputs.input_ids,
    pixel_values=inputs.pixel_values,
    max_length=512
)
answer = processor.decode(outputs[0], skip_special_tokens=True)
print(answer)
```

## Quantization

Donut supports weight quantization to reduce memory. Example with torchao int4:

```python
from transformers import AutoModelForImageTextToText, AutoProcessor, TorchAoConfig

quantization_config = TorchAoConfig("int4_weight_only", group_size=128)
processor = AutoProcessor.from_pretrained(
    "naver-clova-ix/donut-base-finetuned-docvqa"
)
model = AutoModelForImageTextToText.from_pretrained(
    "naver-clova-ix/donut-base-finetuned-docvqa",
    quantization_config=quantization_config,
    device_map="auto"
)
```

Also compatible with bitsandbytes (8-bit, 4-bit) via `load_in_8bit=True` / `load_in_4bit=True`.

## Task Prompt Tokens

Each fine-tuned variant uses a special task prompt token that tells the model what task to perform:

| Task | Model | Prompt Token |
|------|-------|-------------|
| Document VQA | donut-base-finetuned-docvqa | `<s_docvqa><s_question>{question}</s_question><s_answer>` |
| Receipt parsing | donut-base-finetuned-cord-v2 | `<s_cord-v2>` |
| Document classification | donut-base-finetuned-rvlcdip | `<s_rvlcdip>` |
| Chinese ticket parsing | donut-base-finetuned-zhtrainticket | `<s_zhtrainticket>` |
| Japanese cursive | donut-base-finetuned-kuzushiji | `<s_kuzushiji>` |

## Transformers Classes Reference

| Class | Description |
|-------|-------------|
| `DonutSwinConfig` | Configuration for the Swin Transformer encoder |
| `DonutSwinModel` | Swin Transformer encoder (outputs image patch embeddings) |
| `DonutSwinForImageClassification` | Swin encoder with classification head |
| `DonutImageProcessor` | Image pre-processing (resize, normalize, tensor conversion) |
| `DonutImageProcessorPil` | PIL-based image pre-processing variant |
| `DonutProcessor` | Combined processor (image + text) — the main entry point |
| `VisionEncoderDecoderModel` | Wrapper pairing DonutSwinModel + BART decoder |

## Zero-Cost Inference Strategies

Donut runs well on CPU with reasonable speed for single documents:
```python
# CPU inference — no GPU needed
processor = DonutProcessor.from_pretrained("naver-clova-ix/donut-base-finetuned-cord-v2")
model = VisionEncoderDecoderModel.from_pretrained(
    "naver-clova-ix/donut-base-finetuned-cord-v2"
)  # no device_map — runs on CPU

# Serverless Inference via HF InferenceClient
from huggingface_hub import InferenceClient
client = InferenceClient("naver-clova-ix/donut-base-finetuned-cord-v2")
# Note: Donut isn't typically on free Inference Providers; use local CPU for zero-cost
```

## Fine-Tuning Donut

Fine-tuning requires a dataset with document images and structured JSON targets. Steps:
1. Prepare dataset: images + JSON annotations (e.g., CORD format)
2. Load pre-trained `donut-base` (not fine-tuned variant)
3. Use `VisionEncoderDecoderModel.from_pretrained()` with the base model
4. Train with `Seq2SeqTrainer` or custom training loop
5. Key considerations:
   - Learning rate: ~5e-5
   - Max document image size: 2560×1920 (can reduce for faster training)
   - Task prompt token must be added to tokenizer
   - `processor.token2json()` expects structured output format

## Finding Donut on HF Hub

```python
from huggingface_hub import HfApi

api = HfApi()
models = api.list_models(
    search="donut",
    pipeline_tag="image-to-text",
    library="transformers",
    sort="downloads",
    direction=-1,
    limit=20
)
for m in models:
    print(f"{m.modelId} — {m.downloads} downloads")
```

## Ecosystems & Related Models

Donut is part of the broader Hugging Face Document AI ecosystem:
- **LayoutLMv3** — OCR-based document understanding (layout + text + image)
- **Nougat** — Neural Optical Understanding for Academic Documents (LaTeX/PDF → Markdown)
- **TrOCR** — Transformer-based OCR (printed/handwritten text recognition)
- **Pix2Struct** — Visual language understanding for screenshots, documents, and figures
- **GOT-OCR2** — General OCR Theory model (Chinese + English)
- **DePlot** — Chart/plot understanding
- **MatCha** — Math and chart understanding
- **PP-OCRv5/v6** — PaddleOCR models on HF Hub

## Demo Spaces

Notable Donut Spaces on HF Hub:
- `naver-clova-ix/Donut-Base-Finetuned-Cord-V2` — official receipt parsing demo
- `nielsr/Donut-DocVQA` — DocVQA interactive demo
- `nielsr/Donut-RVLCDIP` — Document classification demo
- Various community Spaces for receipt parsing, DocVQA, and form understanding

## Pitfalls

1. **Image size matters**: Donut expects high-resolution images (default 2560×1920). Smaller images lose detail. Balance resolution vs. memory.
2. **Task prompt is required**: Without the correct `<s_task>` prompt, the decoder won't produce meaningful output.
3. **token2json format**: The output JSON structure depends on the fine-tuning dataset. Each variant outputs different keys.
4. **Don't use OCR-based models for OCR-free tasks**: Donut excels where OCR would fail (noisy docs, irregular layouts, multiple languages). For clean printed text, TrOCR may be faster.
5. **Memory usage**: Base model is ~350MB. Fine-tuned variants are similar. With int4 quantization, can run in <200MB.
6. **CPU speed**: Expect 5–15 seconds per document on CPU. Batch processing is recommended for throughput.
7. **Bad words IDs**: Always set `bad_words_ids=[[processor.tokenizer.unk_token_id]]` during generation to prevent `<unk>` tokens.
