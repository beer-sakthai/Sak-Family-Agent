# Learning Journal

## 2026-07-25

### Models
- 1.5B tool-calling verified: works with `<tools>` block in prompt
- 0.5B too small for tool-calling (base model limit)
- Coder 1.5B: 5/5 coding verified
- Dataset enriched: v7 = 2,003 examples (was 1,408)
- Food-Penguin dataset: 200 examples created

### Infrastructure
- Training on CPU not viable (OOM at step 14/150)
- Kaggle is the path for GPU training
- CI fixed: saktan references removed from tests
- Gitleaks fixed: .curator_backups/ allowlisted

### Improvements Made
- 12 model cards updated with family links
- 8 old repos deleted from HF
- RAG for Food-Penguin advisor added
- Auto-improve cron active every 5 min

## 2026-07-26

### Ecosystem Improvement (Cron run)

**Target**: `sakthai-vision-7b` (0 downloads, weak card)
**Improvement**: Full rewrite of README.md
- Previously: 27 lines, empty Usage section, no code examples
- Now: 90 lines with structured tables, 4 usage methods (llama.cpp, Python, Ollama, LM Studio), use-cases table, file structure, family cross-links
- Verified: `hf upload` commit `fa791ee` — card live at HF

### Current ecosystem state
| Category | Count |
|----------|-------|
| Models | 14 (7 public with weights, 2 private, 5 lightweight) |
| Datasets | 4 |
| Spaces | 2 |
| Collection | 1 (sakthai-model-family) |

### Downloads snapshot
| Model | Downloads |
|-------|-----------|
| 1.5B-merged | 942 |
| 7B-merged | 534 |
| Coder 1.5B | 15 |
| Vision 7B | **0** (card improved this run) |
| Embedding Multilingual | 0 |
| TTS Model | 0 |

### Next
- Train Food-Penguin model on Kaggle T4 GPU
- Promote embedding-multilingual card next (also 0 dl, 25-line thin card)
- Improve TTS card if needed (already 184 lines, decent)
- Richer analytics for Food-Penguin dashboard
