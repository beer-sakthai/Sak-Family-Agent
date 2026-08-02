# Cycle-Based Training Plan Template

When Beer says "plan train model," present using the full 6-stage Growth Cycle.

## Required upfront elements

Every plan MUST include:
- **Cost**: explicitly state $0 or actual cost
- **Success probability**: e.g. "~90% for 1.5B on Kaggle"
- **GPU source**: Kaggle, Colab, or HF Jobs (only free tiers)
- **Duration estimate**: how long training takes
- **Output repos**: what will be created on HF

## Template

```
## 🌙 DREAM — Vision
[What model we're building and why]

## 🌅 HOPE — Options
| Option | GPU | Cost | Time | Success |
|--------|-----|------|------|---------|
| 1.5B on Kaggle (recommended) | T4 | $0 | ~20 min | ~90% |
| 7B on Kaggle | T4 | $0 | ~90 min | ~75% |

## 🏗️ CARE — Build Plan
Phase 1: Pre-Flight (HF asset audit)
Phase 2: Dataset prep
Phase 3: Train on Kaggle/Colab
Phase 4: Post-process (merge, quantize, benchmark)

## 🎉 JOY — Deliverable
[What the user gets — model repos, reports]

## 🔎 TRUST — Verification
Checklist: loads, tool-calls, direct-answer, zero-cost-aware

## 🌱 GROWTH — Lesson Capture
Compare benchmarks, capture what worked
```

## Beer's rules
- Zero-cost only — never propose paid GPU
- Kaggle over Colab (more reliable)
- Success % + cost upfront before committing
- Full cycle, no skipping Dream/Hope stages
