/**
 * Domain types for the Semantic Response Caching & Token Cost Optimizer Layer.
 */

export interface SemanticCacheEntry {
  id: string;
  prompt: string;
  normalizedPrompt: string;
  response: string;
  personaSlug: string;
  model: string;
  embedding: number[];
  tokensSaved: number;
  costSavedUsd: number;
  hitCount: number;
  similarityThreshold: number;
  ttlSeconds: number;
  createdAt: string;
  lastAccessedAt: string;
  expiresAt: string;
}

export interface CacheLookupQuery {
  prompt: string;
  personaSlug?: string;
  model?: string;
  minSimilarity?: number;
}

export interface CacheLookupResult {
  hit: boolean;
  similarity: number;
  entry?: SemanticCacheEntry;
  latencySavedMs: number;
  lookupLatencyMs: number;
}

export interface ModelPricing {
  promptCostPer1k: number;
  completionCostPer1k: number;
}

export interface CacheAnalytics {
  totalLookups: number;
  totalHits: number;
  hitRatePercent: number;
  totalTokensSaved: number;
  totalCostSavedUsd: number;
  avgLookupLatencyMs: number;
  cacheSize: number;
  topCachedPatterns: Array<{ prompt: string; hitCount: number; costSavedUsd: number }>;
}

export const MODEL_PRICING_CATALOG: Record<string, ModelPricing> = {
  'claude-3-5-sonnet-20241022': { promptCostPer1k: 0.003, completionCostPer1k: 0.015 },
  'gemini-1.5-pro': { promptCostPer1k: 0.00125, completionCostPer1k: 0.005 },
  'gemini-1.5-flash': { promptCostPer1k: 0.000075, completionCostPer1k: 0.0003 },
  'gpt-4o': { promptCostPer1k: 0.0025, completionCostPer1k: 0.01 },
  'sakthai-v2-qlora': { promptCostPer1k: 0.0, completionCostPer1k: 0.0 } // Free local
};
