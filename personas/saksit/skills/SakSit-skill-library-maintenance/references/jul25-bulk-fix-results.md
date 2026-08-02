# Jul 25-26 Bulk Fix Results

Full structural test and fix pass across all 205 skills (SakSit profile).

## Before

| Issue | Count |
|-------|-------|
| Descriptions >60 chars | 117 |
| Missing tags | 52 |
| Broken related_skills | 21 |
| Name mismatch (fm vs dir) | 4 |
| Missing linked file stubs | 5 |
| False positives (prose artifacts) | 2 |
| **Total** | **201** |

## Fix Workflow (validated)

1. `cp -r skills skills.bak` — backup first
2. Generate `SHORT_DESC` dict with ≤60-char descriptions for all 117 long ones
3. Generate `TAGS_MAP` dict with inferred tags for 52 tagless skills
4. Run Python script: `yaml.safe_load` → modify dict → `yaml.dump` per file
5. Fix name mismatches: 4 skills (lm-eval-harness, vllm, audiocraft, segment-anything)
6. Fix related_skills: handle both `- item` and `[item1, item2]` formats separately
7. Create stub files at correct category-nested paths (`skills/<category>/<name>/...`)
8. Re-verify — if YAML errors found, restore from backup and re-apply with targeted fixes
9. Sync to GitHub via `saksit-skills-repo` git commit

## Key Learnings

- **Restore from backup** when YAML corruption occurs. `cp -r skills.bak skills` reverses damage.
- **Test one fix type at a time.** Running desc + tags + name + related in one monolithic script caused YAML corruption cascade. The bulk-fix.py `--fix-X` flags allow phase-by-phase application.
- **Category nesting.** Skills live under `skills/<category>/<skill-name>/SKILL.md`, not flat. Stub creation and rglob must account for this.
- **Inline YAML arrays.** `related_skills: [item1, item2]` is the format used by metadata.hermes blocks. Line-level removal doesn't work — must edit the inline bracket list.

## After

Zero issues. All 205 skills clean.
