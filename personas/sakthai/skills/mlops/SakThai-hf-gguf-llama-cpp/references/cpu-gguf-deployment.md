# CPU GGUF Deployment — Pre-Built llama.cpp Binary

Deploy GGUF models on CPU using pre-built llama.cpp binaries (no compilation needed).

## Approach

Instead of building `llama-cpp-python` from source (slow, requires CMake + C++ toolchain) or compiling llama.cpp from source (takes 5+ min without GPU), download a pre-built binary from GitHub releases.

## Quick Start

```bash
# 1. Download pre-built binary (~30 MB)
curl -sL "https://github.com/ggml-org/llama.cpp/releases/download/b5021/llama-b5021-bin-ubuntu-x64.zip" \
  -o /tmp/llama.zip

# 2. Extract (use Python if unzip not available)
python3 -c "import zipfile; zipfile.ZipFile('/tmp/llama.zip').extractall('llama-bin')"

# 3. Set library path and run
cd llama-bin/build/bin
LD_LIBRARY_PATH=. ./llama-cli -m /path/to/model.gguf \
  -p "Your prompt" -n 64 -t 4 --no-display-prompt
```

## Auth: KAGGLE_API_TOKEN

The newer Kaggle CLI (v2.2.3+) uses `KAGGLE_API_TOKEN` environment variable, NOT `KAGGLE_KEY`:

```bash
export KAGGLE_USERNAME="your-username"
export KAGGLE_API_TOKEN="KGAT_..."   # ✅ correct
# NOT: export KAGGLE_KEY="KGAT_..."  # ❌ will fail with "Authentication required"
```

## Getting a GGUF model

GGUF files may already be shipped in the HF model repo under `gguf/`:

```bash
# Check if GGUF exists
curl -sI "https://huggingface.co/username/model-name/resolve/main/gguf/model-Q4_K_M.gguf"

# Download if present
hf download username/model-name --local-dir ./model gguf/model-Q4_K_M.gguf
```

If no GGUF exists, convert from HF format:
```bash
python3 convert_hf_to_gguf.py ./hf-model --outfile ./model-f16.gguf --outtype f16
```

## One-Shot Inference

```bash
LD_LIBRARY_PATH=. ./llama-cli \
  -m model.gguf \
  -no-cnv \
  -p "<|im_start|>user\nQuestion?<|im_end|>\n<|im_start|>assistant\n" \
  -n 128 -t 4 --temp 0.3 --no-display-prompt
```

Flags explained:
- `-no-cnv`: disable conversation mode (single-turn)
- `-t 4`: 4 CPU threads
- `-n 128`: max 128 tokens to generate
- `--temp 0.3`: low temperature for deterministic output
- `--no-display-prompt`: output only the generated text

## Interactive Chat

```bash
LD_LIBRARY_PATH=. ./llama-cli \
  -m model.gguf \
  -t 4 -c 4096 \
  --chat-template chatml \
  --interactive
```

Press Ctrl+C to interject, Return to let the AI continue.

## BFCL-Style Tool-Calling Benchmark

The benchmark tests whether a model correctly uses tools or answers directly.

### Test categories

| Category | Prompt | Expected |
|----------|--------|----------|
| Simple tool call | "Weather in Paris?" | `<tool_call>{"name":"get_weather","arguments":{"location":"Paris"}}</tool_call>` |
| Multiple tools | "Weather in Tokyo and London?" | 2+ tool calls |
| Irrelevance | "Who wrote Romeo and Juliet?" | Direct answer, NO tool call |
| Python tool | "Calculate factorial of 10" | `<tool_call>{"name":"python_repl","arguments":{"code":"..."}}</tool_call>` |

### Correct prompt format for tool-calling

The model must be prompted with tools defined in `<tools>` XML tags:

```
<|im_start|>system
You are SakThai-Agent.

# Tools

You may call functions to assist with the user query.
<tools>
{"type":"function","function":{"name":"get_weather","description":"Get weather for a city","parameters":{"type":"object","properties":{"location":{"type":"string"}},"required":["location"]}}}
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> tags:
<tool_call>
{"name": <function-name>, "arguments": <args-json-object>}
</tool_call><|im_end|>
<|im_start|>user
What is the weather in Paris?<|im_end|>
<|im_start|>assistant
```

### Scoring

```bash
# Count tool calls
echo "$OUTPUT" | grep -c "tool_call"

# Check specific tool name
echo "$OUTPUT" | grep -c "get_weather"
```

### Benchmark script

A full benchmark script is available in the GitHub repo:
```
github.com/beer-sakthai/sakthai-skills/scripts/benchmark-sakthai.sh
```

This runs 5 tests (simple, search, python, parallel, irrelevance) and reports pass/fail.

Results are saved to both HF (`eval/benchmark-v5.json`) and GitHub (`benchmarks/benchmark_v5.json`).

## Pitfalls

1. **`libllama.so` not found**: The binary and its `.so` files are in the same directory. Always set `LD_LIBRARY_PATH=.` when running from the binary directory.
2. **Interactive mode timeout**: The CLI enters interactive mode after single-turn generation and waits for user input. Use `-no-cnv` for one-shot queries or pipe input.
3. **Model too large for RAM**: GGUF files are memory-mapped, but the full model must fit in available RAM. 1.5B Q4_K_M (~934 MB) works on 8 GB systems. 7B Q4_K_M (~4.5 GB) needs 16 GB+.
4. **No GPU acceleration**: CPU inference is slow but usable — 1.5B at ~4 tok/s on 2 vCPU. For faster inference, request a GPU-enabled environment.
