# Model Card Standard (Lean) — HF Card Workflow

The canonical rules for writing/updating any `Nanthasit/*` model, dataset, **or Space**
card. Cards should read like an ML engineer wrote them: accurate, scannable,
low-maintenance. Keep the House of Sak identity, drop the marketing bloat.

> Adopted 2026-07-29 after a full ecosystem rewrite. This REPLACES the old "enrich every
> card with a full family table + download counts + comparison tables + Rising Stars"
> pattern, which produced stale, repetitive, low-credibility cards. **Do not reintroduce
> that pattern.**

## Global rules (apply to every card)

1. **No hardcoded download numbers anywhere.** Use ONE dynamic badge at the top:
   ```html
   <img src="https://img.shields.io/badge/dynamic/json?url=https%3A//huggingface.co/api/models/Nanthasit/REPO&query=%24.downloads&label=downloads&color=blue&cacheSeconds=3600" alt="Downloads"/>
   ```
   Use `badge/dynamic/json` with `query=$.downloads`, **not** `endpoint`. The HF API returns
   repo metadata, not shields' `{schemaVersion,label,message}` contract, so an `endpoint`
   badge renders the literal text `invalid properties: label, message`. The `url=` value must
   stay percent-encoded (`https%3A//…`) or shields drops the query string.
   (Datasets: swap `/api/models/` for `/api/datasets/`.) Family tables carry **size + role**, never
   counts. Hardcoded numbers go stale the moment you push — never emit them, and never emit a
   `badge/downloads-625-blue`-style static badge.
2. **One family table per card**, not three. Use the canonical table below verbatim.
3. **Personal / recovery story lives on the profile card only.** Every other card gets a
   one-line identity + a `[Read the story →](https://huggingface.co/Nanthasit)` link. Never
   duplicate the full story across cards.
4. **Honest evals only.** Never set `verified: true` (that means HF-verified — we are not).
   Label internal numbers "internal, not third-party verified". `model-index` values must be
   real numbers (e.g. `100.0`), never strings like `5/5`. Mark base-model reference scores as
   base-model scores.
5. **No funnel sections.** Do NOT add "Rising Stars", "Low-Download Gems", "Growing the
   Garden", "Hidden Gems", "zero-download alert", or multi-bullet "Support the Project"
   sections. One short support line at most.
6. **Canonical facts** (never contradict):
   - Ecosystem size: **12 models in the family · 8 datasets · 3 Spaces**.
     Verified against the Hub API on 2026-07-30: there are **15 public model repos**
     (16 counting the `Nanthasit/Nanthasit` profile repo), **8 public datasets**, and
     **3 Spaces**. "12 models" is the *curated family* — the 15 minus the
     `0.5b-exp-lora-masked-v4` tombstone, the stray `combined-v6` model repo, and the
     private/superseded `sakthai-embedding`. Say "12 models in the family", never a bare
     "12 models", or it contradicts the profile page a visitor can count for themselves.
     The old "5 datasets" was simply wrong — do not reintroduce it.
   - Collection URL (full, hashed): `https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02`
   - `food-penguin-v1` = **restaurant-analytics tool-calling** dataset (7 functions), NOT image classification.
   - There is **no** `sakthai-context-paper` repo — never add a "Paper" link to it.
   - Private English `sakthai-embedding` is superseded by `sakthai-embedding-multilingual`;
     do not list the private repo in family tables.
7. **Preserve YAML frontmatter**; only edit content after the closing `---`. Don't re-upload
   unchanged cards. Spot-check 2–3 cards a few minutes after a batch push (a sibling-agent
   commit or CDN cache can mask the result).

## Section order (models)

