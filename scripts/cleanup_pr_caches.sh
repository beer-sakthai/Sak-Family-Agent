#!/usr/bin/env bash
# Remove GitHub Actions caches belonging to closed pull requests.
# Discovery failures fail closed: no delete is attempted unless the candidate set
# has been completely enumerated first.
set -euo pipefail

: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY must be set}"

readonly PAGE_SIZE="${CACHE_CLEANUP_PAGE_SIZE:-100}"
readonly REPOSITORY="${GITHUB_REPOSITORY}"
readonly DRY_RUN="${DRY_RUN:-false}"
readonly PR_NUMBER="${PR_NUMBER:-}"

[[ "${PAGE_SIZE}" =~ ^[1-9][0-9]*$ ]] || {
  echo "::error::CACHE_CLEANUP_PAGE_SIZE must be a positive integer" >&2
  exit 2
}

case "${DRY_RUN}" in
  true|false) ;;
  *) echo "::error::DRY_RUN must be true or false" >&2; exit 2 ;;
esac

for command in gh jq; do
  command -v "${command}" >/dev/null 2>&1 || {
    echo "::error::Required command not found: ${command}" >&2
    exit 2
  }
done

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

api_get() {
  local endpoint="$1"
  local expected_type="$2"
  local output
  if ! output="$(gh api "${endpoint}")"; then
    echo "::error::GitHub API read failed: ${endpoint}" >&2
    return 1
  fi
  if ! jq -e --arg expected_type "${expected_type}" 'type == $expected_type' >/dev/null <<<"${output}"; then
    echo "::error::GitHub API returned invalid JSON for: ${endpoint}" >&2
    return 1
  fi
  printf '%s\n' "${output}"
}

list_cache_records() {
  local page=1
  local endpoint response count
  : "${1:-}" # optional ref query, already URL-encoded by the caller
  local ref_query="${1:+&ref=${1}}"

  : >"${tmp_dir}/caches"
  while :; do
    endpoint="repos/${REPOSITORY}/actions/caches?per_page=${PAGE_SIZE}&page=${page}${ref_query}"
    response="$(api_get "${endpoint}" object)"
    if ! jq -e '.actions_caches | type == "array"' >/dev/null <<<"${response}"; then
      echo "::error::Invalid cache-list response for page ${page}" >&2
      return 1
    fi
    jq -c '.actions_caches[] | {id, ref}' <<<"${response}" >>"${tmp_dir}/caches"
    count="$(jq '.actions_caches | length' <<<"${response}")"
    (( count < PAGE_SIZE )) && break
    page=$((page + 1))
  done
}

list_open_prs() {
  local page=1
  local endpoint response count

  : >"${tmp_dir}/open_prs"
  while :; do
    endpoint="repos/${REPOSITORY}/pulls?state=open&per_page=${PAGE_SIZE}&page=${page}"
    response="$(api_get "${endpoint}" array)"
    if ! jq -e 'type == "array"' >/dev/null <<<"${response}"; then
      echo "::error::Invalid open-PR response for page ${page}" >&2
      return 1
    fi
    jq -r '.[].number' <<<"${response}" >>"${tmp_dir}/open_prs"
    count="$(jq 'length' <<<"${response}")"
    (( count < PAGE_SIZE )) && break
    page=$((page + 1))
  done
}

record_delete_failure() {
  local cache_id="$1"
  printf '%s\n' "${cache_id}" >>"${tmp_dir}/failed_deletes"
  echo "::error::Failed to delete cache ${cache_id}" >&2
}

delete_cache() {
  local cache_id="$1"
  if [[ "${DRY_RUN}" == true ]]; then
    echo "DRY RUN: would delete cache ${cache_id}"
    return 0
  fi
  if ! gh api -X DELETE "repos/${REPOSITORY}/actions/caches/${cache_id}"; then
    record_delete_failure "${cache_id}"
    return 0
  fi
  echo "Deleted cache ${cache_id}"
}

: >"${tmp_dir}/failed_deletes"

if [[ -n "${PR_NUMBER}" ]]; then
  [[ "${PR_NUMBER}" =~ ^[0-9]+$ ]] || {
    echo "::error::PR_NUMBER must be numeric" >&2
    exit 2
  }
  ref="refs/pull/${PR_NUMBER}/merge"
  encoded_ref="$(jq -rn --arg ref "${ref}" '$ref|@uri')"
  echo "Searching caches for closed PR #${PR_NUMBER} (${ref})..."
  list_cache_records "${encoded_ref}"
  while IFS= read -r record; do
    cache_id="$(jq -er '.id | numbers' <<<"${record}")"
    cache_ref="$(jq -er '.ref | strings' <<<"${record}")"
    [[ "${cache_ref}" == "${ref}" ]] || {
      echo "::warning::Skipping cache ${cache_id} with unexpected ref ${cache_ref}" >&2
      continue
    }
    delete_cache "${cache_id}"
  done <"${tmp_dir}/caches"
else
  echo "Manual sweep: enumerating open PRs and all PR caches..."
  # Both discovery operations complete before any delete is attempted.
  list_open_prs
  list_cache_records

  while IFS= read -r record; do
    cache_id="$(jq -er '.id | numbers' <<<"${record}")"
    cache_ref="$(jq -er '.ref | strings' <<<"${record}")"
    if [[ "${cache_ref}" =~ ^refs/pull/([0-9]+)/merge$ ]]; then
      pr_num="${BASH_REMATCH[1]}"
      if ! grep -Fqx "${pr_num}" "${tmp_dir}/open_prs"; then
        echo "Deleting orphaned cache ${cache_id} for closed PR #${pr_num}"
        delete_cache "${cache_id}"
      else
        echo "Keeping cache ${cache_id} for open PR #${pr_num}"
      fi
    fi
  done <"${tmp_dir}/caches"
fi

if [[ -s "${tmp_dir}/failed_deletes" ]]; then
  failed_count="$(wc -l <"${tmp_dir}/failed_deletes")"
  echo "::error::Cache cleanup failed for ${failed_count} cache(s)" >&2
  exit 1
fi

echo "Cache cleanup completed successfully."
