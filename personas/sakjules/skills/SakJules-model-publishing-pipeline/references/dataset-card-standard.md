# Dataset Card Standard (SOP) — `Nanthasit/*` datasets

The operating procedure for writing or updating any `Nanthasit/*` **dataset** card.
It layers Hugging Face's official dataset-card spec on top of the lean house style in
[`model-card-enrichment-workflow.md`](model-card-enrichment-workflow.md). Where the two
disagree, **the HF spec wins** — it drives Hub search, filtering, and the dataset viewer.

> Sources: <https://huggingface.co/docs/hub/datasets-cards> and the field spec at
> <https://github.com/huggingface/hub-docs/blob/main/datasetcard.md>. Adopted 2026-07-30.

## 1. YAML frontmatter — the part that actually does work

The body is for humans; the frontmatter is what the Hub *indexes*. Get it right first.

**Required on every dataset:**

| Key | Value | Notes |
|---|---|---|
| `license` | e.g. `apache-2.0` | A bare string. Use a valid HF identifier. |
| `language` | list of ISO 639-1 | **List every language actually present**, not just the intended one. |
| `pretty_name` | string | Shown as the dataset title. |
| `size_categories` | one enum value | Must match the real row count (see §2). |
| `task_categories` | list | `text-generation` for all SakThai tool-calling sets. |
| `tags` | list | Keep `sakthai`, `house-of-sak`, plus content tags. |

**Strongly recommended** (all SakThai sets should carry them):
`task_ids`, `annotations_creators`, `language_creators`, `multilinguality`, `source_datasets`.

`task_ids` is a **closed enum and there is no function-calling or api-calling value in it.**
`other-api-calling` / `other-function-calling` are *not* valid — the Hub rejects them with
"not in the official list" (they were on `food-penguin-v1`, which is why they spread). Use
**`dialogue-modeling`** for the multi-turn tool-calling sets, and express the tool-calling
nature through `tags` instead, which is free-form.

`size_categories` is a **closed enum** — only these values are legal:
`n<1K`, `1K<n<10K`, `10K<n<100K`, `100K<n<1M`, `1M<n<10M`, `10M<n<100M`, `100M<n<1B`, `n>1B`.

`annotations_creators` / `language_creators` are also closed enums:
`crowdsourced`, `found`, `expert-generated`, `machine-generated`, `other`.

### Never put model-card keys on a dataset

`pipeline_tag`, `base_model`, `library_name`, `widget`, `model-index`, and `datasets`
are **model**-card fields. On a dataset repo they are invalid and silently do nothing.
(`sakthai-combined-v7` carried `pipeline_tag` and `datasets` until 2026-07-30.)

### Never hand-edit `configs` or `dataset_info`

These drive the dataset viewer and the parquet conversion. A wrong `data_files` path
breaks `load_dataset()` for every downstream user. Let the Hub generate them, or change
them only alongside a verified `load_dataset()` round trip.

## 2. Ground every number in the data

Do not copy row counts between cards or trust an older card. Read them:

```bash
# authoritative row count + split sizes, no download
curl -s "https://datasets-server.huggingface.co/size?dataset=Nanthasit/REPO" \
  | python3 -c "import json,sys; d=json.load(sys.stdin)['size']; print(d['dataset'])"
```

`language` has the same rule. Sample the rows and look before you declare a language:

```bash
# does this dataset actually contain Thai?
curl -s "https://datasets-server.huggingface.co/rows?dataset=Nanthasit/REPO&config=default&split=train&offset=0&length=100" \
  | grep -cP '[\x{0E00}-\x{0E7F}]'
```

Measured 2026-07-30: `sakthai-combined-v7` and `sakthai-bench-v2` are **5% Thai**;
both had declared `language: [en]` only.

## 3. Section order (body)

Follow HF's official template, trimmed to what we can honestly fill:

1. `# <h1>` + one-line tagline, then the badge row
2. **Dataset Description** — what it is, in 2–3 sentences
3. **Uses** — Direct Use and, where a set is easy to misuse, Out-of-Scope Use
4. **Dataset Structure** — fields, splits, composition table
5. **Dataset Creation** — curation rationale and how the data was produced
6. **Bias, Risks, and Limitations** — the honest caveats section
7. **Trained models / Related assets** — one table, links only
8. **Citation** (optional) · **License**

A benchmark card additionally needs **how it is scored** and **what must be excluded from
training** — see `sakthai-bench-v2`, whose `train_exclude_fingerprints.json` contract is
what keeps the benchmark valid.

## 4. Lean rules inherited from the model-card standard

- **One downloads badge, dynamic, never hardcoded.** For datasets:
  ```html
  <img src="https://img.shields.io/badge/dynamic/json?url=https%3A//huggingface.co/api/datasets/Nanthasit/REPO&query=%24.downloads&label=downloads&color=blue&cacheSeconds=3600" alt="Downloads"/>
  ```
  Not `shields.io/endpoint` — that renders `invalid properties: label, message`.
- **No funnel sections** — no "Growing the Ecosystem", "Low-Download Gems",
  "Support the Project", no zero-download pleas.
- **One family/related table**, size + role, never download counts.
- **Story lives on the profile card only**; link to it.
- **Preserve frontmatter you are not deliberately changing**, byte for byte.

## 5. Verify after every push

The promotion agent rewrites `Nanthasit/*` cards; a push is not done until re-read.

```bash
# re-fetch and diff what you believe you pushed
curl -s "https://huggingface.co/datasets/Nanthasit/REPO/raw/main/README.md" | diff - local.md
```

Check the dataset page still shows a working viewer afterwards — a broken `configs`
block shows an error banner instead of rows.
