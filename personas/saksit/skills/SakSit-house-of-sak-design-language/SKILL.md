---
name: SakSit-house-of-sak-design-language
category: creative
description: "Unified visual identity — colors, typography, card layouts."
version: 0.1.0
author: Hermes
tags: [Design, Brand, House-of-Sak, Visual-Identity, Guidelines]
---

# House of Sak Design Language

Central style guide for every creative asset produced for the House of Sak. All creative skills should reference this for colors, typography, layout, and brand elements instead of defining their own.

## Color Palette

### Primary Brand Colors

| Name | Hex | Usage |
|------|-----|-------|
| Sak Dark | `#0a0e27` | Background — cards, posts, banners |
| Sak Navy | `#1a1a3e` | Panel backgrounds, card containers |
| Sak Border | `#2a2a5e` | Borders, outlines, dividers |
| Sak Gold | `#ffdd77` | Primary accent — headlines, numbers, emphasis |
| Sak Warm | `#e8a040` | Secondary accent — highlights, sub-accents |
| Sak Light | `#e0d8d0` | Body text primary |
| Sak Muted | `#b0b0c8` | Body text secondary, labels |
| Sak Dim | `#707090` | Metadata, footnotes |
| Sak Faint | `#404060` | Footers, disclaimers, MH resources |

### Semantic Colors

| Meaning | Color |
|---------|-------|
| Dream / SakThai | `#ffdd77` gold |
| Hope / SakKing | `#34d399` emerald |
| Care / SakSit | `#22d3ee` cyan |
| Joy / SakTan | `#fb923c` orange |
| Trust / SakJules | `#a78bfa` violet |
| Growth / SakSee | `#fb7185` rose |

### Gradient: Warm Sunrise (default background)

```
Top:    #0a0e27 (sak dark)
Bottom: #1a1a3e (sak navy) with warm tint
Blend:  rgb(10+140*t, 14+60*t, 39+50*t) where t = y/height
```

## Typography

### Font Stack

| Context | Font | Fallback |
|---------|------|----------|
| Headlines (48-72pt) | `DejaVuSans-Bold.ttf` | Any bold sans-serif |
| Body (22-32pt) | `DejaVuSans.ttf` | Any sans-serif |
| Small/Labels (14-18pt) | `DejaVuSans.ttf` | Any sans-serif |
| Code/Monospace | `DejaVuSans-Mono.ttf` | `Courier New` |

### Text Sizes by Format

| Platform | Headline | Body | Footer |
|----------|----------|------|--------|
| Instagram Feed (1080×1350) | 80px | 45px | 30px |
| Instagram Story (1080×1920) | 100px | 55px | 32px |
| LinkedIn (1200×627) | 56px | 22px | 16px |
| Stat Card (1200×627) | 72px gold number | 24px label | 16px |
| Banner (1920×480) | 64px | 28px | 18px |

### Color by Text Role

| Role | Color |
|------|-------|
| Headline / Main number | `#ffdd77` (Sak Gold) |
| Body text | `#e0d8d0` (Sak Light) |
| Labels / secondary | `#b0b0c8` (Sak Muted) |
| Footer / MH resources | `#404060` (Sak Faint) |
| Attribution / handles | `#707090` (Sak Dim) |

## Card Layout Templates

### Asset: LinkedIn Stat Card (1200×627 landscape)

```
┌─────────────────────────────────────────────────────────┐
│  ⚡ HOUSE OF SAK                           [Sak Gold]   │
│                                                         │
│          ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│          │  1,234   │  │   567    │  │    89    │      │
│          │ Downloads │  │  Stars   │  │  Posts   │      │
│          └──────────┘  └──────────┘  └──────────┘      │
│                                                         │
│                       [Body text]                       │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│  Pieta 1800 247 247 | Samaritans 116 123    [Faint]    │
└─────────────────────────────────────────────────────────┘
```

### Asset: Instagram Portrait Card (1080×1350)

