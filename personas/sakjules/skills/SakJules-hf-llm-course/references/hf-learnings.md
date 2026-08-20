# HF Learnings — LLM/NLP Course Comprehensive Deep Dive

## 2026-07-25: hf-llm-course-comprehensive-deep-dive — Complete Curriculum & Implementation Guide (Topic #248)

### Summary
Comprehensive deep-dive into the Hugging Face LLM/NLP Course (https://huggingface.co/learn/llm-course) — the flagship educational resource covering the full transformer model lifecycle. The course spans 8 chapters and ~70 units across natural language processing, transformer architectures, model fine-tuning, dataset processing, tokenizer training, and production deployment. It is the primary on-ramp for the entire HF ecosystem.

### Source
- Course homepage: https://huggingface.co/learn/llm-course
- Course notebooks: https://github.com/huggingface/notebooks/tree/main/course
- Transformers docs: https://huggingface.co/docs/transformers
- Datasets docs: https://huggingface.co/docs/datasets
- Tokenizers docs: https://huggingface.co/docs/tokenizers
- Accelerate docs: https://huggingface.co/docs/accelerate
- Hub docs: https://huggingface.co/docs/hub

### Course Architecture

The HF LLM Course is a **progressive curriculum** that takes learners from zero NLP knowledge to production-ready transformer competence. It is designed around five core HF libraries:
1. **transformers** (v5.x) — model loading, inference, fine-tuning, architecture zoo
2. **datasets** (v5.x) — dataset access, processing, streaming, FAISS search
3. **tokenizers** (latest) — fast tokenization, BPE/WordPiece/Unigram training
4. **accelerate** — distributed training across GPUs/TPUs without boilerplate
5. **huggingface_hub** — model sharing, discovery, collaboration

The course follows this progression:
```
Setup → Theory → Usage → Fine-tuning → Sharing → Data → Tokenizers → Tasks
 (Ch0)   (Ch1)   (Ch2)     (Ch3)       (Ch4)    (Ch5)    (Ch6)      (Ch7)
```

---

### Chapter 0: Setup & Environment (1 unit)

**Unit 1 — Introduction:** Environment setup guide covering:
- Google Colab (free GPU, no install needed, good for quick starts)
- Python virtual environments (`python -m venv`, `conda`)
- Installing core libraries: `pip install transformers datasets tokenizers accelerate gradio`
- Jupyter notebook configuration
- **Checkpoint**: Learners verify their environment can import `transformers` and run inference

---

### Chapter 1: Introduction to Transformers & LLMs (11 units)

This chapter provides the theoretical foundation for the entire course.

**Unit 1 — Introduction:** Course roadmap, what transformers are, why they matter.

**Unit 2 — NLP and Large Language Models:** Core NLP concepts:
- Traditional NLP (rule-based, statistical, word vectors) vs modern deep learning
- The rise of the Transformer architecture (Vaswani et al., 2017)
- Language modeling as next-token prediction
- Scale drives emergent abilities in LLMs (>1B params)
- **Key distinction**: Encoder-only (BERT), decoder-only (GPT), encoder-decoder (T5)

**Unit 3 — Transformers, What Can They Do?** Pipeline API showcase:
```python
from transformers import pipeline
classifier = pipeline("sentiment-analysis")
classifier("I loved this movie!")  # → [{'label': 'POSITIVE', 'score': 0.999}]
```
Other pipelines demonstrated: text-generation, fill-mask, ner, question-answering, summarization, translation, zero-shot-classification.

**Unit 4 — How Do Transformers Work?** Core architecture concepts:
- Self-attention mechanism (Q,K,V projections, scaled dot-product attention)
- Multi-head attention (parallel attention heads, concatenation, projection)
- Positional encodings (absolute sinusoidal, learned, RoPE)
- Residual connections and layer normalization
- Feed-forward blocks (MLPs with ReLU/GELU)
- **Visual**: The original "Attention Is All You Need" encoder-decoder diagram

**Unit 5 — How 🤗 Transformers Solve Tasks:** The model head architecture:
- Transformer backbone (shared) + task-specific head (replaceable)
- **Model types**:
  - `AutoModel` — base backbone without head (for embeddings/extraction)
  - `AutoModelForSequenceClassification` — classification head
  - `AutoModelForTokenClassification` — per-token head (NER, POS)
  - `AutoModelForQuestionAnswering` — span-prediction head
  - `AutoModelForCausalLM` — language modeling head (GPT-style)
  - `AutoModelForMaskedLM` — masked language modeling head (BERT-style)
  - `AutoModelForSeq2SeqLM` — encoder-decoder with LM head (T5-style)
- The `AutoModel` API: model selection by checkpoint, configuration injection

**Unit 6 — Transformer Architectures:** Comparing the three families:
| Architecture | Example | Training Objective | Best For |
|---|---|---|---|
| Encoder-only | BERT, RoBERTa, DeBERTa | Masked LM | Classification, NER, QA |
| Decoder-only | GPT-2, Llama, Mistral | Causal LM | Generation, Chat, Code |
| Encoder-Decoder | T5, BART, Pegasus | Span Corruption | Translation, Summarization |

- Prefix LM (e.g., ChatGLM) as a hybrid variant
- MoE (Mixture of Experts) architectures (e.g., Mixtral 8x7B)

**Unit 7 — Ungraded Quiz:** Self-assessment on chapter 1 concepts.

**Unit 8 — Deep Dive into Text Generation Inference with LLMs:**
- Autoregressive generation: token-by-token with KV cache
- Decoding strategies visualized:
  - Greedy: `do_sample=False, num_beams=1` — fastest, repetitive
  - Beam search: `num_beams=4+` — higher quality, slower
  - Sampling: `do_sample=True, temperature=0.7` — creative
  - Top-k sampling: `top_k=50` — filters to k most probable
  - Top-p (nucleus) sampling: `top_p=0.9` — filters to cumulative probability mass
  - Contrastive search: `penalty_alpha=0.6` — balance repetition vs. diversity
- `Temperature` scaling: lower = sharper distribution, higher = more uniform
- `max_new_tokens` vs `max_length`: **Always use `max_new_tokens`** in v5.x
- `generate()` API parameters reference

**Unit 9 — Bias and Limitations:**
- Training data bias: gender, race, cultural skews in downstream outputs
- Stereotype amplification from web-crawled data
- Hallucination: confident but incorrect generations
- Lack of true understanding (stochastic parrot debate)
- Mitigation strategies: dataset curation, RLHF, prompt engineering, output filtering
- **Ethical responsibility**: always evaluate model outputs, never trust blindly

**Unit 10 — Summary:** Key takeaways from chapter 1.

**Unit 11 — Exam Time!** Certification quiz for chapter 1.

---

### Chapter 2: Using 🤗 Transformers (9 units)

The hands-on "how to use transformers" chapter.

**Unit 1 — Introduction:** Chapter overview.

**Unit 2 — Behind the Pipeline:** What `pipeline()` actually does:
1. **AutoModelForXxx** — loads the appropriate model class from checkpoint
2. **AutoTokenizer** — loads and configures the tokenizer
3. **Preprocessing** — tokenize → convert to tensors → move to device
4. **Forward pass** — model inference, returns logits
5. **Postprocessing** — softmax/argmax → label mapping → human-readable output
- Manual pipeline implementation walking through each step

**Unit 3 — Models:** Deep dive into `AutoModel` and configuration:
```python
from transformers import AutoConfig, AutoModel
config = AutoConfig.from_pretrained("bert-base-cased")
model = AutoModel.from_config(config)  # random weights
# vs
model = AutoModel.from_pretrained("bert-base-cased")  # pretrained weights
```
- `save_pretrained()` / `from_pretrained()` serialization
- Configuration object: `hidden_size`, `num_attention_heads`, `num_hidden_layers`
- Cache management: `~/.cache/huggingface/hub/`
- Transformers v5.x architecture registry: model loading by architecture tag

**Unit 4 — Tokenizers:** The bridge between text and model:
- Word-based: simple but large vocab, OOV problems
- Character-based: tiny vocab but very long sequences
- Subword-based **(best of both worlds)**:
  - **BPE** (GPT-2, RoBERTa): merges frequent character pairs iteratively
  - **WordPiece** (BERT): merges by maximizing likelihood
  - **Unigram** (XLNet, ALBERT): starts with large vocab, prunes
- `AutoTokenizer.from_pretrained()` — always use the model's own tokenizer
- Special tokens: `[CLS]`, `[SEP]`, `[PAD]`, `[UNK]`, `[MASK]`
- Tokenizer output: `input_ids`, `attention_mask`, `token_type_ids` (BERT)

**Unit 5 — Handling Multiple Sequences:** Batching and padding:
- Padding: pad sequences to equal length with `padding=True`
- Truncation: cap at model maximum with `truncation=True`
- `return_tensors="pt"` (PyTorch), `"tf"` (TensorFlow)
- Dynamic padding vs fixed padding: memory vs. performance trade-off
- Attention mask: tells model which tokens are real vs. padding

**Unit 6 — Putting It All Together:** End-to-end workflow:
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

checkpoint = "distilbert-base-uncased-finetuned-sst-2-english"
tokenizer = AutoTokenizer.from_pretrained(checkpoint)
model = AutoModelForSequenceClassification.from_pretrained(checkpoint)

inputs = tokenizer(["I love this!", "This was terrible."], padding=True, 
                   truncation=True, return_tensors="pt")
outputs = model(**inputs)
predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
```

**Unit 7 — Basic Usage Completed!** Checkpoint/review.

**Unit 8 — Optimized Inference Deployment:**
- **ONNX Runtime**: `transformers.onnx` export, optimized CPU inference
- **BetterTransformer**: PyTorch-native fastpath for attention (SDPA)
- **Flash Attention 2**: memory-efficient attention for long sequences
- **vLLM integration**: PagedAttention for production LLM serving
- **Quantization**: `bitsandbytes` 4/8-bit, GPTQ, AWQ, GGUF
- **Text Generation Inference (TGI)**: HF's production-grade inference server
- Static quantization vs dynamic quantization trade-offs

**Unit 9 — End-of-chapter quiz.**

---

### Chapter 3: Fine-tuning a Pretrained Model (7 units)

The practical fine-tuning chapter.

**Unit 1 — Introduction:** Why fine-tune? Adapting general models to specific tasks.

**Unit 2 — Processing the Data:** Loading and preparing datasets:
```python
from datasets import load_dataset
raw_datasets = load_dataset("imdb")
```
- Train/test splits, shuffling, selecting subsets
- Tokenization with `.map()`:
  ```python
  def tokenize_function(examples):
      return tokenizer(examples["text"], truncation=True)
  tokenized_datasets = raw_datasets.map(tokenize_function, batched=True)
  ```
- Dynamic padding in collation vs static padding
- Data collators: `DataCollatorWithPadding`, `DataCollatorForLanguageModeling`

**Unit 3 — Fine-tuning with the Trainer API:**
```python
from transformers import Trainer, TrainingArguments

training_args = TrainingArguments(
    output_dir="./results",
    evaluation_strategy="epoch",
    per_device_train_batch_size=16,
    per_device_eval_batch_size=64,
    num_train_epochs=3,
    weight_decay=0.01,
    push_to_hub=True,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["test"],
    tokenizer=tokenizer,
    data_collator=data_collator,
)
trainer.train()
```
- TrainingArguments breakdown: learning rate, warmup, weight decay, logging, saving
- `Trainer` features: gradient accumulation, mixed precision (fp16/bf16), logging, callbacks
- `push_to_hub=True` uploads model + tokenizer automatically after training

**Unit 4 — A Full Training Loop:** Custom training loop (no Trainer):
```python
from accelerate import Accelerator
accelerator = Accelerator()
optimizer = AdamW(model.parameters(), lr=5e-5)
model, optimizer, dataloader = accelerator.prepare(model, optimizer, dataloader)
```
- Manual loss computation, backward pass, optimizer step
- Gradient accumulation loop
- Mixed precision with `accelerator`
- When to use custom loops vs Trainer: Trainer handles 80% of use cases

**Unit 5 — Understanding Learning Curves:**
- Training loss vs evaluation loss
- Overfitting detection: eval loss rising while train loss falls
- Learning rate schedules: linear, cosine, constant
- Warmup steps: prevent early instability
- Choosing the right learning rate (typically 2e-5 to 5e-5 for fine-tuning)

**Unit 6 — Fine-tuning, Check!** Milestone review.

**Unit 7 — End-of-chapter Certificate:** Certification quiz for chapter 3.

---

### Chapter 4: Sharing Models & Tokenizers (6 units)

The Hub integration chapter.

**Unit 1 — The Hugging Face Hub:** Complete Hub orientation:
- What the Hub is: model repository, dataset repository, Space hosting
- Repository structure: `config.json`, `pytorch_model.bin`, tokenizer files, `README.md`
- Browsing models: tags, pipelines, task filters, sorting by downloads/trending
- **Security**: HF security scanning on every push, secret scanning, malware detection
- Free hosting for public models, gated repos for private/restricted access

**Unit 2 — Using Pretrained Models from the Hub:**
- Checkpoint naming convention: `username/model-name` or `organization/model-name`
- Loading from any revision: `from_pretrained("bert-base-cased", revision="v1.0")`
- Loading specific cache location: `cache_dir="/custom/path"`
- Model card YAML: license, dataset, metrics, widget examples
- Using `huggingface_hub` library's `list_models()`, search filters

**Unit 3 — Sharing Pretrained Models:**
```python
from transformers import AutoModel, AutoTokenizer

model = AutoModel.from_pretrained("bert-base-cased")
# ... fine-tune ...
model.save_pretrained("./my-finetuned-model")
tokenizer.save_pretrained("./my-finetuned-model")
# Then upload via push_to_hub or hub.upload_folder()
model.push_to_hub("my-finetuned-model")
tokenizer.push_to_hub("my-finetuned-model")
```
- Using `push_to_hub` from Trainer (automatic after training)
- Programmatic upload with `huggingface_hub`:
  ```python
  from huggingface_hub import HfApi
  api = HfApi()
  api.create_repo("my-finetuned-model")
  api.upload_folder(folder_path="./my-finetuned-model", repo_id="username/my-finetuned-model")
  ```
- Version control: each push creates a commit, `main` branch always latest

**Unit 4 — Building a Model Card:**
- Why model cards matter: discoverability, reproducibility, ethical transparency
- YAML frontmatter in `README.md`:
  ```yaml
  ---
  language: en
  license: mit
  tags:
  - text-classification
  - sentiment-analysis
  datasets:
  - imdb
  metrics:
  - accuracy
  ---
  ```
- Widget configuration for in-browser demos
- Pipeline tag selection for correct inference API routing
- Writing a good model card: intended use, limitations, training details, evaluation results

**Unit 5 — Part 1 Completed!** Ceremonial Part 1 completion milestone (Chapters 1-4).

**Unit 6 — End-of-chapter quiz.**

---

### Chapter 5: The 🤗 Datasets Library (8 units)

Deep dive into the HF Datasets library (now v5.x).

**Unit 1 — Introduction:** What Datasets provides: unified access to 100K+ datasets, memory-mapped Arrow, streaming.

**Unit 2 — What If My Dataset Isn't on the Hub?** Loading from local files:
```python
from datasets import load_dataset
# CSV
dataset = load_dataset("csv", data_files="my_file.csv")
# JSON Lines
dataset = load_dataset("json", data_files="my_file.jsonl")
# Text files
dataset = load_dataset("text", data_files="my_file.txt")
# Parquet
dataset = load_dataset("parquet", data_files="my_file.parquet")
```
- Automatic file format detection
- Splitting: `data_files={"train": "train.csv", "test": "test.csv"}`

**Unit 3 — Time to Slice and Dice:** Dataset manipulation:
```python
dataset = load_dataset("imdb")
# Select subsets
dataset["train"].select(range(1000))
# Shuffle
dataset["train"].shuffle(seed=42)
# Train/test split
dataset["train"].train_test_split(test_size=0.2)
# Rename/remove columns
dataset = dataset.rename_column("label", "labels")
dataset = dataset.remove_columns(["text"])
# Flatten nested structures
dataset.flatten()
```
- Dataset indexing: integer index, slices, boolean masks
- Dataset features: Arrow schema, type casting

**Unit 4 — Big Data? 🤗 Datasets to the Rescue!** Memory-efficient processing:
- **Apache Arrow backend**: zero-copy reads, memory mapping
- **Streaming mode**: `load_dataset(..., streaming=True)` — no local storage
- **`.map()` with batched=True**: process in chunks, returns IterableDataset
- **`.filter()`** with streaming: filter without loading all data
- **`.take(n)`**: grab first n samples from a streaming dataset
- **Shuffling in streaming**: buffer-based shuffle with `shuffle(buffer_size=1000)`
- **Parquet format**: columnar storage, efficient for selective column reads
- Multi-shard shuffling (datasets v5.0): `max_buffer_input_shards=10`

**Unit 5 — Creating Your Own Dataset:** Dataset builder API:
```python
from datasets import Dataset, DatasetDict, Features, Value, ClassLabel

features = Features({
    "text": Value("string"),
    "label": ClassLabel(names=["neg", "pos"]),
})
dataset = Dataset.from_dict({"text": [...], "label": [...]}, features=features)
dataset.push_to_hub("username/my-dataset")
```
- `Dataset.from_generator()` for memory-efficient construction
- DatasetDict for train/validation/test splits
- Feature types: `Value`, `ClassLabel`, `Sequence`, `Array2D`, `Image`, `Audio`

**Unit 6 — Semantic Search with FAISS:** Embedding-based search:
```python
dataset = load_dataset("squad", split="train")
dataset = dataset.map(lambda x: {"embeddings": embed_fn(x["context"])})
dataset.add_faiss_index(column="embeddings")
scores, samples = dataset.get_nearest_examples("embeddings", query_embedding, k=5)
```
- `add_faiss_index()` — builds FAISS index from an embedding column
- `get_nearest_examples()` — queries the index
- `save_faiss_index()` / `load_faiss_index()` for persistent indexes
- Use cases: RAG retrieval, duplicate detection, semantic clustering

**Unit 7 — 🤗 Datasets, Check!** Milestone review.

**Unit 8 — End-of-chapter quiz.**

---

### Chapter 6: The 🤗 Tokenizers Library (10 units)

Deep dive into fast tokenization.

**Unit 1 — Introduction:** Why Tokenizers exists: speed (Rust backend), training capability, full pipeline control.

**Unit 2 — Training a New Tokenizer from an Old One:**
```python
from transformers import AutoTokenizer
from datasets import load_dataset

old_tokenizer = AutoTokenizer.from_pretrained("gpt2")
dataset = load_dataset("text", data_files="my_corpus.txt", split="train")

def batch_iterator(batch_size=1000):
    for i in range(0, len(dataset), batch_size):
        yield dataset[i : i + batch_size]["text"]

new_tokenizer = old_tokenizer.train_new_from_iterator(
    batch_iterator(), vocab_size=25000
)
new_tokenizer.save_pretrained("./my-tokenizer")
```
- `train_new_from_iterator()` — trains on arbitrary text iterator
- Vocabulary size selection: trade-off between coverage and sequence length
- Adding new tokens without full retraining: `tokenizer.add_tokens(list_of_new_tokens)`

**Unit 3 — Fast Tokenizers' Special Powers:**
- Rust implementation: 50x faster than Python-only (slow) tokenizers
- **Offset mapping**: word → character span mapping
  ```python
  encoding = tokenizer("Hello world!", return_offsets_mapping=True)
  encoding.offset_mapping()  # → [(0, 5), (6, 11)]
  ```
- **Word IDs**: mapping token → original word index
- **Overflow handling**: `return_overflowing_tokens=True` for long document processing
- **Fast tokenizer methods**: `.encode()`, `.encode_batch()`, `.decode()`, `.decode_batch()`
- Batch encoding with overflow: `tokenizer(examples["text"], truncation=True, return_overflowing_tokens=True)`

**Unit 4 — Normalization and Pre-tokenization:**
- **Normalization**: NFKC unicode normalization, lowercasing, accent stripping
- **Pre-tokenization**: splitting text into "words" before subword splitting
  - BPE (GPT-2): regex `\p{L}+|\p{N}+|[^\s\p{L}\p{N}]+\s*`
  - BERT: `Wordpiece` with whitespace splitting
  - Llama: `ByteLevel` with BPE
- Pre-tokenizer configuration in the tokenizer object

**Unit 5 — Byte-Pair Encoding (BPE) Tokenization:**
- Used by: GPT-2, GPT-4, RoBERTa, Llama, Mistral
- Algorithm:
  1. Start with character vocabulary
  2. Count all adjacent byte/character pairs
  3. Merge most frequent pair into a new token
  4. Repeat until target vocab size reached
- **Byte-level BPE** (GPT-2, Llama): base alphabet is bytes (256 tokens), can encode ANY text without unknown tokens
- GPT-2 vocab: 50,257 tokens (50,256 BPE merges + 1 special token)

**Unit 6 — WordPiece Tokenization:**
- Used by: BERT, DistilBERT, Electra
- Algorithm: Starts with character vocab, merges to maximize training likelihood
- Key difference from BPE: merges by likelihood gain, not frequency
- `##` prefix: marks continuation tokens (e.g., "playing" → "play" + "##ing")

**Unit 7 — Unigram Tokenization:**
- Used by: XLNet, ALBERT, T5
- Algorithm:
  1. Start with large vocabulary (all characters + common substrings)
  2. Train unigram language model
  3. Remove tokens that have the smallest loss increase
  4. Repeat until target vocab size
- Subword regularization: multiple segmentation paths during training for robustness
- Probabilistic tokenization: same text can produce different tokenizations

**Unit 8 — Building a Tokenizer, Block by Block:**
```python
from tokenizers import Tokenizer, models, normalizers, pre_tokenizers, decoders, trainers

tokenizer = Tokenizer(models.BPE())
tokenizer.normalizer = normalizers.NFKC()
tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=True)
tokenizer.decoder = decoders.ByteLevel()

trainer = trainers.BpeTrainer(vocab_size=30000, special_tokens=["<s>", "<pad>", "</s>", "<unk>", "<mask>"])
tokenizer.train_from_iterator(training_corpus, trainer=trainer)

# Convert to Transformers-compatible
from transformers import PreTrainedTokenizerFast
fast_tokenizer = PreTrainedTokenizerFast(tokenizer_object=tokenizer)
```
- Tokenizer building blocks: `normalizers`, `pre_tokenizers`, `model`, `trainer`, `post_processor`, `decoder`
- Post-processing: adding special tokens (CLS, SEP), template formatting

**Unit 9 — Tokenizers, Check!** Milestone review.

**Unit 10 — End-of-chapter quiz.**

---

### Chapter 7: Main NLP Tasks (9 units)

Applying everything to real NLP tasks.

**Unit 1 — Introduction:** Overview of NLP tasks covered.

**Unit 2 — Token Classification (NER, POS):**
```python
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch

tokenizer = AutoTokenizer.from_pretrained("dslim/bert-base-NER")
model = AutoModelForTokenClassification.from_pretrained("dslim/bert-base-NER")

inputs = tokenizer("My name is Sarah and I live in London", return_tensors="pt")
outputs = model(**inputs)
predictions = torch.argmax(outputs.logits, dim=-1)
```
- Preprocessing: align labels with tokens (account for subword fragmentation)
- The alignment challenge: one word → multiple tokens, labels only for words
- Using `tokenizer(examples, truncation=True, is_split_into_words=True)` for pre-tokenized inputs
- `model.config.id2label` for mapping IDs to label names
- Sequence-level evaluation metrics: seqeval (precision, recall, F1 per entity type)

**Unit 3 — Fine-tuning a Masked Language Model:**
```python
from transformers import AutoTokenizer, AutoModelForMaskedLM, DataCollatorForLanguageModeling

model = AutoModelForMaskedLM.from_pretrained("distilroberta-base")
data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=True, mlm_probability=0.15)
```
- MLM training: randomly mask 15% of tokens, predict the originals
- 80% masked, 10% random, 10% unchanged (BERT's original strategy)
- Whole Word Masking (WW-MLM): mask all tokens of a word together
- DataCollatorForLanguageModeling handles masking automatically

**Unit 4 — Translation:**
```python
from transformers import pipeline

translator = pipeline("translation_en_to_fr", model="Helsinki-NLP/opus-mt-en-fr")
translator("Hello, how are you?")
```
- Encoder-decoder models for sequence-to-sequence tasks
- MarianMT / OPUS models: specialized per language pair
- T5 as universal translator (single model, multiple language pairs via prefix)
- Evaluation: BLEU score (n-gram overlap with reference translations)

**Unit 5 — Summarization:**
```python
from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
summarizer("Very long article...", max_length=130, min_length=30)
```
- Extractive vs abstractive summarization
- Key constraint parameters: `max_length`, `min_length`, `length_penalty`
- BART: denoising autoencoder, excellent for summarization
- Pegasus: pre-trained with gap-sentence generation, state-of-the-art summarization
- Evaluation: ROUGE score (n-gram overlap between summary and reference)

**Unit 6 — Training a Causal Language Model from Scratch:**
```python
from transformers import AutoTokenizer, AutoModelForCausalLM, DataCollatorForLanguageModeling

tokenizer = AutoTokenizer.from_pretrained("gpt2")
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_config(
    AutoConfig.from_pretrained("gpt2", vocab_size=len(tokenizer), n_ctx=512, n_layer=6, n_head=6)
)

data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
```
- CLM training: predict next token given previous tokens
- Data collator for CLM: shifts input by one position to create labels
- Building a config for custom model size (smaller GPT-2)
- Memory considerations: causal LM training is memory-intensive
- Perplexity as evaluation metric (lower is better)

**Unit 7 — [Untitled / Rate-limited — likely QA or advanced tasks]**

**Unit 8 — [Untitled / Rate-limited — likely final project or advanced deployment]**

**Unit 9 — End-of-chapter quiz.**

---

### Key Takeaways & Integration with Modern HF Ecosystem

**Transformers v5.x Compatibility:**
The course was originally written for transformers v4.x but is fully compatible with v5.x. Key v5 differences:
- Architecture Registry: `AutoModel` resolves via `pipeline_tag` → `model_type` mapping in `transformers.models.auto.architecture_registry`
- New model additions: Llama 4, DeepSeek V3/R1, Qwen3, Phi-4, Mamba hybrid
- SDPA attention is now default (Flash Attention backend where available)
- `generation_config.json` is loaded automatically
- `device_map="auto"` for multi-GPU/CPU offloading inference

**Datasets v5.0 Migration:**
The course covers datasets v2-3 patterns. v5.x key changes:
- Agent traces format support (`format=format:agent-traces`)
- Multi-shard streaming shuffle with `max_buffer_input_shards`
- By-column batching for memory-efficient processing
- JSON type improvements for structured outputs

**Production Deployment Evolution:**
- Unit 2.8 covers TGI and optimized deployment — these now integrate with vLLM natively
- Inference Endpoints: serverless GPU deployment from any model checkpoint
- ZeroGPU Spaces: free GPU for community Spaces

**Course References in Real Projects:**
- The Pipeline API (Ch1) is the most common entry point for beginners
- Trainer API (Ch3) is the basis for `trl`'s `SFTTrainer` and `DPOTrainer`
- Tokenizer training (Ch6) is directly applicable to fine-tuning LLMs for specialized domains
- FAISS search (Ch5) is the core of RAG retrieval pipelines
- The Hub sharing workflow (Ch4) is mandatory for any model publication

### Skill
mlops/hf-llm-course — Hugging Face LLM/NLP Course complete curriculum documentation, covering transformers, datasets, tokenizers, fine-tuning, Hub sharing, and production deployment patterns
