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

## 2026-09-12 - Informative Title Tooltips on OperationsPulse Signal Cards

**Learning:** Interactive signal summary cards in operational pulse panels (such as `OperationsPulse`) act as navigation buttons opening detailed sub-panels, but desktop mouse users lack instant visual target feedback upon hovering unless explicit `title` attributes are provided alongside `aria-label` screen reader text.

**Action:** Always complement `aria-label` attributes on interactive signal cards in `OperationsPulse` with explicit `title` tooltips (`title={`Open ${signal.label} details`}`) for desktop hover guidance.
## 2026-09-14 - Hover Tooltips for Activity Heatmap Legend Level Swatches

**Learning:** Decorative color swatches in dataset/heatmap legends can leave desktop users guessing what specific intensity or run count range each color level represents unless descriptive `title` tooltips are applied to each swatch element.

**Action:** Add explicit `title` attributes (e.g. `title={level === 0 ? "No activity" : \`Activity level ${level} of 4\`}`) on heatmap legend level swatches to provide clear visual hover feedback.

## 2026-09-15 - Screen Reader Announcement Status for KPI Skeleton Placeholders

**Learning:** Skeleton loading containers (such as `KpiSkeleton`) with animated shimmer blocks can cause screen readers to ignore or silently bypass loading states if proper ARIA live regions and labels are missing.

**Action:** Always add `role="status"`, `aria-label="Loading..."`, and visually hidden screen reader text (`<span className="sr-only">Loading...</span>`) to root skeleton container components.
## 2026-09-14 - Explicit Type Attributes and Hover Tooltips on Table Row Action Buttons

**Learning:** Row-level action buttons in data tables (such as "Steps" in `WorkflowRuns` and "View" in `SessionExplorer`) that open detail drawers often carry `aria-label` screen reader text but omit `title` attributes and `type="button"`. Desktop mouse users benefit from instant hover tooltips describing the action target.

**Action:** Always provide explicit `type="button"` and `title` tooltips matching `aria-label` text on table row action trigger buttons.

## 2026-09-16 - Informative Title Tooltips on StitchStudio View Options & Copy Action

**Learning:** View option tab triggers and copy code buttons in workbench panels (such as `StitchStudio`) provide tab roles and `aria-label` text for screen readers, but omit hover `title` tooltips for desktop mouse users. Adding explicit `title` tooltips gives desktop users clear visual feedback on hover.

**Action:** Always complement `role="tab"` and action buttons in workbench tools with explicit `title` hover tooltips.

## 2026-09-17 - Informative Shortcut Tooltips and Explicit Type on Drawer Close Buttons

**Learning:** Header close buttons in overlay/drawer detail components (such as `Drawer`) often carry `aria-label` screen reader text but omit explicit `type="button"` and hover `title` tooltips with keyboard shortcut hints (`title="Close detail panel (Esc)"`). Desktop mouse users benefit from visual tooltip guidance showing both the action and its keyboard shortcut.

**Action:** Always add explicit `type="button"` and `title` tooltips containing shortcut hints (e.g. `title="Close detail panel (Esc)"`) to overlay/drawer close buttons.

## 2026-09-18 - Initial Focus Management on Dropdown Menu Open

**Learning:** Dropdown menu containers with `role="menu"` (such as `PersonaFilter`) that handle arrow key navigation require auto-focusing the first interactive item (`[role="menuitem"]`, `[role="menuitemcheckbox"]`) when opened so keyboard users can immediately start navigating without needing an extra keypress.

**Action:** Add an effect on dropdown menus to focus the first menu item element immediately when `open` state becomes `true`.

## 2026-09-19 - Explicit Type Attributes and Tooltips on Pagination Buttons

**Learning:** Pagination buttons (such as Previous/Next triggers in `SessionExplorer`) often omit explicit `type="button"`. Omitting `type="button"` on interactive controls can cause unintentional form submissions if the component is rendered within a `<form>` element.

**Action:** Always include explicit `type="button"` attributes alongside `aria-label` and `title` tooltips on pagination and table navigation controls.

## 2026-09-20 - Descriptive Screen Reader Labels for Special Keyboard Character Badges

**Learning:** When displaying keyboard shortcut badges (`<kbd>`) for symbols or special characters (such as `⌘`, `?`, `[`), screen readers may fail to announce or mispronounce raw unicode symbols unless mapped to human-readable names (e.g. "Command", "Question mark", "Left bracket") in `aria-label` and `title` attributes.

**Action:** Map unicode symbols to descriptive spoken words in `aria-label` and `title` attributes on `<kbd>` elements.

## 2026-09-21 - Explicit Type Attributes on Mobile Drawer Controls

**Learning:** Mobile navigation drawers and off-canvas overlays (such as in `Sidebar.tsx`) contain backdrop dismiss buttons and close triggers that can default to `type="submit"` if omitted and rendered inside or alongside form contexts, potentially causing accidental form submissions or unexpected navigation behaviors.

**Action:** Always include explicit `type="button"` attributes on mobile drawer dismiss triggers and backdrop overlays alongside `aria-label` and `title` tooltips.

