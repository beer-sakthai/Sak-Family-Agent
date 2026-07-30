# Session 2026-07-25 — Key Lessons

## 1. Verify before reporting, never guess

Beer said "If I said it not check dont guess" — when checking any system state, read the raw output and report exactly what it says. Ambiguity is not license to guess.

## 2. Tool-calling requires the right inference engine

llama.cpp CLI cannot prove tool-calling capability (free text only). Transformers pipeline with chat template and proper `tools` definition is the correct test. Our 0.5B generates valid `<functioncall>` output.

## 3. CI fix rule: read the log first

Do not assume root cause from past knowledge. Always fetch and read the actual error log from the failing CI run. The log tells you what to fix.

## 4. Skills: GitHub + supermemory, both required

Every skill creation/update must be saved to GitHub AND to supermemory. Not one or the other — both. Use `supermemory-save` and `git add -f` if needed.

## 5. Subagent dataset corruption

Subagents can overwrite instead of append when modifying HF datasets. Always verify: check original remote count before dispatch, compare counts afterward, keep a backup commit hash for revert.