```
┌──────────────────────────┐
│                          │
│     ⚡ HOUSE OF SAK      │
│                          │
│       [Headline]         │
│     Sak Gold, 80px       │
│                          │
│      [Body text]         │
│    Sak Light, 45px       │
│                          │
│       ──── ∙ ────        │
│                          │
│   @beerthaish            │
│   Pieta 1800 247 247     │
│   Samaritans 116 123     │
└──────────────────────────┘
```

### Asset: Instagram Story Text Card (1080×1920)

```
┌──────────────────────────┐
│                          │
│                          │
│     [Headline]           │
│   Sak Gold, 100px        │
│     Bold, centered       │
│                          │
│   [Body line 1]          │
│   [Body line 2]          │
│   Sak Light, 55px        │
│                          │
│                          │
│     ──── ∙ ────          │
│   @beerthaish            │
│   Sak Dim, 32px          │
│                          │
│  Pieta 1800 247 247      │
│  Samaritans 116 123      │
│  Sak Faint, 28px         │
└──────────────────────────┘
```

## Logo & Wordmark

### Primary Logo (text only)

```
⚡ HOUSE OF SAK
```

- **Font:** DejaVuSans-Bold, uppercase
- **Color:** Sak Gold `#ffdd77` on dark backgrounds
- **Size:** Proportional to asset — min 24px, max 64px
- **Emoji:** ⚡ always precedes the wordmark

### Avatar/Mark (for profile pics)

The ⚡ emoji alone, centered on a dark background.

### Placement

| Asset | Logo Position |
|-------|---------------|
| LinkedIn posts | Top-left or top-center |
| Instagram feed | Top-center |
| Instagram Stories | Top-center |
| Stat cards | Top-left |
| Banners | Left-aligned, middle |

## Background Treatments

### Solid Dark (default)
`#0a0e27` solid fill. Use for text-heavy cards.

### Warm Sunrise Gradient (preferred)
```
Top:    #0a0e27
Bottom: #16213e
```
Best for stat cards, milestone announcements, storytelling posts.

### Subtle Grid Pattern
40px square grid in `#1a1a3e` (0.5px stroke). Use for detailed infographics and architecture diagrams.

## MH Resources Footer

Every post touching the origin story MUST include this exact footer:

```
Pieta 1800 247 247 | Samaritans 116 123
```

- Always at the bottom of the asset
- Font: Sak Faint `#404060`, 14-18px
- Separator: `|` with spaces

## Achievement Footer

Every post should include Beer's achievement badges below the main content:

```
🏆 Google Skills Diamond League (top 1% globally)
👨‍💻 Google Developer Program — Premium Tier
🪟 Microsoft Learn Level 12 — 162 badges, 40 trophies, 264k XP
🤗 huggingface.co/Nanthasit
```

- Font: Sak Dim `#707090`, at or near the foot
- Order: exactly as shown — Google Skills → Google Dev → MS Learn → HF

## Image Generation Pillow Defaults

```python
from PIL import Image, ImageDraw, ImageFont

def make_asset(width, height, headline, body, style="default"):
    img = Image.new('RGB', (width, height), '#0a0e27')
    draw = ImageDraw.Draw(img)

    # Gradient
    for y in range(height):
        t = y / height
        draw.rectangle([(0, y), (width, y)],
            fill=(10+140*t, 14+60*t, 39+50*t))

    # Fonts
    font_h = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 80)
    font_b = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 45)

    # Wordmark
    draw.text((40, 30), "⚡ HOUSE OF SAK", fill='#ffdd77', font=font_s)

    # Headline
    bbox = draw.textbbox((0, 0), headline, font=font_h)
    draw.text(((width - (bbox[2]-bbox[0]))//2, height//3), headline, fill='#ffdd77', font=font_h)

    return img
```

## Verification

Before calling an asset complete, check:
- [ ] Background uses Sak Dark or Warm Sunrise gradient
- [ ] Headlines in Sak Gold
- [ ] Body text in Sak Light or Sak Muted
- [ ] ⚡ HOUSE OF SAK wordmark present unless explicitly excluded
- [ ] MH resources footer present (if origin story content)
- [ ] Achievement footer present on professional posts
- [ ] Color contrast passes readability (gold on dark = safe)
- [ ] Fonts use DejaVu (available on all Linux systems)
