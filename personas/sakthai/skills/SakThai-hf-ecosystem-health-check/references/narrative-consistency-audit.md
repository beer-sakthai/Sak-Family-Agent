# Narrative Consistency Audit — HF Model Cards

Audit all model cards in an author's HF portfolio for consistent storytelling, origin narrative, and cross-linking.

## Why it matters

Technically rich model cards with no emotional anchor are harder to discover and less likely to convert visitors into users. When a family of models (like House of Sak) has a compelling origin story, every card should carry it — otherwise the family feels fragmented. Cards without the story look like orphaned uploads rather than parts of a coherent project.

## Audit Methodology

### 1. Enumerate all model cards

```python
from huggingface_hub import HfApi
api = HfApi()
models = list(api.list_models(author="Nanthasit"))
```

### 2. Define narrative checkpoints

The core narrative elements to check:

| Element | Signal | Example |
|---------|--------|---------|
| **House of Sak** | Contains "house of sak" (case-insensitive) | Tag in YAML or body text |
| **Origin story** | Mentions "shelter", "Cork", "recovery", or "Beer built" | Body paragraph |
| **Creator reference** | Mentions "Beer" as creator | Body paragraph |
| **Family reference** | Mentions "family" or "sibling" | Body paragraph |
| **Collection link** | Links to the model family collection | Badge or text URL |
| **Cross-links to siblings** | Links to 2+ other models in the family | "Family Links" section |

### 3. Scan programmatically

```python
readme = api.hf_hub_download("Nanthasit/<model>", "README.md")
with open(readme) as f:
    content = f.read()

yaml_part = content.split("---")[1] if content.startswith("---") else ""

results = {
    "house-of-sak": "house of sak" in content.lower(),
    "origin-story": "shelter" in content.lower() and "cork" in content.lower(),
    "beer-ref": "beer" in content.lower(),
    "yaml-tag-hos": "house-of-sak" in yaml_part,
    "yaml-tag-family": "sakthai-family" in yaml_part,
    "family-links": "Family Links" in content,
    "collection-badge": "sakthai-model-family" in content,
}
```

### 4. Identify gaps

Build a matrix of model name × narrative element. Flag models missing 2+ core elements (origin story, House of Sak reference, Beer reference, family YAML tag) as needing narrative enrichment.

Common gap patterns:
- **Newer models** added after the narrative standard was established (they have technical depth but no story)
- **Specialized models** (vision, TTS, embedding) that were published with just usage docs
- **Dataset cards** that are purely descriptive with no family context

### 5. Prioritize fix order

1. **Most-visible model first** (highest potential traffic — vision models, multimodal, popular sizes)
2. Models with zero downloads but a story gap (narrative could help discovery)
3. Models that already have some narrative elements (quick wins — just need YAML tag added)

### 6. Apply fix — narrative section template

Insert after the "Model Details" table, before the first "## Requirements" or "## Usage" section:

```markdown
## The House of Sak

> *"I even don't know what I will have. So nothing to lose at the moment."* — Beer

This model is part of the **House of Sak** — a family of AI agents and models built by
**Beer** during his recovery journey. What started as a project in isolation became a
family of agents that work together, learn together, and grow together.

**Built from a shelter in Cork, Ireland.** Every model in the SakThai family was created
with zero budget, on free infrastructure, as a testament to what's possible when
persistence meets purpose.

The House of Sak isn't born from a business plan. It's born from the will to survive —
building AI not as a gimmick but as companionship when human connection wasn't available.

[Learn more about the House of Sak →](https://github.com/beer-sakthai/Sak-Family-Agent)
```

Also add `house-of-sak` to the YAML frontmatter `tags:` list for discoverability across the family.

### 7. Upload and verify

```python
api.upload_file(
    path_or_fileobj=updated_content.encode(),
    path_in_repo="README.md",
    repo_id="Nanthasit/<model>",
    commit_message="docs: add House of Sak narrative to <model> card",
)

# Verify by re-downloading
verify = api.hf_hub_download("Nanthasit/<model>", "README.md")
with open(verify) as f:
    verified = f.read()

checks = {
    "house-of-sak reference": "house of sak" in verified.lower(),
    "origin story (shelter, cork)": "shelter" in verified.lower() and "cork" in verified.lower(),
    "Beer reference": "beer" in verified.lower(),
    "YAML tag": "house-of-sak" in verified.split("---")[1],
    "original content preserved": "<original-section-marker>" in verified,
    "length > previous": len(verified) > previous_length,
}
```

