---
name: Maintain AGENTS.md
description: |
  Weekly maintenance workflow that reviews merged pull requests and updated source files
  since the last run, then opens a pull request to keep AGENTS.md accurate and current.

on:
  schedule: weekly on monday
  workflow_dispatch:

permissions:
  contents: read
  pull-requests: read
  issues: read

engine: gemini

network: defaults

steps:
  - name: Collect merged PRs and recent repository changes
    uses: actions/github-script@v9.0.0
    with:
      script: |
        const fs = require('fs');
        const path = require('path');

        const outDir = '/tmp/gh-aw/agent';
        fs.mkdirSync(outDir, { recursive: true });

        const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
        
        try {
          const { data: pullRequests } = await github.rest.pulls.list({
            owner: context.repo.owner,
            repo: context.repo.repo,
            state: 'closed',
            sort: 'updated',
            direction: 'desc',
            per_page: 30,
          });

          const mergedRecent = pullRequests
            .filter(pr => pr.merged_at && pr.merged_at >= sevenDaysAgo)
            .map(pr => ({
              number: pr.number,
              title: pr.title,
              body: pr.body ? pr.body.slice(0, 1000) : '',
              merged_at: pr.merged_at,
              author: pr.user ? pr.user.login : 'unknown',
              html_url: pr.html_url
            }));

          fs.writeFileSync(
            path.join(outDir, 'merged-pull-requests.json'),
            JSON.stringify(mergedRecent, null, 2)
          );
          console.log(`Found ${mergedRecent.length} PRs merged in the last 7 days.`);
        } catch (err) {
          console.warn(`Error fetching PRs: ${err.message}`);
          fs.writeFileSync(path.join(outDir, 'merged-pull-requests.json'), '[]');
        }

safe-outputs:
  create-pull-request:
    title-prefix: "[agents-md] "
    labels: [documentation, maintenance]
    draft: true
    max: 1

tools:
  cache-memory: true

timeout-minutes: 15
---

# Maintain AGENTS.md

You are an expert repository documentation and agent maintainer. Your goal is to review recent repository activity (merged pull requests and updated source files since the last run or past 7 days) and ensure that `AGENTS.md` remains accurate, comprehensive, and up-to-date.

## Context

- **Repository**: ${{ github.repository }}
- **Trigger**: ${{ github.event_name }}
- **Run ID**: ${{ github.run_id }}

## Inputs & Data Sources

1. **Pre-fetched Merged Pull Requests**:
   - Read `/tmp/gh-aw/agent/merged-pull-requests.json` for pull requests merged in the last 7 days.
2. **Current `AGENTS.md`**:
   - Read the existing `AGENTS.md` at the repository root (or subpackages/subdirectories if a monorepo).
3. **Repository Source & Configuration**:
   - Inspect recent git commits, changed source files, project structure, package manifests (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, etc.), tool definitions, scripts, workflows, and guidelines.
4. **Cache & Execution History**:
   - Read `/tmp/gh-aw/agent/last-run.json` from `cache-memory` to identify previous run timestamps or commit SHAs, if available.

## Evaluation & Maintenance Protocol

### Step 1: Analyze Merged PRs & Recent Commits
- Review titles, descriptions, and file changes of all pull requests merged since the last run.
- Identify:
  - New tools, commands, scripts, or CLI flags added.
  - New subpackages, modules, directories, or architectural refactorings.
  - Changes to development workflows, testing commands, linters, typecheckers, or build systems.
  - New conventions, rules, coding style requirements, or guardrails.
  - Renamed, moved, or deprecated components and files.

### Step 2: Survey Current `AGENTS.md`
- Check whether the current `AGENTS.md` accurately reflects the latest repository reality:
  - Is the project structure section up-to-date?
  - Are build, test, lint, and run commands accurate?
  - Are coding conventions and style rules aligned with recent practices?
  - Are agent-specific instructions, protocols, or persona guidelines intact and relevant?
  - Are all referenced file paths valid and existing?

### Step 3: Determine Required Updates
- If NO meaningful changes occurred that affect agent guidelines, project structure, commands, or developer instructions:
  - **Do NOT open an unnecessary pull request.**
  - Conclude with a clear explanation of why no changes were required (noop).
  - Update `/tmp/gh-aw/agent/last-run.json` with the current run timestamp and commit SHA.
- If updates ARE needed:
  - Formulate precise, minimal, and high-value edits to `AGENTS.md`.
  - Preserve all existing accurate sections, tone, and formatting conventions.
  - Ensure updated commands, file paths, and guidelines are tested and verified against actual repository contents.

### Step 4: Propose Changes via Pull Request
- Create or update `AGENTS.md` with the necessary revisions.
- Emit a `create_pull_request` safe output:
  - **Title**: `[agents-md] Update AGENTS.md with recent changes`
  - **Body**:
    - **Summary**: Concise bullet points explaining what was updated in `AGENTS.md`.
    - **Motivation / Merged PRs**: List of relevant merged pull requests or commits that triggered these documentation updates.
    - **Verification**: How changes were verified against current repository structure and files.
  - **Labels**: `documentation`, `maintenance`
  - **Draft**: `true`

## Guardrails & Principles
- **Accuracy First**: Never invent commands, scripts, or architecture that do not exist in the codebase.
- **Preserve Structure**: Respect existing formatting, headings, and rules established in `AGENTS.md`.
- **Quality over Quantity**: Do not produce noise or trivial stylistic edits if nothing functional changed.
- **No Self-Merging**: The pull request will be reviewed by human maintainers.
