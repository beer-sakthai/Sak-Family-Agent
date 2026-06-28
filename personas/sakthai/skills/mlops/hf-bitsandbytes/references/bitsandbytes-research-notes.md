# BNB Research Notes

## Installation Matrix (source: HF docs v0.49.2, 2026-06-21)

| Platform | Min PyTorch | Install | Notes |
|----------|-------------|---------|-------|
| NVIDIA CUDA | 2.4+ | `pip install bitsandbytes` | CC ≥ 6.0 for 4/8-bit; CC ≥ 7.5 for LLM.int8() |
| NVIDIA Jetson (L4T) | 2.4+ | source build | CUDA ABI mismatch; compile on-device with `-DCOMPUTE_CAPABILITY=87` |
| Intel XPU | 2.6+ | `pip install bitsandbytes` | SYCL + Triton kernels |
| Intel Gaudi | Gaudi v1.21 | `pip install bitsandbytes` | |
| CPU | 2.4+ | `pip install bitsandbytes` | AVX2 on x86; ARM NEON on arm64 |
| AMD ROCm (preview) | latest ROCm | `pip install bitsandbytes` | RDNA: gfx1100+; CDNA: gfx90a+ |

## Integration Snippets

### Accelerate (non-Transformers PyTorch)
```python
from accelerate import init_empty_weights
from accelerate.utils import BnbQuantizationConfig, load_and_quantize_model

with init_empty_weights():
    model = MyModel(config)

bnb_config = BnbQuantizationConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)

quantized_model = load_and_quantize_model(
    model,
    weights_location=weights_location,
    bnb_quantization_config=bnb_config,
    device_map="auto",
)
```

### PEFT + QLoRA
```python
from peft import prepare_model_for_kbit_training, LoraConfig, get_peft_model

model = prepare_model_for_kbit_training(model_4bit)
lora_config = LoraConfig(
    r=16, lora_alpha=8,
    target_modules="all-linear",
    lora_dropout=0.05, bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model_4bit, lora_config)
```

### 8-bit Optimizer via Trainer
```python
training_args = TrainingArguments(
    optim="paged_adamw_32bit",  # paged states reduce optimizer memory
)
```

## 4-bit Quantizer Modules
- `bitsandbytes.nn.Linear4bit` — base 4-bit quantized linear (FP4 or NF4)
- `bitsandbytes.nn.LinearFP4` — explicit FP4 data type
- `bitsandbytes.nn.LinearNF4` — explicit NF4 data type (normalized bins under N(0,1))
- `bitsandbytes.nn.Params4bit` — parameter container for 4-bit state

## Key Facts
- **NF4** is preferred for LLMs because it calibrates quantization bins to a standard normal distribution.
- **Double quantization** quantizes the quantization constants themselves, saving ~0.37 bits/parameter.
- **bfloat16** is the optimal compute dtype on Ampere+ GPUs. float16 risks inf/nan; float32 is safe but slow.
- **FlashAttention v2** works with 4-bit; FlashAttention v3 is not yet universally compatible.
- **Jetson L4T** cannot use standard Linux aarch64 wheels — mismatch is in CUDA library/ABI layer, not cubins.

## Authoritative Sources
- `https://huggingface.co/docs/bitsandbytes/main/en/index`
- `https://huggingface.co/docs/bitsandbytes/main/en/quickstart`
- `https://huggingface.co/docs/bitsandbytes/main/en/integrations`
- `https://huggingface.co/docs/bitsandbytes/main/en/reference/nn/linear4bit`
- GitHub: `https://github.com/bitsandbytes-foundation/bitsandbytes`
- QLoRA paper: `https://arxiv.org/abs/2305.14314`
