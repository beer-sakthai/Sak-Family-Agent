#!/bin/bash
# SakThai 1.5B Chat — runs locally on CPU via llama.cpp
# Usage: ./sakthai-chat.sh "your question here"

MODEL="/opt/data/models/sakthai-1.5b/gguf/sakthai-1.5b-Q4_K_M.gguf"
LLAMA="/opt/data/llama-bin/build/bin/llama-cli"
LIBDIR="/opt/data/llama-bin/build/bin"

if [ ! -f "$MODEL" ]; then
    echo "Downloading model..."
    mkdir -p /opt/data/models/sakthai-1.5b/gguf
    hf download Nanthasit/sakthai-context-1.5b-merged gguf/sakthai-1.5b-Q4_K_M.gguf \
        --local-dir /opt/data/models/sakthai-1.5b/gguf
fi

if [ "$#" -eq 0 ]; then
    # Interactive mode
    LD_LIBRARY_PATH="$LIBDIR" "$LLAMA" \
        -m "$MODEL" \
        -t 4 \
        -c 4096 \
        --chat-template chatml \
        --interactive
else
    # One-shot query
    LD_LIBRARY_PATH="$LIBDIR" "$LLAMA" \
        -m "$MODEL" \
        -p "$1" \
        -n 128 \
        -t 4 \
        --no-display-prompt 2>/dev/null
fi
