# Refined GGUF Conversion Pipeline (2026-07-24)

Builds on `gguf-conversion.md` with the updated approach using pre-built llama.cpp binaries and `convert_hf_to_gguf.py` from the llama.cpp source (no CMake build needed).

## Overview

```
HF safetensors → convert_hf_to_gguf.py → FP16 GGUF → llama-quantize → Q4_K_M GGUF
                (Python, pip packages)         (pre-built binary)
```

## Prerequisites

```bash
# 1. Install Python dependencies
source .venv-sakthai/bin/activate  # or any venv
uv pip install gguf sentencepiece protobuf

# 2. Download convert script from llama.cpp source
curl -sL "https://raw.githubusercontent.com/ggml-org/llama.cpp/refs/heads/master/convert_hf_to_gguf.py" \
  -o convert_hf_to_gguf.py

# 3. Download llama.cpp source (for conversion module)
curl -sL "https://github.com/ggml-org/llama.cpp/archive/refs/heads/master.tar.gz" -o /tmp/llama.tar.gz
tar xzf /tmp/llama.tar.gz -C /tmp/

# 4. Install gguf-py from the source (ensures compatible version)
uv pip install /tmp/llama.cpp-master/gguf-py/

# 5. Download pre-built llama.cpp binary (no compilation)
# Get latest from https://github.com/ggml-org/llama.cpp/releases
curl -sL "https://github.com/ggml-org/llama.cpp/releases/download/b5021/llama-b5021-bin-ubuntu-x64.zip" \
  -o /tmp/llama.zip
python3 -c "import zipfile; zipfile.ZipFile('/tmp/llama.zip').extractall('llama-bin')"
```

## Step 1: HF → FP16 GGUF

```bash
source .venv-sakthai/bin/activate
uv run python3 /tmp/llama.cpp-master/convert_hf_to_gguf.py \
  --outfile ./model-f16.gguf \
  --outtype f16 \
  /path/to/hf-model-directory
```

This converts the Hugging Face safetensors format to an unquantized FP16 GGUF file. 
Output size is roughly 2× the Q4_K_M size (e.g. 0.5B = 988 MB FP16 → 380 MB Q4_K_M).

## Step 2: FP16 → Q4_K_M Quantization

```bash
LD_LIBRARY_PATH=llama-bin/build/bin \
  llama-bin/build/bin/llama-quantize \
  ./model-f16.gguf \
  ./model-Q4_K_M.gguf \
  Q4_K_M \
  4  # threads
```

## Step 3: Test Inference

```bash
LD_LIBRARY_PATH=llama-bin/build/bin \
  llama-bin/build/bin/llama-cli \
  -m ./model-Q4_K_M.gguf \
  -p "Hello" -n 32 -t 4 --no-display-prompt
```

For tool-calling tests, use the ChatML format with `<tools>` XML tags:

```bash
LD_LIBRARY_PATH=llama-bin/build/bin \
  llama-bin/build/bin/llama-cli \
  -m ./model-Q4_K_M.gguf \
  -no-cnv \
  -p "<|im_start|>system\nYou are an assistant with tools.\n<tools>{\"type\":\"function\",\"function\":{\"name\":\"get_weather\",\"parameters\":{\"type\":\"object\",\"properties\":{\"location\":{\"type\":\"string\"}},\"required\":[\"location\"]}}}</tools><|im_end|>\n<|im_start|>user\nWeather in Paris?<|im_end|>\n<|im_start|>assistant\n" \
  -n 96 -t 4 --temp 0.1 --no-display-prompt
```

## Upload to HF

```python
from huggingface_hub import HfApi
api = HfApi()
api.upload_file(
    path_or_fileobj='./model-Q4_K_M.gguf',
    path_in_repo='gguf/model-Q4_K_M.gguf',
    repo_id='your-username/model-name',
    repo_type='model',
    commit_message='Add Q4_K_M GGUF for CPU inference'
)
```

## Model Size Reference

| Size | FP16 GGUF | Q4_K_M GGUF | CPU RAM | Speed (2-core) |
|------|-----------|-------------|---------|----------------|
| 0.5B | ~988 MB | **~380 MB** | ~400 MB | ~10 tok/s |
| 1.5B | — | **~934 MB** | ~940 MB | ~4 tok/s |
| 7B | — | ~4.5 GB | ~5 GB | ❌ Too large |

## Common Issues

- **`ModuleNotFoundError: No module named 'sentencepiece'`** — Install: `uv pip install sentencepiece protobuf`
- **`ModuleNotFoundError: No module named 'conversion'`** — The `convert_hf_to_gguf.py` script imports from the llama.cpp source tree. Run it via `uv run python3 /path/to/llama.cpp-master/convert_hf_to_gguf.py` (from within the extracted source directory), OR install the full gguf-py package from source.
- **`llama-quantize` API change**: The `Q4_K_M` quantization type with 896-dimension tensors may fall back to Q5_0/Q6_K/Q8_0 for tensors not divisible by 256. This is normal and produces a slightly larger file.
- **`LD_LIBRARY_PATH` required**: The pre-built `llama-cli` and `llama-quantize` binaries need `libllama.so` from the same directory. Always set `LD_LIBRARY_PATH=llama-bin/build/bin` before running.
