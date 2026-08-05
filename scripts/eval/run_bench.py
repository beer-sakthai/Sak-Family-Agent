"""Bench runner and scorer for sakthai-bench-v3 (eval_results YAML output)."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import yaml

KNOWN_CATEGORIES = {
    "simple",
    "parallel",
    "held_out",
    "irrelevance_tools",
    "irrelevance_no_tools",
    "multi_turn",
    "irrelevance",
}


def parse_tool_calls(text: str) -> list[dict]:
    calls: list[dict] = []
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                chunk = text[start : i + 1]
                start = -1
                try:
                    obj = json.loads(chunk)
                except json.JSONDecodeError:
                    continue
                if (
                    isinstance(obj, dict)
                    and isinstance(obj.get("name"), str)
                    and isinstance(obj.get("arguments"), dict)
                ):
                    calls.append({"name": obj["name"], "arguments": obj["arguments"]})
                elif isinstance(obj.get("function"), dict) and isinstance(
                    obj["function"].get("name"), str
                ):
                    calls.append(
                        {
                            "name": obj["function"]["name"],
                            "arguments": obj["function"].get("arguments", {}),
                        }
                    )
    return calls


def score_sample(predicted: str, expected: list[dict]) -> tuple[bool, bool]:
    got = parse_tool_calls(predicted)
    got_names = {c["name"] for c in got}
    if expected and isinstance(expected[0], str):
        selection = got_names == set(expected)
        return selection, selection  # no argument specs in this dataset
    expected_names = {e["name"] for e in expected}
    selection = got_names == expected_names
    if not selection:
        return False, False
    by_name = {c["name"]: c["arguments"] for c in got}
    for exp in expected:
        args = by_name.get(exp["name"], {})
        if any(args.get(k) != v for k, v in exp.get("arguments", {}).items()):
            return True, False
    return True, True


def _pct(ok: int, total: int) -> float:
    return round(ok / total * 100, 2) if total else 0.0


def aggregate(results: list[dict]) -> dict:
    categories: dict[str, dict] = {}
    unknown = 0
    for row in results:
        cat = row["category"]
        if cat not in KNOWN_CATEGORIES:
            unknown += 1
            continue
        entry = categories.setdefault(
            cat, {"count": 0, "selection": 0, "arguments": 0, "strict": 0}
        )
        entry["count"] += 1
        entry["selection"] += int(row["selection"])
        entry["arguments"] += int(row["arguments"])
        entry["strict"] += int(row["selection"] and row["arguments"])
    total = sum(e["count"] for e in categories.values())
    strict_total = sum(e["strict"] for e in categories.values())
    cats_out = {
        cat: {
            "count": e["count"],
            "selection": _pct(e["selection"], e["count"]),
            "arguments": _pct(e["arguments"], e["count"]),
            "strict": _pct(e["strict"], e["count"]),
        }
        for cat, e in categories.items()
    }
    overall = {
        "selection": _pct(sum(e["selection"] for e in categories.values()), total),
        "arguments": _pct(sum(e["arguments"] for e in categories.values()), total),
        "strict": _pct(strict_total, total),
    }
    return {"overall": overall, "categories": cats_out, "unknown_count": unknown}


def render_yaml(
    aggregate: dict, model: str, benchmark: str, run_id: str, status: str, summary: str
) -> str:
    doc = {
        "backend": "run_bench",
        "benchmark_id": f"hf-benchmark-run-{run_id}",
        "completed_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "model": model,
        "benchmark": benchmark,
        "run_id": run_id,
        "status": status,
        "scores": aggregate,
        "summary": summary,
    }
    return yaml.safe_dump(doc, sort_keys=False)


def run_bench(rows: list[dict], predict: Callable[[list[dict], list[dict]], str]) -> list[dict]:
    results = []
    for row in rows:
        predicted = predict(row.get("messages", []), row.get("tools", []))
        selection, arguments = score_sample(predicted, row.get("expected_tools", []))
        results.append(
            {
                "category": row.get("category", "unknown"),
                "selection": selection,
                "arguments": arguments,
            }
        )
    return results


def _load_rows(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text().splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run sakthai bench eval and emit eval_results YAML"
    )
    parser.add_argument("--dataset", type=Path, required=True, help="path to bench JSONL")
    parser.add_argument("--model", required=True)
    parser.add_argument("--smoke", type=int, default=0, help="limit to N rows")
    parser.add_argument("--out", type=Path, default=Path("benchmark-result.yaml"))
    parser.add_argument("--run-id", default=datetime.now(UTC).strftime("%Y%m%d_%H%M%S"))
    parser.add_argument(
        "--publish", action="store_true", help="upload YAML to Nanthasit/eval_results"
    )
    args = parser.parse_args()

    def predict(messages: list[dict], tools: list[dict]) -> str:
        try:
            import transformers  # noqa: F401
        except ImportError as exc:
            raise RuntimeError("transformers not installed; cannot run a real model") from exc
        raise NotImplementedError("real inference dispatch is run-time only (see runbook)")

    rows = _load_rows(args.dataset)
    if args.smoke:
        rows = rows[: args.smoke]
    results = run_bench(rows, predict)
    agg = aggregate(results)
    text = render_yaml(
        agg,
        model=args.model,
        benchmark=args.dataset.stem,
        run_id=args.run_id,
        status="completed",
        summary=f"{len(results)} samples",
    )
    args.out.write_text(text)
    print(text)
    if args.publish:
        raise NotImplementedError("publish dispatch is run-time only (see runbook)")


if __name__ == "__main__":
    main()
