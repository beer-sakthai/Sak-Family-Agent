# Cross-Link Validity Verification

Documented 2026-07-29 — pattern for detecting and fixing broken cross-links between sibling assets (model→dataset, dataset→model, card→sibling repo) that return 404.

## The Problem

Ecosystem cards link to sibling models, datasets, and Spaces to help visitors navigate the family. These links are added during enrichment cycles but rarely **verified for correctness** afterwards. A cross-link can be broken when:

- A card links to `sakthai-combined-v7` (planned name) but only `sakthai-combined-v6` exists
- A link URL was typed manually and has a typo or wrong repo type suffix
- A repo was renamed or moved after the cross-link was created
- A planned/placeholder repo was referenced in text before it was created

Unlike download URLs (which break when files move inside a repo), cross-links between siblings break when **the referenced repo doesn't exist at all**.

**Impact:** A visitor from a popular card (1,269 dl) clicking a sibling link and hitting HF's "404 — No such repo" page will not return. The entire ecosystem loses credibility.

## Detection: Extract All Cross-Repo URLs and Check for 200

### Step 1: Extract all HF repo references from a card

```bash
curl -s "https://huggingface.co/Nanthasit/<repo>/raw/main/README.md" \
  | grep -oP 'https://huggingface\.co/(models/|datasets/|spaces/)?Nanthasit/[a-zA-Z0-9_-]+' \
  | sort -u
```

### Step 2: Check each URL resolves

```python
import urllib.request, json, os

def check_repo_exists(repo_id: str, repo_type: str = "model") -> tuple[bool, str]:
    base = {
        "model": f"https://huggingface.co/api/models/{repo_id}",
        "dataset": f"https://huggingface.co/api/datasets/{repo_id}",
        "space": f"https://huggingface.co/api/spaces/{repo_id}",
    }
    try:
        req = urllib.request.Request(base[repo_type])
        token = os.environ.get("HF_TOKEN", "")
        if token: req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=10) as r:
            return True, f"HTTP {r.status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code} — REPO DOES NOT EXIST"
    except urllib.error.URLError as e:
        return False, f"Connection error: {e.reason}"

# Example: check all siblings referenced in a dataset card
import re
card = urllib.request.urlopen(
    "https://huggingface.co/datasets/Nanthasit/sakthai-irrelevance-supplement/raw/main/README.md"
).read().decode()

for match in re.finditer(r'https://huggingface\.co/(?:datasets/|spaces/)?(Nanthasit/[a-zA-Z0-9._-]+)', card):
    full_ref = match.group(0)
    repo_id = match.group(1)
    rtype = "dataset" if "/datasets/" in full_ref else "space" if "/spaces/" in full_ref else "model"
    exists, detail = check_repo_exists(repo_id, rtype)
    status = "✅" if exists else "❌ BROKEN"
    print(f"  {status} [{rtype:7s}] {repo_id:50s} {detail}")
```

### Step 3: Batch scan the entire ecosystem

```python
import urllib.request, json, re, os

AUTHOR = "Nanthasit"
TOKEN = os.environ.get("HF_TOKEN", "")

def get_json(url):
    req = urllib.request.Request(url)
    if TOKEN: req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def repo_exists(repo_id, rtype):
    base = {"model": "models", "dataset": "datasets", "space": "spaces"}[rtype]
    req = urllib.request.Request(f"https://huggingface.co/api/{base}/{repo_id}")
    if TOKEN: req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        urllib.request.urlopen(req, timeout=10)
        return True
    except urllib.error.HTTPError:
        return False

# Gather all repos
for rt, key in [("model", "models"), ("dataset", "datasets"), ("space", "spaces")]:
    for item in get_json(f"https://huggingface.co/api/{key}?author={AUTHOR}"):
        repo_id = item["id"]
        if repo_id.endswith(f"/{AUTHOR}"): continue
        try:
            base = f"https://huggingface.co/{key}/{repo_id}" if rt != "model" else f"https://huggingface.co/{repo_id}"
            card = urllib.request.urlopen(f"{base}/raw/main/README.md", timeout=10).read().decode()
        except urllib.error.HTTPError:
            try:
                card = urllib.request.urlopen(f"{base}/raw/main/index.html", timeout=10).read().decode()
            except: continue
        for m in re.finditer(rf'https://huggingface\.co/(?:datasets/|spaces/)?({AUTHOR}/[a-zA-Z0-9._-]+)', card):
            target_id = m.group(1)
            if target_id == repo_id: continue
            rtype = "dataset" if "/datasets/" in m.group(0) else "space" if "/spaces/" in m.group(0) else "model"
            if not repo_exists(target_id, rtype):
                print(f"❌ [{rt:7s}] {repo_id:40s} → [{rtype:7s}] {target_id}")
```

