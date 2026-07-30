# HF Learnings — Sentence Transformers Deep-Dive

## 2026-07-25: hf-sentence-transformers-training-deep-dive — Training API, Models Hub, Prompt Templates, Efficiency Backends & Advanced Patterns

### Summary
Deep-dive into the `sentence-transformers` v5.x training ecosystem — covering the full `SentenceTransformerTrainer` API (30+ loss functions, 10+ evaluators, training arguments, multi-dataset training, callbacks), prompt template system (`config_sentence_transformers.json`, `prompts` dict, `default_prompt_name`), model hub integration (`push_to_hub`, `save_pretrained`, model card metadata), efficiency backends (PyTorch, ONNX, OpenVINO with benchmarks), and advanced topics (Matryoshka embeddings, distillation, PEFT adapters, embedding quantization, distributed training with FSDP). Source: SBERT.net official docs, GitHub examples, HF package reference (July 2026).

### Key Concepts

#### 1. Training Architecture (v5.x+)

The `SentenceTransformerTrainer` replaces the old `model.fit()` API and follows the Hugging Face `transformers.Trainer` pattern with four to six components:

```
Training Components:
  Model       → SentenceTransformer or CrossEncoder
  Dataset     → datasets.Dataset or DatasetDict
  Loss        → One of 30+ loss functions
  Args        → SentenceTransformerTrainingArguments (optional)
  Evaluator   → One of 10+ evaluator types (optional)
  Callbacks   → Trainer callbacks (optional)
```

**Key difference from old API:** The Trainer handles batching, logging, checkpointing, evaluation, and push-to-hub automatically. Datasets use `datasets.Dataset` format — not raw lists of tuples.

**Basic training workflow:**
```python
from datasets import load_dataset
from sentence_transformers import (
    SentenceTransformer, SentenceTransformerTrainer,
    SentenceTransformerTrainingArguments, SentenceTransformerModelCardData,
)
from sentence_transformers.sentence_transformer.losses import MultipleNegativesRankingLoss
from sentence_transformers.sentence_transformer.training_args import BatchSamplers
from sentence_transformers.sentence_transformer.evaluation import TripletEvaluator

# 1. Load model
model = SentenceTransformer("microsoft/mpnet-base",
    model_card_data=SentenceTransformerModelCardData(
        language="en", license="apache-2.0",
        model_name="MPNet base trained on AllNLI triplets",
    ),
    model_kwargs={"torch_dtype": "float32"},
)

# 2. Load dataset
dataset = load_dataset("sentence-transformers/all-nli", "triplet")
train_dataset = dataset["train"].select(range(100_000))
eval_dataset = dataset["dev"]

# 3. Define loss
loss = MultipleNegativesRankingLoss(model)

# 4. Training args
args = SentenceTransformerTrainingArguments(
    output_dir="models/mpnet-base-all-nli-triplet",
    num_train_epochs=1,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    learning_rate=2e-5,
    warmup_steps=0.1,
    fp16=True,
    batch_sampler=BatchSamplers.NO_DUPLICATES,
    eval_strategy="steps",
    eval_steps=100,
    save_strategy="steps",
    save_steps=100,
    save_total_limit=2,
    logging_steps=100,
)

# 5. Evaluator
dev_evaluator = TripletEvaluator(
    anchors=eval_dataset["anchor"],
    positives=eval_dataset["positive"],
    negatives=eval_dataset["negative"],
    name="all-nli-dev",
)
dev_evaluator(model)  # Evaluate base model before training

# 6. Train
trainer = SentenceTransformerTrainer(
    model=model, args=args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    loss=loss,
    evaluator=dev_evaluator,
)
trainer.train()

# 7. Save & push
model.save_pretrained("models/mpnet-base-all-nli-triplet")
model.push_to_hub("my-org/mpnet-base-all-nli-triplet")
```

#### 2. Dataset Format Rules

Critical for loss function compatibility:

