# Skill Quality Assessment — 3-Level Testing Protocol

A reusable framework for assessing skill quality at three depth levels. Use after creating/improving skills, before committing to GitHub, or when Beer asks "test skills."

## The 3 Levels

### Level 1 — LOW (Existence & Frontmatter)
*Checks the skill loads and has basic metadata.*

| Check | What to look for |
|-------|-----------------|
| `name:` | Present in YAML frontmatter |
| `author:` | Present, should say `SakThai` |
| `version:` | Present, semantic version |
| `license:` | Present, should say `MIT` |
| `description:` | Present, clear one-liner |
| File exists | `skill_view(name)` succeeds |

**Command:**
```bash
# Quick frontmatter audit
for f in $(find skills/ -name SKILL.md | sort); do
  name=$(grep "^name:" "$f" | sed 's/name: *//')
  auth=$(grep "^author:" "$f" | head -1 | sed 's/author: *//')
  ver=$(grep "^version:" "$f" | head -1 | sed 's/version: *//')
  lic=$(grep "^license:" "$f" | head -1 | sed 's/license: *//')
  echo "$([ -n "$auth" ] && [ -n "$ver" ] && echo "✅" || echo "❌") $name | auth=$auth ver=$ver license=$lic"
done
```

### Level 2 — MIDDLE (Section Coverage)
*Checks the skill has the standard section framework.*

Score 0-5, one point per section present:

| Section | body contains |
|---------|--------------|
| When to Use | "when to use" (case-insensitive) |
| Prerequisites | "prerequisites" (case-insensitive) |
| Pitfalls | "pitfall" (case-insensitive) |
| Verification | "verification" (case-insensitive) |
| Code examples | at least 2 ` ``` ` fences |

**Target:** 5/5 for mature skills, ≥3/5 for draft skills.

**Command:**
```bash
for f in $(find skills/ -name SKILL.md | sort); do
  body=$(cat "$f"); s=0
  echo "$body" | grep -qi "when to use" && s=$((s+1))
  echo "$body" | grep -qi "prerequisites" && s=$((s+1))
  echo "$body" | grep -qi "pitfall" && s=$((s+1))
  echo "$body" | grep -qi "verification" && s=$((s+1))
  [ "$(echo "$body" | grep -c '```')" -ge 2 ] && s=$((s+1))
  echo "$name: $s/5"
done
```

### Level 3 — HIGH (Content Richness)
*Checks depth, completeness, and supporting files.*

Score 0-4, one point per criterion:

| Criterion | Threshold |
|-----------|-----------|
| Length | >150 lines |
| Word count | >500 words |
| Code blocks | ≥4 ` ``` ` fences (at least 2 distinct code examples) |
| References | `references/` directory exists with ≥1 file |

**Target:** ≥3/4 for production skills, ≥2/4 for utility skills.

## When to run

- **After improving a skill** — run Level 1 (quick check)
- **Before committing to GitHub** — run Level 1+2
- **When Beer says "test skills"** — run all 3 levels

## Interpretation

| Score range | Meaning | Action |
|-------------|---------|--------|
| **4-5/5** | Gold standard | Ship it |
| **3/5** | Functional | Consider enriching weak areas |
| **1-2/5** | Thin | Add missing sections next cycle |
| **0/5** | Skeleton | Needs full rewrite |

## Related

- `references/skill-audit.md` — for pruning/usage audit (different purpose)
- `environment-automation/SKILL.md` — machine facts and conventions
