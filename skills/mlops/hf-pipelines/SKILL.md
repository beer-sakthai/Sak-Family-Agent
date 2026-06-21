---
name: hf-pipelines
description: "Hugging Face Pipelines (transformers.pipeline): high-level inference API that wraps models, tokenizers, and post-processing for rapid deployment across text, vision, audio, and multimodal tasks."
version: 1.0.0
author: SakThai
license: MIT
tags: [huggingface, transformers, pipeline, inference, nlp, vision, audio, multimodal]
platforms: [linux, macos, windows]
---

# Hugging Face Pipelines

The `transformers.pipeline()` API provides a **high-level, unified interface** for running inference on thousands of models with minimal code. It automatically handles model downloading, tokenization/preprocessing, inference execution, and post-processing (e.g., decoding logits to labels).

## Core Concept

```python
from transformers import pipeline

# One-liner inference
classifier = pipeline("sentiment-analysis")
result = classifier("I love using Hugging Face!")
# [{'label': 'POSITIVE', 'score': 0.9998}]
```

Pipelines abstract away:
- **Model selection** — picks a sensible default model for the task.
- **Preprocessing** — tokenization, image resizing, audio resampling, etc.
- **Device placement** — GPU/CPU/TPU via `device=` or `device_map`.
- **Post-processing** — softmax decoding, NER span merging, object-detection box filtering.

## Supported Tasks

Common task strings include:

- **Text**: `sentiment-analysis`, `text-classification`, `token-classification`, `ner`, `question-answering`, `summarization`, `translation_en_to_fr`, `text-generation`, `text2text-generation`, `fill-mask`, `zero-shot-classification`
- **Vision**: `image-classification`, `object-detection`, `image-segmentation`, `depth-estimation`, `zero-shot-image-classification`
- **Audio**: `automatic-speech-recognition`, `audio-classification`, `text-to-speech`
- **Multimodal**: `visual-question-answering`, `document-question-answering`, `image-to-text`

Discover available tasks programmatically:

```python
import transformers
print(transformers.pipeline.TASK_ALIASES.keys())
```

## Specifying a Model

By default, pipelines download a small default model. Override it with `model=`:

```python
# Custom model for a task
pipe = pipeline(
    "text-generation",
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    tokenizer="meta-llama/Meta-Llama-3-8B-Instruct",
)

# Or pass just the model; tokenizer is resolved automatically
pipe = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
```

## Device and Memory Management

```python
# Explicit device
pipe = pipeline("summarization", device=0)  # GPU 0
pipe = pipeline("summarization", device=-1) # CPU (default)

# Automatic sharding for large models
pipe = pipeline(
    "text-generation",
    model="bigscience/bloom-560m",
    device_map="auto",      # auto-shard across GPUs
)
```

- `device=-1` → CPU
- `device=0` → first GPU
- `device_map="auto"`, `"balanced"`, `"sequential"` → offload layers across devices.

## Batch Inference

```python
sentences = [
    "I love this!",
    "This is terrible.",
    "Not sure how I feel.",
]

results = pipe(sentences, batch_size=8)
# Returns a list of dicts aligned to inputs
```

Pipelines use the underlying `DataLoader`-style batching internally for supported tasks.

## Streaming Generation (Text)

```python
from transformers import pipeline

pipe = pipeline("text-generation", model="gpt2")
for output in pipe("Once upon a time", streamer=True):
    print(output)
```

Use with `TextStreamer` or `TextIteratorStreamer` for token-by-token output.

## Pipeline Anatomy

Under the hood, a pipeline is composed of:

1. **Feature Extractor / Image Processor / Audio Feature Extractor** — handles raw input conversion.
2. **Tokenizer** — text encoding/decoding.
3. **Model** — the actual forward pass.
4. **Post-Processor** — converts logits to readable outputs.

Access them directly:

```python
pipe = pipeline("ner", model="dslim/bert-base-NER")
print(pipe.model)             # The underlying model
print(pipe.tokenizer)         # The tokenizer
print(pipe.feature_extractor) # None for NER (tokenizer only)
print(pipe.task)              # "ner"
```

## Custom Pipelines

If the built-in tasks don't fit, subclass `pipeline()`:

```python
from transformers import Pipeline

class CustomPipeline(Pipeline):
    def _sanitize_parameters(self, **kwargs):
        # Parse extra kwargs
        return kwargs, {}, {}

    def preprocess(self, inputs):
        # Convert raw input into model-ready format
        return self.tokenizer(inputs, return_tensors="pt")

    def _forward(self, model_inputs):
        return self.model(**model_inputs)

    def postprocess(self, model_outputs):
        # Convert logits -> user-friendly output
        return {"custom": "result"}

# Register and use
from transformers import pipeline
CustomPipeline.register_for_task("custom-task")
pipe = pipeline("custom-task", model="distilbert-base-uncased")
```

Alternatively, define a `.py` preprocessing script next to your model repo on the Hub, and pipelines will use it if `trust_remote_code=True`.

## Trusting Remote Code

Some models require custom modeling code stored in their repo:

```python
pipe = pipeline(
    "text-classification",
    model="some-org/some-model",
    trust_remote_code=True,
)
```

**Security note:** `trust_remote_code=True` executes Python from the Hub. Only use it with trusted repos.

## Common Pitfalls

- **Pipeline vs raw model**: Pipelines add convenience but hide useful flexibility (e.g., custom attention masks). For complex tasks, use `AutoModel` + tokenizer directly.
- **Default models change over time**: Pin explicit model IDs for reproducibility.
- **Memory leaks**: For long-running services, reuse a single pipeline instance instead of recreating it per request.
- **CPU slowness**: Tokenization and CPU inference are single-threaded by default in some cases; set `TOKENIZERS_PARALLELISM=true` or use `num_workers` when applicable.
- **Mixed precision**: Pipelines do not automatically enable `fp16` on GPU for all tasks. Use `torch_dtype=torch.float16` explicitly if needed.

## Performance Tips

1. **Reuse instances** — keep `pipe` alive across requests.
2. **Batch when possible** — `pipe(inputs, batch_size=N)`.
3. **Use `.to()` or `device_map`** — move model to GPU once.
4. **Enable FlashAttention** — pick models that support it (`model="meta-llama/Meta-Llama-3-8B-Instruct"` + `torch_dtype=torch.bfloat16`).
5. **Quantize** — for large models, use `load_in_4bit=True` or `load_in_8bit=True` with `bitsandbytes`.

## References

- **Docs**: https://huggingface.co/docs/transformers/main/en/pipeline_tutorial
- **API reference**: https://huggingface.co/docs/transformers/main/en/main_classes/pipelines
- **Task guide**: https://huggingface.co/docs/transformers/main/en/tasks
