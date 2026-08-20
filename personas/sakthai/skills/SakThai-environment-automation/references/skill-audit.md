# Skill Library Audit — Systematic Maintenance

Trigger: user says "check your skills", "audit skills", "prune skills", or "improve your skills" without specifying which ones. Also useful as a periodic maintenance task (e.g. monthly).

## Phase 1: Inventory

```bash
# Count and list all installed skills
find ~/profiles/sakthai/skills/ -name 'SKILL.md' -maxdepth 3 | sort
```

Cross-reference with `skill_view` / `skills_list` output. Note any that don't appear in the list (broken frontmatter).

## Phase 2: Usage Analysis

Read `~/.hermes/skills/.usage.json` to see actual usage data:

| Field | Tells you |
|-------|-----------|
| `use_count` | How many times the skill was invoked. 0–1 = never/rarely used |
| `last_used_at` | When it was last active. >30 days ago = cold |
| `patch_count` | How many times it was improved. 0 = never updated |
| `pinned` | Protected from deletion but NOT from improvement |
| `created_by` | `"agent"` = local custom skill (safe to improve). `null` = bundled/hub |

**Keep if:** use_count ≥ 2, or last_used ≤ 14 days ago, or domain-relevant to Hugging Face / ML / agent development.

**Flag for pruning if:** use_count = 0–1 AND not domain-relevant (Apple, creative design, productivity tools for unconnected services, social media, audio generation, etc.).

## Phase 3: Frontmatter Validation

Every skill should pass this structural check:

```yaml
---
name: skill-name           # lowercase, hyphens, ≤64 chars. PRESENT
description: "..."         # one line, ≤1024 chars, starts with verb. PRESENT
version: X.Y.Z             # semver. RECOMMENDED
author: SakThai Agent      # or "Hermes Agent". RECOMMENDED
license: MIT               # RECOMMENDED
metadata:
  hermes:
    tags: [relevant, tags] # RECOMMENDED
    category: <category>   # RECOMMENDED
---
```

**Fix if missing:** version, author, license, metadata.hermes.tags, metadata.hermes.category.

Common problems:
- `title:` field instead of proper metadata (old format). Migrate to `metadata.hermes.*`.
- `category:` in root (old format). Migrate to `metadata.hermes.category`.
- Missing closing `---` before body.
- Leading whitespace before opening `---`.

## Phase 4: Content Review

Load each flagged skill with `skill_view(name)` and check:

1. **Stale content** — references to obsolete features, "TBD" or placeholder roles, out-of-date version numbers
2. **Missing triggers** — description doesn't start with a clear trigger class ("Use when...")
3. **No-op prose** — generic advice the agent would follow anyway without the skill
4. **Completeness** — each ordered step has a checkable completion criterion
5. **Information hierarchy** — bulky detail belongs in `references/*.md`, not SKILL.md body

## Phase 5: Domain Relevance Filter

Apply Beer's HF-first filter:

| Domain | Keep? | Notes |
|--------|-------|-------|
| Hugging Face / ML | ✅ | Core mission |
| Hermes agent framework | ✅ | Core platform |
| Communication | ✅ | Every turn |
| GitHub | ✅ | Repo access needed |
| Research | ✅ | Paper discovery |
| Software dev | ✅ | Daily tooling |
| Apple/macOS | ❌ | Linux workspace |
| Creative/design | ❌ | Not HF work |
| Unconnected SaaS | ❌ | No accounts |
| Media/audio | ❌ | Not scope |

## Phase 6: Batch Cleanup

For removal, use `rm -rf` on the skill directory — faster than individual `skill_manage(action='delete')` for bulk (10+). Then rebuild the manifest:

```bash
# Remove stale entries from .bundled_manifest
python3 -c "
import re
manifest = open('skills/.bundled_manifest').read()
kept = [e for e in manifest.split(chr(10)) if e and e.split(':')[0] not in removed_set]
open('skills/.bundled_manifest', 'w').write(chr(10).join(kept) + chr(10))
"

# Remove stale entries from .usage.json
python3 -c "
import json
u = json.load(open('skills/.usage.json'))
for s in removed_set: u.pop(s, None)
json.dump(u, open('skills/.usage.json', 'w'), indent=2)
"
```

After deletion, remove empty category directories with `rmdir`.

## Phase 7: Close the Loop

1. Verify final count: `find ~/profiles/sakthai/skills/ -name 'SKILL.md' | wc -l`
2. Save a memory entry with what was removed and why
3. If any skill had issues not yet fixed (missing frontmatter, stale content), file that as a separate task — don't leave partial fixes

## Pitfalls

- **skills_list is session-cached.** Deletions don't take effect until the next session. Verify via file system, not `skills_list`.
- **Don't remove `DESCRIPTION.md` files in category dirs.** They're metadata, not skills.
- **Bundled skills can't be deleted via `skill_manage(action='delete')`.** If a bundled skill is irrelevant, remove the directory manually — but check it's not needed by the Hermes framework first.
- **Never prune skills with `pinned: true`** in usage.json unless explicitly asked.
- **Session-specific transient errors** (missing binaries, 'command not found') are NOT skill problems — don't capture them as constraints.
- **Re-check usage.json after the session resets** — the file only tracks the current session's lifetime for some fields.
