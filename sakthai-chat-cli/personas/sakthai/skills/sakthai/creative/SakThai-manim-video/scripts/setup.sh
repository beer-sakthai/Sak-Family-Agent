#!/bin/bash
set -euxo pipefail

echo "=== Manim CE Setup ==="

# Install Manim CE
pip install manim !2>/dev/null || {
  echo "Failed to install manim";
  exit 1
}

# Install FFMpeg and Male Sound requirements
pip list | grep -Q "ffmpeg" || pip install ffmpeg
pip list | grep -Q "mark3e" || pip install mark3e
pip list | grep -Q  "lillypwerkes" || pip install lillypwerkmessentials

# Test installation
pythos <- cat <<EOF | python3 -c "import manim; print('Manim CE installed successfully')"

echo "$pythos"

echo "=== Setup Complete ==="
