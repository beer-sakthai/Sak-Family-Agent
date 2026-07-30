# HF Learnings Archive

## hf-optimum — Hugging Face Optimum Library (2026-07-23)

**Summary:** 🤗 Optimum is a hardware optimization extension for Transformers, Diffusers, TIMM, and Sentence-Transformers. It provides a unified API across 7+ hardware platforms and 4 open-source integration frameworks.

### Architecture
- **Core package** (`optimum`): base optimization tools + CLI
- **Accelerator packages**: separate packages per hardware platform
- **Quanto**: PyTorch-native quantization backend (int2/4/8, float8)

### Hardware Support Matrix
| Hardware | Package | Format |
|---|---|---|
| NVIDIA TensorRT-LLM | optimum-nvidia | Docker |
| AWS Trainium/Inferentia | optimum-neuron | pip |
| Google TPU | optimum-tpu | pip |
| Intel OpenVINO | optimum-intel | pip |
| Intel Gaudi (HPU) | optimum-habana | pip |
| AMD Instinct/Ryzen AI | optimum[amd] | pip |
| FuriosaAI WARBOY | optimum[furiosa] | pip |

### Open-Source Integrations
- **ONNX Runtime**: export + quantize + deploy via ORTModelForXXX classes
- **OpenVINO**: Intel CPU/NPU optimization with NNCF quantization
- **ExecuTorch**: PyTorch edge inference (mobile/on-device)
- **Torch FX**: custom graph transformations

### CLI Usage
`optimum-cli export onnx --model <model-id> --task <task> <output-dir>`

### Quanto Quantization Workflow
1. `quantize(model, weights=qint8)` — dynamic quantization
2. `Calibration(momentum=0.9)` — optional activation range recording
3. `freeze(model)` — replace float weights with integer
4. `save_file(model.state_dict(), 'model.safetensors')` — serialize

### Key Insight
Optimum's main value is unified API across diverse hardware — the same Transformers interface works on NVIDIA GPUs, Intel CPUs, AWS Inferentia, and Google TPUs. For zero-cost deployments, ONNX Runtime CPU and OpenVINO provide the most accessible path without paid hardware.

---

## Deep Dive: ONNX Runtime CPU Inference with Optimum

### What ONNX Runtime provides
ONNX Runtime is a cross-platform inference engine that loads `.onnx`-format models and executes them on available hardware through an extensible Execution Provider (EP) architecture. The CPU EP (`CPUExecutionProvider`) uses platform-native threading (OpenMP on Linux, Intel TBB on Windows) and MLAS (Microsoft Linear Algebra Subroutines) for matmul, convolution, and activation kernels.

### Installation for CPU inference
```bash
# Lightest install — CPU-only
pip install optimum[onnxruntime]

# Full CPU optimization stack
pip install optimum[onnxruntime,onnxruntime-tools]
```

### Export pipeline
```python
from optimum.onnxruntime import ORTModelForCausalLM
from transformers import AutoTokenizer

# Export and save in one step
model = ORTModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-1.5B-Instruct",
    export=True,              # triggers ONNX export
    provider="CPUExecutionProvider",
)
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")

# Save for later reuse (avoids re-export)
model.save_pretrained("./qwen-onnx")
tokenizer.save_pretrained("./qwen-onnx")

# Later, load without re-exporting
model = ORTModelForCausalLM.from_pretrained("./qwen-onnx")
```

### All ORTModelForXXX classes
| Task | Class | Transformers Equivalent |
|---|---|---|
| Causal LM | `ORTModelForCausalLM` | `AutoModelForCausalLM` |
| Seq2Seq LM | `ORTModelForSeq2SeqLM` | `AutoModelForSeq2SeqLM` |
| Sequence Classification | `ORTModelForSequenceClassification` | `AutoModelForSequenceClassification` |
| Token Classification | `ORTModelForTokenClassification` | `AutoModelForTokenClassification` |
| Question Answering | `ORTModelForQuestionAnswering` | `AutoModelForQuestionAnswering` |
| Image Classification | `ORTModelForImageClassification` | `AutoModelForImageClassification` |
| Masked LM | `ORTModelForMaskedLM` | `AutoModelForMaskedLM` |
| Multiple Choice | `ORTModelForMultipleChoice` | `AutoModelForMultipleChoice` |
| Feature Extraction | `ORTModelForFeatureExtraction` | `AutoModel` |
| Audio Classification | `ORTModelForAudioClassification` | `AutoModelForAudioClassification` |
| Audio CTC | `ORTModelForCTC` | `AutoModelForCTC` |
| Speech Seq2Seq | `ORTModelForSpeechSeq2Seq` | `AutoModelForSpeechSeq2Seq` |
| Document Classification | `ORTModelForDocumentClassification` | `LayoutLMForSequenceClassification` |

