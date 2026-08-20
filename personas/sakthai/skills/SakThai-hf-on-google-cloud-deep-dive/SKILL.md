---
name: SakThai-hf-on-google-cloud-deep-dive
description: "Complete deep-dive on deploying and training Hugging Face models on Google Cloud\
  \ Platform \u2014 Deep Learning Containers (DLCs), Vertex AI, Google Kubernetes\
  \ Engine (GKE), Cloud Run, and Google TPU integration via Optimum. Covers available\
  \ container images, deployment patterns, gcloud commands, huggingface-inference-toolkit,\
  \ and zero-cost evaluation options."
---

# Hugging Face on Google Cloud — Deep Dive

## Overview

Hugging Face collaborates with Google Cloud to provide **Deep Learning Containers (DLCs)** — ready-to-use Docker images pre-installed with Transformers, Datasets, Tokenizers, and optimized serving stacks — for training and deploying models on Google Cloud infrastructure.

**Key integration points:**
- **DLCs** hosted in Google Cloud Artifact Registry (no build step needed)
- **Vertex AI** — managed ML platform for training, evaluation, and inference
- **GKE** — fully-managed Kubernetes for containerized deployments at scale
- **Cloud Run** — serverless container platform with auto-scaling
- **Google TPUs** — via Optimum-TPU for high-throughput training
- **huggingface-inference-toolkit** — first-class inference library in PyTorch DLCs

## Available Deep Learning Containers (DLCs)

### TGI (Text Generation Inference)

| Container URI | Path | Accelerator |
|---|---|---|
| `us-docker.pkg.dev/deeplearning-platform-release/gcr.io/huggingface-text-generation-inference-cu124.2-4.ubuntu2204.py311` | text-generation-inference-gpu.2.4.0 | GPU |

### TEI (Text Embeddings Inference)

| Container URI | Path | Accelerator |
|---|---|---|
| `us-docker.pkg.dev/deeplearning-platform-release/gcr.io/huggingface-text-embeddings-inference-cu122.1-6.ubuntu2204` | text-embeddings-inference-gpu.1.6.0 | GPU |
| `us-docker.pkg.dev/deeplearning-platform-release/gcr.io/huggingface-text-embeddings-inference-cpu.1-6` | text-embeddings-inference-cpu.1.6.0 | CPU |

### PyTorch Inference

| Container URI | Path | Accelerator |
|---|---|---|
| `us-docker.pkg.dev/deeplearning-platform-release/gcr.io/huggingface-pytorch-inference-cu124.2-4.ubuntu2204.py311` | pytorch-inference-gpu.2.4.0 | GPU |
| `us-docker.pkg.dev/deeplearning-platform-release/gcr.io/huggingface-pytorch-inference-cpu.2-4.ubuntu2204.py311` | pytorch-inference-cpu.2.4.0 | CPU |

### PyTorch Training

| Container URI | Path | Accelerator |
|---|---|---|
| `us-docker.pkg.dev/deeplearning-platform-release/gcr.io/huggingface-pytorch-training-cu124.2-4.ubuntu2204.py311` | pytorch-training-gpu.2.4.0 | GPU |
| `us-docker.pkg.dev/deeplearning-platform-release/gcr.io/huggingface-pytorch-training-tpu.2-4.ubuntu2204.py311` | pytorch-training-tpu.2.4.0 | TPU |

> **List all available containers:**
> ```bash
> gcloud container images list --repository="us-docker.pkg.dev/deeplearning-platform-release/gcr.io" | grep "huggingface-"
> ```

## Deployment Targets

### 1. Vertex AI (Managed ML Platform)

**Inference — deploy a model endpoint:**

```bash
# Create a model from the DLC
gcloud ai models upload \
  --container-image-uri="us-docker.pkg.dev/deeplearning-platform-release/gcr.io/huggingface-pytorch-inference-cpu.2-4.ubuntu2204.py311" \
  --container-ports=8080 \
  --display-name="my-hf-model"

# Deploy to endpoint
gcloud ai endpoints deploy-model \
  --model="my-hf-model" \
  --display-name="hf-endpoint" \
  --machine-type="n1-standard-4"
```

**Training — run a training job:**

```bash
gcloud ai custom-jobs create \
  --region=us-central1 \
  --display-name="hf-training-job" \
  --worker-pool-spec=machine-type=n1-standard-4,container-image-uri="us-docker.pkg.dev/deeplearning-platform-release/gcr.io/huggingface-pytorch-training-cu124.2-4.ubuntu2204.py311",executor-image-uri="us-docker.pkg.dev/deeplearning-platform-release/gcr.io/huggingface-pytorch-training-cu124.2-4.ubuntu2204.py311"
```

