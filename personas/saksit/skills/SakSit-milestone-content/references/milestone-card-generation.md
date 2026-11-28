# Milestone Card Generation & Copywriting Templates

Code scripts and copywriting formulas for turning download numbers and milestones into social cards.

## 1. Stat Card Generation with Pillow
```python
from PIL import Image, ImageDraw, ImageFont

def generate_stat_card(number_str: str, label_str: str, output_path: str = "milestone_card.png"):
    img = Image.new("RGB", (1080, 1080), color=(15, 23, 42))  # Slate 900
    draw = ImageDraw.Draw(img)

    # Primary metric
    draw.text((100, 400), number_str, fill=(56, 189, 248))    # Sky 400
    draw.text((100, 550), label_str, fill=(241, 245, 249))     # Slate 100

    # Branding footer
    draw.text((100, 950), "Sak-Family-Agent · Beer (@beer-sakthai)", fill=(148, 163, 184))
    img.save(output_path)
```

## 2. Platform Copywriting Templates

### LinkedIn Formula
- **Hook**: Direct milestone callout ("Just crossed 2,000+ model downloads on Hugging Face.").
- **Story**: Why small models matter (0.5B/1.5B accessible to all developers without $10k GPUs).
- **Takeaway**: 3 core engineering lessons learned.
- **CTA**: Link to model weights.

### X (Twitter) Formula
- Short hook + exact metric.
- 1 key metric highlight.
- Hugging Face link + `#BuildInPublic #OpenSourceAI`.
