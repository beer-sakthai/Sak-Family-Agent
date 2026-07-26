# HF Learnings Log — hf-hub-daily-papers-and-paper-pages (Deep Dive)

## 2026-07-25: Hugging Face Hub — Daily Papers & Paper Pages API and Ecosystem Deep Dive

### Summary
Deep-dive into the Hugging Face Daily Papers and Paper Pages ecosystem — the API
endpoints, data structures, linking mechanism, discussion system, authorship
claims, paper indexing, and programmatic discovery patterns. This is the complete
reference for navigating and interacting with HF's paper infrastructure at the
API level.

Research was conducted by live querying the daily papers API
(`/api/daily_papers`), the paper detail API (`/api/papers/{id}`), the paper
search/browse API (`/api/papers?`), and by inspecting the Svelte-rendered paper
page HTML (`/papers/{id}`) for embedded state.

### Key Findings

---

#### 1. API Surface Overview

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/daily_papers` | GET | List papers submitted to Daily Papers (default: latest 50, sorted by submission date descending) | None |
| `/api/daily_papers?date=YYYY-MM-DD` | GET | Filter daily papers by submission date | None |
| `/api/papers/{arxivId}` | GET | Full paper detail with linked artifacts | None |
| `/api/papers?search={query}` | GET | Search papers by title/author (returns 3 results max) | None |
| `/api/papers?sort=publishedAt` | GET | Browse papers sorted by publication date | None |
| `/api/papers?sort=upvotes` | GET | Browse papers sorted by upvote count | None |
| `/api/papers?limit=N` | GET | Control result count (unlimited for browse, 3 max for search) | None |
| `hf.co/papers/{arxivId}` | Web | Paper page UI (HTML with Svelte-embedded data) | None |

**Key limitation**: The search endpoint returns at most 3 results. No pagination
or offset parameter is supported for paper search. The daily_papers endpoint
returns 50 entries max.

---

#### 2. Daily Papers API (`/api/daily_papers`)

**Default response**: Array of paper objects, sorted by submission date
descending (most recent first). Each entry has:

```json
{
  "paper": {
    "id": "2607.21557",
    "title": "OpenForgeRL: Train Harness-native Agents in Any Environment",
    "authors": [
      {
        "_id": "6a63a8cbab9cdf9be5794456",
        "name": "Xiao Yu",
        "hidden": false
      }
    ],
    "publishedAt": "2026-07-23T00:00:00.000Z",
    "submittedOnDailyAt": "2026-07-24T00:00:00.000Z",
    "submittedOnDailyBy": {
      "_id": "61942296d5c2ba6daa290357",
      "fullname": "Baolin Peng",
      "user": "Baolin",
      "type": "user",
      "isPro": false,
      "followerCount": 4
    },
    "summary": "Full abstract text...",
    "upvotes": 5,
    "discussionId": "6a63a8ccab9cdf9be579446a",
    "organization": {
      "_id": "5e6485f787403103f9f1055e",
      "name": "microsoft",
      "fullname": "Microsoft",
      "avatar": "https://cdn-avatars.huggingface.co/..."
    }
  },
  "publishedAt": "2026-07-22T20:00:00.000Z",
  "title": "OpenForgeRL: Train Harness-native Agents in Any Environment",
  "summary": "Short description for listing",
  "thumbnail": "https://cdn-thumbnails.huggingface.co/social-thumbnails/papers/2607.21557.png",
  "numComments": 2,
  "submittedBy": { "fullname": "Baolin Peng", "user": "Baolin", "type": "user" },
  "organization": { "name": "microsoft", "fullname": "Microsoft" },
  "isAuthorParticipating": false
}
```

**Key fields**:
- `paper.id` — ArXiv ID (e.g., `2607.21557`)
- `paper.publishedAt` — original ArXiv publication date
- `paper.submittedOnDailyAt` — when submitted to Daily Papers (use `?date=` filter)
- `paper.submittedOnDailyBy` — the HF user who submitted the paper
- `paper.upvotes` — upvote count
- `paper.discussionId` — internal ID for the paper's discussion thread
- `paper.organization` — affiliate organization (not always present)
- `numComments` — count of discussion comments
- `thumbnail` — social share thumbnail URL (CDN-hosted)
- `isAuthorParticipating` — whether paper authors are active in discussion

**Date filtering**:
```
GET /api/daily_papers?date=2026-07-24
```
Returns all papers submitted on that specific day. This is the limit of date
filtering — no date range, no `before`/`after` params.

---

#### 3. Paper Pages API (`/api/papers/{arxivId}`)

**Full paper detail endpoint**. Returns everything from daily_papers plus:

```json
{
  "id": "2607.16859",
  "title": "Dataset Distillation by Influence Matching",
  "authors": [ ... ],
  "publishedAt": "2026-07-18T00:00:00.000Z",
  "submittedOnDailyAt": "2026-07-24T00:00:00.000Z",
  "submittedOnDailyBy": { ... },
  "summary": "Full abstract...",
  "upvotes": 0,
  "discussionId": "6a637e77b49b811f02241cf2",
  "projectPage": "https://github.com/hrtan/infmatch",
  "githubRepo": "https://github.com/hrtan/infmatch",
  "githubRepoAddedBy": "user",
  "githubStars": 0,
  "organization": { ... },
  "linkedModels": [ /* array of linked model objects */ ],
  "numTotalModels": 0,
  "linkedDatasets": [ /* array of linked dataset objects */ ],
  "numTotalDatasets": 0,
  "linkedSpaces": [ /* array of linked Space objects */ ],
  "numTotalSpaces": 0
}
```

**Additional fields** (not in daily_papers):
- `projectPage` — external project page URL
- `githubRepo` — linked GitHub repo
- `githubRepoAddedBy` — who added the repo link (`"user"` or `"auto"`)
- `githubStars` — star count from GitHub API
- `linkedModels`, `linkedDatasets`, `linkedSpaces` — directly linked repos
- `numTotalModels`, `numTotalDatasets`, `numTotalSpaces` — total counts

**Linked repo objects** (from `linkedModels`):

```json
{
  "author": "meta-llama",
  "authorData": {
    "_id": "64aa62fec05da19ca8539776",
    "fullname": "Meta Llama",
    "name": "meta-llama",
    "type": "org",
    "isHf": false,
    "plan": "enterprise",
    "followerCount": 83511
  },
  "downloads": 146356,
  "gated": "manual",
  "id": "meta-llama/Llama-Guard-3-8B",
  "availableInferenceProviders": [],
  "lastModified": "2024-10-11T14:52:47.000Z",
  "likes": 311,
  "pipeline_tag": "text-generation",
  "private": false,
  "repoType": "model",
  "numParameters": 8030261248
}
```

**Linked Space objects**:

```json
{
  "emoji": "🌌",
  "id": "nanotron/ultrascale-playbook",
  "running": true,
  "shortDescription": "The ultimate guide to training LLM on large GPU Clusters",
  "featured": false
}
```

**Example**: The Llama 3 Herd of Models paper (`2407.21783`) has:
- 72 linked models
- 15 linked datasets
- 324 linked Spaces

---

#### 4. Paper Search/Browse API (`/api/papers?`)

```
GET /api/papers?search=transformer&limit=3
GET /api/papers?sort=publishedAt&limit=30
GET /api/papers?sort=upvotes&limit=5
GET /api/papers?limit=50
```

**Behavior**:
- Search (`?search=`) — full-text search across titles and authors, **max 3 results**
- Sort (`?sort=publishedAt`) — chronological browse, no limit cap
- Sort (`?sort=upvotes`) — by upvote count, no limit cap
- The `?author=` parameter acts as a search term, not a filter
- No pagination, no offset parameter

**Search response** (summary format):
```json
{
  "id": "2607.21594",
  "title": "Streaming Multi-Agent Autoregressive Diffusion Model...",
  "thumbnailUrl": "https://cdn-thumbnails.huggingface.co/...",
  "upvotes": 11,
  "publishedAt": "2026-07-23T00:00:00.000Z",
  "authors": [ ... ],
  "summary": "...",
  "projectPage": "https://vail-ucla.github.io/worldweaver/"
}
```

---

#### 5. Linking Papers to Repos (Models/Datasets/Spaces)

Papers are linked to HF repos through the **repo card tag system**:

1. **Automatic linking**: If a repo's `README.md` (card) contains a link to an
   ArXiv abstract URL (`https://arxiv.org/abs/XXXX.YYYYY`) or ArXiv PDF, the
   Hub extracts the ArXiv ID and adds an `arxiv:XXXX.YYYYY` tag to the repo.