| Rule | Description |
|------|-------------|
| **Label column** | A column named `label`, `labels`, `score`, or `scores` is treated as the target |
| **Input columns** | All remaining columns are treated as inputs |
| **Column order matters** | Input columns must be ordered correctly for the loss function |
| **Extraneous columns** | Remove with `Dataset.remove_columns()` — otherwise they're treated as inputs |
| **Number of inputs** | Must match the loss function's required inputs (e.g., CoSENTLoss needs 2, TripletLoss needs 3) |

Example: A dataset with columns `["sentence1", "sentence2", "label"]` works with CoSENTLoss (2 inputs + 1 label). But `["good_answer", "bad_answer", "question"]` would NOT work with a triplet loss expecting (anchor, positive, negative) — use `Dataset.select_columns()` to reorder.

#### 3. All Loss Functions (30+)

The `sentence_transformers.sentence_transformer.losses` module includes:

| Loss | Inputs | Label | Best For |
|------|--------|-------|----------|
| `CoSENTLoss` | 2 texts | float score | Semantic Textual Similarity |
| `AnglELoss` | 2 texts | float score | Angle-optimized STS |
| `CosineSimilarityLoss` | 2 texts | float score | Cosine similarity training |
| `SoftmaxLoss` | 2 texts | class label | NLI classification |
| `MultipleNegativesRankingLoss` | (anchor, positive) | none | Information Retrieval, retrieval-style pairs |
| `MultipleNegativesSymmetricRankingLoss` | (anchor, positive) | none | Symmetric retrieval |
| `CachedMultipleNegativesRankingLoss` | (anchor, positive) | none | Large-batch MNRL with caching |
| `CachedMultipleNegativesSymmetricRankingLoss` | (anchor, positive) | none | Symmetric cached MNRL |
| `TripletLoss` | (anchor, positive, negative) | none | Triplet data |
| `BatchHardTripletLoss` | (anchor, positive, negative) | none | Hard triplet mining |
| `BatchHardSoftMarginTripletLoss` | (anchor, positive, negative) | none | Soft-margin triplets |
| `BatchAllTripletLoss` | (anchor, positive, negative) | none | All valid triplets |
| `BatchSemiHardTripletLoss` | (anchor, positive, negative) | none | Semi-hard triplets |
| `ContrastiveLoss` | 2 texts | binary label | Pair classification |
| `OnlineContrastiveLoss` | 2 texts | binary label | Online contrastive |
| `ContrastiveTensionLoss` | 2 texts | none | Self-supervised CT |
| `ContrastiveTensionLossInBatchNegatives` | 2 texts | none | CT with in-batch negatives |
| `GISTEmbedLoss` | 2 texts | float/class | Guided in-batch negatives |
| `CachedGISTEmbedLoss` | 2 texts | float/class | Cached GISTEmbed |
| `DenoisingAutoEncoderLoss` | corrupted text | original text | TSDAE (unsupervised) |
| `MegaBatchMarginLoss` | (anchor, positives, negatives) | none | Large-scale search |
| `MatryoshkaLoss` | wraps another loss | depends | Matryoshka embeddings |
| `Matryoshka2dLoss` | wraps another loss | depends | 2D Matryoshka |
| `AdaptiveLayerLoss` | wraps another loss | depends | Adaptive layer selection |
| `EmbedDistillLoss` | student+teacher | none | Knowledge distillation |
| `MSELoss` | 2 texts | none | Distillation (MSE on embeddings) |
| `MarginMSELoss` | 2 texts | none | Margin MSE distillation |
| `DistillKLDivLoss` | logits, target probs | none | KL divergence distillation |
| `GlobalOrthogonalRegularizationLoss` | with another loss | depends | Prevent dimension collapse |

**Loss modifiers:** `MatryoshkaLoss`, `Matryoshka2dLoss`, `AdaptiveLayerLoss`, `GlobalOrthogonalRegularizationLoss` wrap an existing loss to add functionality.

