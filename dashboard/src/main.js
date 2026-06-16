import { DEMO_DATA } from './data/demo-data.js';

// Dashboard Application State
let DATA = null;

// Icons mapping
const ICONS = {
  brain: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 3a3 3 0 0 0-3 3v0a3 3 0 0 0-2 5 3 3 0 0 0 1 5 3 3 0 0 0 4 3 3 3 0 0 0 3-2V3z"/><path d="M15 3a3 3 0 0 1 3 3 3 3 0 0 1 2 5 3 3 0 0 1-1 5 3 3 0 0 1-4 3 3 3 0 0 1-3-2V3z"/></svg>',
  clock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
};

function esc(value) {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

async function loadData() {
  try {
    const res = await fetch("/data.json");
    if (!res.ok) throw new Error("HTTP " + res.status);
    DATA = await res.json();
    console.log("Loaded live snapshot.");
  } catch (err) {
    console.warn("Failed to load live data, falling back to DEMO_DATA", err);
    DATA = DEMO_DATA;
  }
  renderDashboard();
}

function renderMetrics() {
  const container = document.getElementById("metrics-container");
  if (!DATA || !DATA.kpis) return;
  
  const m = DATA.kpis;
  container.innerHTML = `
    <div class="metric-box">
      <div class="metric-value" data-count="${m.total_facts || 0}">0</div>
      <div class="metric-label">Total Facts</div>
    </div>
    <div class="metric-box">
      <div class="metric-value" data-count="${m.active_observations || 0}">0</div>
      <div class="metric-label">Active Observations</div>
    </div>
  `;
  
  activateCountUps(container);
}

function renderGallery() {
  const container = document.getElementById("gallery-container");
  if (!DATA || !DATA.facts) return;
  
  container.innerHTML = DATA.facts.slice(0, 10).map(f => `
    <div class="memory-item">
      <span class="memory-tag">${esc(f.kind || "memory")}</span>
      <span>${esc(f.value)}</span>
    </div>
  `).join("") || "<p>No facts found.</p>";
}

function renderSkills() {
  const container = document.getElementById("skills-container");
  if (!DATA || !DATA.skills) {
    container.innerHTML = "<p>No skills data loaded.</p>";
    return;
  }
  // Render placeholder if needed or actual skills
  container.innerHTML = `<p>Successfully loaded ${DATA.skills.length || 0} skills.</p>`;
}

function renderDashboard() {
  renderMetrics();
  renderGallery();
  renderSkills();
  
  // Show toast
  const toast = document.getElementById("toast");
  toast.innerHTML = `<span style="color: var(--accent-primary)">Dashboard Initialized</span>`;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3000);
}

// Animation Engine
function animateCount(el, target, duration = 900) {
  const start = performance.now();
  const isFloat = !Number.isInteger(target);
  const format = (v) => (isFloat ? v.toFixed(1) : Math.round(v).toLocaleString());
  
  function easeOutBack(t) {
    const c1 = 1.70158;
    const c3 = c1 + 1;
    return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
  }
  
  function frame(now) {
    const t = Math.min(1, (now - start) / duration);
    const eased = easeOutBack(t);
    el.textContent = format(target * eased);
    if (t < 1) requestAnimationFrame(frame);
    else el.textContent = format(target);
  }
  requestAnimationFrame(frame);
}

function activateCountUps(root) {
  root.querySelectorAll("[data-count]").forEach((el) => {
    const target = parseFloat(el.getAttribute("data-count"));
    if (!Number.isFinite(target)) return;
    el.textContent = "0";
    animateCount(el, target);
  });
}

// Boot
document.addEventListener("DOMContentLoaded", loadData);
