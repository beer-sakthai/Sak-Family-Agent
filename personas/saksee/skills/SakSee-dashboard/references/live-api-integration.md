# Live API Integration Pattern for SakThai Dashboard

## Problem
The default SakThai dashboard (`src/main.js`) contains hardcoded static data. It shows placeholder metrics (188 skills, 23.3 MB memory) and a static activity feed. This is not production-ready.

## Solution
Rewrite `src/main.js` to fetch live data from the API endpoints on page load, then render the dashboard dynamically.

## Pattern

```javascript
const API_BASE = window.location.origin;

async function fetchJSON(url) {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (e) {
    console.warn(`Failed to fetch ${url}:`, e);
    return null;
  }
}

function renderDashboard(data, ecosystem) {
  // Extract KPIs from data
  const kpis = data?.kpis || {};
  const totalFacts = kpis.total_facts ?? 0;
  const totalObs = kpis.total_observations ?? 0;
  const factsDelta = kpis.total_facts_delta ?? 0;
  const obsDelta = kpis.total_observations_delta ?? 0;

  const recentFacts = data?.recent_facts || [];
  const topObs = data?.top_observations || [];

  const composioStatus = ecosystem?.composio_mcp === 'configured' ? '✅ Connected' : '❌ Not Configured';
  const hfStatus = ecosystem?.huggingface === 'ready' ? '✅ Ready' : '❌ Not Ready';

  // Render the full dashboard HTML with dynamic data
  document.querySelector('#app').innerHTML = `...`;
}

async function init() {
  const [stages, ecosystem] = await Promise.all([
    fetchJSON(`${API_BASE}/api/stages`),
    fetchJSON(`${API_BASE}/api/ecosystem`),
  ]);
  renderDashboard(stages, ecosystem);
}

init();
```

## Key Points

1. **Parallel fetch** — Use `Promise.all` to fetch both endpoints simultaneously
2. **Graceful fallback** — If an API call fails, return `null` and render empty/fallback UI
3. **Dynamic rendering** — Build the HTML string with template literals, inserting live values
4. **Ecosystem status** — Show real-time status of Composio, HuggingFace, and Supermemory
5. **Delta indicators** — Show ↑/↓ arrows with period-over-period changes for KPIs

## API Endpoints

| Endpoint | Returns | Purpose |
|----------|---------|---------|
| `/api/stages` | `{kpis, growth, recent_facts, top_observations, categories}` | Dashboard KPIs and activity data |
| `/api/ecosystem` | `{composio_mcp, huggingface, cron_jobs, supermemory}` | Integration status |

## Build & Deploy

After updating `src/main.js`:

```bash
cd /opt/data/Sak-Family-Agent/dashboard
npm run build
cp -r dist/* /opt/data/Sak-Family-Agent/personas/sakthai/sakthai/dashboard/dist/
```

Then restart the web server for changes to take effect.
