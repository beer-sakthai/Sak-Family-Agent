---
name: SakThai-hf-distilabel
description: HuggingFace Distilabel for synthetic data generation and labeling
...
---

# SakThai Distilabel Skill

Distilabel is an AI Feedback (AIF) framework for building synthetic datasets with and for LLMs. Created by Argilla (part of the Hugging Face ecosystem), it provides a pipeline-based approach to data generation, evaluation, and transformation using LLMs.

## Key Concepts

- **Pipeline**: A directed acyclic graph (DAG) of processing steps. Supports local execution via `multiprocessing` or distributed via `Ray`.
- **Step**: A building block that processes data as lists of dictionaries (`List[Dict[str, Any]]`). Steps connect in a DAG to form a pipeline.
- **Task**: A step that relies on LLMs and prompts to perform generative tasks (text gen, evaluation, scoring).
- **LLM**: A model wrapper (remote API or local) — supports OpenAI, Anthropic, HF Inference Endpoints, vLLM, Ollama, Transformers, llama.cpp, Mistral, Cohere, VertexAI, and more.
- **Distiset**: The pipeline output — a dict-like container mapping leaf step names to `datasets.Dataset` objects, with pipeline metadata and artifacts.

## Common Tasks

- `TextGeneration` / `ChatGeneration` — Basic text generation with Jinja2 templates
- `UltraFeedback` — AI feedback evaluation (from the UltraFeedback paper)
- `EvolInstruct` / `EvolComplexity` / `EvolQuality` — Data evolution techniques
- `Magpie` / `MagpieGenerator` — Self-instruction data generation
- `SelfInstruct` — Seed-instruction expansion
- `PrometheusEval` — LLM-as-a-judge evaluation
- `PairRM` — Pairwise reward model scoring
- `QualityScorer` / `ComplexityScorer` — Data quality filtering
- `CLAIR` — Contrastive learning-based data filtering
- `Genstruct` — Instruction generation from documents
- `InstructionBacktranslation` — Reverse instruction generation
- `StructuredGeneration` — JSON/structured output generation
- `TextClassification` / `GenerateEmbeddings` — Non-LLM tasks
- `APIGen` — API call generation and verification suite

## Usage Pattern

```python
with Pipeline() as pipeline:
    TextGeneration(
        llm=InferenceEndpointsLLM(
            model_id="meta-llama/Meta-Llama-3.1-8B-Instruct",
            generation_kwargs={"temperature": 0.7, "max_new_tokens": 512},
        ),
    )

dataset = load_dataset("dataset/repo", split="test")
distiset = pipeline.run(dataset=dataset)
distiset.push_to_hub(repo_id="my-generated-dataset")
```

## Tips

- Install extras as needed: `pip install "distilabel[hf-inference-endpoints,openai,ray]"`
- Use `use_cache=True` (default) to reuse prior pipeline results
- Use `RayPipeline` for distributed execution on large datasets
- The `Distiset` includes pipeline metadata, logs, and artifacts automatically
- Supports structured generation via Outlines or Instructor
