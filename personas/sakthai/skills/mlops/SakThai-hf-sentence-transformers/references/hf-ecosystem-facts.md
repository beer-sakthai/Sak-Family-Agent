# Sentence-Transformers Ecosystem Facts (July 2026)

Gathered via direct API calls to PyPI, GitHub, and HF Hub on 2026-07-23.

## PyPI Package

| Field | Value |
|-------|-------|
| Latest version | 5.6.1 (released 2026-07-23) |
| Summary | "Embeddings, Retrieval, and Reranking" |
| Python requires | >=3.10 |
| Homepage | https://www.SBERT.net |
| Repository | https://github.com/huggingface/sentence-transformers |
| Author | (transferred to HuggingFace org) |
| Extras | `[image]`, `[audio]`, `[video]`, `[train]`, `[onnx]`, `[openvino]`, `[dev]` |

Recent releases: 5.6.0 (Jun 16), 5.5.1 (May 20), 5.5.0 (May 12), 5.4.1 (Apr 14).

## GitHub Repository

| Field | Value |
|-------|-------|
| Stars | 18,936 |
| Forks | 2,835 |
| Open issues | 1,297 |
| Description | "State-of-the-Art Embeddings, Retrieval, and Reranking" |
| Language | Python |
| Last push | 2026-07-23 (same day as latest PyPI release) |

## Top HF Hub Models (by downloads)

| Model ID | Pipeline | Downloads | Likes |
|----------|----------|-----------|-------|
| `sentence-transformers/all-MiniLM-L6-v2` | sentence-similarity | 254,761,864 | 5,112 |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | sentence-similarity | 51,311,096 | 1,329 |
| `sentence-transformers/all-mpnet-base-v2` | sentence-similarity | 29,439,196 | 1,334 |
| `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | sentence-similarity | 11,612,322 | 479 |
| `sentence-transformers/all-MiniLM-L12-v2` | sentence-similarity | 3,159,973 | 323 |
| `sentence-transformers/paraphrase-MiniLM-L6-v2` | sentence-similarity | 2,357,252 | 149 |
| `sentence-transformers/all-distilroberta-v1` | sentence-similarity | 2,249,229 | 43 |
| `sentence-transformers/multi-qa-mpnet-base-dot-v1` | sentence-similarity | 2,164,085 | 193 |
| `sentence-transformers/paraphrase-MiniLM-L3-v2` | sentence-similarity | 1,793,779 | 30 |
| `sentence-transformers/distiluse-base-multilingual-cased-v2` | sentence-similarity | 1,732,891 | 209 |

Total models on Hub tagged `library:sentence-transformers`: **15,000+**

## Research Methodology Used

This data was collected by querying three public APIs directly via Python `urllib`:

- **PyPI**: `https://pypi.org/pypi/sentence-transformers/json` — package metadata and release history
- **GitHub API**: `https://api.github.com/repos/huggingface/sentence-transformers` — repo stats
- **HF Hub API**: `https://huggingface.co/api/models?author=sentence-transformers&sort=downloads&direction=-1` — model rankings

This direct-API approach works when Composio web search tools are unavailable or blocked, and gives structured JSON that's easier to parse than scraped HTML.