#### 4. TrainingArguments Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `output_dir` | (required) | Where to save checkpoints |
| `num_train_epochs` | 3 | Number of training epochs |
| `per_device_train_batch_size` | 8 | Batch size per device |
| `per_device_eval_batch_size` | 8 | Eval batch size per device |
| `learning_rate` | 5e-5 | Peak learning rate |
| `warmup_steps` | 0 | Linear warmup steps (can be float ratio) |
| `lr_scheduler_type` | "warmupconstant" | LR schedule type |
| `fp16` | False | Enable FP16 training |
| `bf16` | False | Enable BF16 training |
| `batch_sampler` | `BatchSamplers.UNIFORM` | `NO_DUPLICATES` recommended for MNRL-based losses |
| `multi_dataset_batch_sampler` | `PROPORTIONAL` | Sampling strategy for multi-dataset training |
| `eval_strategy` | "no" | Evaluation during training |
| `eval_steps` | None | Evaluate every N steps |
| `save_strategy` | "steps" | Checkpoint save strategy |
| `save_steps` | 500 | Save every N steps |
| `save_total_limit` | None | Max checkpoints to keep |
| `logging_steps` | 500 | Log every N steps |
| `push_to_hub` | False | Push model to Hub during training |
| `hub_model_id` | None | HF Hub repo name |
| `hub_strategy` | "every_save" | When to push to Hub |
| `hub_private_repo` | False | Private Hub repo |
| `report_to` | "none" | Logging backend (wandb, tensorboard) |
| `load_best_model_at_end` | False | Load best checkpoint when done |
| `metric_for_best_model` | None | Metric for best model selection |
| `gradient_accumulation_steps` | 1 | Gradient accumulation |
| `gradient_checkpointing` | False | Memory-efficient training |
| `optim` | "adamw_torch" | Optimizer |
| `auto_find_batch_size` | False | Auto-find max batch size |
| `prompts` | None | Dict of prompt_name → prompt_text |
| `router_mapping` | None | Routing for asymmetric models |
| `learning_rate_mapping` | None | Per-dataset LR multiplier |

#### 5. Evaluators (10+)

| Evaluator | Required Data | Use Case |
|-----------|--------------|----------|
| `EmbeddingSimilarityEvaluator` | (sentences1, sentences2, scores) | STS evaluation |
| `BinaryClassificationEvaluator` | (sentences1, sentences2, labels) | Pair classification |
| `TripletEvaluator` | (anchors, positives, negatives) | Triplet scoring |
| `InformationRetrievalEvaluator` | (queries, corpus, relevant_docs) | Retrieval metrics (MRR, NDCG, Recall) |
| `NanoBEIREvaluator` | None (auto-loads from Hub) | Zero-config benchmark |
| `RerankingEvaluator` | [{query, positive, negative}] | Cross-encoder reranking |
| `ParaphraseMiningEvaluator` | (sentences_map, duplicate_pairs) | Paraphrase detection |
| `TranslationEvaluator` | (lang1_sentences, lang2_sentences) | Cross-lingual alignment |
| `MSEEvaluator` | (source_sentences, teacher_model) | Distillation evaluation |
| `SequentialEvaluator` | List of evaluators | Combine multiple evals |
| `CrossEncoderRerankingEvaluator` | [{query, positive, negative}] | Cross-encoder reranking |
| `CrossEncoderNanoBEIREvaluator` | None | Cross-encoder zero-config |
| `ReciprocalRankFusionEvaluator` | (query, results, scores) | RRF fusion eval |

