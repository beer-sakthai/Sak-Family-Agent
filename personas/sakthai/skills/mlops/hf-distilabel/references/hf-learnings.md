# HF Learnings Log

## 2026-07-24: hf-distilabel — AI Feedback & Synthetic Data Framework (Topic #205)

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

|### Limitations (v1.5.3)

|- No built-in streaming execution (all processing happens in batch)
|- No native async execution (though LLM calls can be async within a step)
|- `GlobalStep` requires file-system buffering (high I/O for large datasets)
|- Community-maintained (original authors moved on; community collaborators now maintain it)
|- No built-in support for multi-turn conversation generation
|- Pipeline YAML serialization is experimental

---

## 2026-07-24: hf-distilabel — Source Code Architecture Deep-Dive (v2)

### Summary
Deep-dive into the **distilabel v1.5.3 source code internals** — the execution engine, caching subsystem, DAG compilation, batch management, and serialization framework. This update extends the prior architectural overview with actual code-level analysis of how the pipeline runs, recovers from cache, and manages batch flow between steps.

### Source Files Analyzed
- `src/distilabel/pipeline/_dag.py` (984 lines) — DAG construction, validation, trophic levels, load stages
- `src/distilabel/pipeline/base.py` (1931 lines) — BasePipeline: run orchestration, caching, fsspec, validation
- `src/distilabel/pipeline/local.py` (437 lines) — Local multiprocessing Pipeline with non-daemon Pool
- `src/distilabel/pipeline/batch.py` (237 lines) — `_Batch` dataclass: data containers with FS spill-to-disk
- `src/distilabel/pipeline/batch_manager.py` (1294 lines) — `_BatchManager` & `_BatchManagerStep`: scheduling & batching
- `src/distilabel/pipeline/step_wrapper.py` (354 lines) — Process-level step lifecycle manager
- `src/distilabel/pipeline/write_buffer.py` (192 lines) — Parquet write buffer for output persistence
- `src/distilabel/steps/base.py` — `_Step`, `Step`, `GeneratorStep` class hierarchy
- `src/distilabel/mixins/signature.py` — SignatureMixin for cache key generation
- `src/distilabel/utils/serialization.py` — `_Serializable` base class (JSON/YAML persistence)
- Total: **183 Python source files** in the distilabel package

---

### 11. Cache System Architecture

The caching system is the most sophisticated subsystem in distilabel, enabling fault-tolerant pipeline execution.

#### 11.1 Three-Level Cache Hierarchy

**Level 1 — Pipeline Configuration Cache:**
- Path: `<cache_dir>/<pipeline_name>/<pipeline_signature>/executions/<aggregated_steps_signature>/pipeline.yaml`
- Contains the full serialized DAG with step configurations
- `pipeline_signature` is a hash of: step names + connection info + routing batch function type info
- Example structure:
  ```
  ~/.cache/distilabel/pipelines/
    my-pipeline/
      a1b2c3d4.../                          # pipeline_signature
        executions/
          e5f6g7h8.../                      # aggregated_steps_signature
            pipeline.yaml                   # Serialized DAG
            batch_manager.json              # Serialized BatchManager state
            stages.json                     # Current execution stage
            pipeline.log                    # Execution log
            data/                           # Leaf step output Parquet files
              step_a/                       # Per-step Parquet directory
                00001.parquet
                00002.parquet
              step_b/
            batch_input_data/               # FS-passed batch data (GlobalStep)
  ```

**Level 2 — Step-Level Cache (SignatureMixin):**
- Each `_Step` generates a unique `signature` hash from its serialized attributes (minus excluded fields like `TYPE_INFO_KEY`, `input_batch_size`, `resources`, `gpu_memory_utilization`)
- The `aggregated_steps_signature` at the pipeline level is `sha1(concat of all step signatures)` — determines the execution subdirectory
- If any step's configuration changes, a new aggregated hash is generated, creating a fresh cache path (old data is preserved but orphaned)

**Level 3 — BatchManager Cache:**
- `_BatchManager` is serialized to `batch_manager.json` after each pipeline run
- Contains the state of `_BatchManagerStep` objects — which batches have been sent, which are pending, and step offsets
- On resume: `_BatchManager.load()` deserializes and reconstructs the exact state, continuing from where the previous run left off
- The `can_generate()` method checks if there are unprocessed batches remaining

