---
name: SakThai-hf-tokenizers-training
author: SakThai
license: MIT
title: HF Tokenizers Training Custom Tokenizers from Scratch
description: "Step-by-step guide to training BPE, WordPiece, and Unigram tokenizers using the Hugging Face tokenizers library. Covers the full pipeline: model, pre-tokenizer, trainer, post-processor, decoder, and integration with transformers."
version: 1.0.0
tags: [tokenizers, bpe, wordpiece, unigram, training, nlp, huggingface]
---

# HF Tokenizers - Training Custom Tokenizers from Scratch

## Overview

The Hugging Face `tokenizers` library (Rust-backed, Python API) provides the fastest tokenizer training available. Training a full BPE tokenizer on 500MB+ of text takes seconds.

### The Tokenization Pipeline

A tokenizer is composed of **4 sequential stages**:

```
Input Text -> Pre-tokenizer -> Model -> Post-processor -> Decoder -> Output
```

Each stage is configurable. You can mix and match components.

---

## 1. Model Types

| Model | Algorithm | Used By | Best For |
|-------|-----------|---------|----------|
| `BPE` | Byte-Pair Encoding | GPT-2, RoBERTa | General subword, byte-level fallback |
| `WordPiece` | Greedy longest-match | BERT | Morphologically rich languages |
| `Unigram` | Probabilistic subword | XLNet, T5, multilingual | Small vocabularies, balanced coverage |
| `WordLevel` | Simple lookup | Baseline | Fixed vocab, no UNK handling built-in |

### Import and Instantiate

```python
from tokenizers import Tokenizer
from tokenizers.models import BPE, WordPiece, Unigram, WordLevel

# BPE (most common for subword)
tokenizer = Tokenizer(BPE(unk_token="[UNK]"))

# WordPiece (BERT-style)
tokenizer = Tokenizer(WordPiece(unk_token="[UNK]"))

# Unigram (SentencePiece-style)
tokenizer = Tokenizer(Unigram())
```

### BPE Constructor Parameters

```python
BPE(
    vocab=None,                     # Dict[str, int] - pre-built vocab
    merges=None,                    # List[Tuple[str, str]] - pre-built merges
    cache_capacity=None,            # Cache size for speed (default: 10K words)
    dropout=None,                   # BPE dropout (0.0-1.0) for regularization
    unk_token=None,                 # Unknown token string
    continuing_subword_prefix=None, # e.g. "##" for WordPiece compatibility
    end_of_word_suffix=None,        # e.g. "</w>"
    fuse_unk=False,                 # Merge consecutive UNK tokens
    byte_fallback=False,            # spaCy byte-fallback trick
)
```

---

## 2. Pre-tokenizers

Pre-tokenizers split raw text into initial word boundaries before the model applies subword splitting.

```python
from tokenizers.pre_tokenizers import (
    Whitespace,        # Split on whitespace
    WhitespaceSplit,   # Split on whitespace (different algo)
    BertPreTokenizer,  # BERT's original pre-tokenizer
    ByteLevel,         # GPT-2 style byte-level
    Punctuation,       # Split on punctuation
    Metaspace,         # Replace spaces with special char
    Digits,            # Split digits
    Sequence,          # Chain multiple pre-tokenizers
)
```

**Common patterns:**

```python
# BPE default: ByteLevel (GPT-2 style)
from tokenizers.pre_tokenizers import ByteLevel
tokenizer.pre_tokenizer = ByteLevel()

# Word-based pre-tokenizer (for corpus with natural word boundaries)
from tokenizers.pre_tokenizers import Whitespace
tokenizer.pre_tokenizer = Whitespace()

# BERT-style
from tokenizers.pre_tokenizers import BertPreTokenizer
tokenizer.pre_tokenizer = BertPreTokenizer()

# Chain pre-tokenizers
from tokenizers.pre_tokenizers import Sequence, Whitespace, Punctuation
tokenizer.pre_tokenizer = Sequence([Whitespace(), Punctuation()])
```

---

## 3. Trainers

### BpeTrainer

