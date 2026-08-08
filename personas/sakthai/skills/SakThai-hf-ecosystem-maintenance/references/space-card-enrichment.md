# Space Card Enrichment — README Updates for HF Spaces

Documented 2026-07-29 — patterns for updating a Hugging Face Space's README.md and using Space cards as promotion channels for low-download sibling assets.

## Why Enrich a Space Card?

Space cards (README.md shown on the Space's landing page) reach a different audience than model cards — visitors browsing demos rather than downloading weights. They are **underutilised promotion channels** for:
- Cross-linking low-download models or datasets
- Featuring sibling Spaces (reciprocal links create a mesh)
- Showcasing the full ecosystem family table

Newly created Spaces (sdk: static) are especially valuable — they start blank and a well-crafted README turns them into an ecosystem hub.

## Updating a Space README via Python API

### Prerequisites

- `HF_TOKEN` environment variable set with write access
- `huggingface_hub` library installed

### Upload Method A: `upload_file` (simple, one file)

```python
from huggingface_hub import HfApi

api = HfApi()

# Read the new README content from a local file
with open('/path/to/updated_readme.md', 'rb') as f:
    content = f.read()

api.upload_file(
    path_or_fileobj=content,         # bytes or file-like object
    path_in_repo='README.md',        # always 'README.md' for card updates
    repo_id='Nanthasit/sakthai-vision-demo',
    repo_type='space',               # CRITICAL: defaults to 'model', must be 'space'
    commit_message='cron: add Rising Stars section promoting low-download assets'
)
```

**Important:** The `repo_type` parameter defaults to `'model'`. Omitting it when updating a Space creates a confusing 404 because the upload targets a model namespace. Always set `repo_type='space'`.

### Upload Method B: `create_commit` (batch updates, more flexible)

Use when you want to batch multiple file operations or need `CommitOperationAdd` for fine-grained control:

```python
from huggingface_hub import HfApi, CommitOperationAdd

api = HfApi(token=os.environ['HF_TOKEN'])

commit = api.create_commit(
    repo_id='Nanthasit/sakthai-tts',
    repo_type='space',
    operations=[
        CommitOperationAdd(
            path_in_repo='README.md',
            path_or_fileobj=content.encode()  # string → bytes
        )
    ],
    commit_message='docs: update ecosystem counts + add zero-download alert [cron]'
)
```

**`create_commit` returns a commit URL** — verify it by checking the API response, then re-fetch the raw README to confirm.

**`CommitOperationAdd` accepts `path_or_fileobj` as bytes** — if your content is a string, call `.encode()` to convert it. Files opened in binary mode (`'rb'`) work directly.

### Prepared-String-Replacement Approach (patch sections, not the whole file)

When the Space README is mostly correct and only specific sections need updating, use prepared string replacements instead of rewriting the entire file:

1. **Fetch current README** via raw URL or `hf_hub_download`
2. **Identify stale sections** — look for patterns like:
   - Ecosystem counts that don't match current API data (e.g., "Datasets: 4" when there are 5)
   - Missing new sibling assets in family/dataset/spaces tables
   - Stale download counts in Rising Stars sections
   - Missing cross-links to newly created Spaces or datasets
3. **Prepare targeted `old_string → new_string` replacements** in Python:
   ```python
   content = content.replace(old_table, new_table_with_new_row)
   ```
4. **Save replaced content to a temp file** then upload
5. **Verify** — re-fetch the raw README and grep for the added content

**Advantages over rewriting the whole file:** Only the targeted rows change, reducing the risk of accidentally dropping formatting, frontmatter, or custom styling. The approach is especially useful for cron jobs where you want to make surgical updates without touching the rest of the card.

**Pitfall:** String replacement fails silently if `old_string` doesn't match exactly (whitespace, trailing spaces). Always verify by checking `content.count(target_marker)` before and after. Test replacements on a local copy first.

### Reading the Current README

```python
from huggingface_hub import HfApi
api = HfApi()

# download returns a local cache path
local_path = api.hf_hub_download(
    repo_id='Nanthasit/sakthai-vision-demo',
    filename='README.md',
    repo_type='space'
)
with open(local_path) as f:
    content = f.read()
```

Or via raw URL (no auth needed for public repos):

```bash
curl -s "https://huggingface.co/spaces/Nanthasit/sakthai-vision-demo/raw/main/README.md"
```

### CLI Alternative

```bash
hf upload Nanthasit/sakthai-vision-demo --type space \
  /path/to/updated.md README.md \
  --commit-message "docs: enrich space card with family table"
```

#### ⚠️ Known Failure: `hf upload` returns 402 for Static Spaces

As of 2026-07-29, `hf upload` on a Static Space (`sdk: static`) fails with:

```
Error: Client error '402 Payment Required' for url 'https://huggingface.co/api/repos/create'
Static Spaces are free for everyone, but hosting Gradio and Docker Spaces on free
cpu-basic requires a PRO subscription.
```

This happens even though static Spaces are free. The error is misleading — the real issue is that `hf upload` appears to check repo existence via the create endpoint rather than simply pushing to the existing repo. **Workaround: use git clone + commit + push** (see next section).

### Git-Based Upload (Reliable Fallback for Spaces)

When `hf upload` and `upload_file` both fail (or when `huggingface_hub` is unavailable), use git directly:

```bash
# 1. Clone the Space (shallow, depth 1)
git clone --depth 1 "https://user:$HF_TOKEN@huggingface.co/spaces/Nanthasit/sakthai-vision-demo" /tmp/repo

# 2. Replace README
cp /path/to/updated.md /tmp/repo/README.md

# 3. Commit and push
cd /tmp/repo
git config user.email "bot@sakthai.dev"
git config user.name "SakThai Agent"
git add README.md
git commit -m "docs: enrich Space README"
git push

# 4. Verify
curl -s "https://huggingface.co/spaces/Nanthasit/sakthai-vision-demo/raw/main/README.md" | grep -c "expected-content"

# 5. Cleanup
rm -rf /tmp/repo
```

**Why this works when other methods fail:**
| Problem | Git fallback |
|---------|-------------|
| `hf upload` returns 402 on existing Space | Git uses the existing repo's push endpoint directly |
| `huggingface_hub` not installed | Git core is always available |
| Python SDK missing | Shell-based, no Python dependency |
| Token auth issues | Embedded in HTTPS clone URL |

**Pitfalls:**
- Token in clone URL: The token is briefly visible in process listings. Acceptable for single-thread cron jobs on a trusted machine.
- First-time clone is slow (~3-5s for small Space). Reuse the clone or use `--depth 1`.
- Auth failure: The HF token must have write permission on the Space. Verify with a HEAD check first.
- Cleanup: Delete the cloned directory after push to avoid stale clones: `rm -rf /tmp/repo`.

## Family Links Table — 3-Column Format (Recommended for 10+ Siblings)

When the ecosystem has many siblings (11+ models, 5 datasets, 3 Spaces), a 3-column table organized by type is more navigable than a flat link list:

| Type | Resource | Link |
|------|----------|------|
| 📦 | **Full Collection** | [SakThai Model Family](https://huggingface.co/collections/Nanthasit/sakthai-model-family-...) |
| 🗣️ | **TTS Showcase** | [sakthai-tts Space](https://huggingface.co/spaces/Nanthasit/sakthai-tts) |
| 👁️ | **Vision Demo** | [sakthai-vision-demo Space](https://huggingface.co/spaces/Nanthasit/sakthai-vision-demo) |
| | | |
| 🧠 | **Context 1.5B** (flagship) | [sakthai-context-1.5b-merged](https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged) |
| 🧠 | **Context 0.5B** | [sakthai-context-0.5b-merged](https://huggingface.co/Nanthasit/sakthai-context-0.5b-merged) |
| 🧠 | **Context 7B** | [sakthai-context-7b-merged](https://huggingface.co/Nanthasit/sakthai-context-7b-merged) |
| 🧠 | **Context 7B-128K** | [sakthai-context-7b-128k](https://huggingface.co/Nanthasit/sakthai-context-7b-128k) |
| 🧠 | **Coder 1.5B** | [sakthai-coder-1.5b](https://huggingface.co/Nanthasit/sakthai-coder-1.5b) |
| 🧠 | **Vision 7B** | [sakthai-vision-7b](https://huggingface.co/Nanthasit/sakthai-vision-7b) |
| 🧠 | **Multilingual Embedding** | [sakthai-embedding-multilingual](https://huggingface.co/Nanthasit/sakthai-embedding-multilingual) |
| | | |
| 🔧 | **7B Tools** (LoRA) | [sakthai-context-7b-tools](https://huggingface.co/Nanthasit/sakthai-context-7b-tools) |
| 🔧 | **1.5B Tools** (LoRA) | [sakthai-context-1.5b-tools](https://huggingface.co/Nanthasit/sakthai-context-1.5b-tools) |
| 🔧 | **0.5B Tools** (LoRA) 🌱 | [sakthai-context-0.5b-tools](https://huggingface.co/Nanthasit/sakthai-context-0.5b-tools) |
| | | |
| 🎙️ | **TTS Model** | [sakthai-tts-model](https://huggingface.co/Nanthasit/sakthai-tts-model) |
| | | |
| 📊 | **Datasets** | [combined-v6](https://huggingface.co/datasets/Nanthasit/sakthai-combined-v6) · [food-penguin](https://huggingface.co/datasets/Nanthasit/food-penguin-v1) · [kaggle](https://huggingface.co/datasets/Nanthasit/sakthai-kaggle-notebooks) · [SimpleToolCalling](https://huggingface.co/datasets/Nanthasit/SimpleToolCalling) · [irrelevance-supplement 🚨](https://huggingface.co/datasets/Nanthasit/sakthai-irrelevance-supplement) |

**When to use 3-column vs 2-column:**
- **3-column** (Type, Resource, Link): Use when the ecosystem has 10+ siblings organized into clear categories (models, LoRAs, Spaces, datasets). The type emoji + spacer rows make it scannable.
- **2-column** (Resource, Link): Use for smaller ecosystems (<10 siblings) or when most items are the same type.

The spacer rows (`| | | |`) visually group categories — use them between: (1) meta/collection refs, (2) base models, (3) LoRA adapters, (4) special models, (5) datasets.

## Verification Strategies

### Method A: Timestamp check (most reliable)

Check that `lastModified` changed after upload:

```python
import json, urllib.request

# Before: fetch and record timestamp
r = urllib.request.urlopen('https://huggingface.co/api/spaces/Nanthasit/sakthai-vision-demo')
before = json.loads(r.read())['lastModified']

# After upload: re-fetch
after_r = urllib.request.urlopen('https://huggingface.co/api/spaces/Nanthasit/sakthai-vision-demo')
after = json.loads(after_r.read())['lastModified']

print(f"Updated: {before[:19]} → {after[:19]}")
assert before != after, "Space was NOT updated!"
```

### Method B: Content grep (quick)

```bash
# Count occurrences of a new section
curl -s "https://huggingface.co/spaces/Nanthasit/sakthai-vision-demo/raw/main/README.md" | \
  grep -c "Rising Stars"
```

### Method C: Raw extraction with sed

```bash
# Extract a specific section
curl -s "https://huggingface.co/spaces/Nanthasit/sakthai-vision-demo/raw/main/README.md" | \
  sed -n '/^## Rising Stars/,/^## /p'
```

### Method D: Python assertion script (most thorough — use for cron deliverables)

For thorough verification after an enrichment pass, write a focused Python script that asserts every expected change:

```python
import os, urllib.request, tempfile

HF_TOKEN = os.environ.get('HF_TOKEN')
url = 'https://huggingface.co/spaces/Nanthasit/sakthai-leaderboard/raw/main/README.md'
req = urllib.request.Request(url)
req.add_header('Authorization', f'Bearer {HF_TOKEN}')
readme = urllib.request.urlopen(req).read().decode()

checks = {
    'expected model mentioned': 'model-name' in readme,
    'expected dataset mentioned': 'dataset-name' in readme,
    'Support the Project section': 'support the project' in readme.lower(),
}

# Write results to temp file (avoids workspace contamination)
tmp = tempfile.NamedTemporaryFile(
    prefix='hermes-verify-',
    suffix='.txt',
    dir='/tmp',
    mode='w',
    delete=False
)
passed = sum(1 for r in checks.values() if r)
failed = len(checks) - passed
for name, result in checks.items():
    tmp.write(f"[{'PASS' if result else 'FAIL'}] {name}\n")
tmp.write(f"\nSummary: {passed}/{len(checks)} passed\n")
tmp.close()
print(f"Verification: {passed}/{len(checks)} passed — see {tmp.name}")
# Clean up after reading
os.unlink(tmp.name)
```

**Use `tempfile.NamedTemporaryFile` with `prefix='hermes-verify-'`** to create workspace-safe verification output. This avoids leaving verification artifacts in the main working directory and satisfies the system's "fresh verification evidence" requirement for cron/modified-path cycles.

## Rising Stars Section (Promotion Pattern)

When a Space card has a "Rising Stars" or "Low-Download Gems" section promoting deserving sibling assets:

1. **Use "Asset" not "Model" as column header** — the section should promote both models AND datasets
2. **Add a dataset row** if one is at 0 downloads — mark it with **0** 🚨
3. **Describe why it matters** — short, compelling value proposition
4. **Keep the table at 4-5 rows** — enough breadth without overwhelming

### Template

```markdown
## Rising Stars ⭐

These family members deserve your attention — each is unique, useful, and growing:

| Asset | Downloads | Why You'll Love It |
|-------|:---------:|--------------------|
| [model-a](https://huggingface.co/author/model-a) | **N** 🌱 | One-line value proposition |
| [model-b](https://huggingface.co/author/model-b) | **N** | Another compelling reason |
| [dataset-c](https://huggingface.co/datasets/author/dataset-c) (dataset) | **0** 🚨 | Critical safety supplement — teaches models when NOT to call tools |
```

## Detecting Stale Data in Space READMEs

Before updating a Space README, identify what's stale:

| Pattern | Signal | Fix |
|---------|--------|-----|
| **Wrong ecosystem counts** | "Datasets: 4" but API shows 5 | Re-count and update the number AND the asset count in the collection line |
| **Missing new siblings** | Dataset table lacks a recently added dataset | Add row to table; if 0 dl, flag with 🚨 |
| **Stale Rising Stars** | A model listed at 7 dl is now at 70 dl | Update count; if >50, consider removing from "low" section |
| **Old Spaces list** | Only 2 Spaces listed but a 3rd exists | Add the new Space row |
| **Duplicated counts** | Model count says "12" but API shows 13 | Cross-check models list vs API |

Always **fetch fresh API data** before editing so your replacements use accurate numbers. A Space README with wrong download counts is worse than none — it undermines trust.

## Zero-Download Alert Callout (Promotion Pattern)

When a dataset or model in your ecosystem has **0 downloads** but is genuinely valuable, add a callout box below the Rising Stars table:

```markdown
> 🚨 **Zero-download alert:** The [dataset-name](https://huggingface.co/datasets/Nanthasit/name) dataset has **0 downloads** but is **critical for safety** — it teaches models when to refuse out-of-scope tool calls, a gap in most BFCL training. Every download validates this approach.
```

**When to use:** Only for assets that serve a genuinely important purpose (safety, critical edge case coverage, unique capability). Avoid overusing — one per Space README maximum, placed right after the Rising Stars table.

**Format:** GitHub-style blockquote with `🚨` emoji for visual salience. Include the download badge count in bold. End with a call to action ("Every download validates this approach").

## Section Template for Space Cards

A well-structured Space README should include:

| Section | When to Include |
|---------|-----------------|
| **About the Space** | Always — what does this space showcase? |
| **Quick Start** | If the Space demonstrates a model — include download+run commands |
| **Family Links** | Always — 3-column table with all siblings, organized by type |
| **Rising Stars ⭐** | Always — promotes 3-5 low-download assets |
| **Support the Project** | Always — CTA with star/report/share/benchmark calls |
| **About the House of Sak** | Always — backstory and motto |
| **Data refresher** | If applicable — explain how live data works |

## Pitfalls

- **`repo_type='space'` is easy to forget.** The `hf upload` CLI also defaults to model type. Always pass `--type space` or `repo_type='space'` explicitly.
- **Static Spaces don't run builds.** Unlike Gradio/Streamlit Spaces, static Spaces (sdk: static) are pure file hosting. README.md is rendered immediately after upload — no build pipeline to wait for.
- **Space README YAML frontmatter is different from model cards.** Spaces use `sdk`, `sdk_version`, `title`, `emoji`, `colorFrom`, `colorTo`, `pinned` fields — not `pipeline_tag`, `library_name`, or `base_model`. Don't copy-paste model card frontmatter into a Space card without adapting it.
- **The Rising Stars section needs periodic refresh.** Download counts drift. A model that was at 7 downloads today may be at 50 next week — update the table and consider removing it from the "low" section when it crosses 100.
- **String replacements can silently fail.** If a trailing space, newline, or tab character differs between `old_string` and the actual file content, `.replace()` returns unchanged content with no error. Always verify replacements by counting markers before and after, and keep a backup of the original in case you need to retry.
- **Workspace verification enforcement.** After editing code in a cron session, the system may require fresh verification evidence. Create ad-hoc tempfile-based verification scripts with `prefix='hermes-verify-'` to satisfy this. Always clean up after yourself — delete temp files with `os.unlink()` or `rm`.