#### 11.2 Cache Collision Avoidance

```python
# pipeline/_dag.py — signature construction
def signature(self) -> str:
    pipeline_dump = self.dump()["pipeline"]
    steps_names = list(self.dag)
    connections_info = [
        f"{c['from']}-{'-'.join(c['to'])}" for c in pipeline_dump["connections"]
    ]
    # Routing batch functions are also hashed
    routing_batch_functions_info = [
        f"{f['step']}-{routing_batch_function._get_type_info()}"
        for f in pipeline_dump["routing_batch_functions"]
    ]
    return hashlib.sha1(
        ",".join(steps_names + connections_info + routing_batch_functions_info).encode()
    ).hexdigest()
```

Cache directory layout is `<cache_dir>/<pipeline_name>/<pipeline_signature>/executions/<aggregated_steps_signature>/`. This means:
- If the pipeline **structure** changes (new steps, different connections) → new `pipeline_signature` → new parent directory
- If any step's **configuration** changes (different model, temperature, prompt template) → new `aggregated_steps_signature` → new execution subdirectory
- Old cache is never deleted automatically — the `distilabel pipeline cache delete` CLI command is provided for manual cleanup

#### 11.3 Cache Recovery Flow

In `BasePipeline.run()`:
1. `_refresh_pipeline_from_cache()` — if `pipeline.yaml` exists on disk, the cached DAG replaces the in-memory one. Preserves secrets and excluded attributes via `recursively_handle_secrets_and_excluded_attributes()` because those aren't serialized
2. `_load_stages_status(use_cache)` — reads `stages.json` to determine which execution stage to resume from
3. `_load_batch_manager(use_cache)` — deserializes `_BatchManager` from `batch_manager.json`, reconstructing the exact buffer state
4. `_setup_write_buffer(use_cache)` — creates `_WriteBuffer` that can append to existing Parquet files if `use_cache=True`
5. If `_batch_manager.can_generate()` returns `False`, the pipeline short-circuits and returns a `Distiset` built from the cached data files

#### 11.4 Step-Level Cache Signature Exclusions

```python
# mixins/signature.py
_EXCLUDE_FROM_SIGNATURE_DEFAULTS = {
    TYPE_INFO_KEY,           # Module/class metadata
    "disable_cuda_device_placement",
    "input_batch_size",      # Step input batch size (runtime-parameterized)
    "gpu_memory_utilization",
    "resources",             # CPU/GPU/memory resource allocation
    "exclude_from_signature",
    "llm_jobs_ids",          # Async batch job IDs (change each run)
    "llm_offline_batch_generation_block_until_done",
}
```

The `SignatureMixin.signature` property flattens the entire `self.dump()` hierarchy recursively and excludes fields listed in `exclude_from_signature`. This is why changing `input_batch_size` doesn't invalidate the cache — it's excluded because it's a runtime parameter.

---

### 12. DAG Compilation & Execution Engine

#### 12.1 Graph Structure

The `DAG` class wraps a `networkx.DiGraph` with:
- **Nodes**: Step names mapped to `_Step` instances via `STEP_ATTR_NAME` attribute
- **Edges**: Data flow direction (from upstream to downstream)
- **Routing batch functions**: Attached to nodes via `ROUTING_BATCH_FUNCTION_ATTR_NAME`

Key graph properties used throughout execution:
| Property | Source | Description |
|----------|--------|-------------|
| `root_steps` | `cached_property` | Nodes with `in_degree == 0` (GeneratorSteps) |
| `leaf_steps` | `cached_property` | Nodes with `out_degree == 0` (terminal steps → Distiset keys) |
| `trophic_levels` | `nx.trophic_levels()` | Ecological trophic levels — root = 1, each edge = +1 |
| `get_step_predecessors()` | `nx.ancestors()` | All transitive ancestors |
| `get_step_replica_count()` | `step.resources.replicas` | Number of parallel replicas |

#### 12.2 Validation Pipeline