```python
from tokenizers.trainers import BpeTrainer

trainer = BpeTrainer(
    vocab_size=30000,
    min_frequency=2,
    special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"],
    show_progress=True,
    limit_alphabet=None,              # Max distinct characters in alphabet
    initial_alphabet=None,            # Pre-seeded alphabet characters
    continuing_subword_prefix=None,   # e.g. "##"
    end_of_word_suffix=None,          # e.g. "</w>"
    max_token_length=None,            # Clamp token length (e.g., 15)
)
```

### WordPieceTrainer

```python
from tokenizers.trainers import WordPieceTrainer

trainer = WordPieceTrainer(
    vocab_size=30000,
    min_frequency=2,
    special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"],
    show_progress=True,
    limit_alphabet=None,
    continuing_subword_prefix="##",   # BERT default
)
```

### UnigramTrainer

```python
from tokenizers.trainers import UnigramTrainer

trainer = UnigramTrainer(
    vocab_size=8000,
    special_tokens=["<unk>", "<s>", "</s>"],
    unk_token="<unk>",
    shrinking_factor=0.75,            # Vocab pruning factor per iteration
    max_piece_length=16,
    show_progress=True,
)
```

### Special Tokens - ORDER MATTERS

The index in the `special_tokens` list determines the token ID. Always put them in the order you want them assigned:

```python
# [UNK]=0, [CLS]=1, [SEP]=2, [PAD]=3, [MASK]=4
special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"]
```

After training, check token IDs with:
```python
tokenizer.token_to_id("[CLS]")  # 1
```

---

## 4. Training the Tokenizer

### From Files (most common)

```python
files = ["data/corpus1.txt", "data/corpus2.txt"]
tokenizer.train(files, trainer)
```

### From Iterator (any iterable of strings)

```python
def get_training_corpus():
    for i in range(1000):
        yield f"Sample text number {i}"

tokenizer.train_from_iterator(get_training_corpus(), trainer)
```

### From a Dataset (using HF datasets library)

```python
from datasets import load_dataset
dataset = load_dataset("wikitext", "wikitext-103-raw", split="train")

def batch_iterator(batch_size=1000):
    for i in range(0, len(dataset), batch_size):
        yield dataset[i : i + batch_size]["text"]

tokenizer.train_from_iterator(batch_iterator(), trainer, length=len(dataset))
```

---

## 5. Post-processing

Add special tokens automatically during encoding with `TemplateProcessing`:

```python
from tokenizers.processors import TemplateProcessing

tokenizer.post_processor = TemplateProcessing(
    single="[CLS] $A [SEP]",
    pair="[CLS] $A [SEP] $B:1 [SEP]:1",
    special_tokens=[
        ("[CLS]", tokenizer.token_to_id("[CLS]")),
        ("[SEP]", tokenizer.token_to_id("[SEP]")),
    ],
)
```

The `:1` suffix sets the type_id (segment) for tokens - defaults to 0 for the first sentence.

---

## 6. Decoder

Decoders convert token IDs back to text. Match the decoder to your pre-tokenizer:

```python
from tokenizers.decoders import ByteLevel, WordPiece, Metaspace, BPEDecoder

tokenizer.decoder = ByteLevel()              # For ByteLevel pre-tokenizer
tokenizer.decoder = WordPiece(prefix="##")   # For WordPiece model
tokenizer.decoder = Metaspace()              # For Metaspace pre-tokenizer
```

---

## 7. Complete End-to-End Example

