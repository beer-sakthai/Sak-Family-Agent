# Hugging Face / Milestone Stat Card — Pillow Pattern

A reusable dark-themed stat card for announcing download milestones, metrics, or any numbers-heavy post on Instagram.

## Visual style
- Background: deep navy (#0a0e27) to warm amber (#8a3e3a) vertical gradient
- Brand: "⚡ HOUSE OF SAK" in muted purple (#7c7caa)
- Hero number: golden (#ffdd77), 200pt DejaVuSans-Bold
- Stat boxes: dark rectangles (#1a1a3e fill, #2a2a5e border), golden numbers inside
- Body text: light grey (#c0c0d8 to #e0d8d0) on dark
- Footer badges: dim grey (#404060)
- MH resources: very dim (#303050) at very bottom

## Minimum font sizes (Beer is visually impaired)
| Element | Font | Size |
|---------|------|------|
| Hero number | DejaVuSans-Bold.ttf | 200pt |
| Headlines | DejaVuSans-Bold.ttf | 72pt |
| Stat values | DejaVuSans-Bold.ttf | 52pt |
| Stat labels / body | DejaVuSans.ttf | 36pt |
| Badges / footer | DejaVuSans.ttf | 28pt |
| MH resources | DejaVuSans.ttf | 24pt |

## Code template (always run from Composio sandbox for IG publish)

```python
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350  # IG portrait 4:5
img = Image.new('RGB', (W, H), '#0a0e27')
draw = ImageDraw.Draw(img)

# Gradient
for y in range(H):
    t = y / H
    r = int(10 + 120 * t)
    g = int(14 + 50 * t)
    b = int(39 + 60 * t)
    draw.rectangle([(0, y), (W, y)], fill=(r, g, b))

# Fonts — NEVER use ImageFont.load_default()
font_huge  = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 200)
font_big   = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 72)
font_mid   = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 52)
font_body  = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 36)
font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 28)
font_tiny  = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)

# Brand
draw.text((W // 2, 50), "⚡ HOUSE OF SAK", fill='#7c7caa', font=font_mid, anchor='mt')

# Hero number
draw.text((W // 2, 200), "2,264", fill='#ffdd77', font=font_huge, anchor='mt')

# Description
draw.text((W // 2, 420), "Total Hugging Face Downloads", fill='#ffffff', font=font_big, anchor='mt')
draw.text((W // 2, 510), "Models + Datasets", fill='#b0b0c8', font=font_body, anchor='mt')

# Stat boxes (side by side)
box_y, box_h, box_w, gap = 600, 130, 300, 20
total_w = box_w * 3 + gap * 2
start_x = (W - total_w) // 2
stats = [("1,934", "MODELS"), ("330", "DATASETS"), ("7", "REPOS")]

for i, (val, lab) in enumerate(stats):
    x = start_x + i * (box_w + gap)
    draw.rectangle([(x, box_y), (x + box_w, box_y + box_h)], fill='#1a1a3e', outline='#2a2a5e', width=4)
    draw.text((x + box_w // 2, box_y + 30), val, fill='#ffdd77', font=font_mid, anchor='mt')
    draw.text((x + box_w // 2, box_y + 85), lab, fill='#9090b0', font=font_body, anchor='mt')

# Top models / list items (manual centering — multiline_text doesn't support anchor)
draw.text((W // 2, 820), "🏆 Top Models", fill='#e0d8d0', font=font_mid, anchor='mt')
items = ["repo-name  ·  667", "repo-name  ·  544", "repo-name  ·  398"]
for i, line in enumerate(items):
    bbox = draw.textbbox((0, 0), line, font=font_body)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, 900 + i * 52), line, fill='#c0c0d8', font=font_body)

# Footer
draw.text((W // 2, 1180), "Built from a shelter in Cork, Ireland", fill='#707090', font=font_body, anchor='mt')
draw.text((W // 2, 1230), "🏆 Google Skills Diamond (top 1%)", fill='#404060', font=font_small, anchor='mt')
draw.text((W // 2, 1270), "🪟 MS Learn L12 · 264k XP · 162 badges", fill='#404060', font=font_small, anchor='mt')
draw.text((W // 2, 1305), "🤗 huggingface.co/Nanthasit", fill='#404060', font=font_small, anchor='mt')
draw.text((W // 2, H - 18), "Pieta 1800 247 247 · Samaritans 116 123", fill='#303050', font=font_tiny, anchor='mb')

img.save('ig-stat-card.png', 'PNG')
```

## Upload for Instagram API

Run the generation INSIDE the Composio workbench sandbox, then:
```python
result, err = upload_local_file('/home/user/ig-stat-card.png')
s3key = result.get('s3key', '')
# Pass s3key to INSTAGRAM_POST_IG_USER_MEDIA as image_file.s3key
```
