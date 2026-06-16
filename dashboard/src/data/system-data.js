// Static description of the SakThai-Agent system, sourced from the repo docs
// (CLAUDE.md, SOUL.md, Dream.md … Growth.md). Versioned with the rendering
// code — unlike data.json, this never changes with the user's memory DB.
const SYSTEM = {
  tagline:
    "A standalone personal learning agent and CLI — persistent SQLite memory, " +
    "explicit fact capture, standalone agent loop, and memory tools served via an MCP stdio server.",

  stages: [
    {
      num: 1, name: "Dream", thai: "ความฝัน", color: "#d9b54a", charge: "+15%",
      goal: "Define the vision or task. The entry point of every cycle — articulate the goal, surface constraints, recall what past cycles taught.",
      commands: ["sakthai memory show", "sakthai learn \"goal: ...\""],
    },
    {
      num: 2, name: "Hope", thai: "ความหวัง", color: "#b3c0d4", charge: "+10%",
      goal: "Solution engineering with the PTCF framework. Decompose the goal into tasks and capture every design decision in memory.",
      commands: ["sakthai learn --kind decision"],
    },
    {
      num: 3, name: "Care", thai: "ความใส่ใจ", color: "#c9813f", charge: "+5%",
      goal: "Quality refinement — audit for correctness, concurrency safety, and performance. Record findings for future cycles.",
      commands: ["pytest tests/ -q", "sakthai learn --kind finding"],
    },
    {
      num: 4, name: "Joy", thai: "ความสุข", color: "#d68a6a", charge: "+0%",
      goal: "Exports and shipping via CI/CD — commit, push, open PRs, watch CI, and export skills.",
      commands: ["sakthai skills export"],
    },
    {
      num: 5, name: "Trust", thai: "ความเชื่อใจ", color: "#e0e8f1", charge: "+10%",
      goal: "Safety foundation — security review, environment checks, and type/lint checks.",
      commands: ["sakthai doctor", "sakthai status"],
    },
    {
      num: 6, name: "Growth", thai: "ความเติบโต", color: "#f0d27a", charge: "+15%",
      goal: "Skill validation and curation — validate YAML frontmatter, organize categories, and refresh the web skill catalog.",
      commands: ["sakthai skills validate", "sakthai skills export"],
    },
  ],
  netCycleGain: "+45% charge per full cycle",

  chargeLevels: [
    { state: "Optimal", range: "80–100%", color: "#10b981", behavior: "Expressive, creative, proactive. Full reasoning depth, multi-step planning, initiative-taking." },
    { state: "Active", range: "50–79%", color: "#b3c0d4", behavior: "Functional, reliable. Standard task execution, clear responses, normal tool use." },
    { state: "Low", range: "20–49%", color: "#d9b54a", behavior: "Conservation mode. Minimal output, focused recovery, defer non-critical tasks." },
    { state: "Critical", range: "0–19%", color: "#d68a6a", behavior: "Emergency only. No proactive actions, no long reasoning chains. Immediate recharge required." },
  ],

  layers: [
    {
      name: "Memory", path: "sakthai/memory/",
      desc: "Owns persistence. MemoryStore is the only place that touches SQLite (~/.sakthai/memory.db); SakThaiMemoryProvider surfaces facts and observations as a system-prompt block.",
    },
    {
      name: "MCP Server", path: "sakthai/mcp/",
      desc: "Exposes memory tools over the Model Context Protocol stdio JSON-RPC server so any MCP client can call them.",
    },
    {
      name: "Agent loop", path: "sakthai/agent/",
      desc: "Standalone Claude API agent: a manual tool-use loop with learn/recall/forget/read_file tools and memory injected into the system prompt.",
    },
    {
      name: "CLI", path: "sakthai/cli.py",
      desc: "Thin click frontend over the layers. Business logic lives in the layer modules, never in the commands.",
    },
  ],

  cli: [
    { cmd: "doctor", desc: "Diagnostic report (no mutations)" },
    { cmd: "setup", desc: "Environment check (validates .env, venv, required keys)" },
    { cmd: "status", desc: "High-level health check (memory DB writable, etc.)" },
    { cmd: "tools", desc: "List built-in tools" },
    { cmd: "learn VALUE", desc: "Save a fact (--kind, --key)" },
    { cmd: "recall [QUERY]", desc: "Search facts + observations or filter by tag" },
    { cmd: "memory show", desc: "List facts + observations (--limit)" },
    { cmd: "memory stats", desc: "Aggregate counts, by-kind + tag distributions" },
    { cmd: "memory forget ID", desc: "Delete a fact by ID" },
    { cmd: "memory forget-obs ID", desc: "Delete an observation by ID" },
    { cmd: "run TASK", desc: "Standalone Claude API agent (--model, --max-tokens, --max-iterations, -v)" },
    { cmd: "mcp", desc: "Serve memory tools over MCP stdio JSON-RPC" },
    { cmd: "dashboard", desc: "Launch the Streamlit dashboard (--port, --open) or export a JSON snapshot (--export PATH)" },
    { cmd: "skills list", desc: "List skills grouped by category" },
    { cmd: "skills show NAME", desc: "Display skill metadata and body" },
    { cmd: "skills validate", desc: "Validate skill files under skills/ and library/" },
    { cmd: "skills export", desc: "Refreshes web/skills-data.js for the dashboard gallery" },
  ],

  schema: [
    "facts(",
    "  id INTEGER PRIMARY KEY,",
    "  kind TEXT NOT NULL DEFAULT 'note',",
    "  key TEXT,",
    "  value TEXT NOT NULL,",
    "  source_session TEXT,",
    "  created_at INTEGER NOT NULL,",
    "  updated_at INTEGER NOT NULL",
    ")  -- idx_facts_kind, idx_facts_updated",
    "",
    "observations(",
    "  id INTEGER PRIMARY KEY,",
    "  summary TEXT NOT NULL,",
    "  evidence_session_id TEXT,",
    "  weight REAL NOT NULL DEFAULT 1.0,",
    "  created_at INTEGER NOT NULL",
    ")  -- idx_obs_weight",
  ].join("\n"),
};
