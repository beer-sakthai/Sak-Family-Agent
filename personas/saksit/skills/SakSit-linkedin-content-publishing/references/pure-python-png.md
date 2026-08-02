# Pure-Python PNG Generation

Generate PNG images when Pillow, cairosvg, ImageMagick, or other image libraries are unavailable. Uses only Python stdlib (`struct`, `zlib`).

## Minimal Function

```python
import struct, zlib

def create_png(width, height, pixels):
    """Generate a PNG from RGB pixel data. pixels[y][x] = (r, g, b)."""
    sig = b'\x89PNG\r\n\x1a\n'
    # IHDR — image header: width, height, bit_depth=8, color_type=2(RGB)
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    # IDAT — compressed pixel data
    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # filter byte (none) per row
        for x in range(width):
            r, g, b = pixels[y][x]
            raw_data += bytes([r, g, b])
    compressed = zlib.compress(raw_data)
    idat_crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
    idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
    # IEND — end marker
    iend_crc = zlib.crc32(b'IEND') & 0xffffffff
    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    return sig + ihdr + idat + iend
```

## Performance: Pre-Allocated Buffer

Pixel-by-pixel loops in Python at 1200×627 (752,400 pixels) take ~60s with naive row building. Use a `bytearray` to cut to <1s:

```python
W, H = 1200, 627
row_len = 1 + W * 3  # filter byte + 3 bytes per pixel
raw = bytearray(H * row_len)

for y in range(H):
    ny = y / H
    row_start = y * row_len
    for x in range(W):
        nx = x / W
        
        # Compute RGB values — example: dark gradient with center glow
        r = int(10 + nx * 10 + ny * 5)
        g = int(10 + nx * 5 + ny * 8)
        b = int(26 + nx * 15 + ny * 10)
        
        # Center glow
        dx = (nx - 0.5) * 2
        dy = (ny - 0.45) * 1.5
        glow = max(0, 1 - (dx*dx + dy*dy)) ** 2
        r += int(glow * 60)
        g += int(glow * 50)
        b += int(glow * 100)
        
        # Bottom-left purple accent
        bdx = (nx - 0.15) * 1.5
        bdy = (ny - 0.85) * 2
        bglow = max(0, 1 - (bdx*bdx + bdy*bdy)) ** 2 * 0.6
        r += int(bglow * 99)
        g += int(bglow * 102)
        b += int(bglow * 241)
        
        px = row_start + 1 + x * 3
        raw[px] = min(255, r)
        raw[px+1] = min(255, g)
        raw[px+2] = min(255, b)

compressed = zlib.compress(bytes(raw), 6)
```

## Common Visual Patterns

### Dark gradient background (for LinkedIn post imagery)
- Base: RGB(10, 10, 26) → lighter towards center
- Center glow: gaussian falloff `max(0, 1 - dist²)²` at (50%, 45%)
- Accent glow: second falloff at (15%, 85%) with purple tint

### Text overlay
Python's stdlib can't render text into PNG. For text, either:
- Save as SVG instead (LinkedIn may not accept SVG)
- Generate a rich gradient background only and let the user add text overlay manually
- Use a smaller image and describe it verbally to the user (Beer can't read on-screen)

## Color Gradients Reference

| Effect | Position | Color | Formula |
|--------|----------|-------|---------|
| Center glow | (0.5, 0.45) | Indigo/blue | `glow = max(0, 1-dist²)²` |
| Accent corner | (0.15, 0.85) | Purple (#6366f1) | `glow = max(0, 1-dist²)² * 0.6` |
| Edge darkening | whole image | Near-black | `base = 10-30` depending on nx, ny |
| Bottom accent line | y=560 | Gradient indigo→purple | SVG level, not pure-PNG |

## File Size Reference

| Dimensions | Compression | Size |
|-----------|-------------|------|
| 600×314 | zlib level 6 | ~100 KB |
| 1200×627 | zlib level 6 | ~230 KB |
| 1200×627 (solid color) | zlib level 6 | ~4 KB |

LinkedIn accepts images up to 20MB, PNG or JPEG. 1200×627 is the recommended aspect ratio (approximately 2:1).