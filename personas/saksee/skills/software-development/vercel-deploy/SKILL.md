---
name: vercel-deploy
description: Deploy static sites and manage projects on Vercel.
category: software-development
tags: [vercel, deployment, static-site]
---

# Vercel Deploy

Deploy static sites to Vercel via Composio or git push.

## Methods

### Git Push (Recommended)

For repos with Vercel integration:
1. Push to `main` branch
2. Vercel auto-detects and deploys
3. URL: `<project>.vercel.app`

### API Deploy (via Composio)

```
VERCEL_CREATE_PROJECT2 → VERCEL_CREATE_NEW_DEPLOYMENT → VERCEL_GET_DEPLOYMENT
```

Files sent inline as `data` field (text or base64 for large files).

## Pitfalls

- Project names must be lowercase, alphanumeric + `.-_`
- `skipAutoDetectionConfirmation: "1"` for static sites
- Free tier: 100GB bandwidth, 6K build min/month
- Two Vercel accounts possible — use the most recent active one
