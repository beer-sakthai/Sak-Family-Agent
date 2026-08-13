#!/usr/bin/env bash
# Build any installed extensions that need a compile step.
#
# `sakthai extensions install <git-url>` clones extensions into
# ${SAKTHAI_HOME:-~/.sakthai}/extensions. Most are ready to use as-is; this
# script runs `npm ci && npm run build` for any that ship a Node MCP server
# (a package.json with a "build" script).
#
# `npm ci`, not `npm install`: an extension is third-party code cloned from a
# git URL, so its dependency tree should resolve to exactly the versions its
# author committed and to the sha512 integrity hashes recorded alongside them.
# `npm install` re-resolves against the registry at build time, which silently
# picks up whatever a matching semver range serves that day. That is also what
# Scorecard's Pinned-Dependencies check flags here (`npmCommand not pinned by
# hash`).
#
# `npm ci` requires a lockfile, so an extension that ships none is reported and
# skipped rather than installed unpinned. Building one is then a deliberate
# choice its owner makes by hand, not something this script does for them.
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
        if [ ! -f "$dir/package-lock.json" ] && [ ! -f "$dir/npm-shrinkwrap.json" ]; then
            echo ">>> Skipping $name — no package-lock.json or npm-shrinkwrap.json."
            echo "    Without a lockfile there are no integrity hashes to install against."
            echo "    Ask the extension to commit one, or build it yourself in $dir."
            skipped=$((skipped + 1))
            continue
        fi
        echo ">>> Building $name…"
        (cd "$dir" && npm ci --silent && npm run build)
        built=$((built + 1))
    fi
done

echo ""
echo "Done. Built $built extension(s), skipped $skipped."
