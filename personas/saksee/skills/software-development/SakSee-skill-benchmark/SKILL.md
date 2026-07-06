---
name: SakSee-skill-benchmark
description: Two-pass cold/hot file read benchmark for SKILL.md files.
category: software-development
tags: [benchmark, performance, page-cache]
---

# Skill Benchmark

Used when asked to "test all skills" or benchmark file load times.

## Steps

1. Find all SKILL.md files with `find`
2. Pass 1 — cold read with `read_file(limit=5)`
3. Pass 2 — hot re-read immediately
4. Compute averages and speedup ratio

See `software-development/benchmarking/SKILL.md` for full methodology.
