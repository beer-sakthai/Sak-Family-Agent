# HF Learnings Log

## 2026-07-24: hf-distilabel — AI Feedback & Synthetic Data Framework (Topic #206)

### Summary
Comprehensive deep-dive into **distilabel v1.5.3** — the Argilla/Hugging Face ecosystem framework for synthetic data generation and AI feedback. Distilabel provides a DAG-based pipeline architecture for generating, evaluating, and transforming datasets using LLMs. It supports 15+ LLM providers, 30+ pre-built tasks (text generation, evol-instruct, preference scoring, quality filtering, structured generation), local and distributed execution (Ray), and seamless Hub integration via `Distiset.push_to_hub()`.

### Source
- GitHub: https://github.com/argilla-io/distilabel
- Docs: https://distilabel.argilla.io/
- PyPI: `pip install distilabel` — extras: `[hf-inference-endpoints,openai,anthropic,ray,vllm,ollama,outlines,instructor]`
- Citation: `@misc{distilabel-argilla-2024}`

---

### 1. Architecture Overview

Distilabel pipelines are **directed acyclic graphs (DAGs)** built using NetworkX (`pip install networkx`). Three component types compose the graph:

```
Pipeline (DAG)
├── Step (base processing unit)
│   ├── GeneratorStep — Yields data into the pipeline (root nodes, e.g. loading a dataset)
│   ├── GlobalStep — Receives ALL batches at once (requires file-system data passing)
│   └── Step — Standard processing, one batch at a time
├── Task (LLM-powered Step subclass)
│   ├── TextGeneration
│   ├── UltraFeedback
│   ├── EvolInstruct
│   ├── Magpie
│   └── ... (30+ implementations)
└── LLM (model wrapper)
    ├── InferenceEndpointsLLM
    ├── OpenAILLM / AnthropicLLM / MistralAILLM
    ├── TransformersLLM
    ├── vLLM / OllamaLLM / LlamaCppLLM
    └── LiteLLM (gateway to 100+ providers)
```

The DAG is defined declaratively via a context manager:

```python
with Pipeline(name="my-pipeline") as pipeline:
    load_data = LoadDataFromHub(...)          # GeneratorStep (root)
    generate = TextGeneration(llm=llm)         # Task
    score = QualityScorer(llm=judge_llm)       # Task
    load_data >> generate >> score             # Connect edges
```

### 2. Pipeline Execution Model

**Local execution (default):** Uses `multiprocessing.Pool` with non-daemon processes (allows subprocesses for vLLM tensor parallelism). Each step replica runs in a separate process, communicating via `multiprocessing.Queue`.

**Ray execution:** Call `pipeline.ray()` to get a `RayPipeline` for distributed execution on a Ray cluster. The same DAG definition works transparently.

**Execution flow:**
1. **DAG compilation** — The `BasePipeline.run()` validates the DAG, creates a topological sort, and assigns step wrappers.
2. **Loading** — Each step's `load()` is called (sequential order for steps sharing a GPU, parallel otherwise).
3. **Processing** — Steps execute in topological order. `GeneratorStep`s yield data as `_Batch` objects. Standard steps process batches from input queues and send results to output queues.
4. **Caching** — Each step's outputs are cached on disk (Parquet/Arrow format). Set `use_cache=True` (default) to skip re-execution of completed steps.
5. **Teardown** — Steps are unloaded, loggers stopped, and the `Distiset` is assembled from cached outputs.

**Key parameters of `pipeline.run()`:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `parameters` | `Dict[str, Dict]` | Runtime parameters per step (e.g., batch size, temperature) |
| `load_groups` | `List[List[str]]` | Steps to load together/in isolation (share GPU resources) |
| `use_cache` | `bool` | Reuse cached results from prior runs (default: `True`) |
| `dataset` | `Dataset` | If provided, auto-wraps in a `GeneratorStep` as root node |
| `dataset_batch_size` | `int` | Batch size when using `dataset` param (default: 50) |
| `use_fs_to_pass_data` | `bool` | Use filesystem for batch data passing (required for `GlobalStep`) |
| `logging_handlers` | `List[Handler]` | Custom logging handlers |

### 3. Step System Deep-Dive

The `_Step` base class (in `steps/base.py`, 830 lines) provides:

**Core properties:**
- `inputs` — Columns expected from upstream (can be required or optional)
- `outputs` — Columns produced by `process()`
- `resources` — `StepResources` (replicas, cpus, gpus, memory)
- `step_name` — Auto-inferred from class name (PascalCase → snake_case)

