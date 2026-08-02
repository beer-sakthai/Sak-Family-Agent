# GGUF CPU Inference with Pre-built llama.cpp

When you need to run a GGUF model locally on CPU without compiling llama-cpp-python (which is slow or may fail on certain Python versions/architectures), use a **pre-built binary release** from GitHub.

## Download Pre-built llama.cpp

```bash
# Download latest release for Ubuntu x64
curl -sL "https://github.com/ggml-org/llama.cpp/releases/download/b5021/llama-b5021-bin-ubuntu-x64.zip" -o /tmp/llama.zip

# Extract (Python zipfile is always available)
python3 -c "
import zipfile
with zipfile.ZipFile('/tmp/llama.zip') as z:
    z.extractall('llama-bin')
"

# Run inference
LD_LIBRARY_PATH=llama-bin/build/bin ./llama-bin/build/bin/llama-cli \
    -m /path/to/model.gguf \
    -p "Your prompt" -n 128 -t 4 --no-display-prompt
```

## One-shot Inference

```bash
MODEL="/path/to/model.gguf"
LLAMA="./llama-bin/build/bin/llama-cli"
LIBDIR="./llama-bin/build/bin"

LD_LIBRARY_PATH="$LIBDIR" "$LLAMA" \
    -m "$MODEL" \
    -p "$1" \
    -n 128 \
    -t 4 \
    --no-display-prompt 2>/dev/null
```

## Interactive Chat

```bash
LD_LIBRARY_PATH="$LIBDIR" "$LLAMA" \
    -m "$MODEL" \
    -t 4 \
    -c 4096 \
    --chat-template chatml \
    --interactive
```

## Important Flags

| Flag | Purpose |
|------|---------|
| `-m` | Path to GGUF file |
| `-n N` | Max tokens to generate |
| `-t N` | CPU threads (use 4 for typical server) |
| `-c N` | Context size (4096 default, 32768 max for Qwen2.5) |
| `--no-display-prompt` | Suppress prompt echo in output |
| `--chat-template chatml` | Use ChatML format for multi-turn |
| `--interactive` | Interactive conversation mode |
| `--stop "<\|im_end\|>"` | Stop token for ChatML models (prevents runaway generation) |

## Memory Requirements

| Quantization | 1.5B Model | 7B Model |
|-------------|-----------|----------|
| Q4_K_M | ~934 MB | ~4.5 GB |
| Q8_0 | ~1.7 GB | ~7.8 GB |
| F16 | ~3.0 GB | ~14 GB |

## Pitfalls

- **LD_LIBRARY_PATH**: The pre-built binaries need `libllama.so` in the same directory. Always set `LD_LIBRARY_PATH=./build/bin` or `cd` into the binary directory.
- **Interactive mode hangs**: llama-cli enters interactive mode by default when no explicit prompt is given. For programmatic use, always pass `-p "..."` and `-n` to limit output.
- **Runaway generation**: Use `--stop "<|im_end|>"` for ChatML models. Without it, the model generates tokens indefinitely.
- **No GPU**: These flags run entirely on CPU. For GPU inference, add `-ngl N` where N is the number of layers to offload to GPU.