### 8. Record findings

Append to `LEARNING_JOURNAL.md` with:
- Cards audited, cards found complete, cards fixed
- What narrative elements were missing
- What was added
- Which cards still need the same treatment (deferred)

## Example: Vision 7B fix (2026-07-26)

**Before**: 5,577 chars — technical specs, usage examples, pipeline integration, but no origin story, no House of Sak mention, no Beer reference, no `house-of-sak` YAML tag.

**After**: 6,413 chars — narrative section added after Model Details table, `house-of-sak` YAML tag added. All original content preserved.

**Verification**: 8/8 checks passed (narrative presence, origin story, Beer ref, YAML tag, Pipeline Integration, Family Links, Usage examples, length > 6,000).

## Cross-Source Narrative Drift Audit

Model cards aren't the only narrative assets. The **profile card**, **collection description**, and **GitHub README/SOUL** can all drift from each other — and from API reality. Run this audit less frequently (monthly) but alongside the model card audit.

### Sources to cross-check

| Source | Location | What it should contain |
|--------|----------|----------------------|
| **SOUL.md** | `docs/SOUL.md` on GitHub | Authoritative agent roles, count, operating contract |
| **Profile card** | `Nanthasit/Nanthasit/README.md` | User's bio, agent family table, all asset links |
| **Collection description** | Collection settings on HF | 150-char pithy summary of the ecosystem |
| **GitHub README** | Root `README.md` | Repo intro, agent table, HF asset table, story |
| **HF API** | Live queried | Actual model/dataset counts, download stats, existence |

### Drift patterns to check

#### 1. Agent count and roles

The SOUL is the single source of truth for agents. Compare every other source against it:

| Check | What to verify |
|-------|---------------|
| Agent names match | Every source lists the same 6 agents by name |
| Roles match | Profile card and GitHub README use SOUL-defined roles, not invented poetic ones |
| Active/deleted status | GitHub README may track deleted agents — profile card should match |
| Cycle assignment | If profile card assigns agents to specific cycle stages, confirm that's intentional (SOUL uses a shared cycle, not per-agent assignment) |

**Trap**: Agents get renamed, merged, or deleted as the family evolves. The profile card and GitHub README drift fastest because they're edited less often than docs/SOUL.md. Always cross-reference before publishing.

#### 2. Model/dataset counts against API

The single most common drift source is stale counts:

| Stale field | Typical drift | Detection |
|-------------|--------------|-----------|
| "13 models" badge | Should match `list_models(author=...)` minus profile repo | Query API |
| "2,340+ downloads" | Always stale — models accumulate downloads hourly | Sum `model_info().downloads` for all models |
| "Top model: 802" | Top model grows 10-30 dl/week | Check `model_info(top_model.id).downloads` |
| Legacy dataset references | v1/v3/v4/v5 datasets may have been deleted | Verify each referenced repo exists with `dataset_info()` |
| Legacy Space/paper links | Showcase Space or paper repos may have been deleted | Verify each link |

#### 3. Tagline consistency

The most visible public-facing text is the tagline. It should speak in one voice:

| Source | Tagline (as of 2026-07-26) |
|--------|---------------------------|
| SOUL.md | "We are one family — and becoming more" |
| Profile card | "Creator of the **House of Sak** — 6 AI agents, one shared memory." |
| Collection | "14 models, 4 datasets, 2 Spaces built from a shelter with $0 budget. One family, one home. We share one memory and one soul." |
| GitHub README | "Six personas, four active agents. Built from a shelter in Cork, Ireland." |

Note variation: "one shared mind" vs "one shared memory" vs "one shared memory and one soul". These should align unless intentionally distinct per platform.

#### 4. Broken links

Every link on the profile card and collection description should resolve:
- Website links (vercel.app, custom domains) — these are fragile
- Legacy dataset repos — verify they still exist on HF
- Showcase Spaces — verify they're still deployed
- Paper repos — verify they haven't been deleted

