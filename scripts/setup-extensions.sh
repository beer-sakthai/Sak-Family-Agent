#!/usr/bin/env bash
# Build any installed extensions that need a compile step.
#
# `sakthai extensions install <git-url>` clones extensions into
# ${SAKTHAI_HOME:-~/.sakthai}/extensions. Most are ready to use as-is; this
# script runs `npm ci && npm run build` for any that ship a Node MCP server (a
# package.json with a "build" script) and a lockfile. One without a lockfile is
# skipped: its dependencies would resolve to whatever the registry serves today.
set -euo pipefail

PERSONA="${1:-}"
BASE_DIR="${SAKTHAI_HOME:-$HOME/.sakthai}"

EXT_DIRS=()
if [ -n "$PERSONA" ]; then
    EXT_DIRS+=("$BASE_DIR/$PERSONA/extensions")
else
    EXT_DIRS+=("$BASE_DIR/extensions")
    for p in sakthai sakking saksee saksit sakjules saktan; do
        if [ -d "$BASE_DIR/$p/extensions" ]; then
            EXT_DIRS+=("$BASE_DIR/$p/extensions")
        fi
    done
fi

built=0
skipped=0
for ext_dir in "${EXT_DIRS[@]}"; do
    [ -d "$ext_dir" ] || continue
    for pkg in "$ext_dir"/*/package.json "$ext_dir"/*/*/package.json; do
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
done

echo ""
echo "Done. Built $built extension(s), skipped $skipped without a lockfile."
