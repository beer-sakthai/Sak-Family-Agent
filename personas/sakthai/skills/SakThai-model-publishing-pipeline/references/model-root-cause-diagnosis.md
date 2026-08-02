# Model Root Cause Diagnosis

When a fine-tuned model underperforms, diagnose BEFORE retraining.

## Protocol

1. Download the BASE model (same architecture, similar quantization)
2. Run identical tests on BOTH models
3. Compare results side-by-side
4. If both fail the same way → it's a base model limitation, not fine-tuning
5. If only fine-tuned fails → training data or training process issue

## 0.5B Case Study (2026-07-25)

| Test | Base Qwen2.5-0.5B | SakThai 0.5B | Root Cause |
|------|:-----------------:|:------------:|:-----------:|
| Weather in Tokyo | Refused | Refused | Base model limitation |
| 2+2 | "4" ✅ | "4" ✅ | Fine-tuning preserved this |
| Romeo & Juliet | "Shakespeare" ✅ | "Shakespeare" ✅ | Fine-tuning preserved this |
| Calculate 15+27 | "42" ✅ | "42" ✅ | Fine-tuning preserved this |
| Time London | Refused | Refused | Base model limitation |

Verdict: 0.5B tool-calling failure is inherited from base model. Our fine-tuning preserved existing Q&A capability but cannot add tool-calling behavior that the base never had.

## What This Means

- A model cannot do what its base was never trained for
- 0.5B class models lack function calling capability at base level
- QLoRA with 1,400 examples is insufficient to overcome this
- Fix would require: full fine-tune (not QLoRA), 2,000+ examples, higher rank (r=32+)