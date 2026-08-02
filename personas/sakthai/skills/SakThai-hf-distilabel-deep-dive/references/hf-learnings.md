# HF Learnings — Deep Dive: hf-distilabel

## 2026-07-25: hf-distilabel — Complete Synthetic Data Pipeline Framework (v1.5.3 Deep Dive)

### Summary
Comprehensive deep dive into **distilabel v1.5.3**, Argilla's framework for building synthetic data generation and AI feedback pipelines. Covers pipeline DAG architecture, step types, column-based data flow, all LLM integrations (16+ providers), 40+ built-in tasks, Distiset output management, caching, Ray distribution, custom step authoring, and real-world patterns for SFT/DPO/RLHF training data generation.

Researched directly from source code and live API exploration on 2026-07-25.

---

### Architecture Overview

distilabel uses a **DAG (Directed Acyclic Graph)** pipeline model where:
- **Steps** are nodes connected by the `>>` operator
- **Data flows** as batches of dicts through the DAG, with columns mapped between steps
- **Pipeline** orchestrates execution with multiprocessing (local) or Ray (distributed)
- **Output** is a `Distiset` — a dict of Hugging Face Datasets (one per leaf step)

**Three step types:**

| Type | Base Class | Purpose | Example |
|------|-----------|---------|---------|
| **Generator** | `GeneratorStep` | Produces data without inputs (root nodes) | `LoadDataFromHub`, `LoadDataFromDicts`, `MagpieGenerator` |
| **Regular** | `Step` | Transform-step | `KeepColumns`, `MergeColumns`, `ExpandColumns` |
| **Task** | `Task` (extends `Step`) | LLM-powered generation with structured output | `TextGeneration`, `UltraFeedback`, `SelfInstruct` |

**Pipeline lifecycle:**
```
1. Build DAG in `with Pipeline(...) as pipeline:` context
2. pipeline.run(parameters={...}, dataset=..., use_cache=True)
3. Distiset returned — push_to_hub, save_to_disk, or train_test_split
```

---

### Pipeline Construction

```python
from distilabel.pipeline import Pipeline
from distilabel.steps import LoadDataFromDicts, KeepColumns
from distilabel.steps.tasks import TextGeneration
from distilabel.models.llms import TransformersLLM

with Pipeline(
    name="my-pipeline",
    description="SFT data generation pipeline",
    enable_metadata=False,       # track provenance columns
    cache_dir=None,              # custom cache location
    requirements=None,           # pip requirements for Ray remote
) as pipeline:
    
    loader = LoadDataFromDicts(data=[{"instruction": "Write a poem"}])
    
    llm = TransformersLLM(
        model="unsloth/Llama-3.2-1B-Instruct",
        device="cpu",
        generation_kwargs={"temperature": 0.7, "max_new_tokens": 256},
    )
    
    generator = TextGeneration(
        llm=llm,
        template="{{ instruction }}",
        columns=["instruction"],
        num_generations=1,
        add_raw_output=True,
        add_raw_input=True,
        use_system_prompt=True,
        system_prompt="You are a helpful assistant.",
    )
    
    keeper = KeepColumns(columns=["instruction", "generation", "raw_output"])
    
    loader >> generator >> keeper
```

**Pipe context:** The `with Pipeline(...)` context is optional — you can construct without it and call `pipeline.run()` later. The context just ensures the DAG is built correctly.

---

### Step Composition & Data Flow

**The `>>` operator** connects steps. Left step's output columns feed into right step's input columns.

**Column flow:**
- Each step declares `input_mappings` and `output_mappings`
- `input_mappings`: `{"step_input_col": "llm_input_col"}` — rename before processing
- `output_mappings`: `{"step_output_col": "pipeline_output_col"}` — rename after
- Mappings are defined at step creation time

**Branching & merging:**
```python
# Multiple generators feed into one task
gen1 >> combiner
gen2 >> combiner

# One step feeds multiple downstream
loader >> splitter
splitter >> branch_a
splitter >> branch_b
```

**Built-in data flow steps:**
- `KeepColumns(columns=[...])` — keep only specified columns
- `MergeColumns(columns=[...], output_column="merged")` — combine columns
- `ExpandColumns(columns=[...])` — expand nested JSON/dict columns
- `GroupColumns()` — group columns by prefix
- `CombineOutputs()` — combine outputs from multiple upstream steps
- `TruncateTextColumn(column="...", max_length=...)` — truncate long text
- `ConversationTemplate(template="...")` — apply chat template

---

### LLM Integration (16+ Providers)

distilabel provides a uniform interface via `LLM` base class with `generate()` method.

**Full provider list:**

