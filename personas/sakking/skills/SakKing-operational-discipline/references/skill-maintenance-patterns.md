# Skill Maintenance Patterns

> Session-derived patterns from the 2026-07-26 skill improvement cycle.
> Covers the two-copy divergence pattern and skill quality audit checklist.

## Two-Copy Divergence

Hermes skills exist in **two copies** that independently diverge:

| Copy | Path | Purpose |
|------|------|---------|
| **Runtime** | `/opt/data/skills/<category>/<name>/` | Loaded every session, affects agent behavior |
| **Repo** | `Sak-Family-Agent/personas/sakking/skills/<name>/` | Version-controlled, canonical for PRs |

**Failure mode:** A fix applied to the repo copy is not reflected in the runtime
copy, and vice versa. The runtime copy is what Hermes actually loads, so it
takes priority for behavioral fixes.

**Corrective pattern:**
1. Identify which copy is stale (use `search_files` or `ls` to check both).
2. Apply the same patch to both copies.
3. Verify with `skill_view()` on the runtime copy (the repo copy doesn't affect
   in-session behavior).

## Skill Quality Audit Checklist

When scanning a skill for issues, check each of these dimensions:

### 1. Skill Name References
- [ ] Are referenced skill names cased correctly? (e.g. `SakKing-family-health-audit` not `sakking-family-health-audit`)
- [ ] Hermes skill names are CamelCase and case-sensitive. Wrong casing = not found.

### 2. Invocation Patterns
- [ ] Are skills referenced via `skill_view()`, not `terminal("run_skill ...")`?
- [ ] Hermes loads skills as markdown content — they are not shell-executable commands.

### 3. Version & Metadata
- [ ] Does the frontmatter have a `version:` field? If not, add one.
- [ ] Should the version be bumped? Material content changes warrant a patch bump.

### 4. Pitfalls
- [ ] Does the skill cover the key failure modes of its domain?
- [ ] Are there relevant cross-cutting pitfalls (two-copy divergence, name casing,
      load-vs-execute, directory≠process)?

### 5. Tool Names & Commands
- [ ] Are tool names correct for the current Hermes version? (e.g. `skill_view` not a legacy name)
- [ ] Are code examples tested/realistic rather than conceptual placeholders?

### 6. Procedure Actionability
- [ ] Can an agent follow the procedure step-by-step without guessing?
- [ ] Is the procedure specific enough, or does it rely on "conceptual" / "illustrative" stubs?

### 7. YAML Frontmatter Integrity

- [ ] No duplicate YAML keys (e.g. two `description:` entries — most parsers silently take the last one, wasting the first)?
- [ ] Frontmatter starts at byte 0 with `---` and closes with `\n---\n`?
- [ ] `name`, `version`, `description` all present? Name ≤ 64 chars, lowercase-hyphens?

### 8. Cross-Reference Validity

- [ ] Every skill name referenced in the body actually exists? (Check with `skill_view()` or `search_files` across the skills tree.)
- [ ] No references to non-existent tools, APIs, or reasoning frameworks?
- [ ] `related_skills` in frontmatter points to skills that resolve at load time?
- [ ] No stale inline code comments referencing old tools or deprecated import paths?

### 9. Content Completeness vs Stub Detection

- [ ] Does the skill have minimal viable content? (Sub-20-line stubs indicate incomplete migration — check if a full version lives at a different path.)
- [ ] No duplicate headings? (e.g. two `## Description` sections — one should be the frontmatter description, the other body content.)
- [ ] No empty or placeholder sections?

### 10. Both Copies

- [ ] Fix applied to **both** `/opt/data/skills/` (runtime) and
      `Sak-Family-Agent/personas/sakking/skills/` (repo)?

## Example Sessions

### 2026-07-26: Duplicate YAML keys & broken cross-references

`SakKing-execution-discipline/SKILL.md` had:
- **Duplicate `description` key** in YAML frontmatter. Line 4 had `description: "Sakking Execution Discipline"` followed immediately by `description: >` with the full block. PyYAML silently drops the first occurrence — the short string was never loaded.
- **Broken cross-reference** to `` `nine-step-reasoning` `` — this skill does not exist in any skills tree. Replaced with generic "structured reasoning skills".
- **Version** bumped from `1.0.0` to `1.1.0` to reflect the fixes.

Fix applied to both runtime copy (`/opt/data/skills/software-development/SakKing-execution-discipline/SKILL.md`) and repo copy (`Sak-Family-Agent/personas/sakking/skills/SakKing-execution-discipline/SKILL.md`). The runtime copy also had a mangled `name:` field from an over-aggressive patch — caught and corrected during the same cycle.

### 2026-07-23: Name casing & invocation pattern fixes

`SakKing-sak-family-agent/SKILL.md` had:
- All 5 skill name references used lowercase (`sakking-family-health-audit`)
- Procedure relied on `terminal("run_skill ...")` — a pattern that doesn't exist
- No version number bumped from 0.1.0 despite draft-quality content
- Missing key pitfalls: name casing, two-copy divergence, directory≠process

The fix applied both copies and was committed + pushed with `HERMES_PUSH_ALLOW=1`.
