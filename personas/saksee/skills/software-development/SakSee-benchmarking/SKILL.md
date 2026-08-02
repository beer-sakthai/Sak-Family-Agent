---
name: SakSee-benchmarking
description: Two-pass cold/hot benchmarking methodology for measuring file I/O, API latency, tool performance, and system throughput.
category: software-development
tags: [benchmark, performance, measurement]
---

# Benchmarking Pattern

## Methodology

Two-pass benchmarking: first pass is cold (uncached), second is hot (cached).

The speedup ratio (cold/hot) reveals:
- < 2x: already cached or very small
- 2-5x: moderate I/O impact
- > 10x: heavy disk I/O avoided by page cache

## Steps

1. **Discover files** — find all relevant files
2. **Pass 1 (cold)** — read each file with minimal read (limit=5)
3. **Pass 2 (hot)** — re-read immediately
4. **Compare** — compute averages and ratios

## Pitfalls
- Use `limit=5` for minimal read overhead
- Sub-0.05ms readings are noise floor
- Batch path discovery once, don't call `find` in loops
