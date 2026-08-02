# Model Card Enrichment Workflow

Enrich all model cards in an HF account with consistent branding, family cross-links, benchmarks, and professional sections.

## PRE-FLIGHT: Narrative Consistency Audit

Before enriching, audit every public model card for narrative consistency. Fetch each card's README.md from the HF raw endpoint and check for these markers:

```python
import urllib.request
MODEL = "sakthai-context-7b-128k"
url = f"https://huggingface.co/Nanthasit/{MODEL}/raw/main/README.md"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=10) as resp:
    text = resp.read().decode("utf-8")

checks = {
    "narrative_house_of_sak":  "House of Sak" in text,
    "narrative_cork":          "shelter in Cork" in text,
    "narrative_six_agents":    "6 AI agents" in text,       # or "family of 6 AI agents"
    "narrative_beer_link":     "beer-sakthai" in text,      # GitHub profile link
    "family_badge":            "sakthai-model-family" in text or "SakThai%20Family" in text,
    "dynamic_download_badge":  "img.shields.io/endpoint" in text,
    "dataset_on_current":      "combined-v6" in text,       # not v5
}
```

Run this across ALL models (iterate by fetching the HF API model list) and identify the thinnest cards first. Fix gaps in priority order: cards with downloads get enriched first.

## Pre-Enrichment: Check for Broken Content

**HTML-in-code-block is a common bug.** Check every ```python block for embedded HTML tags:

```python
code_block = text.split("```python")[1].split("```")[0] if "```python" in text else ""
if any(tag in code_block for tag in ["<div","<h1","<h2","<img","<p>"]):
    print("❌ BROKEN: HTML embedded inside Python code block")
```

This happens when branding headers are accidentally inserted between code fences during card assembly. Fix by ensuring all branding HTML sits after the closing ```.

## Pattern

1. **Branding header** — Add "House of Sak" banner with profile + collection badges:
   ```html
   <div align="center">
     <img src="https://huggingface.co/Nanthasit/resolve/main/logo.png" alt="House of Sak" width="80"/>
     <h1>🏠 <a href="https://huggingface.co/Nanthasit">SakThai</a></h1>
     <p><em>Part of the <strong>House of Sak</strong> — 6 AI agents, one shared mind. Built from a shelter in Cork, Ireland.</em></p>
     <p>
       <a href="https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02">
         <img src="https://img.shields.io/badge/📦-View%20Family-8A2BE2" alt="Family"/>
       </a>
       <a href="https://huggingface.co/Nanthasit">
         <img src="https://img.shields.io/badge/🤗-Profile-6644cc" alt="Profile"/>
       </a>
       <a href="https://github.com/beer-sakthai">
         <img src="https://img.shields.io/badge/GitHub-beer--sakthai-181717?logo=github" alt="GitHub"/>
       </a>
     </p>
   </div>
   ```
   Note: HF may normalize this HTML on upload — the `<div align="center">` may be stripped or converted to `<h1 align="center">`. Check the live result, not just what you uploaded.

2. **Dynamic download badge** — Use `img.shields.io/endpoint` (NOT `img.shields.io/badge/dynamic/json`):
   ```markdown
   [![Downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fhuggingface.co%2Fapi%2Fmodels%2FNanthasit%2Fsakthai-context-7b-128k&query=%24.downloads&label=Downloads&color=blue)](https://huggingface.co/Nanthasit/sakthai-context-7b-128k)
   ```
   Better yet, use the shorter `img.shields.io/endpoint` format which renders more reliably:
   ```markdown
   ![Downloads](https://img.shields.io/endpoint?url=https://huggingface.co/api/models/Nanthasit/sakthai-context-7b-128k&label=downloads&color=blue&cacheSeconds=3600)
   ```

3. **Family cross-link table** — Every card gets a full table of all models with sizes, types, and dynamic download badges. See the 7b-merged enriched card for the reference template.

4. **Pipeline Integration section** — Add a Mermaid flowchart or ASCII pipeline diagram showing where this model fits in the inference pipeline (Embedding → Reasoning → Tool Execution → TTS). Include a stage reference table linking all sibling models.

5. **Benchmark comparison** — For LLM models, add a professional comparison vs similar-sized models using real published data (MMLU, BBH from papers) + your own BFCL tool-calling results

6. **Controlled comparison** — Run the base model side-by-side with your fine-tuned version on the same hardware

7. **Ollama guide** — Add Modelfile creation steps

8. **Hardware requirements** — RAM (min/recommended/disk) table

9. **Training details** — Method, base model, rank, dataset size, context length, dataset version

## Execution

```python
from huggingface_hub import HfApi
api = HfApi()

# Read the improved card
with open("/path/to/new_readme.md") as f:
    content = f.read()

# Upload
path = api.upload_file(
    path_or_fileobj=content.encode("utf-8"),
    path_in_repo="README.md",
    repo_id="Nanthasit/sakthai-context-7b-128k",
    repo_type="model",
)
print(f"Uploaded: {path}")
```

Iterate over ALL models under the author. Check for existing content before adding to avoid duplicates.

## POST-UPLOAD: Verification Checklist

**Always re-fetch the card after upload and verify.** HF's upload API may succeed while the rendered card differs from what you sent (HTML normalization, image URL resolution, etc.).

Re-run the narrative consistency audit checks and ensure:

| Check | What to verify |
|-------|---------------|
| Dynamic download badge | `img.shields.io/endpoint` renders in the fetched card |
| Family badge | Collection link present |
| "House of Sak" | Origin narrative present |
| "shelter in Cork" | Origin location present |
| "6 AI agents" | Family size stated |
| "beer-sakthai" | GitHub link present |
| Cross-links | At least 2 sibling models linked in table/stages |
| No broken code | ````python` blocks contain no `<div`, `<h1`, `<img`, `<p>` tags |
| Dataset version | References current dataset (e.g. `combined-v6`, not `v5`) |
| Logo | If included, verify `logo.png` URL resolves (it may 404 if not uploaded to HF) |

Use a script that fetches the raw card, runs all checks, and exits non-zero if any fail. This prevents "uploaded but didn't verify" situations.

## Pitfalls

- **Preserve YAML frontmatter** — always insert content AFTER the closing `---`
- **Don't re-upload unchanged cards** — verify the existing card first to avoid wasteful commits
- **`img.shields.io/endpoint` ≠ `img.shields.io/badge/dynamic/json`** — these are different URL patterns. The `endpoint` format is simpler and more reliable for HF download counts. Check which one your card actually uses.
- **Logo URL may 404** — uploading a `<img src="...logo.png">` doesn't create the file on HF. The logo must be separately uploaded to the HF account's `resolve/main/` path. If it 404s, the card still renders but shows a broken image.
- **HF normalizes HTML** — `<div align="center">` may be stripped. Test by fetching the raw card after upload, not by trusting your input file.
- **Use official tech report numbers** for comparison tables, not estimates
- **Spot-check every URL** after batch updates — a single broken badge degrades the whole card's professionalism
- **Dataset reference drift** — as datasets are updated (v5→v6→v7), model cards referencing old dataset versions become inconsistent. Always check for the current dataset version before enriching.
