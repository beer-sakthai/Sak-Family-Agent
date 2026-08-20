# Bulk Fix Session — July 25, 2026

Full structural test + fix of 203 skills.

## Baseline

| Issue | Count |
|-------|-------|
| Description >60 chars | 117 |
| Missing tags | 52 |
| Broken related_skills | 21 |
| Name/dir mismatch | 4 |
| Missing linked files | 5 |
| False positives filtered | 2 |

## Key Lessons

**Description length:** System-prompt index truncates at 60 chars. Over 60 = invisible. Lead with trigger class in first 60 chars. Example: "Tiered ABM playbook for B2B SaaS in 2026." (41c) not a 382-char paragraph.

**Never yaml.dump() to rewrite frontmatter.** It corrupts multi-line scalars, reorders keys, breaks metadata blocks. Always use targeted regex replacement on individual frontmatter fields.

**Related_skills has two formats:**
- List: `related_skills:\n  - item` → remove with `re.sub(r'^\s*-\s*broken_name\s*$', '', text, flags=re.MULTILINE)`
- Inline array: `related_skills: [item1, item2]` → remove with `re.sub` on the bracket content including `\bbroken_name\b`

**Skills nest under category dirs:** `skills/<category>/<skill-name>/SKILL.md` not `skills/<skill-name>/`. Stub creation at flat path fails silently.

**Verify between fix phases:** After each bulk-fix operation, re-run structural test before proceeding to next fix type. One monolithic script corrupts YAML across files without warning.

## Results: 201 issues → 0