1. `<h1>` + one-line tagline
2. Badge row (dynamic downloads + license + params/size + collection)
3. One-blockquote identity + `[Read the story →]` link
4. `## What it is` — 2–3 sentences: base, method, what it does
5. `## Quick start` — ONE primary code block (+ one CPU/Ollama line if GGUF)
6. `## Training` — compact table + one-line architecture
7. `## Evaluation` — honest table, internal-vs-verified labeled
8. `## SakThai model family` — the canonical table below (once)
9. `## Links` — inline, one line
10. `## License`

**Datasets have their own SOP** — see [`dataset-card-standard.md`](dataset-card-standard.md),
which layers Hugging Face's official dataset-card spec (required YAML, closed enums, the
`configs`/`dataset_info` no-touch rule) on top of these lean rules. Follow it, not this file,
for anything under `huggingface.co/datasets/Nanthasit/`.

Datasets follow the same spine: identity → What it is → Quick start (load snippet) →
structure/stats → trained-models → License. Right-size the card to the content (a 10-example
dataset does not need a 260-line card).

**Space cards** (`README.md` in a Space repo) follow the same lean rules — same don'ts (no
funnel, no hardcoded counts, no repeated family tables, story on the profile). Two extra
constraints: (a) **preserve the Space config frontmatter** (`title`, `emoji`, `colorFrom`,
`colorTo`, `sdk`, `pinned`) exactly, or the Space breaks — edit only the body and trim
promo-only tags; (b) the demo page itself (`index.html`) must get its numbers **live from
the HF API** (`https://huggingface.co/api/models?author=Nanthasit`), never hardcode download
counts in the page.

## Canonical family table (copy verbatim; mark the current repo with ⬅)

```markdown
| Model | Size | Role |
|---|:--:|---|
| [context-1.5b-merged](https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged) | 934 MB | Flagship tool-calling GGUF |
| [context-0.5b-merged](https://huggingface.co/Nanthasit/sakthai-context-0.5b-merged) | 380 MB | Lightweight / edge |
| [context-7b-merged](https://huggingface.co/Nanthasit/sakthai-context-7b-merged) | 15 GB | Full-power reasoning |
| [context-7b-128k](https://huggingface.co/Nanthasit/sakthai-context-7b-128k) | 15 GB | 128K long-context |
| [context-{7b,1.5b,0.5b}-tools](https://huggingface.co/Nanthasit/sakthai-context-1.5b-tools) | LoRA | Tool-calling adapters |
| [coder-1.5b](https://huggingface.co/Nanthasit/sakthai-coder-1.5b) | 1.1 GB | Code generation |
| [vision-7b](https://huggingface.co/Nanthasit/sakthai-vision-7b) | 3.9 GB | Image→text (LLaVA) |
| [embedding-multilingual](https://huggingface.co/Nanthasit/sakthai-embedding-multilingual) | 80 MB | Cross-lingual embeddings |
| [tts-model](https://huggingface.co/Nanthasit/sakthai-tts-model) | 141 MB | Text-to-speech, 15 langs |

**12 models in the family · 8 datasets · 3 Spaces** — [full collection →](https://huggingface.co/collections/Nanthasit/sakthai-model-family-6a64745450b12d421c1f9f02)
```

## Gathering facts (mechanics unchanged)

Pull architecture from `config.json` (`num_hidden_layers`, `hidden_size`, etc.), LoRA config
from `adapter_config.json`, YaRN from `config.json` `rope_scaling`. Use official tech reports
for any base-model reference numbers and **label them as base-model scores**, not this
fine-tune's.

## Execution

Iterate over models under the author with `HfApi.upload_file()` to update each `README.md`.
Preserve frontmatter, skip unchanged cards, verify after push. A worked reference set of lean
cards already lives on every `Nanthasit/*` repo (rewritten 2026-07-29) — match that style.

## Pitfalls

- Preserve YAML frontmatter — insert content only AFTER the closing `---`.
- Don't re-upload unchanged cards.
- Never emit hardcoded download counts or funnel sections (see rules 1 and 5).
- Spot-check 2–3 cards after a batch push to confirm changes landed and weren't reverted.
