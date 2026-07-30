#!/usr/bin/env python3
"""
verify-dataset-card-counts.py — Cron-mode dataset card verification.

Downloads actual data files for a HF dataset and checks the card's
stated example count. Uses only Python stdlib — no huggingface_hub needed.

Usage:
    python3 verify-dataset-card-counts.py Nanthasit/sakthai-combined-v7

Returns exit code 0 if counts match, 1 if mismatch, 2 on error.
"""

import json, sys, urllib.request, re

USER_AGENT = "sakthai-verify/1.0"

def fetch_text(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT})) as f:
        return f.read().decode("utf-8")

def fetch_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT})) as f:
        return json.loads(f.read().decode("utf-8"))

def count_lines(url):
    text = fetch_text(url).strip()
    return len(text.split("\n")) if text else 0

def extract_card_count(readme_text, split="train"):
    patterns = [
        rf"(\d{{1,3}}(?:,\d{{3}})*)\s+{split}(?:ing)?\s+examples",
        rf"(\d{{1,3}}(?:,\d{{3}})*)\s+examples",
        rf"\|\s*data/{split}\.jsonl\s*\|\s*(\d{{1,3}}(?:,\d{{3}})*)\s*\|",
    ]
    for pat in patterns:
        m = re.search(pat, readme_text, re.IGNORECASE)
        if m:
            return int(m.group(1).replace(",", ""))
    return None

def verify(repo_id, train_path="data/train.jsonl", test_path="data/test.jsonl"):
    base = f"https://huggingface.co/datasets/{repo_id}"
    readme = fetch_text(f"{base}/raw/main/README.md")
    train_stated, test_stated = extract_card_count(readme, "train"), extract_card_count(readme, "test")
    print(f"  Card: train={train_stated}, test={test_stated}")

    ok, code = True, 0
    for name, path, stated in [("train", train_path, train_stated), ("test", test_path, test_stated)]:
        try:
            actual = count_lines(f"{base}/resolve/main/{path}")
        except Exception as e:
            print(f"  {name}: ERROR ({e})")
            if stated is not None: ok = False; code = 1
            continue
        if stated is not None:
            if actual == stated:
                print(f"  MATCH  card={stated}  data={actual}  [{name}]")
            else:
                print(f"  MISMATCH  card={stated}  data={actual}  [{name}]")
                ok = False; code = 1
        else:
            print(f"  DATA-ONLY  card=?  data={actual}  [{name}]")

    api = fetch_json(f"https://huggingface.co/api/datasets/{repo_id}")
    files = [s["rfilename"] for s in api.get("siblings", []) if s.get("rfilename","").startswith("data/")]
    print(f"  Files: {len(files)} ({', '.join(files)})")
    print(f"  => {'ALL VERIFIED' if ok else 'COUNTS NEED UPDATE'}")
    return code

if __name__ == "__main__":
    if len(sys.argv) < 2: print("Usage: python3 verify-dataset-card-counts.py <repo_id>"); sys.exit(2)
    sys.exit(verify(sys.argv[1], *(sys.argv[2:4] or ["data/train.jsonl","data/test.jsonl"])))
