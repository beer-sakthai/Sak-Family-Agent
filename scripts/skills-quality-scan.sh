#!/bin/bash
# skills-quality-scan.sh — Scan skill repos for structural issues
# Checks: name/directory mismatch, missing version, missing description
# Silent if clean, reports violations only
#
# Usage: skills-quality-scan.sh [--fix]
#   --fix  Auto-add missing version: 1.0.0 to affected skill SKILL.md files

SFA="/opt/data/Sak-Family-Agent/personas"
FIX_MODE=false
[[ "$1" == "--fix" ]] && FIX_MODE=true
ISSUES=0
FIXED=0
REPORT=""
FIX_REPORT=""

check_skill() {
  local persona="$1" dir="$2"
  local name; name=$(basename "$dir")
  local md="$dir/SKILL.md"
  [[ -f "$md" ]] || return

  # Check name matches directory
  local md_name
  md_name=$(grep -m1 "^name:" "$md" 2>/dev/null | sed 's/^name:[[:space:]]*//' | sed 's/^"//; s/"$//')
  if [[ -n "$md_name" ]] && [[ "$md_name" != "$name" ]]; then
    REPORT+="❌ $persona: $name → SKILL.md says '$md_name'"$'\n'
    ISSUES=$((ISSUES+1))
  fi

  # Check version field exists
  if ! grep -q "^version:" "$md" 2>/dev/null; then
    REPORT+="⚠️ $persona: $name — missing version field"$'\n'
    ISSUES=$((ISSUES+1))
    if [[ "$FIX_MODE" == true ]]; then
      # Insert version: 1.0.0 after the name: line
      local tmp; tmp=$(mktemp)
      awk '/^name:/ {print; print "version: 1.0.0"; next} {print}' "$md" > "$tmp" && mv "$tmp" "$md"
      FIX_REPORT+="✅ $persona: $name — added version: 1.0.0"$'\n'
      FIXED=$((FIXED+1))
    fi
  fi

  # Check description field exists and is non-empty
  local md_desc
  md_desc=$(grep -m1 "^description:" "$md" 2>/dev/null | sed 's/^description:[[:space:]]*//' | sed 's/^"//; s/"$//')
  if [[ -z "$md_desc" ]]; then
    REPORT+="⚠️ $persona: $name — missing or empty description"$'\n'
    ISSUES=$((ISSUES+1))
  fi
}

for p in sakthai sakking saksee saksit sakjules; do
  dir="$SFA/$p/skills"
  [[ -d "$dir" ]] || continue
  while IFS= read -r -d '' skill; do
    check_skill "$p" "$skill"
  done < <(find "$dir" -mindepth 1 -maxdepth 1 -type d -print0)
done

if [[ "$ISSUES" -gt 0 ]]; then
  echo "⚠️ $ISSUES skill quality issues found:"
  echo "$REPORT"
fi

if [[ "$FIXED" -gt 0 ]]; then
  echo ""
  echo "✅ Auto-fixed $FIXED skills with --fix:"
  echo "$FIX_REPORT"
fi
