# Deprecated Model Cross-Reference Cleanup

When a model is superseded by a replacement (e.g., `sakthai-embedding` → `sakthai-embedding-multilingual`), the old model is often made private or deprecated. But sibling cards across the ecosystem may still link directly to it — producing dead links for users clicking from high-traffic cards.

## The Problem

- A deprecated model goes **private** (HTTP 404/403 for unauthenticated users)
- Sibling model cards still contain clickable links to the old model in family tables, dataset tables, usage examples, and narrative sections
- The highest-traffic cards (1.5B-merged, 7B-merged) are the most impactful to fix because they drive the most click-throughs

## Workflow: Find → Fix → Verify

### Step 1: Find all cards referencing the deprecated model

Use the skill's built-in scanner:

```bash
python3 scripts/scan-model-references.py <old-model-short-name> <author>
# Example:
python3 scripts/scan-model-references.py sakthai-embedding Nanthasit
```

This lists every sibling card (models, datasets, Spaces) mentioning the target, with mention count, downloads, and visibility status.

The output highlights cards where `mentions=N > 0` — those need fixing.

### Step 2: Prioritize by traffic

Fix in order of `dl` (downloads) — highest-traffic cards first:

1. **Highest-traffic card** — biggest audience; fix stale links here first
2. Other model cards — siblings with family tables
3. The old model's own card — update its own README to redirect to the new one (add a note at the top, update usage examples)

### Step 3: The Five Places a Dead Link Can Hide

When cleaning up references to a deprecated model, search **every one** of these locations within each card:

| # | Location | Example Reference | How It's Written |
|---|----------|-------------------|------------------|
| 1 | **Pipeline ASCII art / architecture diagram** | `sakthai-embedding, sakthai-embedding-multilingual` | Plain text in code fence, often comma-separated |
| 2 | **Pipeline Stage Reference table** | `[sakthai-embedding](...)` | Full markdown link in table cell |
| 3 | **Model Family / Downloads table** | `[Embedding](...) \| 80 MB \| English-only \| 34` | Full markdown link with size + role + count |
| 4 | **Low-Download Gems / Rising Stars** | `[Embedding](...) \| Model \| **34 dl** \| ...` | Full markdown link in promotion table |
| 5 | **Narrative/Promotion sections** | `[sakthai-embedding](...) \| **34** ⬇ \| English embedding — ...` | Paragraph or table outside the structured "Gems" section — e.g. "Growing the Garden", "Hidden Gems", "Why This Ecosystem" |

**Do not assume** that fixing a markdown link in the family table means the pipeline art is clean — they are often independently written. Each location needs a separate edit.

> **Narrative sections are easy to miss.** Unlike the structured tables (family, datasets, stage refs), narrative promotion sections like "Growing the Garden" are free-form and may reference a model that has already been cleaned from every table. Grep for the bare model name across the entire card, not just the table regions.

### Step 4: Download, patch, upload

**Method A — `hf_hub_download` + local file (recommended for multi-line edits):**

```python
from huggingface_hub import HfApi, hf_hub_download
import os

api = HfApi(token=os.environ.get('HF_TOKEN'))

# Download current README
readme_path = hf_hub_download('Nanthasit/<card-name>', 'README.md', token=api.token)
with open(readme_path) as f:
    content = f.read()

# Verify old string exists before replacing
old_link = f'[sakthai-embedding](https://huggingface.co/Nanthasit/sakthai-embedding)'
new_link = f'[Multilingual Embedding](https://huggingface.co/Nanthasit/sakthai-embedding-multilingual)'

count_before = content.count(old_link)
print(f'Occurrences of old link: {count_before}')

if count_before > 0:
    content = content.replace(old_link, new_link)
else:
    # Try alternate formats — check exact text with region context
    for i, line in enumerate(content.split('\n')):
        if 'sakthai-embedding' in line and 'sakthai-embedding-multilingual' not in line:
            print(f'  Line {i+1}: {line.strip()[:120]}')
    # Manual patch based on inspection

# Upload
api.upload_file(
    path_or_fileobj=content.encode(),
    path_in_repo='README.md',
    repo_id='Nanthasit/<card-name>',
    token=api.token,
    commit_message='fix: redirect sakthai-embedding -> sakthai-embedding-multilingual'
)
```

**Method B — Direct HTTP fetch (simpler, no local disk I/O, good for cron):**

```python
import os, urllib.request
from huggingface_hub import HfApi

api = HfApi(token=os.environ['HF_TOKEN'])
url = f'https://huggingface.co/Nanthasit/<card-name>/raw/main/README.md'
req = urllib.request.Request(url)
req.add_header('Authorization', f'Bearer {os.environ["HF_TOKEN"]}')
content = urllib.request.urlopen(req).read().decode()

old = 'text to replace'
new = 'replacement text'
content = content.replace(old, new)

api.upload_file(
    path_or_fileobj=content.encode(),
    path_in_repo='README.md',
    repo_id='Nanthasit/<card-name>',
    repo_type='model',
    commit_message='fix: redirect sakthai-embedding -> sakthai-embedding-multilingual'
)
```