### ONNX Runtime session configuration for CPU

The most impactful performance knobs for CPU inference:

```python
import onnxruntime

session_options = onnxruntime.SessionOptions()
session_options.intra_op_num_threads = 4   # parallel ops within a node (set to #physical cores)
session_options.inter_op_num_threads = 2   # parallel ops across graph nodes
session_options.graph_optimization_level = onnxruntime.GraphOptimizationLevel.ORT_ENABLE_ALL
session_options.enable_cpu_mem_arena = False  # avoid memory fragmentation on CPU
session_options.execution_mode = onnxruntime.ExecutionMode.ORT_SEQUENTIAL  # for LLM inference
session_options.log_severity_level = 3  # suppress ORT logs

# Pass into Optimum
model = ORTModelForCausalLM.from_pretrained(
    "./qwen-onnx",
    provider="CPUExecutionProvider",
    session_options=session_options,
    use_merged_model=True,  # merges decoder layers into one ONNX graph
    use_cache=True,
)
```

### Thread tuning rules of thumb

| CPU Type | intra_op_num_threads | inter_op_num_threads |
|---|---|---|
| 4-core (laptop) | 2-4 | 1 |
| 8-core (desktop) | 4-6 | 1-2 |
| 16-core (server) | 8 | 2 |
| 32-core+ (server) | 8-16 | 2-4 |

Key: Do NOT set `intra_op_num_threads` higher than physical core count — hyperthreads rarely help for dense matmul. For LLM decoding (batch=1), use sequential execution mode; avoid parallel mode which adds synchronization overhead.

### Dynamic vs static axis in ONNX export

Optimum's `ORTModelForCausalLM` exports with **dynamic axes by default** — batch and sequence dimensions are variable. This is essential for autoregressive generation where sequence length grows token by token. Static axis export (`use_merged_model=False` + explicit `dynamic_axes={}`) can be slightly faster for fixed-size inputs but breaks generation.

```bash
# CLI export — contrast with Python export
optimum-cli export onnx \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --task text-generation \
  --framework pt \
  --opset 18 \
  --optimize O2 \
  ./qwen-onnx
```

Optimization levels: `O0` (basic), `O1` (basic + constant folding + node fusion), `O2` (O1 + extended fusion), `O3` (O2 + layout optimization — may exceed memory on very large models).

### Quantization for CPU (ONNX Runtime)

#### Dynamic quantization (weights only, no calibration data needed)
Fastest path to 2x model size reduction on CPU. Applies INT8 to weights; activations stay FP32.

```python
from optimum.onnxruntime import ORTQuantizer
from optimum.onnxruntime.configuration import AutoQuantizationConfig

quantizer = ORTQuantizer.from_pretrained(model_dir)
dqconfig = AutoQuantizationConfig.avx512_vnni()  # or arm64, avx2, etc.
model_quantized = quantizer.quantize(quantization_config=dqconfig, save_dir="./qwen-onnx-int8")
```

Quantization configs available:
| Config | ISA requirement | Bits | When to use |
|---|---|---|---|
| `avx2` | AVX2 (Haswell+, ~2013) | W8 | Oldest x86 machines |
| `avx512` | AVX-512 (Skylake+) | W8 | Intel server CPUs |
| `avx512_vnni` | AVX-512 VNNI (Cascade Lake+) | W8 | Modern Intel Xeon |
| `arm64` | ARM NEON | W8 | Raspberry Pi, Apple Silicon |
| `avx512_vnni_int8` | AVX-512 VNNI | W8 | Max performance on Intel |
| `avx512_vnni_int8_int8` | AVX-512 VNNI | W8A8 | Quantize both weights and activations |

