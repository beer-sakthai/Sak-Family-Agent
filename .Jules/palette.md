## 2025-05-18 - Keyboard shortcut hint and Escape key handler for notice banners
**Learning:** Dismiss buttons on banner notices (like `HostedNotice`) benefit from handling keyboard `Escape` events directly on keydown and providing explicit `(Esc)` hint tooltips for clear interaction feedback.
**Action:** Include `onKeyDown` Escape handler on dismiss controls and append shortcut hints in hover tooltips.
