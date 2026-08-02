#!/usr/bin/env python3
"""
Cross-Link Audit Script — systematic gap detection across all model cards.

Fetches every model README from HF Hub and checks for:
  - Dynamic download badge
  - Collection badge
  - Pipeline Integration section
  - Family Links section
  - All sibling models referenced
  - Narrative markers (Cork shelter, House of Sak, Beer)
  - Stale model counts

Usage:
  python3 cross-link-audit.py              # audit all models
  python3 cross-link-audit.py --json       # JSON output for programmatic use

Requires: huggingface_hub or HF token at ~/.cache/huggingface/token
"""
import json
import os
import re
import sys
import urllib.request

# ── CONFIG ──────────────────────────────────────────────────────────────
AUTHOR = "Nanthasit"
# Full model roster (12 meaningful models to audit)
MODELS = [
    "Nanthasit/sakthai-context-1.5b-merged",
    "Nanthasit/sakthai-context-0.5b-merged",
    "Nanthasit/sakthai-context-7b-merged",
    "Nanthasit/sakthai-context-7b-128k",
    "Nanthasit/sakthai-context-7b-tools",
    "Nanthasit/sakthai-context-1.5b-tools",
    "Nanthasit/sakthai-context-0.5b-tools",
    "Nanthasit/sakthai-embedding",
    "Nanthasit/sakthai-embedding-multilingual",
    "Nanthasit/sakthai-vision-7b",
    "Nanthasit/sakthai-tts-model",
    "Nanthasit/sakthai-coder-1.5b",
]

MARKER_SPECS = {
    "download_badge":       ("Download badge",       lambda c: "img.shields.io/endpoint" in c and "sakthai-" in c),
    "collection_badge":     ("Collection badge",     lambda c: "model-family" in c.lower() and "collection" in c.lower()),
    "pipeline_integration": ("Pipeline Integration", lambda c: "## Pipeline Integration" in c),
    "family_links":         ("Family Links",         lambda c: "### LLM / Reasoning" in c or "## Family Links" in c),
    "origin_story":         ("Cork shelter story",   lambda c: "shelter in Cork" in c),
    "house_of_sak":         ("House of Sak",         lambda c: "house-of-sak" in c.lower() or "house of sak" in c.lower()),
    "beer_mention":         ("Beer reference",       lambda c: bool(re.search(r'\bBeer\b', c))),
}


def get_token():
    for p in [os.path.expanduser("~/.cache/huggingface/token"),
              "/opt/data/.cache/huggingface/token"]:
        if os.path.exists(p):
            with open(p) as f:
                return f.read().strip()
    gc = "/opt/data/.git-credentials"
    if os.path.exists(gc):
        with open(gc) as f:
            for line in f:
                if "huggingface" in line:
                    return line.split("://")[1].split("@")[0].split(":")[1].strip()
    return None


def fetch_readme(repo_id, token):
    url = f"https://huggingface.co/{repo_id}/raw/main/README.md"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read().decode()
    except Exception as e:
        return None


def count_siblings(content):
    count = 0
    found = []
    for m in MODELS:
        short = m.split("/")[-1]
        if short in content:
            count += 1
            found.append(short)
    return count, found


def check_stale_counts(content):
    matches = []
    for m in re.finditer(r"(\d+)\s*models?", content, re.IGNORECASE):
        n = int(m.group(1))
        if 10 <= n <= 20:
            start = max(0, m.start() - 40)
            end = min(len(content), m.end() + 40)
            matches.append((n, content[start:end].strip()))
    return matches


