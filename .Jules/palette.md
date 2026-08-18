## 2026-08-18 - Accordion & Collapsible Button Accessibility
**Learning:** Collapsible sections and accordions (like reasoning process blocks in agent cards) require explicit `aria-expanded` attributes and accessible names so screen reader users understand whether the section is open or collapsed. Visible focus outlines (`focus-visible:ring-2`) are also required for keyboard navigation.
**Action:** Always include `aria-expanded={isOpen}`, an descriptive `aria-label`, and `focus-visible:ring-2` styles on toggle buttons for collapsible UI elements.