2. **Tag format**: `arxiv:2204.05149` — prefixed with `arxiv:` followed by the
   full ArXiv ID.

3. **UI display**: The arxiv tag on a repo card is clickable. It links to the
   paper's HF Paper Page (`/papers/{id}`) AND also acts as a filter to find
   other repos citing the same paper.

4. **Bidirectional relationship**: 
   - Paper page → shows linked models/datasets/Spaces via `linkedModels`, `linkedDatasets`, `linkedSpaces`
   - Model/Dataset/Space page → shows the arxiv tag linking back to the paper

5. **No dedicated API endpoint** for `/api/papers/{id}/models` — it returns 404.
   The linked repos are embedded IN the paper detail response only.

---

#### 6. Paper Discussion System

Each paper has a built-in discussion/comment system:

- **discussionId**: A MongoDB ObjectId (e.g., `6a63a8ccab9cdf9be579446a`)
- **Comments are embedded** in the paper page's HTML as Svelte data-props
  (server-rendered, not loaded via a separate API call)
- **No public REST API** exists for paper discussions — comments are only accessible
  through the web page HTML scraping
- **Comment structure** (from HTML data-props):

```json
{
  "id": "6a63eb9aabe9e3bbda67c249",
  "author": {
    "_id": "61942296d5c2ba6daa290357",
    "fullname": "Baolin Peng",
    "name": "Baolin",
    "type": "user",
    "isPro": false,
    "followerCount": 4
  },
  "createdAt": "2026-07-24T22:47:54.000Z",
  "type": "comment",
  "data": {
    "edited": false,
    "hidden": false,
    "latest": {
      "raw": "Full comment text..."
    }
  }
}
```

