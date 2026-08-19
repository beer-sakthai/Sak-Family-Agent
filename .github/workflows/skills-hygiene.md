---
name: Skills Hygiene
emoji: "🧹"
description: |
  Weekly run of the repository's own skill validator across all six persona overlays and
  the shared and curated skill roots. `sakthai skills validate --naming` exists but nothing
  in CI runs it, so naming-convention and frontmatter regressions across the ~800 skill
  directories currently land unnoticed. This workflow runs it and reports what it finds.

on:
  schedule: weekly on wednesday
  workflow_dispatch:

permissions:
  contents: read
  issues: read

engine: gemini
strict: true

network:
  allowed:
    - defaults
    - python

steps:
  - name: Checkout repository
    uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
    with:
      persist-credentials: false

  - name: Set up Python
    uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97
    with:
      python-version: "3.12"

  - name: Install uv
    run: pipx install uv

  - name: Install the package
    run: uv sync --all-extras

  - name: Collect skill validation output
    run: |
      set +e
      mkdir -p /tmp/gh-aw/agent
      uv run sakthai skills validate --naming > /tmp/gh-aw/agent/skills-validate.txt 2>&1
      echo "exit_code=$?" >> /tmp/gh-aw/agent/skills-validate.txt
      uv run sakthai skills list > /tmp/gh-aw/agent/skills-list.txt 2>&1
      echo "--- collected ---"
      wc -l /tmp/gh-aw/agent/skills-validate.txt /tmp/gh-aw/agent/skills-list.txt

safe-outputs:
  create-issue:
    title-prefix: "[skills] "
    labels: [maintenance, automation]
    max: 1
    close-older-issues: true

tools:
  cache-memory: true
  bash:
    - "cat"
    - "find"
    - "ls"
    - "wc"

timeout-minutes: 20
---

# Skill Hygiene Audit

The repository ships roughly 800 skill directories across six persona overlays
(`personas/*/skills/`), the shared root (`personas/shared/skills/`), and the curated root
(`library/`). Two conventions govern them:

- **Naming** — `Sak-` prefix for shared skills, `Sak<Name>-` for per-persona skills,
  enforced by `sakthai skills validate --naming`.
- **Frontmatter** — `tags` and `related_skills` must sit under `metadata.sakthai`. A flat
  top-level `tags:` is silently ignored by the parser in `personas/sakthai/sakthai/skills.py`,
  so a skill can look tagged and not be.

Nothing in CI runs the validator today. A step before this prompt has already run it for
you and captured the output.

## What to do

1. Read `/tmp/gh-aw/agent/skills-validate.txt`. The last line records the validator's exit
   code. Treat a non-zero exit as findings to report, not as a workflow failure.
2. Read `/tmp/gh-aw/agent/skills-list.txt` for the discovered inventory, and reconcile the
   per-root counts against what `CLAUDE.md` documents (SakThai 299, SakSee 182, SakJules
   180, SakKing 106, SakSit 43, SakTan 13, shared 3, curated 31). A count that has drifted
   from the documented figure is itself worth reporting — either skills moved or the docs
   went stale.
3. For each naming violation the validator reports, name the offending directory and the
   prefix it should carry. Do not rename anything.
4. Spot-check frontmatter on any skill the validator flags: read its `SKILL.md` and say
   whether `tags`/`related_skills` are correctly nested under `metadata.sakthai` or sitting
   at the top level where the parser ignores them.

`personas/sakthai/skills/.archive/` holds intentionally retired skills and is excluded from
discovery — never report anything under it as a violation.

## Reporting

Open an issue **only if** the validator reported violations, or a root's skill count has
drifted from the documented figure. A clean run should create nothing and simply say so in
the run log.

When you do open one:

- Title: `Skill hygiene — <n> finding(s)`
- Group findings by root, and give each a path plus the one-line fix.
- Quote the validator's own output for each violation rather than restating it in your own
  words — the exact string is what someone will grep for.
- Include the run URL:
  ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