**Using evaluators with auto-loading data from HF Hub:**
```python
# These evaluators automatically load benchmark data from HF Hub:
from sentence_transformers.sentence_transformer.evaluation import (
    EmbeddingSimilarityEvaluator, NanoBEIREvaluator
)

# NanoBEIREvaluator needs NO DATA — auto-loads all NanoBEIR benchmarks
eval = NanoBEIREvaluator()
results = eval(model)  # Returns dict of dataset → metric scores

# EmbeddingSimilarityEvaluator can load from HF datasets
from datasets import load_dataset
stsb = load_dataset("sentence-transformers/stsb", split="validation")
eval = EmbeddingSimilarityEvaluator(
    sentences1=stsb["sentence1"],
    sentences2=stsb["sentence2"],
    scores=stsb["score"],
    main_similarity=SimilarityFunction.COSINE,
    name="sts-dev",
)
```

#### 6. Multi-Dataset Training

The Trainer natively supports training on multiple datasets simultaneously — each with its own loss function:

```python
from datasets import load_dataset
from sentence_transformers import SentenceTransformer, SentenceTransformerTrainer
from sentence_transformers.sentence_transformer.losses import (
    CoSENTLoss, MultipleNegativesRankingLoss, SoftmaxLoss
)

model = SentenceTransformer("google-bert/bert-base-uncased",
    model_kwargs={"torch_dtype": "float32"})

# Load multiple datasets
all_nli_pair = load_dataset("sentence-transformers/all-nli", "pair", split="train")
all_nli_class = load_dataset("sentence-transformers/all-nli", "pair-class", split="train")
stsb = load_dataset("sentence-transformers/stsb", split="train")

# Create DatasetDict with dataset → loss mapping
train_dataset = {
    "all-nli-pair": all_nli_pair,
    "all-nli-pair-class": all_nli_class,
    "stsb": stsb,
}
losses = {
    "all-nli-pair": MultipleNegativesRankingLoss(model),
    "all-nli-pair-class": SoftmaxLoss(model),
    "stsb": CoSENTLoss(model),
}

# PROPORTIONAL (default): samples proportionally to dataset size
# ROUND_ROBIN: equal sampling from each dataset
args = SentenceTransformerTrainingArguments(
    output_dir="bert-base-multi-task",
    multi_dataset_batch_sampler="proportional",
    ...

trainer = SentenceTransformerTrainer(
    model=model, args=args,
    train_dataset=train_dataset,
    loss=losses,
)
trainer.train()
```

**MultiDatasetBatchSamplers options:**
- `PROPORTIONAL` (default): sample in proportion to each dataset's size — all samples used, larger datasets seen more
- `ROUND_ROBIN`: fair sampling across datasets — some samples may be skipped, but each dataset is sampled equally

#### 7. Push to Hub & Model Card Metadata

**`SentenceTransformerModelCardData`** — controls metadata in the model card:
```python
from sentence_transformers import SentenceTransformerModelCardData

model_card_data = SentenceTransformerModelCardData(
    language="en",
    license="apache-2.0",
    model_name="My Custom Embedding Model",
    model_id="my-org/my-model",  # Override auto-detected model ID
)
```

**`push_to_hub()` method:**
```python
# After training
model.push_to_hub(
    repo_id="my-org/my-model",
    commit_message="Add fine-tuned embedding model",
    private=True,
    # Automatically saves: model.safetensors, config.json,
    # modules.json, tokenizer files, config_sentence_transformers.json
)
```

The `push_to_hub` training argument pushes checkpoints during training:
```python
args = SentenceTransformerTrainingArguments(
    output_dir="./output",
    push_to_hub=True,
    hub_model_id="my-org/my-model",
    hub_strategy="every_save",  # or "end", "checkpoint"
    hub_private_repo=True,
)
```

**Saved artifacts include:**
- `model.safetensors` — model weights (Safetensors format)
- `config.json` — transformer model config
- `modules.json` — ST module composition (Transformer → Pooling → Normalize)
- `config_sentence_transformers.json` — ST-specific config (prompts, default_prompt_name, etc.)
- Tokenizer files (tokenizer.json, tokenizer_config.json, vocab.txt, etc.)
- `README.md` — auto-generated model card
- Evaluation results and training state

#### 8. Prompt Templates System

Prompt templates prepend specific text to inputs during inference. Essential for models like E5, BGE, and INSTRUCTOR.

