#!/usr/bin/env bash
#
# Turn on the repository settings that .github/dependabot.yml cannot turn on
# itself, and report which of them are already on.
#
# The config file governs the *version-update* queue. Dependabot alerts and
# Dependabot security updates are repository settings, driven by the dependency
# graph, and no amount of YAML enables them. This script is the scripted
# alternative to the click path in docs/dependabot-setup.md.
#
# It is a DRY RUN unless --apply is passed, mirroring the contract of
# scripts/code_scanning_analyses.py.
#
# Token: a PAT with the classic `repo` scope, or a fine-grained token with the
# "Administration" repository permission (write). The Actions GITHUB_TOKEN
# cannot do this — see the note in docs/dependabot-setup.md.
#
#   GITHUB_TOKEN=<pat> bash scripts/enable_dependabot.sh            # report only
#   GITHUB_TOKEN=<pat> bash scripts/enable_dependabot.sh --apply    # enable
#
set -euo pipefail

REPO="${GITHUB_REPOSITORY:-beer-sakthai/Sak-Family-Agent}"
TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
APPLY=0

for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --repo=*) REPO="${arg#--repo=}" ;;
    -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

if [ -z "$TOKEN" ]; then
  cat >&2 <<'EOF'
Set GITHUB_TOKEN (or GH_TOKEN) first.

Enabling these settings needs repository administration rights:
  classic       -> the `repo` scope
  fine-grained  -> the "Administration" repository permission, write

The Actions GITHUB_TOKEN cannot do this, whatever `permissions:` a job declares.
EOF
  exit 2
fi

API="https://api.github.com"

# $1 method, $2 path. Prints the HTTP status only; the body is discarded because
# these endpoints answer 204 with no content on success.
_status() {
  curl -sS -o /dev/null -w '%{http_code}' \
    -X "$1" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "${API}${2}"
}

echo "Repository: ${REPO}"
if [ "$APPLY" -eq 1 ]; then
  echo "Mode:       APPLY (settings will be changed)"
else
  echo "Mode:       dry run (nothing will be changed; pass --apply to enable)"
fi
echo

# --- Current state ----------------------------------------------------------
# GET on vulnerability-alerts answers 204 when enabled and 404 when not; that
# 404 is the documented answer, not an error.
echo "--- Current state ---"

alerts_status="$(_status GET "/repos/${REPO}/vulnerability-alerts")"
case "$alerts_status" in
  204) echo "Dependabot alerts          : ENABLED" ;;
  404) echo "Dependabot alerts          : disabled" ;;
  401|403) echo "Dependabot alerts          : ${alerts_status} — token lacks admin rights"; exit 1 ;;
  *)   echo "Dependabot alerts          : unexpected HTTP ${alerts_status}" ;;
esac

# The dependency graph has no dedicated endpoint on a public repository — it is
# on by default and cannot be turned off. `security_and_analysis` reports it for
# private repositories only, so read it from the repo object when present.
#
# The response is captured before it is parsed rather than piped straight into
# python3. Two reasons, and only the second is about the scanner:
#
#   - A failed request used to reach python as an empty stdin and surface as a
#     JSONDecodeError traceback, which reads like a bug in this script rather
#     than a network or token problem. It now fails with a sentence.
#   - `curl … | python3` is the shape Scorecard reports as
#     PinnedDependenciesID "downloadThenRun not pinned by hash". Here that was
#     a false positive — the executed code is the literal `-c` string and the
#     download is only ever data on stdin — but the shape is worth not having.
repo_json="$(
  curl -sS \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "${API}/repos/${REPO}"
)" || { echo "Repository visibility/graph: request to ${API}/repos/${REPO} failed" >&2; exit 1; }

graph="$(
  python3 -c 'import json,sys; d=json.loads(sys.argv[1]); sa=d.get("security_and_analysis") or {}; print(("private" if d.get("private") else "public"), (sa.get("dependency_graph") or {}).get("status","n/a"))' \
    "${repo_json}"
)" || { echo "Repository visibility/graph: could not parse the API response" >&2; exit 1; }
echo "Repository visibility/graph: ${graph}"
echo "  (on a public repository the dependency graph is always on and cannot be disabled)"
echo

if [ "$APPLY" -eq 0 ]; then
  cat <<EOF
Dry run. Re-run with --apply to enable:
  PUT /repos/${REPO}/vulnerability-alerts       (Dependabot alerts)
  PUT /repos/${REPO}/automated-security-fixes   (Dependabot security updates)

Neither is reachable from .github/dependabot.yml; both are repository settings.
EOF
  exit 0
fi

# --- Apply ------------------------------------------------------------------
echo "--- Applying ---"

# Order matters: automated-security-fixes requires alerts to be on first.
va="$(_status PUT "/repos/${REPO}/vulnerability-alerts")"
if [ "$va" = "204" ]; then
  echo "Dependabot alerts          : enabled (HTTP ${va})"
else
  echo "Dependabot alerts          : FAILED (HTTP ${va})" >&2
  exit 1
fi

asf="$(_status PUT "/repos/${REPO}/automated-security-fixes")"
if [ "$asf" = "204" ]; then
  echo "Dependabot security updates: enabled (HTTP ${asf})"
else
  echo "Dependabot security updates: FAILED (HTTP ${asf})" >&2
  exit 1
fi

echo
echo "Done. Verify with:"
echo "  GITHUB_TOKEN=\$TOKEN bash scripts/enable_dependabot.sh"
echo "  GITHUB_TOKEN=\$TOKEN python scripts/dependabot_advisories.py list"
