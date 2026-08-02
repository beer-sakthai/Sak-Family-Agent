#!/usr/bin/env python3
"""Sync SakSit skills + LEARNING_JOURNAL.md + cron-configs.json to beer-sakthai/saksit-skills.

Usage: python3 sync-skills.py

Extracts GitHub PAT from /opt/data/.git-credentials (first line).
Does content comparison via base64 — only pushes changed files.
"""
import json, base64, os, sys, urllib.request, urllib.error

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date
from urllib.parse import urlparse

REPO = "beer-sakthai/saksit-skills"
API_BASE = f"https://api.github.com/repos/{REPO}"
SKILLS_BASE = os.path.expanduser("/opt/data/profiles/saksit/skills")
LJ_PATH = os.path.expanduser("/opt/data/profiles/saksit/LEARNING_JOURNAL.md")


def get_token():
    try:
        with open("/opt/data/.git-credentials") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parsed = urlparse(line)
                if parsed.hostname == "github.com":
                    if "x-access-token:" in line:
                        token = line.split("x-access-token:")[1]
                    elif "@github.com" in line:
                        token = line.split("@github.com")[0].split(":", 2)[-1]
                    else:
                        continue
                    return token.replace("@github.com", "").strip()
    except Exception:
        pass
                if parsed.hostname != "github.com":
                    continue
                if "x-access-token:" in line:
                    token = line.split("x-access-token:")[1]
                elif "@github.com" in line:
                    token = line.split("@github.com")[0].split(":", 2)[-1]
                else:
                    continue
                return token.replace("@github.com", "").strip()
    except OSError as e:
        print(f"Warning: unable to read /opt/data/.git-credentials: {e}", file=sys.stderr)
    return None


def gh_api(token, method, path, data=None):
    url = f"{API_BASE}/{path.lstrip('/')}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method,
                                 headers={"Authorization": f"Bearer {token}",
                                          "Accept": "application/vnd.github.v3+json"})
    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"},
    )
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except json.JSONDecodeError:
            return e.code, {"message": body[:200]}


def collect_files():
    files = []
    for root, dirs, filenames in os.walk(SKILLS_BASE):
    for root, _dirs, filenames in os.walk(SKILLS_BASE):
        if "SKILL.md" in filenames:
            local = os.path.join(root, "SKILL.md")
            remote = local.replace(f"{SKILLS_BASE}/", "")
            files.append((local, remote))
    if os.path.exists(LJ_PATH):
        files.append((LJ_PATH, "LEARNING_JOURNAL.md"))
    cron_dir = os.path.expanduser("~/.hermes/cron")
    cfg = {"cron_jobs": [], "exported_at": date.today().isoformat()}
    if os.path.isdir(cron_dir):
        for fname in sorted(os.listdir(cron_dir)):
            fp = os.path.join(cron_dir, fname)
            if os.path.isfile(fp):
                with open(fp) as f:
                    try:
                        cfg["cron_jobs"].append({fname: json.load(f)})
                    except Exception:
                        cfg["cron_jobs"].append({fname: f.read()})
    tmp = "/tmp/cron-configs.json"
    with open(tmp, "w") as f:
        json.dump(cfg, f, indent=2)
    files.append((tmp, "cron-configs.json"))
    return files


def main():
    token = get_token()
    if not token:
        print("FAIL: no token")
        sys.exit(1)

    files = collect_files()
    pushed = skipped = 0
    failed = []

    for local, remote in files:
        with open(local, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

        status, data = gh_api(token, "GET", f"contents/{remote}")
        exists = status == 200

        if exists:
            if data.get("content", "").replace("\n", "") == b64:
                print(f"  ⏭️  {remote}")
                skipped += 1
                continue
            sha = data["sha"]
        else:
            sha = None

        name = remote.replace("/SKILL.md", "").split("/")[-1]
        if remote == "LEARNING_JOURNAL.md":
            name = "learning-journal"
        elif remote == "cron-configs.json":
            name = "cron-configs"

        put = {"message": f"SakSit: sync {name} — {date.today()}",
               "content": b64}
        put = {"message": f"SakSit: sync {name} — {date.today()}", "content": b64}
        if sha:
            put["sha"] = sha

        st, res = gh_api(token, "PUT", f"contents/{remote}", put)
        if st in (200, 201):
            print(f"  ✅ {remote}")
            pushed += 1
        else:
            print(f"  ❌ {remote}: {st} — {res.get('message','')}")
            print(f"  ❌ {remote}: {st} — {res.get('message', '')}")
            failed.append(remote)

    st, tree = gh_api(token, "GET", "git/trees/main?recursive=1")
    if st == 200:
        print(f"\nRepo: {len(tree.get('tree',[]))} entries on main")
        print(f"\nRepo: {len(tree.get('tree', []))} entries on main")
    print(f"\nPushed: {pushed} | Skipped: {skipped} | Failed: {len(failed)}")
    return pushed, skipped, failed


if __name__ == "__main__":
    main()
