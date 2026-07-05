# Instagram Publish Workflow: s3key Approach

> 2026-07-04 — Discovery session that bypassed public file hosting entirely.  
> Prefer this over external file hosts (uguu.se, etc.) — it's more reliable and keeps everything inside Composio's infrastructure.

## Problem

Instagram's `INSTAGRAM_POST_IG_USER_MEDIA` needs the image to be at a URL their servers can fetch. Local files and private URLs don't work. External file hosts (uguu.se, etc.) are unreliable and often broken.

## Solution: s3key via Composio workbench

The `image_file` parameter accepts `{name, mimetype, s3key}` where `s3key` is a reference to a file already in Composio's S3. Generate the image inside the workbench sandbox and upload it.

## Step-by-step

### 1. Generate the image in the workbench sandbox

The workbench runs in a Composio sandbox that is **completely isolated** from the local host. It cannot:
- Read local filesystem paths
- Reach a local HTTP server (`localhost` or `host.docker.internal`)
- Access files from the Modal sandbox

So generate the image INSIDE the workbench:

```python
from PIL import Image, ImageDraw, ImageFont
import subprocess, os

W, H = 1080, 1080
img = Image.new('RGB', (W, H), '#0a0a0a')
draw = ImageDraw.Draw(img)

# Find fonts available in the sandbox
result = subprocess.run(['find', '/usr/share/fonts', '-name', '*.ttf'],
                       capture_output=True, text=True, timeout=10)
all_fonts = [f for f in result.stdout.strip().split('\n') if f]
# Select bold variant for main text, regular for body
# ... draw your card ...

img.save('/home/user/ig-card.png', 'PNG')
```

**Important:** DejaVu fonts are usually available at `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`. Use `subprocess.run(['find', ...])` to locate them since font paths vary.

### 2. Upload to Composio S3

```python
result, error = upload_local_file('/home/user/ig-card.png')
if error:
    print(f"Upload error: {error}")
else:
    s3key = result.get('s3key')
    # s3key example: "project/pr_Vr2_rzumY6Sm/tool_router_session/trs_xxx/yyy"
    s3url = result.get('s3_url')
    # s3url is a redirect URL, NOT directly usable as image_url by Instagram
```

**Note:** The `s3_url` returned by `upload_local_file` is a **redirect URL** (returns 302 → S3). Instagram's API does NOT follow redirects for `image_url`, which is why `image_file` with `s3key` works but the raw `s3_url` would fail as `image_url`.

### 3. Use s3key in the Instagram tool

```json
{
  "tool_slug": "INSTAGRAM_POST_IG_USER_MEDIA",
  "arguments": {
    "ig_user_id": "27647006041564332",
    "caption": "Your caption text here",
    "image_file": {
      "name": "ig-card.png",
      "mimetype": "image/png",
      "s3key": "project/pr_Vr2_rzumY6Sm/tool_router_session/trs_xxx/yyy"
    }
  }
}
```

### 4. Publish the container

```json
{
  "tool_slug": "INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH",
  "arguments": {
    "ig_user_id": "27647006041564332",
    "creation_id": "18456816136119128",
    "max_wait_seconds": 120
  }
}
```

### 5. Verify

Use `INSTAGRAM_GET_IG_MEDIA` with the published media ID to confirm it's live and get the permalink.

**WARNING:** HTTP 200 on the permalink URL does NOT guarantee the post is in the user's visible media grid. Also call `INSTAGRAM_GET_IG_USER_MEDIA` (limit=10, no cursor) to verify the post shows up.

## Complete script template

```python
# Workbench cell — generates, uploads, and you capture the s3key
from PIL import Image, ImageDraw, ImageFont
import subprocess, os

W, H = 1080, 1080
img = Image.new('RGB', (W, H), '#0a0a0a')
draw = ImageDraw.Draw(img)

# Gradient / visual design
for y in range(H):
    for x in range(W):
        # ... render pixel by pixel or use ImageDraw shapes ...
        pass

draw = ImageDraw.Draw(img)

# Fonts
result = subprocess.run(['find', '/usr/share/fonts', '-name', '*.ttf'],
                       capture_output=True, text=True, timeout=10)
all_fonts = [f for f in result.stdout.strip().split('\n') if f]
# Find bold variant
bold_f = next((f for f in all_fonts if 'Bold' in f), all_fonts[0] if all_fonts else None)
reg_f = next((f for f in all_fonts if 'DejaVuSans' in f and 'Light' not in f and 'Bold' not in f), bold_f)

FONT_BOLD = ImageFont.truetype(bold_f, 58) if bold_f else ImageFont.load_default()
FONT_REG = ImageFont.truetype(reg_f, 22) if reg_f else ImageFont.load_default()
FONT_SMALL = ImageFont.truetype(reg_f, 15) if reg_f else ImageFont.load_default()

# Draw content
# ... draw your text/lines here ...

out = '/home/user/ig-card.png'
img.save(out, 'PNG')
print(f"Generated: {os.path.getsize(out)} bytes")

# Upload
result, error = upload_local_file(out)
if error:
    print(f"Upload error: {error}")
else:
    s3key = result.get('s3key', '')
    print(f"s3key={s3key}")
    print(f"s3_url={result.get('s3_url', '')}")
```

## Known pitfalls

| Pitfall | Cause | Fix |
|---------|-------|-----|
| `upload_local_file` file not found | Path doesn't exist in sandbox | Generate file inside the workbench cell first; don't reference local host paths |
| Font not found | Missing DejaVu in sandbox | Use `find` to locate any `.ttf` and try/except fallback to `ImageFont.load_default()` |
| `INSTAGRAM_POST_IG_USER_MEDIA` returns 400 | Bad s3key or s3key points to wrong file | Re-run upload to get a fresh s3key; s3keys expire after a few hours |
| Post published but not in media grid | Silent failure or quota issue | Check quota with `INSTAGRAM_GET_IG_USER_CONTENT_PUBLISHING_LIMIT`; republish |
| Caption with `#` rejected | Raw `#` in caption without encoding | URL-encode the caption: `urllib.parse.quote(caption)` — Instagram handles this internally through the tool |