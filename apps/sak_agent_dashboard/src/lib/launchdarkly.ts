/**
 * LaunchDarkly Vercel Server SDK integration helper.
 * Provides server-side feature flag evaluation for Next.js / Edge routes.
 */

import { init, type LDClient, type LDOptions } from "@launchdarkly/vercel-server-sdk";
import type { EdgeConfigClient } from "@vercel/edge-config";

let cachedClient: LDClient | null = null;

export interface LaunchDarklyConfig {
  clientSideId?: string;
  edgeConfigClient?: EdgeConfigClient;
  options?: LDOptions;
}

/**
 * Get or initialize the LaunchDarkly Vercel Server SDK client.
 * Returns null if required credentials or edge config are absent.
 */
export function getLaunchDarklyClient(config?: LaunchDarklyConfig): LDClient | null {
  if (cachedClient) {
    return cachedClient;
  }

  const clientSideId =
    config?.clientSideId ||
    process.env.NEXT_PUBLIC_LAUNCHDARKLY_CLIENT_SIDE_ID ||
    process.env.LAUNCHDARKLY_CLIENT_SIDE_ID;
  const edgeConfig = config?.edgeConfigClient;

  if (!clientSideId || !edgeConfig) {
    return null;
  }

  try {
    cachedClient = init(clientSideId, edgeConfig, config?.options);
    return cachedClient;
  } catch (error) {
    console.error("Failed to initialize LaunchDarkly Vercel Server client:", error);
    return null;
  }
}

/**
 * Reset cached client instance (primarily for test environments).
 */
export function resetLaunchDarklyClient(): void {
  cachedClient = null;
}
