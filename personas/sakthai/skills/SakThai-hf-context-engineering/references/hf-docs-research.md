# Researching Hugging Face Documentation

HF docs are built with SvelteKit — the rendered HTML is a client-side SPA shell with no actual content in the server response. **Don't curl the HTML pages.** Use the raw markdown source instead.

## Raw Markdown URL Pattern

```
https://huggingface.co/docs/<library>/<lang>/<page>.md
```

### Examples

| Rendered page | Raw markdown |
|---|---|
| `https://huggingface.co/docs/peft/en/index` | `https://huggingface.co/docs/peft/en/index.md` |
| `https://huggingface.co/docs/peft/en/quicktour` | `https://huggingface.co/docs/peft/en/quicktour.md` |
| `https://huggingface.co/docs/datasets/en/index` | `https://huggingface.co/docs/datasets/en/index.md` |
| `https://huggingface.co/docs/transformers/en/index` | `https://huggingface.co/docs/transformers/en/index.md` |
| `https://huggingface.co/docs/inference-providers/en/index` | `https://huggingface.co/docs/inference-providers/en/index.md` |

## How to Find the Markdown Link

The rendered HTML includes a `<link>` tag with the markdown source URL:

```html
<link rel="alternate" type="text/markdown" href="/docs/peft/en/index.md"/>
```

But it's faster to just append `.md` directly — the pattern is consistent.

## Fetching

```bash
# Quick peek (first 300 lines)
curl -sL "https://huggingface.co/docs/peft/en/quicktour.md" | head -300

# Full content
curl -sL "https://huggingface.co/docs/peft/en/quicktour.md"

# Multiple pages in parallel
curl -sL "https://huggingface.co/docs/peft/en/quicktour.md" \
     -sL "https://huggingface.co/docs/peft/en/package_reference/lora.md"
```

## When This Is Useful

- Researching a new HF library or feature for skill creation
- Extracting code snippets, API signatures, or configuration patterns
- Verifying current docs content without browser JavaScript
- Building reference files for skills

## ⚠️ Single-Page Doc Bundles

Some HF doc projects bundle all content into a single `index.md` — sub-pages like `quick-start.md` do **not** exist as separate files and return 404. Verified examples:

| Doc project | Sub-page `.md` exist? |
|---|---|
| `inference-providers/en/index.md` | ✅ Yes — full content |
| `inference-providers/en/quick-start.md` | ❌ 404 — embedded in `index.md` |

**How to detect:** If `<link rel="alternate" type="text/markdown" href=".../index.md"/>` exists but a sub-page URL returns a 404 page saying "No markdown available for <url>", the docs are a single-page bundle. Fall back to fetching `index.md` — it contains everything.

## ⚠️ Cookbook Exception

The [HF Open-Source AI Cookbook](https://huggingface.co/learn/cookbook) is also a SvelteKit SPA, but **individual recipe pages do NOT expose raw markdown** via the `.md` pattern:

| Page | `.md` access |
|------|-------------|
| `/learn/cookbook/index.md` | ✅ Works — returns index |
| `/learn/cookbook/grpo_vllm_online_training/index.md` | ❌ 404 — "No markdown available" |

The index page raw markdown is available and lists all recipe slugs. For individual recipe notebooks, use the [GitHub repo](https://github.com/huggingface/cookbook) instead — the `.ipynb` files live there.

**Workaround:** Fetch `/learn/cookbook/index.md` to get the recipe listing, then find the corresponding `.ipynb` in the GitHub repo by matching the recipe slug to the filename.

## Limitations

- Not all pages have a `.md` variant — some are fully client-side rendered (rare, mostly dynamic pages like search results)
- Redirects: some old URLs redirect to new ones; follow the redirect and append `.md` to the final URL
- Rate limits: HF doesn't aggressively rate-limit markdown fetches, but add a small delay between bulk requests
