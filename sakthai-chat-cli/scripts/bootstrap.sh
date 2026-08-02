#!/usr/bin/env bash
# First-time setup for SakThai. Run from the repo root: ./scripts/bootstrap.sh
set -euo pipefail
trap 'echo "ERROR: bootstrap failed at line $LINENO" >&2; exit 1' ERR

cd "$(dirname "$0")/.."

# Require Python 3.11+.
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    echo "ERROR: Python 3.11+ required (found $(python3 --version 2>&1))" >&2
    exit 1
fi

# Install with whichever installer is available.
if command -v uv >/dev/null 2>&1; then
    uv pip install -e ".[dev]"
elif command -v pip >/dev/null 2>&1; then
    python3 -m pip install -e ".[dev]"
else
    echo "ERROR: no Python installer found. Install uv or pip." >&2
    exit 1
fi

# Seed a .env from the example if there isn't one yet.
if [ ! -f .env ] && [ -f .env.example ]; then
    cp .env.example .env
    echo "Created .env from .env.example — fill in ANTHROPIC_API_KEY."
fi

if command -v uv >/dev/null 2>&1; then
    uv run sakthai doctor
elif [ -f .venv/bin/sakthai ]; then
    .venv/bin/sakthai doctor
else
    sakthai doctor
fi
echo ""
echo "Done. Try: sakthai learn \"prefers dark mode\"  &&  sakthai recall dark"
