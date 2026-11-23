#!/usr/bin/env bash
# Copy the canonical package modules that are byte-parity-enforced into the five
# sibling persona trees.
#
# personas/sakthai/ is the package that is installed and run; the other five are
# full copies. Only a few files have parity tests, but those tests fail CI the
# moment a copy drifts:
#
#   tests/test_persona_guardrails_parity.py   agent/guardrails.py
#   tests/test_persona_web_server_parity.py   web/server.py
#   tests/test_persona_mcp_parity.py          every module in mcp/
#
# Run this after changing any of them. It also removes a module a persona still
# carries that the canonical package no longer has, which the parity test checks
# for — a plain `cp` would leave it behind.
set -euo pipefail

cd "$(dirname "$0")/.."
CANON="personas/sakthai"
PERSONAS=(sakking saksee saksit sakjules saktan)

# Directories copied wholesale (every *.py), with stale modules pruned.
DIRS=(mcp)

# Individual files copied.
FILES=(
  agent/guardrails.py
  agent/guardrails_hardened.py
  agent/security_hardening.py
  agent/tools.py
  web/server.py
  config.py
)

for persona in "${PERSONAS[@]}"; do
  dest="personas/$persona"
  [ -d "$dest" ] || { echo "no such persona tree: $dest" >&2; exit 1; }

  for dir in "${DIRS[@]}"; do
    mkdir -p "$dest/$dir"
    # Prune first: a module deleted from the canonical package must not survive
    # in a copy.
    for existing in "$dest/$dir"/*.py; do
      [ -e "$existing" ] || continue
      base="$(basename "$existing")"
      [ -f "$CANON/$dir/$base" ] || { echo "  pruning $existing"; rm -f "$existing"; }
    done
    cp "$CANON/$dir"/*.py "$dest/$dir/"
  done

  for file in "${FILES[@]}"; do
    [ -f "$CANON/$file" ] || continue
    mkdir -p "$(dirname "$dest/$file")"
    cp "$CANON/$file" "$dest/$file"
  done
done

echo "synced ${#PERSONAS[@]} persona trees from $CANON"