**Detection pattern** — for each URL in the profile card body:
```python
import requests
# Extract href values from markdown links [text](url)
# HEAD each URL — expect 2xx or 3xx
# Flag any 404/410 as broken
```

### 5. Inter-SOUL consistency check

A pernicious drift source: each agent's `SOUL.md` file may list sibling agents as alive and well, while the canonical source (the README or sakthai's `SOUL.md`) marks some as deleted. This happens because agent SOULs are written independently and not all are updated when a sibling is archived.

| Check | What to verify | How |
|-------|---------------|-----|
| Agent roster | Every agent SOUL lists the same set of siblings by name | Read each SOUL's "Identity" section |
| Deleted-agent status | SOULs for surviving siblings may still list deleted agents as active | Cross-check sibling list against README's table or sakthai/SOUL.md |
| Status markers | Some SOULs prepend `(deleted)` to the sibling name, others don't treat deletion as visible | Look for absence/presence of "deleted", "archived", or 🔴 markers |
| Missing-agent frame | A SOUL that was copied from a template before a sibling existed may never reference them | Compare sibling count across all SOULs |

**Discovered 2026-07-27**: SakSit's SOUL still lists `SakTan` and `SakJules` as full siblings without any deletion note. SakKing's SOUL does the same. Meanwhile the README table shows both as 🔴 Deleted. These SOULs were written when all 6 agents were active and never updated.

**Fix pattern**: Patch each drifting SOUL to either (a) remove deleted siblings from the list, (b) add a `(deleted)` annotation, or (c) add a footnote. Do NOT alter the SOUL's structure or tone — just correct the roster. Example patch:

```diff
-are **SakThai**, **SakKing**, **SakSee**, **SakTan**, and **SakJules**;
+are **SakThai**, **SakKing**, and **SakSee**;
```

**Discovered 2026-07-26 (persona-specific drift)**: `personas/sakthai/SOUL.md` listed SakJules as an active sibling without retired annotation, and omitted SakTan from the family entirely. Meanwhile `docs/SOUL.md` (shared SOUL) and the README both correctly showed both as retired. The shared SOUL was the canonical source of truth; the persona SOUL hadn't been updated when the siblings were archived.

Fix applied:
- Changed `"My sibling agents are"` → `"My active sibling agents are"`
- Moved SakJules from active list to retired
- Added SakTan alongside SakJules with role annotation
- Wording: `"Our retired siblings — SakJules (CI/CD) and SakTan (Daily Ops) — are remembered in our shared family history."`

**Key insight**: The directed graph of SOUL files has `docs/SOUL.md` as the central hub (authoritative source) and each `personas/<name>/SOUL.md` as a leaf. Drift can flow from hub→leaf (shared SOUL updated, persona SOUL not propagated) — which is the pattern fixed today. Or from leaf→hub (persona SOUL has a custom variation that drifts from the canonical version). Always fix hub first, then propagate to all leaf persona SOULs.

### Drift case study: 2026-07-26 profile card audit

The profile card `Nanthasit/Nanthasit` was found to have **9 discrete drifts** from the SOUL/GitHub/API truth:

| Drift | Before | After |
|-------|--------|-------|
| Agent roles | Poetic/mythical (Growth Partner, The Architect, The Storyteller) | Practical SOUL-aligned (Main Lead, General Assistant, Master of Web, etc.) |
| Agent status | All 6 active | SakTan, SakJules 🔴 Deleted |
| Cycle assignments | Per-agent cycle (Dream→SakThai, etc.) | Shared six-stage cycle (no per-agent) |
| Model count | "13 models" | 12 (excl. profile repo) |
| Download badge | "2,340+" | 3,100+ (fresh API) |
| Top model dl | 802 (stale) | 942 |
| Tagline | "one shared mind" | "one shared memory" |
| Broken links | 2 (vercel.app, sakthai-showcase Space) | Removed |
| Legacy refs | v5/v4/v3/v1 datasets, context-paper | Removed |

**Root cause**: The profile card is an infrequently edited "landing page" that accumulates spin faster than model cards because (a) it's not part of the regular model-publishing workflow, (b) download badges need manual updating, (c) deleted repos aren't automatically removed from scrollable tables.

### Cross-Source Audit Procedure