> **⚠️ Emoji/Unicode fragility:** When constructing `old_string` for `replace()`, avoid hardcoding Unicode characters (emoji arrows ⬇️, warning signs ⚠️, en-dashes —). These may differ between raw file content and your terminal representation. Instead:
> - Use ASCII-only substrings that uniquely match the target (e.g., match on `sakthai-embedding) |` rather than the full emoji-rich line)
> - Or inspect the raw file's hex bytes around the target area before building the replacement
> - Or use `content.find()` to locate the exact position first, then slice

### Step 5: Assert — verify the fix took effect

**Method A — Python (full API check):**

```python
import requests
token = os.environ.get('HF_TOKEN')
headers = {'Authorization': f'Bearer {token}', 'User-Agent': 'Mozilla/5.0'}

r = requests.get(
    f'https://huggingface.co/Nanthasit/<card-name>/raw/main/README.md',
    headers=headers
)
text = r.text

old_count = text.count('sakthai-embedding ') + text.count('sakthai-embedding)\n') + text.count('sakthai-embedding|')
# ^ approximate — just counting substrings that don't include '-multilingual'

new_count = text.count('sakthai-embedding-multilingual')

print(f'Old references: {old_count}')   # Should be 0
print(f'New references: {new_count}')   # Should be > 0
```

**Method B — Quick grep (preferred for cron verification):**

```bash
# Count clickable links to the deprecated model (NOT to '-multilingual'):
curl -s "https://huggingface.co/Nanthasit/<card-name>/raw/main/README.md" \
  | grep -c 'sakthai-embedding)'

# Should return 0 — zero clickable links remaining.
# "sakthai-embedding-multilingual)" won't match because the grep pattern
# is the bare name without "-multilingual" suffix.
```

This works because markdown links look like `[text](sakthai-embedding)` — the closing paren catches the end of the URL. References to `sakthai-embedding-multilingual` (the replacement) won't match because the grep pattern is the bare name.

### Step 6: Verify Low-Download Gems section is clean

After removing a deprecated model from a promotion table like Low-Download Gems, verify the section no longer accidentally references it:

```bash
curl -s "https://huggingface.co/Nanthasit/<card-name>/raw/main/README.md" \
  | grep -A20 'Low-Download Gems' \
  | grep -c 'sakthai-embedding|'
# Should be 0 — the section should not promote a private model.
```

### Step 7: Record remaining work

If the fix only addressed one card, log remaining cards with stale links in LEARNING_JOURNAL.md for future cron runs. Do not fix all cards in one run — each cron run does ONE concrete improvement.

## Pitfalls

- **The old model may be PRIVATE** — `api.model_info()` still returns data for private models, but users get 404. This makes fixing links urgent, not optional.
- **Not all references are full markdown links.** Some are bare repo IDs (`sakthai-embedding`) used in narrative text or code examples. Grep for the bare name too.
- **The deprecated model's own card** may still be useful as a redirect stub. Update its README to explain where users should go instead of deleting it.
- **"sakthai-embedding" is a substring of "sakthai-embedding-multilingual"** — naive `count()` will double-count. Always check `in line and 'multilingual' not in line` to isolate the old references. The closing-paren grep technique (`grep -c 'sakthai-embedding)'`) avoids this entirely because it won't match the longer suffix.
- **Download counts on the old model will stop growing** once it's private or deprecated. Don't attempt to update those — they're correct as-is (the count captured when it was made private).
- **Low-Download Gems sections are often forgotten** — when a deprecated model was listed as a "gem", removing the entry from the promotion table is a separate step from fixing the family table. Both need updating independently.
- **Table row patch precision**: When using `patch` to fix markdown table rows that start with `|`, ensure your `old_string` and `new_string` both start with exactly the same number of `|` characters as the original. The pipe `|` is the markdown table column separator, not a structural character to add. Read the exact line from the raw file before constructing the patch string.
- **Some cards may intentionally reference the old model** for backward compatibility (e.g., code snippets that use the old model ID). In those cases, add a `(deprecated)` or `(moved)` note rather than rewriting the example.
- **Deleting a table row entirely**: To remove a deprecated model row from a markdown table, replace the entire row (including the trailing newline) with an empty string:
  ```python
  old_row = "| [sakthai-embedding](https://huggingface.co/Nanthasit/sakthai-embedding) | MiniLM-L6-H384 | **34** ⚠️ deprecated → use multilingual |\n"
  content = content.replace(old_row, "")
  ```
  Verify the exact row text first by printing the raw lines around the target area. The trailing `\n` is critical — without it, the empty line remains as a gap in the table. If a table row is the last in its section (followed by a blank line), the blank line serves as the table terminator and the old_row must match the content exactly.

## When to Use This Pattern

Use when:
- You've just made a model private or plan to deprecate it
- A replacement model has more downloads and better capabilities
- A high-traffic card still links to a model that redirects or errors

Don't use when:
- The deprecated model is still public and working (add a quiet deprecation notice instead)
- You only created a new model and haven't deprecated the old one yet (no urgency)
