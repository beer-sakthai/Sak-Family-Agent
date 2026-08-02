---
name: SakThai-hf-gguf-llama-cpp
description: "GGUF model format on Hugging Face — loading GGUF files via Transformers, conversion between HF and GGUF, deployment with llama.cpp, supported quantization types, and the Hub ecosystem of GGUF models."
---

# GGUF / llama.cpp on Hugging Face

GGUF (GPT-Generated Unified Format) is a single-file model format for inference with GGML, a fast C/C++ inference framework. GGUF is the standard format for running local LLMs on consumer hardware via llama.cpp.

## Key Concepts

### What GGUF is

- **Single file** containing model metadata (architecture, tokenizer config, hyperparameters) and all tensors
- **Quantization-aware**: supports many quantized data types (Q2_K through Q8_0, IQ1_S through IQ4_NL) 
- **Portable**: runs on CPU, GPU (CUDA/Metal/Vulkan), and hybrid setups
- **Interchange format**: models from the Hub can be loaded in both GGUF and native HF format

### Supported Architectures (Transformers)

Transformers can load GGUF files for: Llama, Mistral, Qwen2, Qwen2Moe, Phi3, Bloom, Falcon, StableLM, GPT2, Starcoder2, and many more (see `src/transformers/integrations/ggml.py` in Transformers source).

## Loading GGUF in Transformers

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
filename = "tinyllama-1.1b-chat-v1.0.Q6_K.gguf"

dtype = torch.float32  # can be float16 or bfloat16
tokenizer = AutoTokenizer.from_pretrained(model_id, gguf_file=filename)
model = AutoModelForCausalLM.from_pretrained(model_id, gguf_file=filename, dtype=dtype)
```

**Important**: GGUF checkpoints are **dequantized to fp32** — full weights are available and compatible with PyTorch for further training/fine-tuning.

## Converting Between Formats

### HF → GGUF (for llama.cpp inference) — Refined Pipeline

The official `convert_hf_to_gguf.py` script requires the `gguf-py` package and `sentencepiece`. Use this tested pipeline instead of building from CMake:

```bash
# 1. Install dependencies
pip install gguf sentencepiece protobuf

# 2. Download convert script from llama.cpp repo
curl -sL "https://raw.githubusercontent.com/ggml-org/llama.cpp/refs/heads/master/convert_hf_to_gguf.py" -o convert_hf_to_gguf.py

# 3. Convert HF model → FP16 GGUF
python3 convert_hf_to_gguf.py ./hf-model-dir \
    --outfile ./model-f16.gguf --outtype f16

# 4. Quantize to Q4_K_M
/path/to/llama-quantize ./model-f16.gguf ./model-Q4_K_M.gguf Q4_K_M
```

**GGUF file size reference (Q4_K_M):**

| Model | Q4_K_M Size |
|-------|-------------|
| 0.5B (Qwen2.5) | **380 MB** |
| 1.5B (Qwen2.5) | **934 MB** |
| Code 1.5B | **1.12 GB** |
| Vision 7B (LLaVA) | **3.9 GB** |
| TTS Kokoro 82M (Q8_0) | **141 MB** |

### GGUF → HF (for training/fine-tuning)

Already shown above — use `gguf_file=filename` in `from_pretrained()`.

## Quantization Types (Q-suffix naming)

| Suffix | Description | Relative Size |
|--------|-------------|---------------|
| Q2_K   | 2-bit quantization | Smallest |
| Q3_K_S/M/L | 3-bit small/med/large | |
| Q4_K_S/M | 4-bit small/medium (popular quality/size tradeoff) | ~4.5 GB for 7B |
| Q5_K_S/M | 5-bit small/medium | ~5.5 GB for 7B |
| Q6_K   | 6-bit | ~6 GB for 7B |
| Q8_0   | 8-bit | ~7.5 GB for 7B |
| F16    | Full half-precision | ~14 GB for 7B |

**Recommended**: Q4_K_M for best quality-to-size ratio on consumer hardware.

## HF Hub Ecosystem

- Thousands of GGUF models hosted on the Hub (by TheBloke, bartowski, mradermacher, and many community members)
- Search: `hf models search gguf` or visit https://huggingface.co/models?search=gguf
- GGUF model repos typically contain multiple quantization variants as separate files
- The `gguf` file extension is detected by transformers when passed as `gguf_file=filename`

## Running GGUF with llama.cpp

```bash
# Install
brew install llama.cpp  # macOS
# Or build from source: https://github.com/ggerganov/llama.cpp

# Run
./main -m model.gguf -p "Your prompt here" -n 512

# Server mode (OpenAI-compatible API)
./server -m model.gguf --host 0.0.0.0 --port 8080
```

## Running GGUF with llama.cpp — Pre-Built Binary (No Compile)

Building llama.cpp or llama-cpp-python from source takes 5+ min without GPU. Use pre-built binaries instead:

```bash
# Download (~30 MB) and extract
curl -sL "https://github.com/ggml-org/llama.cpp/releases/download/b5021/llama-b5021-bin-ubuntu-x64.zip" -o /tmp/llama.zip
python3 -c "import zipfile; zipfile.ZipFile('/tmp/llama.zip').extractall('llama-bin')"

# One-shot inference
cd llama-bin/build/bin
LD_LIBRARY_PATH=. ./llama-cli -m /path/to/model.gguf -p "Your prompt" -n 128 -t 4 --no-display-prompt

# Interactive chat
LD_LIBRARY_PATH=. ./llama-cli -m model.gguf -t 4 -c 4096 --chat-template chatml --interactive
```

**Key flags:**
- `-no-cnv`: disable conversation mode (one-shot, prevents interactive hang)
- `LD_LIBRARY_PATH=.`: required — shared libraries (libllama.so, libggml.so) are in the binary directory
- `-t 4`: CPU threads; match to available cores
- `--no-display-prompt`: output only the generated text

**Check if model repo already has a GGUF file:**
```bash
curl -sI "https://huggingface.co/username/model-name/resolve/main/gguf/model-Q4_K_M.gguf"
# HTTP 200 = available; HTTP 404 = create one via convert_hf_to_gguf.py
```

For BFCL-style tool-calling benchmarks, local setup details, and scoring — see `references/cpu-gguf-deployment.md`.

## Pitfalls

1. **GGUF is inference-oriented**: loading in Transformers dequantizes to fp32 — don't expect memory savings in training mode
2. **File selection**: Always match the exact filename; repos contain many GGUF variants
3. **Conversion round-trips**: Converting HF→GGUF→HF loses quantization metadata (the weights become full-precision)
4. **llama.cpp version**: Use a recent version of llama.cpp for best architecture support and performance
5. **llama.cpp CLI does NOT support structured function calling**: The CLI generates free text. It cannot produce OpenAl `tool_calls` JSON output natively. Even if the GGUF model has a chat template with function calling support, llama.cpp CLI will not enforce JSON output structure. To test function calling, use:
   - Ollama API (import GGUF and call via `/api/chat` with tools parameter)
   - HF Transformers pipeline (applies chat template with tool schema)
   - llama.cpp server mode (`llama-server`) with grammar-constrained generation
   Do NOT claim function calling scores based on llama.cpp CLI text output — it tests text generation, not tool-calling capability.
6. **llama-cli runaway on CPU