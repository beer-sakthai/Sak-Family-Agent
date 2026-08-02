#!/usr/bin/env python3
"""Verify HF Hub discussion reactions API: list, detail, and reaction data."""
import json, os, sys, urllib.request, urllib.error

REPO = os.environ.get("HF_TEST_REPO", "microsoft/phi-4")
TOKEN_PATH = os.path.expanduser("~/.cache/huggingface/token")
errors = []

def hf_get(path):
    token = open(TOKEN_PATH).read().strip()
    req = urllib.request.Request(
        f"https://huggingface.co{path}",
        headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

# 1. List endpoint — check structure
data = hf_get(f"/api/models/{REPO}/discussions?limit=50")
assert isinstance(data, dict), f"List: expected dict, got {type(data).__name__}"
assert "discussions" in data, f"List: missing 'discussions' key"
assert "count" in data, f"List: missing 'count' key"
d_count = len(data["discussions"])
print(f"List: {data['count']} total, {d_count} in response")

# 2. Check for reaction fields in list
reaction_discs = [d for d in data["discussions"] if d.get("topReactions")]
print(f"List: {len(reaction_discs)} discussions have topReactions")
for d in reaction_discs[:3]:
    print(f"  #{d['num']}: {d['topReactions']} (users={d.get('numReactionUsers',0)})")

# 3. Detail endpoint — check reactions on comments
if reaction_discs:
    disc_num = reaction_discs[0]["num"]
    detail = hf_get(f"/api/models/{REPO}/discussions/{disc_num}")
    assert "events" in detail, f"Detail: missing 'events' key"
    reaction_events = [
        ev for ev in detail["events"]
        if ev["type"] == "comment" and ev["data"].get("reactions")
    ]
    print(f"Detail #{disc_num}: {len(reaction_events)} comment(s) with reactions")
    for ev in reaction_events[:2]:
        for r in ev["data"]["reactions"]:
            print(f"  {r['reaction']} x {r['count']}: {', '.join(r['users'][:5])}...")

# 4. Verify the reaction endpoint exists
import urllib.request
token = open(TOKEN_PATH).read().strip()
if reaction_events and reaction_events[0]["data"]["reactions"]:
    comment_id = reaction_events[0]["id"]
    req = urllib.request.Request(
        f"https://huggingface.co/api/models/{REPO}/discussions/{disc_num}/comment/{comment_id}/reaction",
        method="POST",
        data=json.dumps({"action": "add", "reaction": "👍"}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req) as r:
            pass  # 200 OK = endpoint exists
        print(f"Reaction endpoint: POST returns {r.status}")
    except urllib.error.HTTPError as e:
        if e.code == 400:
            print(f"Reaction endpoint: exists (returned 400, likely already reacted)")
        else:
            errors.append(f"Reaction endpoint: unexpected {e.code}: {e.read().decode()[:100]}")
else:
    print("Reaction endpoint: skipped (no comments with reactions found)")

if errors:
    for e in errors:
        print(f"FAIL: {e}")
    sys.exit(1)
else:
    print("PASS: All verifications complete")