| Provider | Class | Key Features |
|----------|-------|-------------|
| Hugging Face Inference | `InferenceEndpointsLLM` | Serverless IEs, HF token auth, free tier |
| Local Transformers | `TransformersLLM` | CPU/GPU, device_map, torch_dtype, chat_template |
| OpenAI-compatible | `OpenAILLM` | Any OpenAI API-compatible endpoint |
| Azure OpenAI | `AzureOpenAILLM` | Azure-specific auth |
| LlamaCpp | `LlamaCppLLM` | GGUF models, n_ctx, n_gpu_layers |
| Ollama | `OllamaLLM` | Local Ollama server |
| Anthropic | `AnthropicLLM` | Claude models |
| Gemini | `VertexAILLM` | Google Vertex AI |
| Mistral | `MistralLLM` | Mistral API |
| Cohere | `CohereLLM` | Cohere API |
| Groq | `GroqLLM` | Groq LPU inference |
| Together | `TogetherLLM` | Together API |
| Anyscale | `AnyscaleLLM` | Anyscale endpoints |
| vLLM | `ClientvLLM` | vLLM serving |
| MLX | `MlxLLM` | Apple Silicon |
| LiteLLM | `LiteLLM` | Multi-provider proxy (100+ models) |
| Mixture of Agents | `MixtureOfAgentsLLM` | MoA pattern for improved quality |

**Key LLM runtime parameters:**
- `generation_kwargs` — dict of generation parameters (temperature, max_new_tokens, top_p, etc.)
- `structured_output` — pydantic model or JSON schema for constrained generation
- `cuda_devices` — GPU device placement string
- `use_magpie_template` — for magpie pre-query templates

**Zero-cost LLM strategies:**
1. `TransformersLLM` with small local models (0.5B–3B): free, private, no API costs
2. `InferenceEndpointsLLM` with HF free Inference API tier: free, rate-limited
3. `OllamaLLM` with local ollama: free with GGUF models
4. `LlamaCppLLM` with GGUF files: free, optimized for CPU

---

### Task Types (40+ Built-in)

#### SFT Data Generation
| Task | Description |
|------|------------|
| `TextGeneration` | Generate assistant responses from instructions — the most basic SFT task |
| `SelfInstruct` | Generate instruction-response pairs from seed topics (Wang et al.) |
| `MagpieGenerator` | Generate multi-turn conversations from a pre-query template |
| `Genstruct` | Generate instruction data from documents |
| `EvolInstruct` | Evolve/evaluate instruction complexity (WizardLM) |
| `EvolComplexity` | Complexity evolution variant |
| `EvolQuality` | Quality evolution variant |
| `URIAL` | Untuned LLM alignment via in-context learning |
| `InstructionBacktranslation` | Generate instructions from unlabelled text |

#### DPO/RLHF Preference Data
| Task | Description |
|------|------------|
| `UltraFeedback` | Multi-aspect LLM-as-judge feedback (helpfulness, honesty, safety, etc.) |
| `PairRM` | Pairwise reward model scoring |
| `RewardModelScore` | Score outputs using a reward model |
| `FormatChatGenerationDPO` | Format chat data for DPO training (chosen/rejected) |
| `FormatTextGenerationDPO` | Format text data for DPO training |
| `FormatChatGenerationSFT` | Format chat data for SFT training |
| `FormatTextGenerationSFT` | Format text data for SFT training |
| `PreferenceToArgilla` | Convert preferences to Argilla feedback format |

#### Evaluation & Scoring
| Task | Description |
|------|------------|
| `ComplexityScorer` | Score response complexity |
| `QualityScorer` | Score response quality |
| `PrometheusEval` | LLM-based evaluation (Prometheus framework) |
| `CLAIR` | Chain-of-thought LLM-as-Judge |
| `APIGenExecutionChecker` | Verify API execution correctness |
| `APIGenSemanticChecker` | Semantic validation of API calls |

#### Specialized Generation
| Task | Description |
|------|------------|
| `ChatGeneration` | Multi-turn chat generation |
| `TextClassification` | Text classification data generation |
| `GenerateEmbeddings` | Generate embeddings from text |
| `ImageGeneration` | Image generation (with image models) |
| `GenerateSentencePair` | Sentence pair (STS/NLI) data |
| `MonolingualTripletGenerator` | Triplet data for embedding training |
| `MathShepherdGenerator` | Math step-by-step data |
| `MathShepherdCompleter` | Complete partial math solutions |
| `BitextRetrievalGenerator` | Bitext mining data |
| `GenerateTextRetrievalData` | Retrieval dataset generation |
| `GenerateLongTextMatchingData` | Long-text pair matching |
| `GenerateShortTextMatchingData` | Short-text pair matching |
| `EmbeddingTaskGenerator` | Embedding task instruction generation |
| `StructuredGeneration` | Structured output (JSON/schema) generation |

