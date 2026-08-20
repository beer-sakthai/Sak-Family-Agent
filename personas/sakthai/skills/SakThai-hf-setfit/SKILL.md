---
name: SakThai-hf-setfit
description: 'SetFit: prompt-free, efficient few-shot text classification using Sentence Transformers'
---

# SetFit — Efficient Few-Shot Text Classification

## Overview

SetFit (Sentence Transformer Fine-tuning) is an efficient, **prompt-free** framework for few-shot text classification built on top of Sentence Transformers. It achieves high accuracy with as few as 8 labeled examples per class.

### Key advantages

- **No prompts or verbalizers** — Works directly from text, no prompt engineering needed
- **Fast to train** — Uses small Sentence Transformer models, order of magnitude faster than LLM-based few-shot
- **Multilingual** — Works with any Sentence Transformer on the Hub; fine-tune a multilingual checkpoint
- **Competitive accuracy** — e.g. 8-shot SetFit matches RoBERTa Large fine-tuned on full 3k CR training set

## Architecture

SetFit models have two components:

1. **Body**: a Sentence Transformer embedding model (from Hugging Face Hub)
2. **Head**: a classifier (default: scikit-learn LogisticRegression)

### Two-phase training

**Phase 1 — Embedding finetuning** (contrastive learning):
- Creates positive pairs (same class) and negative pairs (different class) from few labeled samples
- Contrastive loss pulls same-class embeddings closer and pushes different-class apart
- With 8 positives + 8 negatives → 28 positive + 64 negative = 92 unique training pairs
- Nudges the embedding model to align with classification task without forgetting pretrained knowledge

**Phase 2 — Classifier training**:
- Feeds all training sentences through the finetuned embedding model
- Fits a logistic regression classifier (from scikit-learn) on the resulting embeddings and labels
- Fast, efficient, works on CPU

## Quickstart

```python
from setfit import SetFitModel, Trainer, TrainingArguments, sample_dataset
from datasets import load_dataset

# 1. Load model
model = SetFitModel.from_pretrained("BAAI/bge-small-en-v1.5", labels=["negative", "positive"])

# 2. Load & sample dataset (8 shots per class)
dataset = load_dataset("SetFit/sst2")
train_dataset = sample_dataset(dataset["train"], label_column="label", num_samples=8)
test_dataset = dataset["test"]

# 3. Training arguments
args = TrainingArguments(batch_size=32, num_epochs=10)

# 4. Train
trainer = Trainer(model=model, args=args, train_dataset=train_dataset)
trainer.train()

# 5. Evaluate
metrics = trainer.evaluate(test_dataset)
print(metrics)  # ~85% accuracy with 8-shot

# 6. Save & push
model.save_pretrained("setfit-bge-small-v1.5-sst2-8-shot")
model.push_to_hub("my-org/setfit-model-name")
```

## Inference

```python
model = SetFitModel.from_pretrained("my-org/setfit-model-name")
preds = model.predict([
    "It's a charming and often affecting journey.",
    "It's slow -- very, very slow.",
])
# => ['positive', 'negative']
```

## Key Features

### Zero-shot classification
SetFit supports zero-shot via candidate labels — no training data needed. Uses the embedding model's similarity between text and label descriptions.

### Multilabel classification
Use `MultiLabelClassificationHead` for tasks where a sample can belong to multiple classes simultaneously.

### Hyperparameter optimization
SetFit integrates with Optuna for automated hyperparameter search across both training phases.

### Knowledge distillation
Train a smaller student SetFit model from a larger teacher SetFit model, retaining most of the accuracy with faster inference.

### ONNX export
Convert trained SetFit models to ONNX for accelerated CPU inference with `~setfit.SetFitModel.to_onnx()`.

## Model Selection Tips

- Use the **MTEB Leaderboard** to choose a Sentence Transformer backbone
- BAAI/bge-small-en-v1.5 is a good small/performant balance
- For multilingual tasks, use multilingual Sentence Transformers (e.g. `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`)
- Better performance comes from **more data, not more training** — avoid over-epoching

## Best Practices

- `num_epochs` can be a tuple (epochs for phase 1, for phase 2) — tune separately
- `max_steps` takes precedence over `num_epochs` — use to limit training when data is abundant
- Use `column_mapping` in Trainer for datasets with non-standard column names
- Enable `model_card` callback to auto-generate model cards on training completion
- For production: export to ONNX, quantize, then deploy on CPU

## References

- [SetFit Documentation](https://huggingface.co/docs/setfit)
- [SetFit GitHub](https://github.com/huggingface/setfit)
- [SetFit Paper (Lewis Tunstall et al.)](https://arxiv.org/abs/2209.11055)
- [SetFit Models on Hub](https://huggingface.co/SetFit)
- [Sentence Transformers](https://huggingface.co/docs/sentence-transformers)
