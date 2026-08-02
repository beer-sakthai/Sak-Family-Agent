---
name: SakSit-image-analysis-fallback
category: creative
description: 'When vision_analyze fails (DeepSeek/no vision model), use Python/Pillow to extract image metadata — dimensions, color composition, edge/transition detection, dominant tones, and text presence indicators'
version: 1.0.1
author: SakSit
platforms: [linux]
---

# SakSit Image Analysis Fallback

> When the active model doesn't support `vision_analyze` (e.g., DeepSeek-V4-Flash), use Pillow-based analysis to extract what you can from an image Beer sends.

## When to use

- `vision_analyze()` returns "unknown variant `image_url`" or similar deserialization error
- Beer sends an image and you need to describe it to him (he can't read on-screen)
- You need basic info about an image (size, colors, potential text)

## Prerequisites

```bash
uv venv --python 3.13
source .venv/bin/activate
uv pip install Pillow
```

## Analysis script

```python
from PIL import Image

img = Image.open('/path/to/image.jpg')
print("Size:", img.size)
print("Mode:", img.mode)
print("Format:", img.format)

# Sample pixels (every 50th) for color composition
pixels = list(img.getdata())
sampled = pixels[::50]

color_groups = {
    'dark/black': 0, 'white': 0, 'gold/amber': 0,
    'red/pink': 0, 'blue': 0, 'green': 0, 'purple': 0, 'grey': 0
}
for r, g, b in sampled:
    if r < 40 and g < 40 and b < 60:
        color_groups['dark/black'] += 1
    elif r > 220 and g > 220 and b > 220:
        color_groups['white'] += 1
    elif r > 180 and g > 140 and b < 120:
        color_groups['gold/amber'] += 1
    elif r > 180 and g < 110 and b < 130:
        color_groups['red/pink'] += 1
    elif r < 120 and g > 130 and b > 180:
        color_groups['blue'] += 1
    elif r < 120 and g > 150 and b < 130:
        color_groups['green'] += 1
    elif r > 130 and g < 100 and b > 130:
        color_groups['purple'] += 1
    else:
        color_groups['grey'] += 1

total = sum(color_groups.values())
print("\nColor composition:")
for color, count in sorted(color_groups.items(), key=lambda x: -x[1]):
    pct = count/total*100
    if pct > 0.5:
        print(f"  {color}: {pct:.1f}%")

# Corner pixels give edge/background info
print("\nCorner pixels:")
print("  TL:", img.getpixel((0, 0)))
print("  TR:", img.getpixel((img.width-1, 0)))
print("  Center:", img.getpixel((img.width//2, img.height//2)))
print("  BL:", img.getpixel((0, img.height-1)))
print("  BR:", img.getpixel((img.width-1, img.height-1)))

# Detect text by luminance transitions on horizontal center line
center_strip = [img.getpixel((x, img.height//2)) for x in range(0, img.width, 5)]
transitions = 0
for i in range(1, len(center_strip)):
    prev_bright = sum(center_strip[i-1])/3
    curr_bright = sum(center_strip[i])/3
    if abs(curr_bright - prev_bright) > 60:
        transitions += 1
print("\nText edges detected:", transitions)
if transitions > 20:
    print("→ Likely has text on it")
