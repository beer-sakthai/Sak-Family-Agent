#!/usr/bin/env python3
"""Build SakThai synthetic tool-calling SFT data.

Emits JSONL rows in Qwen-friendly format:
    {"tools": [<openai-style function defs>], "messages": [system, user, assistant(+tool_calls)]}

Pure stdlib — no heavy deps. Covers all 8 BUILTIN_TOOLS plus "no-tool" negatives
so the model learns when NOT to call a tool.
"""
import json
import random
from pathlib import Path

random.seed(7)

SYSTEM_PROMPT = (
    "You are SakThai-Agent, Beer's Growth Partner. You are sharp, calm, and direct. "
    "You operate within the 6-stage cycle: Dream, Hope, Care, Joy, Trust, and Growth. "
    "Always be helpful, honest, and protective. Skip filler and be concise. "
    "When a task needs an action, call the appropriate tool. Otherwise answer directly."
)

# OpenAI-style function definitions (what Qwen's chat template consumes via `tools=`).
TOOLS = [
    {"type": "function", "function": {"name": "learn",
        "description": "Save a fact about the user into persistent SakThai memory.",
        "parameters": {"type": "object", "properties": {
            "value": {"type": "string", "description": "The fact text."},
            "kind": {"type": "string", "description": "Category e.g. note, pref, project."},
            "key": {"type": "string", "description": "Optional key/name for the fact."}},
            "required": ["value"]}}},
    {"type": "function", "function": {"name": "recall",
        "description": "List facts and observations currently stored in SakThai memory.",
        "parameters": {"type": "object", "properties": {
            "limit": {"type": "integer", "description": "Maximum entries per section."}}}}},
    {"type": "function", "function": {"name": "search",
        "description": "Search SakThai facts and observations for matching substrings.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "The substring search term."},
            "limit": {"type": "integer", "description": "Maximum entries per section."}},
            "required": ["query"]}}},
    {"type": "function", "function": {"name": "forget",
        "description": "Delete a fact from SakThai memory by its integer id.",
        "parameters": {"type": "object", "properties": {
            "fact_id": {"type": "integer", "description": "The fact id."}},
            "required": ["fact_id"]}}},
    {"type": "function", "function": {"name": "read_file",
        "description": "Read a local text file from disk (truncated at 20,000 chars).",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Absolute or relative path."}},
            "required": ["path"]}}},
    {"type": "function", "function": {"name": "run_command",
        "description": "Execute a CLI command and return its output and exit code.",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string", "description": "The command line to run."},
            "timeout": {"type": "number", "description": "Timeout seconds (1-120)."}},
            "required": ["command"]}}},
    {"type": "function", "function": {"name": "send_telegram_message",
        "description": "Send a text message to Telegram.",
        "parameters": {"type": "object", "properties": {
            "message": {"type": "string", "description": "The message body to send."}},
            "required": ["message"]}}},
    {"type": "function", "function": {"name": "run_agent_loop",
        "description": "Run a high-level task through the full SakThai agent loop.",
        "parameters": {"type": "object", "properties": {
            "task": {"type": "string", "description": "The high-level task to execute."},
            "model": {"type": "string", "description": "Optional model override."},
            "provider": {"type": "string", "description": "Optional provider backend."},
            "max_iterations": {"type": "integer", "description": "Max tool-use cap."},
            "prune_history": {"type": "boolean", "description": "Return only final answer."}},
            "required": ["task"]}}},
]

# ---- generators per tool: (user_text, tool_name, arguments) ----

FACTS = [
    ("I prefer dark mode in all my apps", "pref", "ui_theme"),
    ("My startup is called Growth Partner", "project", "startup_name"),
    ("I work best in the early morning", "pref", "work_schedule"),
    ("My sister's birthday is March 3rd", "note", "sister_birthday"),
    ("I'm learning Thai cooking this year", "note", "goal"),
    ("I use uv, never pip, for Python", "pref", "python_tooling"),
    ("My main repo is sakthai-agent-v2", "project", "main_repo"),
    ("I'm allergic to peanuts", "note", "allergy"),
]
SEARCH_TOPICS = ["my startup", "python preferences", "birthdays", "allergies",
                 "work schedule", "the sakthai repo", "cooking goals", "ui settings"]
FILES = ["~/notes.md", "./README.md", "/home/sakthai/income-plan.md", "todo.md",
         "~/.config/sakthai/config.toml", "report.md", "SOUL.md"]
COMMANDS = ["ls -la", "git status", "uv run pytest", "df -h", "uname -a",
            "git log --oneline -5", "cat pyproject.toml", "whoami"]
TG_MSGS = ["Standup in 10 minutes", "Deploy finished successfully",
           "Don't forget to call the bank", "Tests are green on main",
           "Lunch at 1pm today?", "Backup completed overnight"]