### 2. Google Kubernetes Engine (GKE)

**Deploy a TGI inference deployment:**

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tgi-inference
spec:
  replicas: 2
  selector:
    matchLabels:
      app: tgi
  template:
    metadata:
      labels:
        app: tgi
    spec:
      containers:
      - name: tgi
        image: us-docker.pkg.dev/deeplearning-platform-release/gcr.io/huggingface-text-generation-inference-cu124.2-4.ubuntu2204.py311
        env:
        - name: MODEL_ID
          value: "meta-llama/Llama-3.2-3B-Instruct"
        - name: HF_TOKEN
          valueFrom:
            secretKeyRef:
              name: hf-token
              key: token
        ports:
        - containerPort: 8080
        resources:
          requests:
            nvidia.com/gpu: 1
          limits:
            nvidia.com/gpu: 1
```

```bash
kubectl apply -f deployment.yaml
kubectl expose deployment tgi-inference --type=LoadBalancer --port=8080
```

### 3. Cloud Run (Serverless)

**Deploy a TEI embedding endpoint:**

```bash
gcloud run deploy tei-service \
  --image="us-docker.pkg.dev/deeplearning-platform-release/gcr.io/huggingface-text-embeddings-inference-cpu.1-6" \
  --cpu=4 \
  --memory=8Gi \
  --set-env-vars="MODEL_ID=sentence-transformers/all-MiniLM-L6-v2" \
  --no-allow-unauthenticated \
  --region=us-central1
```

## Training on Google TPUs

Google TPUs (Tensor Processing Units) are available through **Optimum-TPU** and the **PyTorch Training TPU DLC**.

### Requirements

- ✅ Google Cloud project with TPU quota
- ✅ TPU Training DLC: `pytorch-training-tpu.2-4.ubuntu2204.py311`
- ✅ Optimum-TPU (`pip install optimum[tpu]`) pre-installed in DLC
- ✅ PyTorch/XLA for TPU runtime

### Training with Optimum-TPU

```bash
# Using the TRL CLI for fine-tuning
accelerate launch \
  --num_processes=8 \
  --tpu \
  --main_process_ip=$MASTER_ADDR \
  --main_process_port=$MASTER_PORT \
  --machine_rank=$RANK \
  train.py
```

### Example training script (SFT):

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import SFTTrainer
from datasets import load_dataset

model = AutoModelForCausalLM.from_pretrained("google/gemma-2-2b-it")
tokenizer = AutoTokenizer.from_pretrained("google/gemma-2-2b-it")
dataset = load_dataset("databricks/databricks-dolly-15k", split="train")

training_args = TrainingArguments(
    output_dir="./gemma-sft",
    per_device_train_batch_size=4,
    num_train_epochs=1,
    bf16=True,
    logging_steps=10,
    save_strategy="epoch",
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
)

trainer.train()
```

## huggingface-inference-toolkit

The **huggingface-inference-toolkit** is pre-installed in the PyTorch Inference DLCs. It provides a production-ready inference server that wraps any Transformers model as a REST API.

### Key features

- Auto-detects model task from `pipeline_tag`
- Exposes `/predict` endpoint with JSON input/output
- Supports batching and request-level parameters
- Integrated health checks (`/health`, `/metadata`)
- Configurable via environment variables

### Quick start

```python
# app.py — custom inference handler (optional, mounts into DLC)
from huggingface_inference_toolkit import InferenceToolkit

toolkit = InferenceToolkit(model_id="bert-base-uncased")
toolkit.run(host="0.0.0.0", port=8080)
```

**Environment variables:**

| Variable | Description |
|---|---|
| `MODEL_ID` | HF Hub model ID (required) |
| `HF_TOKEN` | HF auth token for gated models |
| `TASK` | Override auto-detected pipeline tag |
| `BATCH_SIZE` | Max batch size for inference |
| `MAX_CONCURRENT_REQUESTS` | Parallel request limit |

## Google Cloud Storage Buckets Integration

Mount GCS buckets for dataset/model checkpoint access:

```bash
# Via gcsfuse in custom startup
gcsfuse my-bucket /data

# Using HF datasets with GCS
python -c "
from datasets import load_dataset
ds = load_dataset('parquet', data_files='gs://my-bucket/data/*.parquet')
print(len(ds['train']))
"
```

