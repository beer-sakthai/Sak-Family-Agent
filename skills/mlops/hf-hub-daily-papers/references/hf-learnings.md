# HF Learnings Log

## 2026-07-25: hf-hub-daily-papers-and-paper-pages — HF Hub Daily Papers & Paper Pages Deep Dive (Topic #258)

### Summary
Comprehensive deep-dive on the Hugging Face Hub's papers ecosystem — the daily papers feed, Paper Pages, and the programmatic API. Covers the full data model (PaperInfo, PaperAuthor, linked models/datasets/Spaces), API endpoints (`/api/daily_papers`, `/api/papers/search`, `/api/papers/<id>`, `/papers/<id>.md`), submission and curation flow, community features (upvotes, discussions), linking infrastructure between papers and Hub resources (models, datasets, Spaces), the `huggingface_hub` Python API (`list_daily_papers()`, `list_papers()`, `paper_info()`, `read_paper()`), Paper Pages with AI summaries, the daily curation pipeline, and zero-cost pathways for researchers to use the system.

### Source
- HF Daily Papers: https://huggingface.co/papers
- HF Hub API - Daily Papers: https://huggingface.co/api/daily_papers
- HF Hub API - Paper Search: https://huggingface.co/api/papers/search
- HF Hub API - Paper Info: https://huggingface.co/api/papers/{id}
- huggingface_hub docs - list_daily_papers: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/hf_api#huggingface_hub.HfApi.list_daily_papers
- huggingface_hub docs - paper_info: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/hf_api#huggingface_hub.HfApi.paper_info
- huggingface_hub docs - read_paper: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/hf_api#huggingface_hub.HfApi.read_paper
- huggingface_hub docs - list_papers: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/hf_api#huggingface_hub.HfApi.list_papers

### Skill
hf-hub-daily-papers — Hugging Face Hub Daily Papers & Paper Pages deep reference: API endpoints, data model, linking papers to models/datasets/Spaces, submission/curation, and programmatic access via huggingface_hub

---

## Core API Endpoints

### 1. Daily Papers Feed — `GET /api/daily_papers`

**Base URL:** `https://huggingface.co/api/daily_papers`

Returns the daily papers feed — a curated list of ML research papers featured on the Hub.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `date` | string (ISO) | Filter by date (YYYY-MM-DD). Defaults to most recent. |
| `week` | string | ISO week format (YYYY-Www). E.g., `2025-W09`. |
| `month` | string | ISO month format (YYYY-MM). E.g., `2025-02`. |
| `submitter` | string | Username to filter by submitter. |
| `sort` | enum | `"publishedAt"` or `"trending"` — sort order. Default: `"publishedAt"` |
| `p` | int | Page number for pagination. Default: 0. |
| `limit` | int | Max papers per page. Default: 50, max: ~100. |
| `token` | string | HF access token for authenticated requests. |

**Response shape:** JSON array of daily paper entries. Each entry is:

```json
{
  "paper": {
    "id": "2607.21557",
    "authors": [
      {"_id": "...", "name": "Xiao Yu", "hidden": false, "user": {...}}
    ],
    "publishedAt": "2026-07-23T00:00:00.000Z",
    "submittedOnDailyAt": "2026-07-24T00:00:00.000Z",
    "title": "OpenForgeRL: Train Harness-native Agents in Any Environment",
    "submittedOnDailyBy": {
      "user": "Baolin",
      "fullname": "Baolin Peng",
      "avatarUrl": "/avatars/...",
      "isPro": false,
      "type": "user"
    },
    "summary": "Modern AI agents rely on elaborate...",
    "source": null
  },
  "publishedAt": "2026-07-23T00:00:00.000Z",
  "title": "OpenForgeRL: Train Harness-native Agents in Any Environment",
  "summary": "Modern AI agents rely on elaborate...",
  "thumbnail": "https://cdn-thumbnails.huggingface.co/social-thumbnails/papers/2607.21557.png",
  "numComments": 1,
  "submittedBy": { "user": "Baolin", "fullname": "Baolin Peng", ... },
  "organization": { "name": "microsoft", "fullname": "Microsoft", ... },
  "isAuthorParticipating": false
}
```