`DAG.validate()` runs before every execution:
1. **Type check per trophic level**: Level 1 steps must be `GeneratorStep` instances
2. **Process signature validation**: Each step's `process()` must have `StepInput` typed arguments
3. **Runtime parameter validation**: All required runtime parameters must be provided
4. **Input mapping verification**: `verify_inputs_mappings()` / `verify_outputs_mappings()` checks column name mappings
5. **Input availability check**: `_step_inputs_are_available()` walks the ancestor graph to verify all required inputs are produced by upstream steps
6. **Convergence step detection**: If all predecessors receive routed batches, the step is marked as a convergence step

#### 12.3 Load Stages System

The `get_steps_load_stages()` method computes execution stages:
```python
# Algorithm:
# 1. Create a load group for each GlobalStep (they load in isolation)
# 2. Sort load groups by topological position
# 3. Steps not in any load group are grouped into stages based on topological order
# 4. GlobalStep stages interrupt normal stages
# Result: Tuple of (stages, stages_last_steps)
```

Example: `A >> [B, C] >> D` where C is a `GlobalStep`:
- Stage 0: [A] (Generator)
- Stage 1: [B, C] (B = normal step, C = GlobalStep in its own group)
- Stage 2: [D] (consumes from both B and C)

The `_save_stages_status()` persists `current_stage` and `stages_last_batch` to `stages.json` for crash recovery.

---

### 13. Batch Management: The Scheduler

#### 13.1 `_BatchManager` (Top-Level Orchestrator)

The `_BatchManager` holds a dictionary of `_BatchManagerStep` instances (one per non-generator step) and orchestrates batch flow. Key methods:

```python
class _BatchManager:
    def can_generate(self) -> bool:     # True if any step has pending data
    def set_next_expected_seq_no(...)   # Ordering enforcement for convergence steps
    def get_routed_batches(self, ...)   # Route batches to specific downstream replicas
    def cache(...)                      # Serialize state to batch_manager.json
    def load(...)                       # Deserialize from cache
```

#### 13.2 `_BatchManagerStep` (Per-Step Buffer)

Each `_BatchManagerStep` maintains:
- `data: Dict[str, List[_Batch]]` — Incoming batch buffers keyed by predecessor step name
- `built_batches: List[_Batch]` — Batches already built but not yet consumed
- `seq_no: int` — Auto-incrementing batch sequence number
- `last_batch_received: List[str]` — Tracks which predecessors have sent their last batch
- `convergence_step: bool` — Special handling for convergence patterns

**Step types determine batching behavior:**

| Step Type | `accumulate` | Batching behavior |
|-----------|-------------|-------------------|
| `Step` (normal) | `False` | Reads `input_batch_size` rows from each predecessor, FIFO |
| `GlobalStep` | `True` | Receives ALL data at once (file-system buffered) |
| Convergence | Special | Groups batches by `created_from.seq_no` to maintain ordering |

#### 13.3 Batch Creation Algorithm (Normal Step)

```
1. _ready_to_create_batch():
   - For each predecessor: sum of buffered rows >= input_batch_size
   - AND all predecessors have at least one batch in buffer
   
2. _get_data_normal():
   - For each predecessor buffer:
     - Take `input_batch_size` rows from the front of the buffer
     - If a source batch has remaining rows, keep it in buffer with updated data
     - Track `batches_used` for cache invalidation
   
3. Returns _Batch with:
   - seq_no (monotonic)
   - data (list of lists: one list per predecessor)
   - created_from (which batches from which steps were consumed)
   - batch_routed_to (if routing batch function applied)
```

#### 13.4 Convergence Step Handling

When `A >> RoutingBatchFunction >> [B, C] >> D`:
- B and C each receive routed subsets of A's output
- D (convergence step) must recombine outputs from B and C in the correct order
- `_get_data_for_convergence_step()` groups incoming batches by the `seq_no` of the batch they were **created from** (tracked via `created_from` dict)
- `convergence_step_batches_consumed` tracks how many rows from each original A-batch have been consumed by B and C
- Ordering is enforced via `next_expected_created_from_batch_seq_no`

---

### 14. Process Execution Model (Local Pipeline)

#### 14.1 Non-Daemon Process Pool

```python
# local.py: Custom non-daemon process pool
class _NoDaemonProcess(mp.Process):
    @property
    def daemon(self) -> bool:
        return False  # Allow child processes (e.g., vLLM tensor parallelism)
```