```python
from sentence_transformers import SentenceTransformer

# Initialize with prompts
model = SentenceTransformer("intfloat/multilingual-e5-large",
    prompts={
        "classification": "Classify the following text: ",
        "retrieval": "Retrieve semantically similar text: ",
        "clustering": "Identify the topic or theme based on the text: ",
    },
    default_prompt_name="retrieval",  # Used when no prompt specified
)

# Or set after initialization
model.prompts = {"query": "query: ", "passage": "passage: "}
model.default_prompt_name = "query"

# Use during inference
embeddings = model.encode(sentences)  # Uses default_prompt_name
query_embs = model.encode(queries, prompt_name="query")
passage_embs = model.encode(passages, prompt_name="passage")

# Or use inline prompt text
embeddings = model.encode(sentences, prompt="Represent this sentence: ")
```

**Storage in config_sentence_transformers.json:**
```json
{
  "prompts": {
    "query": "query: ",
    "passage": "passage: "
  },
  "default_prompt_name": "query"
}
```

Prompts are automatically saved with `model.save_pretrained()` and reloaded on `SentenceTransformer.load()`.

#### 9. Efficiency Backends

Three backends with different performance characteristics:

| Backend | Installation | Best For | Speedup vs PyTorch fp32 |
|---------|-------------|----------|------------------------|
| **PyTorch** | Default | Development, GPU training | 1× (baseline) |
| **ONNX** | `sentence-transformers[onnx]` | CPU inference, cross-platform | 2-4× on CPU |
| **OpenVINO** | `sentence-transformers[openvino]` | Intel CPU optimization | 3-5× on Intel CPU |

**Benchmarks (RTX 3090 GPU, i7-17300K CPU):**
- ONNX on GPU: ~1.2× faster than PyTorch fp32
- ONNX on CPU: ~3× faster than PyTorch fp32
- OpenVINO on Intel CPU: ~4× faster than PyTorch fp32
- PyTorch fp16: ~1.8× faster than PyTorch fp32 on GPU

**ONNX Export & Quantization:**
```python
# Load with ONNX backend (auto-converts if needed)
model = SentenceTransformer("all-MiniLM-L6-v2", backend="onnx")

# Dynamic quantization to int8
from sentence_transformers.backends import export_dynamic_quantized_onnx_model
export_dynamic_quantized_onnx_model(
    model=model,
    quantization_config="avx512",  # or "arm64", "avx2", "avx512_vnni"
    model_name_or_path="my-org/all-MiniLM-L6-v2-qint8",
    push_to_hub=True,
    file_suffix="qint8_quantized",
)
```

**OpenVINO Export:**
```python
model = SentenceTransformer("all-MiniLM-L6-v2", backend="openvino")
# Auto-converts to OpenVINO IR format on first use
# Cached for subsequent loads
```

**Important:** Both ONNX and OpenVINO backends only convert the Transformer component. Pooling and normalization must be applied separately if using the exported model outside of sentence-transformers.

#### 10. Matryoshka Embeddings

Matryoshka embeddings allow truncating embedding dimensions at inference time — a single model produces embeddings usable at any dimensionality.

```python
from sentence_transformers.sentence_transformer.losses import (
    MatryoshkaLoss, MultipleNegativesRankingLoss,
)

base_loss = MultipleNegativesRankingLoss(model)
loss = MatryoshkaLoss(model, base_loss,
    min_dims=64, max_dims=768, step_dims=64)

trainer = SentenceTransformerTrainer(
    model=model, args=args,
    train_dataset=train_dataset,
    loss=loss,
)
trainer.train()

# At inference, use any dimension
embeddings_768 = model.encode(texts)           # Full 768d
embeddings_256 = model.encode(texts, truncate_dim=256)  # Truncated to 256d
embeddings_64  = model.encode(texts, truncate_dim=64)   # Truncated to 64d
```