**Core methods:**
- `load()` — Initialize resources (LLM, model, connections). Called before processing.
- `unload()` — Release resources. Called after processing.
- `process(*inputs)` — Main processing logic. Accepts `StepInput` (list of dicts).
- `process_appender_callback()` — Post-process hook for results.

**Step sub-types:**
| Type | Characteristic |
|------|---------------|
| `Step` | Standard step. Processes batches sequentially. One input queue, one output queue. |
| `GeneratorStep` | Root node. No input. Yields batches via `next()` on an iterator. |
| `GlobalStep` | Receives ALL upstream batches at once (file-system buffered). For global ops (dedup, clustering). |

**RoutingBatchFunction** — A special edge type that routes batches to specific downstream replicas based on a function (e.g., hash-based partitioning).

**StepResources** controls parallelism:
```python
Step(resources=StepResources(replicas=2, gpus=1))  # 2 replicas, 1 GPU each
```

### 4. Task System Deep-Dive

`Task` (extending `_Step`) is the LLM-powered step type in `steps/tasks/base.py`. Key additions over `_Step`:

- `llm` — An `LLM` instance that does the generation
- `format_input(input)` — Converts a row dict to OpenAI chat format (`ChatType`)
- `format_output(output, input)` — Converts raw LLM output to the output dict
- `num_generations` — Generate N variants per input row
- `group_generations` — Boolean to group N generations as a list in one row vs N rows

**Task workflow:**
```
input row → format_input() → ChatType → LLM.generate() → raw text(s) → format_output() → output row
```

**Available Tasks (30+):**
| Task | Category | Description |
|------|----------|-------------|
| `TextGeneration` | text-gen | Jinja2-templated text generation |
| `ChatGeneration` | chat-gen | OpenAI-format conversation continuation |
| `UltraFeedback` | evaluation | AI feedback scoring (UltraFeedback paper) |
| `EvolInstruct` | evolution | Evol-Instruct: evolve seed instructions to be more complex |
| `EvolComplexity` | evolution | Evol-Complexity: increase instruction complexity |
| `EvolQuality` | evolution | Evol-Quality: improve instruction quality |
| `Magpie` | self-instruct | Generate instruction-response pairs from an LLM |
| `MagpieGenerator` | self-instruct | Magpie's generation step |
| `SelfInstruct` | self-instruct | Classic self-instruct: expand seed tasks |
| `PrometheusEval` | evaluation | LLM-as-a-judge scoring via Prometheus |
| `PairRM` | evaluation | Pairwise reward model scoring |
| `QualityScorer` | filtering | Score output quality (helpfulness, relevance) |
| `ComplexityScorer` | filtering | Score instruction complexity |
| `CLAIR` | filtering | Contrastive learning-based data filtering |
| `Genstruct` | generation | Generate instructions from documents |
| `InstructionBacktranslation` | generation | Reverse: generate instruction from response |
| `StructuredGeneration` | generation | JSON/structured output with schema |
| `TextClassification` | nlp | Zero-shot/few-shot text classification |
| `GenerateEmbeddings` | nlp | Generate embeddings with sentence-transformers |
| `TextGenerationWithImage` | vision | Multi-modal text generation |
| `ImageGeneration` | vision | Generate images from prompts |
| `APIGenGenerator` | code | Generate API call examples |
| `APIGenExecutionChecker` | code | Verify API call executability |
| `APIGenSemanticChecker` | code | Verify API call semantic correctness |

### 5. LLM Integration Architecture

The `LLM` base class (in `models/llms/base.py`, 560 lines) provides:

**Abstract methods to implement:**
- `model_name` — property returning the model identifier
- `generate(inputs, num_generations)` — Core generation method

**Built-in features:**
- **Generation kwargs** — `generation_kwargs: Dict` passed to every call
- **Offline batch generation** — `use_offline_batch_generation` with optional polling (`offline_batch_generation_block_until_done`)
- **Structured output** — Integration with Outlines and Instructor for JSON schema-constrained generation
- **Runtime parameters** — Dynamic configuration via `RuntimeParameter` Pydantic fields

**Official LLM integrations:**

