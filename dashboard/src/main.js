import './style.css';

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
        <h3 class="card-title">Loaded Skills</h3>
        <div class="metric">188</div>
      </div>
      <div class="glass-panel">
        <h3 class="card-title">Memory Size</h3>
        <div class="metric">23.3 MB</div>
      </div>
      <div class="glass-panel">
        <h3 class="card-title">Compute Node</h3>
        <div class="metric" style="font-size: 1.5rem; display: flex; align-items: center; height: 100%;">Ollama Local</div>
      </div>
    </div>

    <div class="glass-panel activity-feed">
      <h3 class="card-title">Recent Activities</h3>
      <ul class="feed-list" id="activity-feed">
        <li class="feed-item">
          <div class="feed-icon">🔧</div>
          <div class="feed-text">
            <h4>Skills Synchronized</h4>
            <p>Copied 188 skills from House of Sak.</p>
          </div>
        </li>
        <li class="feed-item">
          <div class="feed-icon">🔒</div>
          <div class="feed-text">
            <h4>Security Update</h4>
            <p>Configured for 100% local-first execution. Cloud providers disabled.</p>
          </div>
        </li>
        <li class="feed-item">
          <div class="feed-icon">✨</div>
          <div class="feed-text">
            <h4>UI/UX Dashboard Deployed</h4>
            <p>Successfully launched premium glassmorphism dashboard.</p>
          </div>
        </li>
      </ul>
    </div>
  </main>
`;
