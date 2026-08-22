## 2026-08-18 - Accessibility & Keyboard Focus for Icon-Only Controls in Real-Time Streams
**Learning:** Icon-only buttons (such as trash/clear icons) with only a `title` attribute are inaccessible to many screen readers and lack distinct focus-visible rings for keyboard users.
**Action:** Always complement or replace icon-only buttons with explicit `aria-label` attributes and Tailwind `focus-visible:ring-2` focus states to ensure seamless accessibility across input modalities.

## 2026-08-19 - Accessible Command Palette Modal with Full Keyboard Loop Navigation
**Learning:** Command palette modals in SPA dashboards often lack explicit ARIA listbox semantics (`role="dialog"`, `role="listbox"`, `role="option"`, `aria-selected`), accessible close buttons, and arrow-key cycling across search results.
**Action:** Always implement modal dialog semantics (`role="dialog"`, `aria-modal="true"`), backdrop dismiss handlers, explicit `aria-label` attributes on icon controls, and ArrowUp/ArrowDown/Enter selection with state synchronization to ensure accessible keyboard-only navigation.

## 2026-08-19 - Semantic Buttons and ARIA States for Interactive Persona Cards & Toggles
**Learning:** Interactive cards built using `<div>` with `onClick` handlers are completely unreachable via keyboard Tab navigation and fail to communicate toggle state to assistive technologies.
**Action:** Always construct interactive toggle cards with native `<button type="button">` elements equipped with `aria-pressed`, descriptive `aria-label`, and Tailwind `focus-visible:ring-2` ring indicators.

## 2026-08-20 - Accessible Data Table Filter Tabs with Live Region Updates
**Learning:** Table filter buttons (such as severity level filter tabs) often lack explicit `aria-pressed` states and fail to announce filter changes to screen readers when focus remains on the active filter button.
**Action:** Complement table filter tabs with `type="button"`, `aria-pressed`, descriptive `aria-label` attributes, focus ring styles, and an `aria-live="polite"` element that announces updated matching row counts to screen readers on filter selection.

## 2026-08-18 - Accordion & Collapsible Button Accessibility
**Learning:** Collapsible sections and accordions (like reasoning process blocks in agent cards) require explicit `aria-expanded` attributes and accessible names so screen reader users understand whether the section is open or collapsed. Visible focus outlines (`focus-visible:ring-2`) are also required for keyboard navigation.
**Action:** Always include `aria-expanded={isOpen}`, an descriptive `aria-label`, and `focus-visible:ring-2` styles on toggle buttons for collapsible UI elements.

## 2026-08-20 - Action Name Consistency in Control ARIA Labels
**Learning:** Replacing an interactive control's `aria-label` with a status string when disabled (e.g., changing `"Clear stream events"` to `"Stream is empty"`) degrades screen reader accessibility because it obscures the action of the control. Assistive technologies already announce the button role and disabled state (e.g. *"Clear stream events, button, disabled"*).
**Action:** Keep `aria-label` consistent and action-oriented regardless of disabled state; convey conditional state information via `title` attributes or status live regions instead.

## 2026-08-21 - Semantic Expandable Stage Cards in Multi-Agent Pipelines
**Learning:** Expandable workflow stage cards implemented as `<div>` tags with `onClick` handlers fail keyboard accessibility standards (unreachable via Tab, missing `aria-expanded` and focus rings).
**Action:** Render interactive expandable cards using semantic `<button type="button">` elements with explicit `aria-expanded`, descriptive `aria-label`, full block width styling (`w-full text-left`), and focus rings (`focus-visible:ring-2`).

## 2026-08-21 - Accessible Session Transcript Explorer Controls and Dialog Semantics
**Learning:** Data table explorer controls (search input, filter dropdowns, pagination buttons, modal inspectors) often omit explicit `aria-label` names, `aria-live="polite"` result count announcements, and `role="dialog"` modal attributes.
**Action:** Always complement search inputs and select controls with explicit `aria-label`s, visible focus rings (`focus-visible:ring-2`), polite live regions for result counts, and `role="dialog"` modal containers.

## 2026-08-22 - Labeled Buttons and ARIA Pressed Selection States
**Learning:** Adding an `aria-label` attribute to a button with visible text overrides its accessible name, violating WCAG Label in Name standards and breaking text-based queries.
**Action:** Preserve visible text as the accessible name for buttons with text content, and use `type="button"`, `aria-pressed={isActive}`, and visible focus indicators (`focus-visible:ring-2`) for keyboard accessibility.
