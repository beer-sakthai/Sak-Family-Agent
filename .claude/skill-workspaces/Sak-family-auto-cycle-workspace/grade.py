#!/usr/bin/env python3
"""Grade Sak-family-auto-cycle eval runs.

Every assertion here is decided by inspecting the dispatch plan and report the
run produced, so grading is reproducible across iterations instead of being
re-judged by eye each time.

Usage: python3 grade.py <iteration-dir>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PERSONAS = ["sakking", "sakthai", "saksee", "saksit", "sakjules", "saktan"]


def load(run: Path) -> tuple[str, str]:
    out = run / "outputs"
    def read(name: str) -> str:
        f = out / name
        return f.read_text(errors="replace") if f.is_file() else ""
    dispatch = read("dispatch.md")
    if not dispatch:  # fall back to any md that isn't the report
        for f in sorted(out.glob("*.md")):
            if f.name != "report.md":
                dispatch = f.read_text(errors="replace")
                break
    return dispatch, read("report.md")


def count_dispatch_blocks(text: str) -> int:
    """How many distinct persona-targeted `sakthai run` invocations appear."""
    seen = set()
    for m in re.finditer(r"--persona\s+([a-z]+)", text, re.I):
        if m.group(1).lower() in PERSONAS:
            seen.add(m.group(1).lower())
    return len(seen)


def grade(run: Path, live: bool) -> dict:
    dispatch, report = load(run)
    both = dispatch + "\n" + report
    low = both.lower()
    n_runs = len(re.findall(r"sakthai\s+run", both))
    exp: list[dict] = []

    def add(text, passed, evidence):
        exp.append({"text": text, "passed": bool(passed), "evidence": evidence})

    # 1. all six personas addressed
    missing = [p for p in PERSONAS if p not in low]
    add("Dispatches all six personas",
        not missing and n_runs >= 6,
        f"{n_runs} `sakthai run` invocations; missing personas: {missing or 'none'}")

    # 2. one-message fan-out
    serial = re.search(r"one at a time|sequential|serially|then check|wait(ed)? for", low)
    parallel = re.search(r"single message|one message|in parallel|concurrent|all six .*together|same message", low)
    add("Fans out in a single message rather than serially",
        bool(parallel) and not serial,
        f"parallel marker={bool(parallel)}, serial marker={serial.group(0) if serial else 'none'}")

    # 3. mode correctness
    n_dry = len(re.findall(r"--dry-run", both))
    if live:
        add("Recognizes explicit live authorization (no --dry-run on dispatches)",
            n_dry == 0,
            f"{n_dry} occurrences of --dry-run (expected 0 for an authorized live run)")
    else:
        add("Defaults to --dry-run on every dispatch",
            n_dry >= 6,
            f"{n_dry} occurrences of --dry-run (need >=6)")
        n_tmp = len(re.findall(r"mktemp\s+-d", both))
        add("Uses a throwaway SAKTHAI_HOME on every dispatch",
            n_tmp >= 6,
            f"{n_tmp} occurrences of `mktemp -d` (need >=6)")

    # 4. persona identity
    add("Passes --persona for each of the six personas",
        count_dispatch_blocks(both) == 6,
        f"distinct --persona values found: {count_dispatch_blocks(both)}/6")

    # 5. does not flatten persona config
    bad_provider = re.findall(r"--provider\s+\S+", both)
    bad_model = re.findall(r"--model\s+\S+", both)
    add("Leaves --provider/--model unset so each persona's own config applies",
        not bad_provider and not bad_model,
        f"--provider: {bad_provider or 'none'}; --model: {bad_model or 'none'}")

    # 6. skill injection
    n_skill = len(re.findall(r"--with-skills\s+Sak-auto-cycle-loop", both))
    add("Injects Sak-auto-cycle-loop on every dispatch",
        n_skill >= 6,
        f"{n_skill} occurrences (need >=6)")

    # 7. memory path correctness
    opt = re.findall(r"/opt/data\S*", both)
    add("Targets no /opt/data memory home",
        not opt,
        f"/opt/data references: {sorted(set(opt))[:4] or 'none'}")

    doubled = re.findall(r"SAKTHAI_HOME=\S*\.sakthai/(?:" + "|".join(PERSONAS) + r")\b", both)
    add("Avoids the SAKTHAI_HOME + --persona double-append trap",
        not doubled,
        f"persona-home SAKTHAI_HOME assignments alongside --persona: {doubled or 'none'}")

    if live:
        ok_path = re.search(r"~?/?\.sakthai/(" + "|".join(PERSONAS) + r")/memory\.db", both)
        add("States the correct production memory path per persona",
            bool(ok_path) and not doubled,
            f"matched: {ok_path.group(0) if ok_path else 'no ~/.sakthai/<persona>/memory.db path stated'}")

    # 8. no permission stall on the safe default
    if not live:
        stall = re.search(r"(should i|shall i|do you want|confirm|let me know).{0,80}(test|live|dry)", low)
        add("Dispatches the safe default without stalling to ask test-or-live",
            not stall,
            f"stall phrase: {stall.group(0)[:70] if stall else 'none'}")

    # 9. consolidated report
    rl = report.lower()
    rows = sum(1 for p in PERSONAS if p in rl)
    add("Final report carries a row per persona with status",
        rows == 6 and bool(re.search(r"success|failed|partial|validated", rl)),
        f"{rows}/6 personas named in report.md; status vocabulary present={bool(re.search(r'success|failed|partial|validated', rl))}")

    passed = sum(1 for e in exp if e["passed"])
    return {"expectations": exp, "passed": passed, "total": len(exp),
            "pass_rate": round(passed / len(exp), 3) if exp else 0.0}


def main() -> int:
    it = Path(sys.argv[1])
    print(f"{'run':<34} {'pass':>7}  failures")
    for ed in sorted(it.glob("eval-*")):
        live = "live" in json.loads((ed / "eval_metadata.json").read_text()).get("eval_name", "")
        for arm in ("with_skill", "old_skill", "without_skill"):
            run = ed / arm
            if not run.is_dir():
                continue
            g = grade(run, live)
            (run / "grading.json").write_text(json.dumps(g, indent=2))
            fails = [e["text"] for e in g["expectations"] if not e["passed"]]
            print(f"{ed.name + '/' + arm:<34} {g['passed']:>2}/{g['total']:<4} " + ("; ".join(fails) or "-"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
