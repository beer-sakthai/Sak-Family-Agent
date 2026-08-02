# House of Sak — Full Sak Cycle Update Case Study

**Date:** July 6, 2026
**Cycle:** Round 2 (improvement pass on the live site)
**Agent:** SakSee
**Commissioned by:** Nanthasit "Beer" Burankum

## Context

The first House of Sak cycle produced a live landing page, business plan, and service docs. This second pass was triggered when Beer asked for an update and then requested all phases of the improvement plan be processed, with mistakes recorded so they would not repeat.

## What changed

### Docs
- `PLAN.md` was merged into `plan.md` (duplicate removed).
- `plan.md` retained EUR pricing consistent with the live site.
- `design.md` updated to include new SEO/trust features.
- Created `_summaries` directory in diaries to organize reports.

### Site (`index.html`)
| Addition | Purpose |
|----------|---------|
| Dynamic days counter | Replaced hardcoded "82" with JS-calculated days since April 15, 2026 |
| Fixed `og:url` | Changed from `https://houseofsak.ie` to `https://house-of-sak.vercel.app/` |
| Nav links `#why` / `#pricing` | Complete section coverage in nav |
| Verified profile badge row | Show profiles in "Why Us" section, not just footer |
| Scope at a Glance | Prevents scope creep by clearly stating included/not-included per service |
| First Client Offer banner | 20% off for first public case study |
| Sak Cycle flow | Visual stage chain in "How It Works" |
| As Seen On | Social proof placeholders |
| Case Studies | Empty-state section ready for first project |
| Stories & Reports | Showcase origin stories and technical reports |
| Crisis protocol link | Footer note linking to `CRISIS.md` |
| Lead-capture form | Email form in contact section |

## Commits
- `9bdaca14ae6edf920a0ec99ce2896efc265778c3` — site + docs sync
- `d28b12abfcbca09c3bf2ba043476f98742f4d04d` — remove duplicate `PLAN.md`
- `[new commit]` — add Stories & Reports section and diaries summaries

## Workflow corrections recorded

### Anticipate before asking
When Beer asks "check repo X for Y", read the files and compare them first, then answer. The follow-up question "Every time ask why I told you where or what? Think about what is for checking it first" became a communication rule.

### Use direct Composio MCP HTTP for file commits
During Round 1, passing placeholder text into `GITHUB_COMMIT_MULTIPLE_FILES` corrupted `index.html` with a git diff stat. Round 2 used the JSON-RPC/SSE endpoint at `https://connect.composio.dev/mcp` with variable-resolved base64/utf-8 content and verified via `curl https://raw.githubusercontent.com/...` after every push.

### Save mistakes to memory at Growth stage
The user explicitly required every cycle end with a report + memory save. The final memory update included:
- Correct local checkout path (`/opt/data/house-of-sak-report`, not `/opt/data/house-of-sak`).
- Composio corruption mistake.
- Verified profile URLs verbatim.
- Full cycle execution report.

## Verification checklist (Trust stage)
- [x] Live site returns 200
- [x] All new sections present in DOM
- [x] All 4 verified profile URLs reachable (200 HEAD)
- [x] `plan.md` and `design.md` present on GitHub `main`
- [x] Duplicate `PLAN.md` deleted (API 404)
- [x] `robots.txt` and `sitemap.xml` unchanged and present

## Lessons
- **Check assumptions about local paths.** A checkout can be renamed while the repo name stays the same.
- **Distinguish raw GitHub cache from actual deletion.** After deleting `PLAN.md`, the raw CDN briefly still served the file. Use the GitHub API for authoritative state.
- **One `index.html` replacement is safer than many small patches.** Doing all HTML edits in a single Python transform reduces the chance of partial matches breaking the page.
- **Document currency in one source of truth.** The site, `SERVICES.md`, and `plan.md` all use EUR. Any future USD mention is a bug.
