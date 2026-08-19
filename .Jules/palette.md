## 2026-08-18 - Accessibility & Keyboard Focus for Icon-Only Controls in Real-Time Streams
**Learning:** Icon-only buttons (such as trash/clear icons) with only a `title` attribute are inaccessible to many screen readers and lack distinct focus-visible rings for keyboard users.
**Action:** Always complement or replace icon-only buttons with explicit `aria-label` attributes and Tailwind `focus-visible:ring-2` focus states to ensure seamless accessibility across input modalities.

## 2026-08-19 - Accessible Command Palette Listbox & Keyboard Navigation Pattern
**Learning:** Command palette overlays without ARIA modal roles (`role="dialog"`, `role="listbox"`, `role="option"`, `aria-selected`) and arrow key listeners leave screen reader users unable to discover options or navigate without a pointer.
**Action:** Always wrap search dialogs in proper ARIA roles (`role="dialog"`, `aria-modal="true"`, `role="listbox"`), maintain active option index with `ArrowUp`/`ArrowDown`/`Enter` key handlers, and ensure smooth scroll into view with guard checks (`typeof el.scrollIntoView === 'function'`).
