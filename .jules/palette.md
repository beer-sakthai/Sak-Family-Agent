## 2026-08-02 - Accessible Icon Buttons and Focus Ring Patterns

**Learning:** Icon-only buttons (such as search clear inputs, pagination arrows, and modal close triggers) lack descriptive names for screen readers and default focus states can be subtle or hidden in dark mode glassmorphism UI shells.

**Action:** Always provide explicit `aria-label` attributes and keyboard focus ring styles (`focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500`) on interactive icon-only elements across Next.js / Tailwind dashboard components.
