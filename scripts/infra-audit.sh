#!/bin/bash
# infra-audit.sh — Check system resources and drift
# Silent if healthy, reports issues only
DISK=$(df /opt/data --output=pcent 2>/dev/null | tail -1 | tr -d ' %')
MEM=$(free -m | grep Mem | awk '{printf "%d", $3/$2 * 100}')
LOAD=$(cat /proc/loadavg | awk '{print $1}')

ISSUES=0
if [[ "$DISK" -gt 85 ]]; then echo "⚠️ Disk: ${DISK}% used"; ISSUES=$((ISSUES+1)); fi
if [[ "$MEM" -gt 85 ]]; then 
  echo "⚠️ Memory: ${MEM}% used"
  echo "  └─ Top processes by memory:"
  ps aux --sort=-%mem | head -6 | tail -5 | awk '{printf "    %-6s %-4s %-4s  %s\n", $11, $4"%", $3"%", $6}'
  ISSUES=$((ISSUES+1))
fi
if [[ "$(echo "$LOAD > 4" | bc 2>/dev/null)" == "1" ]]; then 
  echo "⚠️ Load: $LOAD"; ISSUES=$((ISSUES+1)); 
fi
