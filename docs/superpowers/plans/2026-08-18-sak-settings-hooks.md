# Sak Settings Hooks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two team-wide Claude Code hooks to `Sak-Family-Agent/.claude/settings.json` — a PostToolUse `ruff check --fix` pass that complements the existing `ruff format` hook, and a PreToolUse reminder that fires when a byte-synced persona copy of `guardrails.py` / `web/server.py` is edited outside the canonical path.

**Architecture:** Both hooks are `command`-type hooks in `.claude/settings.json`. Each reads the hook's stdin JSON, extracts `tool_input.file_path`, and branches on a shell `case` glob. The PostToolUse hook runs `uv run ruff check --fix` on edited Python files in the canonical package and tests. The PreToolUse hook emits a `{"systemMessage": ...}` JSON document (non-blocking) when the edited path is a non-canonical byte-synced copy, pointing the editor at the canonical source and the parity test. No new files are created; one file is modified.

**Tech Stack:** Claude Code hooks (settings.json `hooks` schema), bash `case` globs, `uv` + `ruff`, `python3` (JSON extraction fallback and settings validation).

**Spec:** (none — derived from the `claude-automation-recommender` recommendations produced 2026-08-18; this plan is self-contained and argues from the repo conventions in `CLAUDE.md` / `AGENTS.md`.)

## Global Constraints

- **`jq` is not installed** in this environment. Every hook command MUST use the `if command -v jq …; then jq …; else python3 -c …; fi` fallback pattern — copy it verbatim from the existing `ruff format` hook. Do not write a hook that assumes `jq`.
- Hooks run with the working directory set by the harness; commands that need the repo root MUST `cd "${CLAUDE_PROJECT_DIR:-$PWD}"` first (match the existing hook).
- Hook `tool_input.file_path` may arrive **relative** (`personas/…`) or **absolute** (`/home/beern/Sak-Family-Agent/personas/…`). Path globs MUST match both — use a leading `*` (e.g. `*personas/sakjules/…`) which matches zero-or-more leading characters.
- These are **team-wide** hooks → write to `.claude/settings.json` (committed). Do NOT use `.claude/settings.local.json`.
- The PreToolUse hook is a **non-blocking reminder only** — it emits `systemMessage` and does NOT set `permissionDecision`. Editors are informed, not blocked.
- **Canonical path** for the synced files is `personas/sakthai/sakthai/agent/guardrails.py` and `personas/sakthai/sakthai/web/server.py`. The `sakthai` persona MUST NOT trigger the reminder.
- **Non-canonical (byte-synced) copies** that MAY drift: `personas/{sakjules,sakking,saksee,saksit,saktan}/sakthai/agent/guardrails.py` and `personas/{sakjules,sakking,saksee,saksit,saktan}/sakthai/web/server.py`. (Each is a real 1515-line / 433-line file on disk.)
- The parity invariant is enforced by `tests/test_persona_guardrails_parity.py`; run it with `uv run pytest tests/test_persona_guardrails_parity.py -q`.
- Python lint/format uses `uv run ruff …` (never bare `ruff`). `ruff` excludes `library/` and `scripts/` via `pyproject.toml`, so scoping the hook to `personas/sakthai/sakthai/*.py` and `tests/*.py` is correct and matches the existing format hook.
- **Amendment (2026-08-18, plan-mandated-finding ruling):** the `ruff check --fix` hook command uses `--quiet` (`uv run ruff check --fix --quiet "$file_path" 2>/dev/null || true`). Without `--quiet`, `ruff check` prints `All checks passed!` to stdout on every clean file, and PostToolUse hook stdout is surfaced into the transcript — asymmetric noise vs. the silent `ruff format` hook. Verified: `--quiet` yields empty stdout + exit 0 on a clean file (parity with `format`). The Task 1 review raised this as Important/`plan-mandated`; the spec's silent-auto-fix intent supports the amendment over the plan's earlier literal `2>/dev/null`-only command.
- Conventional commit prefixes are used in this repo (`feat:`, `chore:`, `refactor:`, …).

## How these hooks work (read first if you're new to Claude Code hooks)

A `command`-type hook is a shell command the harness runs at a lifecycle event. The harness pipes a JSON object to the hook's **stdin** describing the tool call. For `Write`/`Edit`, the relevant shape is:

```json
{"tool_name": "Edit", "tool_input": {"file_path": "tests/test_cli.py", "old_string": "...", "new_string": "..."}}
```

- **PostToolUse** runs *after* a successful Write/Edit. Used here to auto-fix the file just written.
- **PreToolUse** runs *before* the tool is allowed to proceed. A hook can print a JSON object on stdout to influence behavior; printing `{"systemMessage": "…"}` surfaces a message to the model/user without blocking. That is what the reminder hook uses.

The `matcher` field is a regex-ish tool-name pattern (`"Write|Edit"` matches either tool). Multiple hooks in one entry's `hooks` array all run for a match, in order.

## File Structure

- **Modify:** `Sak-Family-Agent/.claude/settings.json` — the only file touched.
  - Task 1 adds a second `command` hook to the *existing* `PostToolUse` / `Write|Edit` entry's `hooks` array (so `ruff format` then `ruff check --fix` both run).
  - Task 2 adds a new top-level `PreToolUse` key with one entry / one hook.
- **No new files.**
- "Tests" are: (a) pipe-test the command with synthesized stdin, (b) validate `settings.json` structure with `python3` (there is no `jq`), (c) prove the hook fires in the harness.

---

### Task 1: PostToolUse `ruff check --fix` hook

**Files:**
- Modify: `Sak-Family-Agent/.claude/settings.json` (the existing `hooks.PostToolUse[0].hooks` array — add a second entry)

**Interfaces:**
- Consumes: the existing `hooks.PostToolUse[0]` entry (matcher `Write|Edit`, one `ruff format` hook). Leaves it intact; appends a sibling.
- Produces: a `settings.json` whose `PostToolUse` / `Write|Edit` entry runs `ruff format` then `ruff check --fix` on edited Python files under `personas/sakthai/sakthai/` and `tests/`.

