# Palette's Journal

## 2026-07-02 - [Initial Audit]

**Learning:** The dashboard uses Lucide icons for many interactive elements (sidebar toggle, search, shield button) without ARIA labels or focus-visible rings.

**Action:** Add ARIA labels to icon-only buttons and ensure keyboard accessibility with focus ring

## 2026-07-07 - [Data Table Accessibility]

**Context:** The dashboard's data tables, such as the session history and memory views, were built using non-semantic `<div>` tags or basic `<table>` structures without proper header associations.

**Learning:** For screen readers to correctly interpret and navigate tabular data, the tables must be built with semantic HTML. This includes using `<caption>` for titles, `<thead>` for headers, and `<th>` tags with the `scope` attribute (`col` or `row`) to programmatically link data cells to their corresponding headers.

**Action:** Refactor all data tables to use proper semantic structure. Ensure `<th>` elements have the correct `scope` attribute, and add a `<caption>` to each table to provide a descriptive title for assistive technologies.