The `Pipeline.run()` method:
1. Calls `BasePipeline.run()` for setup/validation/cache recovery
2. If cache is valid and complete, returns `Distiset` immediately
3. Otherwise, creates `multiprocessing.Manager()`, `_NoDaemonPool`, and queues
4. For each step + replica, calls `_run_step()` which wraps the step in `_StepWrapper` and submits to the pool via `pool.apply_async()`

#### 14.2 Step Wrapper Lifecycle

`_StepWrapper.run()` executes the full step lifecycle in a subprocess:

```
1. step.load()                 — Initialize LLM, models, connections
2. Notify load_queue: loaded   — Main process tracks load status
3. Generate or process loop:
   - GeneratorStep: yield batches on demand (backpressure via input_queue)
   - Normal Step: receive batches from input_queue, process, send to output_queue
4. step.unload()               — Release GPU memory, close connections
5. Notify load_queue: unloaded — Main process marks step as complete
```

#### 14.3 Generator Step Backpressure Protocol

Generator steps use a **pull-based backpressure** mechanism:
1. Main process sends an initial empty `_Batch` (signal) to the generator's `input_queue`
2. Generator calls `process(offset=...)` which yields `(data, last_batch)` tuples
3. Each yielded batch is sent to `output_queue`
4. Generator blocks waiting for the next empty batch on `input_queue` (backpressure signal from downstream)
5. Loop continues until `last_batch=True` or `None` sentinel received

```python
# step_wrapper.py — generator step process loop
def _generator_step_process_loop(self):
    batch = self.input_queue.get()  # Wait for request signal
    offset = batch.seq_no * step.batch_size
    
    for data, last_batch in step.process_applying_mappings(offset=offset):
        batch.set_data([data])
        batch.last_batch = self.dry_run or last_batch
        self._send_batch(batch)  # Send to output_queue
        
        if batch.last_batch:
            return
        
        batch = self.input_queue.get()  # Block for next request (backpressure)
```

#### 14.4 Output Queue Thread

The main process runs a dedicated thread (`_run_output_queue_loop_in_thread`) that:
1. Receives completed batches from `_StepWrapper` subprocesses via `self._output_queue`
2. Passes them to `_BatchManager.add_batch()` for distribution to downstream steps
3. When a step's stage completes, signals the next stage's steps to load
4. Writes output to `_WriteBuffer` for persistence
5. The thread blocks on `self._output_queue_thread.join()` until all batches are consumed

---

### 15. Write Buffer — Parquet Persistence

`_WriteBuffer` converts step output batches to Parquet files:

```python
class _WriteBuffer:
    def __init__(self, path, leaf_steps, steps_cached=None):
        # Creates directory structure:
        # <path>/step_a/
        # <path>/step_b/
```

**Write mechanism:**
1. Batches accumulate in `_buffers[step_name]` (list of dicts)
2. When buffer reaches `_buffers_dump_batch_size` (hardcoded: 50 rows), triggers `_write()`
3. `_write()` converts to PyArrow table, writes to `<step_name>/NNNNN.parquet`
4. On cache recovery (existing Parquet file found + `use_cache=True`): reads previous table, concatenates with `pa.concat_tables()`
5. `close()` writes remaining buffer contents and rewrites files with unified schema

**Schema evolution handling:**
- If schemas differ but column names match, selects `last_schema.names` for ordering
- If schemas truly diverge, uses `pa.unify_schemas()` to create a union schema
- Flattened dicts used as fallback for mixed struct/non-struct data
- All files in a step's directory are rewritten with the final schema on `close()`

---

### 16. Distiset — Output Assembly

When the pipeline finishes, `create_distiset()` scans the data directory:

```python
# distiset.py
distiset = create_distiset(
    data_dir=self._cache_location["data"],
    pipeline_path=self._cache_location["pipeline"],
    log_filename_path=self._cache_location["log_file"],
    enable_metadata=self._enable_metadata,
    dag=self.dag,
)
```

- Each leaf step's Parquet directory becomes a key in the `Distiset` dict
- For each key: scans `data/<step_name>/*.parquet`, reads all files via `datasets.load_dataset("parquet")`
- The `Distiset` also bundles pipeline path, artifacts path, and log path
- `push_to_hub()` reads all leaf datasets, generates dataset card with pipeline metadata, and pushes

---

