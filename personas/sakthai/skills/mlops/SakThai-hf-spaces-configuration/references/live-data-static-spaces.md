# Live-Data Static Spaces (Gradio Alternative)

Static Spaces are free for everyone. When you need live data (auto-updating stats,
dashboard) but Gradio requires PRO, use **static HTML + JavaScript** that fetches
from the HF API in the browser.

## Pattern: Static HTML + JS fetch from HF API

```html
<script>
async function loadStats() {
  const res = await fetch('https://huggingface.co/api/models?author=Nanthasit&sort=lastModified&direction=-1');
  const models = await res.json();

  // Filter profile repos
  const filtered = models.filter(m => m.id !== 'Nanthasit/Nanthasit' && m.pipeline_tag);
  const totalDownloads = filtered.reduce((s, m) => s + (m.downloads || 0), 0);

  document.getElementById('stats').innerHTML = `
    <div class="stat-card">
      <div class="stat-value">${filtered.length}</div>
      <div class="stat-label">Models</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">${totalDownloads}</div>
      <div class="stat-label">Total Downloads</div>
    </div>`;
}
loadStats();
</script>
```

### Key API endpoints for live stats

| Data | Endpoint |
|------|----------|
| Models by author | `https://huggingface.co/api/models?author={username}&sort=lastModified` |
| Datasets by author | `https://huggingface.co/api/datasets?author={username}&sort=lastModified` |
| Spaces by author | `https://huggingface.co/api/spaces?author={username}` |
| Single model stats | `https://huggingface.co/api/models/{user}/{repo}` |
| Single dataset stats | `https://huggingface.co/api/datasets/{user}/{repo}` |
| Raw file content | `https://huggingface.co/{user}/{repo}/raw/main/{path}` |
| Repo file listing | `https://huggingface.co/api/{type}/{user}/{repo}` |

### What to filter out

- **Profile repos**: `Nanthasit/Nanthasit` (author profile, not a model)
- **Misclassified repos**: dataset repos sometimes appear under `/api/models` with empty `pipeline_tag` — filter by `m.pipeline_tag` being truthy
- **Private repos**: check `m.private` — they'll 401 on direct links

### What renders live vs static

| Element | Live? | How |
|---------|-------|-----|
| Downloads count | ✅ | Fetch from API, render with JS |
| Model names | ✅ | Dynamic table rows |
| Last modified date | ✅ | From API timestamp |
| Badges (shields.io) | ✅ | Dynamic badges auto-update |
| Layout/CSS | ❌ | Static — deployed with the Space |
| Space title/emoji | ❌ | From README.md YAML |

## Deploying to HF Spaces

### Method 1: git clone + edit + push (WORKS for existing Spaces)

```bash
# Clone the existing Space (shallow is fine for static)
git clone --depth 1 https://huggingface.co/spaces/{user}/{space-name}
cd {space-name}

# Edit files
# ... replace index.html, style.css, README.md ...

# Remove old files no longer needed
git rm style.css .gitattributes 2>/dev/null

# Commit and push
git add -A
git commit -m "feat: convert to static HTML with live HF API"
git push
```

This works with the default `hf auth token` — git picks up credentials from
the initial clone. No token in URL needed.

### Method 2: `hf upload` (may fail with 402)

```bash
hf upload {user}/{space-name} index.html --type space \
  --commit-message "update index.html"
```

**Known issue**: `hf upload` returns `402 Payment Required` even for existing
static Spaces. It appears to call the repo-create API endpoint first, which
fails on free accounts. **Workaround**: use git clone+push (Method 1).

### Method 3: Fresh clone + hf repo create + git push

For brand-new Spaces, create via `hf repos create` first, then clone and push:

```bash
hf repos create {space-name} --type space --sdk static
git clone https://huggingface.co/spaces/{user}/{space-name}
# ... add files, commit, push
```

## Pitfalls

### Gradio/PRO paywall
Gradio Spaces on `cpu-basic` require PRO subscription. The error is:
```
402 Payment Required — Static Spaces are free for everyone, but hosting
Gradio and Docker Spaces on free cpu-basic requires a PRO subscription.
```
**Do NOT convert a static Space to Gradio on a free account** — the API
will reject Space creation and the old static Space won't be usable until
reverted.

Always default to **static HTML + JS** for live-data dashboards on free
accounts.

### JS cross-origin limits
HF API at `huggingface.co/api/` has **no CORS restrictions** on read
endpoints — you can call it directly from the browser. No proxy needed.

### Performance on first load
Static Spaces load fast but the JS fetch adds ~1-2s for each API call.
Users see a "Loading..." state. Mitigation:
- Show a skeleton/spinner while data loads
- Fetch multiple endpoints in parallel with `Promise.all()`
- Cache results in `sessionStorage` for same-visit navigation

### Unicode/emoji in verification scripts
The Hermes Tirith security scanner may block inline heredocs with emoji.
When building the HTML as a string in Python to write to disk, use
`write_file()` to save the file, then deploy separately.