**Context — the exact current `settings.json` (before this task):**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "file_path=$(if command -v jq >/dev/null 2>&1; then jq -r '.tool_input.file_path // empty' 2>/dev/null; else python3 -c \"import json,sys;d=json.load(sys.stdin);print((d.get('tool_input') or {}).get('file_path') or '')\" 2>/dev/null; fi); case \"$file_path\" in personas/sakthai/sakthai/*.py|*/personas/sakthai/sakthai/*.py|tests/*.py|*/tests/*.py) cd \"${CLAUDE_PROJECT_DIR:-$PWD}\" && uv run ruff format \"$file_path\" 2>/dev/null || true ;; esac"
          }
        ]
      }
    ]
  }
}
```

The new hook command (the second entry). It is identical to the format hook except it runs `ruff check --fix` instead of `ruff format`:

```
file_path=$(if command -v jq >/dev/null 2>&1; then jq -r '.tool_input.file_path // empty' 2>/dev/null; else python3 -c "import json,sys;d=json.load(sys.stdin);print((d.get('tool_input') or {}).get('file_path') or '')" 2>/dev/null; fi); case "$file_path" in personas/sakthai/sakthai/*.py|*/personas/sakthai/sakthai/*.py|tests/*.py|*/tests/*.py) cd "${CLAUDE_PROJECT_DIR:-$PWD}" && uv run ruff check --fix --quiet "$file_path" 2>/dev/null || true ;; esac
```

- [ ] **Step 1: Pipe-test the new command standalone (prove it works before wiring it in)**

Run from the `Sak-Family-Agent` repo root. This synthesizes the stdin JSON the harness would send after an Edit on a test file:

```bash
cd /home/beern/Sak-Family-Agent
echo '{"tool_name":"Edit","tool_input":{"file_path":"tests/test_cli.py"}}' | bash -c 'file_path=$(if command -v jq >/dev/null 2>&1; then jq -r ".tool_input.file_path // empty" 2>/dev/null; else python3 -c "import json,sys;d=json.load(sys.stdin);print((d.get(\"tool_input\") or {}).get(\"file_path\") or \"\")" 2>/dev/null; fi); case "$file_path" in personas/sakthai/sakthai/*.py|*/personas/sakthai/sakthai/*.py|tests/*.py|*/tests/*.py) cd "${CLAUDE_PROJECT_DIR:-$PWD}" && uv run ruff check --fix --quiet "$file_path" 2>/dev/null || true ;; esac'
```

Expected: exit 0, no stdout. `ruff check --fix` on an already-clean file is a no-op. (If `tests/test_cli.py` has autofixable issues, they will be fixed in place — that is the hook working correctly; let it run.) Confirm there is no error about a missing `jq` (the fallback handles it).

- [ ] **Step 2: Edit `settings.json` to add the second hook entry**

Modify `Sak-Family-Agent/.claude/settings.json` so the `PostToolUse[0].hooks` array has **two** entries — the existing `ruff format` one (unchanged) first, then the new `ruff check --fix` one. The full file after this step:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "file_path=$(if command -v jq >/dev/null 2>&1; then jq -r '.tool_input.file_path // empty' 2>/dev/null; else python3 -c \"import json,sys;d=json.load(sys.stdin);print((d.get('tool_input') or {}).get('file_path') or '')\" 2>/dev/null; fi); case \"$file_path\" in personas/sakthai/sakthai/*.py|*/personas/sakthai/sakthai/*.py|tests/*.py|*/tests/*.py) cd \"${CLAUDE_PROJECT_DIR:-$PWD}\" && uv run ruff format \"$file_path\" 2>/dev/null || true ;; esac"
          },
          {
            "type": "command",
            "command": "file_path=$(if command -v jq >/dev/null 2>&1; then jq -r '.tool_input.file_path // empty' 2>/dev/null; else python3 -c \"import json,sys;d=json.load(sys.stdin);print((d.get('tool_input') or {}).get('file_path') or '')\" 2>/dev/null; fi); case \"$file_path\" in personas/sakthai/sakthai/*.py|*/personas/sakthai/sakthai/*.py|tests/*.py|*/tests/*.py) cd \"${CLAUDE_PROJECT_DIR:-$PWD}\" && uv run ruff check --fix --quiet \"$file_path\" 2>/dev/null || true ;; esac"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 3: Validate the JSON and the hook structure with `python3` (no `jq` available)**

```bash
cd /home/beern/Sak-Family-Agent
python3 -c "import json; d=json.load(open('.claude/settings.json')); h=d['hooks']['PostToolUse'][0]; assert h['matcher']=='Write|Edit', 'matcher wrong'; cmds=[x['command'] for x in h['hooks']]; assert len(cmds)==2, f'expected 2 hooks, got {len(cmds)}'; assert any('ruff format' in c for c in cmds), 'missing ruff format'; assert any('ruff check --fix' in c for c in cmds), 'missing ruff check --fix'; assert all('command -v jq' in c for c in cmds), 'a hook lacks the jq fallback'; print('PostToolUse OK:', len(cmds), 'hooks')"
```

Expected: `PostToolUse OK: 2 hooks`. A malformed `settings.json` raises `json.JSONDecodeError`; a structural mistake raises `AssertionError` with a message naming the problem. Either failure means the file is broken — fix it before continuing (a broken `settings.json` silently disables **all** settings from that file).

- [ ] **Step 4: Prove the hook fires in the harness**

Open `/hooks` once in the Claude Code UI to force a config reload (the settings watcher only watches directories that held a settings file at session start; `.claude/` did, but reloading guarantees the new entry is live). Then, in this session, use the Edit tool to introduce a `ruff`-autofixable violation in a test file — add an unused import on its own line near the top of `tests/test_cli.py`:

```python
import os
```

(Place it above the first real import. `ruff` rule F401 "unused import" is autofixed by `ruff check --fix`. Do NOT use trailing whitespace as the violation — the Edit tool strips trailing whitespace before writing, so the hook would have nothing to fix.)

Re-read `tests/test_cli.py`. Expected: the `import os` line is gone — the `ruff check --fix` hook removed it. That proves the hook fired and autofixed.

- [ ] **Step 5: Revert the test edit**

Remove the `import os` line you added if it somehow survived (it should not have), leaving `tests/test_cli.py` exactly as it was before Step 4. Verify with:

```bash
cd /home/beern/Sak-Family-Agent
git diff --stat tests/test_cli.py
```

Expected: no diff (or only the unused-import removal, which you then restore by `git checkout -- tests/test_cli.py`).

- [ ] **Step 6: Commit**

```bash
cd /home/beern/Sak-Family-Agent
git add .claude/settings.json
git commit -m "feat(claude): add PostToolUse ruff check --fix hook for Python edits"
```

---

### Task 2: PreToolUse guardrail-sync reminder hook

**Files:**
- Modify: `Sak-Family-Agent/.claude/settings.json` (add a new top-level `PreToolUse` key alongside `PostToolUse`)

**Interfaces:**
- Consumes: the `settings.json` produced by Task 1 (reads its existing `hooks` object).
- Produces: a `PreToolUse` / `Write|Edit` hook that prints `{"systemMessage": …}` when the edited path is one of the ten non-canonical byte-synced copies, and prints nothing otherwise (including for the canonical `sakthai` paths).

**The new hook command.** The `case` lists all ten non-canonical copy paths (5 personas × 2 files). The leading `*` matches both relative and absolute paths. The `printf '%s'` emits the JSON; the message contains no double-quotes so it needs no escaping inside the JSON string:

```
file_path=$(if command -v jq >/dev/null 2>&1; then jq -r '.tool_input.file_path // empty' 2>/dev/null; else python3 -c "import json,sys;d=json.load(sys.stdin);print((d.get('tool_input') or {}).get('file_path') or '')" 2>/dev/null; fi); case "$file_path" in *personas/sakjules/sakthai/agent/guardrails.py|*personas/sakking/sakthai/agent/guardrails.py|*personas/saksee/sakthai/agent/guardrails.py|*personas/saksit/sakthai/agent/guardrails.py|*personas/saktan/sakthai/agent/guardrails.py|*personas/sakjules/sakthai/web/server.py|*personas/sakking/sakthai/web/server.py|*personas/saksee/sakthai/web/server.py|*personas/saksit/sakthai/web/server.py|*personas/saktan/sakthai/web/server.py) printf '%s' '{"systemMessage":"Editing a byte-synced persona copy. Canonical source: personas/sakthai/sakthai/agent/guardrails.py (or web/server.py). tests/test_persona_guardrails_parity.py fails CI on drift — edit canonical and re-sync, then run: uv run pytest tests/test_persona_guardrails_parity.py -q"}' ;; esac
```

- [ ] **Step 1: Pipe-test — matching path MUST emit the systemMessage**

```bash
cd /home/beern/Sak-Family-Agent
echo '{"tool_name":"Edit","tool_input":{"file_path":"personas/sakjules/sakthai/agent/guardrails.py"}}' | bash -c 'file_path=$(if command -v jq >/dev/null 2>&1; then jq -r ".tool_input.file_path // empty" 2>/dev/null; else python3 -c "import json,sys;d=json.load(sys.stdin);print((d.get(\"tool_input\") or {}).get(\"file_path\") or \"\")" 2>/dev/null; fi); case "$file_path" in *personas/sakjules/sakthai/agent/guardrails.py|*personas/sakking/sakthai/agent/guardrails.py|*personas/saksee/sakthai/agent/guardrails.py|*personas/saksit/sakthai/agent/guardrails.py|*personas/saktan/sakthai/agent/guardrails.py|*personas/sakjules/sakthai/web/server.py|*personas/sakking/sakthai/web/server.py|*personas/saksee/sakthai/web/server.py|*personas/saksit/sakthai/web/server.py|*personas/saktan/sakthai/web/server.py) printf "%s" "{\"systemMessage\":\"Editing a byte-synced persona copy. Canonical source: personas/sakthai/sakthai/agent/guardrails.py (or web/server.py). tests/test_persona_guardrails_parity.py fails CI on drift — edit canonical and re-sync, then run: uv run pytest tests/test_persona_guardrails_parity.py -q\"}" ;; esac'
```

Expected stdout (exactly):

```
{"systemMessage":"Editing a byte-synced persona copy. Canonical source: personas/sakthai/sakthai/agent/guardrails.py (or web/server.py). tests/test_persona_guardrails_parity.py fails CI on drift — edit canonical and re-sync, then run: uv run pytest tests/test_persona_guardrails_parity.py -q"}
```

Also test an absolute matching path (proves the `*` glob covers `/home/…`):

```bash
echo '{"tool_name":"Edit","tool_input":{"file_path":"/home/beern/Sak-Family-Agent/personas/saksee/sakthai/web/server.py"}}' | bash -c '<same command as above>'
```

Expected: the same `{"systemMessage": …}` line.

- [ ] **Step 2: Pipe-test — canonical path MUST NOT emit anything**

```bash
cd /home/beern/Sak-Family-Agent
echo '{"tool_name":"Edit","tool_input":{"file_path":"personas/sakthai/sakthai/agent/guardrails.py"}}' | bash -c '<same command as above>'
```

Expected: **no stdout** (the canonical `sakthai` path is deliberately not in the `case`). This is the critical negative case — a reminder on the canonical file would be noise. Also confirm `personas/sakthai/sakthai/web/server.py` produces no output.

- [ ] **Step 3: Pipe-test — unrelated path MUST NOT emit anything**

```bash
cd /home/beern/Sak-Family-Agent
echo '{"tool_name":"Edit","tool_input":{"file_path":"tests/test_cli.py"}}' | bash -c '<same command as above>'
```

Expected: no stdout.

- [ ] **Step 4: Edit `settings.json` to add the `PreToolUse` block**

Add a `PreToolUse` key alongside the existing `PostToolUse` key. The full file after this step (Task 1's two PostToolUse hooks preserved, Task 2's PreToolUse added):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "file_path=$(if command -v jq >/dev/null 2>&1; then jq -r '.tool_input.file_path // empty' 2>/dev/null; else python3 -c \"import json,sys;d=json.load(sys.stdin);print((d.get('tool_input') or {}).get('file_path') or '')\" 2>/dev/null; fi); case \"$file_path\" in personas/sakthai/sakthai/*.py|*/personas/sakthai/sakthai/*.py|tests/*.py|*/tests/*.py) cd \"${CLAUDE_PROJECT_DIR:-$PWD}\" && uv run ruff format \"$file_path\" 2>/dev/null || true ;; esac"
          },
          {
            "type": "command",
            "command": "file_path=$(if command -v jq >/dev/null 2>&1; then jq -r '.tool_input.file_path // empty' 2>/dev/null; else python3 -c \"import json,sys;d=json.load(sys.stdin);print((d.get('tool_input') or {}).get('file_path') or '')\" 2>/dev/null; fi); case \"$file_path\" in personas/sakthai/sakthai/*.py|*/personas/sakthai/sakthai/*.py|tests/*.py|*/tests/*.py) cd \"${CLAUDE_PROJECT_DIR:-$PWD}\" && uv run ruff check --fix --quiet \"$file_path\" 2>/dev/null || true ;; esac"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "file_path=$(if command -v jq >/dev/null 2>&1; then jq -r '.tool_input.file_path // empty' 2>/dev/null; else python3 -c \"import json,sys;d=json.load(sys.stdin);print((d.get('tool_input') or {}).get('file_path') or '')\" 2>/dev/null; fi); case \"$file_path\" in *personas/sakjules/sakthai/agent/guardrails.py|*personas/sakking/sakthai/agent/guardrails.py|*personas/saksee/sakthai/agent/guardrails.py|*personas/saksit/sakthai/agent/guardrails.py|*personas/saktan/sakthai/agent/guardrails.py|*personas/sakjules/sakthai/web/server.py|*personas/sakking/sakthai/web/server.py|*personas/saksee/sakthai/web/server.py|*personas/saksit/sakthai/web/server.py|*personas/saktan/sakthai/web/server.py) printf '%s' '{\"systemMessage\":\"Editing a byte-synced persona copy. Canonical source: personas/sakthai/sakthai/agent/guardrails.py (or web/server.py). tests/test_persona_guardrails_parity.py fails CI on drift — edit canonical and re-sync, then run: uv run pytest tests/test_persona_guardrails_parity.py -q\"}' ;; esac"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 5: Validate the JSON and the PreToolUse structure with `python3`**

```bash
cd /home/beern/Sak-Family-Agent
python3 -c "import json; d=json.load(open('.claude/settings.json')); assert set(d['hooks']) == {'PostToolUse','PreToolUse'}, f'unexpected hook keys: {set(d[\"hooks\"])}'; p=d['hooks']['PreToolUse'][0]; assert p['matcher']=='Write|Edit', 'PreToolUse matcher wrong'; c=p['hooks'][0]['command']; assert c.count('type') or True; assert 'systemMessage' in c, 'no systemMessage in command'; assert 'sakjules' in c and 'saktan' in c, 'missing non-canonical personas'; assert 'command -v jq' in c, 'lacks jq fallback'; assert 'sakthai/sakthai/agent/guardrails.py' in c, 'message missing canonical path'; print('PreToolUse OK; PostToolUse still', len(d['hooks']['PostToolUse'][0]['hooks']), 'hooks')"
```

Expected: `PreToolUse OK; PostToolUse still 2 hooks`. This also confirms Task 1's hooks survived the edit.

- [ ] **Step 6: Confirm the parity test still passes (the hooks touch no Python, but assert no drift was introduced)**

```bash
cd /home/beern/Sak-Family-Agent
uv run pytest tests/test_persona_guardrails_parity.py -q
```

Expected: PASS. (The hooks are config-only; this is a belt-and-braces check that nothing under `personas/*/sakthai/` was disturbed.)

- [ ] **Step 7: Prove the hook fires in the harness (non-destructive)**

Open `/hooks` once to reload config. The PreToolUse matcher is `Write|Edit`, which fires in-session. To prove it fires **without editing a real byte-synced file**, temporarily prepend a sentinel to the command and add a throwaway path to the `case`:

1. In `.claude/settings.json`, change the PreToolUse command's `case` glob to also match `*/tmp/hook-fire-test.py` and prefix the body with a sentinel echo. The temporary command's `case` line becomes:

   ```
   case "$file_path" in */tmp/hook-fire-test.py|*personas/sakjules/sakthai/agent/guardrails.py|*personas/sakking/sakthai/agent/guardrails.py|*personas/saksee/sakthai/agent/guardrails.py|*personas/saksit/sakthai/agent/guardrails.py|*personas/saktan/sakthai/agent/guardrails.py|*personas/sakjules/sakthai/web/server.py|*personas/sakking/sakthai/web/server.py|*personas/saksee/sakthai/web/server.py|*personas/saksit/sakthai/web/server.py|*personas/saktan/sakthai/web/server.py) echo "pretooluse-fired" >> /tmp/hook-fire.txt; printf '%s' '{"systemMessage":"..."}' ;; esac
   ```

2. Create the throwaway file and trigger an Edit on it:

   ```bash
   echo "x" > /tmp/hook-fire-test.py
   ```
   Then use the Edit tool to change `x` to `y` in `/tmp/hook-fire-test.py`.

3. Check the sentinel:

   ```bash
   cat /tmp/hook-fire.txt
   ```
   Expected: `pretooluse-fired` (the PreToolUse hook ran before the Edit was allowed).

4. **Revert:** restore the PreToolUse command in `.claude/settings.json` to the exact form from Step 4 (remove the `*/tmp/hook-fire-test.py` glob and the sentinel echo), then clean up:

   ```bash
   rm -f /tmp/hook-fire-test.py /tmp/hook-fire.txt
   ```

5. Re-run the Step 5 validation to confirm the final `settings.json` is the intended one.

If the sentinel never appears: the pipe-tests (Steps 1–3) already proved the command logic and the `python3` validation (Step 5) proved the file shape — the miss is the settings watcher, not the hook. Open `/hooks` once more or restart Claude Code; you cannot reload from within a tool call.

- [ ] **Step 8: Commit**

```bash
cd /home/beern/Sak-Family-Agent
git add .claude/settings.json
git commit -m "feat(claude): add PreToolUse guardrail-sync reminder for byte-synced persona copies"
```

---

## Self-Review

**1. Spec coverage.** The recommendation specified two hooks: (a) PostToolUse `ruff check --fix` on Python edits → Task 1. (b) PreToolUse guardrail-sync reminder for non-canonical byte-synced copies → Task 2. Both covered. The "extend the existing hook block" guidance is honored: Task 1 appends to the existing `PostToolUse[0].hooks` array rather than replacing it.

**2. Placeholder scan.** No `TODO`/`TBD`/"add appropriate handling". Every code step contains the exact command or exact JSON. The `<same command as above>` tokens in Task 2 Steps 1–3 refer to the fully-written command in the task's intro paragraph (repeated verbatim where the engineer copies it into a `bash -c`); this is a copy pointer to text within the same task, not a forward reference to another task.

**3. Type / structural consistency.** The `PostToolUse` entry retains matcher `Write|Edit` and grows from 1 to 2 hooks (Task 1), then stays at 2 (Task 2's Step 5 asserts this). The `PreToolUse` entry uses the same matcher. Both hooks use the identical `jq`-or-`python3` `file_path` extraction prefix. The non-canonical persona list (`sakjules, sakking, saksee, saksit, saktan`) is consistent across the `case` glob (10 patterns) and the Step 5 validation. The canonical `sakthai` is consistently excluded from the reminder and included in the PostToolUse format/check scope.