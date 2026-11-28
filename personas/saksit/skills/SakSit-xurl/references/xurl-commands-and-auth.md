# xurl Commands & Authentication Reference Guide

Comprehensive guide for the official X/Twitter developer CLI (`xurl`).

## 1. Authentication & Security Guardrails
- **Secret Zero-Exposure**: Never print, inspect, or summarize `~/.xurl`. Never pass inline credentials via `--bearer-token` or `--consumer-key`.
- Verify authentication status via `xurl auth status`.
- OAuth 2.0 PKCE tokens auto-refresh in `~/.xurl`.

## 2. Core CLI Commands
| Action | Command |
|---|---|
| Post text | `xurl post "Your post content here"` |
| Reply | `xurl post --reply-to <POST_ID> "Your reply text"` |
| Quote post | `xurl post --quote <POST_ID> "Commentary here"` |
| Delete post | `xurl delete post <POST_ID>` |
| Like post | `xurl like <POST_ID>` |
| Repost | `xurl repost <POST_ID>` |
| Search recent | `xurl search "python query" --limit 10` |
| User timeline | `xurl timeline <USERNAME> --limit 10` |
| Mentions | `xurl mentions --limit 10` |

## 3. Media Uploads
```bash
# Upload image and attach to post
MEDIA_ID=$(xurl media upload path/to/image.png | jq -r '.data.id')
xurl post "Check out this visual artifact!" --media-ids "$MEDIA_ID"
```

## 4. Raw API Access
Execute raw API v2 calls directly:
```bash
xurl api get /2/users/by/username/sakthai
xurl api post /2/tweets -d '{"text": "Automated update"}'
```
