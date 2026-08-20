---
name: SakThai-hf-datasets-image-processing
description: "Covers the datasets.Image feature \u2014 loading, decoding, transforming, encoding,\
  \ and streaming image data through the Hugging Face datasets library (v5.0.0+)."
---

# HF Datasets Image Processing

## Description
Covers the `datasets.Image` feature — loading, decoding, transforming, encoding, and streaming image data through the Hugging Face `datasets` library (v5.0.0+). Handles all input types (paths, bytes, PIL Images, numpy arrays), streaming patterns, image folder datasets, on-the-fly transforms, and memory management.

## Key Resources
- [Image feature API reference](https://huggingface.co/docs/datasets/en/package_reference/main_classes#datasets.Image)
- [Image dataset loading guide](https://huggingface.co/docs/datasets/en/image_dataset)
- [Image processing guide](https://huggingface.co/docs/datasets/en/image_process)
- [ImageFolder builder](https://huggingface.co/docs/datasets/en/image_dataset#imagefolder)
- [Streaming documentation](https://huggingface.co/docs/datasets/en/stream)

## Topics Covered
- `Image()` feature: decode=True/False, mode conversion, encode_example, decode_example
- Arrow storage layer: `struct<bytes: binary, path: string>` and cast_storage
- Streaming image datasets with `load_dataset(streaming=True)`
- ImageFolder: directory-structured datasets with automatic label inference
- On-the-fly transforms via `.map()` and `.with_transform()`
- Memory-efficient patterns: deferred decode, batch processing, embed_storage
- Input types and encoding: PIL, numpy, paths, bytes dicts
- Integration with model pipelines (transformers, torchvision)
- Private repo image access via `token_per_repo_id`
- Parquet-based image datasets: encoded bytes columns
- Image mode conversion (`RGB`, `L`, etc.) during decode
