---
name: SakSit-skill-library-maintenance
description: Audit, test, and evolve the skill library.
author: SakSit
category: core
tags:
- skill-management
- audit
- quality
- evolution
- maintenance
- sak-family
related_skills:
- hermes-skill-evolution
- plan
---

# Skill Library Maintenance

Maintain the quality of every SKILL.md in the agent's profile. Covers end-to-end lifecycle: inventory → structural test → content check → automated evolution → manual consolidation → deploy + monitor.

## Trigger When

- User asks to "test all skills," "run test all skills," "evolve skills," "audit skills," "review the skill library," or "clean up skills"
- A skill was found broken, outdated, or duplicate during use
- New skills have been added and need validation
- Periodic quality review (weekly/monthly)

## The 7-Phase Framework

### Phase 0: Inventory & Audit

Catalog every SKILL.md with metadata:
- name, path, category, line count
- YAML frontmatter parsed (check: name matches dir, description exists, version, tags)
- `linked_files`, `required_commands`, `required_environment_variables`
- Cross-reference `related_skills` against actual skill names
- Detect duplicates (same content, different name) and near-duplicates
- **Tool-reference classification** — scan each body for tool calls (`COMPOSIO_*`, `terminal(`, `browser_`, `execute_code`, `delegate_task`, `cronjob`, `image_generate`, `skill_view`, etc.). Classify skills as **Executable** (tools available), **Reference** (pure knowledge), or **Conditional** (needs Composio/API connections).

**Method (Python via execute_code):**
```python
import os, re, yaml
SKILLS_BASE = "/opt/data/profiles/saksit/skills"
skill_paths = []
for root, dirs, files in os.walk(SKILLS_BASE):
    for f in files:
        if f == "SKILL.md":
            skill_paths.append(os.path.join(root, f))
# Frontmatter check
for p in skill_paths:
    with open(p) as f: content = f.read()
    fm_match = re.match(r'^---\s*\n(.*?)\n(?:---|\.\.\.)', content, re.DOTALL)
    fm = yaml.safe_load(fm_match.group(1)) if fm_match else {}
    name = fm.get('name', '') if isinstance(fm, dict) else ''
# Linked file check
for p in skill_paths:
    with open(p) as f: content = f.read()
    body = re.sub(r'^---\s*\n.*?\n(?:---|\.\.\.)', '', content, count=1, flags=re.DOTALL)
    for m in re.finditer(r'(?:references|templates|scripts|assets)/[\w./-]+', body):
        ref = m.group(0).strip(')`.,"\'')
        if not os.path.exists(os.path.join(os.path.dirname(p), ref)):
            print(f"MISSING: {p} → {ref}")
```
**Output:** JSON inventory with validation flags per skill.

### Patching Broken References

When linked files are missing:
1. **Classify each reference** — is it a real file path or a regex false-positive? Check: `scripts/run_tests.sh` is real; `references/templates/scripts/assets` in prose text is a regex artifact from a sentence like "enforces the references/templates/scripts/assets subdir allowlist."
2. **Filter false-positives programmatically** by checking context before the match:
   ```python
   # Skip matches preceded by prose-signalling words
   before = body[max(0, m.start()-40):m.start()]
   if re.search(r'\b(the|and|or|in|of|for|to|by|subdir|allowlist|enforce|our|like|location|directory|path|here|see|under|listed)\b', before, re.I):
       continue  # prose, not a file reference

   # Skip matches preceded by a backtick (code/example context)
   if before.rstrip().endswith('`'):
       continue

   # Also skip matches where the captured subpath is empty or not a valid path
   subpath = m.group(1)
   if not subpath or not re.match(r'^[\w./-]+$', subpath):
       continue
   ```
   This catches common prose patterns (allowlist descriptions, natural language lists) without manual inspection of every match.
3. **Create stubs** for real missing files — minimal placeholder content that makes the reference resolve (scripts get boilerplate, templates get structure docs, reference files get topic summaries).
4. **Executable scripts** (`*.sh`) get `chmod 0o755`.
5. **Resolve false-positives** not caught by the filter by verifying the skill's markdown.
6. **Re-run linked-file check** to confirm all resolved.

### Phase 1: Structural Testing

Run the bundled structural test script:

```bash
uv pip install pyyaml -q
uv run python3 scripts/structural-test.py
```

This checks every SKILL.md for:
- **YAML frontmatter** — parses cleanly, required fields present
- **Description length** — must be ≤60 chars (hard limit: the system-prompt skill index truncates at 60 chars; anything past is silently cut and the skill never routes to the task. No grace margin.)
- **Tags presence** — skills without tags don't route well in the skill index
- **Name/dir match** — frontmatter `name:` must equal directory name
- **Linked files** — every `references/`, `templates/`, `scripts/`, `assets/` path resolves on disk
- **Related skills** — every name in `related_skills` cross-references an existing skill
- **Required commands** — every binary in `required_commands` exists on `$PATH`
- **Required env vars** — every variable in `required_environment_variables` is set

The script filters out prose false-positives (e.g. "enforces the references/templates/scripts/assets subdir") using a heuristic context check before each match.

**Output:** Reports grouping issues by check type with severity levels. Exit code 2 when critical issues found (frontmatter, missing refs).

Also accessible programmatically — see `scripts/structural-test.py` for the full implementation.

### Phase 1b: Bulk Fixing

When issues are found, use the bundled bulk-fix script:

```bash
# Dry-run first: report what would change without writing
uv run python3 scripts/bulk-fix.py --fix-desc --fix-tags --fix-name --fix-related --dry-run

