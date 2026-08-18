import { describe, it, expect } from "vitest";
import { SAK_HUB_ASSETS, getHubEcosystemData } from "@/lib/hub";
import { hfEcosystemEngine } from "@/lib/hfEcosystemEngine";

describe("Hugging Face Hub Ecosystem Suite", () => {
  it("verifies inventory includes models, datasets, and spaces", () => {
    const data = getHubEcosystemData();
    expect(data.totalModels).toBeGreaterThanOrEqual(12);
    expect(data.totalDatasets).toBeGreaterThanOrEqual(5);
    expect(data.totalSpaces).toBeGreaterThanOrEqual(3);
    expect(data.assets.length).toBeGreaterThan(0);
  });

  it("ensures all assets possess valid URL and metadata", () => {
    SAK_HUB_ASSETS.forEach((asset) => {
      expect(asset.url).toMatch(/^https:\/\/huggingface\.co\//);
      expect(asset.name).toBeTruthy();
      expect(asset.meta.tags).toBeInstanceOf(Array);
    });
  });

  it("validates model card content correctly", () => {
    const cleanCard = `---
license: apache-2.0
pipeline_tag: text-generation
tags:
  - sak-family
---
# Test Model
> Tagline
## What it is
Specialized fine-tuned model.
## Evaluation
- Score: 80% (internal, not third-party verified; verified: false)
| Model | Size | Role |
|---|---|---|
| context-1.5b-merged | 1.5B | Flagship |
`;
    const res = hfEcosystemEngine.validateCard("sakthai/test", cleanCard);
    expect(res.valid).toBe(true);
    expect(res.score).toBeGreaterThanOrEqual(80);
  });
});
