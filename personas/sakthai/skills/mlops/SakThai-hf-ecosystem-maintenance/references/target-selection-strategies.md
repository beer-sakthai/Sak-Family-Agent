# Target Selection Strategies for HF Ecosystem Maintenance

Documented 2026-07-29 — strategies for deciding *which* card to work on
in each cron cycle. Choosing the right target is as important as the fix itself.

## Strategy 1: Lowest-Downloads First (Organic Growth)

**Pick the model or dataset with the lowest downloads that still needs work.**

Best for new ecosystems where the priority is validating that every asset has
a minimum viable card. Ensures no asset stays at 0 downloads forever.

**Selection query:**
```python
models = sorted(api.list_models(author="Nanthasit"), key=lambda m: m.downloads or 0)
targets = [m for m in models if "Nanthasit" not in m.id.split("/")[1] and m.downloads == 0]
```

**When to use:**
- First few cycles of a new ecosystem (assets < 10 dl)
- After a batch of new models/datasets was created
- When the directive specifically says "promote low-download models"

**Pitfall:** Zero-download assets are often newly created and may have no data
yet (empty scaffolds). Fixing the card before data exists means the promotion
leads nowhere — visitors arrive to "in preparation" text. Check data first.

**Pitfall — stale ecosystem counts on zero-download cards:** Zero-download
models are the *most likely* to have stale ecosystem summary counts (e.g.,
"5 datasets" when there are actually 6). This happens because:

- No human or cron has inspected the card since creation
- The YAML `datasets:` frontmatter was written at creation time and never
  refreshed to include new sibling datasets created later
- The datasets/sibling tables in the card body drifted independently from
  the actual ecosystem state

**Detection:** Before editing a zero-download card, verify ALL its ecosystem
counts against the current API state — not just download counts:

```bash
# Check what the card says
curl -s "https://huggingface.co/author/repo/raw/main/README.md" \
  | grep -oiP '\d+\s+(model|dataset|space)s?'

# Check what the ecosystem actually has
curl -s "https://huggingface.co/api/models?author=author" | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print(f'{len(d)} models')"
curl -s "https://huggingface.co/api/datasets?author=author" | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print(f'{len(d)} datasets')"
```

**Fix scope:** A single zero-download card fix should update:
1. Ecosystem count line (e.g., "5 datasets" → "6 datasets")
2. YAML `datasets:` frontmatter (add new siblings)
3. Datasets table in the body
4. Family table (add any new sibling models since card creation)

**Real example (Cron #021, 2026-07-29):** `sakthai-context-0.5b-tools-v2`
(0 dl) claimed "5 datasets" when the ecosystem had 6. The combined-v7
dataset was missing from YAML, datasets table, and training section.
The card had good badges and descriptions but its ecosystem cross-references
were frozen at creation time.

---

## Strategy 2: Highest-Traffic Depletion (Impact Maximization)

**Pick the highest-downloaded model still using old/outdated card format.**

Best for mature ecosystems where most high-traffic cards already have good cards
but a few holdouts remain. Fixing a 219-dl card reaches ~3x more visitors than
fixing a 70-dl card.

**Litmus test for "modern card":** Check whether the family table includes all
v2 models (e.g., `context-0.5b-tools-v2`, `context-1.5b-tools-v2`). If they're
absent, the card hasn't been overhauled yet.

```python
# Find highest-download model WITHOUT modern ecosystem cross-promotion
# Litmus: check for v2 models in family table
models = sorted(api.list_models(author="Nanthasit"), 
                key=lambda m: -(m.downloads or 0))
for m in models:
    if "Nanthasit" in m.id.split("/")[1]:  # skip profile
        continue
    if m.private:
        continue
    # Download card and check markers
    readme_path = api.hf_hub_download(repo_id=m.id, filename="README.md")
    with open(readme_path) as f:
        content = f.read()
    has_v2 = "context-0.5b-tools-v2" in content
    has_ecosystem = "Growing the Ecosystem" in content
    if not has_v2 or not has_ecosystem:
        print(f"NEEDS WORK ({m.downloads} dl): {m.id}")
```

**Additional modern-card markers (any missing = needs overhaul):**

| Marker | What it indicates | Priority |
|--------|-------------------|:--------:|
| `context-0.5b-tools-v2` in body | Family table includes v2 models | High |
| `13 models` in body | Count is current (not stale 12) | High |
| `6 datasets` in body | Dataset count is current (not stale 5) | High |
| `3 Spaces` in body | Space count is current | Medium |
| `Growing the Ecosystem` or `Low-Download Gems` | Has cross-promotion section | Medium |
| `combined-v7` in YAML datasets | YAML frontmatter is current | Medium |

**When to use:**
- After Strategy 1 rounds (all 0-dl assets have cards)
- When the directive says "improve cards with <50 downloads" but all low-dl
  assets already have enrichment — look for higher-dl cards still missing it
- When the ecosystem is mature (10+ cycles deep)

**Real example (Cron #020, 2026-07-29):**
`sakthai-context-7b-tools` (219 dl — #6 most downloaded) was still using old
compact format with grouped rows and stale counts. Fixed: 4,005 → 7,757 bytes.

---

## Strategy 3: Rotation (Fairness Coverage)

**Cycle through pipeline categories in round-robin order.**

Ensures that text-generation, feature-extraction, vision, TTS, and code models
all get attention rather than one category getting all the improvements.

**Categories:**
1. Text Generation / GGUF merged (1.5B, 0.5B, 7B, 7B-128K)
2. Tool-calling LoRA adapters (7B, 1.5B, 0.5B, v2 variants)
3. Specialized models (Vision, Coder, TTS)
4. Embedding models (multilingual, English)

**When to use:**
- After all cards in one category are done, rotate to the next
- When the ecosystem has diverse model types and you want to avoid neglecting
  a whole category

---

## Strategy 4: New-Asset Reactive

**Improve the most recently created asset that still lacks a proper card.**

Best for keeping up with ecosystem growth. When Beer or another sibling creates
a new repo, this strategy ensures it gets a card and collection entry within
1-2 cron cycles.

**Detection:** Use `new-asset-discovery.md` to find repos not in the baseline.

**When to use:**
- As the first check in every cron run (check for new repos before deciding
  what to improve)
- Immediately after Beer confirms a new model push
- When the "new model detected" note appeared in the previous cron journal

---

## Selection Decision Matrix

| Situation | Recommended Strategy | Rationale |
|-----------|---------------------|-----------|
| New ecosystem (<5 cycles old) | Lowest-Downloads First | Build baseline for all assets |
| 0-dl assets all have cards | Highest-Traffic Depletion | Maximize impact per cycle |
| New model detected | New-Asset Reactive | Catch it before it drifts |
| One category neglected | Rotation | Balance across ecosystem |
| Directive says "promote low-dl" | Lowest-Downloads First | Follow explicit goal |
| Most cards done, 3-4 holdouts | Highest-Traffic Depletion | Finish the job |
| Unknown/undirected | Highest-Traffic Depletion | Default: maximize reach |

## Cross-Reference

- `card-enrichment-patterns.md` — HOW to enrich a card once selected
- `new-asset-discovery.md` — HOW to detect new repos for Strategy 4
- `cron-execution-patterns.md` — HOW to execute the fix safely in cron
- `verification-patterns.md` — HOW to verify the fix was applied correctly
