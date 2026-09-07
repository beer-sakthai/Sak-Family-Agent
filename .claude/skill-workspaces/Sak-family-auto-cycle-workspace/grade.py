#!/usr/bin/env python3
"""Grade Sak-family-auto-cycle eval runs.

Every assertion is decided by inspecting what the run actually produced, so
grading is reproducible across iterations instead of re-judged by eye.

The important subtlety: these runs *narrate* the flags they deliberately did
not use ("no --model, no --provider", "not one at a time"). Grading flag
assertions over the whole document therefore scores a correct run as a
violation. So flag checks run only over extracted `sakthai run` invocations,
and the prose checks are negation-aware.

Usage: python3 grade.py <iteration-dir>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PERSONAS = ["sakking", "sakthai", "saksee", "saksit", "sakjules", "saktan"]
NEGATORS = r"(?:not|never|no|n't|rather than|instead of|without|avoid\w*|didn't|did not)"


def load(run: Path) -> tuple[str, str]:
    out = run / "outputs"

    def read(name: str) -> str:
        f = out / name
        return f.read_text(errors="replace") if f.is_file() else ""

    dispatch = read("dispatch.md")
    if not dispatch:
        for f in sorted(out.glob("*.md")):
            if f.name != "report.md":
                dispatch = f.read_text(errors="replace")
                break
    return dispatch, read("report.md")


def commands(text: str) -> list[str]:
    """Extract full `sakthai run` invocations, joining backslash continuations."""
    joined = re.sub(r"\\\s*\n\s*", " ", text)
    return [ln.strip() for ln in joined.splitlines() if re.search(r"sakthai\s+run\b", ln)]


def negated(text: str, match: re.Match) -> bool:
    """True if a negator appears shortly before the match (same sentence-ish)."""
    window = text[max(0, match.start() - 60):match.start()]
    return bool(re.search(NEGATORS + r"[^.!?]{0,40}$", window, re.I))


def unnegated(text: str, pattern: str) -> re.Match | None:
    for m in re.finditer(pattern, text, re.I):
        if not negated(text, m):
            return m
    return None


def grade(run: Path, live: bool) -> dict:
    dispatch, report = load(run)
    both = dispatch + "\n" + report
    cmds = commands(both)
    cmd_text = "\n".join(cmds)
    exp: list[dict] = []

    def add(text, passed, evidence):
        exp.append({"text": text, "passed": bool(passed), "evidence": evidence})

    # --- command-level assertions (graded only over real invocations) ---
    persona_vals = {m.group(1).lower() for m in re.finditer(r"--persona\s+([a-z]+)", cmd_text, re.I)}
    persona_vals &= set(PERSONAS)

    # Coverage is graded over the whole document, not the command text: the old
    # skill's commands never name the persona (identity came from the
    # SAKTHAI_HOME path), and that gap is already scored by the --persona
    # assertion below. Grading it here too would double-count the same defect.
    covered = sum(p in both.lower() for p in PERSONAS)
    add("Dispatches all six personas",
        len(cmds) >= 6 and covered == 6,
        f"{len(cmds)} `sakthai run` invocations; {covered}/6 personas addressed")

    add("Passes --persona for each of the six personas",
        len(persona_vals) == 6,
        f"distinct --persona values in commands: {len(persona_vals)}/6 "
        f"({', '.join(sorted(persona_vals)) or 'none'})")

    prov = re.findall(r"--provider\s+\S+", cmd_text)
    mod = re.findall(r"--model\s+\S+", cmd_text)
    add("Leaves --provider/--model unset so each persona's own config applies",
        not prov and not mod,
        f"in commands — --provider: {sorted(set(prov)) or 'none'}; --model: {sorted(set(mod)) or 'none'}")

    n_skill = len(re.findall(r"--with-skills\s+Sak-auto-cycle-loop", cmd_text))
    add("Injects Sak-auto-cycle-loop on every dispatch",
        n_skill >= 6, f"{n_skill}/6 commands carry the flag")

    n_dry = len(re.findall(r"--dry-run", cmd_text))
    if live:
        add("Recognizes explicit live authorization (no --dry-run on dispatches)",
            n_dry == 0, f"{n_dry} commands carry --dry-run (expected 0)")
    else:
        add("Defaults to --dry-run on every dispatch",
            n_dry >= 6, f"{n_dry}/6 commands carry --dry-run")
        n_tmp = len(re.findall(r"mktemp\s+-d", cmd_text))
        add("Uses a throwaway SAKTHAI_HOME on every dispatch",
            n_tmp >= 6, f"{n_tmp}/6 commands set SAKTHAI_HOME=$(mktemp -d)")

    opt = re.findall(r"/opt/data\S*", cmd_text)
    add("Targets no /opt/data memory home",
        not opt, f"/opt/data in commands: {sorted(set(opt))[:4] or 'none'}")

    doubled = re.findall(
        r"SAKTHAI_HOME=\S*\.sakthai/(?:" + "|".join(PERSONAS) + r")\b", cmd_text)
    add("Avoids the SAKTHAI_HOME + --persona double-append trap",
        not doubled, f"persona-home SAKTHAI_HOME in commands: {sorted(set(doubled)) or 'none'}")

    if live:
        # accept both the enumerated and brace-expanded forms
        path_re = (r"\.sakthai/(?:\{[^}]*\}|" + "|".join(PERSONAS) + r")/memory\.db")
        hit = re.search(path_re, both)
        add("States the correct production memory path per persona",
            bool(hit) and not doubled,
            f"matched: {hit.group(0) if hit else 'no ~/.sakthai/<persona>/memory.db path stated'}")

    # --- prose assertions (negation-aware) ---
    parallel = re.search(
        r"single message|one message|in parallel|concurrent|all six[^.]{0,40}together|same message",
        both, re.I)
    serial = unnegated(both, r"one at a time|sequential(?:ly)?|serially|dispatched .{0,20}then")
    add("Fans out in a single message rather than serially",
        bool(parallel) and not serial,
        f"parallel marker: {parallel.group(0) if parallel else 'none'}; "
        f"unnegated serial claim: {serial.group(0) if serial else 'none'}")

    if not live:
        stall = unnegated(both, r"(?:should i|shall i|do you want me to|please confirm)[^.?]{0,60}(?:test|live|dry)")
        add("Dispatches the safe default without stalling to ask test-or-live",
            not stall, f"stall phrase: {stall.group(0)[:70] if stall else 'none'}")

    rl = report.lower()
    rows = sum(1 for p in PERSONAS if p in rl)
    has_status = bool(re.search(r"success|failed|partial|validated", rl))
    add("Final report carries a row per persona with status",
        rows == 6 and has_status,
        f"{rows}/6 personas named in report.md; status vocabulary present={has_status}")

    passed = sum(1 for e in exp if e["passed"])
    total = len(exp)
    rate = round(passed / total, 3) if total else 0.0
    # `expectations` is what the viewer renders; `summary` is what
    # scripts.aggregate_benchmark reads. Emit both so one grading pass feeds
    # the qualitative and quantitative views alike.
    return {"expectations": exp, "passed": passed, "total": total, "pass_rate": rate,
            "summary": {"pass_rate": rate, "passed": passed,
                        "failed": total - passed, "total": total}}


def main() -> int:
    it = Path(sys.argv[1])
    print(f"{'run':<30} {'pass':>8}  failures")
    for ed in sorted(it.glob("eval-*")):
        live = "live" in json.loads((ed / "eval_metadata.json").read_text()).get("eval_name", "")
        for arm in ("with_skill", "old_skill", "without_skill"):
            run = ed / arm
            if not run.is_dir():
                continue
            g = grade(run, live)
            (run / "grading.json").write_text(json.dumps(g, indent=2))
            # aggregate_benchmark expects <config>/run-*/grading.json; the
            # viewer reads <config>/grading.json. Write both from one pass.
            sub = run / "run-1"
            sub.mkdir(exist_ok=True)
            (sub / "grading.json").write_text(json.dumps(g, indent=2))
            timing = run / "timing.json"
            if timing.is_file():
                (sub / "timing.json").write_text(timing.read_text())
            fails = [e["text"] for e in g["expectations"] if not e["passed"]]
            pct = f"{g['passed']}/{g['total']}"
            print(f"{ed.name + '/' + arm:<30} {pct:>8}  " + ("; ".join(fails) or "-"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
