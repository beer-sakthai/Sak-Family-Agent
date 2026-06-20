---\nname: playwright-performance\ncategory: testing\ndescription: Automate budget validation and core web vitals measurement in Playwright; combines before/after budget checks with reproducible vitals collection.\nversion: 1.0.0\n---\n\n# Playwright Performance\n\nAutomate budget validation and core web vitals measurement in Playwright; combines before/after budget checks with reproducible vitals collection.

## When to use

Use this skill when a change risks render/bundle/network cost or when validating Core Web Vitals in CI.

## Steps

1. Create a baseline before changes; store budget values in `perf/budget.json` keyed by route.
2. Measure per route:
   - request count and transfer size.
   - main-thread and layout timing.
   - LCP, CLS, FID/INP where supported.
3. Fail CI when the delta exceeds allowed percent or absolute budget.
4. Use `expect(locator)` to wait for meaningful paint before measuring vitals.

## Pitfalls

- local vs CI environments diverge in memory/CPU; prefer relative budgets or expected ranges, not single numbers.
- avoid warm-cache vs cold-cache comparison without an explicit policy.
- Chrome headless on Linux needs a proper container display for reliable paint timing.
