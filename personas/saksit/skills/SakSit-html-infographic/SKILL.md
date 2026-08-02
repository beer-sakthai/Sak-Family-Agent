---
name: SakSit-html-infographic
description: Self-contained HTML infographic files.
version: 1.0.0
author: Hermes Agent (SakSit)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - infographic
    - html
    - design
    - creative
    - visual
    - dashboard
    - timeline
    - diagram
    related_skills:
    - SakSit-baoyu-infographic
    - SakSit-claude-design
    - SakSit-sketch
category: creative
---

# HTML Infographic

Create **self-contained HTML infographic files** — beautiful, designed, single-file documents that render in any browser with zero external dependencies (except optional Google Fonts via `@import`).

Use this when the user asks for infographics, data snapshots, visual summaries, timelines, dashboards, or information graphics as *HTML files* (not images). The content goes into a browser, not a PNG.

Also use this as the **fallback** when image generation is unavailable — instead of telling the user you can't generate images, switch to HTML mode automatically. The output is a viewable, screenshot-able HTML file the user can open in any browser.

## Relationship to baoyu-infographic

This skill shares the **layout gallery** and **style gallery** from `baoyu-infographic` — the same 21 layouts × 21 styles matrix. The difference is delivery: `baoyu-infographic` generates a PNG via `image_generate`; this skill generates a `.html` file.

**Load `baoyu-infographic` alongside this skill** when the user requests a named style or layout from that gallery (e.g. "corporate memphis style", "hub-spoke layout", "pop-laboratory"). The style definitions there drive the visual choices here.

**Choose HTML mode when:**
- Text-heavy content (lots of labels, stats, categories) — HTML renders text crisp; images blur it
- The user will want to edit, proofread, or reuse the content
- Data density is high (many data points needing accurate positioning)
- Zero API cost matters (no image generation credits)

**Choose image mode (baoyu-infographic) when:**
- The user needs a shareable PNG/JPEG for social media or print
- The style requires authentic brush/paint textures CSS can't replicate
- Content is simple (few labels, one visual concept)

## Standard Canvas

All infographics are a **fixed-size canvas** centered in the viewport:

```
960×540 px  = 16:9 landscape (default)
540×960 px  = 9:16 portrait
600×600 px  = 1:1 square
```

Structure:
```html
<body style="display:flex;justify-content:center;align-items:center;min-height:100vh;background:{outer-bg}">
<div class="canvas" style="width:960px;height:540px;position:relative;overflow:hidden;border-radius:24px;background:{inner-bg}">
  <!-- decoration layers (position:absolute, pointer-events:none, z-index low) -->
  <!-- title area (z-index high) -->
  <!-- content grid / flex layout -->
  <!-- footer / branding -->
</div>
</body>
```

The outer body centers the canvas. The canvas element carries the design background, rounded corners, and shadow. Content sits inside the canvas with `position:relative;z-index` layering.

## Visual Decorations (No Images)

All visual texture comes from CSS — never embed images:

| Technique | Use Case |
|-----------|----------|
| `background: linear-gradient(135deg, ...)` | Background gradient, hero bars, accent fills |
| `::before { background: repeating-linear-gradient(...) }` | Blueprint grids, paper texture, dot patterns |
| `radial-gradient(circle, ...)` over `::after` | Watercolor bloom overlays, spotlight effects |
| `backdrop-filter: blur(12px)` | Glassmorphism cards (corporate-memphis) |
| `box-shadow` stacks | Depth, glow, elevation |
| Emoji (Unicode characters) | Icons — no SVG, no images |
| `@import url('https://fonts.googleapis.com/css2?family=...')` | Google Fonts — only acceptable external dep |

## Layout-to-HTML Patterns

### Dashboard
- CSS grid `grid-template-columns: repeat(3, 1fr)` or `2fr 1fr`
- Cards as `<div class="card">` with glassmorphism backgrounds
- Mini-charts as inline `<div>` bars with percentage widths
- Stat rows: `display:flex;gap:20px` with label + number

### Hub-and-Spoke
- SVG `<line>` / `<path>` from center to nodes — `viewBox="0 0 960 540"` for absolute positioning in canvas coords
- Nodes: `position:absolute` with `top`/`left` in hexagon layout
- Central hub: `position:absolute;top:50%;left:50%;transform:translate(-50%,-50%)` with radial gradient background

### Linear Timeline
- Horizontal track: `height:3px; background: linear-gradient(90deg, ...)` with `position:absolute`
- Milestones: `display:flex; justify-content: space-around` or absolutely positioned
- Cards alternate above/below using `position:absolute` with `top` values above/below the track
- Node dots: `width:32px;height:32px;border-radius:50%` with gradient backgrounds

### Periodic Table
- Multi-section grid, each using `display:grid;grid-template-columns: repeat(6,1fr);gap:8px`
- Category labels span full width via `grid-column: 1 / -1`
- Element cards: colored borders per category, hover lift effect
- Hero header with gradient stripe across top

### Bento Grid
- CSS grid with `grid-template-areas` or manual `grid-column: span N`
- One featured cell at 2× size
- Mixed card sizes create the bento look

### Funnel / Pyramid
- Stacked `div`s with `margin:0 auto` and decreasing `width` percentages
- Each stage has its own background shade

### Circular Flow
- Five-to-seven absolutely-positioned circle nodes around a center
- SVG `<path>` or `<circle>` arcs for connecting lines with `stroke-dasharray`

### Binary Comparison
- Two equal columns `grid-template-columns: 1fr 1fr`
- Each side has its own accent color
- Mirrored card structure

