#!/usr/bin/env bash
# Security check script: audits dependencies and code for vulnerabilities
# Run this locally before committing security-sensitive changes

set -e

echo "🔒 Running Security Checks..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

failed=0
warnings=0

# 1. Dependency audit with pip-audit
echo "${YELLOW}1. Auditing Python dependencies...${NC}"
if ! uv run pip-audit --skip-editable; then
  echo "${RED}❌ pip-audit found vulnerabilities${NC}"
  failed=$((failed + 1))
else
  echo "${GREEN}✓ No dependency vulnerabilities found${NC}"
fi
echo ""

# 2. Bandit security analysis
echo "${YELLOW}2. Running bandit security analysis...${NC}"
if uv run bandit -r sakthai/ -f json > /tmp/bandit-report.json 2>/dev/null; then
  if grep -q '"severity": "HIGH"' /tmp/bandit-report.json; then
    echo "${RED}❌ Bandit found high-severity issues${NC}"
    uv run bandit -r sakthai/ -f txt | grep -A3 "HIGH" || true
    failed=$((failed + 1))
  else
    echo "${GREEN}✓ No high-severity code issues found${NC}"
  fi
else
  # Bandit exits non-zero if issues found
  if grep -q '"severity": "HIGH"' /tmp/bandit-report.json; then
    echo "${RED}❌ Bandit found high-severity issues${NC}"
    failed=$((failed + 1))
  else
    echo "${GREEN}✓ No high-severity code issues found${NC}"
  fi
fi
echo ""

# 3. Check for hardcoded secrets
echo "${YELLOW}3. Checking for hardcoded secrets...${NC}"
if git rev-parse --git-dir > /dev/null 2>&1; then
  # Check staged and unstaged changes
  if git grep -P '(password|secret|token|api[_-]?key|aws_access_key|private_key).*=' -- ':!*.md' ':!*.txt' 2>/dev/null | grep -v "test_" > /tmp/secrets.txt 2>&1; then
    echo "${YELLOW}⚠️  Possible hardcoded secrets found:${NC}"
    head -5 /tmp/secrets.txt
    warnings=$((warnings + 1))
  else
    echo "${GREEN}✓ No obvious hardcoded secrets found${NC}"
  fi
else
  echo "${YELLOW}⚠️  Not in a git repository, skipping secret check${NC}"
fi
echo ""

# 4. Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $failed -eq 0 ]; then
  if [ $warnings -gt 0 ]; then
    echo "${YELLOW}⚠️  Security check complete with $warnings warning(s)${NC}"
    exit 0
  else
    echo "${GREEN}✓ All security checks passed!${NC}"
    exit 0
  fi
else
  echo "${RED}✗ Security check failed with $failed critical issue(s)${NC}"
  echo ""
  echo "Next steps:"
  echo "1. Review the issues above"
  echo "2. Fix vulnerabilities or update dependencies:"
  echo "   uv sync --all-extras"
  echo "3. Re-run this script to verify:"
  echo "   ./scripts/security-check.sh"
  exit 1
fi
