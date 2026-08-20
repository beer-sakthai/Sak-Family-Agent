#!/usr/bin/env bash
#
# Install everything this repository's workflows expect a runner to already
# have. GitHub-hosted `ubuntu-latest` images ship most of it; a bare VM ships
# none of it, and the failure mode is a job that dies on step three with
# "uv: command not found" after you have already waited for the checkout.
#
# Run as the runner user (not root — it installs into ~/.local and ~/.cargo).
# Anything needing root is called out and left to you, so the script never
# silently sudo's on a host you did not expect it to.
#
#   ./bootstrap-toolchain.sh          # install
#   ./bootstrap-toolchain.sh --check  # report what is present, change nothing
set -euo pipefail

CHECK_ONLY=0
[[ "${1:-}" == "--check" ]] && CHECK_ONLY=1

# Node 22, not 20 — the dashboard's locked tree needs it. jsdom@30 declares
# `engines.node: ^22.22.2 || ^24.15.0 || >=26.0.0` and pulls undici@8; on Node
# 20 every vitest worker dies at startup before a single test runs. Keep this
# at or above that floor whenever either dependency moves.
NODE_MAJOR="${NODE_MAJOR:-22}"

report() {
  local name="$1" cmd="$2"
  if command -v "${cmd}" >/dev/null 2>&1; then
    printf '  %-12s %s\n' "${name}" "$(command -v "${cmd}")"
  else
    printf '  %-12s MISSING\n' "${name}"
  fi
}

if [[ ${CHECK_ONLY} -eq 1 ]]; then
  echo "Toolchain on $(hostname -s):"
  report git git
  report python3 python3
  report uv uv
  report node node
  report pnpm pnpm
  report docker docker
  exit 0
fi

echo "==> system packages (needs sudo)"
# git and curl for checkout; build-essential and the libffi/ssl headers because
# a wheel-less package in the locked closure will be built from source on an
# architecture PyPI has no wheel for.
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends \
  git curl ca-certificates build-essential pkg-config \
  libffi-dev libssl-dev

echo "==> uv"
# uv provisions its own CPython builds, so the host does not need a system
# Python matching the matrix — `uv sync --locked` fetches 3.11 and 3.12 itself.
# That is why this script installs uv and not two Python versions.
if ! command -v uv >/dev/null 2>&1; then
  curl -fsSL https://astral.sh/uv/install.sh | sh
fi
export PATH="${HOME}/.local/bin:${PATH}"

echo "==> node ${NODE_MAJOR} + pnpm"
if ! command -v node >/dev/null 2>&1 || [[ "$(node -v | cut -c2- | cut -d. -f1)" -lt "${NODE_MAJOR}" ]]; then
  curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | sudo -E bash -
  sudo apt-get install -y nodejs
fi
# corepack ships with Node and reads `packageManager: pnpm@9.15.9` from the
# dashboard's package.json, so the runner resolves the same pnpm the lockfile
# was generated with rather than whatever is newest.
sudo corepack enable

cat <<'NOTE'

==> docker (optional, left to you)

`sakthai run --sandbox` shells out to docker, and infra/vm-agents runs the
personas as containers. No workflow in .github/workflows/ needs it today, so
this script does not install it — adding a runner user to the `docker` group
is equivalent to giving it root, and that is not a decision to make silently
inside a bootstrap script. Install it deliberately if this host needs it.
NOTE

echo
echo "==> resulting toolchain"
exec "$0" --check
