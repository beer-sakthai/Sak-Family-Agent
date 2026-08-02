---
name: SakSit-image-analysis-fallback
category: creative
description: Analyze images with Pillow when vision unavailable.
version: 1.1.0
author: SakSit
platforms:
- linux
tags:
- Image
- Analysis
---

# SakSit Image Analysis Fallback

> When the active model doesn't support `vision_analyze` (e.g., DeepSeek-V4-Flash), use Pillow-based analysis to extract what you can from an image Beer sends.

## When to use

- `vision_analyze()` returns "unknown variant `image_url`" or similar deserialization error
- `vision_analyze()` returns a 400/5xx upstream error ("Upstream request failed", "Error from provider")
- Beer sends an image and you need to describe it to him (he can't read on-screen)
- You need basic info about an image (size, colors, potential text)

## Prerequisites

### Pillow install

Best approach (temp venv, no pollution):
```bash
python3 -m venv /tmp/imgview --system-site-packages && /tmp/imgview/bin/pip install Pillow
```

Or if you want a project venv:
```bash
uv venv --python 3.13
source .venv/bin/activate
uv pip install Pillow
```

⚠️ **Pitfall**: `uv pip install Pillow --system` may report success but Pillow won't actually import. The PEP 668 guard on this system blocks it silently. Always use a venv.
⚠️ **Pitfall**: the JPEG header byte parser and Pillow may disagree on dimensions on progressive JPEGs (SOF2). The raw header parser showed 8704×769 but Pillow read 412×512. Always trust Pillow for actual usable dimensions.

## Analysis script — tiered intensity

### Tier 1: Quick check (file exists, format valid)

```python
import os
path = '/path/to/image.jpg'
if not os.path.exists(path):
    print("FILE NOT FOUND")
    raise SystemExit(1)
with open(path, 'rb') as f:
    header = f.read(4)
if header[:2] == b'\xff\xd8':
    print("Valid JPEG header: YES")
    print(f"File size: {os.path.getsize(path)} bytes")
elif header[:8] == b'\x89PNG\r\n\x1a\n':
    print("Valid PNG header: YES")
else:
    print(f"Unknown format, magic bytes: {header.hex()}")
```

### Tier 2: Basic properties (always run)

```python
from PIL import Image
from collections import Counter

img = Image.open(path)
print("Size:", img.size)
print("Mode:", img.mode)
print("Format:", img.format)

pixels = list(img.getdata())
unique = set(pixels)
avg_bright = sum((r+g+b)//3 for r,g,b in pixels) / len(pixels)
print(f"Avg brightness: {avg_bright:.1f}")
print(f"Unique colors: {len(unique)}")
print(f"Most common colors: {Counter(pixels).most_common(10)}")
```

### Tier 3: Grid analysis (best for understanding layout)

```python
w, h = img.size
rows, cols = 4, 4
cell_w, cell_h = w // cols, h // rows
for r in range(rows):
    for c in range(cols):
        left = c * cell_w
        upper = r * cell_h
        right = min((c+1)*cell_w, w)
        lower = min((r+1)*cell_h, h)
        cell = img.crop((left, upper, right, lower))
        avg = cell.resize((1,1)).getpixel((0,0))
        num_colors = len(cell.getcolors(maxcolors=50)) if cell.getcolors(maxcolors=50) else 0
        print(f"  Cell ({c+1},{r+1}) [{left}:{right}, {upper}:{lower}]: avg={avg}, colors≈{num_colors}")
```

### Tier 4: Vertical strip analysis (wide images — timelines, screenshots, spreadsheets)

```python
parts = 8
part_w = w // parts
for i in range(parts):
    left = i * part_w
    right = min((i+1)*part_w, w)
    section = img.crop((left, 0, right, h))
    avg = section.resize((1,1)).getpixel((0,0))
    colors = section.getcolors(maxcolors=50)
    num = len(colors) if colors else 0
    print(f"Section {i+1} (x={left}-{right}): avg={avg}, colors≈{num}")
```

### Tier 5: Edge analysis (checking borders for background colour)

```python
for y in [0, h//4, h//2, 3*h//4, h-1]:
    row_colors = [img.getpixel((x, y)) for x in [0, w//4, w//2, 3*w//4, w-1]]
    print(f"  Row y={y}: {row_colors}")
```

### Tier 6: Enhanced copies (for visual inspection or re-upload)

```python
from PIL import ImageEnhance, ImageOps

# High contrast version
enhanced = ImageEnhance.Contrast(img).enhance(2.0)
enhanced = ImageEnhance.Sharpness(enhanced).enhance(2.0)
enhanced.save('/tmp/img_enhanced.jpg', 'JPEG', quality=95)

# Inverted version (dark text on light bg → light text on dark bg)
inverted = ImageOps.invert(img)
inverted.save('/tmp/img_inverted.jpg', 'JPEG', quality=95)
```

## Presenting results to the user

When full vision is unavailable:
1. Say vision is down, don't pretend it isn't
2. Give dimensions, format, file size
3. Describe the colour palette from grid/edge analysis
4. Mention any detected text indicators (edge transitions)
5. Offer to save enhanced/inverted versions they can look at
6. Ask the user to describe what they sent so you can help
