"""Before/after regression report between two eval_results YAML files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def load_results(path: Path) -> dict:
    doc = yaml.safe_load(path.read_text())
    if "scores" not in doc or "categories" not in doc.get("scores", {}):
        raise ValueError(f"{path}: missing scores.categories")
    return doc


def compare(prev: dict, new: dict, targets: dict[str, float]) -> list[dict]:
    prev_cats = prev["scores"]["categories"]
    new_cats = new["scores"]["categories"]
    rows = []
    for cat in sorted(set(prev_cats) | set(new_cats)):
        p = prev_cats.get(cat, {}).get("strict", 0.0)
        n = new_cats.get(cat, {}).get("strict", 0.0)
        target = targets.get(cat)
        if target is not None and n >= target:
            status = "pass"
        elif n < p:
            status = "regression"
        else:
            status = "improved"
        rows.append(
            {"category": cat, "prev": p, "new": n, "delta": round(n - p, 2), "status": status}
        )
    return rows


def render_report(comparison: list[dict], models: tuple[str, str]) -> str:
    prev_model, new_model = models
    lines = [
        f"# Regression report: {prev_model} -> {new_model}",
        "",
        "| Category | Prev | New | Delta | Status |",
        "|---|---|---|---|---|",
    ]
    for row in comparison:
        lines.append(
            f"| {row['category']} | {row['prev']} | {row['new']} | {row['delta']} | {row['status']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two eval_results YAML files")
    parser.add_argument("--prev", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    parser.add_argument(
        "--targets",
        type=json.loads,
        default='{"simple": 60, "parallel": 60, "held_out": 40, "irrelevance_tools": 60, "irrelevance_no_tools": 95}',
    )
    args = parser.parse_args()
    report = render_report(
        compare(load_results(args.prev), load_results(args.new), args.targets),
        (args.prev.stem, args.new.stem),
    )
    print(report)


if __name__ == "__main__":
    main()
