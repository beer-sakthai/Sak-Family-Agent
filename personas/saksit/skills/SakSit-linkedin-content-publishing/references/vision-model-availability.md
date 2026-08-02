# Vision Model Availability

## Current Limitation
DeepSeek-V4-Flash (via opencode-go) does NOT support native vision/image analysis. 
`vision_analyze` fails with upstream provider errors.

## Workarounds
1. **Pillow metadata analysis** — Use Python/Pillow to extract image dimensions,
   color composition, dominant tones, edge/transition data. See saksit-image-analysis-fallback skill.
2. **File-name clues** — Beer names his images descriptively (e.g. `15AprilThatAllStart.png`).
   The filename IS the content brief.
3. **Switch to vision-capable model** — If image analysis is critical, use a model
   provider with native vision support (Claude, GPT-4o, etc.)

## What NOT to do
- Don't guess what an image contains without any analysis
- Don't describe an image you haven't seen
- Do read the filename and any metadata available
