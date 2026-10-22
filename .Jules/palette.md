## 2026-03-30 - WAI-ARIA progressbar semantics on operational signal bars
**Learning:** Signal health meter bars in summary cards benefit from explicit WAI-ARIA `role="progressbar"` attributes (`aria-label`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`, `aria-valuetext`) rather than `aria-hidden` so screen readers accurately announce signal health metrics.
**Action:** Replace `aria-hidden` on progress bar containers with WAI-ARIA progressbar attributes describing signal state.

## 2025-05-18 - Keyboard shortcut hint and Escape key handler for notice banners
**Learning:** Dismiss buttons on banner notices (like `HostedNotice`) benefit from handling keyboard `Escape` events directly on keydown and providing explicit `(Esc)` hint tooltips for clear interaction feedback.
**Action:** Include `onKeyDown` Escape handler on dismiss controls and append shortcut hints in hover tooltips.

## 2026-10-03 - Search input keyboard focus shortcut with visual indicator
**Learning:** Adding a global `/` key listener to focus search inputs (bypassing when focus is already inside editable controls) alongside a subtle `<kbd>` hint badge improves keyboard discoverability and navigation efficiency.
**Action:** Attach a global keydown handler for `/`, mark the inner `<kbd>` badge with `aria-hidden="true"`, and include `(/)` in `title` and `placeholder` attributes.

## 2026-10-05 - Search filter Escape key clearance in overlay modals
**Learning:** Search inputs inside modal overlays benefit from intercepting `Escape` keydown when populated to clear search text and stop event propagation, preventing users from accidentally dismissing the entire modal.
**Action:** Add `onKeyDown` handler checking `e.key === "Escape"` to search inputs in overlays to call `e.stopPropagation()` and reset search query.

## 2026-10-08 - Accessible empty state containers and data source tooltips for chart panels
**Learning:** Chart panel headers benefit from decorative icons marked `aria-hidden="true"`, data source badges with explicit `title` hover tooltips and `aria-label` descriptions, and empty chart state containers marked with `role="status"` and `aria-label` to announce empty states to assistive technologies.
**Action:** Mark decorative chart panel icons with `aria-hidden="true"`, add `title` and `aria-label` to data source badges, and assign `role="status"` and `aria-label` to empty chart placeholder containers.

## 2026-10-08 - WCAG 2.5.3 Label in Name compliance on ARIA-labeled text buttons
**Learning:** When adding `aria-label` screen reader names to interactive buttons displaying visible text, the `aria-label` must begin with or contain the exact visible text (e.g., `aria-label="Try again - re-render the dashboard"` for a button showing "Try again") to comply with WCAG 2.5.3 (Label in Name) and prevent speech recognition activation failures.
**Action:** Ensure button `aria-label` values include the full visible button text before additional contextual descriptions.

## 2026-10-11 - Avoid nesting interactive controls inside trigger buttons
**Learning:** Placing interactive controls (`span role="button" tabIndex={0}`) inside native `<button>` elements violates HTML semantics and causes erratic focus behavior and screen reader misannouncements. Wrapping the trigger and clear buttons as sibling `<button>` elements inside a flex container maintains the pill aesthetic while ensuring proper ARIA accessibility and keyboard navigation.
**Action:** Structure composite buttons with inner clear actions using sibling `<button>` elements inside a flex wrapper rather than nesting interactive elements inside a `<button>`.

## 2026-10-13 - Visual and ARIA selection state for table rows with detail drawers
**Learning:** In table views accompanied by side detail drawers, table rows should check if their ID matches the open item, applying `aria-selected={isSelected}` and active highlight styling (`bg-raised/80 font-medium`) so users visually spot the open record and screen readers announce row selection.
**Action:** Set `aria-selected={isSelected}` and active background styling on table rows when their detail drawer is open.

## 2026-10-16 - Stable target IDs for single dynamic tabpanel containers
**Learning:** In tablist components where multiple tabs switch content inside a single dynamic `<div role="tabpanel">` container, tab controls (`role="tab"`) should reference a stable container ID (`aria-controls="stitch-tabpanel"`) rather than tab-specific IDs, ensuring `aria-controls` always resolves to a valid DOM node regardless of active tab state.
**Action:** Assign a stable `id` to single dynamic `<div role="tabpanel">` containers and set matching `aria-controls` on all member `role="tab"` buttons.

## 2026-10-18 - Popover dismissal and trigger focus restoration on option selection
**Learning:** Selecting a menu item radio or option button inside a preference popover menu (`role="menuitemradio"`) should dismiss the popover (`setOpen(false)`) and restore focus to the trigger element (`triggerRef.current?.focus()`) to maintain a predictable ARIA focus flow and avoid leaving users stuck inside a fulfilled menu.
**Action:** Call `setOpen(false)` and `triggerRef.current?.focus()` inside click handlers for preference option items in popover menus.

## 2026-10-21 - Dedicated visual live previews for workbench preset selections
**Learning:** In UI workbench showcase components like StitchStudio, preset selections (such as `mermaid-arch` architecture diagrams) should render dedicated visual live preview components in the preview panel rather than falling through to raw code text.
**Action:** Render styled visual flow diagrams or card previews for diagram and UI presets in workbench preview panels.

## 2026-10-25 - Screen reader live status announcements for overlay search query results
**Learning:** In overlay search tools (such as CommandPalette and ShortcutsOverlay), adding an off-screen `role="status"` polite live region when a search query is active and matches exist ensures screen reader users receive immediate verbal feedback on matching result counts as they type.
**Action:** Include a `<span className="sr-only" role="status" aria-live="polite">` element reporting the match count when search queries are active in overlay modal filters.
**Action:** Render styled visual flow diagrams or card previews for diagram and UI presets in workbench preset panels.

## 2026-10-24 - Section badge count metrics in tablist aria-label and collapsed hover tooltips
**Learning:** Navigation tab buttons carrying badge counts (e.g. `Sessions` with badge `42`) should include the count metric in `aria-label` and hover `title` tooltips so screen readers announce section metrics during tablist navigation and collapsed sidebar hover tooltips expose metrics to desktop users.
**Action:** Include section count metrics in `aria-label` and `title` attributes on navigation tab buttons when count metrics are defined.

## 2026-10-27 - Explicit top-full vertical anchor class on absolute popovers
**Learning:** Popover menus rendered inside `relative` trigger containers require an explicit `top-full` (`top: 100%`) CSS positioning utility class so the popover panel anchors directly below the trigger button rather than overlapping it with browser-default static top positioning.
**Action:** Include `top-full` on `absolute` popover containers alongside `right-0` and `mt-2` when positioned inside relative trigger wrappers.

## 2026-10-30 - Real-time match count announcements via off-screen polite live regions
**Learning:** In overlay search tools like `CommandPalette`, maintaining a persistently mounted off-screen `<span className="sr-only" role="status" aria-live="polite">` live region element that updates its text content (e.g. `5 commands found`) as search queries change ensures screen readers reliably announce real-time match count updates to the user as they type.
**Action:** Add a persistently mounted `<span className="sr-only" role="status" aria-live="polite">` inside modal search overlays that reflects active result counts when search queries are present.

## 2026-11-02 - Descriptive hover tooltips on non-interactive KPI summary tiles
**Learning:** Non-interactive KPI summary tiles (such as Success rate or Avg latency) benefit from explicit `title` attributes incorporating label, value, and hint text so desktop mouse users can inspect metric details on hover without adding unnecessary `tabIndex={0}` tab stops to non-interactive elements.
**Action:** Set `title={`${tile.label}: ${tile.value}${tile.hint ? ` (${tile.hint})` : ""}`}` on non-interactive KPI summary cards.
