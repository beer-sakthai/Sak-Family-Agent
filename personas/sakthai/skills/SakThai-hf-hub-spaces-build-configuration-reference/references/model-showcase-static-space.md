# Static Spaces as Model Showcase Pages

**Problem:** Gradio/Docker Spaces now require HF PRO subscription (402 Payment Required). But static Spaces remain free. How do you promote a model when you can't run interactive inference?

**Solution:** A well-designed static Space serves as a **model showcase landing page** — no fake demo needed. Honest, informative, cross-linked.

## When to Use

- Model has <50 downloads and needs promotion with $0 budget
- Model is not inference-compatible with serverless (GGUF, custom format)
- You want a permanent, always-on promotional page that costs nothing

## What NOT to Do

**Do not create fake demos.** The old `sakthai-tts` Space used browser's native `window.speechSynthesis` — completely unrelated to the actual Kokoro TTS model. Visitors heard generic browser voices, not the model. This is misleading and harms trust.

Instead: **Be honest that it's a showcase, not a demo.** Say "This is a static showcase. For live inference, use InferenceClient or run locally."

## Anatomy of a Good Showcase Page

| Section | Purpose | Details |
|---------|---------|---------|
| **Hero** | Identify the model + its role | Name, tagline, badge row (downloads, collection, profile, GitHub) |
| **Model Specs Card** | Quick reference table | Architecture, format, size, languages, metrics, requirements |
| **Usage Examples** | Show don't tell | 2–3 code snippets: InferenceClient, llama.cpp CLI, Python bindings |
| **Pipeline Diagram** | Show where it fits | Full vision→embed→reason→speak chain with links to sibling models |
| **Language/Feature Grid** | Visualize scope | Flags, tags, feature cards — scannable at a glance |
| **Use Cases** | Show applications | 4–6 cards matching real use patterns |
| **Family Download Table** | Cross-link ecosystem | All sibling models with live download counts, highlights current model |
| **Dataset Links** | Connect data assets | 2–3 related datasets with download counts |
| **Citation** | Enable academic use | BibTeX block |
| **Footer** | Context + branding | "Part of X", "Built by Y", family motto |

## Upload Workflow (Python)

```python
from huggingface_hub import HfApi
import os

api = HfApi(token=os.environ['HF_TOKEN'])

# Upload updated index.html
api.upload_file(
    path_or_fileobj='local/index.html',
    path_in_repo='index.html',
    repo_id='username/my-space',
    repo_type='space'
)

# Upload updated README.md
api.upload_file(
    path_or_fileobj='local/README.md',
    path_in_repo='README.md',
    repo_id='username/my-space',
    repo_type='space'
)
```

## Verification

After uploading, verify via live fetch:

```python
import urllib.request

url = 'https://huggingface.co/spaces/username/my-space/raw/main/index.html'
with urllib.request.urlopen(url, timeout=10) as r:
    html = r.read().decode()

# Check for anti-patterns
assert 'SpeechSynthesis' not in html  # no fake browser APIs

# Check for required sections
assert 'Model Details' in html
assert 'Usage' in html
assert 'Download' in html
```

## Anti-Patterns to Avoid

| Anti-pattern | Why it's bad | Fix |
|-------------|-------------|-----|
| Browser TTS as model demo | Misleads visitors about model quality | Showcase page with honest "no live demo" notice |
| Empty card | Wastes discovery potential | Add specs, code examples, cross-links |
| Single page with no navigation | Visitors bounce | Use sections/anchors for scannability |
| No family cross-links | Missed network effect | Table of sibling models with download counts |
| No link to actual model repo | Visitors can't download | Prominent "Download Model" button + badge |

## Cost

**$0.** Static Spaces are free to create, host, and maintain. No GPU, no compute, no PRO subscription needed.
