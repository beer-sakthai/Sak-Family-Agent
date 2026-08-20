# HF → GGUF Conversion Notes

Step-by-step for converting a HuggingFace model to GGUF format for local inference.

## Full pipeline

```bash
# 1. Setup llama.cpp
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build && cmake --build build --config Release -j$(nproc)

# 2. Create Python venv with conversion deps
uv venv .venv
source .venv/bin/activate
uv pip install torch numpy transformers sentencepiece huggingface_hub

# 3. Download model (if not already local)
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(repo_id='org/model-name', local_dir='./model-dir')
"

# 4. Convert to FP16 GGUF
python3 convert_hf_to_gguf.py ./model-dir \
    --outfile ./model-dir/model-f16.gguf \
    --outtype f16

# 5. Quantize
build/bin/llama-quantize \
    ./model-dir/model-f16.gguf \
    ./model-dir/model-Q4_K_M.gguf \
    Q4_K_M

# 6. Upload to HF
python3 -c "
from huggingface_hub import HfApi, login
import os
login(token=os.environ['HF_TOKEN'])
api = HfApi()
api.upload_file(
    path_or_fileobj='./model-dir/model-Q4_K_M.gguf',
    path_in_repo='gguf/model-Q4_K_M.gguf',
    repo_id='org/model-name',
    repo_type='model',
    commit_message='Add Q4_K_M GGUF quant'
)
print('Done')
"
```

## Time estimates

| Model size | Convert (CPU) | Quantize (CPU) | Total |
|-----------|---------------|----------------|-------|
| 1.5B (3 GB FP16) | 1 min | 1 min | ~2 min |
| 7B (14 GB FP16) | 5 min | 5 min | ~10 min |
| 70B (140 GB FP16) | 40 min | 45 min | ~1.5 hrs |

## Key flags

| Flag | Purpose |
|------|---------|
| `--outtype f16` | FP16 output (balanced size/quality). Never use f32 — 2× size. |
| `Q4_K_M` | Recommended default quant — good quality/size balance |
| `Q5_K_M` | Higher quality, slightly larger |
| `Q8_0` | Near-lossless, ~2× size of Q4 |
| `--allow-requantize` | Only needed if input is already quantized (FP16 → Q4 doesn't need it) |

## Common issues

- **"ModuleNotFoundError: No module named 'torch'"**: Run convert from venv with torch installed, not from system Python
- **"Unable to mmap"**: Model file may be corrupt or disk full. Check with `python3 -c "import gguf; gguf.GGUFReader('model.gguf')"`
- **OOM**: Use `--concurrency 1` for large models
- **Interactive mode hanging**: llama-cli enters interactive mode after generating. Send `<ctrl+d>` / EOF via stdin or use `--no-display-prompt` and pipe `input="\n"` in subprocess
- **`--no-interactive` not a valid flag**: This flag doesn't exist in many llama.cpp builds. Instead, pipe input via subprocess and strip the banner (lines starting with `> `, ASCII art, "build" info, "available commands").
- **HF_TOKEN sourcing**: Check `~/.env` or `/opt/data/.env` as a secondary source with `set -a; source /opt/data/.env; set +a` before Python scripts if `HF_TOKEN` isn't set in the current shell.
- **Exit code 137 (SIGKILL/OOM on low-RAM)**: Model + KV cache exceeds available RAM. Reduce `--ctx-size`, remove `--mlock` (which disables swapping and can trigger OOM-killer on low-RAM hosts), or process in smaller chunks.
