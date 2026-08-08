# Common CI Failure Patterns — Sak-Family-Agent

## Pattern 1: Root `skills/` dir breaks validation

**Error:** `test_real_skill_catalog_validates_cleanly` — "missing SKILL.md" with 41+ items in root `skills/` dir.

**Root cause:** The GitHub-Auto-Sync cron (`github-sync.sh`) copies from the live profile to the repo root, recreating a root-level `skills/` directory that conflicts with the `personas/<name>/skills/` canonical location.

**Fix:**
1. `rm -rf skills/` from repo root
2. Ensure `skills/` is in `.gitignore` so it never gets re-tracked
3. The sync script should strip root `skills/` before committing:
   ```bash
   rm -rf skills/ 2>/dev/null
   ```
4. Commit the `.gitignore` update and push

## Pattern 2: Secret Scan — gitleaks false positive

**Error:** `gitleaks` workflow fails on `main` branch.

**Root cause:** Auto-generated hypothesis test-cache files (`.hypothesis/constants/*`) contain strings that look like credentials. OR a real credential was committed (HF_TOKEN, Kaggle token, etc.)

**Diagnosis:** Check the gitleaks output for the file path and value. If it's a `.hypothesis/` file, it's a false positive.

**Fix:**
1. Add `.hypothesis/` to `.gitignore`
2. Remove from tracking: `git rm -r --cached .hypothesis/`
3. Commit and push

## Pattern 3: Test dependency missing

**Error:** `ModuleNotFoundError: No module named 'hypothesis'` or similar during `Run tests with coverage`.

**Root cause:** CI runs `uv sync --all-extras` which uses the lockfile. If a new dependency was added but `uv.lock` wasn't updated, the test dependency isn't available.

**Fix:**
1. Run `uv lock` locally to regenerate the lockfile
2. Commit the updated `uv.lock`

## Pattern 5: BFCL false positives (substring matching)

**Error:** All models show ✅ 5/5 on tool-calling tests, but actually none called a tool.

**Root cause:** The test used `grep -qi "get_weather"` which matches plain English text like "the **weather** in Tokyo is...". The grep found the keyword in the model's free-text response, not in an actual tool call.

**Fix:**
1. Check for EXACT tool call syntax — the output must START with a tool construct, not just contain a keyword:
   ```bash
   echo "$output" | grep -qiE "^(<tool|tool_call|<search|<get_|<calculate|<get_time)"
   ```
2. Always inspect the first line of output, not the whole response
3. Run multi-trial tests (5 runs minimum) with format-specific checks
4. Verify by looking at the raw output, not just pass/fail counts

**Proof pattern (this session's finding):**
```bash
# Before (BROKEN): substring match
grep -qi "get_weather" <<< "the weather in Tokyo is sunny"  # ❌ passes
# After (CORRECT): first-line tool syntax check
head -1 <<< "the weather in Tokyo is sunny" | grep -qiE "^(<tool|tool_call)"  # ❌ correctly fails
```

## Pattern 6: CI log access

The GitHub log-download endpoint requires token auth. Use:
```bash
TOKEN=$(cat ~/.git-credentials | grep -oP '(?<=x-access-token:)[^@]+(?=@github\.com)')
curl -sL -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/actions/runs/<RUN_ID>/logs"
```

If the token lacks the `actions:read` scope, inspect the failing step's output from the GitHub Actions web UI instead (visible without auth).
