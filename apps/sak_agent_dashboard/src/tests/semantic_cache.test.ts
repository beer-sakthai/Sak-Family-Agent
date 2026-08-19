import { describe, it, expect } from 'vitest';
import { SemanticCacheEngine } from '../lib/cache/semanticCacheEngine';

describe('SemanticCacheEngine', () => {
  it('normalizes prompt text by stripping punctuation and lowercasing', () => {
    const raw = '  Generate minimal rootless Dockerfile, for Next.js 15!  ';
    const normalized = SemanticCacheEngine.normalizeText(raw);
    expect(normalized).toBe('generate minimal rootless dockerfile for nextjs 15');
  });

  it('generates 64-dimensional L2-normalized embedding vectors', () => {
    const vec = SemanticCacheEngine.generateEmbedding('hello world agentic mesh');
    expect(vec).toHaveLength(64);

    const magnitude = Math.sqrt(vec.reduce((sum, val) => sum + val * val, 0));
    expect(magnitude).toBeCloseTo(1.0, 4);
  });

  it('computes cosine similarity accurately between identical and disparate text', () => {
    const vec1 = SemanticCacheEngine.generateEmbedding('Generate minimal rootless multi-stage Dockerfile for Next.js 15 app');
    const vec2 = SemanticCacheEngine.generateEmbedding('Generate minimal rootless multi-stage Dockerfile for Next.js 15 app');
    const vec3 = SemanticCacheEngine.generateEmbedding('Completely unrelated cooking recipe for chocolate cake');

    const exactSim = SemanticCacheEngine.cosineSimilarity(vec1, vec2);
    expect(exactSim).toBeCloseTo(1.0, 4);

    const disparateSim = SemanticCacheEngine.cosineSimilarity(vec1, vec3);
    expect(disparateSim).toBeLessThan(0.4);
  });

  it('performs semantic cache hits with exact match', () => {
    const res = SemanticCacheEngine.lookup({
      prompt: 'Generate minimal rootless multi-stage Dockerfile for Next.js 15 app',
      minSimilarity: 0.85
    });

    expect(res.hit).toBe(true);
    expect(res.similarity).toBe(1.0);
    expect(res.entry).toBeDefined();
    expect(res.entry?.personaSlug).toBe('sakjules');
    expect(res.latencySavedMs).toBeGreaterThan(0);
  });

  it('stores and invalidates dynamic prompt entries', () => {
    const entry = SemanticCacheEngine.store(
      'Custom Unique Prompt for Test Scenario ABC',
      'Custom Generated Output XYZ',
      'sakthai',
      'gemini-1.5-pro',
      3600
    );

    expect(entry.id).toBeDefined();
    expect(entry.tokensSaved).toBeGreaterThan(0);
    expect(entry.costSavedUsd).toBeGreaterThan(0);

    const lookupBefore = SemanticCacheEngine.lookup({
      prompt: 'Custom Unique Prompt for Test Scenario ABC'
    });
    expect(lookupBefore.hit).toBe(true);

    const deleted = SemanticCacheEngine.invalidate(entry.id);
    expect(deleted).toBe(1);

    const lookupAfter = SemanticCacheEngine.lookup({
      prompt: 'Custom Unique Prompt for Test Scenario ABC'
    });
    expect(lookupAfter.hit).toBe(false);
  });

  it('calculates comprehensive cache analytics and dollar savings', () => {
    const analytics = SemanticCacheEngine.getAnalytics();
    expect(analytics.totalLookups).toBeGreaterThan(0);
    expect(analytics.hitRatePercent).toBeGreaterThan(50);
    expect(analytics.totalCostSavedUsd).toBeGreaterThan(0);
    expect(analytics.topCachedPatterns.length).toBeGreaterThanOrEqual(1);
  });
});
