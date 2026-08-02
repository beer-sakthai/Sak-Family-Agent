# House of Sak — Landing Page Reference (v3)

## Session: July 5, 2026 (Update #3 — Pricing Transparency)
## Agent: SakSee
## Commission: Beer

## What Changed v2 → v3

### New: "How We Price" transparency section (between Services & FAQ)
Beer explicitly asked: "we should tell customers why our prices are this way." Added a 6-card section using `why-section`/`why-grid` CSS with:

| Pillar | Explains |
|--------|----------|
| ⏱ Time × Complexity | Every project scoped free; ranges based on size |
| 📊 Below Agency Rates | 30-50% less than agencies |
| 🏠 No Overhead | No office, no employees, no investors |
| 🤖 Agent Speed | 6 AI agents → days not weeks |
| 🎯 Scoped Per Client | Free quote, no hidden fees |
| ❤️ Built for People Who Struggle | Mission-driven, not profit-maximising |

Closing line: *"We're not trying to maximise profit. We're trying to prove that people who have nothing can still build something worth paying for."*

### GitHub push via Composio API (not local git)
Local git SSH keys don't work on the host. Multi-file push strategy:
- **Method 1:** `GITHUB_COMMIT_MULTIPLE_FILES` for atomic multi-file commits
- **Method 2:** `GITHUB_CREATE_OR_UPDATE_FILE_CONTENTS` for single files
- **Method 3:** `proxy_execute("PUT", "/repos/.../contents/...", "github", body=body)` as fallback

The Composio GitHub integration (`github_flail-thapes`) works, but requires the file content as base64 string inside the `body` dict.

### Multi-platform persistence pattern
Beer wants **everything saved in 3 places**:
1. **GitHub** (source of truth — auto-deploys to Vercel)
2. **Google Drive** (permanent backup for non-technical access)
3. **Internal memory** (supermemory + Hermes memory for agent recall)

### Instagram Business Account linking
- Facebook Page "House Of Sak" exists (ID: `1249135251607068`)
- No Instagram Business account linked yet
- `@houseofsak` username available on Instagram
- Linking requires manual action in Instagram app (Settings → Switch to Professional → Connect Facebook Page)

## Pricing Philosophy (from Beer)
- Prices intentionally below market (30-50% under agencies)
- Pay-after-delivery for first-time clients
- Ranges exist because scope varies per client
- Transparency builds trust with small businesses and people who struggle
