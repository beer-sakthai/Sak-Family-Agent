---
name: sakthai-playwright-shadow-dom
category: dogfood
description: Use Playwright locators with `:scope`, `locator('css=...)` targeting
  `shadowRoot`, and `evaluate()` to interact with, assert on, and extract state fromShadow
  DOM, closed Shadow DOM workarounds, and shadow-piercing strategies for LWC/SLDS/Custom
  Elements in headless browser flows.
version: 1.0.0
platforms:
- linux
- macos
- windows
metadata:
  sakthai:
    tags:
    - hermes
    - dogfood
    related_skills: []
    source: hermes:playwright-shadow-dom
---

# Playwright Shadow DOM Automation

## Problem

Custom elements and modern component libraries (LWC, SLDS, Shoelace, Ionic, Material Web) increasingly hide interactive state inside Shadow DOM roots. Standard locators stop at the host element, so scripts blind to shadow boundaries fail open-or-die assertions and interactions. This skill documents Playwright-specific shadow-DOM strategies that are not represented elsewhere in the catalog.

## When to Use

- A component library hides buttons, inputs, or text behind `shadowRoot`
- An accessibility audit or Dogfood QA depends on text/roles inside Shadow DOM
- Assertions against toast/icon/tooltip content fail because the DOM view ends at `<my-element>`
- You need to pump state into/out of a closed vs. open Shadow DOM tree

## Core Capabilities

### 1. Pierce Open Shadow Roots with Scoped Locators

Playwright’s locator engine can run against a shadow root via `evaluate()` or by `locator('css=>>>')` within a container that exposes the boundary. Prefer binding at the host and then targeting within the root.

```python
host = page.locator("my-element").first
# Open shadow root: evaluate exposes the scoped root to the outside
shadow_root = host.evaluate("el => el.shadowRoot")
text = host.evaluate("el => el.shadowRoot.querySelector('span').textContent")
assert "expected" in text
```

### 2. Use `evaluate()` for Read/Write in Closed or Nested Roots

For closed / non-local shadow boundaries, `evaluate()` is the reliable escape hatch. Pass functions that operate on `=== shadowRoot` literals and return serializable values.

```python
value = page.evaluate("""([el, sel]) => {
  const root = el.shadowRoot;
  return root.querySelector(sel).textContent;
}""", [host.element_handle(), "p.welcome"])
page.evaluate("""([el, sel, val]) => {
  el.shadowRoot.querySelector(sel).value = val;
}""", [host.element_handle(), "input#name"], "new value")
```

### 3. Prefer `:scope`-Style Queries When Possible

Targeting `:scope` inside a shadow root keeps selectors short and predictable.

```python
page.evaluate("""([el, sel]) => el.shadowRoot.querySelector(':scope ' + sel).textContent""",
              [host.element_handle(), ".status"])
```

` `:scope > .slot` avoids sloppy ancestor matches across slot boundaries.

### 4. Drill Through Composite Components

Multi-layer components (LWC `<lightning-card>`, `<my-composite>`) chain shadow roots. Drill with a small helper:

```python
def get_inner_text(page, base_locator, path):
    # path: list of selectors inside successive shadow roots
    return page.evaluate("""([el, steps]) => {
      let current = el;
      for (const sel of steps) {
        current = current.shadowRoot.querySelector(sel);
        if (!current) return null;
      }
      return current.textContent.trim();
    }""", [base_locator.element_handle(), path])
```

### 5. Assert Visible Accessibility Properties

When shadow DOM is the only rendering path, visibility assertions and role assertions need to account for the boundary. Wait on the host, then evaluate inside.

```python
host.wait_for(state="visible")
role = host.evaluate("el => el.shadowRoot.querySelector('.btn').getAttribute('role')")
assert role == "button"
```

### 6. Handle Slot Content for QA Coverage

When the app exposes DOM into a parent via `<slot>`, QA should validate both the host and projected content. `evaluate()` can rebuild a flattened view of text across boundaries.

```python
all_text = page.evaluate("el => {
  const txt = new Set();
  function walk(node) {
    if (node.nodeType === 3) txt.add(node.textContent.trim());
    else if (node.shadowRoot) walk(node.shadowRoot);
    [...node.children].forEach(walk);
  }
  walk(el);
  return [...txt].join(' | ');
}", host.element_handle())
```

## Workflow

1. Identify a failing locator and confirm whether the target lives inside a Shadow Root (DevTools > Elements).
2. Bind to the host element and fetch the shadow root via `evaluate()`.
3. Query and interact inside the root using small helper functions that return serializable results.
4. Assert via text, attributes, or ARIA roles rather than DOM distance.
5. Close artifacts with host-scoped assertions so cron/CI reports are meaningful.

## Anti-Patterns

- Don't loop `evaluate()` per step when a single helper extracting multiple values is faster and less flaky.
- Don't assume `page.locator('my-element button')` pierces Shadow DOM — it does not.
- Don't rely on `locator('text=...')` across shadow boundaries without first evaluating inside the root.
- Don't access closed shadow roots from page scripts without using the host’s native methods; the browser will block.

## Verification

1. Write a QA page with a known open shadow root and interact purely via the host + evaluate path.
2. Confirm the page reports the correct inner text/attribute without altering the component.
3. Run under `playwright test --headed` and `--headless` to confirm parity.
4. For a known closed-root component, confirm evaluate-through-host is required and assert it returns expected values.
