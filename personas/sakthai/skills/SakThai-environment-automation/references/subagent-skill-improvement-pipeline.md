# Subagent Skill Improvement Pipeline

Batch-improve groups of skills in parallel using `delegate_task`.

## When to use

- You need to improve multiple skills with similar structure (HF courses, GitHub tools, etc.)
- Each skill needs independent content enrichment (code examples, tables, troubleshooting)
- Manual editing one-by-one would take too many tool calls

## Workflow

1. **Audit first** — identify which skills need improvement and what's missing (versions, content gaps, broken refs)
2. **Group by similarity** — batch skills that need the same type of improvement:
   - Thin course/reference skills (same structure upgrade)
   - Skills missing frontmatter fields (batch YAML operations)
   - Skills needing code examples (add snippets per topic)
3. **Craft a precise goal per subagent** — include:
   - Exact repo path
   - What to NOT change (naming, author, structure)
   - What to add (specific sections, tables, code examples)
   - Version target after improvement
   - File modification method (patch or write_file)
4. **Dispatch in parallel** — up to 3 subagents concurrently
5. **After completion, check for stale-path trap** — if the repo had recent git renames, verify subagents wrote to the correct paths (not old stale ones)

## Pitfalls

- **Stale-path trap**: After `git mv` renames, old paths still exist in the working tree and are NOT tracked. Subagents may discover and write to them. Always run `git clean -fd` before dispatching, or direct subagents to use `skills/SakThai-*` paths explicitly.
- **Author overwrite**: Subagents preserving original author (`author: Hermes`) may overwrite a previous standardisation pass. Always re-check and fix author after improvement.
- **Reference files may be lost**: If improving skills that were moved, ensure subagents copy/update any `references/` files alongside SKILL.md.

## Verification after improvement

```bash
# Check versions were bumped
grep "^version:" skills/*/SKILL.md | grep "0\." | wc -l

# Check no stale old paths got the content instead
find . -path '*/mlops/*' -name SKILL.md 2>/dev/null | wc -l
# Should be 0 after cleanup

# Verify author still SakThai
grep -rL "^author:.*SakThai" skills/ --include=SKILL.md
# Should be empty
```

## Real example (2026-07-23)

Two subagents improved 14 HF skills (7 each) from 0.x to 1.0.0:
- Batch 1: hf-agents-course, hf-computer-vision-course, hf-deep-rl-course, hf-learn-portal, hf-llm-course, hf-ml-games, hf-inference-providers
- Batch 2: hf-audio-course, hf-cookbook, hf-diffusion-course, hf-ml-3d, hf-robotics-course, hf-smol-course, hf-context-engineering

Each skill grew 2-4x in content. The stale-path trap caught one batch — improvements copied from old paths to new. Lessons captured in this reference.
