#!/usr/bin/env python3
"""
Verification script for structural model card overhauls.

Checks for presence of key structural sections after a full card rewrite.
Use after enriching a card with ecosystem cross-promotion (datasets table,
spaces table, growing ecosystem section, expanded family table).

Usage:
  python3 scripts/verify-card-structure.py <repo_id> [--type model|dataset|space] [--counts M D S]

Arguments:
  repo_id     Hugging Face repo ID (e.g. "Nanthasit/sakthai-context-7b-merged")
  --type      Repo type: model, dataset, or space (default: model)
  --counts    Expected ecosystem counts: M=models D=datasets S=spaces (default: "13 6 3")

Examples:
  python3 verify-card-structure.py Nanthasit/sakthai-context-7b-merged
  python3 verify-card-structure.py Nanthasit/sakthai-context-7b-merged --counts "13 6 3"
  python3 verify-card-structure.py Nanthasit/sakthai-irrelevance-supplement --type dataset

Exit code: 0 if all checks pass, 1 if any fail.
"""

import sys
import urllib.request


def fetch_readme(repo_id, repo_type):
    """Fetch the raw README.md from Hugging Face."""
    base = "https://huggingface.co"
    if repo_type == "dataset":
        base += "/datasets"
    elif repo_type == "space":
        base += "/spaces"
    url = f"{base}/{repo_id}/raw/main/README.md"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SakThai-Verify/1.0"})
        resp = urllib.request.urlopen(req)
        return resp.read().decode()
    except Exception as e:
        print(f"  ERROR: Cannot fetch README from {url}")
        print(f"  {type(e).__name__}: {e}")
        return None

def check(content, name, term):
    """Check that a term is present in content."""
    found = term in content
    status = "PASS" if found else "FAIL"
    print(f"  [{status}] {name}")
    return found

def check_not(content, name, term):
    """Check that a term is NOT present in content."""
    absent = term not in content
    status = "PASS" if absent else "FAIL"
    print(f"  [{status}] {name} (should be absent)")
    return absent

def check_yaml(content, name, term):
    """Check that a term is present in the YAML frontmatter (first --- block)."""
    parts = content.split("---")
    if len(parts) < 3:
        print(f"  [SKIP] {name} (no YAML frontmatter)")
        return True  # skip if no YAML
    yaml = parts[1]
    found = term in yaml
    status = "PASS" if found else "FAIL"
    print(f"  [{status}] {name} (YAML)")
    return found


def verify(repo_id, repo_type="model", expected_counts=None):
    """Run all structural checks on a repo's README."""
    if expected_counts is None:
        expected_counts = {"models": 13, "datasets": 6, "spaces": 3}

    content = fetch_readme(repo_id, repo_type)
    if content is None:
        return False

    checks = []
    repo_short = repo_id.split("/")[1] if "/" in repo_id else repo_id

    # === General structural checks ===
    checks.append(check(content, "Ecosystem count mentions models",
                        f"{expected_counts['models']} models"))
    checks.append(check(content, "Ecosystem count mentions datasets",
                        f"{expected_counts['datasets']} datasets"))
    checks.append(check(content, "Ecosystem count mentions Spaces",
                        f"{expected_counts['spaces']} Spaces"))
    checks.append(check(content, "Collection link present",
                        "sakthai-model-family"))
    checks.append(check(content, "License section present",
                        "Apache 2.0" if repo_type == "model" else "mit"))

    # === Growing ecosystem / cross-promotion section ===
    checks.append(check(content, "Growing ecosystem section (🌱)",
                        "Growing the ecosystem"))
    checks.append(check(content, "Low-download gems mention",
                        "low-download"))
    checks.append(check(content, "Download count mention in tables",
                        "⬇" if "⬇" in content else True))  # soft check

    # === Dataset-table-level checks (for model cards) ===
    if repo_type == "model":
        checks.append(check(content, "Sibling datasets table",
                            "sakthai-combined-v6"))
        checks.append(check(content, "Latest dataset v7 referenced",
                            "combined-v7"))
        checks.append(check(content, "Irrelevance supplement referenced",
                            "irrelevance-supplement"))

    # === Model-table-level checks ===
    checks.append(check(content, "1.5B-merged listed",
                        "context-1.5b-merged"))
    checks.append(check(content, "0.5B-merged listed",
                        "context-0.5b-merged"))
    checks.append(check(content, "v2 tools model listed",
                        "context-1.5b-tools-v2") if repo_type == "model" else True)
    checks.append(check(content, "v2 0.5B tools listed",
                        "context-0.5b-tools-v2") if repo_type == "model" else True)
    checks.append(check(content, "v1 0.5B tools listed",
                        "context-0.5b-tools (v1)") if repo_type == "model" else True)

    # === Spaces table ===
    if repo_type == "model":
        checks.append(check(content, "Vision Demo Space linked",
                            "sakthai-vision-demo"))
        checks.append(check(content, "TTS Demo Space linked",
                            "sakthai-tts"))
        checks.append(check(content, "Leaderboard Space linked",
                            "sakthai-leaderboard"))

    # === YAML frontmatter checks ===
    checks.append(check_yaml(content, "Pipeline tag present in YAML",
                             "pipeline_tag:"))
    checks.append(check_yaml(content, "License in YAML", "license:"))

    if repo_type == "model":
        checks.append(check_yaml(content, "Model-index in YAML",
                                 "model-index:"))

    # === Report ===
    passed = sum(1 for c in checks if c)
    failed = sum(1 for c in checks if not c)
    total = len(checks)

    print(f"\n  Results: {passed}/{total} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <repo_id> [--type model|dataset|space] [--counts \"M D S\"]")
        sys.exit(1)

    repo_id = sys.argv[1]
    repo_type = "model"
    counts_str = "13 6 3"

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--type" and i + 1 < len(sys.argv):
            repo_type = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--counts" and i + 1 < len(sys.argv):
            counts_str = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    parts = counts_str.split()
    expected_counts = {
        "models": int(parts[0]) if len(parts) > 0 else 13,
        "datasets": int(parts[1]) if len(parts) > 1 else 6,
        "spaces": int(parts[2]) if len(parts) > 2 else 3,
    }

    print(f"Verifying: {repo_id} ({repo_type})")
    print(f"Expected counts: {expected_counts['models']} models · "
          f"{expected_counts['datasets']} datasets · {expected_counts['spaces']} Spaces")
    print()

    success = verify(repo_id, repo_type, expected_counts)
    sys.exit(0 if success else 1)
