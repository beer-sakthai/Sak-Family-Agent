#!/usr/bin/env bash
# Build any installed extensions that need a compile step.
#
# `sakthai extensions install <git-url>` clones extensions into
# ${SAKTHAI_HOME:-~/.sakthai}/extensions. Most are ready to use as-is; this
# script runs `npm ci && npm run build` for any that ship a Node MCP server (a
# package.json with a "build" script) and a lockfile. One without a lockfile is
# skipped: its dependencies would resolve to whatever the registry serves today.
set -euo pipefail

EXT_DIR="${SAKTHAI_HOME:-$HOME/.sakthai}/extensions"

if [ ! -d "$EXT_DIR" ]; then
    echo "No extensions directory at $EXT_DIR — nothing to build."
    echo "Install one with: sakthai extensions install <git-url>"
    exit 0
fi

built=0
skipped=0
for pkg in "$EXT_DIR"/*/package.json "$EXT_DIR"/*/*/package.json; do
    [ -f "$pkg" ] || continue
    dir="$(dirname "$pkg")"
    if grep -q '"build"' "$pkg"; then
        name="$(basename "$(dirname "$dir")")/$(basename "$dir")"
        if [ -f "$dir/package-lock.json" ] || [ -f "$dir/npm-shrinkwrap.json" ]; then
            echo ">>> Building $name…"
            (cd "$dir" && npm ci --silent && npm run build)
            built=$((built + 1))
        else
            echo ">>> Skipping $name: no package-lock.json to install from."
            echo "    Review it, then build it yourself in $dir"
            skipped=$((skipped + 1))
        fi
    fi
done

echo ""
echo "Done. Built $built extension(s), skipped $skipped without a lockfile."
