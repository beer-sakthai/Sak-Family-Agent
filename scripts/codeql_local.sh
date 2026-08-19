#!/usr/bin/env bash
#
# Run this repository's CodeQL analysis locally, with the same scope and the
# same query suites the `CodeQL Advanced` workflow uses.
#
# WHY: the only place CodeQL findings surface today is the Security tab, after
# a push. That is a slow loop for anyone actually working through the ~243
# first-party alerts, and it is no loop at all for checking whether a change
# *introduces* one — you push, wait for the analysis, and read it afterwards.
# This script closes that: same config file, same per-language suites, results
# on the terminal.
#
# It is a convenience, not a gate. `.github/workflows/codeql.yml` is what
# uploads to code scanning; nothing here writes to GitHub.
#
# REQUIREMENT: the CodeQL CLI on PATH. It is not a pip/npm package — download
# the bundle (CLI + the query packs it needs, which a bare CLI does not
# include) from https://github.com/github/codeql-action/releases and put its
# `codeql` on PATH. `./scripts/codeql_local.sh --check` verifies the setup and
# prints the version without analysing anything.
#
# USAGE
#   scripts/codeql_local.sh                     # all three languages
#   scripts/codeql_local.sh python              # one language
#   scripts/codeql_local.sh actions python      # a subset
#   scripts/codeql_local.sh --check             # verify the CLI is usable
#   scripts/codeql_local.sh --sarif python      # also write SARIF next to the db
#
# The databases land in `.codeql/` (gitignored) and are reused between runs
# unless you pass --rebuild; building the python database over this repository
# is the slow part.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG="${REPO_ROOT}/.github/codeql/codeql-config.yml"
DB_ROOT="${REPO_ROOT}/.codeql"

# Keep this table in step with the `matrix.include` block in
# .github/workflows/codeql.yml. A language analysed here with a different suite
# than CI uses is worse than not analysing it: it produces findings that will
# not appear on the dashboard, or misses ones that will.
declare -A SUITES=(
  [actions]="codeql/actions-queries:codeql-suites/actions-security-extended.qls"
  [javascript-typescript]="codeql/javascript-queries:codeql-suites/javascript-code-scanning.qls"
  [python]="codeql/python-queries:codeql-suites/python-code-scanning.qls"
)

ALL_LANGUAGES=(actions javascript-typescript python)

want_sarif=0
rebuild=0
languages=()

for arg in "$@"; do
  case "${arg}" in
    --check)
      if ! command -v codeql >/dev/null 2>&1; then
        echo "codeql is not on PATH." >&2
        echo "Download the bundle from https://github.com/github/codeql-action/releases" >&2
        echo "(the bundle, not the bare CLI — the bare CLI ships no query packs)." >&2
        exit 1
      fi
      codeql version --format=terse
      echo "config: ${CONFIG}"
      exit 0
      ;;
    --sarif)   want_sarif=1 ;;
    --rebuild) rebuild=1 ;;
    -h|--help)
      sed -n '3,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    -*)
      echo "unknown flag: ${arg}" >&2
      exit 2
      ;;
    *)
      if [[ -z "${SUITES[${arg}]:-}" ]]; then
        echo "unknown language: ${arg}" >&2
        echo "known: ${ALL_LANGUAGES[*]}" >&2
        exit 2
      fi
      languages+=("${arg}")
      ;;
  esac
done

if [[ ${#languages[@]} -eq 0 ]]; then
  languages=("${ALL_LANGUAGES[@]}")
fi

if ! command -v codeql >/dev/null 2>&1; then
  echo "codeql is not on PATH — run 'scripts/codeql_local.sh --check' for setup notes." >&2
  exit 1
fi

mkdir -p "${DB_ROOT}"

for language in "${languages[@]}"; do
  db="${DB_ROOT}/${language}"

  if [[ ${rebuild} -eq 1 && -d "${db}" ]]; then
    rm -rf "${db}"
  fi

  if [[ ! -d "${db}" ]]; then
    echo "==> building the ${language} database (this is the slow part)"
    # --codescanning-config is what makes `paths-ignore` apply. Without it the
    # local run analyses the ~900 vendored skill directories and the folded-in
    # sakthai-chat-cli copy, and reproduces the 545 alerts that scope exists to
    # keep off the dashboard.
    codeql database create "${db}" \
      --language="${language}" \
      --build-mode=none \
      --source-root="${REPO_ROOT}" \
      --codescanning-config="${CONFIG}" \
      --overwrite
  else
    echo "==> reusing ${db} (pass --rebuild to discard it)"
  fi

  echo "==> analysing ${language}"
  analyze_args=(
    "${db}"
    "${SUITES[${language}]}"
    --format=sarif-latest
    --output="${db}.sarif"
  )
  codeql database analyze "${analyze_args[@]}"

  # SARIF is the upload format, not a readable one. Summarise by rule so the
  # terminal output is the thing you actually wanted.
  python3 - "${db}.sarif" <<'PY'
import collections, json, pathlib, sys

sarif = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
counts: collections.Counter[str] = collections.Counter()
for run in sarif.get("runs", []):
    for result in run.get("results", []):
        counts[result.get("ruleId", "<no rule id>")] += 1

total = sum(counts.values())
if not total:
    print("    no findings")
else:
    print(f"    {total} finding(s):")
    for rule, n in counts.most_common():
        print(f"      {n:>4}  {rule}")
PY

  if [[ ${want_sarif} -eq 0 ]]; then
    rm -f "${db}.sarif"
  else
    echo "    sarif: ${db}.sarif"
  fi
done
