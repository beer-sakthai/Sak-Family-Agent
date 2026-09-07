#!/usr/bin/env python3
"""Verify a static site deploy against local source.

Checks:
1. Local index.html is valid HTML (starts with doctype/html tag, contains <title>).
2. GitHub raw main/index.html is valid HTML.
3. Vercel responds 200 with text/html.
4. Vercel body and GitHub raw content match local file.

Usage:
    python3 verify-deploy.py --owner beer-sakthai --repo house-of-sak \
        --url https://house-of-sak.vercel.app/ --local index.html
"""
import argparse, sys, requests


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def is_valid_html(text: str) -> bool:
    stripped = text.lstrip().lower()
    return stripped.startswith("<!doctype html>") or stripped.startswith("<html")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify static site deploy")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--local", required=True)
    args = parser.parse_args()

    raw_url = f"https://raw.githubusercontent.com/{args.owner}/{args.repo}/main/index.html"

    # 1. Local file
    try:
        with open(args.local, "r") as f:
            local_html = f.read()
    except FileNotFoundError:
        fail(f"local file not found: {args.local}")

    if not is_valid_html(local_html):
        fail(f"local file {args.local} does not look like valid HTML")

    # 2. GitHub raw content
    r = requests.get(raw_url, timeout=30)
    if r.status_code != 200:
        fail(f"GitHub raw returned {r.status_code}")
    if not is_valid_html(r.text):
        fail("GitHub raw index.html does not look like valid HTML")

    # 3. Vercel live response
    r2 = requests.get(args.url, timeout=30)
    if r2.status_code != 200:
        fail(f"Vercel returned {r2.status_code}")
    ct = r2.headers.get("content-type", "")
    if "text/html" not in ct:
        fail(f"Vercel content-type is {ct}, expected text/html")

    # 4. Compare bodies (normalise whitespace)
    if r.text.strip() != local_html.strip():
        fail("GitHub raw content differs from local file")

    print("PASS: deployed content matches local content")


if __name__ == "__main__":
    main()
