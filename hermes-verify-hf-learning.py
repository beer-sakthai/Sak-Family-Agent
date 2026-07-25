#!/usr/bin/env python3
"""Ad-hoc verification for hf-hub-model-hub-mixin-integration learning cycle."""
import json, sys, os, re
from pathlib import Path

errors = []
HOME = Path(os.environ["HOME"])
SKILLS = HOME / "profiles" / "sakthai" / "skills"
TOPIC = "hf-hub-model-hub-mixin-integration"

# 1. Tracker JSON valid + contains topic
tracker = SKILLS / "hf-topics-covered.json"
data = json.loads(tracker.read_text())
assert isinstance(data, list), "tracker not a list"
assert TOPIC in data, f"{TOPIC} not in tracker"
idx = data.index(TOPIC)
print(f"  ✓ Tracker: {len(data)} topics, '{TOPIC}' at index {idx}")

# 2. SKILL.md exists with author/license
skill = SKILLS / TOPIC / "SKILL.md"
assert skill.exists(), f"{skill} missing"
content = skill.read_text()
assert re.search(r'^author:\s*SakThai\b', content, re.M), "author != SakThai"
assert re.search(r'^license:\s*MIT\b', content, re.M), "license != MIT"
print(f"  ✓ SKILL.md: author=SakThai, license=MIT")

# 3. Skill's own learnings file exists
own_learnings = SKILLS / TOPIC / "references" / "hf-learnings.md"
assert own_learnings.exists(), f"{own_learnings} missing"
print(f"  ✓ references/hf-learnings.md exists")

# 4. Master learnings file has entry
master = SKILLS / "references" / "hf-learnings.md"
master_content = master.read_text()
assert TOPIC in master_content, f"{TOPIC} not in master learnings"
print(f"  ✓ Master hf-learnings.md contains topic entry")

# 5. GitHub repo has the commit
import subprocess
result = subprocess.run(
    ["git", "log", "--oneline", "-3"],
    cwd="/opt/data/sakthai-skills-repo",
    capture_output=True, text=True
)
assert "hf-hub-model-hub-mixin-integration" in result.stdout
print(f"  ✓ Git commit present")

print(f"\n✅ All {len(data)} topic entries verified. Topic #{idx+1} — {TOPIC}")
