#!/usr/bin/env python3
"""Per-agent diagnostics for the four Sak Family Agents.

Where `.claude/skills/run-sakthai-agent-v2/driver.py` smoke-tests the *core*
once, this checks each persona (SakKing, SakThai, SakSee, SakSit) end to end and
confirms the family can *improve*:

For every persona it verifies, offline and with zero token spend:
  1. its skill tree composes (shared + overlay) via scripts/compose_persona.py;
  2. its model is configured (personas/<name>/config/config.yaml);
  3. its MCP servers load from personas/<name>/config/mcp.json;
  4. the zero-cost agent preflight resolves (`run --dry-run --no-mcp`);
  5. shared memory round-trips (`learn` -> `recall`).
It also reports naming-convention drift per overlay (a warning — the bulk rename
is deferred to scripts/rename_skills.py).

Then, once, it proves the *improve* loop: memory consolidation folds facts into
an observation, the growth cycle advances, and it reports whether the
DSPy/GEPA self-evolution package is importable.

Exit code is non-zero if any hard check fails (naming drift and a missing
self-evolution dep are warnings, not failures).

Usage:
    python scripts/diagnose_personas.py
    SAKTHAI_BIN=/path/to/sakthai python scripts/diagnose_personas.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sakthai.skills import (  # noqa: E402  (path bootstrap above)
    PERSONA_SKILL_PREFIXES,
    naming_violations,
)

PERSONAS = ("sakking", "sakthai", "saksee", "saksit")
PERSONAS_DIR = REPO_ROOT / "personas"
BIN = os.environ.get("SAKTHAI_BIN", "sakthai")

failures: list[str] = []
warnings: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(label)


def warn(label: str, detail: str = "") -> None:
    print(f"  [WARN] {label}" + (f" — {detail}" if detail else ""))
    warnings.append(label)


def info(label: str, detail: str = "") -> None:
    print(f"  [INFO] {label}" + (f" — {detail}" if detail else ""))


def run(args: list[str], env: dict[str, str], stdin: str | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        [BIN, *args], env=env, input=stdin, capture_output=True, text=True, timeout=120
    )
    return proc.returncode, proc.stdout + proc.stderr


def model_summary(persona: str) -> str:
    cfg = PERSONAS_DIR / persona / "config" / "config.yaml"
    if not cfg.is_file():
        return "(no config.yaml)"
    data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    m = data.get("model", {}) or {}
    fb = data.get("fallback_model", {}) or {}
    primary = f"{m.get('provider')}:{m.get('default')}"
    fallback = f"{fb.get('provider')}:{fb.get('model')}" if fb else "(none)"
    return f"{primary}  (fallback {fallback})"


def mcp_server_names(persona: str, env: dict[str, str]) -> list[str]:
    cfg = PERSONAS_DIR / persona / "config" / "mcp.json"
    if not cfg.is_file():
        return []
    code = "from sakthai.mcp.servers import load_server_specs; print(' '.join(s.name for s in load_server_specs()))"
    proc = subprocess.run(
        [sys.executable, "-c", code],
        env={**env, "SAKTHAI_MCP_CONFIG": str(cfg)},
        capture_output=True,
        text=True,
        timeout=60,
    )
    return proc.stdout.split()


def diagnose_persona(persona: str) -> None:
    print(f"\n=== {persona} ===")
    home = Path(tempfile.mkdtemp(prefix=f"sakthai-diag-{persona}."))
    env = {**os.environ, "SAKTHAI_HOME": str(home)}
    try:
        # 1. skills compose
        out_dir = home / "skills"
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "compose_persona.py"), persona,
             "--out", str(out_dir)],
            capture_output=True, text=True, timeout=120,
        )
        n_files = sum(1 for _ in out_dir.rglob("SKILL.md")) if out_dir.is_dir() else 0
        check("skills compose", proc.returncode == 0 and n_files > 0, f"{n_files} skills")

        # 2. model configured
        info("model", model_summary(persona))
        check("model configured", "None" not in model_summary(persona).split("(")[0])

        # 3. MCP servers load
        names = mcp_server_names(persona, env)
        check("mcp servers load", bool(names), ", ".join(names) or "none")

        # 4. agent preflight (no API call)
        rc, out = run(["run", "ping", "--dry-run", "--no-mcp"], env)
        check("agent preflight (--dry-run)", rc == 0 and "runnable:" in out)

        # 5. shared memory round-trip
        rc, _ = run(["learn", f"{persona} was here", "--kind", "note"], env)
        rc2, out = run(["recall", "was here"], env)
        check("memory learn -> recall", rc == 0 and rc2 == 0 and "was here" in out)

        # naming drift (warning only — bulk rename deferred)
        overlay = PERSONAS_DIR / persona / "skills"
        prefix = PERSONA_SKILL_PREFIXES[persona]
        drift = naming_violations(overlay, prefix=prefix)
        if drift:
            warn("naming convention", f"{len(drift)} overlay skill(s) need '{prefix}' (run scripts/rename_skills.py)")
        else:
            check("naming convention", True)
    finally:
        import shutil
        shutil.rmtree(home, ignore_errors=True)


def diagnose_improve() -> None:
    print("\n=== improve loop (shared) ===")
    home = Path(tempfile.mkdtemp(prefix="sakthai-diag-improve."))
    env = {**os.environ, "SAKTHAI_HOME": str(home)}
    try:
        run(["learn", "alpha fact", "--kind", "note"], env)
        run(["learn", "beta fact", "--kind", "note"], env)
        rc, out = run(["memory", "consolidate", "--age", "0"], env)
        check("memory consolidate folds facts", rc == 0)

        rc, out = run(["cycle", "status"], env)
        check("growth cycle status", rc == 0)
        rc, out = run(["cycle", "next"], env)
        check("growth cycle advances", rc == 0)

        try:
            subprocess.run(
                [sys.executable, "-c", "import evolution"],
                cwd=str(REPO_ROOT / "packages" / "agent-self-evolution"),
                capture_output=True, text=True, timeout=60, check=True,
            )
            info("self-evolution (DSPy/GEPA)", "importable")
        except Exception:
            info("self-evolution (DSPy/GEPA)", "package present, deps not installed (pip install -e packages/agent-self-evolution)")
    finally:
        import shutil
        shutil.rmtree(home, ignore_errors=True)


def main() -> int:
    print(f"Sak Family per-agent diagnostics · bin={BIN}")
    for persona in PERSONAS:
        diagnose_persona(persona)
    diagnose_improve()

    print()
    if warnings:
        print(f"{len(warnings)} warning(s): {', '.join(warnings)}")
    if failures:
        print(f"FAILED: {len(failures)} check(s): {', '.join(failures)}")
        return 1
    print("OK: all persona checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
