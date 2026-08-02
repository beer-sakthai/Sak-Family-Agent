#!/usr/bin/env bash
# Verify HF Datasets Server API endpoints for a given dataset
# Usage: verify-dataset.sh <dataset> [config] [split]
# Example: verify-dataset.sh wikimedia/wikipedia 20231101.en train
set -euo pipefail

DATASET="${1:?Usage: $0 <dataset> [config] [split]}"
CONFIG="${2:-}"
SPLIT="${3:-train}"
BASE="https://datasets-server.huggingface.co"
PASS=0
FAIL=0
red='\033[0;31m'; green='\033[0;32m'; nc='\033[0m'

check() {
    local label="$1" url="$2" expected="$3"
    local resp
    resp=$(curl -sL --max-time 10 "$url" 2>&1)
    if echo "$resp" | grep -q "$expected"; then
        echo -e "  ${green}PASS${nc} $label"
        ((PASS++))
    else
        echo -e "  ${red}FAIL${nc} $label"
        echo "    URL: $url"
        echo "    Expected to contain: $expected"
        echo "    Got: $(echo "$resp" | head -c 200)"
        ((FAIL++))
    fi
}

echo "=== Datasets Server Smoke Test ==="
echo "Dataset: $DATASET | Config: ${CONFIG:-<auto>} | Split: ${SPLIT:-train}"
echo ""

check "/is-valid" "$BASE/is-valid?dataset=$DATASET" '"preview"'
check "/splits" "$BASE/splits?dataset=$DATASET" '"splits"'

if [ -n "$CONFIG" ]; then
    check "/info" "$BASE/info?dataset=$DATASET&config=$CONFIG" '"dataset"'
    check "/first-rows" "$BASE/first-rows?dataset=$DATASET&config=$CONFIG&split=$SPLIT" '"rows"'
    check "/rows" "$BASE/rows?dataset=$DATASET&config=$CONFIG&split=$SPLIT&offset=0&length=2" '"rows"'
    check "/parquet" "$BASE/parquet?dataset=$DATASET&config=$CONFIG" '"parquet_files"'
    check "/size" "$BASE/size?dataset=$DATASET" "$CONFIG"
fi

echo ""
echo "---"
if [ $FAIL -eq 0 ]; then
    echo -e "${green}All $PASS checks passed${nc}"
else
    echo -e "${red}$FAIL/$((PASS+FAIL)) checks failed${nc}"
    exit 1
fi
