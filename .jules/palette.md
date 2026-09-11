## 2026-08-02 - Accessible Icon Buttons and Focus Ring Patterns

**Learning:** Icon-only buttons (such as search clear inputs, pagination arrows, and modal close triggers) lack descriptive names for screen readers and default focus states can be subtle or hidden in dark mode glassmorphism UI shells.

**Action:** Always provide explicit `aria-label` attributes and keyboard focus ring styles (`focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500`) on interactive icon-only elements across Next.js / Tailwind dashboard components.

## 2026-09-02 - WAI-ARIA Tablist Roving TabIndex and Arrow Navigation Pattern

**Learning:** Tab components using `role="tablist"` require roving `tabIndex` (`0` on active tab, `-1` on inactive tabs) and keyboard event handlers (`ArrowRight`, `ArrowLeft`, `Home`, `End`) so screen reader and keyboard users can seamlessly navigate between tabs without excessive tab stops.

**Action:** On all tabbed interfaces in dashboard components, implement `tabIndex={active ? 0 : -1}` and handle keyboard navigation events to focus and activate tabs.

## 2026-09-07 - Informative Tooltips and Disabled Cursors on Header Actions

**Learning:** Interactive controls in the topbar (such as refresh triggers and data mode toggles) can leave users uncertain about state during async refetches or when toggling datasets if hover tooltips (`title`) and explicit disabled cursor states (`disabled:cursor-not-allowed`) are missing.

**Action:** Always complement `aria-label` and `disabled` attributes on topbar controls with dynamic `title` tooltips explaining current status/actions and `disabled:cursor-not-allowed` styles.

## 2026-09-09 - Accessible Focus Rings and Tooltips on Modal Backdrop Scrims

**Learning:** Full-screen modal and drawer backdrop scrim buttons (such as in `CommandPalette` and `Drawer`) act as dismiss triggers when clicked or focused by keyboard, but lack visible focus indicators and hover tooltips unless explicit `title` attributes and inset focus ring classes (`focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset`) are applied.

**Action:** Always provide explicit `title` tooltips and inset focus ring styles (`focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset`) on interactive backdrop scrim buttons.

## 2026-09-11 - Informative Title Tooltips on Interactive KPI Tile Cards

**Learning:** Interactive KPI tile cards that act as shortcut buttons navigating to background dashboard panels can confuse desktop users if hover tooltips (`title`) indicating the destination panel are missing alongside screen reader `aria-label` attributes.

**Action:** Always provide explicit `title` attributes (`title={`Open the ${target} panel`}`) on interactive tile cards in `KpiStrip` to give instant hover guidance for desktop mouse users.