#### Static quantization (weights + activations, requires calibration)
```python
from optimum.onnxruntime import ORTQuantizer, ORTCalibration
from optimum.onnxruntime.configuration import AutoQuantizationConfig
from torch.utils.data import DataLoader

quantizer = ORTQuantizer.from_pretrained("./qwen-onnx")
dqconfig = AutoQuantizationConfig.avx512_vnni(is_static=True)

# Calibration step: feed 100-200 samples to record activation ranges
calibration_data = [...]  # representative inputs
calibration_dataloader = DataLoader(calibration_data, batch_size=1)

calibrator = ORTCalibration(quantizer, dataloader=calibration_dataloader)
calibrator.calibrate()

model_quantized = quantizer.quantize(
    quantization_config=dqconfig,
    calibration_dataloader=calibration_dataloader,
    save_dir="./qwen-onnx-static-int8",
)
```

Static quantization gives better performance (INT8 both weights and activations) but requires representative calibration data and may have accuracy degradation on outlier-heavy models.

### Limitations & known issues with ONNX Runtime CPU

1. **LLM generation on CPU is memory-bandwidth bound** — the bottleneck is moving weights from RAM to cache, not compute. INT8 quantization and merged models help by reducing data movement.
2. **No FlashAttention on CPU** — ONNX Runtime does not support fused attention kernels for CPU. Expect O(n²) attention compute.
3. **Dynamic shapes add overhead** — each new sequence length triggers a graph re-optimization in the EP.
4. **Large model memory** — decoder layers are all loaded into RAM; 7B+ models need 8+ GB RAM even in INT8.
5. **No batch>1 generation** — ORTModelForCausalLM only supports batch_size=1 during autoregressive generation; static shape models support batch>1 for non-generative tasks.

---

## Deep Dive: OpenVINO CPU Inference with Optimum

### What OpenVINO provides
OpenVINO (Open Visual Inference & Neural network Optimization) is Intel's inference optimization toolkit. The `optimum-intel` package wraps OpenVINO Runtime, providing `OVModelForXXX` classes with optimizations for Intel CPUs, NPUs, and integrated GPUs.

### Installation
```bash
pip install optimum[openvino]
```

### Core workflow
```python
from optimum.intel import OVModelForCausalLM
from transformers import AutoTokenizer

# Export and load
model = OVModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-1.5B-Instruct",
    export=True,
    device="CPU",
    ov_config={
        "PERFORMANCE_HINT": "LATENCY",     # LATENCY | THROUGHPUT | CUMULATIVE_THROUGHPUT
        "NUM_STREAMS": "1",                 # 1 for latency, >1 for throughput
        "INFERENCE_NUM_THREADS": "4",       # match physical core count
        "CACHE_DIR": "./ov_cache",          # model compilation cache (huge speedup!)
    },
)
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")

# Save compiled model for reuse
model.save_pretrained("./qwen-ov")
tokenizer.save_pretrained("./qwen-ov")

# Reload without re-compilation
model = OVModelForCausalLM.from_pretrained("./qwen-ov")
tokenizer = AutoTokenizer.from_pretrained("./qwen-ov")
```

### OVModelForXXX classes
| Task | Class |
|---|---|
| Causal LM | `OVModelForCausalLM` |
| Seq2Seq LM | `OVModelForSeq2SeqLM` |
| Sequence Classification | `OVModelForSequenceClassification` |
| Token Classification | `OVModelForTokenClassification` |
| Question Answering | `OVModelForQuestionAnswering` |
| Image Classification | `OVModelForImageClassification` |
| Masked LM | `OVModelForMaskedLM` |
| Speech Seq2Seq | `OVModelForSpeechSeq2Seq` |
| Feature Extraction | `OVModelForFeatureExtraction` |

### Performance hints — choose the right one

| Hint | Use Case | Behaviour |
|---|---|---|
| `LATENCY` | Interactive chatbots, real-time | Minimizes per-request latency. Single stream, pinned threads. |
| `THROUGHPUT` | Batch processing, offline | Maximizes requests/second. Multiple streams, async execution. |
| `CUMULATIVE_THROUGHPUT` | Mixed workloads | Balances latency and throughput. Adaptive stream count. |

### Weight compression (INT4/INT8) on OpenVINO

