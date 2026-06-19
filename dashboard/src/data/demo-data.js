export const DEMO_DATA = {
  "generated_at": "2025-06-18",
  "source": "demo",
  "kpis": {
    "total_facts": 128,
    "total_facts_delta": 18,
    "total_observations": 45,
    "total_observations_delta": 7,
    "sessions": 24,
    "total_tokens": 156000
  },
  "growth": {
    "labels": ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"],
    "facts": [20, 45, 60, 85, 100, 115, 128],
    "observations": [5, 12, 18, 25, 32, 38, 45]
  },
  "recent_facts": [
    { "id": 5, "kind": "pref", "key": "language", "value": "Python", "created": "2025-06-18" },
    { "id": 4, "kind": "pref", "key": "editor", "value": "VS Code", "created": "2025-06-17" },
    { "id": 3, "kind": "profile", "key": "timezone", "value": "Asia/Bangkok", "created": "2025-06-17" },
    { "id": 2, "kind": "note", "key": "", "value": "Prefers concise replies", "created": "2025-06-16" },
    { "id": 1, "kind": "project", "key": "", "value": "Building SakThai Dashboard", "created": "2025-06-15" }
  ],
  "top_observations": [
    { "summary": "User prefers Python for data tasks", "weight": 0.95 },
    { "summary": "User focuses on data analysis and automation", "weight": 0.9 },
    { "summary": "User values practical, actionable solutions", "weight": 0.85 }
  ],
  "evolution": {
    "current_version": "v2.1",
    "performance_gain": "+24%",
    "runs": 18,
    "success_rate": 94.4,
    "neural_focus": [
      { "name": "Context recall", "pct": 91 },
      { "name": "Response accuracy", "pct": 93 },
      { "name": "Tool selection", "pct": 88 }
    ]
  },
  "chat": {
    "confidence": 98,
    "messages": [
      { "role": "user", "text": "What programming language do I use the most?" },
      { "role": "agent", "text": "Based on my analysis, you use Python the most in your projects (78% of repos)." }
    ],
    "thought_process": [
      { "group": "Memory Retrieval", "steps": ["Recall preferences", "Recall recent project context"] },
      { "group": "Reasoning", "steps": ["Rank relevant facts", "Draft grounded answer"] }
    ]
  },
  "skills": [
    { "category": "coding", "count": 12, "skills": [
      { "name": "python-expert", "version": "1.0", "description": "Expert Python coding skill", "tags": ["python", "coding"] }
    ]},
    { "category": "memory", "count": 5, "skills": [
      { "name": "long-term-recall", "version": "2.1", "description": "Recall facts from SQLite", "tags": ["memory", "sqlite"] }
    ]}
  ],
  "recent_sessions": [
    { "date": "2025-06-18", "model": "claude-3-opus", "task": "Modernize dashboard UI", "total_tokens": 12500, "iterations": 4, "stop_reason": "success" },
    { "date": "2025-06-17", "model": "gpt-4o", "task": "Optimize memory queries", "total_tokens": 8200, "iterations": 2, "stop_reason": "success" }
  ]
};
