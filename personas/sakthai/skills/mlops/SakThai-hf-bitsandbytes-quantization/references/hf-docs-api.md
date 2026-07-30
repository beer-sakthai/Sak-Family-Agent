# bitsandbytes HF Docs — Extracted API Reference

Source: https://huggingface.co/docs/transformers/en/quantization/bitsandbytes (v5.14.0)

## BitsAndBytesConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `load_in_8bit` | bool | False | Enable 8-bit quantization (LLM.int8()) |
| `load_in_4bit` | bool | False | Enable 4-bit quantization |
| `llm_int8_threshold` | float | 6.0 | Outlier threshold for LLM.int8() |
| `llm_int8_skip_modules` | list | None | Module names to skip during 8-bit quantization |
| `llm_int8_enable_fp32_cpu_offload` | bool | False | Offload to CPU in fp32 |
| `bnb_4bit_compute_dtype` | torch.dtype | torch.float32 | Compute dtype for 4-bit (use bf16 for speed) |
| `bnb_4bit_quant_type` | str | "fp4" | "fp4" or "nf4" (NF4 from QLoRA paper, best for training) |
| `bnb_4bit_use_double_quant` | bool | False | Nested quantization (saves ~0.4 bits/param) |

## Hardware Support
- NVIDIA GPUs (CUDA): sm_52+ (Compute Capability 5.2+)
- Intel GPUs (XPU): via Intel Extension for PyTorch
- Intel Gaudi (HPU): via SynapseAI
- CPU: limited support for 8-bit optimizers

## QLoRA Training — Key Details
- For training, do NOT pass `device_map` — model auto-loads on GPU
- Use `bnb_4bit_quant_type="nf4"` for training (from QLoRA paper)
- NF4 is adapted for weights initialized from a normal distribution
- Double quantization adds no performance cost but saves memory

## Dequantization
```python
model.dequantize()  # May lose quality, requires enough GPU memory
```

## Example: Llama-13b on 16GB T4
```python
double_quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
)
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-13b-chat-hf",
    dtype="auto",
    quantization_config=double_quant_config,
)
```

## Resources
- QLoRA paper: https://hf.co/papers/2305.14314
- Blog (4-bit): https://huggingface.co/blog/4bit-transformers-bitsandbytes
- Blog (8-bit): https://huggingface.co/blog/hf-bitsandbytes-integration
- Notebook: https://colab.research.google.com/drive/1ge2F1QSK8Q7h0hn3YKuBCOAS0bK8E0wf
- License: MIT
