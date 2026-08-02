# Professional Model Card — 11-Section Template

## Always aim for v3 on first attempt. Reference: `sakthai-context-0.5b-merged` (8.2K chars, 9/9).

## 1. YAML Frontmatter
```
---
license: apache-2.0
language:
- en
library_name: transformers
pipeline_tag: text-generation
tags:
- qwen2.5
- sakthai
- house-of-sak
- tool-calling
- instruct
- merged
- lora
- agent
- evaluation
- function-calling
datasets:
- Nanthasit/sakthai-combined-v3
base_model:
- Qwen/Qwen2.5-0.5B-Instruct
model-index:
- name: sakthai-context-0.5b-merged
  results:
  - task:
      type: text-generation
    dataset:
      name: SakThai Eval Suite
    metrics:
    - type: pass_rate
      value: 100.0
      name: Overall (45/45)
---
```

## 2. Badges (shields.io)
```
<p align="center">
  <a href="https://huggingface.co/Nanthasit"><img src="https://img.shields.io/badge/🤗-Nanthasit-6644cc" alt="Profile"/></a>
  <a href="https://github.com/beer-sakthai"><img src="https://img.shields.io/badge/GitHub-beer--sakthai-181717" alt="GitHub"/></a>
  <a href="https://house-of-sak.vercel.app"><img src="https://img.shields.io/badge/🏠-House%20of%20Sak-gold" alt="HoS"/></a>
  <img src="https://img.shields.io/badge/license-Apache%202.0-brightgreen" alt="License"/>
  <img src="https://img.shields.io/badge/downloads-802-blue" alt="Downloads"/>
  <img src="https://img.shields.io/badge/params-1.54B-blueviolet" alt="Params"/>
</p>
```

## 3. Model Description
`<h1 align="center">Model Name</h1>` + House of Sak tagline + 1-2 paragraphs: base model, purpose, key capability, origin context.

## 4. Quick Start
Full copy-paste Python with imports, model loading, inference, and output.

## 5. Architecture Table
| Property | Value | — Base Model, Parameters, Hidden Size, Layers, Attention Heads (GQA), Intermediate Size, Vocab Size, Max Context, Activation (SwiGLU), Precision.

## 6. Training Hyperparameters
| Hyperparameter | Value | — LoRA r/alpha/dropout, Target Modules, Dataset name+size, Epochs, Steps, Duration, Optimizer, Learning Rate, Compute.

## 7. Evaluation Results
Full table from `eval/` files. Include comparison vs base model where available.

## 8. Sample Responses
| Test | Model Output | — Real outputs from eval files. greeting, json-array, weather-query, coding, etc.

## 9. Limitations & Biases
~5 bullet points: size constraints, training data scope, language, safety alignment, latency.

## 10. Citation (BibTeX)
```
@misc{sakthai-{model-name},
  author = {Nanthasit Burankum},
  title = {SakThai Context {Size}: {Description}},
  year = {2026},
  publisher = {Hugging Face},
  journal = {House of Sak Model Family},
  howpublished = {\\url{https://huggingface.co/Nanthasit/{repo}}}
}
```

## 11. Links Table
| Resource | Link | — Profile, GitHub, House of Sak, Adapter, Dataset, Eval files.

## Category Variants

### Datasets (v3-v6, kaggle)
Skip 5-6. Add: stats table, data structure, trained models, successor chain. Target: 5-7/9.

### Adapters (tools repos)
Skip 5, 7, 9-10. Keep: training config table, usage code with PEFT, merged model link. Target: 5-7/9.

### Deprecated / Superseded
Skip 5-10. Keep: badges (with deprecation status), deprecation notice, usage code, successor link(s). Target: 3-4/9.

### Profile Repo (Nanthasit/Nanthasit)
Different standard. Bio, House of Sak agent table, badges, links. No architecture/eval/citation. Target: 2-3/9.
