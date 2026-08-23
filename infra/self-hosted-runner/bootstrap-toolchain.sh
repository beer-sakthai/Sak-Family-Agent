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
#
# Downloaded to a file and checksummed before it is executed, rather than
# `curl … | sh`. A pipe straight into a shell runs whatever the endpoint served
# at that moment, with no chance to inspect it and nothing to compare against
# if the endpoint is ever compromised — Scorecard reports it as
# PinnedDependenciesID "downloadThenRun not pinned by hash".
#
# The URL carries the version, which is what makes the digest stable: the
# unversioned https://astral.sh/uv/install.sh is rewritten on every uv release,
# so pinning a hash against it would break on each upstream bump.
#
# To move to a new uv:
#   V=0.12.6
#   curl -fsSL "https://astral.sh/uv/${V}/install.sh" | sha256sum
# then update both constants below.
UV_VERSION="${UV_VERSION:-0.12.5}"
UV_INSTALLER_SHA256="504511fbbbd811aeaba6738abc79408956b6c7da0ca35437b3dcc24a41efc111"

if ! command -v uv >/dev/null 2>&1; then
  uv_installer="$(mktemp -t uv-installer.XXXXXX.sh)"
  trap 'rm -f "${uv_installer}"' EXIT
  curl -fsSL "https://astral.sh/uv/${UV_VERSION}/install.sh" -o "${uv_installer}"
  if ! echo "${UV_INSTALLER_SHA256}  ${uv_installer}" | sha256sum -c - >/dev/null 2>&1; then
    echo "ERROR: uv ${UV_VERSION} installer failed checksum verification." >&2
    echo "  expected ${UV_INSTALLER_SHA256}" >&2
    echo "  got      $(sha256sum "${uv_installer}" | cut -d' ' -f1)" >&2
    echo "Refusing to execute it. If uv was bumped upstream, re-pin both" >&2
    echo "UV_VERSION and UV_INSTALLER_SHA256 above." >&2
    exit 1
  fi
  sh "${uv_installer}"
  rm -f "${uv_installer}"
  trap - EXIT
fi
export PATH="${HOME}/.local/bin:${PATH}"

echo "==> node ${NODE_MAJOR} + pnpm"
# NodeSource's own `setup_${NODE_MAJOR}.x` is a shell script meant to be piped
# into `sudo bash` — remote code as root, and the worst instance of the pattern
# in this file. All that script ultimately does is register NodeSource's apt
# key and repository, so this does that directly instead. Nothing downloaded
# here is executed: the key is data, and apt verifies every package signature
# against it, which is a stronger guarantee than hashing an installer would be.
#
# The fingerprint is pinned. NodeSource rotating its key is indistinguishable
# from an attacker substituting one, so a mismatch stops the script rather than
# importing whatever arrived.
NODESOURCE_GPG_FINGERPRINT="6F71F525282841EEDAF851B42F59B5F99B1BE0B4"

if ! command -v node >/dev/null 2>&1 || [[ "$(node -v | cut -c2- | cut -d. -f1)" -lt "${NODE_MAJOR}" ]]; then
  ns_key="$(mktemp -t nodesource.XXXXXX.asc)"
  trap 'rm -f "${ns_key}"' EXIT
  curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key -o "${ns_key}"

  if ! gpg --show-keys --with-colons "${ns_key}" 2>/dev/null |
       awk -F: '/^fpr:/{print $10}' | grep -qx "${NODESOURCE_GPG_FINGERPRINT}"; then
    echo "ERROR: NodeSource signing key does not match the pinned fingerprint." >&2
    echo "  expected ${NODESOURCE_GPG_FINGERPRINT}" >&2
    echo "  got      $(gpg --show-keys --with-colons "${ns_key}" 2>/dev/null |
                       awk -F: '/^fpr:/{print $10}' | paste -sd, -)" >&2
    echo "Refusing to trust it. Verify the rotation against nodesource.com" >&2
    echo "before updating NODESOURCE_GPG_FINGERPRINT above." >&2
    exit 1
  fi

  sudo install -d -m 0755 /etc/apt/keyrings
  sudo gpg --batch --yes --dearmor -o /etc/apt/keyrings/nodesource.gpg "${ns_key}"
  sudo chmod 0644 /etc/apt/keyrings/nodesource.gpg
  rm -f "${ns_key}"
  trap - EXIT

  echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_MAJOR}.x nodistro main" |
    sudo tee /etc/apt/sources.list.d/nodesource.list >/dev/null
  sudo apt-get update -qq
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
