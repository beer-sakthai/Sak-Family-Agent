#!/usr/bin/env python3
"""Build SakThai synthetic tool-calling SFT data.


Emits JSONL rows in Qwen-friendly format:
    {"tools": [<openai-style function defs>], "messages": [system, user, assistant(+tool_calls)]}

Pure stdlib — no heavy deps. Covers all 8 BUILTIN_TOOLS plus "no-tool" negatives
so the model learns when NOT to call a tool.
"""

import json
import random
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

random.seed(7)

SYSTEM_PROMPT = (
    "You are SakThai-Agent, Beer's Growth Partner. You are a sharp, calm, and direct assistant. "
    "Be helpful, honest, and concise. "
    "When a task requires an action, call the appropriate tool. Otherwise, answer directly."
)

# OpenAI-style function definitions (what Qwen's chat template consumes via `tools=`).
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "learn",
            "description": "Save a fact about the user into persistent SakThai memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {"type": "string", "description": "The fact text."},
                    "kind": {"type": "string", "description": "Category e.g. note, pref, project."},
                    "key": {"type": "string", "description": "Optional key/name for the fact."},
                },
                "required": ["value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recall",
            "description": "List facts and observations currently stored in SakThai memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Maximum entries per section."}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search SakThai facts and observations for matching substrings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The substring search term."},
                    "limit": {"type": "integer", "description": "Maximum entries per section."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "forget",
            "description": "Delete a fact from SakThai memory by its integer id.",
            "parameters": {
                "type": "object",
                "properties": {"fact_id": {"type": "integer", "description": "The fact id."}},
                "required": ["fact_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a local text file from disk (truncated at 20,000 chars).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative path."}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a CLI command and return its output and exit code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The command line to run."},
                    "timeout": {"type": "number", "description": "Timeout seconds (1-120)."},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_telegram_message",
            "description": "Send a text message to Telegram.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "The message body to send."}
                },
                "required": ["message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_agent_loop",
            "description": "Run a high-level task through the full SakThai agent loop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "The high-level task to execute."},
                    "model": {"type": "string", "description": "Optional model override."},
                    "provider": {"type": "string", "description": "Optional provider backend."},
                    "max_iterations": {"type": "integer", "description": "Max tool-use cap."},
                    "prune_history": {
                        "type": "boolean",
                        "description": "Return only final answer.",
                    },
                },
                "required": ["task"],
            },
        },
    },
]

# Create a mapping from tool name to its definition for easier lookup
TOOL_MAP = {tool["function"]["name"]: tool for tool in TOOLS}


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
SEARCH_TOPICS = [
    "my startup",
    "python preferences",
    "birthdays",
    "allergies",
    "work schedule",
    "the sakthai repo",
    "cooking goals",
    "ui settings",
]
FILES = [
    "~/notes.md",
    "./README.md",
    "/home/sakthai/income-plan.md",
    "todo.md",
    "~/.config/sakthai/config.toml",
    "report.md",
    "SOUL.md",
]
COMMANDS = [
    "ls -l",
    "git status",
    "uv run pytest",
    "df -h",
    "uname -a",
    "git log --oneline -5",
    "cat pyproject.toml",
    "pwd",
    "ls -F src/",
    "git diff --stat",
    'grep -r "TODO" .',
    'find . -name "*.py" | wc -l',
    "pytest -k test_memory_store -v",
]
TG_MSGS = [
    "Standup in 10 minutes",
    "Deploy finished successfully",
    "Don't forget to call the bank",
    "Tests are green on main",
    "Lunch at 1pm today?",
    "Backup completed overnight",
]
BIG_TASKS = [
    "clean up my downloads folder and summarise what was there",
    "review the open PRs in sakthai-agent-v2 and report blockers",
    "find all TODO comments in the repo and list them",
    "set up a daily backup of my memory store",
    "audit my project for leftover debug prints",
]

CHAINED_TASKS = [
    (
        "Find the main readme file and show me what's inside.",
        "find . -name README.md",
        "[exit 0]\n./README.md",
        "./README.md",
    ),
    (
        "List the markdown files and then read the first one you find.",
        "ls *.md",
        "[exit 0]\nCONTRIBUTING.md\nREADME.md",
        "CONTRIBUTING.md",
    ),
]

