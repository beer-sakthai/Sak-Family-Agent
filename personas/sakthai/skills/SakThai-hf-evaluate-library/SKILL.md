---
name: SakThai-hf-evaluate-library
description: "\U0001F917 Evaluate: load, compute, and save ML metrics (accuracy, F1, BLEU, ROUGE,\
  \ perplexity) and run evaluator pipelines for text classification, QA, summarization.\
  \ Covers EvaluationSuite, custom metrics, Hub integration, and visualization."
---

# 🤗 Evaluate Library — Metrics, Evaluators & Suites

## What's inside

🤗 Evaluate is Hugging Face's library for evaluating ML models and datasets. With a single line you get access to 100+ evaluation methods across NLP, Computer Vision, Reinforcement Learning, and more. It's the standard way to compute metrics, run evaluator pipelines, track results, and share evaluations on the Hub.

Three layers of abstraction:
- **Metrics** — individual scoring functions (accuracy, F1, BLEU, perplexity)
- **Evaluators** — end-to-end pipelines combining model + dataset + metric
- **EvaluationSuites** — multi-task evaluation composing several evaluators

## Quick start

**Installation**:
```bash
pip install evaluate
```

**Verify it works**:
```python
import evaluate
metric = evaluate.load("accuracy")
result = metric.compute(references=[0, 1, 0, 1], predictions=[0, 1, 1, 1])
print(result)
# {'accuracy': 0.75}
```

## Common workflows

### Workflow 1: Load and compute individual metrics

```python
import evaluate

# --- Classification metrics ---
accuracy = evaluate.load("accuracy")
accuracy.compute(references=[0,1,0,1], predictions=[0,1,1,1])
# {'accuracy': 0.75}

f1 = evaluate.load("f1")
f1.compute(references=[0,1,0,1], predictions=[0,1,1,1], average="macro")
# {'f1': 0.8333}

precision = evaluate.load("precision")
recall = evaluate.load("recall")
precision.compute(references=[0,1,0,1], predictions=[0,1,1,1])
recall.compute(references=[0,1,0,1], predictions=[0,1,1,1])

# --- Text generation metrics ---
bleu = evaluate.load("bleu")
bleu.compute(references=[["the", "cat", "sat"], ["a", "cat", "sits"]],
             predictions=[["the", "cat", "is", "sitting"]])
# {'bleu': 0.512, 'precisions': [0.75, 0.5, 0.333, 0.0], ...}

rouge = evaluate.load("rouge")
rouge.compute(references=["the cat sat on the mat"],
              predictions=["the cat is on the mat"])
# {'rouge1': 0.75, 'rouge2': 0.667, 'rougeL': 0.75, ...}

perplexity = evaluate.load("perplexity", module_type="measurement")
# Requires a model + tokenizer — see Workflow 3

# --- Regression metrics ---
mse = evaluate.load("mse")
mse.compute(references=[1.0, 2.0, 3.0], predictions=[1.1, 2.2, 2.8])
# {'mse': 0.0633}

mae = evaluate.load("mae")
r2 = evaluate.load("r2")

# --- Multi-class confusion matrix ---
cm = evaluate.load("confusion_matrix")
cm.compute(references=[0,1,2,1,0], predictions=[0,2,2,1,0])
# {'confusion_matrix': [[2,0,0],[0,1,1],[0,0,1]]}
```

### Workflow 2: List and discover available metrics

```python
import evaluate

# List ALL available metrics
all_metrics = evaluate.list_evaluation_modules(
    module_type="metric",
    include_community=True
)
print(f"Total metrics available: {len(all_metrics)}")

# Filter by task
nlp_metrics = evaluate.list_evaluation_modules(
    module_type="metric",
    task="text-classification"
)

# Search for a specific metric
seqeval = evaluate.list_evaluation_modules(
    module_type="metric",
    include_community=False
)
# Filter locally
bleu_like = [m for m in all_metrics if "bleu" in m.lower()]
print(f"BLEU-related metrics: {bleu_like}")
```

### Workflow 3: Evaluate a model's perplexity on a dataset

```python
import evaluate
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load a causal LM and its tokenizer
model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")

# Load the perplexity measurement
perplexity = evaluate.load("perplexity", module_type="measurement")

# Tokenize some text
text = ["The cat sat on the mat.", "I love machine learning."]
results = perplexity.compute(model=model, tokenizer=tokenizer, data=text)

print(f"Perplexity: {results['perplexities']}")
print(f"Mean perplexity: {results['mean_perplexity']}")
# {'mean_perplexity': 89.2, 'perplexities': [...]}
```

### Workflow 4: End-to-end Evaluator pipelines

The `Evaluator` classes handle the full loop: model → dataset → metric → results.

