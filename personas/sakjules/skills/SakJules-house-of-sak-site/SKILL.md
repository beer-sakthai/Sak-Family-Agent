---
name: SakJules-SakSee-house-of-sak-site
description: "Manage the House of Sak landing page and repo \u2014 update sections, services, pricing,\
  \ and push to GitHub \u2192 Vercel auto-deploy."
---

# House of Sak Site Management

Manage the `house-of-sak` repository at `/opt/data/house-of-sak/`.

## Repo Info

- **Local path:** `/opt/data/house-of-sak/`
- **GitHub:** `beer-sakthai/house-of-sak`
- **Vercel:** `house-of-sak.vercel.app` (auto-deploys from `main`)
- **Branch:** `main`

## Site Sections
| # | Section | ID | Description |
|---|---------|-----|-------------|
| 1 | Story | `#story` | Origin — shelter in Cork |
| 2 | Agents | `#agents` | 6 Sak agents |
| 3 | Process | `#process` | Full Sak Cycle |
| 4 | Services | `#services` | Service cards |
| 5 | Pricing | `#pricing` | How We Price |
| 6 | FAQ | `#faq` | FAQ accordion |
| 7 | CTA | `#contact` | Call to action + crisis footer |

## Services
| Package | Price |
|---------|-------|
| QA Shield | €200–€500 |
| Agent Builder | €300–€800 |
| Social Pulse | €100–€300/mo |
| Fast Prototype | €150–€400 |
| Trust Check | €150–€300 |
| Full House | €600–€1,600 |

## Key Files
- `index.html` — landing page (1,476 lines)
- `SERVICES.md` — packages
- `CRISIS.md` — crisis protocol

## Pitfalls
- Don't push internal reports to GitHub
- index.html is the only production file
- Vercel auto-deploys from main
