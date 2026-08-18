/**
 * Hugging Face Ecosystem Engine for sak_agent_dashboard.
 * Provides live catalog management, card validation, and health checks.
 */

import { HubAsset, HubEcosystemData } from "./types";
import { SAK_HUB_ASSETS, getHubEcosystemData } from "./hub";

export interface CardValidationResult {
  valid: boolean;
  score: number;
  issues: Array<{
    rule: string;
    message: string;
    severity: "error" | "warning";
  }>;
}

export class HFEcosystemEngine {
  private assets: HubAsset[] = SAK_HUB_ASSETS;

  getAssets(): HubAsset[] {
    return this.assets;
  }

  getEcosystemSummary(): HubEcosystemData {
    return getHubEcosystemData();
  }

  validateCard(repoId: string, content: string): CardValidationResult {
    const issues: Array<{ rule: string; message: string; severity: "error" | "warning" }> = [];
    let score = 100;

    // Rule 1: No hardcoded downloads
    if (/\b(\d+[\d,]*\+?\s*downloads?)\b/i.test(content)) {
      issues.push({
        rule: "no_hardcoded_downloads",
        message: "Found hardcoded download count in Markdown text. Use dynamic shields.io badge.",
        severity: "warning",
      });
      score -= 15;
    }

    // Rule 2: Single family table
    const matches = content.match(/\|.*context-1\.5b-merged.*\|/g);
    if (matches && matches.length > 1) {
      issues.push({
        rule: "single_family_table",
        message: `Family table repeated ${matches.length} times. Keep single canonical table.`,
        severity: "warning",
      });
      score -= 15;
    }

    // Rule 3: Honest evals
    if (/verified:\s*true/i.test(content)) {
      issues.push({
        rule: "honest_evals",
        message: "Found 'verified: true'. Internal evaluations must be labeled 'verified: false'.",
        severity: "error",
      });
      score -= 30;
    }

    // Rule 4: Correct food-penguin
    if (content.includes("food-penguin") && /food\s+image\s+classification/i.test(content)) {
      issues.push({
        rule: "canonical_dataset_facts",
        message: "food-penguin incorrectly labeled as 'food image classification'; should be 'restaurant-analytics tool-calling'.",
        severity: "error",
      });
      score -= 20;
    }

    // Rule 5: Frontmatter
    if (!content.startsWith("---")) {
      issues.push({
        rule: "yaml_frontmatter",
        message: "Missing YAML frontmatter header delimiters (---).",
        severity: "error",
      });
      score -= 20;
    }

    return {
      valid: !issues.some((i) => i.severity === "error") && score >= 70,
      score: Math.max(0, score),
      issues,
    };
  }
}

export const hfEcosystemEngine = new HFEcosystemEngine();
