# Verified OG Tag Behavior (2026-07-30)

Captured live from `https://huggingface.co/Nanthasit/sakthai-context-0.5b-tools`:

## Model page meta tags

```html
<meta name="description" content="We're on a journey to advance and democratize artificial
intelligence through open source and open science." />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:site" content="@huggingface" />
<meta name="twitter:image" content="https://cdn-thumbnails.huggingface.co/social-thumbnails/models/Nanthasit/sakthai-context-0.5b-tools.png" />
<meta property="og:title" content="Nanthasit/sakthai-context-0.5b-tools · Hugging Face" />
<meta property="og:description" content="We're on a journey to advance and democratize AI..." />
<meta property="og:type" content="website" />
<meta property="og:url" content="https://huggingface.co/Nanthasit/sakthai-context-0.5b-tools" />
<meta property="og:image" content="https://cdn-thumbnails.huggingface.co/social-thumbnails/models/Nanthasit/sakthai-context-0.5b-tools.png" />
```

## Key findings

1. **`og:description` is NOT customizable per repo** — always uses the generic HF site motto.
2. **Social thumbnail server:** `cdn-thumbnails.huggingface.co` with header `x-powered-by: hf-social-thumbnails`.
3. **Thumbnail file:** 422 KB PNG, cached 30 min (`s-maxage=1800`).
4. **Thumbnail URL pattern:** `https://cdn-thumbnails.huggingface.co/social-thumbnails/{type}/{author}/{repo}.png`
5. **`twitter:card`** is always `summary_large_image` (large image preview).
6. **`twitter:site`** is always `@huggingface`.

## Thumbnail HTTP headers

```
HTTP/2 200
content-type: image/png
content-length: 422494
cache-control: s-maxage=1800
x-powered-by: hf-social-thumbnails
```

## Unverified (needs testing)

- Whether the `thumbnail:` YAML field overrides the auto-generated `og:image`
- Whether Spaces pages have different OG tag behavior
- Whether dataset pages (which can be gated) have the same tag structure
