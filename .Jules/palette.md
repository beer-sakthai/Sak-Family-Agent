## 2026-08-18 - Accessibility & Keyboard Focus for Icon-Only Controls in Real-Time Streams
**Learning:** Icon-only buttons (such as trash/clear icons) with only a `title` attribute are inaccessible to many screen readers and lack distinct focus-visible rings for keyboard users.
**Action:** Always complement or replace icon-only buttons with explicit `aria-label` attributes and Tailwind `focus-visible:ring-2` focus states to ensure seamless accessibility across input modalities.

## 2026-08-19 - Accessible Command Palette Modal with Full Keyboard Loop Navigation
**Learning:** Command palette modals in SPA dashboards often lack explicit ARIA listbox semantics (`role="dialog"`, `role="listbox"`, `role="option"`, `aria-selected`), accessible close buttons, and arrow-key cycling across search results.
**Action:** Always implement modal dialog semantics (`role="dialog"`, `aria-modal="true"`), backdrop dismiss handlers, explicit `aria-label` attributes on icon controls, and ArrowUp/ArrowDown/Enter selection with state synchronization to ensure accessible keyboard-only navigation.

## 2026-08-19 - Semantic Buttons and ARIA States for Interactive Persona Cards & Toggles
**Learning:** Interactive cards built using `<div>` with `onClick` handlers are completely unreachable via keyboard Tab navigation and fail to communicate toggle state to assistive technologies.
**Action:** Always construct interactive toggle cards with native `<button type="button">` elements equipped with `aria-pressed`, descriptive `aria-label`, and Tailwind `focus-visible:ring-2` ring indicators.
## 2026-08-18 - Accordion & Collapsible Button Accessibility
**Learning:** Collapsible sections and accordions (like reasoning process blocks in agent cards) require explicit `aria-expanded` attributes and accessible names so screen reader users understand whether the section is open or collapsed. Visible focus outlines (`focus-visible:ring-2`) are also required for keyboard navigation.
**Action:** Always include `aria-expanded={isOpen}`, an descriptive `aria-label`, and `focus-visible:ring-2` styles on toggle buttons for collapsible UI elements.
