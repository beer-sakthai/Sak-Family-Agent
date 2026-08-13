---
on: weekly on monday

permissions:
  contents: read

checkout:
  repository: my-org/main-repo
  github-token: ${{ secrets.GH_AW_MAIN_REPO_TOKEN }}
  path: repo
  current: true

tools:
  github:
    github-token: ${{ secrets.GH_AW_MAIN_REPO_TOKEN }}
    toolsets: [repos, pull_requests]
  bash:
    - "npx:*"
    - "eslint:*"
    - "pip:*"

safe-outputs:
  github-token: ${{ secrets.GH_AW_MAIN_REPO_TOKEN }}
  create-issue:
    target-repo: "my-org/main-repo"
    title-prefix: "[quality] "
    labels: [code-quality, automation]
    max: 10

---

# Weekly Code Quality Review

The target repository has been checked out to `${{ github.workspace }}/repo`. Start by navigating there:

```
cd ${{ github.workspace }}/repo
```

## What to Analyze

### 1. JavaScript / TypeScript (if package.json exists)

```bash
npx eslint . --format json --max-warnings 0 2>/dev/null | head -200
```

Prioritize files with more than 5 ESLint errors, missing error-handling patterns such as empty `catch` blocks, and repeated unused imports or variables.

### 2. Complexity (any language)

Count lines per file and flag files over 500 lines as candidates for splitting:

```bash
find . -name "*.ts" -o -name "*.js" -o -name "*.py" | xargs wc -l | sort -rn | head -20
```

### 3. Python (if requirements.txt or pyproject.toml exists)

```bash
pip install flake8 --quiet && flake8 . --count --statistics 2>/dev/null | tail -20
```

Flag modules with more than 10 flake8 errors.

### 4. Repository signals

Check open Dependabot alerts on `my-org/main-repo`, then review the last 10 merged PRs for recurring patterns such as skipped tests or files that are repeatedly changed together.

## What to Create

Create **one issue per distinct finding category** rather than one per file. Each issue should name the affected files or modules with GitHub links, explain why the finding matters, suggest a concrete first step, and assign a severity: High for security or crash risks, Medium for maintainability, and Low for style. Skip findings with fewer than 3 instances to avoid noise.

## What to Skip

Do not create issues for style preferences without an established linter rule, files with a `// quality-exempt` comment, or test files such as `*.test.*`, `*.spec.*`, and `__tests__/`.