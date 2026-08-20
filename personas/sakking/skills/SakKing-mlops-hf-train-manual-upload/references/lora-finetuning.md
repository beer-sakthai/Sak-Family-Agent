# LoRA Fine-Tuning Quick Reference

## Parameters
- `r=8`: Rank of low-rank matrices
- `lora_alpha=16`: Scaling factor (alpha/r = 2)
- `target_modules=["q_proj", "v_proj"]`: Apply to attention layers
- `lora_dropout=0.05`: Prevents overfitting
- `bias="none"`: Do not train bias terms

## Workflow
1. Load base model: `AutoModelForCausalLM.from_pretrained("base-model")`
2. Apply config: `get_peft_model(model, config)`
3. Train with `Trainer` or custom loop
4. Save: `model.save_pretrained("lora_adapter")`
5. Push: `api.upload_folder(..., repo_type="model")`

## Compatibility
- Works with: LLaMA, Mistral, Qwen, Phi-3, Gemma
- Requires: `peft>=0.10.0`, `transformers>=4.38.0`

> Always test adapter on 5 samples before deployment.