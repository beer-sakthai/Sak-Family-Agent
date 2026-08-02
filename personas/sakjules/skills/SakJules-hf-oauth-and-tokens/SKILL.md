---
name: SakJules-SakThai-hf-oauth-and-tokens
description: ">   Complete reference on Hugging Face Hub authentication — User Access Tokens   (fine-grained, read, write), OAuth 2.0 / OpenID Connect flows (authorization   code, device code, PKCE), Spaces OAuth integration, Token Exchange for   Organizations (RF"
---

# HF Hub OAuth & Token Management

## What This Covers

All authentication mechanisms on the Hugging Face Hub:

| Mechanism | Best For |
|-----------|----------|
| **User Access Tokens** | Scripts, notebooks, CLI tools |
| **OAuth 2.0 / OIDC** | Web apps, CLIs ("Sign in with HF") |
| **Device Code OAuth** | Headless/CLI environments |
| **Token Exchange (RFC 8693)** | Enterprise: issue tokens for org members programmatically |
| **Trusted Publishers** | CI/CD pipelines — no HF_TOKEN secret |
| **Spaces OAuth** | Built-in sign-in for Gradio/Spaces |

## Quick Reference

### Token Types

- **fine-grained**: Scoped to specific repos/orgs — safest for production
- **read**: All repos you can read (public + private)
- **write**: Read + write access to repos you have access to

### OAuth Endpoints

| Action | Endpoint |
|--------|----------|
| Authorize | `GET https://huggingface.co/oauth/authorize` |
| Token | `POST https://huggingface.co/oauth/token` |
| Device code | `POST https://huggingface.co/oauth/device` |
| WhoAmI | `GET https://huggingface.co/api/whoami-v2` |
| OpenID config | `GET https://huggingface.co/.well-known/openid-configuration` |

### Supported OAuth Scopes

`openid`, `profile`, `email`, `read-billing`, `read-repos`, `gated-repos`,
`contribute-repos`, `write-repos`, `manage-repos`, `read-collections`,
`write-collections`, `inference-api`, `jobs`, `webhooks`, `write-discussions`

### Key Docs

- Tokens: https://huggingface.co/docs/hub/en/security-tokens
- OAuth: https://huggingface.co/docs/hub/en/oauth
- Trusted Publishers: https://huggingface.co/docs/hub/en/trusted-publishers
- Spaces OAuth: https://huggingface.co/docs/hub/en/spaces-oauth
- Settings (tokens): https://huggingface.co/settings/tokens
- Settings (OAuth apps): https://huggingface.co/settings/applications/new
- OpenID metadata: https://huggingface.co/.well-known/openid-configuration

For the full deep-dive with code examples see `references/hf-learnings.md`.
