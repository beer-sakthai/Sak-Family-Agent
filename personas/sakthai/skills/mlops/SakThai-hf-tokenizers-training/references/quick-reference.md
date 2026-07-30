# HF Tokenizers — Quick Reference

Quick-reference patterns for the four most common tokenizer training recipes.

## Recipe 1: BPE (GPT-2 / RoBERTa style)

```python
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.pre_tokenizers import ByteLevel
from tokenizers.trainers import BpeTrainer
from tokenizers.processors import TemplateProcessing
from tokenizers.decoders import ByteLevel as ByteLevelDecoder

tokenizer = Tokenizer(BPE(unk_token="[UNK]"))
tokenizer.pre_tokenizer = ByteLevel(add_prefix_space=True)

trainer = BpeTrainer(
    vocab_size=32000,
    min_frequency=2,
    special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"],
)
tokenizer.train(["corpus.txt"], trainer)

tokenizer.post_processor = TemplateProcessing(
    single="[CLS] $A [SEP]",
    pair="[CLS] $A [SEP] $B:1 [SEP]:1",
    special_tokens=[("[CLS]", 1), ("[SEP]", 2)],
)
tokenizer.decoder = ByteLevelDecoder()
tokenizer.save("bpe-tokenizer.json")
```

## Recipe 2: WordPiece (BERT style)

```python
from tokenizers import Tokenizer
from tokenizers.models import WordPiece
from tokenizers.pre_tokenizers import BertPreTokenizer
from tokenizers.trainers import WordPieceTrainer
from tokenizers.decoders import WordPiece as WordPieceDecoder

tokenizer = Tokenizer(WordPiece(unk_token="[UNK]"))
tokenizer.pre_tokenizer = BertPreTokenizer()

trainer = WordPieceTrainer(
    vocab_size=30000,
    min_frequency=2,
    continuing_subword_prefix="##",
    special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"],
)
tokenizer.train(["corpus.txt"], trainer)

tokenizer.decoder = WordPieceDecoder()
tokenizer.save("wordpiece-tokenizer.json")
```

## Recipe 3: Unigram (SentencePiece / T5 style)

```python
from tokenizers import Tokenizer
from tokenizers.models import Unigram
from tokenizers.pre_tokenizers import Metaspace
from tokenizers.trainers import UnigramTrainer
from tokenizers.decoders import Metaspace as MetaspaceDecoder

tokenizer = Tokenizer(Unigram())
tokenizer.pre_tokenizer = Metaspace()

trainer = UnigramTrainer(
    vocab_size=8000,
    special_tokens=["<unk>", "<s>", "</s>"],
    unk_token="<unk>",
    shrinking_factor=0.75,
)
tokenizer.train(["corpus.txt"], trainer)

tokenizer.decoder = MetaspaceDecoder()
tokenizer.save("unigram-tokenizer.json")
```

## Recipe 4: Train from HF Dataset

```python
from datasets import load_dataset
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer

dataset = load_dataset("wikitext", "wikitext-103-raw", split="train")

def batch_iterator(batch_size=1000):
    for i in range(0, len(dataset), batch_size):
        yield dataset[i : i + batch_size]["text"]

tokenizer = Tokenizer(BPE(unk_token="[UNK]"))
trainer = BpeTrainer(vocab_size=32000, special_tokens=["[UNK]", "[CLS]", "[SEP]"])
tokenizer.train_from_iterator(batch_iterator(), trainer, length=len(dataset))
```

## Key Constants

| Concept | Typical Value | Notes |
|---------|--------------|-------|
| BPE vocab_size | 30,000–50,000 | Larger = lower UNK rate, higher memory |
| WordPiece vocab_size | 28,000–32,000 | BERT uses ~30K |
| Unigram vocab_size | 4,000–32,000 | Smaller works for multilingual |
| min_frequency | 2 | Lower = more merges, noisier |
| BPE dropout | 0.1 | Regularization during training only |
| ByteLevel add_prefix_space | True | Match GPT-2 tokenizer behavior |
| WordPiece continuing_subword_prefix | "##" | BERT convention |

## Common Error Patterns

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `YAML frontmatter parse error: mapping values are not allowed here` | Colon in unquoted `description` | Wrap description in double quotes |
| `Frontmatter must include 'name' field` | Missing `name:` in frontmatter | Add `name: <skill-name>` to frontmatter |
| `module 'tokenizers' has no attribute 'X'` | Wrong import path | Use `from tokenizers.models import X`, not `from tokenizers import X` |
| High `[UNK]` rate | vocab too small, or missing unk_token | Set `unk_token` + increase `vocab_size` |