BIG_TASKS = ["clean up my downloads folder and summarise what was there",
             "review the open PRs in sakthai-agent-v2 and report blockers",
             "find all TODO comments in the repo and list them",
             "set up a daily backup of my memory store",
             "audit my project for leftover debug prints"]


def learn_rows():
    tmpl = ["Remember that {f}.", "Note for later: {f}.", "Save this: {f}.",
            "Keep in mind {f}.", "FYI, {f} — hold onto that."]
    for value, kind, key in FACTS:
        for t in random.sample(tmpl, 3):
            yield t.format(f=value.lower()), "learn", {"value": value, "kind": kind, "key": key}


def recall_rows():
    for u in ["What do you know about me?", "List everything in your memory.",
              "Show me my stored facts.", "Remind me what we've saved so far.",
              "Dump your memory.", "What's in long-term memory right now?"]:
        args = {} if random.random() < 0.5 else {"limit": random.choice([10, 20, 50])}
        yield u, "recall", args


def search_rows():
    tmpl = ["Do you have anything saved about {q}?", "Search your memory for {q}.",
            "Find notes related to {q}.", "What do you remember about {q}?"]
    for q in SEARCH_TOPICS:
        for t in random.sample(tmpl, 2):
            yield t.format(q=q), "search", {"query": q}


def forget_rows():
    for u, fid in [("Delete fact 5.", 5), ("Forget memory id 12.", 12),
                   ("Remove the fact numbered 3.", 3), ("Drop entry 27 from memory.", 27),
                   ("That fact 9 is wrong, delete it.", 9)]:
        yield u, "forget", {"fact_id": fid}


def read_file_rows():
    tmpl = ["Read {p} for me.", "What's in {p}?", "Open {p} and show me.",
            "Pull up the contents of {p}."]
    for p in FILES:
        yield random.choice(tmpl).format(p=p), "read_file", {"path": p}


def run_command_rows():
    tmpl = ["Run `{c}`.", "Execute {c}.", "Can you run {c} for me?", "Shell: {c}"]
    for c in COMMANDS:
        args = {"command": c}
        if random.random() < 0.3:
            args["timeout"] = random.choice([10, 60, 120])
        yield random.choice(tmpl).format(c=c), "run_command", args


def telegram_rows():
    tmpl = ["Text me: {m}", "Send a Telegram saying '{m}'.", "Ping me on Telegram: {m}",
            "Message me '{m}' on Telegram."]
    for m in TG_MSGS:
        yield random.choice(tmpl).format(m=m), "send_telegram_message", {"message": m}


def agent_loop_rows():
    tmpl = ["Go ahead and {t}.", "Handle this end to end: {t}.",
            "Take care of this task: {t}.", "I need you to {t} — run with it."]
    for t in BIG_TASKS:
        args = {"task": t}
        if random.random() < 0.3:
            args["max_iterations"] = random.choice([6, 12, 20])
        yield random.choice(tmpl).format(t=t), "run_agent_loop", args


# ---- negatives: answer directly, no tool call ----
NEGATIVES = [
    ("Hey, how are you?", "I'm sharp and ready. What are we working on?"),
    ("What does the Dream stage mean?", "Dream is where we name the ambition plainly — the outcome you actually want before we plan toward it."),
    ("Thanks, that's helpful!", "Good. What's next?"),
    ("Tell me a fact about the ocean.", "The ocean holds about 97% of Earth's water and produces over half its oxygen."),
    ("Who are you?", "I'm SakThai-Agent — Beer's Growth Partner, here to move you through Dream, Hope, Care, Joy, Trust, and Growth."),
    ("What's 12 times 11?", "132."),
]


def build():
    rows = []
    for gen in (learn_rows, recall_rows, search_rows, forget_rows, read_file_rows,
                run_command_rows, telegram_rows, agent_loop_rows):
        for user_text, name, args in gen():
            rows.append({
                "tools": TOOLS,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text},
                    {"role": "assistant", "content": "",
                     "tool_calls": [{"type": "function",
                                     "function": {"name": name, "arguments": args}}]},
                ],
            })
    for user_text, answer in NEGATIVES:
        rows.append({
            "tools": TOOLS,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": answer},
            ],
        })
    random.shuffle(rows)
    return rows


if __name__ == "__main__":
    rows = build()
    out = Path("sakthai_toolcalling_synthetic.jsonl")
    with out.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    # quick stats
    tool_calls = sum(1 for r in rows if "tool_calls" in r["messages"][-1])
    print(f"wrote {len(rows)} rows -> {out}  ({tool_calls} tool-call, {len(rows)-tool_calls} no-tool)")