## Google TPUs via Optimum

### Available TPU types on Google Cloud

| TPU Type | vCPUs | Memory | Pod slices | Best for |
|---|---|---|---|---|
| v5e-1 | 4 | 16 GB | 1 | Small models, dev |
| v5e-4 | 16 | 64 GB | 4 | Fine-tuning |
| v5e-8 | 32 | 128 GB | 8 | Medium models |
| v5e-16 | 64 | 256 GB | 16 | Large models |
| v5p-8 | 48 | 192 GB | 8 | Pre-training |
| v5p-128 | 768 | 3 TB | 128 | Massive training |

### Setting up a TPU VM with HF

```bash
# Create TPU VM
gcloud compute tpus tpu-vm create hf-tpu \
  --zone=us-central2-b \
  --accelerator-type=v5e-4 \
  --version=tpu-ubuntu2204-base

# SSH and install HF stack
gcloud compute tpus tpu-vm ssh hf-tpu --zone=us-central2-b \
  --command="pip install transformers datasets accelerate torch-xla"

# Run training
gcloud compute tpus tpu-vm ssh hf-tpu --zone=us-central2-b \
  --command="python train.py"
```

### Optimum-TPU vs PyTorch/XLA

| Approach | When to use |
|---|---|
| **Optimum-TPU** | Higher-level API, integrates with Trainer, TRL, PEFT |
| **PyTorch/XLA** | Direct TPU control, custom training loops |

## Deployment Patterns Comparison

| Platform | Scaling | GPU support | Cold start | Best for |
|---|---|---|---|---|
| **Vertex AI** | Manual + auto | ✅ All GCP GPUs | 30–60s | Managed ML pipelines |
| **GKE** | HPA + KEDA | ✅ NVIDIA GPUs | Seconds (warm) | Custom infra, multi-model |
| **Cloud Run** | Auto (0→N) | ❌ CPU only | <1s | Lightweight embeddings, CPU inference |
| **Vertex AI Batch** | N/A | ✅ GPUs | Minutes | Offline eval, batch inference |

## Zero-Cost Patterns

Since Beer has no budget, these patterns minimize cost:

1. **Cloud Run CPU inference** — auto-scales to zero when idle, pay per request (~$0 for low traffic)
2. **Vertex AI batch prediction** — don't keep endpoints running; submit batch jobs with `gcloud ai batch-predict`
3. **GKE with spot/preemptible VMs** — heavily discounted, OK for fault-tolerant batch jobs
4. **TPU VM + preemptible** — significantly cheaper, suitable for training that can checkpoint
5. **Free-tier GCP credits** — new accounts get $300 free credits; use them for one-shot experiments

## Limitations

- Cloud Run does **not** support GPU (CPU inference only for embedding/text classification)
- TGI DLC currently **GPU-only** (no CPU variant published)
- Vertex AI custom endpoints incur **per-minute** cost while running
- Some DLCs have region restrictions (TPUs in specific zones only)
- **No free-tier GPU** on Google Cloud (unlike Kaggle/Colab)
- DLCs require a Google Cloud project with **billing enabled**

## Related HF Topics

| Topic | Relationship |
|---|---|
| **Optimum** | Hardware optimization — TPU support via Optimum-TPU |
| **TGI** | High-performance text generation serving (DLC variant) |
| **TEI** | Embedding model serving (DLC variant) |
| **Inference Endpoints** | Alternative managed deployment on HF infra |
| **Deploying on AWS** | Equivalent DLC ecosystem on AWS |
| **Microsoft Azure** | Equivalent DLC ecosystem on Azure |
| **Kernels** | Compute kernels used in TPU-optimized models |

## References

- [Official Docs: Hugging Face on Google Cloud](https://huggingface.co/docs/google-cloud/main/en/index)
- [Google-Cloud-Containers GitHub](https://github.com/huggingface/Google-Cloud-Containers)
- [Available DLCs on Google Cloud](https://huggingface.co/docs/google-cloud/main/en/available-dlcs)
- [Optimum Documentation](https://huggingface.co/docs/optimum/main/en/index)
- [Optimum-TPU](https://huggingface.co/docs/optimum/main/en/tpu)
- [Google Cloud Deep Learning Containers](https://cloud.google.com/deep-learning-containers)
- [TGI on Google Cloud blog](https://huggingface.co/blog/tgi-gke-vertex)
