#!/usr/bin/env python3
"""Hugging Face Portfolio Health & Telemetry Audit.

Audits all models, datasets, spaces, and collections under Nanthasit on Hugging Face Hub.
"""

import json
import sys
import urllib.request
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

AUTHOR = "Nanthasit"
COLLECTION_SLUG = f"{AUTHOR}/sakthai-model-family-6a64745450b12d421c1f9f02"
ALLOWED_HOSTS = {"huggingface.co"}


def fetch_json(url: str, timeout: int = 30) -> Any:
    """Fetch and decode JSON from Hugging Face Hub API."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
    if parsed.netloc not in ALLOWED_HOSTS and not parsed.netloc.endswith(".huggingface.co"):
        raise ValueError(f"Untrusted host: {parsed.netloc}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
        return json.loads(resp.read().decode())


def main() -> int:
    print("==================================================")
    print(f"HF Portfolio Health Check — {AUTHOR}")
    print(f"Timestamp: {datetime.now(UTC).isoformat()}")
    print("==================================================\n")

    # 1. Fetch Models
    models = fetch_json(f"https://huggingface.co/api/models?author={AUTHOR}&full=true")
    print(f"📦 Total Models: {len(models)}")

    total_downloads = sum(m.get("downloads", 0) for m in models)
    total_likes = sum(m.get("likes", 0) for m in models)

    healthy = 0
    issues_list = []

    for m in models:
        mid = m["id"]
        tags = m.get("tags", [])
        pipeline = m.get("pipeline_tag")
        dl = m.get("downloads", 0)
        likes = m.get("likes", 0)

        has_license = any(t.startswith("license:") for t in tags)
        has_pipeline = pipeline is not None

        repo_issues = []
        if not has_pipeline:
            repo_issues.append("Missing pipeline_tag")
        if not has_license:
            repo_issues.append("Missing license")

        if not repo_issues:
            healthy += 1
            print(
                f"  ✅ {mid.replace(f'{AUTHOR}/', ''):<35} | {pipeline:<22} | "
                f"DL: {dl:>4} | Likes: {likes}"
            )
        else:
            print(f"  ⚠️ {mid.replace(f'{AUTHOR}/', ''):<35} | Issues: {', '.join(repo_issues)}")
            issues_list.append((mid, repo_issues))

    score_pct = (healthy / len(models) * 100) if models else 0.0
    print(f"\n📊 Health Score: {healthy}/{len(models)} ({score_pct:.1f}%)")
    print(f"📥 Total Downloads: {total_downloads:,}")
    print(f"❤️ Total Likes: {total_likes}\n")

    # 2. Fetch Spaces
    spaces = fetch_json(f"https://huggingface.co/api/spaces?author={AUTHOR}")
    print(f"🚀 Active Spaces ({len(spaces)}):")
    for s in spaces:
        sid = s.get("id", "").replace(f"{AUTHOR}/", "")
        sdk = s.get("sdk", "unknown")
        print(f"  🌐 {sid:<25} | SDK: {sdk:<10} | URL: https://huggingface.co/spaces/{s.get('id')}")

    # 3. Fetch Collection
    try:
        col = fetch_json(f"https://huggingface.co/api/collections/{COLLECTION_SLUG}")
        items_count = len(col.get("items", []))
        print(f"\n🗂️  Collection '{col.get('title')}': {items_count} items")
    except Exception as e:
        print(f"\n⚠️  Could not fetch collection: {e}")

    print("\n==================================================")
    if issues_list:
        print(f"❌ {len(issues_list)} issues require attention.")
        return 1
    else:
        print("🎉 All models are healthy, indexed, and categorized!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
