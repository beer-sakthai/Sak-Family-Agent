# Adding model-index YAML to a Model Card

Adds structured evaluation data to the YAML frontmatter — renders the "Evaluations" section on the HF model page and improves search ranking.

## When to Add

Any model card that has:
- A pipeline tag that supports evaluation (text-generation, image-to-text, text-to-speech, feature-extraction, etc.)
- Published benchmarks (upstream base model scores, internal suite results)
- `model-index` missing from its YAML frontmatter

Models with model-index get an "Evaluations" tab on their HF page and rank higher in filtered searches.

## Workflow

### 1. Check if model already has model-index

```python
import urllib.request, json
url = "https://huggingface.co/api/models/{author}/{repo}"
with urllib.request.urlopen(url) as r:
    d = json.loads(r.read().decode())
card = d.get('cardData', {}) or {}
mi = card.get('model-index')
print(f"Has model-index: {bool(mi)}")
```

### 2. Fetch current README

```python
from huggingface_hub import hf_hub_download
path = hf_hub_download(repo_id="{author}/{repo}", filename="README.md", repo_type="model")
with open(path) as f:
    content = f.read()
```

### 3. Add model-index to YAML frontmatter

The YAML frontmatter is between the first `---` and second `---`. Add `model-index:` after the `tags:` block (or after `datasets:` / `base_model:`).

Template for text-generation models:
```yaml
model-index:
- name: {repo-name}
  results:
  - task:
      type: text-generation
      name: Benchmark Name
    dataset:
      name: Dataset Name
      type: dataset-type
    metrics:
    - type: accuracy
      value: 0.85
      name: Metric Name (description)
      verified: false
```

Template for image-to-text (vision) models:
```yaml
model-index:
- name: {repo-name}
  results:
  - task:
      type: image-to-text
      name: Image Captioning
    dataset:
      name: Upstream reference
      type: upstream
    metrics:
    - type: accuracy
      value: 0.75
      name: CIDEr (reference)
      verified: false
```

Template for text-to-speech models:
```yaml
model-index:
- name: {repo-name}
  results:
  - task:
      type: text-to-speech
      name: Text-to-Speech (English)
    dataset:
      name: Upstream eval
      type: upstream
    metrics:
    - type: mos
      value: 3.8
      name: Mean Opinion Score (reference)
      verified: false
```

Template for feature-extraction (embedding) models:
```yaml
model-index:
- name: {repo-name}
  results:
  - task:
      type: semantic-similarity
      name: Semantic Similarity
    dataset:
      name: STS Benchmark
      type: sts-benchmark
    metrics:
    - type: spearman_cosine
      value: 0.79
      name: Spearman Correlation
      verified: false
  - task:
      type: retrieval
      name: Retrieval
    dataset:
      name: Amazon Reviews
      type: amazon-reviews
    metrics:
    - type: map_at_100
      value: 0.38
      name: MAP@100
      verified: false
```

### 4. Verification: Two Checks

**Check A — API cardData (authoritative):**
```python
url = "https://huggingface.co/api/models/{author}/{repo}"
with urllib.request.urlopen(url) as r:
    d = json.loads(r.read().decode())
card = d.get('cardData', {}) or {}
mi = card.get('model-index')
assert bool(mi), "❌ model-index not in cardData"
for entry in mi:
    n = len(entry.get('results', []))
    assert n > 0, f"❌ Entry {entry.get('name')} has 0 results"
    print(f"✅ {entry.get('name')}: {n} results")
```

**Check B — Raw README YAML (surface-level):**
```python
import urllib.request
readme = urllib.request.urlopen("https://huggingface.co/{author}/{repo}/raw/main/README.md").read().decode()
# Find the YAML frontmatter: between first two --- markers
start = readme.find('---')
end = readme.find('---', start + 3)
frontmatter = readme[start:end + 3]
assert 'model-index' in frontmatter, "❌ model-index missing from YAML frontmatter"
print("✅ model-index found in YAML frontmatter")
```

> ⚠️ **Pitfall:** Check the FULL frontmatter section (between `---` and `---`), not just the first 200 chars. In long frontmatters with 15+ language entries, `model-index:` may appear later in the block.

## Relevant Metrics by Pipeline Type

| Pipeline Tag | Recommended Metric Types | Source |
|-------------|------------------------|--------|
| text-generation | accuracy, pass@1, bleu, rouge | Internal eval, upstream leaderboard |
| image-to-text | cider, spice, meteor | Upstream LLaVA / BLIP eval |
| text-to-speech | mos, wer, speaker_similarity | Upstream Kokoro / YourTTS eval |
| feature-extraction | spearman_cosine, map_at_100, accuracy, mrr, v_measure | MTEB leaderboard |
| sentence-similarity | spearman_cosine, pearson | STS Benchmark |
| text-to-audio (music) | clam, fd, kl | Upstream eval |

## Semantic Versioning for Model-Index Updates

- Add new results — append to existing list
- Verified results — change `verified: false` → `verified: true` with evidence
- Remove stale results — delete the entry entirely (don't leave empty entries)

## One concrete example: sakthai-tts-model (2026-07-29)

**Before:** 89 lines, solid README, no model-index in YAML. The model page had no "Evaluations" section.

**After:** Added model-index with 2 entries:
1. Text-to-Speech (English) — MOS 3.8 (Kokoro upstream reference, verified: false)
2. Multilingual TTS (15 languages) — language count metric (15, verified: false)

**Verification:**
```python
# API confirms model-index parsed correctly
# raw README shows model-index in frontmatter
# lastModified timestamp updated
```

**Full workflow used:**
```python
from huggingface_hub import HfApi

api = HfApi()
path = api.hf_hub_download(repo_id="Nanthasit/sakthai-tts-model", filename="README.md", repo_type="model")
with open(path) as f:
    content = f.read()

# String replace of the tags block
new_content = content.replace(old_yaml_tags, new_yaml_tags_with_model_index)

with open("/tmp/updated_readme.md", "w") as f:
    f.write(new_content)

api.upload_file(
    repo_id="Nanthasit/sakthai-tts-model",
    path_in_repo="README.md",
    path_or_fileobj="/tmp/updated_readme.md",
    repo_type="model",
    commit_message="Add model-index with upstream metrics (verified: false)",
)
```
