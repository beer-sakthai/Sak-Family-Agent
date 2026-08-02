# Hugging Face Profile Audit & Constraints

## Accessing Profile Data

**Via API (read-only, requires HF_TOKEN):**
```python
GET https://huggingface.co/api/whoami-v2
Authorization: Bearer $HF_TOKEN
```
Returns: id, name, fullname, email, avatarUrl, isPro, orgs[], bio, websiteUrl, signup (github, homepage, linkedin, twitter, bluesky, details)

**Via browser:**
Navigate to `https://huggingface.co/<username>` — the page HTML contains a JSON blob with all profile data including the `signup` object and `u` user metadata.

## Current Profile State (Beer — 2026-07-06)

| Field | Value | Editable? |
|-------|-------|:---------:|
| Username | Nanthasit | — |
| Fullname | Nanthasit Burankum | — |
| Website | https://house-of-sak.vercel.app/ ✅ | Set via signup form |
| GitHub | beer-sakthai ✅ | Set via signup form |
| Bio | **Empty** | ❌ No API — manual only |
| LinkedIn | Empty | ❌ No API |
| Twitter/X | Empty | ❌ No API |
| Bluesky | Empty | ❌ No API |
| Details | Empty | ❌ No API |
| AI & ML interests | "None yet" | ❌ Must set via web |
| Status | "In a Training Loop" 🔄 | Set via HF web |
| Organization | litert-community (contributor) | — |
| Followers | 6 | — |
| Models | 9 | — |
| Datasets | 6 | — |

## Update Capability

**Can NOT update via API or tools:**
- Hugging Face offers no public REST/PATCH endpoint for profile edits (browser-based bot detection blocks automation)
- The `/settings/profile` page is behind CloudFront WAF — automated browsers get 403
- No Composio toolkit exists for Hugging Face at all

**Manual updates required at:** https://huggingface.co/settings/profile
- Bio text (1000 char max)
- AI & ML interests (comma-separated tags)
- Social links (GitHub, LinkedIn, Twitter/X, Bluesky)
- Avatar image
- Profile status/emoji

## API Endpoints Tried (all failed for write)

| Endpoint | Method | Result |
|----------|--------|--------|
| `/api/settings` | POST/PATCH/PUT | 404 |
| `/api/users/Nanthasit` | PUT/PATCH | 404 |
| `/api/users/Nanthasit/profile` | PUT/PATCH | 404 |
| `/api/users/Nanthasit/settings` | GET/PUT | 404 |
| `/api/whoami-v2` | PATCH | 404 |
| `/api/gql` | POST | 404 (GraphQL attempt) |
| `/api/organizations/litert-community` | GET | 404 |
| `/api/orgs/litert-community` | GET | 404 |

## Key Insight

Hugging Face is the **only platform** where the website link was already set correctly (house-of-sak.vercel.app) before any audit. The bio and social links are the gaps — but they require manual login by Beer to update.