- Comments support: text, edited tracking, hidden state
- Total comment count available in daily_papers listing via `numComments`

---

#### 7. Paper Page Web UI (Svelte Data Model)

The paper page at `https://huggingface.co/papers/{arxivId}` is server-rendered
with Svelte. The `<div data-target="PaperContent" data-props="...">` element
contains the full page state as a JSON-encoded string (HTML-entity escaped).

**Embedded data keys**:
| Key | Description |
|-----|-------------|
| `paper` | Full paper object (same as API) |
| `comments` | Array of comment objects |
| `primaryEmailConfirmed` | Whether current user has confirmed email |
| `canReadDatabase` | User permission flag |
| `canManagePapers` | User permission flag |
| `canSubmit` | Whether user can submit papers to daily papers |
| `hasHfLevelAccess` | Admin access flag |
| `upvoted` | Whether current user upvoted |
| `upvoters` | Array of users who upvoted |
| `dailyPaperRank` | Paper rank in daily listing |
| `organization` | Paper's organization |
| `markdownContentUrl` | URL to the paper's markdown content |
| `query` | Current URL query params |

**Markdown content URL pattern**:
```
https://huggingface.co/buckets/huggingchat/papers-content/resolve/{folder}/{arxivId}.md
```
Where `{folder}` is the ArXiv ID up to the dot (e.g., `2607` for `2607.21557`).
This delivers the paper content as Markdown, converted from the ArXiv HTML source.

---

#### 8. Paper Authorship & Claiming

**Automatic matching**: The Hub automatically attempts to match paper authors to
HF users based on their registered email address.

**Claiming process**:
1. Visit the paper page (`hf.co/papers/{arxivId}`)
2. Click on your name in the author list → "claim authorship"
3. Redirected to paper settings where you confirm the request
4. HF admin team validates and confirms
5. Once confirmed, the paper shows as "verified" on your profile

**Profile management**:
- Visit `https://huggingface.co/settings/papers` to see all verified papers
- Toggle "Show on profile" checkbox per paper to control visibility
- Papers that have not been indexed yet can be indexed by visiting
  `hf.co/papers/XXXX.YYYYY` directly (with the ArXiv ID)

**Indexing a new paper**:
1. Go to the main Papers page at `https://huggingface.co/papers`
2. Search by paper name or ArXiv ID
3. If the paper doesn't exist, HF offers an option to index it
4. Alternatively, directly visit `hf.co/papers/XXXX.YYYYY` — if the paper
   doesn't exist, HF fetches it from ArXiv and creates a paper page

---

#### 9. Discovery Features

**Upvoting**: Users can upvote papers. The upvoter list is embedded in the paper
page HTML as an array of user objects.