## Fixing a Broken Cross-Link

### 1. Find the correct target

Look at context around the broken link. If it references `sakthai-combined-v7` with a download count of 175, the actual repo is probably `sakthai-combined-v6` (which has 175 dl):

```bash
curl -s "https://huggingface.co/api/datasets?author=Nanthasit&search=combined" \
  | python3 -c "import json,sys; [print(d['id'], d.get('downloads',0)) for d in json.load(sys.stdin)]"
```

### 2. Update the card

```bash
curl -s -o /tmp/card_fixed.md "https://huggingface.co/datasets/Nanthasit/<dataset>/raw/main/README.md"
sed -i 's|sakthai-combined-v7|sakthai-combined-v6|g' /tmp/card_fixed.md
hf upload Nanthasit/<dataset> /tmp/card_fixed.md README.md \
  --repo-type dataset \
  --commit-message "Fix broken cross-link: combined-v7→combined-v6 (v7 doesn't exist)"
```

### 3. Verify

```bash
# Confirm broken URL gone
curl -s "https://huggingface.co/datasets/Nanthasit/<dataset>/raw/main/README.md" | grep -c "sakthai-combined-v7"
# Expected: 0

# Confirm correct URL present
curl -s "..." | grep -c "sakthai-combined-v6"
# Expected: ≥1
```

## Placeholder Inflation of Footer Counts

When a card lists both real and planned models in a single table, the ecosystem footer ("12 models · 5 datasets") must count **only repos that actually exist on HF**, not all rows in the table.

### Detection

```bash
curl -s "https://huggingface.co/api/models?author=Nanthasit" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); r=[m for m in d if m.get('pipeline_tag') and m['id'] != 'Nanthasit/Nanthasit']; print(f'{len(r)} real models')"
curl -s "https://huggingface.co/api/datasets?author=Nanthasit" \
  | python3 -c "import json,sys; print(f'{len(json.load(sys.stdin))} datasets')"
curl -s "https://huggingface.co/api/spaces?author=Nanthasit" \
  | python3 -c "import json,sys; print(f'{len(json.load(sys.stdin))} Spaces')"
```

### Fix

If footer says "15 models" but API returns 12, update the footer. Planned/placeholder rows are useful for roadmap visibility but should NOT inflate the summary count.

**Rule:** `"[count] models · [count] datasets · [count] Spaces"` always matches API reality. Table rows can list planned items (marked with 🌱), but the summary is reserved for **shippable, downloadable assets only**.

## When to Run This Check

| Trigger | Action |
|---------|--------|
| After adding a new asset | Check existing cards that might reference the new name (often typed before repo existed) |
| After each enrichment cycle | Batch-scan all cards for 404 URLs |
| When a card references a v2/v7/bench name | Verify the target exists BEFORE linking |
| Monthly full audit | Run the batch Python scan across all repos |

## Real Example (2026-07-29)

`sakthai-irrelevance-supplement` linked to `sakthai-combined-v7` in two places — but that repo doesn't exist. The intended target was `sakthai-combined-v6` (175 dl). Fix: correct the URL and remove phantom entries. Commit: `d2a2e80`.

`sakthai-vision-7b` footer said "15 models · 7 datasets" from counting placeholder rows. Actual: 12 models, 5 datasets. Fix: correct footer to API reality. Commit: `4938171`.

## Relation to Other References

- `url-path-verification.md` — verifies *download URLs*; this covers *cross-link URLs* between siblings
- `stale-count-detection.md` — detects stale *numbers*; this detects stale *repo references* (404s)
- `cross-link-gap-enrichment.md` — *adds missing* cross-links; this *validates existing* ones
- `verification-patterns.md` — general verification checklist — add a row for cross-link validity
