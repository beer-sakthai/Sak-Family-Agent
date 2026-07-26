# HF Learnings: FineWeb Dataset Processing Pipeline

## 2026-07-25: FineWeb & FineWeb-Edu — Hugging Face's Web-Scale Dataset Processing Pipeline (Topic #379)

### Summary
Deep dive into the FineWeb dataset family — the complete pipeline for processing CommonCrawl web data at petabyte scale for LLM pretraining. Covers the 7-stage datatrove processing pipeline (URL filtering, text extraction, language filtering, quality heuristics, custom FineWeb filters, MinHash deduplication, PII anonymization), the educational quality classifier used for FineWeb-Edu (trained on LLama3-70B-Instruct synthetic annotations), FineWeb-2's 846-language multilingual expansion, and practical usage patterns via datatrove, huggingface_hub, and datasets library.

### Key Findings

#### 1. Dataset Scale
- **FineWeb**: 18.5T tokens (gpt2), 50.4 TB on disk, 96 CommonCrawl dumps from 2013–2025, 2,965 HF likes, 668K downloads
- **FineWeb-Edu**: 1.3T tokens of educational content, 5.4T in score-2 variant, 1,217 likes, 380K downloads
- **FineWeb-2**: 846 languages, 72K downloads, 846 likes
- All released under ODC-By 1.0 license (Open Data Commons Attribution)

#### 2. The 7-Stage Processing Pipeline (datatrove)

The pipeline runs per CommonCrawl dump and uses the `datatrove` library (3,223 GitHub stars):

**Stage 1: URL Filtering**
- Removes documents from malicious and NSFW websites
- Uses blocklist + subword detection
- Exclusion writer captures removed URLs for audit

**Stage 2: Text Extraction with Trafilatura**
- Extracts main page text from raw HTML WARC files
- Uses `favour_precision=True` config to minimize noise
- Handles the full CommonCrawl WARC format

**Stage 3: Language Filtering**
- FastText language classifier
- Threshold: English language score ≥ 0.65
- Non-English documents written to exclusion with language tag for potential reuse

**Stage 4: Quality Filtering (3 sub-layers)**
- **Gopher Repetition Filter**: Removes documents with excessive line/paragraph repetition
- **Gopher Quality Filter**: Heuristics from DeepMind's Gopher: min/max words per doc, word count stats
- **C4 Quality Filter**: Removes docs with terminal punctuation issues (except the `terminal_punct` rule which was too aggressive)
- **FineWeb Custom Filters**: Three custom heuristics:
  - List-like document removal (detects documents that are just markdown lists/bullets)
  - Repeated lines detection (duplicate line content)
  - Wrong line formatting (documents with broken paragraph structure)

**Stage 5: MinHash Deduplication**
- Per-dump deduplication (NOT cross-dump — ablations showed per-dump outperforms global)
- 5-gram tokenization
- 14 buckets × 8 hashes per bucket (112 total hash functions)
- SHA1 hash with 64-bit precision
- 4 sub-stages: signature computation → bucket assignment → cluster formation → filter application

**Stage 6: PII Anonymization**
- Email addresses → replaced with placeholders (`email@example.com` or `firstname.lastname@example.org`)
- Public IP addresses → replaced with inert IPs (e.g., `22.214.171.124`, non-responsive at creation time)
- Phone numbers deliberately NOT anonymized (high false positive rate from regex)

**Stage 7: Token Counting (Metadata)**
- Applies gpt2 tokenizer to count tokens per document
- Stored in `token_count` field

#### 3. FineWeb-Edu Educational Quality Classifier

FineWeb-Edu adds an 8th stage: **educational quality filtering via ML classifier**

**Annotation pipeline:**
- 500K FineWeb samples scored by **LLama3-70B-Instruct** on 0–5 educational quality scale
- Prompt uses additive scale from Yuan et al. (arXiv:2401.10020)
- Focus on grade-school/middle-school knowledge (not highly technical arXiv pages)
- Threshold ≥ 3 to retain educational content

**Classifier training:**
- Trained on LLama3-70B-Instruct annotations
- Binary classifier (≥3 = educational)
- Code released at https://github.com/huggingface/cosmopedia/tree/main/classification
- Model available at https://huggingface.co/HuggingFaceFW/fineweb-edu-classifier

**Why not jury-based?**
- Tested Mixtral-8x7B and Mixtral-8x22B as additional annotators
- Jury averaging shifted distribution right (lower precision)
- Single Llama3-70B annotator outperformed jury approach

**Performance:** FineWeb-Edu outperforms FineWeb on popular benchmarks despite being 14× smaller (1.3T vs 18.5T tokens)

#### 4. Architectural Decisions and Ablations

Key findings from ablation studies (1.8B models trained on 27B tokens each):

- **Per-dump dedup > global dedup**: Deduplicating each CommonCrawl dump individually outperforms global deduplication across all dumps
- **No ML-based toxicity filtering**: Deliberately avoided toxicity classifiers because they disproportionately filter content from specific dialects and social identities
- **Code content limitation**: Code is under-represented; FineWeb recommends supplementing with The Stack v2 for code capabilities
- **Recent dumps better**: For <550B token training, recommended dumps are CC-MAIN-2023-50, CC-MAIN-2024-10, CC-MAIN-2024-18

#### 5. Usage Patterns

**datatrove (streaming processing):**
```python
from datatrove.pipeline.readers import ParquetReader
reader = ParquetReader("hf://datasets/HuggingFaceFW/fineweb/data/CC-MAIN-2024-10", limit=1000)
for doc in reader():
    print(doc.text[:100])
```

**huggingface_hub (download):**
```python
from huggingface_hub import snapshot_download
folder = snapshot_download("HuggingFaceFW/fineweb", repo_type="dataset",
                           local_dir="./fineweb/",
                           allow_patterns="data/CC-MAIN-2023-50/*")
```

**datasets (streaming):**
```python
from datasets import load_dataset
fw = load_dataset("HuggingFaceFW/fineweb", name="sample-10BT", split="train", streaming=True)
```

#### 6. datatrove Execution Model

- Designed for **Slurm** cluster execution (HuggingFace's hopper-cpu partition)
- Supports 8000 parallel tasks per processing stage
- Each stage can depend on previous stages via `depends=` parameter
- MinHash dedup stages are split into 4 sequential sub-stages with dependencies
- S3-based intermediate storage between stages
- Supports CPU-only execution (no GPU needed)

#### 7. Future Evolution (v1.4.0+)

- January 2025: Fixed processing bug in 7 dumps (+400B tokens), C&D compliance removal
- June 2025: Added 6 new snapshots covering Jan–June 2025
- FineWeb-2 adds 846 languages but 72K downloads suggests community adoption is still growing

### Skill Created
`hf-fineweb-dataset-processing/` — SKILL.md (author: SakThai, license: MIT) + references/hf-learnings.md covering the complete FineWeb family processing pipeline, datatrove architecture, quality filtering methodology, educational classification system, and usage patterns.