CHAINED_FAILURE_TASKS = [
    (
        "Find the 'config.yaml' file and read it for me.",
        "find . -name config.yaml",
        "[exit 1]",  # find returns 1 if no files are found
        "I couldn't find a file named 'config.yaml' in the current directory.",
    ),
    (
        "What's in the 'nonexistent_folder/' directory?",
        "ls nonexistent_folder/",
        "[exit 2]\n[stderr]\nls: cannot access 'nonexistent_folder/': No such file or directory",
        "I couldn't list the contents of 'nonexistent_folder/' because the directory does not exist.",
    ),
]


# ---- Example Generators (Class-based approach) ----


class ExampleGenerator:
    """Base class for generating training examples."""

    def generate(self) -> Iterable[dict[str, Any]]:
        raise NotImplementedError


@dataclass
class SingleToolCallGenerator(ExampleGenerator):
    """Generates examples for a single tool call."""

    tool_name: str
    templates: list[str]
    items: Iterable[Any]
    arg_builder: Callable[[Any], dict[str, Any]]
    sample_size: int = 1

    def generate(self) -> Iterable[dict[str, Any]]:
        for item in self.items:
            for template in random.sample(
                self.templates, min(self.sample_size, len(self.templates))
            ):
                user_text = template.format(item=item) if "{item}" in template else template
                args = self.arg_builder(item)
                yield {
                    "tools": TOOLS,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_text},
                        {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [
                                {
                                    "type": "function",
                                    "function": {"name": self.tool_name, "arguments": args},
                                }
                            ],
                        },
                    ],
                }


@dataclass
class ChainedSuccessGenerator(ExampleGenerator):
    """Generates successful multi-turn tool-chaining examples."""

    tasks: list[tuple[str, str, str, str]]
    templates: list[str]

    def generate(self) -> Iterable[dict[str, Any]]:
        for task, cmd, cmd_output, file_to_read in self.tasks:
            user_text = random.choice(self.templates).format(t=task.lower())
            yield {
                "tools": TOOLS,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text},
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "type": "function",
                                "function": {"name": "run_command", "arguments": {"command": cmd}},
                            }
                        ],
                    },
                    {"role": "tool", "content": cmd_output, "tool_call_id": None},
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "type": "function",
                                "function": {
                                    "name": "read_file",
                                    "arguments": {"path": file_to_read},
                                },
                            }
                        ],
                    },
                ],
            }


@dataclass
class ChainedFailureGenerator(ExampleGenerator):
    """Generates failed multi-turn tool-chaining examples."""

    tasks: list[tuple[str, str, str, str]]
    templates: list[str]

    def generate(self) -> Iterable[dict[str, Any]]:
        for task, cmd, cmd_output, assistant_reply in self.tasks:
            user_text = random.choice(self.templates).format(t=task.lower())
            yield {
                "tools": TOOLS,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text},
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "type": "function",
                                "function": {"name": "run_command", "arguments": {"command": cmd}},
                            }
                        ],
                    },
                    {"role": "tool", "content": cmd_output, "tool_call_id": None},
                    {"role": "assistant", "content": assistant_reply, "tool_calls": []},
                ],
            }


@dataclass
class DirectAnswerGenerator(ExampleGenerator):
    """Generates examples where the agent answers directly without tools."""

    items: list[tuple[str, str]]

    def generate(self) -> Iterable[dict[str, Any]]:
        for user_text, answer in self.items:
            yield {
                "tools": TOOLS,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text},
                    {"role": "assistant", "content": answer, "tool_calls": []},
                ],
            }


# ---- negatives: answer directly, no tool call ----
NEGATIVES = [
    ("Hey, how are you?", "I'm sharp and ready. What are we working on?"),
    (
        "What does the Dream stage mean?",
        "Dream is where we name the ambition plainly — the outcome you actually want before we plan toward it.",
    ),
    ("Thanks, that's helpful!", "Good. What's next?"),
    (
        "Tell me a fact about the ocean.",
        "The ocean holds about 97% of Earth's water and produces over half its oxygen.",
    ),
    (
        "Who are you?",
        "I'm SakThai-Agent — Beer's Growth Partner, here to move you through Dream, Hope, Care, Joy, Trust, and Growth.",
    ),
    ("What's 12 times 11?", "132."),
    ("What is the capital of France?", "Paris."),
    ("Can you help me with something?", "Of course. What's the task?"),
    (
        "What can you do?",
        "I can help you with tasks by using tools like reading files, running commands, and managing a persistent memory of facts. I can also answer questions directly.",
    ),
    ("Okay, sounds good.", "Great. What's our next step?"),
    (
        "Explain the concept of recursion in programming.",
        "Recursion is a method where a function calls itself to solve a problem. It breaks down a problem into smaller, identical sub-problems until it reaches a base case that can be solved directly.",
    ),
    ("Who wrote Hamlet?", "William Shakespeare."),
    ("What's the weather like?", "I can't check real-time information like the weather."),
    (
        "How do I declare a variable in Python?",
        "You can declare a variable in Python by assigning a value to a name, like `my_variable = 10`.",
    ),
    ("Good morning!", "Good morning. I'm ready to get started."),
]


