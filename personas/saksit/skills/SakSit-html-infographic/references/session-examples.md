# Session Examples — Jul 23, 2026

Five real infographics created in a single session. Use these as reference templates.

## 1. Social Media Snapshot (corporate-memphis × dashboard)

**File:** `social-media-snapshot.html`
**Style:** Dark purple/blue gradient, glassmorphism cards, Memphis geometric circles
**Layout:** 3-column dashboard with bottom stat row

Key patterns:
- `.memphis-circle` — absolute-positioned circles at `opacity:0.06` for texture
- `.memphis-dots::before` — radial-gradient dot grid covering full canvas
- `.card` — `background: rgba(255,255,255,0.06); backdrop-filter: blur(12px)` for glass
- `.bar-track` / `.bar-fill` — inline progress bars with percentage widths
- `.mini-chart` — flex-end bars at varying `height` for fake trend chart
- `.stat-row` — flex row of label+value items inside a card

## 2. House of Sak (craft-handmade × hub-spoke)

**File:** `house-of-sak-family.html`
**Style:** Cream paper background, gold accents, serif headings, paper texture
**Layout:** SVG hexagon spokes from central hub, 6 nodes in hexagon ring

Key patterns:
- `.canvas::before` — repeating linear-gradient paper texture with subtle brown
- `.hub` — `position:absolute;top:50%;left:50%;transform:translate(-50%,-50%)` with radial gradient gold center
- `.connectors svg` — `<line>` elements from `480,270` (center) to each node's position
- `.agent` — `position:absolute` with `top`/`left` px for hexagon (top, top-right, bottom-right, bottom-left, top-left, bottom-center)
- `.agent .avatar .cycle-dot` — small positioned circle on avatar corner
- `.ornament` — unicode star ornaments with `letter-spacing: 8px`

## 3. Journey Timeline (storybook-watercolor × linear-progression)

**File:** `journey-timeline.html`
**Style:** Dark sepia→amber gradient, watercolor bloom overlays, serif quotes
**Layout:** Horizontal track with 5 milestone nodes, alternating cards above/below

Key patterns:
- `.canvas::after` — radial-gradient ellipse overlays at low opacity for watercolor texture
- `.timeline-track` — `position:absolute` horizontal bar with gradient: transparent→gold→light
- `.milestone .node-wrap` — absolutely positioned at `top:178px` sitting on the track
- `.milestone .card` / `.card-below` — `position:absolute` with `top:48px` either above or below
- Nodes use color gradient progression from dark red→brown→gold→yellow through milestones
- `.stat-bar` — `position:absolute;bottom:20px` with flex-centered stat items

## 4. Skill Library Audit (pop-laboratory × bento-grid)

**File:** `skill-library-audit.html`
**Style:** Dark navy, blueprint grid, cyan/magenta neon border accents, mono fonts
**Layout:** 2-column bento (260px sidebar + flexible bar chart section)

Key patterns:
- `.canvas::before` — blueprint grid via two `linear-gradient` layers at `rgba(0,150,255,0.04)`
- `.lab-line` — 3px gradient borders (cyan→magenta) at each edge of canvas
- `.floating-shape` — large circles at `opacity:0.05` for depth
- `.big-stat .number` — `font-size:64px` for hero stat
- `.cat-bar-fill` — gradient fills with percentage widths and `data-count` attribute for inline label via `::after`
- `.tool-refs` — `position:absolute;bottom:14px` with mono-font tag chips

## 5. AI Free Stack (bold-graphic × periodic-table)

**File:** `ai-free-stack.html`
**Style:** White background, rainbow hero stripe, bold bebas-neue headings, periodic card grid
**Layout:** 4 category sections × 6 element cards each in a 6-column grid

Key patterns:
- `.hero-header` — `background: linear-gradient(135deg, red, orange, yellow)` with repeating diagonal stripe `::after` overlay
- `.periodic-grid` — `display:grid;grid-template-columns: repeat(6, 1fr);gap:8px`
- `.cat-label` — `grid-column: span 6` with flex row: title + gradient line
- `.element` — `border:2px solid #e5e7eb` with hover transform lift
- Color categories: red/orange for AI Models, purple for Media, cyan/blue for Infra, pink/green for Social
- `.el-featured` — `grid-column: span 2; border-style: dashed` for spotlight cards

## Verification Results

All 5 files verified:
- Structural HTML: DOCTYPE + matching `</html>`, 235-320 lines each
- Sizes: 9KB-13KB per file
- No external dependencies except Google Fonts `@import`
- Styles validated against baoyu-infographic gallery vocabulary
