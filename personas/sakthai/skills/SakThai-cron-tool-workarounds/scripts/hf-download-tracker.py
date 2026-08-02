#!/usr/bin/env python3
"""HF Download Tracker — self-contained cron script (verified 2026-07-31).

Fetches download stats for ALL of a user's models + datasets from the HF Hub
API, compares against the previous snapshot, reports gains/losses/new/removed
repos, and saves the new snapshot. Prints SILENT when nothing changed so the
cron wrapper suppresses delivery.

Why self-fetching urllib instead of curl:
  - No pipe-to-interpreter security block (no `curl | python3`).
  - No /tmp files to clean up (write_file to /tmp is blocked in cron mode).
  - Standalone: no dependency on pre-fetched scratch files.

Key pitfall handled: a repo can appear in BOTH the models and datasets API
responses (e.g. Nanthasit/sakthai-coder-browser). Build the union as a dict
keyed by repo ID so the dedupe is automatic — never sum len(models)+len(datasets).

Change the AUTHOR constant per user. Snapshot path is per profile.
"""
import json
import os
import urllib.request

AUTHOR = "Nanthasit"
SNAPSHOT_PATH = os.path.expanduser("~/profiles/sakthai/cron/hf-download-snapshot.json")
API = "https://huggingface.co/api"


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "sakthai-hf-download-tracker"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def build_current():
    """Union of model + dataset repos, deduped by ID (some repos appear in both lists)."""
    current = {}
    for m in fetch_json(f"{API}/models?author={AUTHOR}&limit=100"):
        current[m["id"]] = {"downloads": m.get("downloads", 0), "likes": m.get("likes", 0), "type": "model"}
    for d in fetch_json(f"{API}/datasets?author={AUTHOR}&limit=100"):
        current[d["id"]] = {"downloads": d.get("downloads", 0), "likes": d.get("likes", 0), "type": "dataset"}
    return current


def main():
    current = build_current()

    try:
        with open(SNAPSHOT_PATH) as f:
            previous = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        previous = {}

    diff = {"gained": {}, "lost": {}, "new": {}, "removed": {}}
    for repo in set(list(previous.keys()) + list(current.keys())):
        prev = previous.get(repo, {})
        cur = current.get(repo, {})
        prev_dl = prev.get("downloads", 0) if isinstance(prev, dict) else 0
        cur_dl = cur.get("downloads", 0) if isinstance(cur, dict) else 0

        if repo not in previous:
            diff["new"][repo] = {"downloads": cur_dl, "type": cur.get("type", "?")}
        elif repo not in current:
            diff["removed"][repo] = {"downloads": prev_dl, "type": prev.get("type", "?")}
        elif cur_dl > prev_dl:
            diff["gained"][repo] = {"prev": prev_dl, "cur": cur_dl, "diff": cur_dl - prev_dl, "type": cur.get("type", "?")}
        elif cur_dl < prev_dl:
            diff["lost"][repo] = {"prev": prev_dl, "cur": cur_dl, "diff": prev_dl - cur_dl, "type": cur.get("type", "?")}

    likes_diff = []
    for repo in current:
        if repo in previous:
            prev_likes = previous[repo].get("likes", 0) if isinstance(previous[repo], dict) else 0
            cur_likes = current[repo].get("likes", 0)
            if cur_likes > prev_likes:
                likes_diff.append(f"{repo}: {prev_likes} → {cur_likes} likes")

    any_change = any([diff["gained"], diff["lost"], diff["new"], diff["removed"], likes_diff])

    if not any_change:
        # Still save the snapshot (fresh baseline) but stay silent.
        with open(SNAPSHOT_PATH, "w") as f:
            json.dump(current, f, indent=2)
        print("SILENT")
        return

    lines = ["=== HF DOWNLOAD TRACKER ===",
             f"Previous: {len(previous)} repos | Current: {len(current)} repos", ""]
    if diff["gained"]:
        lines.append("📈 DOWNLOAD GAINS:")
        for r, d in sorted(diff["gained"].items(), key=lambda x: -x[1]["diff"]):
            lines.append(f"  +{d['diff']}  {r}  ({d['prev']}→{d['cur']}) [{d['type']}]")
    if diff["lost"]:
        lines.append("\n📉 DOWNLOAD LOSSES:")
        for r, d in sorted(diff["lost"].items(), key=lambda x: -x[1]["diff"]):
            lines.append(f"  -{d['diff']}  {r}  ({d['prev']}→{d['cur']}) [{d['type']}]")
    if diff["new"]:
        lines.append("\n🆕 NEW REPOS:")
        for r, d in sorted(diff["new"].items()):
            lines.append(f"  {r}  ({d['downloads']} downloads) [{d['type']}]")
    if diff["removed"]:
        lines.append("\n🗑️ REMOVED REPOS:")
        for r, d in sorted(diff["removed"].items()):
            lines.append(f"  {r} (had {d['downloads']}) [{d['type']}]")
    if likes_diff:
        lines.append("\n❤️ LIKE CHANGES:")
        lines.extend(f"  {l}" for l in likes_diff)

    total_dl = sum(r["downloads"] for r in current.values())
    total_likes = sum(r["likes"] for r in current.values() if r["type"] == "model")
    models_n = sum(1 for r in current.values() if r["type"] == "model")
    datasets_n = sum(1 for r in current.values() if r["type"] == "dataset")
    lines.append(f"\n📊 TOTALS: {models_n} models + {datasets_n} datasets = {total_dl} downloads, {total_likes} model likes")

    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(current, f, indent=2)
    lines.append("✅ Snapshot saved.")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
