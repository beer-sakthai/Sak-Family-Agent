---
name: SakSee-research-diary-documentation
description: "Create and save research diaries to GitHub for documentation safety."
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Documentation, Research, Diary, GitHub, Git]
---

# Research Diary Documentation

This skill helps document project research and save it to GitHub for safety and version control. It creates structured diary entries from research findings and ensures they are properly committed and pushed to a GitHub repository.

## When to Use
- After completing research tasks that need documentation
- When consolidating findings from multiple sources
- Before ending a research session to capture key insights
- When creating project diaries for future reference
- To ensure research findings are safely stored in version control

## Prerequisites
- Git repository initialized and configured
- GitHub authentication set up (HTTPS token or SSH key)
- Git identity configured (user.name and user.email)
- Write access to the target repository
- Directory structure with a `diaries/` folder

## How to Run
Invoke through the `terminal` tool with appropriate git commands, or use `write_file` to create diary entries in the appropriate directory structure.

## Quick Reference
- `diaries/` - Main directory for all diary entries
- `diaries/{agent}/` - Agent-specific diary folders
- `git add .` - Stage all changes
- `git commit -m "message"` - Commit changes
- `git push origin main` - Push to GitHub
- `scripts/create-diary-entry.sh {agent} {topic}` - Create new diary entry

## Procedure
1. Create a new diary entry file using the helper script:
   - Run `scripts/create-diary-entry.sh {agent} {topic}` to create a structured diary entry
   - Or use `write_file` to create markdown files in `diaries/{agent}/` with the template

2. Fill in the diary entry with research findings:
   - Include date, research topic, findings, and conclusions
   - Add sources consulted and detailed analysis
   - Document next steps and action items

3. Review and finalize the diary entry:
   - Ensure all relevant information is included
   - Check links and references are correct
   - Verify the structure follows the template

4. Add and commit the diary entry:
   - Use `terminal` with `git add diaries/{agent}/{filename}.md`
   - Commit with a descriptive message: `git commit -m "docs: add research diary for {topic}"`

5. Push to GitHub for safety:
   - Use `terminal` with `git push origin main` or appropriate branch
   - Verify the push was successful

6. Update any relevant documentation or README files:
   - Link to new diary entries in appropriate indexes
   - Update project documentation with key findings

## Pitfalls
- Forgetting to commit and push diary entries, leading to data loss
- Creating diary entries in wrong directories or with inconsistent naming
- Not including enough context in diary entries for future reference
- Overwriting existing diary entries accidentally
- Not setting up proper Git authentication before attempting to push
- Creating overly verbose entries that are hard to scan later
- Script failing due to lack of permissions or missing directories
- Not customizing the template content after using the script

## Verification
Run `git status` to check if diary files are staged, then `git log --oneline -5` to verify the commit was created, and finally `git push` to ensure changes are saved to GitHub.