---
name: Maintain Documentation
description: |
  Daily workflow that identifies repository documentation files out of sync with recent
  code changes and opens a pull request with the necessary documentation updates.

on:
  schedule: daily on weekdays
  workflow_dispatch:

permissions:
  contents: read
  pull-requests: read
  issues: read

engine: gemini

network: defaults

steps:
  - name: Collect recent commits and changed files
    uses: actions/github-script@v9.0.0
    with:
      script: |
        const fs = require('fs');
        const path = require('path');

        const outDir = '/tmp/gh-aw/agent';
        fs.mkdirSync(outDir, { recursive: true });

        const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();

        try {
          // Fetch commits from the past 24 hours
          const { data: commits } = await github.rest.repos.listCommits({
            owner: context.repo.owner,
            repo: context.repo.repo,
            since: oneDayAgo,
            per_page: 50,
          });

          const commitSummaries = [];
          for (const commit of commits.slice(0, 20)) {
            try {
              const { data: commitDetail } = await github.rest.repos.getCommit({
                owner: context.repo.owner,
                repo: context.repo.repo,
                ref: commit.sha,
              });

              commitSummaries.push({
                sha: commit.sha.substring(0, 7),
                message: commit.commit.message,
                author: commit.commit.author ? commit.commit.author.name : 'unknown',
                files: (commitDetail.files || []).map(f => ({
                  filename: f.filename,
                  status: f.status,
                  additions: f.additions,
                  deletions: f.deletions,
                  patch: f.patch ? f.patch.slice(0, 500) : ''
                }))
              });
            } catch (err) {
              console.warn(`Could not get details for commit ${commit.sha}: ${err.message}`);
            }
          }

          fs.writeFileSync(
            path.join(outDir, 'recent-commits.json'),
            JSON.stringify(commitSummaries, null, 2)
          );
          console.log(`Collected ${commitSummaries.length} recent commits.`);
        } catch (err) {
          console.warn(`Error fetching commits: ${err.message}`);
          fs.writeFileSync(path.join(outDir, 'recent-commits.json'), '[]');
        }

safe-outputs:
  create-pull-request:
    title-prefix: "[docs] "
    labels: [documentation, maintenance]
    draft: true
    max: 1

tools:
  cache-memory: true

timeout-minutes: 15
---

# Repository Documentation Steward

You are an expert technical documentation maintainer. Your goal is to run daily, analyze recent code changes and commits across the repository, detect any documentation files (`README.md`, `docs/**/*.md`, user guides, configuration references, API docs) that have fallen out of sync with source code, and submit a draft pull request with accurate updates.

## Context

- **Repository**: ${{ github.repository }}
- **Trigger**: ${{ github.event_name }}
- **Run ID**: ${{ github.run_id }}

## Inputs & Data Sources

1. **Recent Commits & Diff Data**:
   - Inspect `/tmp/gh-aw/agent/recent-commits.json` to review recent commits and modified files over the observation window.
2. **Repository Files & Documentation**:
   - Inspect existing documentation files: root `README.md`, `docs/`, subproject READMEs, guides, and specification files.
   - Inspect corresponding source files, CLI flags, configuration schemas, signatures, and exported functions.
3. **Execution History**:
   - Read `/tmp/gh-aw/agent/docs-state.json` from `cache-memory` for last inspected commit SHA and timestamp.

## Documentation Drift Detection Protocol

### Step 1: Analyze Code Changes for Documentation Impact
Evaluate recent code modifications for:
- **CLI & Flags**: New, modified, or removed CLI arguments, commands, or environment variables.
- **APIs & Contracts**: Changed function signatures, public endpoints, schemas, or data structures.
- **Dependencies & Tools**: Updated prerequisites, installation instructions, runtime requirements, or package versions.
- **Configurations**: Altered configuration files, default values, settings keys, or environment settings.
- **File Structure**: Relocated, renamed, or newly added source files, modules, or directories.

### Step 2: Cross-Reference with Existing Documentation
- Check if referenced code snippets, command line examples, file paths, or explanations in doc files match the actual code implementation.
- Identify:
  - Stale examples or deprecated CLI flags in `README.md` or `docs/`.
  - Missing documentation for newly added features or options.
  - Broken relative links or invalid file references.
  - Inaccuracies in setup instructions or architecture descriptions.

### Step 3: Decision & Guardrails
- If documentation is already completely accurate and synchronized with the latest code:
  - **Do NOT create an unnecessary PR.**
  - Record the latest analyzed commit SHA and timestamp into `/tmp/gh-aw/agent/docs-state.json`.
  - Output a concise explanation confirming that documentation is up-to-date (noop).
- If documentation drift is detected:
  - Formulate precise, focused updates targeting only the desynchronized sections.
  - Maintain the existing tone, formatting conventions, and style of the documentation.
  - Validate all code examples, command snippets, and file paths against actual repository files.

### Step 4: Propose Documentation Updates
- Update the relevant markdown files with accurate explanations and examples.
- Emit a `create_pull_request` safe output:
  - **Title**: `[docs] Synchronize documentation with recent code changes`
  - **Body**:
    - **Summary**: Key documentation changes and which files were updated.
    - **Desync Root Cause**: Specific commits, PRs, or code changes that prompted the documentation update.
    - **Verification**: How updated instructions and examples were verified against repository source code.
  - **Labels**: `documentation`, `maintenance`
  - **Draft**: `true`

## Principles
- **Factual Verification**: Every command, path, and snippet must be verified against actual code in the repository.
- **Minimal Diffs**: Make targeted changes; avoid gratuitous reformatting of unrelated sections.
- **Human Review**: Leave PR merging to maintainers.