| Integration | Extra | Class | Provider |
|-------------|-------|-------|----------|
| OpenAI | `openai` | `OpenAILLM` | OpenAI API |
| Azure OpenAI | `openai` | `AzureOpenAILLM` | Azure |
| Anthropic | `anthropic` | `AnthropicLLM` | Anthropic API |
| Cohere | `cohere` | `CohereLLM` | Cohere |
| Mistral AI | `mistralai` | `MistralAILLM` | Mistral API |
| HF Inference Endpoints | `hf-inference-endpoints` | `InferenceEndpointsLLM` | HF IE |
| LiteLLM | `litellm` | `LiteLLM` | 100+ providers via LiteLLM |
| vLLM | `vllm` | `vLLM` | Local vLLM server |
| Ollama | `ollama` | `OllamaLLM` | Local Ollama |
| Transformers | `hf-transformers` | `TransformersLLM` | Local HF transformers |
| llama.cpp | `llama-cpp` | `LlamaCppLLM` | Local GGUF via llama.cpp |
| Vertex AI | `vertexai` | `VertexAILLM` | Google Vertex AI |
| Groq | `groq` | `GroqLLM` | Groq API |
| Together AI | `openai` | `TogetherLLM` | Together (OpenAI-compatible) |
| Anyscale | `openai` | `AnyscaleLLM` | Anyscale (OpenAI-compatible) |
| MLX | `mlx` | `MlxLLM` | Apple MLX |

### 6. Distiset — Pipeline Output Container

The `Distiset` class (in `distiset.py`, 786 lines) extends `dict` — keys are leaf step names, values are `datasets.Dataset` objects.

**Key features:**
- `push_to_hub(repo_id, ...)` — Push all leaf datasets, pipeline config, artifacts, and logs to the Hub
- `save_to_disk(path)` / `load_from_disk(path)` — Local persistence
- `train_test_split(..., train_size, test_size)` — Standard dataset splitting
- `_pipeline_path` — Path to serialized pipeline config
- `_artifacts_path` — Path to step artifacts (images, plots, etc.)
- `_log_filename_path` — Path to the pipeline execution log

**Auto-generated metadata when pushing to Hub:**
- Pipeline configuration (steps, LLMs, parameters)
- Pipeline log file
- Step artifacts
- Dataset card with BibTeX citation, license, size categories
- System信息和 prompt 模板 recorded in card metadata

### 7. Structured Generation

Distilabel supports structured/constrained generation via two backends:

**Outlines (`pip install distilabel[outlines]`):**
- Uses `outlines` library for regex, JSON schema, and grammar-guided generation
- `StructuredGeneration` task with `structure` parameter
- Supports `json`, `regex`, `grammar`, `choice` structure types

**Instructor (`pip install distilabel[instructor]`):**
- Uses `instructor` library with Pydantic models
- `StructuredGeneration` with `mode="instructor"` and a Pydantic response model
- Automatically retries on validation failure

### 8. CLI Tools

Distilabel ships with a CLI accessible via `distilabel` command:

- `distilabel pipeline run` — Run a pipeline from a Python file
- `distilabel pipeline info` — Show pipeline DAG information
- `distilabel pipeline cache delete` — Delete pipeline cache
- `distilabel pipeline list` — List available pipelines

### 9. Hub Integration

**Pushing datasets:**
```python
distiset.push_to_hub(
    repo_id="username/my-dataset",
    private=True,
    commit_message="Generated with distilabel",
)
```

**Auto-generated dataset card** includes:
- Pipeline structure visualization
- LLM model names used
- Generation parameters (temperature, max tokens)
- Step-by-step column descriptions
- BibTeX citation for distilabel

**Reading in downstream pipelines:**
```python
from datasets import load_dataset
# Each leaf step becomes a dataset split/config
dataset = load_dataset("username/my-dataset", split="text_generation_0")
```

### 10. Best Practices

1. **Use caching wisely** — Set `use_cache=False` when iterating on pipeline design, then `use_cache=True` for production runs to avoid re-generating expensive LLM calls.
2. **Batch size tuning** — `dataset_batch_size=50` is default. Larger batches = more throughput but higher memory. For very long context LLMs, reduce to 1-8.
3. **GPU sharing** — Use `load_groups` to ensure steps sharing a GPU are loaded sequentially (one at a time) rather than competing for memory.
4. **Offline batch generation** — For large datasets, set `use_offline_batch_generation=True` on the LLM with `offline_batch_generation_block_until_done` for polling. This ships requests to the provider's batch API and polls for completion.
5. **Custom steps** — Subclass `Step` and override `process()`. For LLM-powered steps, subclass `Task` and override `format_input()` / `format_output()`.
6. **Ray for scale** — When processing >100K rows, use `RayPipeline` for parallel execution across a cluster.
7. **Structured output for downstream** — Use `StructuredGeneration` with JSON schema when the output must be machine-parseable.

### Limitations (v1.5.3)

- No built-in streaming execution (all processing happens in batch)
- No native async execution (though LLM calls can be async within a step)
- `GlobalStep` requires file-system buffering (high I/O for large datasets)
- Community-maintained (original authors moved on; community collaborators now maintain it)
- No built-in support for multi-turn conversation generation
- Pipeline YAML serialization is experimental
