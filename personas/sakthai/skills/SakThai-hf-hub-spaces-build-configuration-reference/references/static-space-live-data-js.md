# Static Space Live Data via HF API JavaScript

**Problem:** Static Spaces are free but their content is hardcoded — download counts, model lists, and stats go stale immediately. How do you make a static Space show live data without paying for Gradio/Docker?

**Solution:** Embed JavaScript that fetches live data from the Hugging Face REST API on every page load. The page stays static (free hosting), but numbers update themselves.

## How It Works

The browser runs JS that calls `https://huggingface.co/api/...` endpoints and updates the DOM. No server, no cron, no PRO subscription.

## Key HF API Endpoints

| Endpoint | Returns | Use Case |
|----------|---------|----------|
| `GET /api/models?author={user}` | All user's models with downloads, likes, tags | Model leaderboard, sibling table |
| `GET /api/datasets?author={user}` | All user's datasets with downloads | Dataset stats list |
| `GET /api/spaces?author={user}` | All user's Spaces | Space overview count |
| `GET /api/models/{user}/{repo}` | Single model details | Individual download count |
| `GET /api/collections/{user}/{id}` | Collection contents | Featured ecosystem view |

## URL construction in JS

```javascript
const HF_API = 'https://huggingface.co/api';
const AUTHOR = 'Nanthasit';

// All models by author, sorted by downloads
const models = await (await fetch(
  `${HF_API}/models?author=${AUTHOR}&sort=downloads&direction=-1`
)).json();

// All datasets by author
const datasets = await (await fetch(
  `${HF_API}/datasets?author=${AUTHOR}`
)).json();

// Single model
const model = await (await fetch(
  `${HF_API}/models/Nanthasit/sakthai-tts-model`
)).json();
```

## Canonical Pattern: Model Download Counter

```html
<span id="tts-downloads">—</span>
<script>
const HF_API = 'https://huggingface.co/api';

async function updateDownloadCount() {
  const res = await fetch(`${HF_API}/models/Nanthasit/sakthai-tts-model`);
  const data = await res.json();
  document.getElementById('tts-downloads').textContent = 
    humanSize(data.downloads || 0);
}

function humanSize(n) {
  if (n >= 1000000) return (n/1000000).toFixed(1)+'M';
  if (n >= 1000) return (n/1000).toFixed(1)+'K';
  return String(n);
}

updateDownloadCount();
</script>
```

## Canonical Pattern: Sibling Models Table (sorted, live)

```html
<tbody id="sibling-table">
  <tr><td colspan="2">Loading...</td></tr>
</tbody>

<script>
const SIBLING_IDS = [
  'Nanthasit/sakthai-context-1.5b-merged',
  'Nanthasit/sakthai-context-0.5b-merged',
  // ... all model IDs
];

async function buildTable() {
  const res = await fetch(`${HF_API}/models?author=${AUTHOR}&sort=downloads&direction=-1`);
  const models = await res.json();
  
  // Build download map
  const dlMap = {};
  for (const m of models) dlMap[m.id] = m.downloads || 0;
  
  // Sort by downloads
  const sorted = [...SIBLING_IDS].sort((a, b) => (dlMap[b]||0) - (dlMap[a]||0));
  
  document.getElementById('sibling-table').innerHTML = sorted.map(id =>
    `<tr>
      <td><a href="https://huggingface.co/${id}">${id.split('/')[1]}</a></td>
      <td>${humanSize(dlMap[id] || 0)}</td>
    </tr>`
  ).join('');
}

buildTable();
</script>
```

## Canonical Pattern: Stats Cards

```html
<div class="stats">
  <div class="stat-card">
    <div class="stat-value" id="stat-models">—</div>
    <div class="stat-label">Models</div>
  </div>
  <div class="stat-card">
    <div class="stat-value" id="stat-downloads">—</div>
    <div class="stat-label">Total Downloads</div>
  </div>
</div>

<script>
async function updateStats() {
  const res = await fetch(`${HF_API}/models?author=${AUTHOR}&sort=downloads&direction=-1`);
  const models = await res.json();
  
  const totalDl = models.reduce((s, m) => s + (m.downloads || 0), 0);
  
  document.getElementById('stat-models').textContent = models.length;
  document.getElementById('stat-downloads').textContent = humanSize(totalDl);
}
updateStats();
</script>
```

## Requirements

- JS [template literals](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Template_literals) — all modern browsers, no transpilation needed
- No CORS issues — the HF API serves `Access-Control-Allow-Origin: *`
- No authentication needed for public repos (models, datasets, Spaces)
- Static SDK in `README.md` — `sdk: static`

## Filters & Exclusions

The HF API returns ALL repos including profile repos and misclassified repos. Filter them out:

```javascript
const EXCLUDE = new Set([
  'Nanthasit/Nanthasit',               // profile repo
  'Nanthasit/sakthai-combined-v6',     // dataset misclassified as model
]);

const models = (await response.json())
  .filter(m => !EXCLUDE.has(m.id) && m.pipeline_tag);
```

The `pipeline_tag` check filters out repos that have no ML pipeline tag (profile repos, dataset repos miscreated as model repos).

## Testing

After deploying, verify via raw file fetch:

```bash
curl -s "https://huggingface.co/spaces/{user}/{space}/raw/main/index.html" \
  | grep -c "fetchAll\|HF_API\|huggingface.co/api"
# Should return > 0
```

Check browser console for CORS or API errors:
```bash
curl -I "https://huggingface.co/api/models?author=Nanthasit" \
  | grep -i "access-control"
# Should show: Access-Control-Allow-Origin: *
```

## Deploy Workflow

```bash
# Clone existing Space
git clone https://huggingface.co/spaces/{user}/{space}

# Replace files
cp index.html {space}/index.html
cp README.md {space}/README.md

# Commit & push
cd {space}
git add -A
git commit -m "feat: live download counts from HF API"
git push origin main
```

For Spaces that don't exist yet:
```yaml
# README.md (HF will auto-create the Space on push)
---
title: My Live Dashboard
emoji: 📊
colorFrom: blue
colorTo: green
sdk: static
pinned: false
---
```

## When NOT to Use This Pattern

- **Need interactive inference** — use Gradio (requires PRO to create, but free ZeroGPU for inference)
- **Need server-side logic** — authentication, secrets, private data processing
- **Data changes more often than page loads** — use a real web app with cron
- **Auth-protected endpoints** — private repos need tokens, which can't be safely embedded in client-side JS

## Cost

**$0.** Same as any static Space — no compute, no GPU, no PRO subscription needed. Every visitor fetches data fresh from the HF API at no cost to you.
