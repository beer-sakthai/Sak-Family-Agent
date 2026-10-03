## 2026-03-30 - WAI-ARIA progressbar semantics on operational signal bars
**Learning:** Signal health meter bars in summary cards benefit from explicit WAI-ARIA `role="progressbar"` attributes (`aria-label`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`, `aria-valuetext`) rather than `aria-hidden` so screen readers accurately announce signal health metrics.
**Action:** Replace `aria-hidden` on progress bar containers with WAI-ARIA progressbar attributes describing signal state.

## 2025-05-18 - Keyboard shortcut hint and Escape key handler for notice banners
**Learning:** Dismiss buttons on banner notices (like `HostedNotice`) benefit from handling keyboard `Escape` events directly on keydown and providing explicit `(Esc)` hint tooltips for clear interaction feedback.
**Action:** Include `onKeyDown` Escape handler on dismiss controls and append shortcut hints in hover tooltips.

## 2026-10-03 - Search input keyboard focus shortcut with visual indicator
**Learning:** Adding a global `/` key listener to focus search inputs (bypassing when focus is already inside editable controls) alongside a subtle `<kbd>` hint badge improves keyboard discoverability and navigation efficiency.
**Action:** Attach a global keydown handler for `/`, mark the inner `<kbd>` badge with `aria-hidden="true"`, and include `(/)` in `title` and `placeholder` attributes.
