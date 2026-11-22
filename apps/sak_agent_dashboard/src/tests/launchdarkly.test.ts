import type { EdgeConfigClient } from "@vercel/edge-config";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  createLaunchDarklyInstance,
  getLaunchDarklyClient,
  resetLaunchDarklyClient,
} from "@/lib/launchdarkly";

function createMockEdgeConfig(): EdgeConfigClient {
  return {
    get: vi.fn(),
    getAll: vi.fn(),
    has: vi.fn(),
    digest: vi.fn(),
  } as unknown as EdgeConfigClient;
}

describe("LaunchDarkly Vercel Server SDK helper", () => {
  beforeEach(() => {
    resetLaunchDarklyClient();
    delete process.env.NEXT_PUBLIC_LAUNCHDARKLY_CLIENT_SIDE_ID;
    delete process.env.LAUNCHDARKLY_CLIENT_SIDE_ID;
    delete process.env.EDGE_CONFIG;
    vi.restoreAllMocks();
  });

  it("returns null when no client ID or edgeConfig is provided", () => {
    const client = getLaunchDarklyClient();
    expect(client).toBeNull();
  });

  it("returns null when only client ID is provided without edgeConfig", () => {
    process.env.NEXT_PUBLIC_LAUNCHDARKLY_CLIENT_SIDE_ID = "test-client-id";
    const client = getLaunchDarklyClient();
    expect(client).toBeNull();
  });

  it("creates a client instance using createLaunchDarklyInstance", () => {
    const mockEdgeConfig = createMockEdgeConfig();
    const instance = createLaunchDarklyInstance(
      "example-client-side-id",
      mockEdgeConfig,
    );

    expect(instance).not.toBeNull();
    expect(typeof instance.variation).toBe("function");
  });

  it("initializes client when config with clientSideId and edgeConfigClient is provided", () => {
    const mockEdgeConfig = createMockEdgeConfig();

    const client = getLaunchDarklyClient({
      clientSideId: "test-client-id",
      edgeConfigClient: mockEdgeConfig,
    });

    expect(client).not.toBeNull();
    expect(typeof client?.variation).toBe("function");
  });

  it("caches the initialized client across subsequent calls", () => {
    const mockEdgeConfig = createMockEdgeConfig();

    const first = getLaunchDarklyClient({
      clientSideId: "cached-id",
      edgeConfigClient: mockEdgeConfig,
    });
    const second = getLaunchDarklyClient();

    expect(first).toBe(second);
  });

  it("clears cached client when resetLaunchDarklyClient is called", () => {
    const mockEdgeConfig = createMockEdgeConfig();

    const first = getLaunchDarklyClient({
      clientSideId: "cached-id",
      edgeConfigClient: mockEdgeConfig,
    });
    expect(first).not.toBeNull();

    resetLaunchDarklyClient();
    const second = getLaunchDarklyClient();
    expect(second).toBeNull();
  });
});
