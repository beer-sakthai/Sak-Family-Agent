export const DEMO_DATA = {
  "generated_at": "2026-06-18",
  "source": "demo",
  "kpis": {
    "total_facts": 128,
    "total_facts_delta": 18,
    "total_observations": 45,
    "total_observations_delta": 7,
    "sessions": 24,
    "total_tokens": 156000,
    "total_skills": 66
  },
  "growth": {
    "labels": [
      "2026-05-19","2026-05-22","2026-05-25","2026-05-28","2026-05-31",
      "2026-06-03","2026-06-06","2026-06-09","2026-06-12","2026-06-15","2026-06-18"
    ],
    "facts": [20, 38, 55, 68, 80, 92, 102, 112, 118, 124, 128],
    "observations": [4, 9, 15, 20, 26, 30, 35, 39, 42, 44, 45]
  },
  "recent_facts": [
    { "id": 8, "kind": "pref",    "key": "language",  "value": "Python",               "created": "2026-06-18" },
    { "id": 7, "kind": "pref",    "key": "editor",    "value": "VS Code",              "created": "2026-06-17" },
    { "id": 6, "kind": "profile", "key": "timezone",  "value": "Asia/Bangkok",         "created": "2026-06-17" },
    { "id": 5, "kind": "note",    "key": "",          "value": "Prefers concise replies", "created": "2026-06-16" },
    { "id": 4, "kind": "project", "key": "",          "value": "Building SakThai v2 dashboard", "created": "2026-06-15" },
    { "id": 3, "kind": "skill",   "key": "focus",     "value": "sakthai-coding-testing", "created": "2026-06-14" },
    { "id": 2, "kind": "pref",    "key": "model",     "value": "claude-sonnet-4-6",    "created": "2026-06-13" },
    { "id": 1, "kind": "profile", "key": "name",      "value": "Nanthasit (Beer)",     "created": "2026-06-10" }
  ],
  "top_observations": [
    { "summary": "User prefers Python for data tasks and automation scripts", "weight": 0.95 },
    { "summary": "User focuses on local-first agent architecture with SQLite persistence", "weight": 0.91 },
    { "summary": "User values practical, actionable solutions over theoretical frameworks", "weight": 0.87 },
    { "summary": "Most active between 18:00–23:00 Asia/Bangkok time", "weight": 0.82 },
    { "summary": "Prefers type-safe Python with mypy strict mode", "weight": 0.78 },
    { "summary": "Interested in MCP stdio server patterns for tool reuse", "weight": 0.74 }
  ],
  "categories": [
    { "name": "Pref",        "count": 42, "color": "#d9b54a" },
    { "name": "Note",        "count": 28, "color": "#c9813f" },
    { "name": "Project",     "count": 22, "color": "#3b82f6" },
    { "name": "Profile",     "count": 18, "color": "#10b981" },
    { "name": "Skill",       "count": 12, "color": "#a855f7" },
    { "name": "Observations","count": 45, "color": "#f472b6" }
  ],
  "evolution": {
    "current_version": "v2.0",
    "performance_gain": "+21%",
    "runs": 24,
    "success_rate": 94.4,
    "neural_focus": [
      { "name": "Context recall",       "pct": 91 },
      { "name": "Response accuracy",    "pct": 93 },
      { "name": "Tool selection",       "pct": 88 },
      { "name": "Knowledge integration","pct": 85 },
      { "name": "Latency reduction",    "pct": 82 }
    ]
  },
  "chat": {
    "confidence": 96,
    "messages": [
      { "role": "user",  "text": "What programming language do I use most?" },
      { "role": "agent", "text": "Based on 128 stored facts, Python is your primary language (42 references). You also use TypeScript for the React dashboard." }
    ],
    "thought_process": [
      { "group": "Memory Retrieval", "steps": ["Recall pref:language facts", "Scan project-kind facts for language signals"] },
      { "group": "Reasoning",        "steps": ["Rank by recency and weight", "Draft grounded answer with fact count"] }
    ]
  },
  "skills": [
    {
      "category": "agent", "count": 4,
      "skills": [
        { "name": "sakthai-agent-planning",  "version": "1.0", "description": "Plan multi-step tasks before acting.", "tags": ["agent"] },
        { "name": "sakthai-agent-reasoning", "version": "1.0", "description": "Reason and use tools deliberately inside the agent loop.", "tags": ["agent"] },
        { "name": "sakthai-agent-sessions",  "version": "1.0", "description": "Treat each run as a session worth reviewing.", "tags": ["agent"] },
        { "name": "sakthai-agent-tools",     "version": "1.0", "description": "Use the built-in tools deliberately.", "tags": ["agent"] }
      ]
    },
    {
      "category": "automation", "count": 2,
      "skills": [
        { "name": "sakthai-automation-incident",  "version": "1.0", "description": "Run an incident from detection to learning.", "tags": ["automation"] },
        { "name": "sakthai-automation-workflows", "version": "1.0", "description": "Compose multi-step flows with checkpoints.", "tags": ["automation"] }
      ]
    },
    {
      "category": "coding", "count": 12,
      "skills": [
        { "name": "sakthai-coding-codebase-knowledge", "version": "1.0", "description": "Onboard to a codebase systematically by scanning structure, stack, conventions, and concerns.", "tags": ["coding", "research"] },
        { "name": "sakthai-coding-conventions",        "version": "1.0", "description": "Honor stored preferences and project conventions.", "tags": ["coding"] },
        { "name": "sakthai-coding-debugging",          "version": "1.0", "description": "Debug runtime behavior systematically using breakpoints and isolated reproduction scripts.", "tags": ["coding"] },
        { "name": "sakthai-coding-error-handling",     "version": "1.0", "description": "Handle failures the v2 way — surface tool errors to the model, fail soft on external MCP servers.", "tags": ["coding", "resilience"] },
        { "name": "sakthai-coding-llm-prompting",      "version": "1.0", "description": "Write prompts that work reliably across Claude and Gemini.", "tags": ["coding", "llm"] },
        { "name": "sakthai-coding-mcp-tools",          "version": "1.0", "description": "Build MCP tools that are safe, testable, and well-typed.", "tags": ["coding", "mcp"] },
        { "name": "sakthai-coding-security",           "version": "1.0", "description": "Write code that is secure by default.", "tags": ["coding", "security"] },
        { "name": "sakthai-coding-tdd",                "version": "1.0", "description": "Write tests first, then make them pass.", "tags": ["coding", "testing"] },
        { "name": "sakthai-coding-testing",            "version": "1.0", "description": "Write hermetic, fast unit tests — no network, no GCP credentials.", "tags": ["coding", "testing"] },
        { "name": "sakthai-coding-type-safety",        "version": "1.0", "description": "Keep mypy strict-clean across the sakthai/ package.", "tags": ["coding", "types"] },
        { "name": "sakthai-coding-uv",                 "version": "1.0", "description": "Use uv for reproducible Python environments.", "tags": ["coding", "devops"] },
        { "name": "sakthai-coding-pr-review",          "version": "1.0", "description": "Review pull requests for correctness, safety, and simplicity.", "tags": ["coding", "review"] }
      ]
    },
    {
      "category": "cycle", "count": 6,
      "skills": [
        { "name": "sakthai-cycle-care",   "version": "1.0", "description": "Audit correctness, safety, and performance before shipping.", "tags": ["cycle"] },
        { "name": "sakthai-cycle-dream",  "version": "1.0", "description": "Define the vision and recall prior context before building.", "tags": ["cycle"] },
        { "name": "sakthai-cycle-growth", "version": "1.0", "description": "Reflect and consolidate knowledge after each session.", "tags": ["cycle"] },
        { "name": "sakthai-cycle-hope",   "version": "1.0", "description": "Break the vision into a concrete, sequenced plan.", "tags": ["cycle"] },
        { "name": "sakthai-cycle-joy",    "version": "1.0", "description": "Execute the plan with momentum and tool use.", "tags": ["cycle"] },
        { "name": "sakthai-cycle-trust",  "version": "1.0", "description": "Verify correctness end-to-end before declaring done.", "tags": ["cycle"] }
      ]
    },
    {
      "category": "devops", "count": 3,
      "skills": [
        { "name": "sakthai-devops-ci",      "version": "1.0", "description": "Keep changes green before they land.", "tags": ["devops", "ci"] },
        { "name": "sakthai-devops-env",     "version": "1.0", "description": "Treat configuration as code, secrets as environment.", "tags": ["devops"] },
        { "name": "sakthai-devops-release", "version": "1.0", "description": "Ship releases with confidence using changelogs and tags.", "tags": ["devops"] }
      ]
    },
    {
      "category": "learning", "count": 3,
      "skills": [
        { "name": "sakthai-learning-curation", "version": "1.0", "description": "Keep memory healthy — consolidate, dedupe, and forget stale facts.", "tags": ["learning", "memory"] },
        { "name": "sakthai-learning-feedback", "version": "1.0", "description": "Capture user feedback as durable facts.", "tags": ["learning"] },
        { "name": "sakthai-learning-goals",    "version": "1.0", "description": "Track learning goals across sessions.", "tags": ["learning"] }
      ]
    },
    {
      "category": "llm", "count": 2,
      "skills": [
        { "name": "sakthai-llm-prompting",  "version": "1.0", "description": "Inject memory, then keep prompts lean.", "tags": ["llm"] },
        { "name": "sakthai-llm-providers",  "version": "1.0", "description": "Pick the provider deliberately: Claude for reasoning, Gemini for long context.", "tags": ["llm"] }
      ]
    },
    {
      "category": "memory", "count": 4,
      "skills": [
        { "name": "sakthai-memory-consolidate", "version": "1.0", "description": "Periodically fold and dedupe memory to keep it sharp.", "tags": ["memory"] },
        { "name": "sakthai-memory-recall",      "version": "1.0", "description": "Recall relevant memory before answering.", "tags": ["memory"] },
        { "name": "sakthai-memory-admin",       "version": "1.0", "description": "Proactively manage, synchronize, and back up the persistent SQLite memory store.", "tags": ["memory", "admin"] },
        { "name": "sakthai-memory-search",      "version": "1.0", "description": "Search memory with semantic and keyword queries.", "tags": ["memory"] }
      ]
    },
    {
      "category": "observability", "count": 2,
      "skills": [
        { "name": "sakthai-observability-sessions", "version": "1.0", "description": "Use session logs to debug runs and track token usage.", "tags": ["observability"] },
        { "name": "sakthai-observability-stats",    "version": "1.0", "description": "Watch memory health over time with stats and growth charts.", "tags": ["observability"] }
      ]
    },
    {
      "category": "research", "count": 1,
      "skills": [
        { "name": "sakthai-research-sessions", "version": "1.0", "description": "Research with stored context; save findings back to memory.", "tags": ["research"] }
      ]
    },
    {
      "category": "safety", "count": 2,
      "skills": [
        { "name": "sakthai-safety-guardrails", "version": "1.0", "description": "Keep destructive and outward-facing actions gated.", "tags": ["safety"] },
        { "name": "sakthai-safety-secrets",    "version": "1.0", "description": "Never capture secrets into memory.", "tags": ["safety", "security"] }
      ]
    },
    {
      "category": "sakthai", "count": 4,
      "skills": [
        { "name": "sakthai-personal",                       "version": "1.0", "description": "Recall the user's persistent SakThai memory (facts, observations, preferences).", "tags": ["sakthai", "memory"] },
        { "name": "sakthai-understand-caveman",             "version": "1.0", "description": "Explain complex technical topics in plain, accessible language.", "tags": ["sakthai"] },
        { "name": "sakthai-understand-claude-code-workflows","version": "1.0", "description": "Deep knowledge of Claude Code workflows, hooks, and MCP integration.", "tags": ["sakthai", "claude"] },
        { "name": "sakthai-coding-uv",                     "version": "1.0", "description": "Use uv for reproducible Python environments in the sakthai ecosystem.", "tags": ["sakthai", "devops"] }
      ]
    },
    {
      "category": "security", "count": 3,
      "skills": [
        { "name": "sakthai-security-hardening", "version": "1.0", "description": "Harden the code and runtime; keep privilege least.", "tags": ["security"] },
        { "name": "sakthai-security-privacy",   "version": "1.0", "description": "Protect user data; treat external sync as publication.", "tags": ["security", "privacy"] },
        { "name": "sakthai-coding-security",    "version": "1.0", "description": "Write code that is secure by default — no injection, no insecure defaults.", "tags": ["security", "coding"] }
      ]
    }
  ],
  "recent_sessions": [
    { "date": "2026-06-18", "model": "claude-sonnet-4-6", "task": "Improve dashboard with real repo data and deploy to GitHub Pages", "total_tokens": 14200, "iterations": 6, "stop_reason": "success" },
    { "date": "2026-06-17", "model": "claude-sonnet-4-6", "task": "Add Pylint workflow for Python code analysis", "total_tokens": 8800,  "iterations": 3, "stop_reason": "success" },
    { "date": "2026-06-16", "model": "claude-sonnet-4-6", "task": "Finalize modern React dashboard and fix all lint/format issues", "total_tokens": 12500, "iterations": 5, "stop_reason": "success" },
    { "date": "2026-06-15", "model": "claude-sonnet-4-6", "task": "Fix collect_session_data schema and dashboard tests for React build", "total_tokens": 9200,  "iterations": 4, "stop_reason": "success" },
    { "date": "2026-06-14", "model": "claude-sonnet-4-6", "task": "Add CI/coverage/Python/license status badges to README", "total_tokens": 5600,  "iterations": 2, "stop_reason": "success" },
    { "date": "2026-06-13", "model": "claude-sonnet-4-6", "task": "Extend _parse_slash_command to search extension bundle subdirectories", "total_tokens": 7300, "iterations": 3, "stop_reason": "success" }
  ]
};
