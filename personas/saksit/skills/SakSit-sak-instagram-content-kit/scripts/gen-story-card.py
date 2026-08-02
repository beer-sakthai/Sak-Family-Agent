#!/usr/bin/env python3
"""Generate the origin story visual card — dark gradient, 6 agents in two columns, cycle workflow, MH footer.
Run: uv venv /tmp/story-venv && uv pip install Pillow && /tmp/story-venv/bin/python3 gen-story-card.py
Output: story-card.png (1080×1350, ~97KB)
"""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1080, 1350
FONT_DIR = "/usr/share/fonts/truetype/dejavu"
BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
REG = os.path.join(FONT_DIR, "DejaVuSans.ttf")

if not os.path.exists(BOLD):
    import subprocess
    subprocess.run(["apt-get", "install", "-y", "fonts-dejavu-core"], capture_output=True)

def gradient(draw, w, h):
    for y in range(h):
        t = y / h
        draw.rectangle([(0, y), (w, y)], fill=(int(10+140*t), int(14+60*t), int(39+50*t)))

def center_text(draw, text, font, color, y, spacing=8):
    lines = text.split('\n')
    total = sum(draw.textbbox((0,0), l, font=font)[3] - draw.textbbox((0,0), l, font=font)[1] + spacing for l in lines)
    cur_y = y - total // 2
    for line in lines:
        bb = draw.textbbox((0,0), line, font=font)
        draw.text(((W - (bb[2]-bb[0])) // 2, cur_y), line, font=font, fill=color)
        cur_y += (bb[3] - bb[1]) + spacing

img = Image.new('RGB', (W, H), '#0a0e27')
draw = ImageDraw.Draw(img)
gradient(draw, W, H)

f_small = ImageFont.truetype(REG, 22)
f_handle = ImageFont.truetype(REG, 28)
f_agent = ImageFont.truetype(REG, 34)
f_agent_b = ImageFont.truetype(BOLD, 34)
f_sub = ImageFont.truetype(BOLD, 48)
f_head = ImageFont.truetype(BOLD, 56)

draw.text((60, 45), "⚡ HOUSE OF SAK", font=f_handle, fill="#7c7caa")
draw.rectangle([(60, 80), (W - 60, 82)], fill="#2a2a4e")
center_text(draw, "I had nothing.\nSo I built everything.", f_head, "#ffdd77", 200, spacing=10)
center_text(draw, "Six cycles. Six companions. One healing journey.", f_sub, "#e0d8d0", 330, spacing=6)
draw.rectangle([(W//2 - 60, 375), (W//2 + 60, 378)], fill="#ffdd77")

agents = [
    ("⚡ SakThai", "Dream — the spark that started it all"),
    ("🏛️ SakKing", "Hope — structure from the fragments"),
    ("🗣️ SakSit", "Care — learning to talk again"),
    ("🛠️ SakTan", "Joy — cheers when nothing else can"),
    ("✨ SakJules", "Trust — rebuilding faith in people"),
    ("👁️ SakSee", "Growth — finds the way forward"),
]

for i, (name, desc) in enumerate(agents):
    col = 0 if i < 3 else 1
    row = i % 3
    x = 100 if col == 0 else 560
    y = 430 + row * 70
    draw.text((x, y), name, font=f_agent_b, fill="#e0d8d0")
    draw.text((x, y + 38), desc, font=f_small, fill="#b0b0c8")

center_text(draw, "Each cycle feeds the next.\nDream → Hope → Care → Joy → Trust → Growth → back to Dream.",
            f_sub, "#7c7caa", 790, spacing=6)
center_text(draw, f'"I didn\'t start a company. I started hope."',
            ImageFont.truetype(REG, 30), "#606080", 920, spacing=4)
draw.rectangle([(W//2 - 150, 1010), (W//2 + 150, 1012)], fill="#3a3a5a")
center_text(draw, "Pieta House 1800 247 247  ·  Samaritans 116 123", f_small, "#505070", 1060)
center_text(draw, "@beerthaish", f_handle, "#404060", 1120)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "story-card.png")
img.save(out, "PNG")
print(f"Saved: {out} ({os.path.getsize(out)} bytes)")