---

### Data Flow Architecture

**Batch-based processing:**
- Steps process data in batches (default `input_batch_size=50`)
- Generator steps produce batches (default `batch_size=50`)
- Each batch is a `List[Dict[str, Any]]`
- Batches flow through the DAG via multiprocessing queues

**Step signature:**
```python
class MyStep(Step):
    @property
    def inputs(self) -> List[str]:
        return ["input_column"]
    
    @property
    def outputs(self) -> List[str]:
        return ["output_column"]
    
    def process(self, *inputs: StepInput) -> StepOutput:
        for batch in inputs:
            # batch is List[Dict[str, Any]]
            for row in batch:
                row["output_column"] = transform(row["input_column"])
            yield batch
```

**Column mappings:**
```python
# Rename columns before they enter the step
task = TextGeneration(
    llm=llm,
    input_mappings={"user_query": "instruction"},
    output_mappings={"generation": "response"},
)
```

---

### Distiset Output

`Pipeline.run()` returns a `Distiset` — a dict-like object where:
- Keys are leaf step names (usually the last step's name)
- Values are Hugging Face `datasets.Dataset` objects

**Distiset methods:**

| Method | Description |
|--------|------------|
| `push_to_hub(repo_id, private, token, generate_card)` | Push dataset to HF Hub |
| `save_to_disk(path, max_shard_size, num_shards)` | Save to local disk |
| `train_test_split(train_size, shuffle, seed)` | Split into train/test |
| `load_from_disk(path)` | Load from local disk |
| `keys() / values() / items()` | Dict-like access |
| `get(key)` | Access a specific leaf dataset |
| `pipeline_path / log_filename_path / artifacts_path` | Path attributes |

**Training data preparation flow:**
```
pipeline.run() → Distiset → .train_test_split() → .push_to_hub()
```

---

### Caching System

distilabel caches pipeline runs by default (`use_cache=True` in `pipeline.run()`):
- **Cache key:** Computed from step configuration + input data hash
- **Cache location:** `~/.cache/distilabel/` (or custom `cache_dir`)
- **Invalidation:** Any change to step parameters or input data invalidates the cache
- **Skip cache:** `pipeline.run(use_cache=False)` to force re-run
- **Benefits:** Repeated runs with same config = instant retrieval of previous results

---

### Runtime Parameters

Parameters can be overridden at runtime without rebuilding the pipeline:

```python
pipeline.run(parameters={
    "text_generation_0": {
        "llm": {
            "generation_kwargs": {"temperature": 0.9, "max_new_tokens": 512}
        }
    },
    "load_data_from_dicts_0": {
        "data": new_input_data,
    },
})
```

This allows reusing the same pipeline with different:
- Input data
- Generation parameters
- Batch sizes
- Model configurations

---

### StepResources (Parallelism)

Control compute resources per step:

```python
from distilabel.steps import StepResources

heavy_task = TextGeneration(
    llm=llm,
    resources=StepResources(
        replicas=2,      # 2 parallel copies
        cpus=4,          # 4 CPUs per replica
        gpus=1,          # 1 GPU per replica
        memory="8Gi",    # 8 GB memory per replica
    ),
)
```

Only available with RayPipeline. Local Pipeline uses single-process multiprocessing.

---

### Ray Distribution

Convert local pipeline to distributed:

```python
ray_pipeline = pipeline.ray(
    ray_head_node_url="auto",  # or specific Ray cluster URL
    ray_init_kwargs={"num_cpus": 8, "num_gpus": 2},
)
ray_pipeline.run(...)
```

Or build directly with RayPipeline:
```python
from distilabel.pipeline import RayPipeline

with RayPipeline(name="distributed") as pipeline:
    ...
```

---

### Custom Step Authoring

```python
from distilabel.steps import Step
from distilabel.steps.base import StepInput, StepOutput
from typing import List, Dict, Any

class TextFilterStep(Step):
    @property
    def inputs(self) -> List[str]:
        return ["text", "min_length"]
    
    @property
    def outputs(self) -> List[str]:
        return ["filtered_text"]
    
    def process(self, *inputs: StepInput) -> StepOutput:
        for batch in inputs:
            filtered = []
            for row in batch:
                if len(row["text"]) >= row["min_length"]:
                    row["filtered_text"] = row["text"]
                    filtered.append(row)
            yield filtered
```

For custom LLM-powered tasks:
```python
from distilabel.steps.tasks import Task
from distilabel.steps.tasks.base import RuntimeParameters

class CustomGrader(Task):
    llm: "LLM"  # injected LLM
    
    @property
    def inputs(self) -> List[str]:
        return ["question", "answer"]
    
    @property
    def outputs(self) -> List[str]:
        return ["grade", "feedback"]
    
    def format_input(self, input: Dict[str, Any]) -> str:
        return f"Question: {input['question']}\nAnswer: {input['answer']}\nGrade:"
    
    @property
    def template(cls) -> str:
        return "{{ question }}\n{{ answer }}"
```

---

### Real-World Patterns

#### Pattern 1: Self-Instruct for SFT Data
```python
with Pipeline(name="self-instruct-sft") as pipeline:
    # Seed topics from a small set
    loader = LoadDataFromDicts(data=[
        {"topic": "machine learning"},
        {"topic": "python programming"},
        {"topic": "history"},
    ])
    
    # Generate instructions from topics
    self_instruct = SelfInstruct(llm=llm)
    
    # Generate responses
    text_gen = TextGeneration(llm=llm)
    
    # Format for SFT
    formatter = FormatChatGenerationSFT()
    
    loader >> self_instruct >> text_gen >> formatter
```

#### Pattern 2: UltraFeedback for DPO Preference Data
```python
with Pipeline(name="ultrafeedback-dpo") as pipeline:
    loader = LoadDataFromHub(repo_id="my-dataset")
    
    # Generate 2 responses per instruction
    generator = TextGeneration(llm=llm, num_generations=2)
    
    # Score with UltraFeedback
    judge_llm = InferenceEndpointsLLM(model_id="mistralai/Mixtral-8x7B-Instruct-v0.1")
    ultrafeedback = UltraFeedback(
        llm=judge_llm,
        aspects=["helpfulness", "honesty", "safety"],
    )
    
    # Format for DPO
    dpo_format = FormatChatGenerationDPO()
    
    loader >> generator >> ultrafeedback >> dpo_format
```

#### Pattern 3: Magpie for Multi-turn Chat
```python
with Pipeline(name="magpie-chat") as pipeline:
    magpie = MagpieGenerator(
        llm=llm,
        max_turns=3,
        system_prompt="You are a helpful assistant.",
    )
    
    loader = LoadDataFromDicts(data=[
        {"pre_query": "User asked about..."},
    ])
    
    loader >> magpie
```

#### Pattern 4: Evaluation Pipeline
```python
with Pipeline(name="eval-pipeline") as pipeline:
    loader = LoadDataFromHub(repo_id="test-set")
    
    generator = TextGeneration(llm=llm)
    quality = QualityScorer(llm=judge_llm)
    complexity = ComplexityScorer(llm=judge_llm)
    
    loader >> generator
    generator >> quality
    generator >> complexity
```

---

### Push to Hub & Sharing

```python
distiset = pipeline.run(
    parameters={"text_generation_0": {"llm": {"generation_kwargs": {"temperature": 0.7}}}},
    dataset=dataset_batch,
    use_cache=True,
)

# Push to HF Hub
distiset.push_to_hub(
    repo_id="username/my-sft-dataset",
    private=False,
    generate_card=True,       # auto-generate dataset card
    include_script=True,      # include pipeline script
)

# Or save locally
distiset.save_to_disk("./my-dataset", num_shards=10)

# Split for training
train_ds, test_ds = distiset.train_test_split(train_size=0.9, shuffle=True, seed=42)
```

---

### Key Constraints & Best Practices

1. **Input columns must match step inputs** — use `input_mappings` to reconcile differences
2. **LLM context limits** — set `max_new_tokens` appropriately for the model
3. **Cache management** — delete `~/.cache/distilabel/` if cache gets corrupted
4. **Batching for speed** — larger `input_batch_size` reduces overhead but uses more memory
5. **Structured output** — pass a Pydantic model to `structured_output` for JSON-modes
6. **LLM failure handling** — steps should handle LLM generation failures gracefully
7. **Zero-cost priority** — use `TransformersLLM` with small models or `InferenceEndpointsLLM` with free HF Inference API

---

### Source
- distilabel v1.5.3 installed and introspected live on 2026-07-25
- API explored via Python introspection of all 16+ LLM providers
- All 40+ task types documented from `distilabel.steps.tasks`
- Pipeline DAG, Distiset, Step, and caching verified via live API calls

### Skill Created
`hf-distilabel-deep-dive/` — complete reference with SKILL.md (author: SakThai, license: MIT), pipeline architecture, full task catalog, LLM integration matrix, custom step authoring, and real-world patterns for SFT/DPO/RLHF data generation.
