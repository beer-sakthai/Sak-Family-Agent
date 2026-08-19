## 2026-08-18 - Accessibility & Keyboard Focus for Icon-Only Controls in Real-Time Streams
**Learning:** Icon-only buttons (such as trash/clear icons) with only a `title` attribute are inaccessible to many screen readers and lack distinct focus-visible rings for keyboard users.
**Action:** Always complement or replace icon-only buttons with explicit `aria-label` attributes and Tailwind `focus-visible:ring-2` focus states to ensure seamless accessibility across input modalities.

## 2026-08-19 - Semantic Buttons and ARIA States for Interactive Persona Cards & Toggles
**Learning:** Interactive cards built using `<div>` with `onClick` handlers are completely unreachable via keyboard Tab navigation and fail to communicate toggle state to assistive technologies.
**Action:** Always construct interactive toggle cards with native `<button type="button">` elements equipped with `aria-pressed`, descriptive `aria-label`, and Tailwind `focus-visible:ring-2` ring indicators.
