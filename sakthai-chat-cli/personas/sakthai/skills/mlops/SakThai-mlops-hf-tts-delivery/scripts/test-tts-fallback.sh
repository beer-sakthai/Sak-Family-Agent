#!/bin/bash
# Safe fallback test for TTS delivery
# Run this after config change to verify if voice can be generated

echo "Testing TTS fallback..."

# Test if espeak exists
if command -v espeak >/dev/null 2>&1; then
    echo "✓ espeak found"
    espeak -v en-us "Voice delivery is active" --stdout | ffmpeg -f wav -i - -acodec libopus -application audio -f ogg /tmp/test.ogg 2>/dev/null && echo "✓ Fallback audio generated" || echo "✗ ffmpeg failed"
else
    echo "✗ espeak not found - fallback unavailable"
fi

# Test if ffmpeg exists
if command -v ffmpeg >/dev/null 2>&1; then
    echo "✓ ffmpeg found"
else
    echo "✗ ffmpeg not found"
fi

# Output suggestion
if [ ! -f "/tmp/test.ogg" ]; then
    echo "💡 Suggestion: Install espeak and ffmpeg manually in WSL:"
    echo "  sudo apt update && sudo apt install espeak ffmpeg"
    echo "  (Requires sudo - not possible in this environment)"
fi