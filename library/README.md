# library/

A curated library of **SakThai's own skills**, grouped by category. Each
category folder has a `DESCRIPTION.md` and one or more `<skill>/SKILL.md` files.

`sakthai skills` discovers everything here and under the repo's top-level
`skills/` directory:

```bash
sakthai skills list                  # grouped catalog (skills/ + library/)
sakthai skills list --source library # just this library
sakthai skills show sakthai-memory-recall
sakthai skills validate              # frontmatter check, exits 1 on errors
```

## Layout

```
library/
├── agent/          DESCRIPTION.md + sakthai-agent-* skills
├── devops/         DESCRIPTION.md + sakthai-devops-* skills
├── learning/       DESCRIPTION.md + sakthai-learning-* skills
├── llm/            DESCRIPTION.md + sakthai-llm-* skills
├── memory/         DESCRIPTION.md + sakthai-memory-* skills
├── observability/  DESCRIPTION.md + sakthai-observability-* skills
└── safety/         DESCRIPTION.md + sakthai-safety-* skills
```

## Note on third-party skills

The original project's `library/` also vendored ~90 third-party skills (each
under its own upstream license). Those are **not** copied here — only SakThai's
own skills live in this repo. Pull external skills in yourself with
`sakthai extensions install <git-url>`, which keeps them in `~/.sakthai` under
their original licenses.
