#!/usr/bin/env python3
"""Ad-hoc verification for hf-eval-updater cron outputs (llm_cron_v1).

Verifies, after an eval snapshot upload:
  1. Local YAML parses and carries all required llm_cron_v1 top-level keys,
     correct target_model.id, has_weights true, consistent weighted health
     score, correct schema + cron_run.
  2. Tracker JSON is consistent (total_runs matches history length, last
     entry matches the upload, commit hash is 40 chars, filenames unique).
  3. Live raw file on HF Hub byte-matches the local YAML.

Usage:
  uv run python3 scripts/verify-eval-cron.py \
      --repo Nanthasit/sakthai-context-1.5b-merged \
      --yaml /opt/data/profiles/sakthai/cron/eval-results-<...>.yaml \
      --tracker /opt/data/profiles/sakthai/cron/hf-eval-updated.json \
      --run 3

Exit code 0 = PASS; nonzero = FAIL with reasons printed.
Run from a tempfile dir in cron mode (mkdir with hermes-verify- prefix),
clean up afterward. Ad-hoc verification, not a suite.
"""
import argparse, json, sys, urllib.request

try:
    import yaml
except ImportError:
    print("FAIL: pyyaml not importable")
    sys.exit(2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="Nanthasit/{repo}")
    ap.add_argument("--yaml", required=True, help="local eval YAML path")
    ap.add_argument("--tracker", required=True, help="hf-eval-updated.json path")
    ap.add_argument("--run", required=True, type=int, help="expected cron_run")
    args = ap.parse_args()

    errors = []
    repo = args.repo
    slug = repo.split("/")[-1]
    expected_file = f".eval_results/cron-eval-{slug}-2026-*-{args.run}.yaml"

    # 1) YAML schema
    with open(args.yaml) as f:
        doc = yaml.safe_load(f)
    required_top = [
        "target_model", "architecture", "repo_summary", "benchmarks",
        "training", "card_quality", "health_score", "sibling_comparison",
        "eval_type", "eval_note", "eval_metadata",
    ]
    missing = [k for k in required_top if k not in doc]
    if missing:
        errors.append(f"missing top-level keys: {missing}")

    tm = doc.get("target_model", {})
    if tm.get("id") != repo:
        errors.append(f"target_model.id {tm.get('id')!r} != {repo!r}")
    if tm.get("has_weights") is not True:
        errors.append("has_weights != true")

    hs = doc.get("health_score", {})
    comps, weights = hs.get("components", {}), hs.get("weights", {})
    if comps and weights:
        calc = sum(comps[k] * weights[k] for k in comps)
        if abs(calc - hs.get("overall", -1)) > 1.5:
            errors.append(f"overall {hs.get('overall')} != weighted sum {calc:.1f}")

    em = doc.get("eval_metadata", {})
    if em.get("schema") != "llm_cron_v1":
        errors.append(f"schema {em.get('schema')!r} != llm_cron_v1")
    if em.get("cron_run") != args.run:
        errors.append(f"cron_run {em.get('cron_run')} != {args.run}")

    # 2) Tracker JSON
    with open(args.tracker) as f:
        tr = json.load(f)
    if tr.get("total_runs") != len(tr.get("history", [])):
        errors.append("total_runs != len(history)")
    last = tr["history"][-1]
    if last["model"] != repo:
        errors.append(f"tracker last model {last['model']!r} != {repo!r}")
    if len(last.get("commit", "")) != 40:
        errors.append(f"commit hash len {len(last.get('commit',''))} != 40")
    files = [h["file"] for h in tr["history"]]
    if len(files) != len(set(files)):
        errors.append("duplicate eval filenames across runs")
    if args.run > 1:
        prev = tr["history"][-2]
        if prev["run"] != args.run - 1:
            errors.append(f"history out of order: run {prev['run']} before {args.run}")

    # 3) Live byte-match
    actual_file = last["file"]
    url = f"https://huggingface.co/{repo}/raw/main/{actual_file}"
    with urllib.request.urlopen(url, timeout=30) as r:
        live = r.read().decode()
    with open(args.yaml) as f:
        local = f.read()
    if live.strip() != local.strip():
        errors.append(f"live HF file != local YAML ({len(local)} vs {len(live)} chars)")

    if errors:
        print("VERIFY FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print(f"VERIFY PASS: {repo} run={args.run} yaml_keys={len(required_top)}"
          f"/{len(required_top)} health={hs.get('overall')} live_match=ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
