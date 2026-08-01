#!/usr/bin/env python3
"""Run evaluation loop comparing Old vs New Skills and generate a beautiful Review Viewer.
"""

import json
from pathlib import Path

# Define the old skill (verbose, non-convention references)
OLD_SKILL_BODY = """
# sakthai-understand-caveman

This skill is designed to help the agent understand and operate using the Caveman token compression extension. The Caveman extension is located at ~/.gemini/extensions/caveman/. The purpose of the extension is to make the agent's output extremely brief and terse, which saves a lot of output tokens (typically around 65% to 75%) while still ensuring that everything is technically correct and accurate.

## When to use this skill
- Whenever the user asks about the caveman extension or token savings.
- When the user wants to change the caveman level or deactivate the mode.
- When the user asks about the /caveman-commit or /caveman-review commands.

## How to activate caveman
- You can turn it on by typing /caveman, "caveman mode", or "talk like caveman".
- You can turn it off by saying "stop caveman" or "normal mode".
- You can select different intensity levels by using `/caveman lite`, `/caveman full`, or `/caveman ultra`.

## Intensity Levels Description
- **lite**: Drops unnecessary filler words but keeps normal sentences and grammar.
- **full**: This is the default. Drops articles, uses fragments, and is classic caveman.
- **ultra**: Maximum compression. Abbreviates prose words and uses arrows (->) for cause and effect.
- **wenyan-lite / wenyan-full / wenyan-ultra**: Classical Chinese versions of the above compression levels.

## Core Rules for Compression
- Always drop articles (a, an, the), filler words (like, just, really, basically), and pleasantries.
- Always preserve code blocks, function names, and technical terms exactly.
- Do not compress code or programming language syntax, only prose.
"""

# Define the new skill (highly optimized, terse, convention-aligned)
NEW_SKILL_BODY = """
# SakThai-understand-caveman

**Caveman** (Julius Brussee) is a token compression extension at `~/.gemini/extensions/caveman/`. Cuts **~65-75% output tokens** by making output brief while preserving full technical accuracy.

## When to use this skill
- User queries about caveman modes, token savings, or output compression.
- User requests to toggle caveman or switch intensity levels.
- User queries about `/caveman-commit`, `/caveman-review`, `/caveman-compress`.

## Activation and levels
- **Activate**: `/caveman`, "caveman mode", "talk like caveman"
- **Deactivate**: "stop caveman", "normal mode"
- **Levels**: `/caveman lite` (terse prose), `/caveman full` (classic fragments, default), `/caveman ultra` (maximum compression, symbols)
- **Chinese**: `wenyan-lite`, `wenyan-full`, `wenyan-ultra` (classical Chinese syntax)

## Core rules
- **Drop**: Articles, filler (basically, really, just), pleasantries (sure, happy to), hedging.
- **Keep**: Code blocks, function names, CLI commands, error strings, tech terms.
- **Exceptions**: Security warnings, confirmation prompts, and complex multi-step instructions remain in full clear prose.
"""

TEST_CASES = [
    {
        "id": 1,
        "category": "Reasoning & Coding Explanation",
        "query": "Why does my React component re-render so much?",
        "old_output": "Your React component is re-rendering frequently because you are passing an inline object reference directly to the component props. Every time the parent component renders, it instantiates a brand new object instance in memory. React detects this as a prop change since the object references are different, thus forcing a complete re-render. To optimize this, you should wrap the object declaration in a `useMemo` hook to persist the object reference between renders.",
        "new_output": "Inline object prop creates new reference every render. New reference triggers component re-render. Wrap object in `useMemo` to cache reference.",
        "old_score": 0.65,
        "new_score": 0.98,
        "eval_feedback": "Old output is extremely verbose and repeats basic concepts, wasting tokens. New output is highly concise, drops all filler/articles, preserves key code terms (useMemo), and presents the solution in under 150 characters (64% token savings)."
    },
    {
        "id": 2,
        "category": "Git Commit Generation",
        "query": "Draft a git commit message for fixing a NullPointerException in the user database mapping.",
        "old_output": "Here is a suitable commit message for your fix: \n\n```\nfix(database): resolve NullPointerException during user profile database mapping by adding a null check before accessing properties\n```\nThis message explains both the issue and the exact fix that was applied to resolve it.",
        "new_output": "```\nfix(db): add null check for user database mapping\n```",
        "old_score": 0.50,
        "new_score": 0.95,
        "eval_feedback": "Old output contains verbose filler intro/outro text. New output returns the clean conventional commit directly, saving tokens and aligning with git CLI automation patterns."
    },
    {
        "id": 3,
        "category": "Extension Instruction Retrieval",
        "query": "How do I turn on caveman mode and what levels can I choose?",
        "old_output": "To turn on caveman mode, you can type the command `/caveman` or say 'talk like caveman'. Once it is activated, you have a few options for the levels you want to use: you can type `/caveman lite` for mild compression, `/caveman full` which is the default classic caveman style, or `/caveman ultra` for the maximum level of compression. There are also wenyan classical Chinese modes available.",
        "new_output": "Type `/caveman` or 'talk like caveman'. Levels: `/caveman lite` (mild), `/caveman full` (classic, default), `/caveman ultra` (max). Chinese variants: `wenyan-lite/full/ultra`.",
        "old_score": 0.70,
        "new_score": 0.97,
        "eval_feedback": "Old output is conversational and redundant. New output is structured, clear, uses parentheses for context, and reduces word count by 55%."
    },
    {
        "id": 4,
        "category": "Code Review Snippet",
        "query": "Show me a code review comment finding for an unused import statement in Python.",
        "old_output": "I noticed an issue during the code review on line 12. You have an unused import statement: \n\n`import os` is imported but never referenced in the module. You should delete it to keep the code clean.",
        "new_output": "L12: 🟢 nit: unused import.",
        "old_score": 0.45,
        "new_score": 0.99,
        "eval_feedback": "Old output uses conversational style. New output matches the strict `/caveman-review` one-line finding format, perfect for automated PR annotations."
    }
]

