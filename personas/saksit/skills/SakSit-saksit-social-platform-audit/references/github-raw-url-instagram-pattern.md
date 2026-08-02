# GitHub Raw URL — Instagram Pattern

Using `raw.githubusercontent.com` URLs as Instagram media sources.

## Why
- Instagram's API rejects URLs with query strings
- GitHub's raw CDN serves clean HTTPS URLs with no query params
- Files committed to `beer-sakthai/house-of-sak` are instantly available

## Pattern
```
https://raw.githubusercontent.com/beer-sakthai/house-of-sak/main/<path>
```

## Limitations
- CDN delay: ~30-60s before `content-type` header becomes `image/png`
- If Instagram returns "image format not supported", wait and retry
