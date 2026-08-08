# Execution Pattern References

## Prompt verification sequence

In this session, after creating skills, the agent realized the skill
registry did not reflect the new skills. The correct sequence was:

1. Inspect the target skill path.
2. Read the skill file for verification.
3. Confirm via `skills_list`.
4. Continue with the task instead of rerunning creation behavior.

## Evidence-first rule

Before any command is run to install or fix dependency state, confirm:
- authoritative docs URL and exact command
- installed version from which the script is being run
- shebang/proxy/symlink state if packages or binaries are involved

Missing any of the above counts as insufficient evidence to act.

## Empty-output trap

When a tool call returns no content, treat that as a state change and
use explicit read/inspect calls to verify progress. Do not reissue the
same intent without inspection.

## User-provided path mismatch

When the user gives a filesystem path that does not exist on disk,
do not assume the task is impossible — search for the actual location
before concluding. The path may be a stale reference, a different repo
structure, or a renamed directory. One `search_files(target="files")`
or `ls` probe resolves the ambiguity.

Example from session: user gave
`/opt/data/sakthai-skills-repo/personas/sakking/skills/` which did not
exist. Searching revealed the actual skills at
`/opt/data/Sak-Family-Agent/personas/sakking/skills/`.

## Two-copy divergence (runtime vs repo)

Hermes skills exist in two copies that can independently diverge:
- **Runtime copy** at `~/.hermes/skills/<category>/<name>/` — loaded
  every session, affects agent behavior.
- **Repo copy** under version control (e.g. Sak-Family-Agent repo)
  — may have different content, version number, or stale references.

A fix applied to the repo copy is not automatically reflected in the
runtime copy, and vice versa. When maintaining skills, verify which
copy is being modified and apply the fix to both when appropriate.
The runtime copy is what actually loads, so it takes priority for
behavioral fixes.

## `read_file` display ambiguity

When reading files with `read_file` (especially with offset/limit
pagination), the `LINE_NUM|CONTENT` output format can be ambiguous
when the file content itself contains `|` or backtick characters.

Backticks in particular are invisible in the `read_file` display
because they are consumed as markdown formatting. Pipe characters
adjacent to the line-number separator can also be misread.

**How it manifests:** The agent sees what appears to be a formatting
bug (unclosed backtick, broken inline code) and acts on it, when the
file is actually correct.

**Resolution:** Before acting on a suspected content issue detected
via `read_file`, verify with raw bytes:

```python
line = open(path, 'rb').readlines()[N]
print(repr(line))
for i, b in enumerate(line):
    if b == 96:  # backtick
        print(f'backtick at byte {i}: context={line[max(0,i-3):i+4]}')
```

Alternatively, use `python3 -c "print(repr(open(path).readlines()[N]))"`
to get a precise string representation that exposes every character.

**Lesson:** `read_file` is a high-level display tool, not an
authoritative source for character-level content inspection. When
the question is "does this file contain the exact characters I
expect," use raw bytes or `repr()` as the evidence source.

## `patch` tool false-success with special characters

The `patch` agent tool can report `"success": true` without actually
applying any change when the target content contains special
characters such as backticks, asterisks, or unbalanced quotes. The
fuzzy matcher may accept the pattern but produce an identical output
(no-op), or write content that looks correct to the display layer
but still contains the original issue.

**How it manifests in this session:** Three separate `patch` calls
(the Hermes tool, not the terminal-tool patch mode) claimed success
on fixing unclosed backtick code spans in a SKILL.md file. Each
returned `"success": true`. The content never changed. The fix only
applied when using `python3 -c` via `terminal()` to do a
`str.replace()` on the file content directly.

**Resolution sequence when `patch` reports success but content
doesn't change:**

1. **Verify the change** — immediately read the target line with
   `python3 -c "print(repr(open(path).readlines()[N]))"` to see the
   actual byte-level content. Do NOT trust `read_file` for this check
   (see ambiguity note above).
2. **Escalate to terminal** — use a direct Python or sed command
   in `terminal()` to apply the fix. `patch`-like operations are
   reliable for regular text but degrade with backtick-heavy content.
3. **Verify again** — re-read with `repr()` to confirm the fix landed.

**Root cause:** The `patch` tool uses fuzzy matching strategies that
can match on structure while ignoring character-level details. For
plain text, this is fine. For markdown with code spans (backtick
delimiters), the delimiters themselves can confuse the match/apply
logic because they look like shell metacharacters or markdown
boundaries to the fuzzy layer.

**Lesson:** After every `patch` call that touches content with
backticks, asterisks, or inline code, verify independently with
`repr()` via terminal. `"success": true` from the `patch` tool is
a report of attempted application, not a guarantee of applied change.

## Confirmation-bias trap in patch verification

Terminal output and `read_file` can show misleading content when
the display layer transforms special characters. In one session, a
repo file already had `$GITHUB_TOKEN` and `<token>` in its curl
Authorization headers and Bearer pitfall text, but every display
tool showed `***` instead. Only byte-level verification against the
committed git object revealed the truth.

**How it manifests:** The agent reads a file via `read_file` or
`cat`/`sed`, sees `***` placeholders, assumes they need fixing, and
may even apply no-op patches that report success but change nothing
— because the file was already correct. The display layer creates
a false positive that wastes turns and risks introducing actual bugs.

