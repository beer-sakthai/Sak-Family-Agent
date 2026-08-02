# Batch YAML Frontmatter Operations

A reusable Python approach for editing YAML frontmatter across all SKILL.md files in the repo.

Use cases:
- Bulk-add/update `author:` field across all skills
- Bulk-add/update `version:` field across all skills
- Bulk-add/update `license:` field across all skills
- Any single-value YAML metadata change across the entire skill library

## Pitfall — sed breaks on multi-line descriptions

```bash
# DON'T do this — it breaks YAML for multi-line description: | and >- fields
sed -i '/^description:/a\author: SakThai' */SKILL.md
```

YAML block scalars (`|` for literal, `>-` for folded) span multiple lines.
Appending after `description:` injects the new field between the header
and the content, producing invalid YAML.

**Check for multi-line descriptions first:**
```bash
grep -l '^description: [|>]' skills/*/SKILL.md 2>/dev/null
```

## Working pattern — Python YAML frontmatter parser

```python
#!/usr/bin/env python3
"""Batch-fix SKILL.md frontmatter: target field across all files."""
import os

REPO = "/opt/data/sakthai-skills-repo/skills"

def parse_frontmatter(lines):
    """Return (frontmatter_lines, body_lines)"""
    if not lines or lines[0].strip() != '---':
        return None, lines
    end = 1
    while end < len(lines) and lines[end].strip() != '---':
        end += 1
    if end >= len(lines):
        return None, lines
    return lines[1:end], lines[end+1:]

def get_field(fm_lines, field):
    """Return (value, index) of a single-line YAML field."""
    for i, line in enumerate(fm_lines):
        stripped = line.rstrip()
        if stripped.startswith(field + ':') and \
           (len(stripped) == len(field) + 1 or stripped[len(field)+1] == ' '):
            return stripped[len(field)+1:].strip(), i
    return None, -1

def insert_after(fm_lines, after_field, new_line):
    """Insert new_line after the first occurrence of after_field.
    Skips multi-line fields (ending with |, >-, or >)."""
    for i, line in enumerate(fm_lines):
        if line.startswith(after_field + ':') and \
           not (line.endswith('|') or line.endswith('>-') or line.endswith('>')):
            fm_lines.insert(i + 1, new_line)
            return
    fm_lines.insert(1, new_line)  # fallback: after first line

for root, dirs, files in os.walk(REPO):
    for fn in files:
        if fn != 'SKILL.md':
            continue
        path = os.path.join(root, fn)
        with open(path) as f:
            text = f.read()
        lines = text.split('\n')
        fm_lines, body = parse_frontmatter(lines)
        if fm_lines is None:
            continue

        original = list(fm_lines)

        # --- Add/modify target field ---
        val, idx = get_field(fm_lines, 'target_field')
        if val is None:
            insert_after(fm_lines, 'name', 'target_field: value')

        if fm_lines == original:
            continue

        new_text = '---\n' + '\n'.join(fm_lines) + '\n---\n' + '\n'.join(body)
        with open(path, 'w') as f:
            f.write(new_text)

        rel = os.path.relpath(path, REPO)
        print(f"  Updated {rel}")
```

## Testing before bulk run

```bash
# 1. Test on one file
python3 -c "
import yaml
with open('skills/SakThai-plan/SKILL.md') as f:
    content = f.read()
    fm = content.split('---')[1]
    data = yaml.safe_load(fm)
    print(data.keys())
"

# 2. Dry run — count only
grep -r "^author:" skills/ --include=SKILL.md | wc -l

# 3. Check affected files before commit
git diff --stat
```

## Subagent stale-path trap

When running batch operations on the repo AFTER a `git mv` rename, the
old directory paths (e.g. `mlops/hf-agents-course/`) may still exist
in the working tree even though they're no longer tracked by git.

If a subagent discovers these stale paths and writes improvements there,
the changes go to the OLD location — not to the current `skills/SakThai-*`
paths. The git index only tracks the new paths, so the subagent's work
is invisible to git until someone manually copies it over.

**Prevention:**
```bash
# Before dispatching subagents, clean stale working-tree files
git clean -fd                                # removes all untracked files
# OR (more targeted)
find . -path ./.git -prune -o -type d -name "hf-*" -print | xargs rm -rf
```

**Detection:**
```bash
# Check if old paths still have content
for old in autonomous-ai-agents mlops github research communication; do
  [ -d "$old" ] && echo "STALE: $old/ still has $(find $old -type f | wc -l) files"
done
```

**Recovery:** Compare file sizes between old and new paths — the larger
one has the improvements. Copy the SKILL.md and references/ dir over.
