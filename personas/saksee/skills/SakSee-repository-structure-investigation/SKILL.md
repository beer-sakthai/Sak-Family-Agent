---
name: SakSee-repository-structure-investigation
description: Investigate complex repository structures, especially when processes may be running
  from integrated components rather than standalone repositories.
...
---

# Repository Structure Investigation

Investigate complex repository structures, especially when processes may be running from integrated components rather than standalone repositories. This skill covers techniques for understanding how repositories are organized and how to identify the actual location of running processes.

## When to Use

- When investigating processes that may be running from components of larger repositories
- When expected repository locations don't match actual process locations
- When trying to understand complex monorepo or integrated repository structures
- When processes are running from unexpected paths

## Prerequisites

- Basic understanding of Git and repository structures
- Familiarity with Unix/Linux file system navigation
- Knowledge of process investigation techniques

## Quick Reference

| Command | Action |
|---------|--------|
| `find . -type d -name "*sakthai*" 2>/dev/null` | Find directories matching a pattern |
| `ls -la .claude/skills/ | grep sakthai` | Check for skill directories |
| `git remote -v` | Verify repository origin |
| `grep -r "sakthai-agent-v2" . --exclude-dir=.git` | Search for references to specific repositories |

## Procedure

### 1. Initial Investigation

When a process is running from an unexpected location:

```bash
# Check for the process
ps aux | grep <process_name>

# Look for directories matching the expected name
find /opt/data -type d -name "*sakthai*" 2>/dev/null

# Check skill directories
ls -la /opt/data/Sak-Family-Agent/.claude/skills/ | grep sakthai
```

### 2. Repository Structure Analysis

Understand how repositories are organized:

```bash
# Check if it's a component of a larger repository
cd /path/to/suspected/location
ls -la
git remote -v

# Look for skill or integration directories
find . -name ".claude" -type d
find . -name "skills" -type d

# Search for references to the expected repository name
grep -r "sakthai-agent-v2" . --exclude-dir=.git
```

### 3. Component Integration Patterns

Look for signs that a tool is integrated rather than standalone:

```bash
# Check for package structure within a larger repo
ls -la personas/*/sakthai/
ls -la library/*/sakthai-*/

# Look for skill directories that might contain drivers
ls -la .claude/skills/*/run-*/

# Check documentation for integration information
find . -name "*.md" -exec grep -l "integrated\|component\|part of" {} \;
```

### 4. Verification

Confirm the actual structure and location:

```bash
# Verify the actual package location
ls -la /opt/data/Sak-Family-Agent/personas/sakthai/sakthai/

# Check the skill that drives the component
ls -la /opt/data/Sak-Family-Agent/.claude/skills/run-sakthai-agent-v2/

# Verify setup instructions
cat /opt/data/Sak-Family-Agent/.claude/skills/run-sakthai-agent-v2/SKILL.md
```

## Pitfalls

- **Assuming standalone repositories**: Not all tools are in standalone repositories; many are components of larger systems
- **Repository consolidation**: Recent changes may have moved tools from separate repositories into integrated ones
- **Outdated documentation**: Documentation may reference old repository locations
- **Skill-based integration**: Tools may be accessed through skills rather than direct repository clones
- **Path assumptions**: Expected paths may not match actual installation locations
- **Git status ahead of remote**: Repositories may have local commits that haven't been pushed to the remote yet, which can cause confusion when checking status
- **Modified files without commit**: Local modifications to files (like dashboard updates) may exist without being committed, requiring git diff to see actual changes

## Verification

To verify that you've correctly identified a repository structure:

1. Confirm the actual location of the package code
2. Check skill directories for integration drivers
3. Verify setup instructions match the actual location
4. Confirm that the process is running from the identified location
5. Check git remote information to confirm repository origin

See `references/repository-structure-examples.md` for specific examples of complex repository investigations.
See `references/food-penguin-limited-investigation.md` for a detailed investigation of a complex dashboard repository.
See `references/sakthai-xyz-website-investigation.md` for a detailed investigation of website deployment issues and repository status checks.
