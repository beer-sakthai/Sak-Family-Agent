// Fallback snapshot used when data.json cannot be fetched (e.g. file://).
// Mirrors sakthai.dashboard.data.DEMO_DATA exactly — regenerate with:
//   python -c "import json; from sakthai.dashboard.data import DEMO_DATA; print(json.dumps(DEMO_DATA, indent=2))"
// tests/test_dashboard_export.py pins this file to the Python source.
export const DEMO_DATA = {
  "generated_at": "demo",
  "source": "demo",
  "kpis": {
    "total_facts": 128,
    "total_facts_delta": 18,
    "active_observations": 45,
    "active_observations_delta": 7
  },
  "growth": {
    "labels": [
      "Day 1",
      "Day 2",
      "Day 3",
      "Day 4",
      "Day 5",
      "Day 6",
      "Day 7",
      "Day 8",
      "Day 9",
      "Day 10",
      "Day 11",
      "Day 12",
      "Day 13",
      "Day 14",
      "Day 15",
      "Day 16",
      "Day 17",
      "Day 18",
      "Day 19",
      "Day 20",
      "Day 21",
      "Day 22",
      "Day 23",
      "Day 24",
      "Day 25",
      "Day 26",
      "Day 27",
      "Day 28",
      "Day 29",
      "Day 30"
    ],
    "facts": [
      18,
      22,
      27,
      30,
      34,
      39,
      45,
      51,
      56,
      60,
      66,
      71,
      77,
      82,
      88,
      93,
      98,
      103,
      107,
      111,
      114,
      117,
      119,
      121,
      123,
      124,
      125,
      126,
      127,
      128
    ],
    "observations": [
      4,
      5,
      7,
      8,
      10,
      11,
      13,
      15,
      17,
      18,
      20,
      22,
      24,
      25,
      27,
      29,
      30,
      32,
      33,
      35,
      36,
      37,
      38,
      39,
      40,
      41,
      42,
      43,
      44,
      45
    ]
  },
  "recent_facts": [
    {
      "kind": "pref",
      "key": "favorite_language",
      "value": "Python",
      "created": "2025-06-02"
    },
    {
      "kind": "pref",
      "key": "code_editor",
      "value": "VS Code",
      "created": "2025-06-01"
    },
    {
      "kind": "fact",
      "key": "timezone",
      "value": "Asia/Bangkok (GMT+7)",
      "created": "2025-06-01"
    },
    {
      "kind": "fact",
      "key": "name",
      "value": "SakThai",
      "created": "2025-05-31"
    },
    {
      "kind": "pref",
      "key": "data_analysis_library",
      "value": "pandas",
      "created": "2025-05-31"
    }
  ],
  "top_observations": [
    {
      "summary": "User prefers Python for data tasks",
      "weight": 0.95
    },
    {
      "summary": "User focuses on data analysis and automation",
      "weight": 0.9
    },
    {
      "summary": "User is most active in the evening (18:00-23:00)",
      "weight": 0.83
    },
    {
      "summary": "User values practical, actionable solutions",
      "weight": 0.78
    },
    {
      "summary": "User iterates quickly and prefers concise replies",
      "weight": 0.74
    }
  ],
  "graph": {
    "categories": [
      {
        "name": "User Preferences",
        "count": 18,
        "color": "#a855f7"
      },
      {
        "name": "Project Context",
        "count": 12,
        "color": "#3b82f6"
      },
      {
        "name": "Technical Notes",
        "count": 10,
        "color": "#22d3ee"
      },
      {
        "name": "Observations",
        "count": 45,
        "color": "#f472b6"
      }
    ],
    "total_nodes": 128,
    "connections": 342
  },
  "evolution": {
    "current_version": "V2.1",
    "evolved_pct": 85,
    "performance_gain": "+24%",
    "runs": 18,
    "success_rate": 94.4,
    "history": [
      {
        "version": "V2.1",
        "date": "May 18, 2025",
        "success": 94.4,
        "gain": "+24%",
        "latest": true
      },
      {
        "version": "V2.0",
        "date": "May 10, 2025",
        "success": 91.2,
        "gain": "+18%"
      },
      {
        "version": "V1.9",
        "date": "May 02, 2025",
        "success": 95.1,
        "gain": "+15%"
      },
      {
        "version": "V1.8",
        "date": "Apr 21, 2025",
        "success": 93.3,
        "gain": "+12%"
      },
      {
        "version": "V1.7",
        "date": "Apr 09, 2025",
        "success": 90.0,
        "gain": "+9%"
      }
    ],
    "before_after": {
      "accuracy": {
        "before": 78.3,
        "after": 97.1
      },
      "latency": {
        "before": 1280,
        "after": 820
      }
    },
    "neural_focus": [
      {
        "name": "Context Understanding",
        "pct": 92
      },
      {
        "name": "Response Accuracy",
        "pct": 97
      },
      {
        "name": "Latency Reduction",
        "pct": 88
      },
      {
        "name": "Knowledge Integration",
        "pct": 85
      },
      {
        "name": "Tool Usage Efficiency",
        "pct": 91
      }
    ]
  },
  "chat": {
    "confidence": 98,
    "messages": [
      {
        "role": "user",
        "text": "What programming language do I use the most in my projects?"
      },
      {
        "role": "agent",
        "text": "Based on my analysis, you use Python the most in your projects. It appears in 78% of your repositories and recent conversations."
      }
    ],
    "thought_process": [
      {
        "group": "Memory Retrieval",
        "steps": [
          "Retrieving fact: favorite_language -> Python",
          "Retrieving fact: top_languages",
          "Retrieving context: recent_projects (12 found)"
        ]
      },
      {
        "group": "Knowledge Search",
        "steps": [
          "Searching GitHub repositories (found 34)",
          "Analyzing language distribution: Python 78%"
        ]
      },
      {
        "group": "Database Query",
        "steps": [
          "SELECT * FROM projects",
          "Found 156 relevant records"
        ]
      }
    ]
  },
  "dev_metrics": {
    "test_coverage": "92.4%",
    "ci_status": "Passed",
    "latest_pr": "feat: modernize SakThai-Agent dashboard UI",
    "repo_health": "Stable"
  }
};