**Matryoshka2dLoss** extends this with 2D truncation (dimension + adaptive layer pruning).

**AdaptiveLayerLoss** allows selecting which transformer layers to use at inference time — trade off speed vs quality without retraining.

#### 11. Model Distillation

```python
from sentence_transformers.sentence_transformer.losses import MSELoss

# Teacher model (large, accurate)
teacher = SentenceTransformer("all-mpnet-base-v2")

# Student model (small, fast)
student = SentenceTransformer("all-MiniLM-L6-v2")

# Distill: minimize MSE between teacher and student embeddings
loss = MSELLoss(student)

# Alternative: MarginMSELoss (margin-aware distillation)
# Alternative: DistillKLDivLoss (KL divergence on logits)
```

#### 12. PEFT Adapter Training

```python
# Train a LoRA adapter on top of a pretrained SentenceTransformer
from sentence_transformers import SentenceTransformer
from sentence_transformers.sentence_transformer.training_args import BatchSamplers

model = SentenceTransformer("microsoft/mpnet-base",
    adapter_name="default",  # Initialize adapter
    model_kwargs={"torch_dtype": "float32"},
)

# Train with adapter (only adapter weights are updated)
trainer = SentenceTransformerTrainer(
    model=model, args=args,
    train_dataset=train_dataset,
    loss=loss,
)
trainer.train()

# Save only the adapter
model.save_pretrained("./adapter-output")
model.push_to_hub("my-org/mpnet-base-all-nli-adapter")

# Load adapter later
model = SentenceTransformer("microsoft/mpnet-base")
model.load_adapter("my-org/mpnet-base-all-nli-adapter")
```

#### 13. Embedding Quantization (Post-Training)

Binary and int8 quantization of output embeddings for cheaper storage and faster retrieval:

- **Binary quantization:** Compress float32 to 1-bit → 32× smaller, use Hamming distance
- **Scalar int8 quantization:** Compress to 8-bit → 4× smaller, with minimal accuracy loss

Available via `model.encode(..., precision="ubinary")` or by using the `embedding_quantization` package:
```python
pip install "sentence-transformers[dev]"  # includes embedding_quantization extras
```

#### 14. Distributed Training with FSDP

```python
from sentence_transformers import SentenceTransformerTrainer

# With FSDP (Fully Sharded Data Parallel)
trainer = SentenceTransformerTrainer(
    model=model,
    args=SentenceTransformerTrainingArguments(
        output_dir="./output",
        fsdp=True,
        fsdp_config={
            "transformer_layer_cls": "BertLayer",  # or model-specific
            "sharding_strategy": "FULL_SHARD",      # or HYBRID_SHARD
        },
    ),
    train_dataset=train_dataset,
    loss=loss,
)
```

#### 15. Multimodal Models (v5.4+)

sentence-transformers v5.4+ supports vision-language models (VLMs), audio, and video:

```python
# VLM approach (single backbone, multiple modalities)
model = SentenceTransformer("google/siglip2-base-patch16-224",
    model_kwargs={"torch_dtype": "float32"}
)
print(model.modalities)  # ['text', 'image', 'video', 'message']
print(model.supports("image"))  # True

# Router approach (separate encoders per modality)
from sentence_transformers.base.modules import Transformer, Pooling, Dense, Router

text_encoder = Transformer("sentence-transformers/all-mpnet-base-v2")
image_encoder = Transformer("google/siglip2-base-patch16-224")

# Compose with Router
router = Router({
    "text": text_encoder,
    "image": image_encoder,
})
model = SentenceTransformer(modules=router)
```

#### 16. Loss Overview Table (Complete)

The full loss table from docs:

| Loss Function | # Inputs | Requires Label | Label Type |
|--------------|----------|---------------|------------|
| BatchAllTripletLoss | 3 | ❌ | - |
| BatchHardSoftMarginTripletLoss | 3 | ❌ | - |
| BatchHardTripletLoss | 3 | ❌ | - |
| BatchSemiHardTripletLoss | 3 | ❌ | - |
| ContrastiveLoss | 2 | ✅ | binary (0/1) |
| OnlineContrastiveLoss | 2 | ✅ | binary (0/1) |
| ContrastiveTensionLoss | 2 | ❌ | - |
| ContrastiveTensionLossInBatchNegatives | 2 | ❌ | - |
| CoSENTLoss | 2 | ✅ | float |
| AnglELoss | 2 | ✅ | float |
| CosineSimilarityLoss | 2 | ✅ | float |
| DenoisingAutoEncoderLoss | 1 | ❌ | - |
| GISTEmbedLoss | 2 | ✅ | float or binary |
| CachedGISTEmbedLoss | 2 | ✅ | float or binary |
| GlobalOrthogonalRegularizationLoss | wraps | depends | - |
| EmbedDistillLoss | 2 | ❌ | - |
| MSELoss | 2 | ❌ | - |
| MarginMSELoss | 2 | ❌ | - |
| MatryoshkaLoss | wraps | depends | - |
| Matryoshka2dLoss | wraps | depends | - |
| AdaptiveLayerLoss | wraps | depends | - |
| MegaBatchMarginLoss | 3+ | ❌ | - |
| MultipleNegativesRankingLoss | 2 | ❌ | - |
| CachedMultipleNegativesRankingLoss | 2 | ❌ | - |
| MultipleNegativesSymmetricRankingLoss | 2 | ❌ | - |
| CachedMultipleNegativesSymmetricRankingLoss | 2 | ❌ | - |
| SoftmaxLoss | 2 | ✅ | class label |
| TripletLoss | 3 | ❌ | - |
| DistillKLDivLoss | 2 | ❌ | - |

### Skill Alignment

This deep-dive expands the existing `mlops/hf-sentence-transformers` skill's reference knowledge. The skill's SKILL.md already covers basic usage (SentenceTransformer, CrossEncoder, SparseEncoder, MTEB leaderboard, pitfalls). This learnings file adds the advanced training infrastructure (Trainer API, loss functions, evaluators), prompt template system, model hub integration, efficiency backends, and all the advanced patterns above.

### Key Insights

1. **Training API is now Hugging Face-native** — `SentenceTransformerTrainer` mirrors `transformers.Trainer` with `TrainingArguments`, `TrainerCallback`, and HF Datasets integration. Old `model.fit()` is deprecated.
2. **30+ loss functions** — Choose based on data format, not model architecture. The `Dataset Format` → `Loss Overview` docs are the definitive guide.
3. **`BatchSamplers.NO_DUPLICATES` is critical for in-batch negative losses** — without it, MNRL and similar losses underperform because duplicate positives appear in the same batch.
4. **Multi-dataset training with multiple losses** — The top-ranked embedding models use this technique (Huang et al., E5-mistral, etc.) — mixing MNRL, CoSENT, and Softmax across datasets.
5. **Prompt templates are now first-class** — Saved in `config_sentence_transformers.json`, automatically loaded, and accessible via `model.encode(prompt_name=...)` or `model.encode(prompt=...)`.
6. **ONNX/OpenVINO backends are drop-in** — Change `backend=` parameter, get 2-4× CPU speedup. No code changes needed for the rest of the pipeline.
7. **Matryoshka embeddings eliminate retraining** for different output dimensions — one model serves all use cases from 64d to 768d.
8. **push_to_hub is fully integrated** with `TrainingArguments` — models can be pushed during or after training, with full metadata via `SentenceTransformerModelCardData`.
9. **`NanoBEIREvaluator` requires zero data** — auto-loads all NanoBEIR benchmarks from the Hub for zero-config evaluation.
10. **All zero-cost compatible** — Training works on CPUs (slow but free), ONNX/OpenVINO backends run on CPU, embedding quantization reduces storage costs. For free GPU training, use HF Spaces with ZeroGPU or HF Jobs trial credits.