**Thumbnails**: Papers get auto-generated social thumbnails:
```
https://cdn-thumbnails.huggingface.co/social-thumbnails/papers/{arxivId}.png
```

**Discussion participation**: Authors can participate in their paper's
discussion (tracked by `isAuthorParticipating`).

**Organization linking**: Papers affiliated with organizations show the org
badge and link on the paper page.

---

#### 10. Programmatic Access Patterns (Zero-Cost)

**Daily monitoring of new papers**:
```python
import requests

# Get today's daily papers
r = requests.get("https://huggingface.co/api/daily_papers")
papers = r.json()
for entry in papers:
    paper = entry["paper"]
    print(f"{paper['title']} — {paper['id']} ({paper.get('upvotes', 0)} 👍)")
```

**Get paper details + linked resources**:
```python
arxiv_id = "2407.21783"
r = requests.get(f"https://huggingface.co/api/papers/{arxiv_id}")
data = r.json()
print(f"Models: {data['numTotalModels']}, Datasets: {data['numTotalDatasets']}, Spaces: {data['numTotalSpaces']}")
```

**Search for papers on a topic**:
```python
r = requests.get("https://huggingface.co/api/papers", params={"search": "multi-agent"})
# Note: max 3 results returned
```

**Extract comments from paper page** (HTML scraping):
```python
import re, json, requests
from html import unescape

arxiv_id = "2607.21557"
html = requests.get(f"https://huggingface.co/papers/{arxiv_id}").text

# Find the PaperContent data-props
pattern = r'data-target="PaperContent" data-props="(.*?)"(?:\s|>)'
match = re.search(pattern, html, re.DOTALL)
if match:
    raw = match.group(1)
    raw = raw.replace('&quot;', '"').replace('&#x27;', "'").replace('&amp;', '&')
    data = json.loads(raw)
    comments = data.get("comments", [])
    for c in comments:
        print(f"{c['author']['fullname']}: {c['data']['latest']['raw'][:100]}...")
```

**Get paper content as Markdown**:
```python
arxiv_id = "2607.21557"
folder = arxiv_id.split(".")[0]
url = f"https://huggingface.co/buckets/huggingchat/papers-content/resolve/{folder}/{arxiv_id}.md"
md = requests.get(url).text
```

**Find repos linked to a paper**:
```python
r = requests.get(f"https://huggingface.co/api/papers/2407.21783")
data = r.json()
# Models
for model in data.get("linkedModels", []):
    print(f"  Model: {model['id']} ({model.get('pipeline_tag', '?')})")
# Datasets
for ds in data.get("linkedDatasets", []):
    print(f"  Dataset: {ds['id']} (downloads: {ds.get('downloads', 0)})")
# Spaces
for sp in data.get("linkedSpaces", []):
    print(f"  Space: {sp['id']} (running: {sp.get('running', False)})")
```

---

#### 11. Key Takeaways for Zero-Cost Users

| Aspect | Assessment |
|--------|-----------|
| **Cost** | Completely free — all APIs are unauthenticated |
| **API limits** | Search capped at 3 results; daily_papers at 50; no pagination on search |
| **Discovery** | Daily Papers gives latest 50 submissions; browse by date, sort by upvotes |
| **Paper content** | Available as Markdown via buckets URL |
| **Linked artifacts** | Full linked models/datasets/Spaces in paper detail endpoint |
| **Discussions** | Only accessible via HTML scraping (no REST API) |
| **Paper indexing** | Automatic on visiting `hf.co/papers/{id}` |
| **Best uses** | Research monitoring, finding models for papers, trend analysis |

**Integration with other HF features**:
- Paper tags (`arxiv:XXXX.YYYYY`) integrate with the Hub's tag system and model
  search — you can filter models by arxiv tag
- Paper pages support discussions which integrate with HF's notification system
- Paper authorship links to user profiles and organization pages

### References
- https://huggingface.co/docs/hub/en/paper-pages (Hub docs)
- https://huggingface.co/api/daily_papers (Daily Papers API)
- https://huggingface.co/api/papers/{id} (Paper detail API)
- https://huggingface.co/api/papers (Paper search/browse API)
- https://huggingface.co/papers/{id} (Paper page UI)
- https://huggingface.co/settings/papers (Paper settings for authorship)
- https://huggingface.co/docs/hub/en/repositories-licenses (Repo licensing)
- https://huggingface.co/docs/hub/en/models-tags (Tag system docs)
