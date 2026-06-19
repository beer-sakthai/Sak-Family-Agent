# Playwright Visual Testing

Cover image-snapshot regression and responsive viewport checks together; avoids splitting the same visual workflow across skills.

## When to use

Use this skill for pixel/image regression and for viewport/responsive behavior that changes rendering.

## Steps

1. Set test-scoped base viewport; keep image compare masks minimal.
2. Capture deterministic screenshots:
   - disable animations when relevant.
   - wait for networkidle or a stable selector.
   - avoid baselines generated under explicit animation runs.
3. Record failed baselines into `tests/visual/failures/` with deterministic naming.
4. For viewport testing, assert breakpoint-driven visibility or order, not only percent similarity.

## Pitfalls

- CI environments must use the same browser pixel density as local runs; mismatch causes noisy diffs.
- full-page `screenshot` is fragile; prefer element-level or defined clip regions.
- font loading or lazy assets cause transient diffs—wait for `load`/`networkidle`.
