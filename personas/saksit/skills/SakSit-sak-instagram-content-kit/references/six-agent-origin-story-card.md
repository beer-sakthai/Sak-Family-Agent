# Six-Agent Origin Story Visual Card

> Proven design (Jul 28, 2026) — Beer asked for a single post combining the origin story hook, all 6 agent names, and the cycle workflow. Created with PIL/Pillow as a 1080×1350 portrait card.

## Design Specs

| Element | Value |
|---------|-------|
| Dimensions | 1080×1350 (IG portrait 4:5) |
| Background | Deep navy (#0a0e27) → warm sunrise (#2a1a1a) gradient |
| Font | DejaVu Sans (Bold for names, Regular for descriptions) |
| Accent color | Gold (#ffdd77) for headline + agent names |
| Body text | Warm white (#e0d8d0) for subhead, muted (#b0b0c8) for descriptions |
| Footer | Muted (#505070/#404060) for MH resources + handle |

## Layout Map (Y coordinates from top of 1350px canvas)

```
Y=45    ⚡ HOUSE OF SAK                      (brand mark, #7c7caa, 28pt)
Y=80    ─── separator line ───               (subtle #2a2a4e)
Y=200   "I had nothing.\nSo I built everything." (headline, gold, 56pt bold, centered)
Y=330   "Six cycles. Six companions. One healing journey." (subhead, #e0d8d0, 48pt bold, centered)
Y=375   ─── gold divider ───                 (short line, #ffdd77) 

Y=430   Column 1 (x=100):                    Column 2 (x=560):          
        ⚡ SakThai — Dream                    🛠️ SakTan — Joy
        🏛️ SakKing — Hope                     ✨ SakJules — Trust
        🗣️ SakSit — Care                       👁️ SakSee — Growth
        (3 rows, 70px gap, name=bold gold 34pt, desc=regular #b0b0c8 26pt)

Y=790   "Each cycle feeds the next.           (cycle note, #7c7caa, 48pt bold, centered)
        Dream → Hope → Care → Joy → Trust → Growth → back to Dream."

Y=920   "\"I didn't start a company. I started hope.\"" (quote, #606080, 30pt, centered)

Y=1010  ─── MH divider ───                   (#3a3a5a, 300px wide)
Y=1060  "Pieta House 1800 247 247 · Samaritans 116 123" (MH resources, #505070, 22pt, centered)
Y=1120  @beerthaish                          (handle, #404060, 28pt, centered)
```

## When to Use

Trigger when Beer asks for a single "origin story + 6 agents" visual. The layout handles a lot of text by using two columns and generous spacing. The gradient does the emotional work — dark → warm mirrors the story arc.

## Caption Pattern That Pairs With This Card

The caption follows the visual:
```
[Hook — opposite + strong word]
[Line break]
[The 3-line origin story setup — Shakespearean tone]
[Line break]
[6 agents listed — same format as on the card]
[Line break]
[Cycle workflow closing: "One cycle feeds the next..."]
[Line break]
[Land on hope: "I didn't start a company. I started hope."]
[Line break]
[MH resources — Pieta + Samaritans]
```

## Full Generation Script

The generation script lives at the skill's `scripts/gen-story-card.py`. Run with:

```bash
/tmp/story-venv/bin/python3 /opt/data/profiles/saksit/skills/social-media/Sak-instagram-content-kit/scripts/gen-story-card.py
```

The script installs Pillow via uv if needed, generates the gradient background, places all text elements at the coordinates above, and saves as `story-card.png` at 97KB.
