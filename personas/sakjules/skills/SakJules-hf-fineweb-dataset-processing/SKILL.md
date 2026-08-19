---
name: SakJules-SakThai-hf-fineweb-dataset-processing
description: "Hugging Faces FineWeb, FineWeb-Edu, and FineWeb-2 datasets \u2014 web-scale data\
  \ processing pipeline using datatrove for LLM pretraining data curation, including\
  \ URL filtering, text extraction, language filtering, quality heuristics, MinHash\
  \ deduplication"
---

# FineWeb Dataset Processing Pipeline

The Hugging Face FineWeb family (FineWeb, FineWeb-Edu, FineWeb-2) represents the largest open-source collection of cleaned web data for LLM pretraining, processed using the `datatrove` library. This skill covers the complete processing pipeline, quality filtering methodology, and educational classification system.

## Key References

- FineWeb dataset: https://huggingface.co/datasets/HuggingFaceFW/fineweb
- FineWeb-Edu dataset: https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu
- FineWeb-2 (multilingual): https://huggingface.co/datasets/HuggingFaceFW/fineweb-2
- datatrove library: https://github.com/huggingface/datatrove
- Processing script: https://github.com/huggingface/datatrove/blob/main/examples/fineweb.py
- Educational classifier: https://huggingface.co/HuggingFaceFW/fineweb-edu-classifier
- Paper: https://arxiv.org/abs/2406.17557 (NeurIPS 2024 Datasets & Benchmarks)
