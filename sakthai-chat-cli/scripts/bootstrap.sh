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

# Require uv (https://docs.astral.sh/uv/) for reproducible local environment setup.
if ! command -v uv >/dev/null 2>&1; then
    echo "ERROR: uv is required for SakThai bootstrap (https://docs.astral.sh/uv/)." >&2
    echo "Install uv via: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

uv pip install -e ".[dev]"

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
