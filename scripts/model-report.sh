#!/bin/bash
# Model Status Report — reports on all new HF models
DATE=$(date '+%Y-%m-%d %H:%M')
REPORT="/tmp/model-report.txt"

echo "📦 SakThai New Models Report — $DATE" > $REPORT
echo "" >> $REPORT

check_model() {
    local name="$1"
    local url="$2"
    local status=$(curl -s -o /dev/null -w "%{http_code}" "https://huggingface.co/api/models/$name" 2>/dev/null)
    if [ "$status" = "200" ]; then
        echo "  ✅ $name — live on HF" >> $REPORT
    else
        echo "  ❌ $name — HTTP $status" >> $REPORT
    fi
}

check_space() {
    local name="$1"
    local status=$(curl -s -o /dev/null -w "%{http_code}" "https://huggingface.co/api/spaces/$name" 2>/dev/null)
    if [ "$status" = "200" ]; then
        echo "  ✅ $name — live on HF Spaces" >> $REPORT
    else
        echo "  ❌ $name — HTTP $status" >> $REPORT
    fi
}

echo "Models:" >> $REPORT
check_model "Nanthasit/sakthai-embedding" 
check_model "Nanthasit/sakthai-coder-1.5b"
check_model "Nanthasit/sakthai-vision-7b"
check_model "Nanthasit/sakthai-tts-model"
check_model "Nanthasit/sakthai-embedding-multilingual"

echo "" >> $REPORT
echo "Spaces:" >> $REPORT
check_space "Nanthasit/sakthai-tts"

echo "" >> $REPORT
echo "--- All assets verified ---" >> $REPORT
cat $REPORT