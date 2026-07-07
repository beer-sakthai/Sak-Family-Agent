import './style.css';

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

function formatNumber(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
  return String(n);
}

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0;
  let size = bytes;
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024;
    i++;
  }
  return size.toFixed(1) + ' ' + units[i];
}

function renderDashboard(data, ecosystem) {
  const kpis = data?.kpis || {};
  const totalFacts = kpis.total_facts ?? 0;
  const totalObs = kpis.total_observations ?? 0;
  const factsDelta = kpis.total_facts_delta ?? 0;
  const obsDelta = kpis.total_observations_delta ?? 0;

  const recentFacts = data?.recent_facts || [];
  const topObs = data?.top_observations || [];

  const composioStatus = ecosystem?.composio_mcp === 'configured' ? '✅ Connected' : '❌ Not Configured';
  const hfStatus = ecosystem?.huggingface === 'ready' ? '✅ Ready' : '❌ Not Ready';

  document.querySelector('#app').innerHTML = `
    <aside class="glass-panel sidebar">
      <div class="brand">
        <div class="brand-icon">👑</div>
        <h1>SakKing OS</h1>
      </div>
      <ul class="nav-links">
        <li><a href="#" class="active">Dashboard</a></li>
        <li><a href="#">Tasks</a></li>
        <li><a href="#">Skills Registry</a></li>
        <li><a href="#">Memory Store</a></li>
        <li><a href="#">Settings</a></li>
      </ul>
      <div class="glass-panel" style="margin-top: auto; padding: 1rem;">
        <div class="card-title">Ecosystem</div>
        <div style="font-size: 0.85rem; display: flex; flex-direction: column; gap: 0.5rem;">
          <div>Composio: ${composioStatus}</div>
          <div>HuggingFace: ${hfStatus}</div>
          <div>Supermemory: ✅ Connected</div>
        </div>
      </div>
    </aside>

    <main class="main-content">
      <header class="header">
        <h2>Overview</h2>
        <div class="status-badge">
          <span class="status-dot"></span>
          100% Local · Active
        </div>
      </header>

      <div class="dashboard-grid">
        <div class="glass-panel">
          <h3 class="card-title">Total Facts</h3>
          <div class="metric">${formatNumber(totalFacts)}</div>
          <div style="font-size: 0.8rem; color: ${factsDelta >= 0 ? 'var(--success)' : 'var(--warning)'}; margin-top: 0.5rem;">
            ${factsDelta >= 0 ? '↑' : '↓'} ${Math.abs(factsDelta)} this period
          </div>
        </div>
        <div class="glass-panel">
          <h3 class="card-title">Observations</h3>
          <div class="metric">${formatNumber(totalObs)}</div>
          <div style="font-size: 0.8rem; color: ${obsDelta >= 0 ? 'var(--success)' : 'var(--warning)'}; margin-top: 0.5rem;">
            ${obsDelta >= 0 ? '↑' : '↓'} ${Math.abs(obsDelta)} this period
          </div>
        </div>
        <div class="glass-panel">
          <h3 class="card-title">Compute Node</h3>
          <div class="metric" style="font-size: 1.5rem; display: flex; align-items: center; height: 100%;">Ollama Local</div>
        </div>
      </div>

      <div class="glass-panel activity-feed">
        <h3 class="card-title">Recent Facts</h3>
        <ul class="feed-list" id="activity-feed">
          ${recentFacts.length > 0
            ? recentFacts.map(f => `
                <li class="feed-item">
                  <div class="feed-icon">📝</div>
                  <div class="feed-text">
                    <h4>${f.kind || 'fact'}</h4>
                    <p>${f.value || JSON.stringify(f)}</p>
                  </div>
                </li>
              `).join('')
            : `
              <li class="feed-item">
                <div class="feed-icon">ℹ️</div>
                <div class="feed-text">
                  <h4>No Recent Facts</h4>
                  <p>Start learning to populate your memory.</p>
                </div>
              </li>
            `
          }
        </ul>
      </div>

      <div class="glass-panel activity-feed">
        <h3 class="card-title">Top Observations</h3>
        <ul class="feed-list">
          ${topObs.length > 0
            ? topObs.map(o => `
                <li class="feed-item">
                  <div class="feed-icon">🔍</div>
                  <div class="feed-text">
                    <h4>${o.label || 'observation'}</h4>
                    <p>${o.value || JSON.stringify(o)}</p>
                  </div>
                </li>
              `).join('')
            : `
              <li class="feed-item">
                <div class="feed-icon">ℹ️</div>
                <div class="feed-text">
                  <h4>No Observations Yet</h4>
                  <p>Observations will appear as the agent learns.</p>
                </div>
              </li>
            `
          }
        </ul>
      </div>
    </main>
  `;
}

async function init() {
  const [stages, ecosystem] = await Promise.all([
    fetchJSON(`${API_BASE}/api/stages`),
    fetchJSON(`${API_BASE}/api/ecosystem`),
  ]);
  renderDashboard(stages, ecosystem);
}

init();