### 17. Routing Batch Functions

The `RoutingBatchFunction` enables dynamic batch routing:

```python
# Defined using >> operator with a function
routing_fn = RoutingBatchFunction(
    fn=lambda batch: [step_name_1] if condition else [step_name_2]
)
step_a >> routing_fn >> [step_b, step_c]
```

**Key implementation details:**
- `ROUTING_BATCH_FUNCTION_ATTR_NAME` is stored on the DAG node of the source step
- `batch_routed_to: List[str]` is set on each `_Batch` output by the routing function
- `_BatchManager.get_routed_batches()` filters which downstream replicas receive which batches
- Steps receiving routed batches are tracked in `steps_receiving_routed_batches` list during validation
- Convergence steps (all predecessors receive routed batches) get special ordering treatment

---

### 18. Serialization Framework

The `_Serializable` base class provides:
- `dump()` → dict with `TYPE_INFO_KEY` (module + class name) for polymorphic deserialization
- `save()` → JSON or YAML serialization
- `from_dict()` / `from_json()` / `from_yaml()` → polymorphic reconstruction via `load_with_type_info()`
- `_model_dump()` → pydantic model serialization with:
  - API key exclusion (keys named `api_key` are stripped)
  - EnumType special handling
  - `RuntimeParametersMixin` list serialization

---

### 19. Pipeline Execution State Machine

```
                   ┌──────────────────────────────────┐
                   │         BasePipeline.run()        │
                   │  (setup, validation, cache check) │
                   └──────────┬───────────────────────-┘
                              │
                    ┌─────────▼─────────┐
                    │  Cache complete?  │──Yes──► Return Distiset from cache
                    └─────────┬─────────┘
                              │ No
                    ┌─────────▼─────────┐
                    │ Load stage N      │
                    │ (Group of steps)  │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Submit steps to    │
                    │ Pool (apply_async) │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Output Queue Loop  │
                    │ - Route batches    │
                    │ - Write to buffer  │
                    │ - Track completion │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Stage complete?   │──No──► Continue processing
                    └─────────┬─────────┘
                              │ Yes
                    ┌─────────▼─────────┐
                    │ More stages?      │──Yes──► Increment stage, loop
                    └─────────┬─────────┘
                              │ No
                    ┌─────────▼─────────┐
                    │ Teardown, cache,   │
                    │ create Distiset    │
                    └───────────────────┘
```

---

### 20. Key Performance Internals

| Component | Bottleneck | Mitigation |
|-----------|-----------|------------|
| Batch creation | FIFO ordering requires keeping batches sorted (`sort(key=lambda b: b.seq_no)`) | Sorting only happens on insertion, which is O(log n) per batch |
| FS data passing | Parquet serialization/deserialization overhead | Only used for `GlobalStep` (required) or when `use_fs_to_pass_data=True` |
| Cache serialization | Full pipeline dump every `_cache()` call | Only called once at teardown; cache reads are more frequent (YAML/JSON deserialization) |
| Pool parallelism | `multiprocessing.Queue` contention | Queue-based IPC is designed for batch-oriented (not row-oriented) data |
| Write buffer | PyArrow table creation per 50 rows | Buffer size is a tradeoff — too large = memory pressure, too small = many small Parquet files |

### New Insights for Practitioners

1. **Cache path structure**: Understand `<pipeline_sig>/<step_sig>` to predict when cache invalidates. Changing any LLM parameter (temperature, model_id) creates a new cache path — old data is orphaned.
2. **Backpressure tuning**: Generator steps are throttled by downstream consumption rate. If a pipeline appears stuck, check if a downstream step is slow to process (generator is blocking on `input_queue.get()`).
3. **GlobalStep performance**: `GlobalStep` forces FS buffering (Parquet on disk for intermediate data). For large datasets, this creates significant I/O — consider whether a regular `Step` with large `input_batch_size` would suffice.
4. **Convergence step memory**: The `convergence_step_batches_consumed` dict tracks per-batch consumption. For pipelines with many routing branches, this dict can grow large — plan accordingly.
5. **Schema drift**: The `_WriteBuffer` schema unification (`pa.unify_schemas()`) can silently handle column additions mid-pipeline, but it rewrites all prior Parquet files on `close()` — costly for outputs with many shards.