**The git-object comparison technique** (proven in this session):

```python
import subprocess

# Get the committed version
old = subprocess.run(
    ['git', 'show', 'HEAD:path/to/file'],
    capture_output=True
)
old_lines = old.stdout.split(b'\n')
old_line_n = old_lines[INDEX]  # 0-indexed

# Get the current version
with open('path/to/file', 'rb') as f:
    current_lines = f.read().split(b'\n')
new_line_n = current_lines[INDEX]

# Compare hex
print('OLD hex:', old_line_n.hex())
print('NEW hex:', new_line_n.hex())

# Find byte-level differences
for i, (ob, nb) in enumerate(zip(old_line_n, new_line_n)):
    if ob != nb:
        print(f'Diff at byte {i}: '
              f'OLD={chr(ob) if 32<=ob<127 else f"0x{ob:02x}"} '
              f'NEW={chr(nb) if 32<=nb<127 else f"0x{nb:02x}"}')

if len(old_line_n) != len(new_line_n):
    print(f'Length differs: OLD={len(old_line_n)} NEW={len(new_line_n)}')
```

**Key principle:** Terminal output is a display-layer artifact, not
an authoritative source. When the question is "did my patch actually
change the file," the only reliable answer comes from comparing raw
bytes — most easily done against the committed git object for the
"before" state and `open(path, 'rb')` for the "after" state.

**Lesson:** Always complement display-layer verification with
byte-level git-object comparison, especially when the content
involves tokens, placeholders, or variables that look like shell
metacharacters.

## `od -c` as a lightweight byte-level probe

The Python `repr()` approach (`python3 -c "print(repr(open(path).readlines()[N]))"`)
spawns an interpreter and works everywhere Python is installed. A faster
native alternative for quick checks is `od -c` (coreutils, always
available on any Unix/POSIX system):

```bash
sed -n '569p' path/to/file | od -c
```

This dumps every byte as a printable character escape. Backticks appear
as `` ` ``, newlines as `\n`, tabs as `\t`, and non-printable bytes as
3-digit octal. Compared to `repr()`:

- **No Python dependency** — works in minimal environments.
- **Visual alignment** — characters are column-aligned at 16 bytes per
  row, making it easy to spot repeating patterns or unexpected bytes.
- **Instant feedback** — no import overhead; the shell pipes `sed`
  straight into `od`.

Example from a skill-audit cron session: `read_file` showed `***` on a
line — but `sed -n '569p' file | od -c` revealed the actual content was
`<token>`, confirming the file was already correct and preventing a
no-op patch.

**When to use `repr()` instead:** When you need to compare two lines
programmatically (e.g., diff old vs new across a commit boundary),
Python's string manipulation is more composable. `od -c` is for the
quick "what's actually on this exact line right now" check.

**Principle:** The inspection tool should match the inspection
precision. `read_file` is a prose-reading tool. `od -c` is a character-
inspection tool. Use the right tool for the question you're asking.

## 2026-07-26: Cron-audit display-layer redaction confirmation

**Context:** A scheduled cron job audited `SakKing-github-code-review`
in the repo. All display tools showed `***` as the token placeholder
in 15+ curl Authorization headers. The file appeared to need patching.

**What actually happened:** Byte-level verification (`od -A x -t x1z`)
revealed every single `***` was actually `$GITHUB_TOKEN` — the display
layer redacted the variable references for security. The file was
already correct and needed no changes.

**Tools that lied:** Display-layer redaction affected ALL of these:
- `read_file` (showed `***`)
- `terminal(grep -rn 'Bearer' ...)` (showed `***`)
- `terminal(sed -n 'LINEp' file)` (showed `***`)
- Terminal output piped to the conversation (display layer redacted)

**Tools that told the truth:**
- `od -A x -t x1z` (hex dump — `$GITHUB_TOKEN` = `24 47 49 54 48 55 42 5f 54 4f 4b 45 4e`)
- `od -c` (character dump — shows `$ G I T H U B _ T O K E N`)
- Python `open(path, 'rb')` via `execute_code` (raw bytes)

**Verification sequence used:**

```bash
# Step 1: Suspect redaction when you see *** in a file
grep -n 'Bearer' file.md  # shows "Bearer ***" — could be real or redacted

# Step 2: Verify with hex dump
sed -n 'LINEp' file.md | od -A x -t x1z
# If you see 24 47 49 54... it's $GITHUB_TOKEN, not ***

# Step 3: Use the automated script for bulk checks
python3 scripts/verify-file-bytes.py file.md --search "Bearer"
# Reports actual bytes with hex dump, flags redaction risks
```

**Key insight from this session:** The display-layer redaction is
pervasive — it affects every tool whose output passes through the
conversation display layer. Even `grep` in a terminal block had its
output redacted before the agent saw it. The ONLY reliable evidence
is raw bytes read outside the display layer (hex dump, Python
`open(path, 'rb')`, git object inspection).

**Lesson applied:** This session verified the `SakKing-execution-discipline`
skill's Rule #5 in real time. Without the hex probe, the agent would
have applied a no-op "fix" to a file that was already correct — wasting
turns and creating a misleading commit.
