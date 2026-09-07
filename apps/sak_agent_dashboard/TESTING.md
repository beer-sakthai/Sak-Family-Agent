# Testing the Sak-Agent-Family Dashboard

> Replaces `TEST_INFRA.md` and `TEST_READY.md`, which described a Vitest 2 /
> Next 14 suite of "4 files, 28 tests" that had not matched the repository for
> some time, and asserted a pass rate that could not be reproduced.

## Running

```bash
npm ci
npm run lint      # eslint (flat config; `next lint` was removed in Next 16)
npm run build     # must precede the typecheck -- see below
npx tsc --noEmit
npm test          # vitest run
```

`.github/workflows/apps.yml` runs exactly this sequence, path-filtered to
`apps/**`.

**Build before typecheck.** `next-env.d.ts` imports `./.next/types/routes.d.ts`,
which only exists once a build has generated it, so a cold `tsc --noEmit` on a
clean checkout fails.

## What the suite covers

| File | Focus |
|---|---|
| `src/tests/fixtures.ts` | Builds a real `~/.sakthai`-shaped tree, including a real SQLite database |
| `src/tests/local-source.test.ts` | `LocalFsSource` against that tree — personas, metrics, sessions, memory, audit, workflows |
| `src/tests/routes.test.ts` | The actual route handlers, imported and called |
| `src/tests/source.test.ts` | Path resolution, the source-selection rule, query-param clamping |
| `src/tests/demo.test.ts` | The single demo dataset: determinism and coverage of all six personas |
| `src/tests/components.test.tsx` | Rendering against contract-shaped data |
| `src/tests/heatmap.test.tsx` | `buildHeatmap`/`longestStreak` against a pinned "today", plus what the calendar says in text |
| `src/tests/persona-drawer.test.tsx` | The share figures, and the zero-denominator cases behind them |

## Two things this suite deliberately does

**It uses real files, not mocks.** `fixtures.ts` writes an actual temp runtime
root and an actual SQLite database. That is not incidental: `src/lib/db.ts`
previously called CommonJS `require("better-sqlite3")` inside an ESM module,
which throws under Vitest and was swallowed into a demo-data fallback — so the
SQLite read path had never executed under test. Breaking `db.ts` now turns
about a dozen tests red.

**It has no escape hatch.** The previous `api.test.ts` and `components.test.tsx`
wrapped every assertion in:

```ts
async function getApiRouteModule(routePath: string) {
  try { return await import(`../app/api/${routePath}/route`); } catch { return null; }
}
// ...
if (mod) { /* assert on the route */ } else { /* assert on an inline literal */ }
```

so the suite reported green when the import failed — testing its own fixtures
rather than the application. Route modules are now imported directly, and an
import failure is a test failure.

`integration.test.ts` also imported its types **from `api.test.ts`**, which
pulled that file's `describe` blocks into a second module graph and ran twelve
tests twice. Types now come from `src/lib/contracts.generated.ts`.

## The generated contract

`src/lib/contracts.generated.ts` is produced from
`personas/sakthai/sakthai/web/contracts.py` by `scripts/gen_dashboard_types.py`
(`make contract-types`). Do not edit it by hand; CI regenerates it and fails on
a diff, which is what keeps the Python and TypeScript views of the same payloads
from drifting.
