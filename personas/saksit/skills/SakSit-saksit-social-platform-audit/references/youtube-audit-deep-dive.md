# YouTube Platform Deep-Dive

A subordinate audit to run when the user asks about YouTube specifically
(e.g. "what can you do in youtube?" or "plan youtube strategy").

## YouTube Tool Capabilities (via Composio)

| Capability | Available? | Tool |
|------------|:----------:|------|
| Search videos/channels | ✅ | `YOUTUBE_SEARCH_YOU_TUBE` |
| List channel videos | ✅ | `YOUTUBE_LIST_CHANNEL_VIDEOS` |
| Batch video details | ✅ | `YOUTUBE_GET_VIDEO_DETAILS_BATCH` (up to 50 IDs) |
| Get channel stats | ✅ | `YOUTUBE_GET_CHANNEL_STATISTICS` |
| Check captions | ✅ | `YOUTUBE_LIST_CAPTION_TRACK` |
| Read comments | ✅ | `YOUTUBE_LIST_COMMENT_THREADS2` |
| Create playlist | ✅ | `YOUTUBE_CREATE_PLAYLIST` |
| Post comment | ✅ | `YOUTUBE_POST_COMMENT` |
| Update channel description | ✅ | `YOUTUBE_UPDATE_CHANNEL` |
| **Upload video** | ❌ | Not in current Composio toolkit |
| **Edit video metadata** | ❌ | No update tool |
| **Channel banner/art** | ❌ | Not in current toolkit |

## YouTube Audit Workflow

### Step 1 — Channel baseline

```python
YOUTUBE_GET_CHANNEL_STATISTICS(
  id="UChLpu5PVljj2v9_fBMsUS4A",
  part="statistics,snippet,brandingSettings"
)
```

Check: subscriberCount, videoCount, viewCount, description, brandingSettings.channel.

### Step 2 — List existing content

```python
YOUTUBE_LIST_CHANNEL_VIDEOS(
  mine=true,
  maxResults=50
)
```

If items is empty (0 videos), channel is a blank slate.

### Step 3 — Competitor & trend research

Search the niche with multiple queries in parallel:

```python
YOUTUBE_SEARCH_YOU_TUBE(q="relevant query", maxResults=5, order="relevance", type="video")
```

Switch `order` to "date" to see recent content, "viewCount" for top performers.
Use `relevanceLanguage` and `regionCode` to narrow by market.

### Step 4 — Deep-dive on competitor videos

```python
YOUTUBE_GET_VIDEO_DETAILS_BATCH(
  id=["videoId1","videoId2"],
  parts=["snippet","statistics"]
)
```

Extract: title patterns, description structure, tag usage, view/like/comment ratios.

### Step 5 — Read audience sentiment

```python
YOUTUBE_LIST_COMMENT_THREADS2(
  videoId="...",
  part="snippet,replies",
  maxResults=20,
  order="relevance"
)
```

Common questions and pain points in comments = content ideas for your own channel.

## YouTube-Specific Findings (2026-07-06)

**Channel @nanthasitburankum:**
- Created 2026-05-03
- 0 subscribers, 0 videos, 0 views
- Empty description, default avatar
- No branding settings

**AI Agent content landscape:**
- Highly competitive (Zinho ~289K, Futurepedia ~750K, Liam Ottley ~508K)
- All focus on "no-code" tutorials and sponsored tool reviews
- NOBODY shows the real Hermes/Composio tool stack
- NOBODY combines founder story + technical depth
- Gap: authentic, story-driven AI agent content from a developer's perspective

**All searches return 1M+ results** — the audience demand is real.

## YouTube Strategy Framework

| Phase | What | Who Does It |
|-------|------|-------------|
| 1. Channel setup | Description, avatar, banner, links | Beer (in YouTube Studio) |
| 2. Content pillars | (a) Agent building tutorials, (b) Origin story, (c) Tips & tools | Plan together |
| 3. Production | Record screen/face, edit | Beer |
| 4. Upload & metadata | Titles, descriptions, tags, thumbnails | Beer uploads; I write metadata |
| 5. Engagement | Reply to comments, community building | I can comment via API |

## Known Gaps

- I can prepare SEARCH strategy, TITLE analysis, DESCRIPTION text, and TAG research
- I can post COMMENTS on other channels to build presence
- I CANNOT upload videos, edit video metadata, or manage live streams
- The channel needs **at least 1 video** uploaded before playlists are useful
