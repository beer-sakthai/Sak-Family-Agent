import { describe, it, expect, beforeEach } from "vitest";
import { serverMemoryCache } from "@/lib/memoryCache";
import { getMemoryData } from "@/lib/db";

describe("Server Memory Cache & Dashboard Integration", () => {
  beforeEach(() => {
    serverMemoryCache.clear();
  });

  it("caches memory shards and tracks hits/misses", () => {
    expect(serverMemoryCache.getShard("sakthai")).toBeNull();
    const metrics1 = serverMemoryCache.getMetrics();
    expect(metrics1.misses).toBe(1);
    expect(metrics1.l1Hits).toBe(0);

    serverMemoryCache.setShard("sakthai", {
      facts: [
        {
          id: "f1",
          entity: "deployment",
          fact: "CI active",
          persona: "SakThai",
          createdAt: new Date().toISOString(),
        },
      ],
      observations: [],
      status: {
        persona: "sakthai",
        path: "/tmp/sakthai/memory.db",
        exists: true,
        factCount: 1,
        observationCount: 0,
      },
    });

    const cached = serverMemoryCache.getShard("sakthai");
    expect(cached).not.toBeNull();
    expect(cached?.facts.length).toBe(1);
    expect(cached?.facts[0].fact).toBe("CI active");

    const metrics2 = serverMemoryCache.getMetrics();
    expect(metrics2.l1Hits).toBe(1);
    expect(metrics2.hitRate).toBe(0.5);
  });

  it("getMemoryData attaches cacheMetrics to the payload", async () => {
    const res = await getMemoryData(true);
    expect(res.memory).toBeDefined();
    expect(res.dataSource).toBe("demo");
  });

  it("invalidates cache selectively or completely", () => {
    serverMemoryCache.setShard("sakking", {
      facts: [],
      observations: [],
      status: {
        persona: "sakking",
        path: "/tmp/sakking/memory.db",
        exists: true,
        factCount: 0,
        observationCount: 0,
      },
    });
    serverMemoryCache.setShard("saksee", {
      facts: [],
      observations: [],
      status: {
        persona: "saksee",
        path: "/tmp/saksee/memory.db",
        exists: true,
        factCount: 0,
        observationCount: 0,
      },
    });

    expect(serverMemoryCache.getShard("sakking")).not.toBeNull();
    serverMemoryCache.invalidate("sakking");
    expect(serverMemoryCache.getShard("sakking")).toBeNull();
    expect(serverMemoryCache.getShard("saksee")).not.toBeNull();

    serverMemoryCache.invalidate();
    expect(serverMemoryCache.getShard("saksee")).toBeNull();
  });
});
