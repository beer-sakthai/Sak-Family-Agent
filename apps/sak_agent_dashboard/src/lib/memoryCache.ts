/**
 * High-performance server-side memory caching engine for sak_agent_dashboard.
 * Provides process-local L1 LRU caching for multi-persona SQLite memory shards.
 */

import { FactRecord, ObservationRecord, MemoryShardStatus } from "./types";

export interface ShardCacheEntry {
  persona: string;
  facts: FactRecord[];
  observations: ObservationRecord[];
  status: MemoryShardStatus;
  cachedAt: number;
}

export interface MemoryCacheMetrics {
  hitRate: number;
  l1Hits: number;
  misses: number;
  totalRequests: number;
  cachedShardsCount: number;
  latencyAvgMs: number;
}

class ServerMemoryCache {
  private cache = new Map<string, ShardCacheEntry>();
  private readonly ttlMs: number;
  private hits = 0;
  private misses = 0;
  private latencies: number[] = [];

  constructor(ttlMs: number = 30_000) {
    this.ttlMs = ttlMs;
  }

  getShard(persona: string): ShardCacheEntry | null {
    const entry = this.cache.get(persona);
    if (!entry) {
      this.misses++;
      return null;
    }
    if (Date.now() - entry.cachedAt > this.ttlMs) {
      this.cache.delete(persona);
      this.misses++;
      return null;
    }
    this.hits++;
    return entry;
  }

  setShard(
    persona: string,
    data: {
      facts: FactRecord[];
      observations: ObservationRecord[];
      status: MemoryShardStatus;
    }
  ): void {
    this.cache.set(persona, {
      persona,
      facts: data.facts,
      observations: data.observations,
      status: data.status,
      cachedAt: Date.now(),
    });
  }

  invalidate(persona?: string): void {
    if (persona) {
      this.cache.delete(persona);
    } else {
      this.cache.clear();
    }
  }

  recordLatency(ms: number): void {
    this.latencies.push(ms);
    if (this.latencies.length > 50) {
      this.latencies.shift();
    }
  }

  getMetrics(): MemoryCacheMetrics {
    const total = this.hits + this.misses;
    const hitRate = total > 0 ? this.hits / total : 0;
    const avgLatency =
      this.latencies.length > 0
        ? this.latencies.reduce((a, b) => a + b, 0) / this.latencies.length
        : 0;

    return {
      hitRate: Number(hitRate.toFixed(4)),
      l1Hits: this.hits,
      misses: this.misses,
      totalRequests: total,
      cachedShardsCount: this.cache.size,
      latencyAvgMs: Number(avgLatency.toFixed(2)),
    };
  }

  clear(): void {
    this.cache.clear();
    this.hits = 0;
    this.misses = 0;
    this.latencies = [];
  }
}

// Global server singleton instance
export const serverMemoryCache = new ServerMemoryCache(30_000);