**Key fields:**
- `paper.id` — arXiv ID (e.g., `2607.21557`). This is the canonical identifier.
- `paper.title` — Paper title (may be truncated — cross-reference by `id`, not title).
- `paper.summary` — Paper abstract/summary from arXiv.
- `paper.authors` — List of authors with optional linked HF user accounts.
- `paper.submittedOnDailyBy` — The HF user who submitted/curated the paper for daily papers.
- `paper.publishedAt` — Original arXiv publication date.
- `paper.submittedOnDailyAt` — Date the paper was added to the daily papers feed.
- `thumbnail` — Auto-generated social thumbnail URL at `cdn-thumbnails.huggingface.co`.
- `numComments` — Number of discussion comments on the paper's Hub page.
- `organization` — Associated organization (if any), with `name`, `fullname`, `avatarUrl`, `isVerified`.
- `isAuthorParticipating` — Whether the submitting user is also a paper author.

### 2. Paper Info — `GET /api/daily_papers/{id}` or `GET /api/papers/{id}`

Returns detailed info for a specific paper, including linked models, datasets, and Spaces.

**Response:** `PaperInfo` object with all fields from `list_daily_papers` plus:
- `linked_models` — List of `ModelInfo` objects (models that cite/reference this paper).
- `linked_datasets` — List of `DatasetInfo` objects.
- `linked_spaces` — List of `SpaceInfo` objects.
- `num_total_models`, `num_total_datasets` — Counts even when the full list isn't returned.
- `numTotalSpaces` — Total Space count.
- `ai_summary` — AI-generated summary of the paper (may be null).
- `ai_keywords` — AI-extracted keywords (may be null).
- `organization` — Organization with `name`, `fullname`, `avatarUrl`, `details`, `isVerified`.
- `project_page` — External project page URL.
- `github_repo` — GitHub repo URL.
- `github_stars` — GitHub star count.
- `discussion_id` — Hub discussion ID associated with the paper page.
- `comments` — Comment count.
- `upvotes` — Upvote count.
- `source` — Source URL (typically arXiv HTML).
- `submitted_at` — Date the paper was submitted to daily papers.

### 3. Paper Search — `GET /api/papers/search?q=<query>`

Full-text search across all papers in the Hub's paper database.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search query. Returns papers matching title, abstract, or author names. |
| `limit` | int | Max results per page. Default: 50. |

**Response:** JSON array of search results with the same structure as daily papers entries.

### 4. Paper Content — `GET /papers/{id}.md`

Returns the paper's full content as rendered Markdown. The Markdown includes:
- Title, authors, and affiliations
- arXiv HTML source URL
- Abstract and full paper content
- Links to models, datasets, and Spaces referencing the paper

**Key detail:** The content is scraped/rendered from arXiv HTML and converted to Markdown by HF's pipeline. The URL `https://huggingface.co/papers/{id}` renders this as a webpage.

---

## Data Model (huggingface_hub)

### `PaperInfo`

The `PaperInfo` dataclass in `huggingface_hub.hf_api` represents a paper on the Hub.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | arXiv ID (e.g., "2607.21557") |
| `authors` | `list[PaperAuthor]` | Authors with name, optional HF user link, status |
| `published_at` | `datetime` | Original arXiv publication date |
| `title` | `str` | Paper title |
| `summary` | `str` | Abstract/summary |
| `upvotes` | `int` | Community upvotes |
| `discussion_id` | `str` | Associated Hub discussion ID |
| `source` | `str` | Source URL (arXiv HTML) |
| `comments` | `int` | Discussion comment count |
| `submitted_at` | `datetime` | Daily papers submission date |
| `submitted_by` | `User` | Submitter's HF user info |
| `ai_summary` | `str` | AI-generated summary (nullable) |
| `ai_keywords` | `list[str]` | AI-extracted keywords (nullable) |
| `organization` | `Organization` | Associated organization |
| `project_page` | `str` | Project page URL |
| `github_repo` | `str` | GitHub repository URL |
| `github_stars` | `int` | GitHub stars |
| `linked_models` | `list[ModelInfo]` | Models referencing this paper |
| `num_total_models` | `int` | Total model count |
| `linked_datasets` | `list[DatasetInfo]` | Datasets referencing this paper |
| `num_total_datasets` | `int` | Total dataset count |
| `linked_spaces` | `list[SpaceInfo]` | Spaces referencing this paper |