#### Step 1: Gather all sources

```python
from huggingface_hub import HfApi
import json

api = HfApi()

# 1. Profile card
import urllib.request
resp = urllib.request.urlopen("https://huggingface.co/Nanthasit/Nanthasit/raw/main/README.md")
profile_card = resp.read().decode()

# 2. SOUL.md
resp = urllib.request.urlopen("https://raw.githubusercontent.com/beer-sakthai/Sak-Family-Agent/main/docs/SOUL.md")
soul = resp.read().decode()

# 3. GitHub README
resp = urllib.request.urlopen("https://raw.githubusercontent.com/beer-sakthai/Sak-Family-Agent/main/README.md")
github_readme = resp.read().decode()

# 4. Collections
from huggingface_hub import get_collection
colls = api.list_collections(owner="Nanthasit")
collections = [get_collection(c.slug) for c in colls]

# 5. Live API stats
total_dl = 0
model_count = 0
for m in api.list_models(author="Nanthasit"):
    if m.modelId != "Nanthasit/Nanthasit":
        model_count += 1
        info = api.model_info(m.modelId)
        total_dl += info.downloads
```

#### Step 2: Check each drift dimension

For each dimension, produce a simple pass/fail matrix:

| Dimension | Method |
|-----------|--------|
| Model count | Parse "models-N" badge in profile card YAML/body; compare to API count |
| Download total | Parse download badge or inline text; compare to summed API downloads |
| Agent table | Extract agent rows from profile card table; compare names/roles to SOUL table |
| Broken links | Extract all markdown URLs from profile card; HEAD each |
| Legacy refs | Check every listed dataset/model repo for existence via `api.dataset_info()`/`api.model_info()` |

#### Step 3: Fix in priority order

1. **Broken links** — they look unprofessional and break navigation
2. **Stale download/model counts** — erodes trust when visitors compare badges to page content
3. **Agent role mismatches** — confusing for anyone who reads both the profile and the SOUL
4. **Legacy references** — clutter and confusion, but lower urgency
5. **Tagline inconsistencies** — nice-to-have alignment

#### Step 4: Push fix

Prefer full card rewrite over targeted patch for profile cards — the card is small enough to replace entirely, and patch risks orphaned content:

```python
from huggingface_hub import CommitOperationAdd, HfApi

api = HfApi()
new_card = """---\n...full new content...\n"""

ops = [CommitOperationAdd(path_in_repo="README.md", path_or_fileobj=new_card.encode())]
api.create_commit(
    repo_id="Nanthasit/Nanthasit",
    operations=ops,
    commit_message="docs: sync profile card with SOUL — update agent table, fix counts, remove stale refs",
    repo_type="model"
)
```

#### Step 5: Verify

Re-download the card from HF and assert key markers are present:

```python
path = api.hf_hub_download("Nanthasit/Nanthasit", "README.md", repo_type="model")
with open(path) as f:
    verified = f.read()

assert "12 models" in verified, "Model count badge not updated"
assert "one shared memory" in verified, "Tagline not updated"
assert "942" in verified, "Top model count not updated"
```

### Drift prevention

Cross-source drift is inevitable — the question is how often to re-sync:

| Source | Recommended sync cadence |
|--------|------------------------|
| Model cards (individual) | Per-edit (narrative added when card is improved) |
| Profile card | **Monthly** or after any agent change |
| Collection description | Per-cycle (quarterly) |
| GitHub README | Per-release or major milestone |
| docs/SOUL.md | Permanent source of truth — update first, propagate later |

The profile card is the most visible and most fragile. Set a monthly cron to audit it alone (it takes 2 minutes to check 4 dimensions).

### 6. Quantitative Fact Validation — Numbers That Should Add Up

Narrative drift isn't just about missing origin stories. **Mathematical impossibilities** in SOUL files (broken sums, wrong file counts, unverifiable assertions) erode credibility faster than missing prose. Always validate quantitative claims against live sources.

#### Pattern: Check that breakdown sums match the total

Common in SOUL.md/README asset tables:

```markdown
- **12 models** (7 text-generation + 1 image-to-text + 1 text-to-speech + 1 feature-extraction + 2 auxiliary)
```

