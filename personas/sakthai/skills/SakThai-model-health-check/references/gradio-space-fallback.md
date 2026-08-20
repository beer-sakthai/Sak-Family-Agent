# Companion Space Fallback for Inference Testing

When a model's serverless inference is unavailable (router returns HTTP 400, `StopIteration` from huggingface_hub provider system), many non-Transformer models have companion Gradio Spaces that serve as the intended test harness.

## When to use this

- Model has `pipeline_tag` for a non-text-generation task (text-to-speech, image-to-text, etc.)
- Router returns `{"error":"Model not supported by provider hf-inference"}`
- Model uses a non-standard format (GGUF custom architecture, ONNX, custom PyTorch)
- Model's README or `cardData` mentions a demo Space

## Space Discovery

```bash
# Method 1: Search model's cardData for space links
curl -s "https://huggingface.co/api/models/{owner}/{model}" \
  -H "Authorization: Bearer $HF_TOKEN" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
# Check cardData for spaces references
card = d.get('cardData', {}) or {}
for key in ['spaces', 'space', 'demo', 'app']:
    if key in card:
        print(f'{key}: {card[key]}')
# Also check tags for sibling space names
tags = d.get('tags', [])
for t in tags:
    if t.startswith('space:'):
        print(f'space tag: {t}')
"

# Method 2: Look up known spaces for the model
curl -s "https://huggingface.co/api/spaces?search={owner}-{model}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for s in data[:5]:
    print(f'{s[\"id\"]} | sdk: {s.get(\"sdk\",\"?\")} | status: {s.get(\"runtime\",{}).get(\"stage\",\"?\")}')
"
```

## Space Status Check

```bash
OWNER="Nanthasit"
SPACE="sakthai-tts"

# Get space metadata
curl -s "https://huggingface.co/api/spaces/$OWNER/$SPACE" \
  -H "Authorization: Bearer $HF_TOKEN" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
sd = d.get('subdomain', '')
print(f'SDK: {d.get(\"sdk\")}')
print(f'Hardware: {d.get(\"hardware\", \"cpu-basic\")}')
print(f'Status: {d.get(\"runtime\", {}).get(\"stage\", \"unknown\")}')
if sd:
    url = f'https://{sd}.hf.space'
    print(f'Space URL: {url}')
    print(f'Gradio 5 API: {url}/api/predict')
    print(f'Gradio 6+ API: {url}/gradio_api/api/predict')
    print(f'Direct call: {url}/call/... (Gradio 6+)')
"
```

## Gradio API Patterns

### Gradio 5 (pre-June 2026)

```bash
curl -s -X POST "https://{subdomain}.hf.space/api/predict" \
  -H "Content-Type: application/json" \
  -d '{"data": ["input text"]}'
```

### Gradio 6+ (SvelteKit, current)

The `/api/predict` endpoint returns 405 (wrong method). Use:

```bash
# First, get the endpoint info
curl -s "https://{subdomain}.hf.space/gradio_api/api/predict" \
  -H "Content-Type: application/json" \
  -d '{"data": ["input text"]}'

# Or discover available endpoints
curl -s "https://{subdomain}.hf.space/gradio_api/api/info"

# Look for the predict endpoint URL in the page source
curl -s "https://{subdomain}.hf.space" | grep -oP 'call/[a-zA-Z0-9_-]+' | head -5
```

### Fallback: Full page load + form interaction

If the API endpoint isn't documented, you can use the browser tool to:
1. Navigate to the Space URL
2. Use `browser_vision` to see the interface
3. Type input and interact with components
4. Check console output via `browser_console`

## Recording Results

When using a Space as an inference test harness, record in the YAML:

```yaml
gradio_space_status:
  space_id: "Owner/space-name"
  status: "RUNNING"  # or STOPPED, BUILDING, SLEEPING
  url: "https://owner-space-name.hf.space"
  sdk: "gradio"
  hardware: "cpu-basic"  # or the actual tier
  note: "Space is running and can be used for manual testing via the web UI"
```

## Limitations

- Free Spaces **sleep after inactivity** (15 min default). Cold start takes 30-60s.
- ZeroGPU Spaces have **daily quotas** (CPU: 100h, GPU: varies).
- Spaces behind OAuth require login cookies/tokens — not cron-friendly.
- Gradio API endpoints change between versions — always probe before scripting.
