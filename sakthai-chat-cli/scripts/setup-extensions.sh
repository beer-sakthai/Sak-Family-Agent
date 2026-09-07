#!/usr/bin/env bash
# Build any installed extensions that need a compile step.
#
# `sakthai extensions install <git-url>` clones extensions into
# ${SAKTHAI_HOME:-~/.sakthai}/extensions. Most are ready to use as-is; this
# script runs `npm install && npm run build` for any that ship a Node MCP
# server (a package.json with a "build" script).
set -euo pipefail

EXT_DIR="${SAKTHAI_HOME:-$HOME/.sakthai}/extensions"

if [ ! -d "$EXT_DIR" ]; then
    echo "No extensions directory at $EXT_DIR — nothing to build."
    echo "Install one with: sakthai extensions install <git-url>"
    exit 0
fi

built=0
for pkg in "$EXT_DIR"/*/package.json "$EXT_DIR"/*/*/package.json; do
    [ -f "$pkg" ] || continue
    dir="$(dirname "$pkg")"
    if grep -q '"build"' "$pkg"; then
        echo ">>> Building $(basename "$(dirname "$dir")")/$(basename "$dir")…"
        (cd "$dir" && npm install --silent && npm run build)
        built=$((built + 1))
    fi
done

echo ""
echo "Done. Built $built extension(s)."
