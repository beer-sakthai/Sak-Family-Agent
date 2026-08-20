---
name: SakThai-hf-transformers-5
description: '>-   Deep-dive skill for Hugging Face Transformers v5.x architecture. Covers the   new
  cache system (DynamicCache, StaticCache, MtpCache, QuantizedCache),   Multi-Token
  Prediction (MTP), built-in watermarking, continuous batching   for production ser'
---

# Hugging Face Transformers v5 — Architecture Deep Dive

Key references in `references/hf-learnings.md`.

## Quick Reference

### Cache Selection
```python
model.generate(**inputs, cache_implementation="quantized")       # Quantized KV cache
model.generate(**inputs, cache_implementation="offloaded")       # CPU offloaded
model.generate(**inputs, cache_implementation="sliding_window")  # Sliding window
```

### Multi-Token Prediction
```python
model.generate(**inputs, use_mtp=True, num_assistant_tokens=3)
```

### Watermarking
```python
from transformers import WatermarkingConfig
model.generate(**inputs, watermarking_config=WatermarkingConfig(greenlist_ratio=0.25))
```

### New Pipelines
```python
from transformers import pipeline
pipe = pipeline("any-to-any", model="google/gemma-3n-E4B-it")
pipe = pipeline("image-text-to-text", model="google/gemma-4-it")
```

## Resources
- Cache utils: `transformers.cache_utils`
- Generation: `transformers.generation`
- Docs: https://huggingface.co/docs/transformers/en/index
