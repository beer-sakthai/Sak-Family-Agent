#!/usr/bin/env bash
# Smoke-driver for the Hermes Telegram-agent fleet.
#
# Drives the LIVE fleet through its controllable surfaces — there is no
# headless way to do a real Telegram round-trip, so "driving" here means:
#   1. all 4 gateway systemd --user services are active (hard FAIL if not)
#   2. provider auth resolves (huggingface/copilot = primary; nous = optional)
#   3. each gateway connected its MCP servers without a storm of failures
#   4. repo-level config is sane (doctor.py)
#   5. `hermes status` runs clean
#
# Exit 0 = fleet up and serving. Non-zero = at least one gateway down or
# doctor failed. WARN lines (nous logged out, a flaky MCP server) do NOT
# fail the run — the bots serve on HuggingFace, nous is only the cron model.
#
# Override the hermes binary with HERMES_BIN=/path/to/hermes.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNIT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"   # infra/hermes-agents
HERMES_BIN="${HERMES_BIN:-hermes}"
GATEWAYS=(hermes-gateway hermes-gateway-saksee hermes-gateway-saksit hermes-gateway-sakthai)

fail=0
pass() { printf '  [PASS] %s\n' "$1"; }
warn() { printf '  [WARN] %s\n' "$1"; }
bad()  { printf '  [FAIL] %s\n' "$1"; fail=1; }

echo "hermes-fleet smoke · $(date '+%H:%M:%S') · hermes=$(command -v "$HERMES_BIN" || echo MISSING)"
echo

echo "Gateway services (systemd --user):"
for u in "${GATEWAYS[@]}"; do
  act="$(systemctl --user is-active "$u" 2>/dev/null)"
  nr="$(systemctl --user show "$u" -p NRestarts --value 2>/dev/null)"
  if [ "$act" = "active" ]; then
    pass "$u active (restarts=${nr:-?})"
  else
    bad "$u is '${act:-unknown}' (expected active)"
  fi
done
echo

echo "Provider auth:"
for p in huggingface copilot nous; do
  line="$("$HERMES_BIN" auth status "$p" 2>&1 | head -1)"
  case "$line" in
    *"logged in"*) pass "$line" ;;
    *nous*)        warn "$line  (optional — bots serve on HuggingFace; nous is only the cron model)" ;;
    *)             warn "$line" ;;
  esac
done
creds="$("$HERMES_BIN" auth list 2>/dev/null | grep -cE '^\s+#[0-9]')"
pass "pooled credentials: ${creds:-0}"
echo

echo "MCP connection health (journal, last 5 min):"
for u in "${GATEWAYS[@]}"; do
  n="$(journalctl --user -u "$u" --since '5 minutes ago' --no-pager 2>/dev/null \
        | grep -ciE 'mcp.*(fail|error|unavailable|unauthorized)')"
  if [ "${n:-0}" -eq 0 ]; then pass "$u: 0 MCP error lines"
  else warn "$u: $n MCP error lines (inspect: journalctl --user -u $u | grep -i mcp)"; fi
done
echo

echo "Repo config (doctor.py):"
if health="$(cd "$UNIT_DIR" && python3 doctor.py 2>/dev/null \
      | python3 -c 'import sys,json;print(json.load(sys.stdin)["overall_health"])' 2>/dev/null)"; then
  [ "$health" = "PASS" ] && pass "doctor.py overall_health=PASS" || bad "doctor.py overall_health=$health"
else
  warn "doctor.py did not produce parseable JSON (run it directly to see why)"
fi
echo

echo "hermes status:"
if "$HERMES_BIN" status >/dev/null 2>&1; then pass "hermes status exit 0"; else bad "hermes status non-zero"; fi
echo

if [ "$fail" -eq 0 ]; then echo "OK: fleet up and serving"; else echo "PROBLEM: see [FAIL] lines above"; fi
exit "$fail"
