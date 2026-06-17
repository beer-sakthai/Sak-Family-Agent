# Streamlit Dashboard Improvements

Roadmap of still-relevant dashboard features for the Streamlit application (`dashboard/app.py`).

---

## 📋 High Priority

### 1. Inline Fact Editing & Deletion
* **Goal**: Enable editing and deletion of memories directly from the dashboard UI.
* **Requirements**:
  - Add "Edit" (pencil) and "Delete" (trash) buttons next to each fact in the Memory tab.
  - Implement a confirmation popup or dialogue for deletions to prevent accidents.
  - Route changes to the `MemoryStore` sqlite DB.

### 2. Responsive Mobile Design
* **Goal**: Optimize layouts for mobile screens and tablets.
* **Requirements**:
  - Collapse the navigation sidebar on screen widths smaller than 768px.
  - Stack multi-column data cards vertically.
  - Resize Plotly charts dynamically based on the viewport width.

---

## 📊 Medium Priority

### 3. Advanced Memory Filtering & Search
* **Goal**: Easily locate relevant facts and observations.
* **Requirements**:
  - Add date range picker and text search input.
  - Multi-select filters for fact categories (`pref`, `note`, `project`).
  - Add query pagination to prevent dashboard lag on large databases.

### 4. Export & Import Snapshots
* **Goal**: Easily backup or sync SQLite memory state.
* **Requirements**:
  - "Export JSON" button to trigger a browser download of the SQLite database as JSON.
  - "Import JSON" file uploader supporting overwrite or deduplicated merge strategies.
