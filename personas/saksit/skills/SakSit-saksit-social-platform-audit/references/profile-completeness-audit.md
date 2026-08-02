# Profile Completeness Audit

After discovering connected platforms and pulling identity data, run a
**profile completeness check** to see what's filled, what's missing, and what
can be updated via available tools vs manually.

## Completeness Matrix Template

For each platform, map these fields:

| Field | Meaning | Instagram | LinkedIn | Facebook | YouTube | Reddit | HF |
|-------|---------|-----------|----------|----------|---------|--------|----|
| ✅ Name | Display name | username | fullname | page name | channel name | username | fullname |
| ✅ Bio | Description text | bio text | headline/about | description | description | public_desc | bio |
| ✅ Website | Link URL | website field | profile link | website field | links | — | homepage field |
| ✅ Profile pic | Avatar | profile_pic | profile_pic | picture | thumbnail | icon_img | avatar |
| ✅ Cover/banner | Header image | — | — | cover | banner | banner_img | — |
| ✅ Social links | GitHub/LI/Twitter | — | — | — | links | — | signup links |

## Real Audit Results (2026-07-06)

### Instagram (@beerthaish)

| Field | Value | Can Update via Tool? |
|-------|-------|:-------------------:|
| Username | `beerthaish` | — |
| Bio | ✅ "My name Is Beer. 🇹🇭 Living in Cork..." | ❌ No Instagram profile-update tool in Composio |
| Website | ❌ **Empty** | ❌ No tool |
| Profile pic | ✅ Set | ❌ No tool |
| Account type | MEDIA_CREATOR | — |

### LinkedIn (Nanthasit Burankum)

| Field | Value | Can Update via Tool? |
|-------|-------|:-------------------:|
| Name | ✅ Nanthasit Burankum | — |
| Headline | ❓ Not visible from API | ❌ No profile-edit tool |
| About | ❓ Not visible from API | ❌ No profile-edit tool |
| Profile pic | ✅ Set | ❌ No tool |
| Website | ❓ Not visible from API | ❌ No tool |

### Facebook (House Of Sak Page)

| Field | Value | Can Update via Tool? |
|-------|-------|:-------------------:|
| Page name | ✅ House Of Sak | — |
| Category | ✅ Local business | — |
| Description | ❌ **Empty** | ✅ `FACEBOOK_UPDATE_PAGE_SETTINGS(description=...)` |
| Website | ❌ **Empty** | ✅ `FACEBOOK_UPDATE_PAGE_SETTINGS(website=...)` |
| About | ❌ Empty | ✅ `FACEBOOK_UPDATE_PAGE_SETTINGS(about=...)` |
| Profile pic | ❌ **Default silhouette** | ❌ No image-update tool |
| Permissions | ✅ MANAGE, CREATE_CONTENT | ✅ Can update settings |

### YouTube (@nanthasitburankum)

| Field | Value | Can Update via Tool? |
|-------|-------|:-------------------:|
| Channel name | ✅ Nanthasit Burankum | — |
| Description | ❌ **Empty** | ✅ `YOUTUBE_UPDATE_CHANNEL(brandingSettings={channel:{description:...}})` |
| Channel art | ❌ Not set | ❌ No tool |
| Avatar | ✅ Default Google pic | ❌ No tool |
| Keywords | ❌ Not set | ✅ `YOUTUBE_UPDATE_CHANNEL(brandingSettings={channel:{keywords:...}})` |
| Links | ❌ None | ❌ No tool |
| Subscribers | 0 | — |
| Videos | 0 | ❌ No upload tool |

### Hugging Face (Nanthasit)

| Field | Value | Can Update via Tool? |
|-------|-------|:-------------------:|
| Name | ✅ Nanthasit Burankum | — |
| Bio | ❌ **Empty** | ❌ No API — must use hf.co/settings/profile |
| Website | ✅ https://house-of-sak.vercel.app/ | Already set via signup |
| GitHub | ✅ beer-sakthai | Already set |
| LinkedIn | ❌ Empty | ❌ No API |
| Twitter/X | ❌ Empty | ❌ No API |
| Bluesky | ❌ Empty | ❌ No API |
| Status | ✅ "In a Training Loop" 🔄 | Set via HF web |
| AI & ML interests | ❌ "None yet" | Must set via HF web |

### Reddit (u/Then-Chest-8704)

| Field | Value | Can Update via Tool? |
|-------|-------|:-------------------:|
| Username | ✅ Then-Chest-8704 | — |
| Link karma | **1** | — |
| Comment karma | 0 | — |
| Public description | ❌ Empty | ❌ No profile-edit tool |
| Avatar | ❌ Default Reddit avatar | ❌ No tool |

## Update Priority by Impact

| Priority | Platform | Action | Tool |
|:--------:|----------|--------|------|
| 🥇 | Facebook | Add website + description | `FACEBOOK_UPDATE_PAGE_SETTINGS` |
| 🥇 | YouTube | Add channel description | `YOUTUBE_UPDATE_CHANNEL` |
| 🥈 | Instagram | Add website to bio | Manual (no API) |
| 🥈 | Hugging Face | Add bio + LinkedIn link | Manual (hf.co/settings/profile) |
| 🥉 | LinkedIn | Update headline/about | Manual (linkedin.com) |
| 🥉 | Reddit | Build karma first | Organic engagement |

## Template for Reporting

Use this format when presenting completeness findings:

```
## Current Social Profile Audit

### 🔵 LinkedIn — Nanthasit Burankum
| Field | Status |
|-------|--------|
| Name | ✅ Set |
| Profile pic | ✅ Set |
| Headline | ❓ Not visible |
| About | ❓ Not visible |

### 🟣 Instagram — @beerthaish
| Field | Status |
|-------|--------|
| Bio | ✅ "..." |
| Profile pic | ✅ Set |
| Website | ❌ Empty |
```

## Key Insight

The **most updatable platform** is Facebook Page (website, description, about all
editable via `FACEBOOK_UPDATE_PAGE_SETTINGS`). YouTube is second (description
via `YOUTUBE_UPDATE_CHANNEL`). Instagram and Hugging Face require manual web
editing. Reddit needs karma before any profile updates matter.