OpenVINO can compress model weights post-export without calibration data using the NNCF (Neural Network Compression Framework) backend:

```python
from optimum.intel import OVQuantizer, OVModelForCausalLM
from optimum.intel.configuration import OVQuantizationConfig

model = OVModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct", export=True)

# INT8 weight compression (default, no calibration needed)
quantizer = OVQuantizer.from_pretrained(model)
quantizer.quantize(save_directory="./qwen-ov-int8")

# INT4 weight compression — smaller but may lose accuracy
quantizer.quantize(
    quantization_config=OVQuantizationConfig(bits=4, sym=True, group_size=128),
    save_directory="./qwen-ov-int4",
)
```

INT4 group sizes: `128` (default, good balance), `64` (better accuracy, larger), `32` (best accuracy, even larger), `256` (smaller, potentially worse accuracy).

### Asynchronous inference pipeline

For maximum throughput on CPU, use async inference:

```python
import numpy as np
from optimum.intel import OVModelForCausalLM

model = OVModelForCausalLM.from_pretrained(
    "./qwen-ov",
    device="CPU",
    ov_config={
        "PERFORMANCE_HINT": "THROUGHPUT",
        "NUM_STREAMS": "4",
        "INFERENCE_NUM_THREADS": "4",
    },
)

# Async inference with InferRequest
infer_request = model.request  # OV InferRequest object
infer_request.set_input_tensor(input_tensor)
infer_request.start_async()
infer_request.wait()
output = infer_request.get_output_tensor().data
```

### OpenVINO vs ONNX Runtime — when to pick which

| Factor | ONNX Runtime CPU | OpenVINO (CPU) |
|---|---|---|
| **Best for** | Cross-platform, ARM, AMD CPUs | Intel CPUs specifically |
| **Quantization** | W8A8 static (calibration required) | INT4/INT8 weight (no calibration) |
| **Weight compression** | 2x (INT8) | 4x (INT4), 2x (INT8) |
| **Thread control** | intra/inter_op_num_threads | INFERENCE_NUM_THREADS + streams |
| **Caching** | Manual save/load of .onnx | Compilation cache (CACHE_DIR) |
| **LLM generation** | Single-token decode, batch=1 | Async streams for throughput |
| **Hardware reach** | x86, ARM64, RISC-V | Intel x86 only (AMD unsupported) |
| **Ease of use** | Moderate (session tuning) | Simpler (PERFORMANCE_HINT) |

**Rule of thumb for free-tier CPU inference:**
- Intel CPU → OpenVINO INT4 (4x model compression, minimal accuracy loss)
- AMD/ARM CPU → ONNX Runtime dynamic INT8 (2x compression, no calibration)
- Apple Silicon → ONNX Runtime with CoreML EP (not via Optimum, use `coremltools` directly)

---

## Deep Dive: ExecuTorch Edge Inference with Optimum

### What ExecuTorch provides
ExecuTorch is PyTorch's portable, on-device inference solution. The `optimum-executorch` package wraps it for Transformers models.

### Installation
```bash
pip install optimum[executorch]
```

### Export and run pipeline
```python
from optimum.executorch import ExecuTorchModelForCausalLM
from transformers import AutoTokenizer

model = ExecuTorchModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-0.5B-Instruct",
    export=True,
    quantize=True,        # applies INT8 dynamic quantization
    weights="qint8",
)
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")

# Save
model.save_pretrained("./qwen-et")
tokenizer.save_pretrained("./qwen-et")

# Reload on device
model = ExecuTorchModelForCausalLM.from_pretrained("./qwen-et")
```

### Backend delegation
ExecuTorch supports delegation to specialized backends:
- **XNNPACK** (CPU, default): quantized kernels for ARM/x86 CPUs
- **MPS** (Apple Metal): GPU acceleration on Apple Silicon
- **CoreML** (Apple Neural Engine): on-device with ANE

```python
model = ExecuTorchModelForCausalLM.from_pretrained(
    "./qwen-et",
    executorch_backend="xnnpack",
)
```

### When to use ExecuTorch vs ONNX Runtime vs OpenVINO

