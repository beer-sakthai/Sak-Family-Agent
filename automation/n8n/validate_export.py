import json
from pathlib import Path

path = Path(__file__).with_name("issue-triage.json")
data = json.loads(path.read_text())
nodes = data["nodes"]
assert data["active"] is False
assert data["settings"]["executionOrder"] == "v1"
assert len(nodes) == 9
names = {node["name"] for node in nodes}
assert len(names) == len(nodes)
assert {"GitHub Issue Webhook", "Validate GitHub Event", "Opened Issue?", "Classify Issue with AI", "Normalize Triage Result", "Apply GitHub Labels", "Post Triage Comment", "Acknowledge Triage", "Acknowledge Ignored Event"} == names

for source, branches in data["connections"].items():
    assert source in names, source
    for branch in branches["main"]:
        for connection in branch:
            assert connection["node"] in names, connection["node"]

webhook = next(node for node in nodes if node["name"] == "GitHub Issue Webhook")
assert webhook["parameters"]["responseMode"] == "responseNode"
assert webhook["parameters"]["httpMethod"] == "POST"

if_node = next(node for node in nodes if node["name"] == "Opened Issue?")
assert len(if_node["parameters"]["conditions"]["conditions"]) == 1

for node_name in ("Classify Issue with AI", "Apply GitHub Labels", "Post Triage Comment"):
    node = next(node for node in nodes if node["name"] == node_name)
    assert node["parameters"]["method"] == "POST"
    assert node["parameters"]["sendHeaders"] is True
    assert node["parameters"]["sendBody"] is True

comment = next(node for node in nodes if node["name"] == "Post Triage Comment")
assert "Normalize Triage Result" in comment["parameters"]["url"]
assert "Normalize Triage Result" in comment["parameters"]["jsonBody"]

print(f"valid n8n export: {path} ({len(nodes)} nodes)")
