#!/bin/bash
# SakThai 1.5B Inference — optimal settings for tool-calling
# Usage: ./sakthai-infer.sh "Your question here"
LLAMA="/opt/data/llama-bin/build/bin/llama-cli"
LIB="/opt/data/llama-bin/build/bin"
MODEL="/opt/data/models/sakthai-1.5b-merged/sakthai-1.5b-Q4_K_M.gguf"

SYSTEM="You are a function-calling assistant. Respond with tool_calls JSON when appropriate."

if [ $# -eq 0 ]; then
  echo "Usage: $0 \"Your question\""
  echo "Example: $0 \"What is the weather in Tokyo?\""
  exit 1
fi

LD_LIBRARY_PATH="$LIB" "$LLAMA" -m "$MODEL" -no-cnv \
  -p "<|im_start|>system\n$SYSTEM\n<tools>\n<tool>get_weather(location)</tool>\n<tool>search_web(query)</tool>\n<tool>calculate(expression)</tool>\n<tool>get_time(timezone)</tool>\n</tools><|im_end|>\n<|im_start|>user\n$1<|im_end|>\n<|im_start|>assistant\n" \
  -n 128 -t 2 --temp 0.1 --no-display-prompt 2>/dev/null