```python
from evaluate import evaluator
from datasets import load_dataset

# --- Text classification evaluator ---
eval_clf = evaluator("text-classification")

dataset = load_dataset("imdb", split="test[:50]")

results = eval_clf.compute(
    model_or_pipeline="lvwerra/distilbert-imdb",
    data=dataset,
    input_column="text",
    label_column="label",
    metric="accuracy",
    label_mapping={"NEGATIVE": 0, "POSITIVE": 1},
    strategy="simple",  # or "bootstrap"
)

print(f"Accuracy: {results['accuracy']['score']:.4f} ± {results['accuracy']['uncertainty']:.4f}")

# --- Question answering evaluator ---
eval_qa = evaluator("question-answering")

qa_dataset = load_dataset("squad_v2", split="validation[:100]")

qa_results = eval_qa.compute(
    model_or_pipeline="distilbert-base-cased-distilled-squad",
    data=qa_dataset,
    metric="squad",
)

print(f"F1: {qa_results['f1']['score']:.2f}")
print(f"Exact match: {qa_results['exact_match']['score']:.2f}")
```

### Workflow 5: EvaluationSuite — multi-task evaluation

Evaluate a model across several tasks in one run:

```python
import evaluate
from evaluate.evaluation_suite import SubTask

class MySuite(evaluate.EvaluationSuite):
    def __init__(self, name):
        super().__init__(name)
        self.suite = [
            SubTask(
                task_type="text-classification",
                data="glue",
                subset="sst2",
                split="validation[:50]",
                args_for_task={
                    "metric": "accuracy",
                    "input_column": "sentence",
                    "label_column": "label",
                    "label_mapping": {"LABEL_0": 0.0, "LABEL_1": 1.0},
                },
            ),
            SubTask(
                task_type="question-answering",
                data="squad_v2",
                split="validation[:50]",
                args_for_task={
                    "metric": "squad",
                },
            ),
        ]

# Run from a script or Space
suite = evaluate.EvaluationSuite.load("path/to/my_suite.py")
results = suite.run("distilbert-base-uncased")

import pandas as pd
print(pd.DataFrame(results))
#   task_name  accuracy  f1  exact_match  total_time_in_seconds  samples_per_second
# 0 glue/sst2     0.84  NaN          NaN                  5.23               9.56
# 1 squad_v2      NaN 0.78         0.65                 12.47               4.01
```

### Workflow 6: Save/load results to/from the Hub

```python
import evaluate
from huggingface_hub import HfApi

# Compute a metric
metric = evaluate.load("accuracy")
result = metric.compute(references=[0,1,0,1], predictions=[0,1,1,1])

# Save locally
metric.save("./my_eval_results/")

# Push to the Hub (requires write token)
# metric.push_to_hub("my-org/my-eval-results", private=True)

# Load from Hub
# metric = evaluate.load("my-org/my-eval-results")
```

### Workflow 7: Combine metrics with Transformers Trainer

```python
import evaluate
from transformers import Trainer, TrainingArguments

# Load metrics outside the Trainer
accuracy = evaluate.load("accuracy")
f1 = evaluate.load("f1")

def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = predictions.argmax(axis=-1)
    acc = accuracy.compute(predictions=predictions, references=labels)
    f1_score = f1.compute(predictions=predictions, references=labels, average="macro")
    return {**acc, **f1_score}

training_args = TrainingArguments(
    output_dir="./output",
    evaluation_strategy="epoch",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    compute_metrics=compute_metrics,
)

trainer.train()
```

### Workflow 8: Confidence intervals with bootstrapping

```python
from evaluate import evaluator
from datasets import load_dataset

eval_clf = evaluator("text-classification")

results = eval_clf.compute(
    model_or_pipeline="lvwerra/distilbert-imdb",
    data=load_dataset("imdb", split="test[:100]"),
    input_column="text",
    label_column="label",
    metric="accuracy",
    strategy="bootstrap",
    n_resamples=1000,  # Number of bootstrap samples
    random_state=42,
)

print(f"Accuracy: {results['accuracy']['score']:.3f}")
print(f"95% CI: [{results['accuracy']['confidence_interval']['low']:.3f}, "
      f"{results['accuracy']['confidence_interval']['high']:.3f}]")
```

## Metric categories

| Category | Example metrics | Use case |
|----------|----------------|----------|
| **Classification** | accuracy, f1, precision, recall, matthews_correlation, roc_auc | Binary & multi-class classification |
| **Text Generation** | bleu, rouge, sacrebleu, meteor, ter, chrf, bertscore, mauve | Translation, summarization, generation |
| **QA** | squad, squad_v2, exact_match | Question answering |
| **Regression** | mse, mae, r2, spearmanr, pearsonr | Continuous value prediction |
| **Sequence Labeling** | seqeval, conll | NER, POS tagging |
| **Image** | ceres, image_quality | Computer vision |
| **Fairness** | demographic_parity, equalized_odds | Bias detection |
| **Measurements** | perplexity, mase | Intrinsic model measures |

