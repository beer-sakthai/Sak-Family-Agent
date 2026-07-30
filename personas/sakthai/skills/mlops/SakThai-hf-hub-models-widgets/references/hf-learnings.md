# HF Hub Inference Widgets — Deep Dive

Learned: 2026-07-25
Author: SakThai
License: MIT

## Key Findings

### How Widgets Work
The Hub model page widget is a client-side inference demo that makes REST calls
through the Inference Providers network. When a user clicks "Compute" on a
model page, the browser sends the input to `https://api-inference.huggingface.co/models/{model_id}`
(or via the Inference Providers routing system), which selects a provider and returns
the output.

### Widget YAML Configuration
The `widget:` key in model card metadata controls:
- **Example inputs** — what users see as pre-filled demos
- **Example outputs** — for models without live provider support (show expected results)
- **Gallery entries** — text-to-image outputs shown on model pages

### Provider Integration
The widget now routes through Inference Providers rather than the old single-provider
system. The official supported tasks list is at:
`https://huggingface.co/docs/inference-providers/tasks/index`

### Community Request System
If a model has no provider backing it, users can click "Ask for provider support"
to signal demand — enough signals may incent providers to add the model.

### Playground
The Inference Playground (`/playground`) is a full chat-completion UI using the
same provider infrastructure — useful for testing models before integration.

### Default Widget Inputs
Community-maintained default inputs are in the huggingface.js monorepo at:
`packages/tasks/src/default-widget-inputs.ts`

## Practical Notes for Beer

1. **For his models**: Adding `widget:` with example inputs to model card YAML
   makes models look professional and usable.
2. **For his Spaces**: The Inference Playground can be used to test which provider
   gives best quality/performance for a given model.
3. **Zero-cost**: Widget inference through community-tier providers is free.
4. **Model card YAML widgets** also enable the "Gallery" view for image models.
