# PEFT Method Variants, Prompt Tuning & Architecture Specs

| Config Class | Method | Description |
|---|---|---|
| `LoraConfig` | LoRA | Low-Rank Adaptation — most popular, broadly supported |
| `LoraConfig(use_dora=True)` | DoRA | Weight-Decomposed LoRA — typically better than vanilla LoRA |
| `PromptTuningConfig` | Prompt Tuning | Learn soft prompt tokens |
| `PrefixTuningConfig` | Prefix Tuning | Learn prefix activations for each transformer layer |
| `P tuningConfig` | P-Tuning | Learn continuous prompts with an LSTM/MLP encoder |
| `IA3Config` | (IA)³ | Learn rescaling vectors for attention/FF layers |
| `AdaLoraConfig` | AdaLoRA | Adaptive budget allocation — automatically prunes unimportant LoRA ranks |
| `LoHaConfig` | LoHa | Low-Rank Hadamard product — more expressive than LoRA |
| `BOFTConfig` | BOFT | Butterfly Orthogonal Fine-Tuning — orthogonal rotations |
| `LoraConfig(init_lora_weights="pissa")` | PiSSA | Principal Singular Values and Singular Vectors Adaptation — better initialization |

## Pitfalls

- **Module name mismatches**: Not all models use the same names (e.g., LLaMA uses `q_proj`, GPT-2 uses `q_proj`, BERT uses `query`). Always inspect the model first.
- **Multi-adapter and `merge_and_unload`**: You must merge the active adapter before calling `merge_and_unload`. Multi-adapter merging is not supported — you get the current active adapter's weights.
- **QLoRA requires `device_map="auto"`**: Without auto device mapping, 4-bit model loading may fail or produce unexpected behavior.
- **Adapter config must match training config**: When loading for inference, the adapter config specifies `r`, `alpha`, and `target_modules`. The base model must be compatible.
- **Inference-only loading with `AutoPeftModel`**: If the repo only has adapter weights (not the full base model), `AutoPeftModel` won't work; use `PeftModel.from_pretrained(base_model, adapter_path)` instead.
- **`push_to_hub` on PEFT model**: Pushes only the adapter. The base model must be loaded separately on the other end. This is by design (adapter is tiny).
- **PEFT v0.20+ changes**: In recent versions, `PeftModelForCausalLM` is deprecated in favor of `AutoPeftModelForCausalLM`. Use the Auto class for inference.
- **Gradient checkpointing**: When training large models with PEFT, enable `gradient_checkpointing=True` in `TrainingArguments` to reduce memory.

## Verification

```python
# Check trainable parameter count
peft_model.print_trainable_parameters()

# Verify adapter is loaded by checking active adapter name
print(f"Active adapter: {peft_model.active_adapter}")

# Test inference
inputs = tokenizer("A quick brown fox", return_tensors="pt")
outputs = peft_model.generate(**inputs, max_new_tokens=20)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## Related Skills

- `huggingface-hub` — for uploading/sharing adapters via CLI
- `model-publishing-pipeline` — end-to-end training → publish pipeline including LoRA
- `hf-smol-course` — SFT, DPO, GRPO with TRL

## References

- `references/model-merging-docs.md` — Official HF doc excerpts for TIES/DARE/Linear merging, paper links, API reference, and code patterns
