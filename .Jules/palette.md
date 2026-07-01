# Palette's Journal

## 2025-05-14 - [Accessibility Baseline for Dashboard]
**Learning:** The dashboard lacked basic ARIA attributes for interactive elements and visible focus states for keyboard users.
Adding `aria-current` to navigation items and descriptive `aria-label` to icon-only buttons/links significantly improves the screen reader experience.
Using Tailwind's `focus-visible` utility allows for "delightful" focus states that only appear when navigating via keyboard,
keeping the UI clean for mouse users while remaining accessible.

**Action:** Always include `focus-visible:ring-2` and appropriate ARIA attributes for any new interactive components in the dashboard.
Ensure external links always include `aria-label` noting they open in a new tab.
