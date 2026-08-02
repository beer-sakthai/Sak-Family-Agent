# Test-run notes, artifacts layout & rerun checklist

## Artifacts layout (with the bundled `playwright.config.ts`)
- `playwright-report/index.html` — HTML report (reporter `html`, `open: 'never'`).
- `test-results/` — per-failure screenshots, videos, and traces
  (`screenshot: only-on-failure`, `video`/`trace: retain-on-failure`).
- Deliver these to the user by path; in the sandbox they live under the project's
  working dir (e.g. `/tmp/<project>/playwright-report/index.html`).

## Recording a flow with codegen
On a host with a display you'd use `npx playwright codegen <url>`. The sandbox is
**headless / no display**, so write the spec by hand using `templates/demo.spec.ts`
as the starting point, or capture selectors by scripting
`page.locator(...).first()` probes and printing `innerText()`.

## Rerun checklist
1. Bootstrap done this session? (`npx playwright install --with-deps chromium`)
2. `playwright.config.ts` present in the project dir? (`cp` from `templates/`)
3. Spec files under `tests/*.spec.ts`.
4. Run: `npx playwright test --reporter=list,html`.
5. On failure, open `test-results/` for the screenshot/video/trace of the failing case.
6. View the trace with `npx playwright show-trace test-results/<...>/trace.zip` if needed.