## 2026-09-22 - Explicit Type Attributes on TopBar Controls and Dropdown Menu Options

**Learning:** TopBar controls (mobile nav toggle, command palette search, link copy, presentation mode, refresh) and dropdown options (`role="menuitem"`, `role="menuitemcheckbox"`, `role="menuitemradio"`) in header menus can default to `type="submit"` when explicit `type="button"` attributes are omitted, risking unintentional form submissions if embedded inside or alongside form contexts.

**Action:** Always specify `type="button"` on all interactive topbar triggers and dropdown menu option elements across dashboard shell components.

## 2026-09-23 - Explicit Type Attributes and Dynamic Tooltips on Sidebar Nav Buttons

**Learning:** Navigation tab buttons (`NavButton`) in sidebar components can default to `type="submit"` if `type="button"` is omitted and rendered in a form context. Additionally, omitting hover tooltips on expanded sidebar tabs leaves desktop users without instant target feedback.

**Action:** Always provide explicit `type="button"` attributes and dynamic `title` tooltips (`title={collapsed ? item.label : \`Switch to ${item.label} section\`}`) on sidebar navigation tabs.

## 2026-09-24 - Screen Reader Hidden Shortcut Badges and Tooltips in CommandPalette Options

**Learning:** Interactive option items in command palettes (such as `CommandPalette.tsx`) render visual keyboard shortcut badges (`<kbd>`), which screen readers announce as redundant or unspaced text alongside the option label unless marked with `aria-hidden="true"`. Additionally, hover tooltips (`title`) on option items provide desktop users instant visual shortcut feedback.

**Action:** Add `aria-hidden="true"` to visual `<kbd>` elements inside `CommandPalette` option buttons and complement them with informative hover `title` tooltips.

## 2026-09-25 - Informative Hover Tooltips on AgentCard Stat Badges

**Learning:** Token usage and error count status badges in `AgentCard` cards display numerical stats on screen, but desktop mouse users lack visual hover tooltips explaining the full context of those stats unless explicit `title` attributes are provided.

**Action:** Add descriptive `title` tooltips (e.g. `title={`Total token usage: ${tokens} tokens`}` and `title={`Recorded errors: ${errors}`}`) to status badge elements on agent overview cards.

## 2026-09-26 - Screen Reader Hidden Shortcut Badges in ShortcutsOverlay

**Learning:** Shortcut list rows rendering multi-key combinations with visual `<kbd>` badges can cause screen readers to voice disjointed or repeated key announcements when each `<kbd>` element bears an individual `aria-label`. Marking visual `<kbd>` badges with `aria-hidden="true"` and providing a single visually hidden (`sr-only`) spoken text string (e.g. `(Command + K)`) allows screen readers to announce full key combinations smoothly.

**Action:** Mark visual `<kbd>` elements inside shortcut list rows with `aria-hidden="true"` and render accessible spoken text inside a `<span className="sr-only">`.

## 2026-09-27 - Explicit Type Attributes and Tooltips on Alert Banner Actions and Footer Badges

**Learning:** Action buttons on error or warning alert banners (such as "Dismiss" and "Retry now") can default to `type="submit"` when rendered within form contexts if explicit `type="button"` attributes are omitted. Furthermore, visual `<kbd>` badges in page footers can cause disjointed screen reader output unless hidden with `aria-hidden="true"` and supplemented with hover `title` tooltips.

**Action:** Always specify `type="button"` and `title` tooltips on alert banner action triggers, and apply `aria-hidden="true"` alongside `title` tooltips to footer shortcut badges.
## 2026-09-27 - Explicit Button Types, ARIA Labels, and Tooltips on Alert Banners and Error Boundaries

**Learning:** Alert banner action triggers (such as error banner dismiss and partial data retry buttons) and route error boundary reset buttons can default to `type="submit"` if `type="button"` is omitted, and lack hover tooltips for desktop mouse users if `title` and `aria-label` attributes are missing.

**Action:** Always include explicit `type="button"`, `aria-label`, and `title` tooltips on alert/warning banner action buttons and error boundary reset triggers.

## 2026-09-28 - Informative Title Tooltips and ARIA Labels on Status and Severity Badges

**Learning:** Status pills in workflow runs (`WorkflowRuns.tsx`) and severity badges in security audit logs (`AuditLogs.tsx`) render icons alongside status text, but desktop mouse users and screen readers lack explicit hover tooltips (`title`) and screen reader labels (`aria-label`) describing badge purpose.

**Action:** Always provide explicit `title` and `aria-label` attributes on status and severity badge components (e.g. `title={`Workflow run status: ${status}`}` and `aria-label={`Severity: ${severity}`}`).

## 2026-09-29 - Image Roles for Non-Interactive Visual Legend Swatches with ARIA Labels

**Learning:** Static `<span>` elements (such as color intensity swatches in `ActivityHeatmap`) bearing `aria-label` attributes are ignored by screen readers unless given an explicit `role="img"`, because WAI-ARIA ignores `aria-label` on generic non-interactive HTML elements without a landmark or component role.

**Action:** Always include `role="img"` alongside `aria-label` and `title` when labeling static visual swatch or icon elements.