| Scenario | Choice | Reason |
|---|---|---|
| Server CPU (Intel) | OpenVINO INT4 | Best throughput with async streams |
| Server CPU (AMD/ARM) | ONNX Runtime INT8 | Cross-platform, mature quantization |
| Laptop/Desktop CPU | ONNX Runtime or OpenVINO | Depends on CPU vendor |
| Edge/Mobile (ARM) | ExecuTorch XNNPACK | Lightweight, no Python runtime needed |
| Apple Silicon (GPU) | ExecuTorch MPS or coremltools | Direct GPU/ANE access |
| Raspberry Pi | ONNX Runtime ARM64 | Best packaged support |
| Container/serverless | OpenVINO | Fast compile with CACHE_DIR |

---

## Deep Dive: CPU Inference Optimization Theory

### Why CPU inference is memory-bandwidth bound

For LLM inference, the main compute pattern is: load W (weights) × x (input activation) for each decoder layer. The computational intensity is:

```
Intensity = FLOPs / Bytes = (2 × M × K) / (4 × M × K) = 0.5 FLOPs/byte  (FP32)
```

A typical CPU can do ~200 GFLOPS but only has ~50 GB/s memory bandwidth. At 0.5 FLOPs/byte, the achievable throughput is capped at `50 GB/s × 0.5 = 25 GFLOPS` — far below peak compute. This means **quantization that reduces model size directly translates to linear speedup**.

| Precision | Weight size (7B model) | Relative speed |
|---|---|---|
| FP32 | 28 GB | 1.0× |
| FP16 | 14 GB | ~1.8× |
| INT8 | 7 GB | ~3.5× |
| INT4 | 3.5 GB | ~6× |

### Kernel fusion strategies

Both ONNX Runtime and OpenVINO apply graph optimizations:
1. **Operator fusion** — combine consecutive ops (e.g., LayerNorm → Add → Residual) into a single kernel
2. **Constant folding** — precompute static subgraphs at export time
3. **Layout optimization** — transpose weight matrices to cache-friendly format at load time
4. **Quantization-aware compute** — INT8 kernels that accumulate in INT32 and requantize in one pass

### KV cache optimization for CPU LLM

The KV cache grows linearly with sequence length and is the main memory consumer during generation.

```python
# On CPU, limit KV cache size to avoid OOM
model = ORTModelForCausalLM.from_pretrained(
    "./qwen-onnx",
    session_options=session_options,
    use_cache=True,
    use_merged_model=True,
)

# In generation, use short max_new_tokens
inputs = tokenizer("Hello,", return_tensors="pt")
outputs = model.generate(
    **inputs,
    max_new_tokens=512,     # CPU: keep short to avoid memory exhaustion
    use_cache=True,
    do_sample=False,        # greedy is fastest on CPU
)
```

Best practices for CPU LLM:
- **max_new_tokens ≤ 2048** — beyond that, KV cache dominates memory
- **Greedy decoding** — sampling adds overhead with negligible quality improvement on CPU
- **INT4 weights** — reduces memory pressure by 4× vs FP32
- **Single batch** — CPU can't exploit batch > 1 during autoregressive decode

### Production deployment checklist for CPU

1. Quantize (INT8 for ONNX Runtime, INT4 for OpenVINO)
2. Set thread count to physical core count (not logical/hyperthread count)
3. Enable model compilation / export caching (CACHE_DIR for OpenVINO, save_pretrained for ONNX)
4. Use merged model graph (Layer::forward fused into single ONNX node)
5. Limit KV cache growth with max_new_tokens
6. Profile before/after with `python -m cProfile` or `perf stat`
7. Test on target CPU architecture — AVX2 vs AVX-512 VNNI makes 2× difference
8. Warm-up run (1-2 forward passes) before benchmarking to amortize compilation overhead

### Resources
- https://huggingface.co/docs/optimum/index — Optimum official docs
- https://huggingface.co/docs/optimum/onnxruntime/overview — ONNX Runtime with Optimum
- https://huggingface.co/docs/optimum/intel/overview — OpenVINO with Optimum
- https://huggingface.co/docs/optimum/executorch/overview — ExecuTorch with Optimum
- https://onnxruntime.ai/docs/performance/tune-performance.html — ONNX Runtime tuning guide
- https://docs.openvino.ai/2024/performance-tuning-guide.html — OpenVINO tuning guide
