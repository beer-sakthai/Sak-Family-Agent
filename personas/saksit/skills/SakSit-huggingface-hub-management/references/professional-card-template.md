# Professional HF Model Card — Template & Checklist

## Card must have ALL 11 sections to match Qwen/Mistral standard:

### 1. YAML Frontmatter
Required fields: license, language, library_name, pipeline_tag, tags (+house-of-sak, agent, function-calling), datasets, base_model, model-index (with eval metrics).

### 2. Badges (shields.io)
- HF Profile: `https://img.shields.io/badge/🤗-Nanthasit-6644cc`
- GitHub: `https://img.shields.io/badge/GitHub-beer--sakthai-181717`
- House of Sak: `https://img.shields.io/badge/🏠-House%20of%20Sak-gold`
- License: `https://img.shields.io/badge/license-Apache%202.0-brightgreen`
- Downloads: `https://img.shields.io/badge/downloads-{N}-blue`
- Params: `https://img.shields.io/badge/params-{N}B-blueviolet`

### 3. Model Description
Base model, purpose, key capability. House of Sak origin (1-2 paragraphs).

### 4. Quick Start
Copy-paste Python with proper imports:
```python
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained("Nanthasit/{repo}")
tokenizer = AutoTokenizer.from_pretrained("Nanthasit/{repo}")
```

### 5. Architecture Table
| Property | Value |
|----------|-------|
| Base Model | |
| Parameters | |
| Hidden Size | |
| Layers | |
| Attention Heads | |
| Intermediate Size | |
| Vocab Size | |
| Max Context | |
| Activation | |
| Precision | |

### 6. Training Hyperparameters
| Hyperparameter | Value |
|----------------|-------|
| Method | LoRA via PEFT |
| LoRA r/alpha/dropout | |
| Target Modules | |
| Dataset | |
| Epochs/Steps | |
| Duration | |
| Optimizer | |
| LR | |
| Compute | |

### 7. Evaluation Results
Full table with pass rates per category. Include comparison vs base model.

### 8. Sample Responses
| Test | Model Output |
|------|-------------|
| greeting | "..." |
| json-array | [...] |
| coding | def ... |

### 9. Limitations & Biases
Size constraints, data scope, language support, safety alignment.

### 10. Citation (BibTeX)
```bibtex
@misc{sakthai-{name},
  author = {Nanthasit Burankum},
  title = {...},
  year = {2026},
  publisher = {Hugging Face},
  howpublished = {\url{https://huggingface.co/Nanthasit/{repo}}}
}
```

### 11. Links Table
| Resource | Link |
|----------|------|
| Profile | huggingface.co/Nanthasit |
| GitHub | github.com/beer-sakthai |
| House of Sak | house-of-sak.vercel.app |

## CRITICAL: ADD, NEVER REMOVE
When updating an existing card, read the current README.md FIRST, then MERGE. Never replace.

## Validation
```python
# After building card content string
from huggingface_hub import ModelCard
card = ModelCard(content)
card.validate()  # Raises on validation errors
```
