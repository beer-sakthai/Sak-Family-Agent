# HF Hub Model Release Checklist — Official Docs Reference

Source: https://huggingface.co/docs/hub/en/model-release-checklist

## Key Sections

### Preparing Your Model for Release
- Use separate repos per model variant
- Prefer safetensors over pickle
- Write comprehensive model cards with YAML metadata + Markdown body

### Metadata Best Practices
- pipeline_tag: choose correct task tag
- library_name: set for code snippets & download tracking
- license: required SPDX identifier
- base_model: specify for fine-tunes, quantized versions, merges
- datasets: link training datasets
- language: ISO 639-1 codes

### Discoverability
- Library integration (transformers, diffusers, timm, etc.)
- Custom notebook.ipynb for one-click Colab/Kaggle
- Collections to group related models
- Interactive Space demos
- Visual examples with <Gallery> component
- Quantized versions with base_model_relation
- Carbon emissions reporting via co2_eq_emissions

### Access Control
- Private → Public transition
- Gated access (auto or manual approval)
- API: list_pending_access_requests, accept/reject/grant
- Custom extra_gated_fields
- Download access report as JSON

### Versioning
- new_version metadata on old model card → banner
- base_model + base_model_relation for model tree

Sources:
- https://huggingface.co/docs/hub/en/model-release-checklist
- https://huggingface.co/docs/hub/en/model-cards
- https://huggingface.co/docs/hub/en/models-gated
- https://huggingface.co/docs/hub/en/models-uploading