def build():
    """Generates the full dataset."""
    all_rows: list[dict[str, Any]] = []
    generators: list[ExampleGenerator] = [
        SingleToolCallGenerator(
            tool_name="learn",
            templates=[
                "Remember that {item[0]}.",
                "Note for later: {item[0]}.",
                "Save this: {item[0]}.",
            ],
            items=FACTS,
            arg_builder=lambda item: {"value": item[0], "kind": item[1], "key": item[2]},
            sample_size=3,
        ),
        SingleToolCallGenerator(
            tool_name="recall",
            templates=[
                "What do you know about me?",
                "List everything in your memory.",
                "Show me my stored facts.",
            ],
            items=[None] * 6,  # Run 6 times with different random args
            arg_builder=lambda _: (
                {} if random.random() < 0.5 else {"limit": random.choice([10, 20, 50])}
            ),
        ),
        SingleToolCallGenerator(
            tool_name="search",
            templates=[
                "Do you have anything saved about {item}?",
                "Search your memory for {item}.",
            ],
            items=SEARCH_TOPICS,
            arg_builder=lambda item: {"query": item},
            sample_size=2,
        ),
        SingleToolCallGenerator(
            tool_name="forget",
            templates=["{item[0]}"],
            items=[
                ("Delete fact 5.", 5),
                ("Forget memory id 12.", 12),
                ("Remove the fact numbered 3.", 3),
            ],
            arg_builder=lambda item: {"fact_id": item[1]},
        ),
        SingleToolCallGenerator(
            tool_name="read_file",
            templates=["Read {item} for me.", "What's in {item}?"],
            items=FILES,
            arg_builder=lambda item: {"path": item},
        ),
        SingleToolCallGenerator(
            tool_name="run_command",
            templates=["Run `{item}`.", "Execute {item}."],
            items=COMMANDS,
            arg_builder=lambda item: (
                {"command": item, "timeout": random.choice([10, 60, 120])}
                if random.random() < 0.3
                else {"command": item}
            ),
        ),
        SingleToolCallGenerator(
            tool_name="send_telegram_message",
            templates=["Text me: {item}", "Send a Telegram saying '{item}'."],
            items=TG_MSGS,
            arg_builder=lambda item: {"message": item},
        ),
        SingleToolCallGenerator(
            tool_name="run_agent_loop",
            templates=["Go ahead and {item}.", "Handle this end to end: {item}."],
            items=BIG_TASKS,
            arg_builder=lambda item: (
                {"task": item, "max_iterations": random.choice([6, 12, 20])}
                if random.random() < 0.3
                else {"task": item}
            ),
        ),
        ChainedSuccessGenerator(
            tasks=CHAINED_TASKS,
            templates=["Can you {t}", "I need you to {t}", "Please {t}"],
        ),
        ChainedFailureGenerator(
            tasks=CHAINED_FAILURE_TASKS,
            templates=["Could you {t}", "Please try to {t}", "I need you to {t}"],
        ),
        DirectAnswerGenerator(items=NEGATIVES),
    ]

    for gen in generators:
        all_rows.extend(gen.generate())

    random.shuffle(all_rows)
    return all_rows


if __name__ == "__main__":
    rows = build()
    out = Path(__file__).parent / "sakthai_toolcalling_synthetic.jsonl"
    with out.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    # quick stats
    single_tool_calls = sum(
        1 for r in rows if len(r["messages"]) == 3 and r["messages"][-1].get("tool_calls")
    )
    chained_success_calls = sum(
        1 for r in rows if len(r["messages"]) == 5 and r["messages"][-1].get("tool_calls")
    )
    chained_failure_calls = sum(
        1 for r in rows if len(r["messages"]) == 5 and not r["messages"][-1].get("tool_calls")
    )
    no_tool_calls = len(rows) - single_tool_calls - chained_success_calls - chained_failure_calls
    print(
        f"Wrote {len(rows)} rows to {out} ({single_tool_calls} single-tool, "
        f"{chained_success_calls} chained-success, {chained_failure_calls} chained-failure, "
        f"{no_tool_calls} no-tool)"
    )