# Then apply:
uv run python3 scripts/bulk-fix.py --fix-desc --fix-tags --fix-name --fix-related
```

The script handles four fix types independently (each opt-in via flag):
- `--fix-desc`: Replace long descriptions with concise ≤60-char versions (requires DESC_MAP dict populated at top of script)
- `--fix-tags`: Add tags to skills missing them (requires TAGS_MAP dict)
- `--fix-name`: Sync frontmatter `name:` field with the directory name
- `--fix-related`: Remove broken `related_skills` entries (handles both `- item` list format AND inline `[item1, item2]` array format)

**Critical rule: verify after EACH phase, not all at once.** Run the structural test between fix types to catch regressions early. A single script that does everything can corrupt YAML in ways that cascade across files.

See `scripts/bulk-fix.py` for full implementation.

### Phase 2: Content Accuracy & Freshness

Check that skill content matches current reality:
- Dry-run `skill_view()` on every actionable skill (not just reference content)
- For date-dated skills (e.g., `*-2026`), confirm they're tagged and relevant
- Sample read ~10% of reference-content skills for quality spot-check
- Flag skills with `setup_needed=true` and verify setup state

**Output:** Dry-run results, content quality scores, stale-skill warnings.

### Phase 3: Evolution Pipeline Setup

Install and validate the DSPy+GEPA evolution pipeline:

```bash
cd /opt/data/profiles/saksit/sak-family-agent/packages/agent-self-evolution
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

Configure models:
- `EVO_OPTIMIZER_MODEL=openrouter/anthropic/claude-3-haiku`
- `EVO_EVAL_MODEL=openrouter/anthropic/claude-3-haiku`
- `EVO_MAX_TOKENS=2048`, `EVO_DATASET_SIZE=10`

Dry-run validate:
```bash
./evolve_agent.sh saksit --skill github-auth --dry-run
```

### Phase 4: Automated Evolution (GEPA Pipeline)

Run evolution by tier:

| Tier | Criteria | Iterations | Dataset |
|------|----------|------------|---------|
| 1 | Small + actionable (<100 lines) | 5 | 10 |
| 2 | Medium + high value (100-300 lines) | 5-8 | 15 |
| 3 | Large + complex (>300 lines) | 3-5 | 10 |
| 4 | Reference content (B2B SaaS) | Skip unless specific need | — |

For each skill:
```bash
python -m evolution.skills.evolve_skill --skill <name> --iterations 5 --dataset-size 10
```

Review PASS/FAIL output. For PASS: review diff, apply if meaningful.
For FAIL: inspect `evolved_FAILED.md`, consider manual patch.

### Phase 5: Manual Evolution & Consolidation

When automated evolution can't improve a skill (or isn't appropriate):

- **Merge duplicates** using `skill_manage(action='delete', absorbed_into='<umbrella>')`
- **Expand stubs** — skills under 50 lines need concrete checklists, pitfalls, examples
- **Fix broken references** — patch `related_skills`, file paths, command names
- **Reclassify** — move skills to correct category if mislabeled
- **Archive non-functional** — skills requiring unavailable hardware/OS get `absorbed_into=""` (prune)

### Phase 6: Reference Content Audit (Optional)

For large content libraries (B2B SaaS reference skills):
- Sample-check for quality and structure
- Identify merge candidates among overlapping topics
- Add consistent tags and category metadata for discoverability

### Phase 7: Sync, Deploy & Monitor

- Push changes to GitHub skills repo via `saksit-skills-repo-sync`
- **Batch-commit fixed files** via `GITHUB_COMMIT_MULTIPLE_FILES` (Composio GitHub API). Build an `upserts` array of `{path, content, encoding}` objects. All files land atomically in one commit. The `saksit-skills` repo uses flat paths (no category nesting — `social-media/saksit-x` becomes `saksit-x`). Confirmed working for 19 files in a single commit.
- For large batches (>50 files), split into multiple commits or use the workbench with `run_composio_tool` in parallel.
- Set up weekly quality cron job:

```bash
cronjob action=create schedule="0 9 * * 1" \
  prompt="Audit SakSit skills for structural issues, missing commands, and duplicates" \
  skills="hermes-skill-evolution,skill-library-maintenance"
```

## Verification Checklist

