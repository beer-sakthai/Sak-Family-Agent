---
name: SakThai-hf-hub-models-widgets
description: ">-   HF Hub model page inference widgets \u2014 configuration, example inputs/outputs,\
  \   provider-backed live inference, playground testing, and widget metadata YAML."
---

# Hugging Face Hub Inference Widgets

## Overview

The model page inference widget allows users to test models directly on the Hub
without writing any code. Widgets are powered by the **Inference Providers**
network — a multi-provider inference serving system that replaced the old
"Hosted Inference API."

## Widget Configuration

Widgets are configured through YAML metadata in the model card:

```yaml
widget:
  - text: "The two men running to become New York City's next mayor..."
    example_title: "Reading comprehension"
  - src: sample1.flac
    example_title: "Speech sample 1"
```

### Example Input Types

- **Text tasks**: `text` property
- **Audio/Image tasks**: `src` property (URL or relative repo path)
- **Multiple examples**: Array under `widget:` key
- **Examples repo-relative**: Just use filename/path inside the repo
- **Default inputs**: Source at `huggingface.js/packages/tasks/src/default-widget-inputs.ts`

### Example Outputs

For models without live provider support, example outputs can be specified:

```yaml
widget:
  - text: "I liked this movie"
    output:
      - label: POSITIVE
        score: 0.8
      - label: NEGATIVE
        score: 0.2
```

Output types:
- **Text output**: `output.text`
- **Label scores**: `output[].label` + `output[].score`
- **Media output**: `output.url` (image/audio file in repo)

## Widget Availability Conditions

1. **Task Support**: The model's pipeline tag must be served by at least one
   Inference Provider
2. **Provider Availability**: At least one provider actively serves that model
3. **Model Configuration**: Proper metadata and config files must exist

If no provider supports a model, "Ask for provider support" button appears.

## Inference Playground

The [Inference Playground](https://huggingface.co/playground) lets users test
chat completion models interactively with custom prompts, compare models, and
tweak parameters (temperature, max tokens). Uses the same Inference Providers
infrastructure.

## How the Widget Differs from InferenceClient

| Aspect | Widget | InferenceClient |
|--------|--------|-----------------|
| Use case | One-click testing on model page | Programmatic inference in code |
| Auth | Uses HF token or cookies | Uses HF token |
| Routing | Provider auto-selection | Provider selection via model ID |
| Streaming | Limited (non-streaming for most) | Full streaming support |
| Cost | Free (community tier) | Free or paid per provider |

## Key Takeaway

Widgets are the public face of Inference Providers on model pages. Configure
them well = better user engagement. For zero-cost production inference, use
InferenceClient with community-tier providers targeting the same model ID.
