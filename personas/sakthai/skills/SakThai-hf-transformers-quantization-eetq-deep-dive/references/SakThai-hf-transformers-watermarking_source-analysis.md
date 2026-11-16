# Source Code Analysis — Transformers Watermarking

Analyzed from `transformers` main branch (v5.14.0+). Watermarking lives in
`src/transformers/generation/`, NOT `src/transformers/watermarking/` (that path
does not exist as of July 2026).

## File Map

| File | Classes | Lines |
|------|---------|-------|
| `configuration_utils.py` | `WatermarkingConfig`, `SynthIDTextWatermarkingConfig`, `CompileConfig` | ~250 |
| `logits_process.py` | `WatermarkLogitsProcessor` (~180 lines), `SynthIDTextWatermarkLogitsProcessor` (~250 lines) | ~430 |
| `watermarking.py` | `WatermarkDetector`, `WatermarkDetectorOutput`, `BayesianDetectorConfig`, `BayesianDetectorWatermarkedLikelihood`, `BayesianDetectorModel`, `SynthIDTextWatermarkDetector` | ~460 |

## Key Architectural Details

### WatermarkLogitsProcessor internals (green/red token approach)

```python
# Fixed random table pre-computed at init (size 1,000,003)
self.fixed_table = torch.randperm(self.table_size, generator=self.rng, device=device)

# Seed derivation:
# "lefthash": seed = hash_key * last_token_value
# "selfhash": seed = hash_key * a * b (where a/b are from fixed_table + 1)
def set_seed(self, input_seq):
    if self.seeding_scheme == "selfhash":
        a = self.fixed_table[input_seq % self.table_size] + 1
        b = self.fixed_table[input_seq[-1] % self.table_size] + 1
        seed = (self.hash_key * a * b).min().item()
    else:
        seed = self.hash_key * input_seq[-1].item()
    self.rng.manual_seed(seed % (2**64 - 1))

# Greenlist: random permutation of vocab, take first N items
def _get_greenlist_ids(self, input_seq):
    self.set_seed(input_seq)
    vocab_permutation = torch.randperm(self.vocab_size, generator=self.rng)
    return vocab_permutation[:self.greenlist_size]

# Selfhash rejection sampling: check top-40 candidates
def _score_rejection_sampling(self, input_seq, scores):
    # Sort scores descending, check if each candidate is in greenlist
    # Return first candidate found in greenlist (up to 40 attempts)
```

### WatermarkDetector detection algorithm

```python
# Statistical test: z-score = (observed_green - expected_green) / std_dev
# expected_green = greenlist_ratio * total_tokens_scored
# std_dev = sqrt(total * p * (1-p))

# Detection: z_score > z_threshold (default 3.0) => watermarked
# confidence = 1 - p_value (p-value from z-score using approximation)
```

### SynthIDTextWatermarkLogitsProcessor internals

```python
# Pre-computes a random sampling table (size 64K, values 0 or 1)
self.sampling_table = torch.randint(low=0, high=2, size=(sampling_table_size,))

# G-values computed from n-gram context using hashing + sampling table
def compute_g_values(self, input_ids):
    # Hash n-gram keys, index into sampling_table to get binary g-values
    # Shape: [batch_size, seq_len - (ngram_len - 1), depth]

# Context repetition: tracks last N contexts to avoid re-watermarking
def compute_context_repetition_mask(self, input_ids):
    # Returns mask: 0 for repeated contexts (skip watermarking), 1 for new

# EOS mask: prevents <eos> token from being scored
def compute_eos_token_mask(self, input_ids, eos_token_id):
    # Returns mask: 0 for EOS positions, 1 otherwise
```

### SynthID Bayesian Detector

```python
# Posterior: P(w|g) = sigmoid(log_odds_prior + sum(log_odds_likelihood))
# Where:
#   - log_odds_prior = log(P(w)) - log(1 - P(w))
#   - log_odds_likelihood = sum over layers and positions of
#     log(P(g_tl|watermarked)) - log(P(g_tl|unwatermarked))
#   - P(g_tl|unwatermarked) = 0.5 (Bernoulli)
#   - P(g_tl|watermarked) = learned logistic regression model

# Watermarked likelihood model: sigmoid(delta * x + beta) for tournament g-values
# delta: [1, 1, depth, depth] parameter (tournament layer interactions)
# beta: [1, 1, depth] parameter (bias per layer)
```

## Training a SynthID Detector

The training script lives at `examples/synthid_text/detector_training.py` in the
transformers repo. Training data pairs:
- Watermarked text → compute g-values using `SynthIDTextWatermarkLogitsProcessor`
- Unwatermarked text → random g-values sampled from Bernoulli(0.5)

Reference project: https://github.com/huggingface/transformers-research-projects/tree/main/synthid_text

## Key Differences Between the Two Approaches

1. **Vocab splitting vs. tournament**: Kirchenbauer partitions vocab into two
   groups (green/red). SynthID uses a multi-layer tournament producing binary
   g-values at each position × depth layer.

2. **Deterministic vs. statistical detection**: Kirchenbauer uses z-score with
   configurable threshold (default 3.0). SynthID uses a trained Bayesian model
   that learns the distribution of g-values under watermark.

3. **Quality impact mechanism**: Kirchenbauer adds a constant bias to green
   tokens. SynthID uses tournament g-values that modify logits more subtly.

4. **Configuration sensitivity**: Both require EXACT same config for detection.
   Kirchenbauer also requires same device (CPU/GPU) for deterministic seeding.

## Pitfalls

- `WatermarkDetector` uses LRU caching (`@lru_cache(maxsize=128)`) on
  `_get_ngram_score` — bump `max_cache_size` for very long sequences
- SynthID `context_history_size` (default 1024) limits how far back context
  repetition is tracked — too small = watermark strength degrades on long texts
- Both watermarking methods require `do_sample=True` or at least non-greedy
  generation for SynthID watermark to be effective
- The `bos_token_id` strip logic in `WatermarkDetector.__call__` assumes if
  first item starts with BOS, ALL batch items do — can miscount on padded batches
