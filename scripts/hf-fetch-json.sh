#!/usr/bin/env bash
# hf-fetch-json.sh — Safe HF API JSON fetcher for cron sessions
#
# The tirith security scanner blocks `curl | python3` pipes.
# Always fetch to a temp file first, then process.
#
# Usage:
#   ./scripts/hf-fetch-json.sh models       -> /tmp/hf_models.json   + counts
#   ./scripts/hf-fetch-json.sh datasets     -> /tmp/hf_datasets.json + counts
#   ./scripts/hf-fetch-json.sh spaces       -> /tmp/hf_spaces.json   + counts
#   ./scripts/hf-fetch-json.sh all          -> all three
#
# Output: writes JSON to /tmp/hf_{type}.json, prints summary to stdout.

set -euo pipefail

BASE="https://huggingface.co/api"
AUTHOR="Nanthasit"

fetch_type() {
    local type="$1"
    local url="$BASE/$type?author=$AUTHOR&sort=downloads&direction=-1"
    local outfile="/tmp/hf_${type}.json"

    curl -s --max-time 15 -o "$outfile" "$url"
    local size
    size=$(wc -c < "$outfile")
    echo "$type: $size bytes -> $outfile"
}

case "${1:-all}" in
    models)
        fetch_type "models"
        ;;
    datasets)
        fetch_type "datasets"
        ;;
    spaces)
        fetch_type "spaces"
        ;;
    all)
        fetch_type "models"
        fetch_type "datasets"
        fetch_type "spaces"
        ;;
    *)
        echo "Usage: $0 {models|datasets|spaces|all}"
        exit 1
        ;;
esac
