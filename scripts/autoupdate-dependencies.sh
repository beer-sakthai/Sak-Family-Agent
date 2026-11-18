#!/bin/bash
set -euo pipefail

# autoupdate-dependencies.sh
# Wrapper for mtl1979/dependencies-autoupdate to avoid positional argument word-splitting.

CMD="${UPDATE_COMMAND:-uv lock --upgrade}"
echo "Running dependency update command: $CMD"
eval "$CMD"