## Supported evaluator task types

| Task type string | Description | Supported metrics |
|-----------------|-------------|------------------|
| `"text-classification"` | Single-label text classification | accuracy, f1, precision, recall |
| `"question-answering"` | Extractive QA | squad, squad_v2 |
| `"token-classification"` | NER / sequence labeling | seqeval |
| `"text-generation"` | Causal LM generation | perplexity |
| `"summarization"` | Summarization | rouge, bleu, meteor |
| `"image-classification"` | Image classification | accuracy, f1 |
| `"text2text-generation"` | Seq2Seq generation | rouge, bleu |

## Creating a custom metric

```python
import evaluate
from evaluate import EvaluationModule

@evaluate.utils.file_utils.add_start_docstrings(...)
class MyMetric(EvaluationModule):
    def _info(self):
        return evaluate.EvaluationModuleInfo(
            description="My custom metric",
            citation="",
            inputs_description="Takes two lists",
            features=[
                evaluate.Features(
                    predictions={"type": "int64"},
                    references={"type": "int64"},
                )
            ],
        )

    def _compute(self, predictions, references):
        # Your custom computation
        correct = sum(p == r for p, r in zip(predictions, references))
        return {"my_accuracy": correct / len(predictions)}

# Register and load
metric = evaluate.load("path/to/my_metric.py")
```

## Integration with other frameworks

### scikit-learn
```python
import evaluate
from sklearn.metrics import accuracy_score
from sklearn.model_selection import cross_val_score

# Use HF metrics alongside sklearn
metric = evaluate.load("accuracy")
y_true = [0, 1, 0, 1]
y_pred = [0, 1, 1, 1]
print(metric.compute(predictions=y_pred, references=y_true))
```

### Keras / TensorFlow
```python
import evaluate
import tensorflow as tf

# Use HF metrics in Keras callbacks
accuracy = evaluate.load("accuracy")

class HFEvalCallback(tf.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs=None):
        y_pred = self.model.predict(x_val)
        y_pred_classes = tf.argmax(y_pred, axis=1)
        result = accuracy.compute(
            predictions=y_pred_classes.numpy(),
            references=y_val_labels
        )
        print(f"HF Accuracy: {result['accuracy']:.4f}")
```

## Best practices

1. **Always use `module_type="measurement"`** for model-dependent evaluations like perplexity (vs `module_type="metric"` for reference-based)
2. **Use `strategy="bootstrap"`** in evaluators to get confidence intervals
3. **Small sample first** — test with `dataset[:10]` before running on full eval set
4. **Push metrics to the Hub** to share evaluation results with the community
5. **Combine with datasets.map()** for large-scale preprocessing before evaluation
6. **Use EvaluationSuite** when a model needs assessment across multiple capabilities
7. **Specify `seed` and `n_resamples`** for reproducible bootstrap results

## Common issues

**Issue: "metric not found"**

Verify the metric name:
```python
import evaluate
print(len(evaluate.list_evaluation_modules(include_community=True)))
# Shows available metrics
```

Community metrics are namespaced: `evaluate.load("community/metric_name")`.

**Issue: Model/perplexity evaluation too slow**

Use a smaller subset, or use `module_type="measurement"` with batched inference:
```python
perplexity.compute(model=model, tokenizer=tokenizer, data=text, batch_size=32)
```

**Issue: BLEU score is 0 or very low**

BLEU requires tokenized inputs (list of list of tokens), not raw strings. Use `sacrebleu` metric instead for raw text:
```python
sacrebleu = evaluate.load("sacrebleu")
sacrebleu.compute(references=["the cat sat"], predictions=["the cat sits"])
```

**Issue: Evaluator fails with custom pipeline**

Pass `model_or_pipeline` as a string (model ID) or as a pipeline object. For custom pipelines:
```python
from transformers import pipeline
my_pipe = pipeline("text-classification", model="my-model", device=0)
eval_clf.compute(model_or_pipeline=my_pipe, ...)
```

## Resources

- Docs: https://huggingface.co/docs/evaluate
- GitHub: https://github.com/huggingface/evaluate
- Metric library: https://huggingface.co/evaluate-metric
- Hub integration: https://huggingface.co/docs/evaluate/en/evaluator_hub
- Available metrics list: https://huggingface.co/evaluate-metric?sort_metric=downloads