After any maintenance pass:
- [ ] Inventory report saved to `.hermes/plans/reports/`
- [ ] All skills pass structural validation (or issues documented)
- [ ] Evolution results saved per skill to `output/<skill>/<timestamp>/`
- [ ] Duplicates merged, stubs expanded, broken refs fixed
- [ ] Skills repo synced to GitHub
- [ ] Quality cron job running

## Common Pitfalls

- **Not every skill needs evolution** — reference content skills (B2B SaaS guides) are documentation, not workflows. Skip automated evolution for them unless there's a specific improvement request.
- **Constraint validation can reject GEPA output** even when quality improved. The evolved text may exceed size limits or restructure too aggressively. Check `evolved_FAILED.md` before giving up.
- **Always dry-run first** on an unfamiliar skill before spending API credits.
- **Zero budget constraint** — use OpenRouter free tier, small datasets (10 examples), few iterations (3-5). Never default to paid providers.
- **Path rot** — after workspace cleanups, evolution pipeline paths may break. Verify existence before running (see Phase 3).
- **Duplicate detection is noisy** — always manually confirm before deleting a skill.
- **Pyyaml not in system python** — the structural test script requires pyyaml. System python3 does not have it. Run with `uv run python3 scripts/structural-test.py` (not bare `python3`). First-time: `uv pip install pyyaml -q`.
- **Control characters from inline editing** - Shell-embedded Python can inject 0x01 SOH characters that break YAML frontmatter silently. Always write batch-editing scripts to a file first, never inline. After any inline batch edit, scan every file for control chars with `ord(c) < 32 and c not in '\n\r\t'` and strip them.
- **Linked-file regex false-positives** - prose like 'enforces the references/templates/scripts/assets subdir' can trigger false-positive ref checks. Also: glob patterns in text like `monitor-*.py` are not file references. The structural test script handles these automatically with a prose-context filter. **Updated 2026-07-29:** `is_prose_reference()` expanded with 7 new words (location, directory, path, here, see, under, listed) and a backtick-prefix check - text like `` `scripts/monitor-*.py` `` is now correctly skipped.
- **GitHub path structure** — the `saksit-skills` repo may use different path structures than the profile skills directory. Always check the actual repo structure before committing.
- **Skills live under category directories** — skills are at `skills/<category>/<skill-name>/SKILL.md`, not `skills/<skill-name>/SKILL.md`. When creating stub files or running remove operations, use `rglob()` not flat path patterns.
- **yaml.dump() corrupts complex frontmatter** — NEVER use `yaml.dump(fm, ...)` to rewrite an entire frontmatter block. It reformats multi-line descriptions, reorders keys, and can break inline `metadata.hermes` blocks. Instead, use targeted regex replacement on the frontmatter text for individual field changes. Only use yaml.safe_load() for READING, not for rewriting.
- **Related_skills has two formats** — related skills can appear as YAML list items (`- item`) OR as inline arrays (`related_skills: [item1, item2]`). Line-level removal (`re.sub(r"^  - item$", "", text)`) only catches the first format. For inline arrays, remove the item from the bracket-enclosed list with careful comma handling using `re.sub(r'(related_skills:\s*\[)([^\]]*?)\bbroken_name\b[\s,]*(.*?\])', r'\1\2\3', text)`.
- **Backup with cp -r not rsync** — rsync is not available on this system. Always use `cp -r path.bak/ path/` for directory backups. Verify with `find | wc -l` after restore.
- **Control characters from inline Python** — Shell-embedded Python (heredocs or `-c` strings) can inject control characters (0x01 SOH) when string escaping interacts badly with shell interpolation. This breaks YAML frontmatter silently — `yaml.safe_load()` raises "unacceptable character #x0001". Always write batch-editing scripts to a `.py` file first and run it from there. After any inline batch edit, re-read + verify every file — scan for chars with `ord(c) < 32 and c not in '\n\r\t'` and strip them.
- **Verify between fix phases** — after each bulk-fix operation, re-run the structural test before proceeding to the next fix type. A single monolithic script that does everything can corrupt YAML across files without warning (the `yaml.dump` pitfall is the main vector).
- **Beer-mode: act first, discuss later** — when Beer says "test all skills," "run test all skills," "fix them all," or a similar comprehensive action, just execute. Don't clarify scope, don't explain methodology, don't discuss trade-offs beforehand. Execute, report results, course-correct only if needed. Short command → full execution → correction only if wrong.
  - Variant: "keep do it" = continue executing the current action, don't pause for confirmation
  - Variant: "keep do do do" = full-speed continuous execution, don't wait between phases

## 6-Cycle Integration

| Cycle | Role in this framework |
|-------|----------------------|
| **Dream** | Choose the phase — what aspect of the library needs attention? |
| **Hope** | Plan the scope: which skills, what tests, expected outcome |
| **Care** | Execute the audit/test/evolve carefully, preserving state at each step |
| **Joy** | Package improvements — commit, sync, deploy |
| **Trust** | Verify each change: re-read the skill, test it loads, check for regressions |
| **Growth** | Save findings — add pitfalls to this umbrella, patch individual skills |
