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

### Next
- Train Food-Penguin model on Kaggle T4 GPU
- Promote 0-dl models (Vision, TTS, Multilingual)
- Richer analytics for Food-Penguin dashboard