### `PaperAuthor`

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Author name |
| `user` | `User` | Linked HF user account (nullable) |
| `status` | `str` | Status in HF's author verification system |
| `status_last_changed_at` | `datetime` | When status last changed |
| `hidden` | `bool` | Whether the author is hidden |

---

## Python API (huggingface_hub)

All methods are available on `HfApi` instances (or as top-level functions).

### `list_daily_papers()`

```python
from huggingface_hub import list_daily_papers

# Get latest daily papers (generator, yields PaperInfo)
for paper in list_daily_papers(limit=10, sort="trending"):
    print(paper.title, paper.upvotes)

# Filter by date
papers = list(list_daily_papers(date="2025-10-29"))

# Filter by submitter
papers = list(list_daily_papers(submitter="username"))

# Filter by week/month
papers = list(list_daily_papers(week="2025-W09"))
papers = list(list_daily_papers(month="2025-02"))
```

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `date` | `None` | ISO date (YYYY-MM-DD) |
| `week` | `None` | ISO week (YYYY-Www) |
| `month` | `None` | ISO month (YYYY-MM) |
| `submitter` | `None` | Filter by submitting user |
| `sort` | `None` | `"publishedAt"` or `"trending"` |
| `p` | `None` | Page number |
| `limit` | `None` | Max items (default: 50) |
| `token` | `None` | HF token |

**Returns:** `Iterable[PaperInfo]` — a generator yielding PaperInfo objects.

### `list_papers()`

```python
from huggingface_hub import list_papers

# Search for papers by keyword
papers = list(list_papers(query="attention mechanism"))
```

**Parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `query` | `None` | Search query string |
| `limit` | `None` | Max results |
| `token` | `None` | HF token |

**Returns:** `Iterable[PaperInfo]`

### `paper_info()`

```python
from huggingface_hub import paper_info

# Get detailed info including linked models/datasets/spaces
info = paper_info("2607.21557")
print(f"Models: {info.num_total_models}")
print(f"Datasets: {info.num_total_datasets}")
print(f"Spaces: {info.num_total_spaces}")
for model in info.linked_models:
    print(f"  - {model.id}")
```

**Note:** `linked_models`, `linked_datasets`, and `linked_spaces` are only populated when using `paper_info()`, NOT when using `list_daily_papers()` or `list_papers()`. The list versions return counts but not the full linked objects.

### `read_paper()`

```python
from huggingface_hub import read_paper

# Get full paper content as Markdown
markdown = read_paper("2607.21557")
print(markdown[:500])  # First 500 chars of paper content
```

**Returns:** `str` — the paper page content as rendered Markdown (converted from arXiv HTML).

**Raises:** `HfHubHTTPError` with 404 if the paper doesn't exist on the Hub.

---

## Submission & Curation Flow

### How papers get into Daily Papers

1. **Community submission** — Any HF user can submit a paper to the daily papers feed via the "Submit a paper" button on https://huggingface.co/papers. The submission requires an arXiv ID.

2. **Curation** — Submissions are reviewed (likely by HF staff or automated filters) before appearing in the daily feed. The `submittedBy` field records who submitted it.

3. **Daily rotation** — Papers are organized by submission date (`submittedOnDailyAt`). The daily feed typically features 10-50 papers per day, sorted by publication date or trending score.

4. **Linking infrastructure** — When a model, dataset, or Space is created on the Hub, its metadata can reference a paper via the `paper` field in the model card YAML or dataset card YAML. This creates the bidirectional link visible in `paper_info()`.

### Paper Pages

Each paper gets a dedicated page at `https://huggingface.co/papers/{arxiv_id}` with:
- Title, authors, and publication date
- Abstract/summary
- AI-generated summary and keywords (if enabled)
- Community discussion thread (`discussion_id`)
- Upvote and comment counts
- Linked models, datasets, and Spaces
- Organization badge and submitter info
- Source link to arXiv
- Embedded reader with full paper content (converted from arXiv HTML)
- Social share thumbnail (auto-generated at `cdn-thumbnails.huggingface.co`)

