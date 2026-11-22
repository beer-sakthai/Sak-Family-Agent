/**
 * LaunchDarkly Vercel Server SDK integration helper.
 * Provides server-side feature flag evaluation for Next.js / Edge routes.
 */

import {
  BasicLogger,
  init,
  type LDClient,
  type LDOptions,
} from "@launchdarkly/vercel-server-sdk";
import { createClient, type EdgeConfigClient } from "@vercel/edge-config";

let cachedClient: LDClient | null = null;

export interface LaunchDarklyConfig {
  clientSideId?: string;
  edgeConfigClient?: EdgeConfigClient;
  options?: LDOptions;
}

export { BasicLogger, createClient, init };
export type { EdgeConfigClient, LDClient, LDOptions };

/**
 * Creates and initializes a LaunchDarkly client configured for Vercel Edge.
 */
export function createLaunchDarklyInstance(
  clientSideId: string,
  edgeConfigClient: EdgeConfigClient,
  customOptions?: LDOptions,
): LDClient {
  const options: LDOptions = {
    logger: new BasicLogger({ destination: console.log }),
    sendEvents: true, // default is false
    ...customOptions,
  };

  return init(clientSideId, edgeConfigClient, options);
}

/**
 * Get or initialize the singleton LaunchDarkly Vercel Server SDK client.
 * Automatically resolves EDGE_CONFIG connection string and client-side ID from environment.
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

  let edgeConfig = config?.edgeConfigClient;
  if (!edgeConfig && process.env.EDGE_CONFIG) {
    try {
      edgeConfig = createClient(process.env.EDGE_CONFIG);
    } catch (err) {
      console.error("Failed to initialize Vercel Edge Config client:", err);
      return null;
    }
  }

  if (!clientSideId || !edgeConfig) {
    return null;
  }

  try {
    cachedClient = createLaunchDarklyInstance(clientSideId, edgeConfig, config?.options);
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
