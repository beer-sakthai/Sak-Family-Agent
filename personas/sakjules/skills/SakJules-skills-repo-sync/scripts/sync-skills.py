#!/usr/bin/env python3
"""Sync SakJules skills to beer-sakthai/sakjules-skills.

Usage: python3 sync-skills.py

Extracts GitHub PAT from GH_TOKEN, GITHUB_TOKEN, gh auth token, or .git-credentials.
Does content comparison via base64 — only pushes changed files.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

REPO = os.getenv("SAKJULES_SKILLS_REPO", "beer-sakthai/sakjules-skills")
API_BASE = f"https://api.github.com/repos/{REPO}"
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SKILLS_BASE = Path(os.getenv("SAKTHAI_SKILLS_DIR", str(SKILL_DIR.parent)))


def get_token() -> str | None:
    # 1. Environment variables
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if token and token.strip():
        return token.strip()

    # 2. gh CLI token
    try:
        res = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=False)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass

    # 3. .git-credentials fallback
    for cred_path in [Path.home() / ".git-credentials", Path("/opt/data/.git-credentials")]:
        if cred_path.is_file():
            try:
                for line in cred_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        parsed = urlparse(line)
                        if parsed.hostname == "github.com":
                            tok = parsed.password or parsed.username
                            if tok:
                                return tok.strip()
                    except Exception:
                        pass
            except OSError as e:
                print(f"Warning: unable to read {cred_path}: {e}", file=sys.stderr)

    return None


def gh_api(token: str, method: str, path: str, data: dict | None = None) -> tuple[int, dict]:
    url = f"{API_BASE}/{path.lstrip('/')}"
    body = json.dumps(data).encode() if data else None
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
        resp_body = e.read().decode()
        try:
            return e.code, json.loads(resp_body)
        except Exception:
            return e.code, {"message": resp_body}


def sync() -> int:
    token = get_token()
    if not token:
        print("Error: GitHub token not found in GH_TOKEN, GITHUB_TOKEN, gh CLI, or .git-credentials.", file=sys.stderr)
        return 1

    print(f"Syncing SakJules skills from {SKILLS_BASE} to {REPO}...")
    skill_files = list(SKILLS_BASE.rglob("SKILL.md"))
    print(f"Found {len(skill_files)} SKILL.md files to verify.")

    pushed = 0
    skipped = 0
    errors = 0

    for sf in skill_files:
        rel = sf.relative_to(SKILLS_BASE).as_posix()
        content_bytes = sf.read_bytes()
        b64_content = base64.b64encode(content_bytes).decode("ascii")

        # Check existing remote file
        status, resp = gh_api(token, "GET", f"contents/{rel}")
        sha = None
        if status == 200:
            sha = resp.get("sha")
            remote_b64 = resp.get("content", "").replace("\n", "")
            if remote_b64 == b64_content:
                skipped += 1
                continue

        # Push updated content
        payload = {
            "message": f"SakJules: sync {rel} — {date.today().isoformat()}",
            "content": b64_content,
        }
        if sha:
            payload["sha"] = sha

        put_status, put_resp = gh_api(token, "PUT", f"contents/{rel}", payload)
        if put_status in (200, 201):
            print(f"  [PUSHED] {rel}")
            pushed += 1
        else:
            print(f"  [ERROR] {rel}: HTTP {put_status} — {put_resp.get('message', 'unknown error')}", file=sys.stderr)
            errors += 1

    print(f"Sync complete: {pushed} pushed, {skipped} unchanged, {errors} errors.")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(sync())