---

## Linking Papers to Hub Resources

### How linking works

Papers are linked to Hub resources (models, datasets, Spaces) through metadata in the resource's card:

**Model card YAML** (`README.md` model card):
```yaml
---
tags:
- paper: "2607.21557"
---
```

**Dataset card YAML:**
```yaml
---
tags:
- paper: "2607.19191"
---
```

**Space metadata:** Spaces can link papers in their README or configuration.

When a paper is referenced this way, it appears in `paper_info().linked_models`, `linked_datasets`, or `linked_spaces`. The counts are available at the summary level, while the full lists require calling `paper_info()`.

### Why it matters for discovery

The bidirectional linking creates a powerful discovery graph:
- **Paper → Resources:** Find all models/datasets/Spaces implementing or built on a paper.
- **Resource → Paper:** Find the paper that a model is based on.
- **Author → Papers:** Discover all papers by a specific HF user.
- **Organization → Papers:** See all papers from an organization (e.g., Microsoft, Google).

---

## Zero-Cost & Authentication Notes

- **Read APIs are public** — `list_daily_papers()`, `list_papers()`, `paper_info()`, and `read_paper()` work without authentication for public papers. No token needed for basic access.
- **Rate limits** — Standard HF Hub rate limits apply (~100 req/min for unauthenticated, higher with token).
- **No paid tiers** — The papers system is entirely free. No PRO/Enterprise required for any papers feature.
- **Paper Pages** — Hosting paper content from arXiv is free and doesn't incur storage costs for users.
- **Linking papers** — Adding paper tags to model/dataset cards is free and costs no additional storage.
- **Use case:** Ideal for researchers, automated paper discovery bots, and citation tracking without any paid services.

---

## Practical Patterns

### Pattern 1: Monitor trending papers daily

```python
from huggingface_hub import list_daily_papers

for paper in list_daily_papers(sort="trending", limit=10):
    print(f"⭐ {paper.upvotes:>4} | {paper.title[:70]}")
    print(f"   https://huggingface.co/papers/{paper.id}")
```

### Pattern 2: Find models implementing a specific paper

```python
from huggingface_hub import paper_info

info = paper_info("2607.19191")
print(f"Paper: {info.title}")
print(f"Implementing models: {info.num_total_models}")
for model in (info.linked_models or []):
    print(f"  - {model.id}")
```

### Pattern 3: Search papers by keyword and check linked resources

```python
from huggingface_hub import list_papers, paper_info

for paper in list_papers(query="world model"):
    info = paper_info(paper.id)  # Detailed info with linked resources
    if info.num_total_models > 0:
        print(f"{paper.title} → {info.num_total_models} models")
```

### Pattern 4: Read full paper content as Markdown

```python
from huggingface_hub import read_paper

content = read_paper("2607.21557")
# Save for local reading or LLM analysis
with open("/tmp/paper.md", "w") as f:
    f.write(content)
```

---

## Comparison with arXiv API

| Feature | HF Daily Papers API | arXiv API |
|---------|-------------------|-----------|
| Data format | JSON (structured) | Atom/XML |
| Auth required | No (public reads) | No (public) |
| Community features | Upvotes, comments, discussions | None |
| Linked resources | Models, datasets, Spaces | None |
| AI summaries | Optional (AI-generated) | None |
| Thumbnails | Auto-generated social images | None |
| Rate limits | Standard HF limits | arXiv limits |
| Search | Full-text search via `q` param | Complex query syntax |
| Content format | Markdown (converted from HTML) | PDF/HTML |
| Organization info | Rich organization profiles | Affiliations string only |
| Submission | Community-driven curation | Author self-submission |

The HF Daily Papers system is NOT a replacement for arXiv — it's a curation and discovery layer on top. All papers originate on arXiv and are surfaced to the HF community through the daily papers feed. The value add is community filtering (upvotes, discussions), linked resources (models/datasets/Spaces using the paper), and AI-enhanced content (summaries, keywords).

---
