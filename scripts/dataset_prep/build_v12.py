"""Build sakthai-combined-v12 training rows (v10/v11 schema) with category balance."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

SIMPLE_TEMPLATE = (
    'User asks "{topic}". Respond with a single tool call like '
    '<tool_call>{{"name": "get_{topic}", "arguments": {{}}}}</tool_call>.'
)
PARALLEL_TEMPLATE = (
    "Perform these lookups in parallel: {subjects}. Respond with one "
    "<tool_call> block per lookup: {names}."
)
HELD_OUT_TEMPLATE = (
    "You only have the tools listed in the user message. If a requested action "
    "needs a tool that is not listed, say you cannot do it."
)


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_no, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSON") from exc
    return rows


def strip_tags(rows: Iterable[dict]) -> list[dict]:
    return [{k: v for k, v in row.items() if k != "_category"} for row in rows]


def category_report(rows: Iterable[dict]) -> dict[str, int]:
    return dict(Counter(row.get("_category", "source") for row in rows))


def synthesize_simple(topic: str) -> dict:
    name = f"get_{topic.replace(' ', '_')}"
    return {
        "messages": [
            {"role": "user", "content": f"What is the {topic}?"},
            {"role": "assistant", "content": SIMPLE_TEMPLATE.format(topic=topic)},
        ],
        "tools": [
            {"name": name, "description": f"returns the {topic}", "parameters": {"type": "object"}}
        ],
        "_category": "simple",
    }


def synthesize_parallel(subjects: list[str], tools: list[dict]) -> dict:
    names = ", ".join(t["name"] for t in tools)
    return {
        "messages": [
            {
                "role": "user",
                "content": PARALLEL_TEMPLATE.format(subjects=", ".join(subjects), names=names),
            },
            {
                "role": "assistant",
                "content": "<tool_call> parallel calls to " + names + " </tool_call>",
            },
        ],
        "tools": tools,
        "_category": "parallel",
    }


def synthesize_held_out(tools: list[dict]) -> dict:
    names = ", ".join(t["name"] for t in tools)
    return {
        "messages": [
            {"role": "user", "content": f"Available tools: {names}. Please book a flight."},
            {"role": "assistant", "content": "I cannot do that: no booking tool is available."},
        ],
        "tools": tools,
        "_category": "held_out",
    }


def validate_balance(rows: list[dict], min_counts: dict[str, int]) -> None:
    counts = category_report(rows)
    under = [
        f"{cat}={counts.get(cat, 0)}<{min_counts[cat]}"
        for cat in min_counts
        if counts.get(cat, 0) < min_counts[cat]
    ]
    if under:
        raise ValueError("category balance below minimums: " + ", ".join(under))


def build_v12(sources: list[Path], out: Path, report: Path, min_counts: dict[str, int]) -> None:
    rows: list[dict] = []
    for src in sources:
        rows.extend(load_jsonl(src))
    counts = category_report(rows)
    for i in range(min_counts.get("simple", 0) - counts.get("simple", 0)):
        rows.append(synthesize_simple(f"topic{i}"))
    for i in range(min_counts.get("parallel", 0) - counts.get("parallel", 0)):
        rows.append(
            synthesize_parallel(
                [f"subject{i}a", f"subject{i}b"],
                [
                    {"name": f"get_a_{i}", "description": "a", "parameters": {"type": "object"}},
                    {"name": f"get_b_{i}", "description": "b", "parameters": {"type": "object"}},
                ],
            )
        )
    for i in range(min_counts.get("held_out", 0) - counts.get("held_out", 0)):
        rows.append(
            synthesize_held_out(
                [{"name": f"get_x_{i}", "description": "x", "parameters": {"type": "object"}}]
            )
        )
    validate_balance(rows, min_counts)
    out.write_text("\n".join(json.dumps(r) for r in strip_tags(rows)) + "\n")
    report.write_text(json.dumps(category_report(rows), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build sakthai-combined-v12 rows.")
    parser.add_argument("--sources", nargs="+", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument(
        "--min-counts", type=json.loads, default='{"simple": 600, "parallel": 400, "held_out": 200}'
    )
    args = parser.parse_args()
    build_v12(args.sources, args.out, args.report, args.min_counts)


if __name__ == "__main__":
    main()