```python
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.pre_tokenizers import ByteLevel
from tokenizers.trainers import BpeTrainer
from tokenizers.processors import TemplateProcessing
from tokenizers.decoders import ByteLevel as ByteLevelDecoder

# 1. Initialize model
tokenizer = Tokenizer(BPE(unk_token="[UNK]"))

# 2. Set pre-tokenizer
tokenizer.pre_tokenizer = ByteLevel(add_prefix_space=True)

# 3. Configure trainer
trainer = BpeTrainer(
    vocab_size=32000,
    min_frequency=2,
    special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"],
    show_progress=True,
)

# 4. Train
files = ["corpus.txt"]
tokenizer.train(files, trainer)

# 5. Set post-processor
tokenizer.post_processor = TemplateProcessing(
    single="[CLS] $A [SEP]",
    pair="[CLS] $A [SEP] $B:1 [SEP]:1",
    special_tokens=[
        ("[CLS]", tokenizer.token_to_id("[CLS]")),
        ("[SEP]", tokenizer.token_to_id("[SEP]")),
    ],
)

# 6. Set decoder
tokenizer.decoder = ByteLevelDecoder()

# 7. Save
tokenizer.save("my-tokenizer.json")

# 8. Test
output = tokenizer.encode("Hello, world!")
print(output.tokens)
print(output.ids)
print(output.offsets)

# 9. Decode back
print(tokenizer.decode(output.ids))
```

---

## 8. Integrating with transformers

### Method A: Train with tokenizers, wrap with transformers (recommended)

```python
from transformers import PreTrainedTokenizerFast

fast_tokenizer = PreTrainedTokenizerFast(
    tokenizer_object=tokenizer,
    unk_token="[UNK]",
    pad_token="[PAD]",
    cls_token="[CLS]",
    sep_token="[SEP]",
    mask_token="[MASK]",
)

fast_tokenizer.save_pretrained("my-custom-tokenizer")

from transformers import AutoTokenizer
loaded = AutoTokenizer.from_pretrained("my-custom-tokenizer")
```

### Method B: Train from scratch with transformers trainers

```python
from transformers import BertTokenizer

old_tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
texts = ["sample text"] * 1000

new_tokenizer = old_tokenizer.train_new_from_iterator(texts, vocab_size=25000)
new_tokenizer.save_pretrained("my-bert-tokenizer")
```

---

## 9. Adding Tokens Post-Training

```python
tokenizer.add_tokens(["<new_token>"])
tokenizer.add_tokens(["<token1>", "<token2>"])
tokenizer.add_special_tokens({"additional_special_tokens": ["<SPECIAL>"]})

# CRITICAL: Resize model embeddings if adding to a transformers model
# model.resize_token_embeddings(len(tokenizer))
```

---

## 10. Key Pitfalls and Best Practices

| Pitfall | Solution |
|---------|----------|
| Training too small a vocab -> high UNK rate | Set `vocab_size` covering 98%+ of tokens in corpus |
| Wrong special tokens order -> model mismatch | Special token ID assignment is positional |
| Pre-tokenizer/decoder mismatch | Always use the corresponding decoder for your pre-tokenizer |
| Not setting `unk_token` | BPE defaults to no UNK handling; always set it |
| Training on unnormalized text | Normalize text first (lowercase, NFC normalize) |
| Forgetting pad_token | Padding is not automatic; explicitly set it |
| Not resizing embedding layer after adding tokens | Call model.resize_token_embeddings() |

### Normalization Checklist

- Lowercase/casefold (if case-insensitive)
- Unicode NFC normalization
- Strip HTML tags
- Remove/replace control characters
- Collapse multiple whitespace

---

## 11. Performance Tips

- The tokenizers library is Rust-based: training is 10-100x faster than pure Python
- Training 500MB of text with BPE takes about 10-15 seconds on a modern CPU
- Use `train_from_iterator()` to train without writing files to disk
- BPE cache defaults to 10K words; increasing to 50K+ speeds inference
- Batch encoding with `tokenizer.encode_batch()` is significantly faster

## References

- [HF Tokenizers Quicktour](https://huggingface.co/docs/tokenizers/quicktour)
- [HF Tokenizers API - Trainers](https://huggingface.co/docs/tokenizers/main/en/api/trainers)
- [HF Tokenizers API - Models](https://huggingface.co/docs/tokenizers/main/en/api/models)
- [HF NLP Course - Tokenizers Chapter](https://huggingface.co/learn/nlp-course/chapter2/4)
- [GitHub: huggingface/tokenizers](https://github.com/huggingface/tokenizers)
- `references/quick-reference.md` — condensed recipes for BPE, WordPiece, Unigram, and dataset-based training