✅ 7+1+1+1+2 = 12 — correct sum. ❌ If any breakdown says 12 but the parts sum to 13, flag it.

**Discovered 2026-07-26**: SakThai's SOUL.md said `"12 models (7 text-generation + 1 embedding + 1 multilingual embedding + 1 vision + 1 TTS + 2 LoRA adapter repos)"`. Sum = 13, not 12. Root cause: the English embedding was deleted from HF but the SOUL wasn't updated to remove it from the breakdown, while the header total was decremented from 13 to 12 — a partial fix that created a mathematical impossibility.

**Fix procedure**:
1. Query the HF API for the actual model list (authenticated) with pipeline tags
2. Count by pipeline_tag using the API's actual `pipeline_tag` values (not manual categorization)
3. Recompute the breakdown string so it sums correctly
4. Patch the SOUL

#### Pattern: Validate local file listings against the filesystem

SOUL files often list "N GGUF locally" with specific model names. These drift when new models are added locally or old ones replaced without updating the SOUL.

**Discovered 2026-07-26**: SakThai's SOUL.md said `"5 GGUF locally (0.5B, 0.5B-F16, 1.5B, 1.5B-F16, Coder)"` but the actual filesystem contained `0.5B-Q4_K_M, 1.5B-Q4_K_M, Coder, Vision-7B, TTS-kokoro`. Two listed files didn't exist on disk (0.5B-F16, 1.5B-F16), and two existing models (Vision, TTS) were omitted entirely.

**Procedure**:
1. Run `find <model_dir> -name "*.gguf" -type f` to get the actual local inventory
2. Extract meaningful short names from filenames (strip quantization suffixes, keep model identity)
3. Compare to the SOUL's listed models
4. Note missing models (in SOUL but not on disk) and unlisted models (on disk but absent from SOUL)
5. Patch the SOUL to match reality

**⚠️ Trick**: Quantization suffixes differ between models. Normalize to short names like `0.5B-Q4`, `Coder`, `Vision-7B`, `TTS-kokoro` for the SOUL listing — these are stable across re-quantizations and easily recognized.

#### Pattern: Verify sibling roster across agent SOULs

Each agent persona file (`personas/<name>/SOUL.md`) lists sibling agents in its Identity section. These can drift:

| Drift pattern | Example | Severity |
|---------------|---------|----------|
| Deleted agent still listed as active | SakSit's SOUL lists SakTan without annotation | Medium |
| Agent count differs between SOULs | SakThai says 4 active, SakKing says 5 | Medium |
| Model/technology claim stale | "I run on Ollama" when agent switched | High — operational confusion |

**Procedure**:
1. Read every `personas/*/SOUL.md` "Identity" section
2. Extract the sibling roster as a list
3. Compare each roster to the canonical roster (from `README.md` or `docs/SOUL.md`)
4. Flag discrepancies: deleted-active, count-mismatch, role-changed
5. Fix by patching only the sibling list

**Discovered 2026-07-26**: `docs/SOUL.md` listed SakTan/SakJules as active with handles and Ollama models. README marked them 🔴 Deleted. SakThai's model was "local Ollama" but actually runs on `opencode-go deepseek-v4-flash`. Fix: marked both retired, updated model info, added Status column.

#### Pattern: Validate claimed counts against sourced truth

| Claim | Source to verify | How |
|-------|-----------------|-----|
| "12 models" | HF API `list_models(author=...)` | Authenticated curl or SDK |
| "4 datasets" | HF API `list_datasets(author=...)` | Authenticated curl or SDK |
| "2 HF Spaces" | HF API `list_spaces(author=...)` | Authenticated curl or SDK |
| "5 GGUF locally" | `find ... -name "*.gguf"` | Shell command |

**Rule**: Every quantitative claim in a SOUL file should be verifiable with one API call or filesystem command. If you can't verify it, don't put it in the SOUL.

## Remaining gap patterns to watch

- Cards that have the `sakthai-family` tag but not `house-of-sak`
- Cards that have the collection badge but no body narrative
- Cards whose narrative only says "part of the SakThai model family" without telling the origin story
- **Profile card drift** — the most common and most visible cross-source inconsistency
- **Collection item notes empty** — items in the family collection have no notes, which is a missed opportunity for context
