#!/usr/bin/env bash
#
# Install and register a GitHub Actions self-hosted runner for this repository.
#
# Run it on the runner host, as the unprivileged user the runner will run as —
# NOT as root. GitHub's `config.sh` refuses to run as root, and for good
# reason: a job on this runner executes whatever is in the repository at the
# commit it is given.
#
#   ./install-runner.sh --token <REGISTRATION_TOKEN> [--labels sak-linux-x64]
#
# Get the registration token from
#   Settings -> Actions -> Runners -> New self-hosted runner
# on https://github.com/beer-sakthai/Sak-Family-Agent, or with
#   gh api -X POST repos/beer-sakthai/Sak-Family-Agent/actions/runners/registration-token --jq .token
# It expires one hour after it is issued, and it is a credential — do not put
# it in a file, a shell history you keep, or a commit.
#
# READ infra/self-hosted-runner/README.md BEFORE RUNNING THIS, in particular
# the section on why this repository's runner must not be exposed to pull
# requests from forks.
set -euo pipefail

RUNNER_VERSION="${RUNNER_VERSION:-2.330.0}"
REPO_URL="${REPO_URL:-https://github.com/beer-sakthai/Sak-Family-Agent}"
RUNNER_DIR="${RUNNER_DIR:-${HOME}/actions-runner}"
RUNNER_NAME="${RUNNER_NAME:-$(hostname -s)}"
LABELS="${LABELS:-sak-linux-x64}"
TOKEN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --token)   TOKEN="$2"; shift 2 ;;
    --labels)  LABELS="$2"; shift 2 ;;
    --name)    RUNNER_NAME="$2"; shift 2 ;;
    --dir)     RUNNER_DIR="$2"; shift 2 ;;
    --version) RUNNER_VERSION="$2"; shift 2 ;;
    -h|--help) sed -n '2,26p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ "$(id -u)" -eq 0 ]]; then
  echo "Refusing to run as root. Create an unprivileged user for the runner:" >&2
  echo "  sudo adduser --system --group --home /home/gh-runner --shell /bin/bash gh-runner" >&2
  exit 1
fi

if [[ -z "${TOKEN}" ]]; then
  echo "--token is required (see the header of this script for where to get one)." >&2
  exit 2
fi

case "$(uname -m)" in
  x86_64)          ARCH="x64" ;;
  aarch64|arm64)   ARCH="arm64" ;;
  *) echo "unsupported architecture: $(uname -m)" >&2; exit 1 ;;
esac

# Digests for the default RUNNER_VERSION (2.330.0), taken from the release
# page. If you bump RUNNER_VERSION, update the matching digest here (or pass
# RUNNER_SHA256=<new digest> explicitly) — the tarball is verified against it
# before anything is extracted.
case "${ARCH}" in
  x64)   RUNNER_SHA256="${RUNNER_SHA256:-af5c33fa94f3cc33b8e97937939136a6b04197e6dadfcfb3b6e33ae1bf41e79a}" ;;
  arm64) RUNNER_SHA256="${RUNNER_SHA256:-9cb43527912086c7c8fb4119cb06409fcbcbd6f93a2d8507f30b07c495620f5c}" ;;
esac

TARBALL="actions-runner-linux-${ARCH}-${RUNNER_VERSION}.tar.gz"
URL="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${TARBALL}"

mkdir -p "${RUNNER_DIR}"
cd "${RUNNER_DIR}"

if [[ ! -x ./config.sh ]]; then
  echo "==> downloading runner ${RUNNER_VERSION} (${ARCH})"
  curl -fsSL -o "${TARBALL}" "${URL}"

  # Verify before extracting. The digest is pinned above (or overridden via
  # RUNNER_SHA256); a mismatch aborts rather than extracting an untrusted
  # tarball. Scorecard's PinnedDependenciesID requires the verification, not
  # just a warning about its absence.
  echo "${RUNNER_SHA256}  ${TARBALL}" | sha256sum -c - || {
    echo "ERROR: runner ${RUNNER_VERSION} (${ARCH}) failed checksum verification." >&2
    echo "  expected ${RUNNER_SHA256}" >&2
    echo "  got      $(sha256sum "${TARBALL}" | cut -d' ' -f1)" >&2
    echo "  If you bumped RUNNER_VERSION, update the pinned digest above." >&2
    rm -f "${TARBALL}"
    exit 1
  }

  tar xzf "${TARBALL}"
  rm -f "${TARBALL}"
fi

echo "==> registering '${RUNNER_NAME}' with labels: ${LABELS}"
# --unattended: fail rather than prompt, so a bad token is an error and not a
#   hung terminal.
# --replace: re-running this script on a host that is already registered
#   replaces its registration instead of creating a second, stale runner entry.
# --ephemeral: the runner accepts ONE job and then deregisters. This is the
#   single most important flag here. A long-lived runner carries state between
#   jobs — a poisoned pip cache, a leftover file in the work directory, an
#   `~/.gitconfig` a previous job wrote — from one commit to the next. Ephemeral
#   runners are the configuration GitHub documents for anything that runs code
#   it did not write, which for this repository includes every agent-authored
#   branch. Pair it with the systemd unit's `Restart=always`, which brings a
#   fresh registration up after each job.
./config.sh \
  --url "${REPO_URL}" \
  --token "${TOKEN}" \
  --name "${RUNNER_NAME}" \
  --labels "${LABELS}" \
  --work "_work" \
  --unattended \
  --replace \
  --ephemeral

cat <<NEXT

Registered. To run it under systemd:

  sudo cp $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/github-actions-runner.service \\
      /etc/systemd/system/github-actions-runner.service
  sudo systemctl daemon-reload
  sudo systemctl enable --now github-actions-runner

Then point a workflow at it by setting the repository variable
CI_RUNNER_LABEL to one of: ${LABELS}
(Settings -> Secrets and variables -> Actions -> Variables).

Unset that variable and everything falls straight back to ubuntu-latest.
NEXT
