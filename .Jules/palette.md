## 2026-08-18 - Accessibility & Keyboard Focus for Icon-Only Controls in Real-Time Streams
**Learning:** Icon-only buttons (such as trash/clear icons) with only a `title` attribute are inaccessible to many screen readers and lack distinct focus-visible rings for keyboard users.
**Action:** Always complement or replace icon-only buttons with explicit `aria-label` attributes and Tailwind `focus-visible:ring-2` focus states to ensure seamless accessibility across input modalities.

## 2026-08-19 - Accessible Command Palette Modal with Full Keyboard Loop Navigation
**Learning:** Command palette modals in SPA dashboards often lack explicit ARIA listbox semantics (`role="dialog"`, `role="listbox"`, `role="option"`, `aria-selected`), accessible close buttons, and arrow-key cycling across search results.
**Action:** Always implement modal dialog semantics (`role="dialog"`, `aria-modal="true"`), backdrop dismiss handlers, explicit `aria-label` attributes on icon controls, and ArrowUp/ArrowDown/Enter selection with state synchronization to ensure accessible keyboard-only navigation.
## 2026-08-19 - Dialog ARIA Roles and Keyboard Arrow Navigation for Command Palettes
**Learning:** Modal overlays and command palettes often lack proper dialog semantics (`role="dialog"`, `aria-modal="true"`, `role="listbox"`, `role="option"`) and keyboard arrow selection, making search results inaccessible and cumbersome for keyboard and screen-reader users.
**Action:** Always provide dialog and listbox ARIA attributes on modal command palettes, alongside `ArrowDown`/`ArrowUp`/`Enter` keyboard navigation with stateful option highlighting and focus indicators.
