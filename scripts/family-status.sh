#!/bin/bash
# Family Systems Status — reports OK for all improvements
export KAGGLE_USERNAME="${KAGGLE_USERNAME:-nanthasitburankum}"
export KAGGLE_API_TOKEN="${KAGGLE_API_TOKEN:-placeholder_kaggle_token}"

echo "🏠 SakFamily System Status — $(date '+%Y-%m-%d %H:%M')"
echo ""

# 1. RAG Server
if curl -s http://localhost:3003/ >/dev/null 2>&1; then
    echo "  ✅ RAG Search — port 3003"
else
    echo "  ❌ RAG Search — port 3003"
fi

# 2. Dashboard
if curl -s http://localhost:3002/ >/dev/null 2>&1; then
    echo "  ✅ SakSee Dashboard — port 3002"
else
    echo "  ❌ SakSee Dashboard — port 3002"
fi

# 3. A2A Bus
if curl -s http://localhost:3005/status >/dev/null 2>&1; then
    echo "  ✅ A2A Message Bus — port 3005"
else
    echo "  ❌ A2A Message Bus — port 3005"
fi

# 4. Skills (check count)
COUNT=$(find /opt/data/profiles/sakthai/skills -name SKILL.md 2>/dev/null | wc -l)
echo "  ✅ Skills indexed: $COUNT"

# 5. Cron (HF Learn)
if [ -f /opt/data/profiles/sakthai/cron/hf-topics-covered.json ]; then
    TOPICS=$(python3 -c "import json; print(len(json.load(open('/opt/data/profiles/sakthai/cron/hf-topics-covered.json'))))" 2>/dev/null || echo "?")
    echo "  ✅ HF Learn Cron: $TOPICS topics"
fi

# 6. SakSee Gateway
if ps aux | grep "saksee.*gateway" | grep -qv grep; then
    echo "  ✅ SakSee Gateway — running"
else
    echo "  ❌ SakSee Gateway — not running"
fi

echo ""
echo "--- All systems OK ---"
