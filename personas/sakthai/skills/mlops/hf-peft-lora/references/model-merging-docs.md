# PEFT Model Merging — Official Documentation Reference

Source: https://huggingface.co/docs/peft/en/developer_guides/model_merging
Fetched: 2026-07-23

## Papers

| Method | Paper | URL |
|--------|-------|-----|
| TIES-Merging | "TIES-Merging: Resolving Interference When Merging Models" (Yadav et al., 2023) | https://hf.co/papers/2306.01708 |
| DARE | "Language Models are Super Mario: Absorbing Abilities from Homologous Models as a Free Lunch" (Yu et al., 2023) | https://hf.co/papers/2311.03099 |

## API Reference — `add_weighted_adapter()`

Defined on `LoraModel` (also available on `IA3Model` without `combination_type`):

```python
model.add_weighted_adapter(
    adapters: List[str],          # names of loaded adapters
    weights: List[float],         # weights per adapter (>1.0 typically better)
    adapter_name: str,            # name for the new merged adapter
    combination_type: str | None, # None | "linear" | "ties" | "dare_linear" | "dare_ties" | "svd" | "cat"
    density: float | None,        # fraction of params to keep (0.0–1.0), required for ties/dare
    svd_rank: int | None,         # rank for SVD combination
)
```

Returns nothing. Creates a new adapter entry in `model.peft_config`.

## Supported `combination_type` Values

| Value | When added | Requires `density` | Notes |
|-------|-----------|-------------------|-------|
| `None` (default) | Always | No | Simple weighted average per parameter |
| `"linear"` | PEFT v0.14+ | No | Weighted average; same as default but explicit |
| `"ties"` | PEFT v0.14+ | Yes (recommended 0.2–0.5) | Trim → Elect → Merge |
| `"dare_linear"` | PEFT v0.14+ | Yes | DARE drop + rescale + linear average |
| `"dare_ties"` | PEFT v0.14+ | Yes | DARE drop + rescale + TIES merging |
| `"svd"` | PEFT v0.14+ | No | SVD-based; use `svd_rank` param |
| `"cat"` | PEFT v0.14+ | No | Concatenate along adapter dim |

## Key Code Patterns from Official Docs

### 1. Base: Load adapters before merging

```python
from peft import PeftModel

model = PeftModel.from_pretrained(base_model, "repo/adapter_1", adapter_name="task_a")
model.load_adapter("repo/adapter_2", adapter_name="task_b")
model.load_adapter("repo/adapter_3", adapter_name="task_c")
```

### 2. Handle vocab size mismatches (important when merging full models)

```python
model.config.vocab_size = 32005
model.resize_token_embeddings(32005)
```

### 3. Official TIES merge snippet from HF docs

```python
adapters = ["norobots", "adcopy", "sql"]
weights = [2.0, 1.0, 1.0]
adapter_name = "merge"
density = 0.2
model.add_weighted_adapter(adapters, weights, adapter_name, combination_type="ties", density=density)
model.set_adapter("merge")
```

### 4. IA3 linear merge (weights should sum to 1.0)

```python
adapters = ["adapter1", "adapter2", "adapter3"]
weights = [0.4, 0.3, 0.3]
model.add_weighted_adapter(adapters, weights, "merge")
model.set_adapter("merge")
```

## Key Differences from `merge_and_unload()`

| Aspect | `merge_and_unload()` | `add_weighted_adapter()` |
|--------|---------------------|--------------------------|
| What it does | Fuses adapter into base weights | Creates a new combined adapter |
| Result | Full-rank model (no PEFT wrapper) | PEFT adapter (stays wrappered) |
| Multi-adapter? | No (only active adapter) | Yes (TIES/DARE/Linear/SVD) |
| Can chain? | Terminal step | Can be followed by `merge_and_unload()` |
| Quantized models? | Cannot unload 4-bit | Works, but stays as adapter |

## Pitfalls from Official Docs

1. **Special token index conflicts**: Different fine-tuned models may have added special tokens at the same embedding position. Resize embeddings before merging.
2. **Weight scale**: Values > 1.0 preserve correct scale better. Start all at 1.0.
3. **Density tuning**: 0.2 keeps 20% of params (aggressive). Start at 0.5.
4. **PEFT version**: Requires v0.14.0+. Check with `import peft; print(peft.__version__)`.
