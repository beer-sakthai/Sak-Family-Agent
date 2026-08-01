#!/usr/bin/env bash
# Build the local Ollama "sakthai" model from the merged weights on Hugging Face.
#
# The model weights are NOT stored in git (they are ~1 GB and live on the Hub).
# This script is the durable, reproducible recipe: on any new machine it grabs
# the prebuilt quantized GGUF that ships inside the merged repo
# (gguf/sakthai-<size>-Q4_K_M.gguf) and registers it with Ollama as "sakthai" —
# exactly what `sakthai chat` expects. Only if the repo has no prebuilt GGUF
# does it fall back to converting the safetensors with llama.cpp.
#
# NOTE (fallback path): use llama.cpp's converter, NOT
# `ollama create FROM <safetensors dir>`. Ollama's built-in safetensors import
# mishandled this model's tokenizer and produced garbage ("??????"); the
# llama.cpp path below fixes that.
#
# Usage:
#   scripts/setup_local_model.sh            # 1.5B (default; prebuilt GGUF ~1 GB)
#   scripts/setup_local_model.sh 0.5b       # 0.5B (lighter, for low-RAM machines)
#
# Prereqs: Ollama (https://ollama.com) and Python. git only for the fallback.
set -euo pipefail

SIZE="${1:-1.5b}"                                    # 1.5b (default) or 0.5b
REPO="Nanthasit/sakthai-context-${SIZE}-merged"
WORK="${SAKTHAI_MODELS_DIR:-$HOME/sakthai-models}"
SRC="$WORK/sakthai-${SIZE}-merged"
LLAMACPP="${LLAMACPP_DIR:-$HOME/llama.cpp}"
PY="${PYTHON:-python3}"
mkdir -p "$WORK"

command -v ollama >/dev/null || { echo "ERROR: Ollama not installed — see https://ollama.com"; exit 1; }

echo "==> [1/3] Python deps (the prebuilt-GGUF path only needs huggingface_hub)"
$PY -m pip install -q --disable-pip-version-check huggingface_hub

echo "==> [2/3] Fetch prebuilt GGUF from $REPO"
GGUF="$($PY - "$REPO" "$SIZE" "$WORK" <<'PY'
import sys
from huggingface_hub import hf_hub_download
repo, size, work = sys.argv[1:4]
try:
    path = hf_hub_download(repo, f"gguf/sakthai-{size}-Q4_K_M.gguf", local_dir=work)
except Exception as exc:  # noqa: BLE001 - any failure means "use the fallback"
    print(f"no prebuilt GGUF ({exc})", file=sys.stderr)
else:
    print(path)
PY
)"

if [ -z "$GGUF" ]; then
  echo "==> Prebuilt GGUF not available — falling back to llama.cpp conversion"

  echo "==> [fallback 1/3] Python deps (conversion needs torch/transformers/gguf)"
  $PY -m pip install -q --disable-pip-version-check \
      huggingface_hub gguf safetensors numpy sentencepiece transformers \
      torch --extra-index-url https://download.pytorch.org/whl/cpu

  echo "==> [fallback 2/3] Download $REPO -> $SRC"
  $PY - "$REPO" "$SRC" <<'PY'
import sys
from huggingface_hub import snapshot_download
snapshot_download(sys.argv[1], local_dir=sys.argv[2],
    allow_patterns=["*.safetensors", "*.json", "tokenizer*", "*.model", "merges.txt", "vocab.json"])
PY

  echo "==> [fallback 3/3] Convert + quantize with llama.cpp"
  [ -f "$LLAMACPP/convert_hf_to_gguf.py" ] || git clone --depth 1 https://github.com/ggerganov/llama.cpp "$LLAMACPP"
  $PY "$LLAMACPP/convert_hf_to_gguf.py" "$SRC" --outfile "$WORK/sakthai-${SIZE}-f16.gguf" --outtype f16
  QUANT="$(command -v llama-quantize || echo /usr/local/lib/ollama/llama-quantize)"
  if [ -x "$QUANT" ]; then
    "$QUANT" "$WORK/sakthai-${SIZE}-f16.gguf" "$WORK/sakthai-${SIZE}-q4.gguf" Q4_K_M
    GGUF="$WORK/sakthai-${SIZE}-q4.gguf"
  else
    echo "   (no llama-quantize found; using f16 — larger/slower)"
    GGUF="$WORK/sakthai-${SIZE}-f16.gguf"
  fi
fi

echo "==> [3/3] Register with Ollama as 'sakthai' (ChatML template + stop token)"
MF="$(mktemp)"
cat > "$MF" <<EOF
FROM $GGUF
TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ range .Messages }}<|im_start|>{{ .Role }}
{{ .Content }}<|im_end|>
{{ end }}<|im_start|>assistant
"""
PARAMETER stop "<|im_end|>"
PARAMETER temperature 0.7
PARAMETER top_p 0.9
EOF
ollama create sakthai -f "$MF"
rm -f "$MF"

cat <<'DONE'

==> Done. Chat with it:
      export OLLAMA_HOST=http://127.0.0.1:11434   # add to ~/.bashrc to make permanent
      sakthai chat
DONE