## Style-to-CSS Recipes

### corporate-memphis
```css
.canvas { background: linear-gradient(135deg, #1a0533, #0d2b5e); }
.memphis-circle { position:absolute; border-radius:50%; opacity:0.06; }
.memphis-dots::before {
  background-image: radial-gradient(circle, rgba(139,92,246,0.08) 1px, transparent 1px);
  background-size: 30px 30px;
}
.card { background: rgba(255,255,255,0.06); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; }
.font { font-family: 'Inter', sans-serif; }
```

### craft-handmade
```css
.canvas { background: #f5efe0; }
.canvas::before {
  background-image: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(139,115,85,0.03) 2px, rgba(139,115,85,0.03) 4px);
}
.font-heading { font-family: 'Playfair Display', serif; }
.font-body { font-family: 'Inter', sans-serif; }
.accent { color: #b8860b; border-color: #d4a843; }
```

### storybook-watercolor
```css
.canvas { background: linear-gradient(160deg, #1a1210, #4a3520, #8b6914); }
.canvas::after {
  background: radial-gradient(ellipse at 20% 80%, rgba(180,120,60,0.08) 0%, transparent 50%);
}
.font-heading { font-family: 'Source Serif 4', serif; }
.font-body { font-family: 'Inter', sans-serif; }
```

### pop-laboratory
```css
.canvas { background: #0d1f3c; }
.canvas::before {
  background-image:
    linear-gradient(rgba(0,150,255,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,150,255,0.04) 1px, transparent 1px);
  background-size: 24px 24px;
}
.lab-border { background: linear-gradient(90deg, transparent, #06b6d4, #ec4899, transparent); height: 3px; }
.font-heading { font-family: 'Space Grotesk', sans-serif; }
.font-mono { font-family: 'JetBrains Mono', monospace; }
```

### bold-graphic
```css
.hero { background: linear-gradient(135deg, #dc2626, #f59e0b, #eab308); }
.font-heading { font-family: 'Bebas Neue', sans-serif; }
.price-tag { background: rgba(0,0,0,0.2); font-family: 'Bebas Neue', sans-serif; }
.element { border: 2px solid #e5e7eb; border-radius: 12px; }
```

## Font Pairs Reference

| Style | Heading | Body |
|---|---|---|
| corporate-memphis | Inter 700-900 | Inter 400-500 |
| craft-handmade | Playfair Display 700-800 | Inter 400-500 |
| storybook-watercolor | Source Serif 4 700-900 | Inter 300-400 |
| pop-laboratory | Space Grotesk 600-700 | JetBrains Mono 400-500 |
| bold-graphic | Bebas Neue | Inter 600-700 |
| aged-academia | Playfair Display / Libre Baskerville | Source Serif 4 |
| kawaii | Quicksand / Fredoka One | Quicksand |
| chalkboard | Caveat / Permanent Marker | Inter |
| retro-pop-grid | Archivo Black / Bebas Neue | Inter |
| hand-drawn-edu | Patrick Hand / Gochi Hand | Patrick Hand |

## Workflow

### 1. Intake
- Determine topic, data points, and tone
- Ask if the user has a preferred style/layout from the baoyu gallery, or infer one
- Confirm aspect ratio (default 16:9 landscape)

### 2. Design brief
- Choose layout (dashboard, timeline, hub-spoke, periodic-table, etc.)
- Choose style (corporate-memphis, craft-handmade, bold-graphic, etc.)
- Choose color scheme that matches content

### 3. Build
- Single self-contained HTML file
- Embedded `<style>` with all CSS
- Google Fonts via `@import url(...)` in `<style>` — the only CDN dependency allowed
- Emoji for all icons
- CSS-only decorations (gradients, pseudo-elements, box-shadows)
- Responsive via media queries (optional, the fixed canvas approach also works)

### 4. Verify
- Check file existence and structural HTML integrity
- If browser tools available: `browser_navigate(file:///path)` → `browser_vision(question)` → `browser_console()`
- Fix rendering issues, font load failures, overlapping elements

### 5. Deliver
- Report exact file path
- Summarize what each infographic contains
- Note verification status

## Pitfalls

1. **Don't use external images** — no `<img src="...">` pointing to CDNs. Emoji and CSS-only graphics only.
2. **Google Fonts via `@import` in `<style>` block** — not via `<link>` in `<head>`. The `@import` URL in a `<style>` element is the most self-contained approach for a single HTML file.
3. **Fixed canvas size** — 960×540 for 16:9. Don't let the canvas stretch to full viewport height or it breaks the designed proportions. Wrap in a centered flex container.
4. **Layer management** — decorative elements (`position:absolute;pointer-events:none`) need `z-index:0-1`, content needs `z-index:2+`. SVG connectors need their own z-index layer between decorations and content.
5. **Emoji rendering differs by OS** — test on the target platform if possible. Use common emoji (⭐, 📊, 🤖, 💻, 📈, 🎨) and avoid newly-released ones that may show as tofu.
6. **Don't fabricate data** — every number, label, and stat must come from the user or verified sources. No "placeholder" metrics.
7. **Font fallbacks** — always provide a system fallback after the Google Font name in `font-family`. Google Fonts can fail to load; the page should remain readable.

## Related Skills

- `baoyu-infographic` — Same layout/style vocabulary, but generates PNG images instead of HTML
- `claude-design` — Broader HTML artifact design (landing pages, decks, prototypes) with surface-first methodology
- `sketch` — Quick throwaway mockups for design exploration, not polished infographics
- `architecture-diagram` — SVG architecture diagrams, a different output format