def audit(token):
    results = {}
    overall_issues = {"badge_missing": 0, "sibling_missing": 0,
                      "section_missing": 0, "narrative_missing": 0}

    for repo in MODELS:
        short = repo.split("/")[-1]
        content = fetch_readme(repo, token)
        if content is None:
            results[short] = {"error": "README unreachable"}
            continue

        markers = {}
        for key, (label, fn) in MARKER_SPECS.items():
            markers[key] = fn(content)

        sibling_count, sibling_found = count_siblings(content)
        expected = len(MODELS) - 1
        stale = check_stale_counts(content)

        issues = []
        if not markers["download_badge"]:
            issues.append("badge:download"); overall_issues["badge_missing"] += 1
        if not markers["pipeline_integration"]:
            issues.append("section:pipeline"); overall_issues["section_missing"] += 1
        if not markers["family_links"]:
            issues.append("section:family_links"); overall_issues["section_missing"] += 1
        if not markers["origin_story"]:
            issues.append("narrative:origin_story"); overall_issues["narrative_missing"] += 1
        if not markers["beer_mention"]:
            issues.append("narrative:beer"); overall_issues["narrative_missing"] += 1

        missing_siblings = []
        if sibling_count < expected:
            sibling_ids = {s.split("/")[-1] for s in sibling_found}
            all_ids = {s.split("/")[-1] for s in MODELS if s != repo}
            missing_siblings = sorted(all_ids - sibling_ids)
            overall_issues["sibling_missing"] += len(missing_siblings)
            issues.append(f"sibling:missing_{len(missing_siblings)}")

        results[short] = {
            "markers": markers,
            "sibling_count": sibling_count,
            "expected_siblings": expected,
            "missing_siblings": missing_siblings,
            "stale_counts": stale,
            "issues": issues,
            "healthy": len(issues) == 0,
        }

    return results, overall_issues


def print_report(results, issues):
    print("=" * 70)
    print("  HF ECOSYSTEM CROSS-LINK AUDIT")
    print("=" * 70)
    print(f"\nModels audited: {len(results)}")
    healthy = sum(1 for r in results.values() if r.get("healthy"))
    print(f"Healthy: {healthy} | With issues: {len(results) - healthy}")
    print(f"\nIssue Summary:")
    print(f"  Badge missing:        {issues['badge_missing']}")
    print(f"  Sibling links missing: {issues['sibling_missing']}")
    print(f"  Sections missing:     {issues['section_missing']}")
    print(f"  Narrative missing:    {issues['narrative_missing']}")

    sorted_repos = sorted(results.items(),
                          key=lambda x: (len(x[1].get("issues", [])), x[0]))
    for short, r in sorted_repos:
        if r.get("error"):
            print(f"\n  !!  {short}  ERROR: {r['error']}")
            continue
        status = "OK" if r["healthy"] else "!!"
        print(f"\n  {status} {short}")
        for key, (label, _) in MARKER_SPECS.items():
            val = r["markers"].get(key, False)
            print(f"      {label:25s} {'OK' if val else '--'}")
        print(f"      Siblings: {r['sibling_count']}/{r['expected_siblings']}", end="")
        if r["missing_siblings"]:
            print(f"  MISSING: {', '.join(r['missing_siblings'])}")
        else:
            print()
        if r["stale_counts"]:
            print(f"      Stale count claims: {r['stale_counts']}")

    print("\n" + "=" * 70)
    print("  PRIORITY QUEUE")
    print("=" * 70)
    candidates = [(s, r) for s, r in sorted_repos if not r.get("healthy")]
    for rank, (short, r) in enumerate(candidates[:3], 1):
        badge = "--" if not r["markers"].get("download_badge") else "OK"
        sib = f"({r['sibling_count']}/{r['expected_siblings']})"
        print(f"  {rank}. {short}  badge={badge}  siblings={sib}")
        if r["missing_siblings"][:3]:
            print(f"     Missing: {', '.join(r['missing_siblings'][:3])}")
    print()


def main():
    token = get_token()
    if not token:
        print("FAIL: No HF token found")
        sys.exit(1)

    results, issues = audit(token)
    if "--json" in sys.argv:
        print(json.dumps({"results": {k: v for k, v in results.items()
                                       if not v.get("error")},
                          "issues_summary": issues}, indent=2))
    else:
        print_report(results, issues)


if __name__ == "__main__":
    main()
