---
name: SakSee-codebase-inspection
description: Inspect codebases w/ pygount: LOC, languages, ratios.
category: github
tags: [analysis, metrics, codebase]
---

# Codebase Inspection

Analyze codebase statistics using `pygount`.

## Quick Start

```bash
pip install pygount
pygount --format=summary /path/to/repo
```

## Output

| Language | Files | Code | Doc | Comment | Empty |
|----------|-------|------|-----|---------|-------|
| Python | 42 | 3500 | 200 | 150 | 300 |
| JavaScript | 15 | 1200 | 50 | 80 | 100 |

## Interpretation

- Code/Doc ratio < 5: well-documented
- Comment/Code ratio < 0.1: under-commented
- Empty/Total ratio > 0.2: sparse files

## Pitfalls

- Large repos may take time to scan
- Use `--suffix` to filter by language
