import { createApiHandler } from "@/lib/api/handler";
import { PROVIDERS } from "@/lib/providers";

export const dynamic = "force-dynamic";

export const GET = createApiHandler("/api/providers", async () => ({
  providers: PROVIDERS,
  totalProviders: PROVIDERS.length,
  timestamp: new Date().toISOString(),
}));
