# HF Learnings: HF Models on Foundry Managed Compute

**author:** SakThai
**license:** MIT

## 2026-07-25: HF Models on Foundry Managed Compute — Enterprise Deployment of Open-Weight Models via Microsoft Foundry (Topic #364)

### Summary

Comprehensive deep-dive into **Hugging Face models on Microsoft Foundry Managed Compute** — announced at Microsoft Build 2026 (July 7, 2026). A curated catalog of open-weight models from the Hugging Face ecosystem, refreshed weekly, deployable in one click onto Foundry Managed Compute (Microsoft's managed GPU platform-as-a-service). Weights are pre-staged in Azure, runtimes are built and scanned by Microsoft, and every model in the Collection ships with enterprise security, governance, observability, and billing. This is distinct from Hugging Face's own enterprise features — it's the operational layer Microsoft runs on top of HF's open ecosystem.

### Key Findings

| Area | Finding |
|------|---------|
| **What it is** | Curated subset of HF models in Foundry Model Catalog, refreshed weekly, one-click deploy onto Managed Compute |
| **Partners** | Microsoft Foundry + Hugging Face — curation pipeline run jointly |
| **Modalities** | Text, vision, audio, multimodal — LLMs, VLMs, ASR, embeddings, segmentation, image generation |
| **Weight format** | Safetensors only — no `trust_remote_code` unless rigorously reviewed |
| **Runtimes** | vLLM (default), SGLang, TensorRT-LLM, NIM, TEI, llama.cpp, hf-serve |
| **GPU accelerators** | A100, H100, MI300X — Global and Data Zone deployments |
| **Pricing model** | Pay-by-accelerator-hour, scale-to-zero, same bill as other Foundry models |
| **Network** | Private network deployable — no outbound access to HF Hub needed |
| **Enterprise features** | RBAC, private networking, Azure Policy integration, content safety, guardrails |
| **Agent integration** | Slots into Foundry Agents as admin-connected model, same SDK as frontier models |

### 1. The Platform: Microsoft Foundry and Managed Compute

Microsoft Foundry is a platform for building and operating agentic AI applications. It offers the widest model selection on any cloud — models from Microsoft, OpenAI, Anthropic, Meta, Mistral, DeepSeek, Hugging Face, and others — all accessible through a **single endpoint** and a single set of SDKs (Python, C#, JavaScript, Java).

On top of models sits the **Foundry Agent Service**: multi-agent orchestration with built-in memory, knowledge grounding through Foundry IQ, and a catalog of connectable tools via agentic protocols. End-to-end tracing, real-time monitoring, continuous evaluations, and a prompt optimizer are part of the platform.

Foundry has three deployment options:
1. **Pay-per-token** — lowest friction, for frontier models
2. **Provisioned throughput** — predictable, high-performance production workloads
3. **Managed Compute** — managed GPU platform-as-a-service for open-source and custom models (this topic)

Managed Compute lets you deploy a model instance described by parameter count, context length, and latency/throughput preference. Foundry handles GPU topology underneath (one accelerator or several). Microsoft takes care of the machine: container updates, runtime upgrades, and security patches happen automatically.

### 2. The Curation Pipeline

Hugging Face and Microsoft run a systematic curation process:

1. **Identify trending models** — based on community signals, partner requests, customer demand
2. **Screen for compliance and security** — license review against Microsoft's enterprise distribution policy; inspect for `trust_remote_code` patterns and custom executable code
3. **Build, scan, and publish runtimes** — Microsoft builds inference container images on supported runtimes, scans for CVEs, signs and publishes to Microsoft-managed container registry
4. **Upload weights to secure Azure storage** — pulled from HF once, validated against model card, stored in Microsoft-managed Azure storage in serving regions
5. **Validate and publish** — every model + runtime + accelerator combination tested for API conformance (chat completions, embeddings, rerank) and performance (latency, throughput, TTFT, ITL)

**Key enterprise benefit**: Because weights are pre-staged in Azure storage and runtime images live in a Microsoft-managed registry, deployments don't need outbound network access to Hugging Face Hub — deployable to production inside a private network.

### 3. Supported Model Runtimes

| Runtime | Best For | Notes |
|---------|----------|-------|
| **vLLM** | Default high-throughput LLM serving | Any Transformers model works out of the box; HF is direct contributor |
| **SGLang** | Structured outputs, agentic workloads | Strong JSON/regex/grammar-constrained generation; HF-built Transformers backend |
| **TEI** | Embeddings, reranker, sequence classification | Accelerator-specific compiled kernels, lean embedding hot path |
| **llama.cpp** | CPU/small-GPU, cost-optimized | GGUF-quantized models, OpenAI-compatible API |
| **TensorRT-LLM** | NVIDIA hardware optimization | NVIDIA's optimized kernels and Triton-based serving |
| **NIM** | NVIDIA hardware optimization | NVIDIA Inference Microservices |
| **hf-serve** | Non-LLM modalities | HF's own multi-model server for vision, audio, segmentation, Transformers-native pipelines |

### 4. Deployment Templates

A deployment template is a named, versioned asset that pins:
- Runtime
- Accelerator family and count
- Context length
- Runtime-specific tuning

Example: Qwen3-32B ships with 4 templates:
- `qwen–qwen3-32b–40k-nvidia-a100`
- `qwen–qwen3-32b–40k-nvidia-h100`
- `qwen–qwen3-32b–128k-nvidia-2xa100`
- `qwen–qwen3-32b–128k-nvidia-2xh100`

Each template is pre-tuned — runtime settings, tool-call and reasoning parsers, scoring path, health probes, request concurrency, context-extension settings are all set by Microsoft.

### 5. Deploy & Score — Python SDK + OpenAI SDK

#### Deploy (Python SDK)
```python
from azure.identity import DefaultAzureCredential
from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient

client = CognitiveServicesManagementClient(
    DefaultAzureCredential(), SUBSCRIPTION_ID
)

deployment = client.managed_compute_deployments.begin_create_or_update(
    resource_group_name=RESOURCE_GROUP,
    account_name=ACCOUNT_NAME,
    deployment_name="qwen3-32b",
    parameters={
        "sku": {"name": "GlobalManagedCompute", "capacity": 1},
        "properties": {
            "model": "azureml://registries/azure-huggingface/models/qwen--qwen3-32b/versions/1",
            "deploymentTemplate": "azureml://registries/azure-huggingface/deploymenttemplates/qwen--qwen3-32b--40k-nvidia-h100/labels/latest",
            "acceleratorType": "H100_80GB",
        }
    }
)
```

#### Score (OpenAI SDK)
```python
from openai import OpenAI

api_key = client.accounts.list_keys(RESOURCE_GROUP, ACCOUNT_NAME).key1
endpoint = f"https://{ACCOUNT_NAME}.services.ai.azure.com/openai/v1"
openai_client = OpenAI(base_url=endpoint, api_key=api_key)

completion = openai_client.chat.completions.create(
    model=deployment.name,
    messages=[{"role": "user", "content": "What is the capital of France?"}],
)
print(completion.choices[0].message)
```

A chat-completions model slots into **Foundry Agents** as an admin-connected model, callable through the Foundry Responses API with the same OpenAI SDK — same auth, same endpoint, same observability.

### 6. Key Enterprise Differentiators

- **No `trust_remote_code`**: Models ship in Safetensors format, no third-party Python execution at load time
- **Private networking**: Deploy inside VNet without outbound internet access to HF Hub
- **Automatic CVE patching**: Runtime images scanned and patched by Microsoft; existing deployments upgraded automatically
- **Global + Data Zone deployments**: Choose global for broadest capacity, data zone for residency/sovereignty
- **Unified billing**: Single bill across pay-per-token, provisioned throughput, and Managed Compute
- **Accelerator family alignment**: Quota aligned to accelerator families (e.g., H100 family), carries forward as new hardware generations come online
- **Bring Your Own Weights** (roadmap): Fine-tuned and proprietary variants through same templates and governance

### 7. What's Available (as of July 7, 2026)

- **Thousands of models** across every modality in preview
- **Accelerators**: NVIDIA A100, NVIDIA H100, AMD MI300X
- **Deployment scopes**: Global and Data Zone
- **Platform features**: Playground, Azure Monitor metrics, per-deployment billing tags, curated runtime upgrades, automatic CVE patching
- **Roadmap**: Broader HF ecosystem coverage, additional accelerator families, Bring Your Own Weights

### Zero-Cost Considerations

Foundry Managed Compute is a paid enterprise service. However:
- Open-weight models avoid per-token costs of frontier APIs
- Scale-to-zero when idle reduces costs for development/staging
- CPU-only deployments via llama.cpp on lower-cost SKUs
- Existing Azure commitments (MACC, pre-paid) can apply

### Sources

- https://huggingface.co/blog/microsoft/foundry-managed-compute
- https://learn.microsoft.com/en-us/azure/ai-foundry/
- https://learn.microsoft.com/en-us/azure/ai-foundry/managed-compute
- https://huggingface.co/collections?search=foundry

---