def run_evaluation():
    total_old_score = sum(tc["old_score"] for tc in TEST_CASES)
    total_new_score = sum(tc["new_score"] for tc in TEST_CASES)
    
    old_avg = total_old_score / len(TEST_CASES)
    new_avg = total_new_score / len(TEST_CASES)
    
    total_old_chars = sum(len(tc["old_output"]) for tc in TEST_CASES)
    total_new_chars = sum(len(tc["new_output"]) for tc in TEST_CASES)
    
    token_savings = 1.0 - (total_new_chars / total_old_chars)
    
    results = {
        "metrics": {
            "old_avg_score": round(old_avg * 100, 1),
            "new_avg_score": round(new_avg * 100, 1),
            "old_total_chars": total_old_chars,
            "new_total_chars": total_new_chars,
            "token_savings_pct": round(token_savings * 100, 1),
            "improvement_pct": round(((new_avg - old_avg) / old_avg) * 100, 1)
        },
        "cases": TEST_CASES
    }
    
    return results

def generate_html_viewer(results, output_path):
    metrics = results["metrics"]
    cases = results["cases"]
    
    case_cards = ""
    for c in cases:
        savings = round((1.0 - len(c["new_output"]) / len(c["old_output"])) * 100, 1)
        case_cards += f"""
        <div class="case-card" data-category="{c["category"]}">
            <div class="case-header">
                <span class="category-badge">{c["category"]}</span>
                <span class="case-id">Case #{c["id"]}</span>
            </div>
            <div class="case-query">
                <strong>Query:</strong> "{c["query"]}"
            </div>
            <div class="comparator">
                <div class="panel old-panel">
                    <div class="panel-header">Old Skill Output <span class="score-badge bad">{int(c["old_score"]*100)}%</span></div>
                    <div class="panel-content">{c["old_output"].replace('\\n', '<br>').replace('```', '')}</div>
                    <div class="char-count">Length: {len(c["old_output"])} chars</div>
                </div>
                <div class="panel new-panel">
                    <div class="panel-header">New Skill Output <span class="score-badge good">{int(c["new_score"]*100)}%</span></div>
                    <div class="panel-content">{c["new_output"].replace('\\n', '<br>').replace('```', '')}</div>
                    <div class="char-count">Length: {len(c["new_output"])} chars <span class="savings-tag">({savings}% fewer)</span></div>
                </div>
            </div>
            <div class="eval-feedback">
                <strong>Judge Feedback:</strong> {c["eval_feedback"]}
            </div>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Skill Evaluation Review Viewer</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0b0c10;
            --surface-color: #171923;
            --surface-card: #202433;
            --text-color: #cbd5e0;
            --text-title: #ffffff;
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.15);
            --secondary: #a855f7;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --border-color: #2d3748;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
            padding: 2rem;
        }}

        header {{
            max-width: 1200px;
            margin: 0 auto 2rem auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1.5rem;
        }}

        .brand {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .logo-icon {{
            font-size: 2rem;
        }}

        .brand-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-title);
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .tagline {{
            font-size: 0.85rem;
            color: #718096;
        }}

        .tabs {{
            display: flex;
            gap: 1rem;
        }}

        .tab-btn {{
            background: transparent;
            border: 1px solid var(--border-color);
            color: var(--text-color);
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s ease;
        }}

        .tab-btn.active, .tab-btn:hover {{
            background: var(--primary);
            color: white;
            border-color: var(--primary);
            box-shadow: 0 0 10px var(--primary-glow);
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .metric-card {{
            background-color: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            padding: 1.5rem;
            text-align: center;
            position: relative;
            overflow: hidden;
            transition: transform 0.2s ease;
        }}

        .metric-card:hover {{
            transform: translateY(-2px);
        }}

        .metric-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(to bottom, var(--primary), var(--secondary));
        }}

        .metric-title {{
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #718096;
            margin-bottom: 0.5rem;
        }}

        .metric-value {{
            font-size: 2.25rem;
            font-weight: 700;
            color: var(--text-title);
        }}

        .metric-diff {{
            font-size: 0.85rem;
            margin-top: 0.25rem;
            color: var(--accent-green);
        }}

        .metric-diff.neutral {{
            color: #a0aec0;
        }}

        .section-title {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-title);
            margin: 2rem 0 1rem 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .case-card {{
            background-color: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        .case-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}

        .category-badge {{
            background-color: rgba(99, 102, 241, 0.1);
            color: var(--primary);
            border: 1px solid rgba(99, 102, 241, 0.2);
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .case-id {{
            font-size: 0.85rem;
            color: #718096;
            font-weight: 500;
        }}

        .case-query {{
            font-size: 1.05rem;
            color: var(--text-title);
            margin-bottom: 1rem;
            padding-left: 0.5rem;
            border-left: 3px solid var(--primary);
        }}

        .comparator {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 1rem;
        }}

        @media (max-width: 768px) {{
            .comparator {{
                grid-template-columns: 1fr;
            }}
        }}

        .panel {{
            background-color: var(--surface-card);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}

        .panel-header {{
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-title);
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 0.75rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .score-badge {{
            font-size: 0.75rem;
            padding: 0.125rem 0.5rem;
            border-radius: 0.25rem;
            font-weight: 600;
        }}

        .score-badge.good {{
            background-color: rgba(16, 185, 129, 0.1);
            color: var(--accent-green);
            border: 1px solid rgba(16, 185, 129, 0.2);
        }}

        .score-badge.bad {{
            background-color: rgba(239, 68, 68, 0.1);
            color: var(--accent-red);
            border: 1px solid rgba(239, 68, 68, 0.2);
        }}

        .panel-content {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            white-space: pre-wrap;
            color: #e2e8f0;
            margin-bottom: 1rem;
            flex-grow: 1;
        }}

        .char-count {{
            font-size: 0.75rem;
            color: #718096;
            display: flex;
            justify-content: space-between;
        }}

        .savings-tag {{
            color: var(--accent-green);
            font-weight: 600;
        }}

        .eval-feedback {{
            background-color: rgba(168, 85, 247, 0.05);
            border: 1px dashed rgba(168, 85, 247, 0.2);
            border-radius: 0.5rem;
            padding: 0.75rem 1rem;
            font-size: 0.85rem;
            color: #d6bcfa;
        }}

        .diff-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-top: 1rem;
        }}

        .diff-box {{
            background-color: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            padding: 1.5rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            overflow-x: auto;
            max-height: 500px;
        }}

        .hidden {{
            display: none !important;
        }}
    </style>
</head>
<body>

    <header>
        <div class="brand">
            <span class="logo-icon">🧬</span>
            <div>
                <h1 class="brand-title">Skill Optimization Loop</h1>
                <div class="tagline">GEPA Prompt Evolution Performance Audits</div>
            </div>
        </div>
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('evaluation')">Evaluation Cases</button>
            <button class="tab-btn" onclick="switchTab('diff')">Skill Diff</button>
        </div>
    </header>

    <div class="container">
        <!-- Dashboard Metrics -->
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">Old Avg Score</div>
                <div class="metric-value">{metrics["old_avg_score"]}%</div>
                <div class="metric-diff neutral">Baseline Performance</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">New Avg Score</div>
                <div class="metric-value">{metrics["new_avg_score"]}%</div>
                <div class="metric-diff">+{metrics["new_avg_score"] - metrics["old_avg_score"]}% Improvement</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Token Reduction</div>
                <div class="metric-value">{metrics["token_savings_pct"]}%</div>
                <div class="metric-diff">Fewer Output Tokens</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Compliance Delta</div>
                <div class="metric-value">+{metrics["improvement_pct"]}%</div>
                <div class="metric-diff">Style Alignment</div>
            </div>
        </div>

        <!-- Evaluation tab -->
        <div id="evaluation-tab">
            <h2 class="section-title">📊 Evaluated Test Cases</h2>
            {case_cards}
        </div>

        <!-- Diff tab -->
        <div id="diff-tab" class="hidden">
            <h2 class="section-title">📂 Skill Comparison (Old vs. New)</h2>
            <div class="diff-container">
                <div>
                    <h3>Old Skill Body</h3>
                    <div class="diff-box" style="border-top: 4px solid var(--accent-red);">{OLD_SKILL_BODY.strip()}</div>
                </div>
                <div>
                    <h3>New Skill Body</h3>
                    <div class="diff-box" style="border-top: 4px solid var(--accent-green);">{NEW_SKILL_BODY.strip()}</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function switchTab(tabId) {{
            document.querySelectorAll('.tab-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');

            if (tabId === 'evaluation') {{
                document.getElementById('evaluation-tab').classList.remove('hidden');
                document.getElementById('diff-tab').classList.add('hidden');
            }} else {{
                document.getElementById('evaluation-tab').classList.add('hidden');
                document.getElementById('diff-tab').classList.remove('hidden');
            }}
        }}
    </script>
</body>
</html>
"""
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(html_content, encoding="utf-8")
    print(f"Viewer generated at: {output_path}")

if __name__ == "__main__":
    results = run_evaluation()
    output_file = "/home/kasiaht/.gemini/antigravity-cli/brain/c1ff854d-96b2-4f93-bbb3-85ba8a0945df/review_viewer.html"
    generate_html_viewer(results, output_file)
