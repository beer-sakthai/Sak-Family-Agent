# Session Lessons — 2026-07-25

## CI Fixes
- saktan persona references deleted from tests, config, chat.py, personas/README.md
- config.SKILLS_DIR changed from root `skills/` to `personas/sakthai/skills/` (reorder PERSONAS_DIR before use)
- gitleaks: added `.curator_backups/` to allowlist in `.gitleaks.toml`
- After `git rm --cached skills/`, CI may not trigger on deletion-only commits — use `git commit --allow-empty` to force a run

## Dataset
- v7 enriched: 1,408 → 2,003 examples (500 tool-calling + 50 edge + 50 safety)
- Food-Penguin dataset: 200 → 648 (real orders from DB, error recovery, nested tool chains)
- Kaggle notebook created for FP training at `Nanthasit/food-penguin-v1/notebooks/`

## Model Improvements
- 1.5B model card updated with optimal prompt settings (temp=0.01, `<tools>` block)
- 8 old repos deleted from HF
- HF Auto Improve cron active every 5 min

## Communication
- Beer ok'd blanket approval for model improvements ("Allow process always if improve models")