# Real Platform Audit — 2026-07-06

This is the output from the first-ever full platform audit performed on July 6, 2026.
Use as a reference for what a complete audit looks like.

## COMPOSIO_SEARCH_TOOLS Results

**Platforms discovered: 4**

| Toolkit | Connection | Account | Status |
|---------|-----------|---------|--------|
| facebook | Active | Beer Cork (ID: 122118580424916082) | House Of Sak Page |
| instagram | Active | @beerthaish (ID: 27647006041564332) | MEDIA_CREATOR |
| linkedin | Active | Nanthasit Burankum (URN: GR_0y0zfGl) | Person profile |
| reddit | Active | u/Then-Chest-8704 (ID: cgsrqi4t) | 1 karma total |

## Parallel Identity Pull Results

**Instagram:**
- Username: beerthaish
- Account type: MEDIA_CREATOR
- Followers: 906 | Following: 570 | Posts: 26
- Bio: Thai in Cork, Ireland
- Daily publish quota: 0 used / 100 total

**LinkedIn:**
- Name: Nanthasit Burankum
- ID: GR_0y0zfGl
- Profile picture URL available

**Facebook:**
- Page: House Of Sak (ID: 1249135251607068)
- Category: Local business
- Permissions: ADVERTISE, ANALYZE, CREATE_CONTENT, MESSAGING, MODERATE, MANAGE
- Link: https://www.facebook.com/1249135251607068

**Reddit:**
- Username: Then-Chest-8704
- Link karma: 1 | Comment karma: 0
- Account created: 2021-06-01
- Verified email: yes
- Reddit age: ~5 years but minimal activity

## Pros/Cons Analysis

### LinkedIn
✅ Full person profile, immediate posting ability
✅ 3000 char limit, up to 20 images, CTA buttons
✅ Visibility control (PUBLIC, CONNECTIONS, CONTAINER)
✅ Best fit for origin story, career pivot, thought leadership
❌ distribution field REQUIRED in post body (422 if missing)
❌ No video in the basic post tool
❌ Targeting requires 300+ min audience

### Instagram
✅ 906 real followers — existing audience
✅ 0/100 daily quota — full capacity
✅ Media Creator account — supports Reels, carousels, images
❌ 2-step publish (create container → wait FINISHED → publish)
❌ Public HTTPS URL required — S3 signed URLs fail
❌ 25 API posts/day hard limit

### Facebook
✅ House Of Sak Page created, full manage permissions
✅ Can schedule posts with timestamp
✅ Audience targeting available
❌ Text/link only in basic post tool
❌ 0 followers shown — cold start
❌ Organic reach ~2-5% on Pages

### Reddit
❌ 1 total karma — can't post in most useful subreddits
❌ AutoModerator silently removes self-promotion
❌ Reddit users hostile to brand/self-promotion
❌ Risk of account ban if posted too aggressively
⚠️ Account is 5 years old but dormant — could build karma over time

## Tiered Strategy

```
Tier 1 — Ship Now:     LinkedIn
Tier 2 — Build First:  Instagram (solve URL constraint)
Tier 3 — Cross-Post:   Facebook (after content exists)
Tier 4 — Later:        Reddit (earn karma first)
```

## Lessons Learned

1. A connected toolkit ≠ a usable platform. Reddit was connected but unusable.
2. Always check rate limits before planning volume (Instagram: 25/day API cap).
3. Identity resolution can surprise you — verify what account the connection maps to.
4. "don't sure don't forget but learn from that" — document what you find.
5. Diary convention for this project: `/opt/data/house-of-sak/diaries/<agent-name>/<date>.md` — commit via Composio GitHub API (`GITHUB_COMMIT_MULTIPLE_FILES`) since local git auth isn't configured. Verify with `curl -s https://raw.githubusercontent.com/beer-sakthai/house-of-sak/main/diaries/<agent-name>/<date>.md | head -5`.
