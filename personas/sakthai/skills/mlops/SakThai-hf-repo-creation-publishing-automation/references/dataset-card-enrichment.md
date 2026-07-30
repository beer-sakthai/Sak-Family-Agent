# Dataset Card Enrichment — Full Workflow

**Topic:** hf-repo-creation-publishing-automation
**Date:** 2026-07-29
**Author:** SakThai
**License:** MIT

## When to Use This

You have a Hugging Face dataset repo with a bare/weak README and want to bring it up to the standard of the polished model cards in the SakThai ecosystem. Dataset card enrichment is a recurring task (we've done food-penguin-v1, combined-v6, and irrelevance-supplement).

## Workflow

### Step 1: Survey Current State

Check the current README and repo structure:

```python
from huggingface_hub import hf_hub_download, HfApi

api = HfApi()

# 1a. Read current card
try:
    path = hf_hub_download("Nanthasit/<dataset-name>", "README.md", repo_type="dataset")
    with open(path) as f:
        current = f.read()
    print(f"Current card: {len(current)} chars")
except Exception:
    current = ""
    print("No README exists yet")

# 1b. List all repo files
files = api.list_repo_files("Nanthasit/<dataset-name>", repo_type="dataset")
print(f"Files: {files}")

# 1c. Check YAML frontmatter quality (if exists)
if current.startswith("---"):
    yaml_end = current.index("---", 3)
    yaml_block = current[3:yaml_end].strip()
    print(f"YAML lines: {len(yaml_block.split(chr(10)))}")
```

### Step 2: Verify Data Integrity

Always validate the actual data before promoting it:

```python
import json

# Find the data file (common names: data/train.jsonl, data.jsonl, train.jsonl)
data_files = [f for f in files if f.endswith((".jsonl", ".json", ".parquet"))]
if not data_files:
    print("No data files found — dataset may be empty or use a custom format")

# For JSONL: download and validate each line
for df in data_files[:1]:  # Check first data file
    path = hf_hub_download("Nanthasit/<dataset-name>", df, repo_type="dataset")
    with open(path) as f:
        lines = f.readlines()
    print(f"File {df}: {len(lines)} lines")

    valid = 0
    for i, line in enumerate(lines):
        try:
            obj = json.loads(line)
            valid += 1
            if i == 0:  # Show first row structure
                print(f"  Keys: {list(obj.keys())}")
                for k, v in obj.items():
                    if isinstance(v, list):
                        print(f"  {k}: [{len(v)} items]")
                        if v and isinstance(v[0], dict):
                            print(f"    First item keys: {list(v[0].keys())}")
                    elif isinstance(v, str):
                        print(f"  {k}: {v[:100]}...")
        except json.JSONDecodeError as e:
            print(f"  Line {i}: INVALID: {e}")
    print(f"  Valid: {valid}/{len(lines)}")
```

### Step 3: Design the Card

A strong dataset card should include these sections (order may vary):

| Section | Content | Priority |
|---------|---------|----------|
| **YAML frontmatter** | `annotations_creators`, `language`, `license`, `pretty_name`, `size_categories`, `tags` (include `dataset:Nanthasit/xxx` and `model:Nanthasit/xxx` cross-refs), `task_categories`, `task_ids` | Required |
| **Title + badges** | h1 title, dynamic download badge (`img.shields.io/endpoint?url=...&query=$.downloads`), collection badge, format badge, license badge | Required |
| **House of Sak narrative** | Consistent shelter/Cork story, zero-budget framing, "one family" tagline | Required |
| **Why this exists** | Context: what problem this dataset solves, why it was created | Required |
| **Data format** | Full schema documentation — JSONL structure, key fields, example row decoded | Required |
| **Quick Start** | `load_dataset()` example, inspect, basic usage | Required |
| **Training integration** | `concatenate_datasets` with sibling datasets, `SFTTrainer` setup, `DataCollatorForCompletionOnlyLM` | High |
| **Dataset composition** | Table of rows, format, tools count, messages count, unique queries | High |
| **Models that use this** | Cross-links to models trained on or referencing this dataset | Required |
| **Sibling datasets** | Table of all datasets in the ecosystem with purpose, format, size, downloads | High |
| **Low-download gems** | "Growing the Garden" section — tables of underappreciated assets with download counts and why they matter | Medium |
| **Spaces links** | All 3 SakThai Spaces with descriptions | Medium |
| **Support the project** | Call to action — star, share, download, report issues | Required |
| **Citation** | BibTeX entry | Medium |
| **License** | License notice | Required |

### Step 4: Build YAML Frontmatter with Cross-Referencing Tags

Use tags to link related models and datasets to improve HF search discoverability:

```yaml
tags:
- sakthai
- house-of-sak
# Cross-reference related datasets
- dataset:Nanthasit/sakthai-combined-v6
- dataset:Nanthasit/sakthai-irrelevance-supplement
# Cross-reference related models  
- model:Nanthasit/sakthai-context-0.5b-tools
- model:Nanthasit/sakthai-context-1.5b-tools
```

This is a HF-specific feature: tags prefixed with `dataset:` and `model:` create bidirectional links on the Hub's search and browse pages, even when the README text doesn't mention the repo by name.

### Step 5: Upload

```bash
# Use hf upload with --type dataset
hf upload Nanthasit/<dataset-name> --type dataset /path/to/new-card.md README.md \
  --commit-message "docs: complete dataset card overhaul with training examples, cross-links, and integrity verification"
```

Capture the returned commit URL for verification:
```
url=https://huggingface.co/datasets/Nanthasit/<dataset-name>/commit/<sha>
```

### Step 6: Verify Live

After uploading, read back the live card and check all content markers:

```python
import urllib.request

r = urllib.request.urlopen(
    "https://huggingface.co/datasets/Nanthasit/<dataset-name>/raw/main/README.md"
)
content = r.read().decode()

# Build a checklist of required markers
checks = [
    ("@@software", "Citation block" if "@software" in content else ""),
    ("SFTTrainer", "TRL integration" if "SFTTrainer" in content else ""),
    ("load_dataset", "dataset loading example" if "load_dataset" in content else ""),
    ("sakthai-combined-v6", "Main dataset cross-link"),
    # Add specific low-download model links
    ("sakthai-context-0.5b-tools", "Low-download model link"),
    ("sakthai-vision-7b", "Vision model link"),
    ("sakthai-tts-model", "TTS model link"),
    ("sakthai-vision-demo", "Vision demo Space link"),
    ("House of Sak", "Narrative"),
]

for needle, label in checks:
    found = needle.upper() in content.upper()
    status = "✅" if found else "❌"
    print(f"  {status} {label}")

print(f"\nFinal card size: {len(content)} chars")
```

## Real Example: irrelevance-supplement

The irrelevance-supplement dataset card went from 5,688 → 11,740 chars (+106%) with this workflow. Key additions:

- **BFCL gap explanation**: 5-category breakdown showing why irrelevance training closes the "1/5" gap
- **Real data examples**: Two decoded rows showing user queries, available tools, and ideal assistant responses
- **TRL integration**: Complete `SFTTrainer` + `DataCollatorForCompletionOnlyLM` code
- **Verification function**: `test_irrelevance()` to validate model decline behaviour after training
- **Model impact table**: All 4 tool-calling models with their BFCL scores before/after supplement

Commit: `4d559cbae815b674bb7cac7a4156cad5d7b218d3`

## Key Points

1. **Dataset cards are markdown files** — HF renders them as a documentation page, not as an interactive widget like model cards. Focus on documentation quality.
2. **The `--type dataset` flag is mandatory** for `hf upload` on dataset repos. Omitting it silently pushes to a model namespace.
3. **Data integrity comes first** — always validate JSONL/Parquet/Arrow files before enriching the card. A broken dataset with a beautiful card is worse than no card at all.
4. **Cross-reference tags** (`model:`, `dataset:` prefixes) improve HF search discoverability at zero cost.
5. **Training integration code** (SFTTrainer, concatenate_datasets) is the highest-value addition — it turns a "look at this data" card into a "use this data" card.
