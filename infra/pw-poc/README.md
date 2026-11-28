# pw-poc

Playwright keyboard-focus / tab-order accessibility probe against a target page.
`test-keyboard.js` presses Tab 25× on `https://example.com`, records the focused
element after each press, reports the active element's outline (focus-visibility),
and saves a screenshot. Used by SakSee to validate keyboard accessibility and tab order in
headless browser workflows (e.g., automated QA and visual verification pipelines).

Dependencies are kept updated via daily Dependabot scanning (`interval: "daily"`).

## Architecture

```mermaid
flowchart LR
    Runner["Node 22+ Test Runner"] --> Playwright["Playwright Headless Chromium"]
    Playwright --> Probe["Tab-Order & Focus Visibility Probe (25x Tab)"]
    Probe --> TargetPage["Target Web Page"]
    Probe --> Artifacts["Artifacts: TAB_ORDER_JSON, FOCUS_VISIBILITY, last-focus.png"]
    Artifacts --> SakSee["SakSee Accessibility Validation"]
```

## Run (host or any Node 22+ box)
```bash
npm i
npx playwright install --with-deps chromium   # first run only
node test-keyboard.js
```

Outputs `TAB_ORDER_JSON`, `FOCUS_VISIBILITY`, and `last-focus.png`.

## Run inside a bot's Modal sandbox
The sandbox can't see the host filesystem, so clone this repo first:
```bash
cd /tmp && git clone <this-repo-url> pw-poc && cd pw-poc
npm i && npx playwright install --with-deps chromium
node test-keyboard.js
```
